#!/usr/bin/env python3
"""Deterministic importer for the pstack Spec Kit extension.

The only path from the pinned upstream tree to the packaged resources. It reads
tracked Git blobs at the pinned commit, verifies each one, applies the explicit
translations in tools/pstack_transforms.py, writes or copies every target, and
records what it did in source-manifest.json. No network access at any point.

    python3 tools/import_upstream.py --upstream /path/to/cursor-plugins

Fails loudly on drift: a missing blob, a moved path, a `find` string that is no
longer present, or a differing occurrence count stops the import. Re-running with
the same upstream tree produces byte-identical output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pstack_transforms as T

PINNED_REPOSITORY = "https://github.com/cursor/plugins"
PINNED_COMMIT = "889ec4b68fa5aab0e867dad71ec3fdf386ae48f3"
UPSTREAM_SUBTREE = "pstack"
EXTENSION_VERSION = "0.2.0"

REPO_ROOT = Path(__file__).resolve().parent.parent
INVENTORY_FILE = REPO_ROOT / "tools" / "source-inventory.json"
OVERRIDES_DIR = REPO_ROOT / "tools" / "overrides"
MANIFEST_FILE = REPO_ROOT / "source-manifest.json"
ADAPTER_DIR = REPO_ROOT / "commands" / "generated"
RESOURCES_DIR = REPO_ROOT / "resources"

TEXT_SUFFIXES = {".md", ".markdown", ".json", ".yaml", ".yml", ".ts", ".mjs", ".js", ".sh", ".txt", ".toml"}
# Runtime source that has no host dependency stays byte-identical: the Bun tools,
# their lockfile, the bootstrap, and the POSIX log helper.
BYTE_IDENTICAL_PREFIXES = (
    f"{UPSTREAM_SUBTREE}/skills/poteto-mode/scripts/orch/",
    f"{UPSTREAM_SUBTREE}/skills/poteto-mode/scripts/watch-pr/",
)
BYTE_IDENTICAL_FILES = frozenset(
    {
        f"{UPSTREAM_SUBTREE}/skills/poteto-mode/scripts/bun.lock",
        f"{UPSTREAM_SUBTREE}/skills/poteto-mode/scripts/package.json",
        f"{UPSTREAM_SUBTREE}/skills/poteto-mode/scripts/bootstrap.ts",
        f"{UPSTREAM_SUBTREE}/skills/show-me-your-work/scripts/log.sh",
        f"{UPSTREAM_SUBTREE}/skills/show-me-your-work/references/decision-log-template.tsv",
    }
)

# Files whose transformed bytes may not be edited by hand.
GENERATED_PREFIXES = ("resources/", "commands/generated/")


class ImportFailure(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(upstream: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(upstream), *args],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ImportFailure(
            f"git {' '.join(args)} failed: {result.stderr.decode('utf-8', 'replace').strip()}"
        )
    return result.stdout


def verify_tracked(upstream: Path, source: str, blob: str, mode: str) -> bytes:
    """Return the bytes of *source* at the pinned commit, verified against *blob*."""
    listing = git(upstream, "ls-tree", PINNED_COMMIT, "--", source).decode("utf-8").strip().splitlines()
    matches = [line for line in listing if line.split("\t", 1)[-1] == source]
    if not matches:
        raise ImportFailure(f"{source} is not tracked at {PINNED_COMMIT[:12]}")
    listing_mode, _kind, listing_blob = matches[0].split("\t")[0].split()
    if listing_blob != blob:
        raise ImportFailure(
            f"{source} has blob {listing_blob} at {PINNED_COMMIT[:12]}, inventory says {blob}"
        )
    if listing_mode != mode:
        raise ImportFailure(f"{source} has mode {listing_mode}, inventory says {mode}")
    content = git(upstream, "cat-file", "blob", blob)
    digest = hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()
    if digest != blob:
        raise ImportFailure(f"{source}: content hash {digest} does not match blob {blob}")
    return content


def classification(source: str) -> str:
    if source in T.COMPANION_FILES:
        return T.COMPANION_FILES[source][1]
    rel = source[len(UPSTREAM_SUBTREE) + 1 :]
    if rel.startswith("skills/"):
        parts = rel.split("/")
        if len(parts) == 3 and parts[2] == "SKILL.md":
            return "command"
        if "/scripts/" in rel:
            return "script"
        return "reference"
    if rel.startswith("agents/"):
        return "agent"
    if rel.startswith("automations/"):
        return "dormant"
    if rel.startswith("docs/"):
        return "doc"
    if rel.startswith("assets/"):
        return "asset"
    if rel == "LICENSE":
        return "asset"
    return "provenance"


def target_for(source: str) -> str:
    if source in T.COMPANION_FILES:
        return T.COMPANION_FILES[source][0]
    rel = source[len(UPSTREAM_SUBTREE) + 1 :]
    if rel.startswith(("skills/", "agents/", "automations/", "docs/", "assets/")):
        return f"resources/{rel}"
    if rel == "LICENSE":
        return "resources/LICENSE"
    if rel == "README.md":
        return "resources/upstream/README.md"
    if rel == ".gitignore":
        return "resources/upstream/pstack.gitignore"
    if rel == ".cursor-plugin/plugin.json":
        return "resources/upstream/cursor-plugin.json"
    raise ImportFailure(f"no target mapping for {source}")


def is_byte_identical(source: str) -> bool:
    return source.startswith(BYTE_IDENTICAL_PREFIXES) or source in BYTE_IDENTICAL_FILES


def apply_edits(source: str, text: str, transforms: list[dict]) -> str:
    for edit in T.FILE_EDITS.get(source, []):
        expected = edit.get("count", 1)
        actual = text.count(edit["find"])
        if actual != expected:
            raise ImportFailure(
                f"{source}: edit expects {expected} occurrence(s) of {edit['find'][:70]!r}, found {actual}"
            )
        text = text.replace(edit["find"], edit["replace"])
        transforms.append(
            {"op": "edit", "from": edit["find"], "to": edit["replace"], "reason": edit["reason"]}
        )
    return text


def apply_global_rewrites(source: str, text: str, transforms: list[dict]) -> str:
    for pattern, replacement, reason in T.GLOBAL_REWRITES:
        new_text, count = re.subn(pattern, replacement, text)
        if count:
            transforms.append({"op": "rewrite", "from": pattern, "to": replacement, "reason": reason})
            text = new_text
    return text

def apply_command_rewrites(source: str, text: str, transforms: list[dict]) -> str:
    names = "|".join(re.escape(name) for name in sorted(T.GUIDE_COMMAND_NAMES, key=len, reverse=True))
    pattern = rf"(?<![A-Za-z0-9_.-])/({names})\b"
    new_text, count = re.subn(pattern, lambda match: f"/speckit.pstack.{match.group(1)}", text)
    if count:
        transforms.append(
            {
                "op": "rewrite",
                "from": "bare pstack command invocations in active resources",
                "to": "/speckit.pstack.<name>",
                "reason": "active resources invoke registered native command names",
            }
        )
    return new_text



def transform_source(source: str, raw: bytes) -> tuple[bytes, list[dict]]:
    """Return the packaged bytes for one source file and the transforms applied."""
    transforms: list[dict] = []
    override = OVERRIDES_DIR / source
    if override.is_file():
        return override.read_bytes(), [
            {"op": "override", "from": source, "reason": T.OVERRIDE_REASONS[source]}
        ]
    suffix = Path(source).suffix.lower()
    if not any(source.endswith(s) for s in TEXT_SUFFIXES) or is_byte_identical(source):
        return raw, transforms
    if classification(source) in {"provenance", "host-manifest"}:
        # Vendored attribution keeps upstream bytes exactly; it is never activated.
        return raw, transforms
    if suffix not in TEXT_SUFFIXES:
        return raw, transforms
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw, transforms
    # Edits run first: they quote upstream text that the global rewrites would
    # otherwise have already changed.
    text = apply_edits(source, text, transforms)
    text = apply_global_rewrites(source, text, transforms)
    text = apply_command_rewrites(source, text, transforms)
    return text.encode("utf-8"), transforms


def frontmatter_description(text: str, fallback: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return fallback
    body: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        body.append(line)
    description: list[str] = []
    collecting = False
    for line in body:
        if collecting:
            if line.startswith((" ", "\t")):
                description.append(line.strip())
                continue
            break
        match = re.match(r"^description:\s*(.*)$", line)
        if match:
            value = match.group(1).strip()
            if value in (">-", ">", "|", "|-"):
                collecting = True
                continue
            description.append(value.strip("\"'"))
            break
    text_out = " ".join(part for part in description if part).strip()
    # Upstream descriptions escape their inner double quotes; drop the escapes
    # before re-emitting, or the generated frontmatter carries an invalid escape.
    text_out = text_out.replace('\\"', '"').replace("\\'", "'").replace("\\", "")
    if text_out.endswith((".", "!", "?")):
        text_out = text_out[:-1]
    text_out = re.sub(r"\s+", " ", text_out).replace('"', "'")
    # The description lands in frontmatter, where no registrar substitutes a host
    # invocation form, so name the command id instead of one host's slash form.
    text_out = text_out.replace("/speckit.pstack.", "speckit.pstack.")
    return text_out or fallback

def frontmatter_adapter_metadata(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    supported = {"paths", "disable-model-invocation"}
    kept: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, _ = line.partition(":")
        if separator and key in supported:
            kept.append(line)
    return "".join(f"{line}\n" for line in kept)


ADAPTER_TEMPLATE = """---
description: "{description}"
{metadata}---

# {title} (pstack)

Run the translated pstack skill named below. Load the shared host contract first,
because it owns role resolution, dispatch, report handling, and skill-name
resolution on this host:

`.specify/extensions/pstack/runtime/host-contract.md`

Then read the skill resource in full and follow it:

`.specify/extensions/pstack/resources/skills/{name}/SKILL.md`

Every reference inside that resource is either relative to its own directory or an
explicit `.specify/extensions/pstack/` path, so both resolve from the project root.
The resources name pstack skills by their bare skill name (`how`, `unslop`). The
host contract maps every such name to its packaged resource path, and the extension's
own commands are registered as `speckit.pstack.<skill>`.

## Arguments

```text
$ARGUMENTS
```
"""

POTETO_MODE_ADAPTER_TEMPLATE = """---
description: "{description}"
{metadata}---

# Poteto Mode (pstack)

Parse `$ARGUMENTS` before reading any pstack resource.

- For `on`, `off`, or `status`, run the matching fixed command through
  `.specify/extensions/pstack/runtime/pstack-native.py mode`. Return its result and
  stop. If the helper is absent or fails, load no resource and do not edit the
  instruction file by hand.
- For no arguments or a task, run
  `.specify/extensions/pstack/runtime/pstack-native.py mode status` first. Continue
  only when `extension.enabled` and `extension.resources_present` are both exactly
  `true`. Project-block readiness is not required for invocation-only session mode.
  Any failed check makes this command inert.

After that readiness check, read these files in order and follow the mode resource
for `$ARGUMENTS`:

1. `.specify/extensions/pstack/runtime/host-contract.md`
2. `.specify/extensions/pstack/resources/skills/poteto-mode/SKILL.md`
"""


def adapter_text(name: str, description: str, metadata: str) -> str:
    title = " ".join(part.capitalize() for part in name.split("-"))
    template = POTETO_MODE_ADAPTER_TEMPLATE if name == "poteto-mode" else ADAPTER_TEMPLATE
    return template.format(description=description, title=title, name=name, metadata=metadata)


def write_file(root: Path, target: str, data: bytes, mode: int = 0o644) -> str:
    path = root / target
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(mode)
    return sha256_bytes(data)


def cleanup_stale(root: Path, keep: set[str], manifest_path: Path) -> list[str]:
    """Delete only importer-owned files that this run did not regenerate."""
    if not manifest_path.is_file():
        return []
    previous = json.loads(manifest_path.read_text(encoding="utf-8"))
    owned: set[str] = set()
    for record in previous.get("files", []):
        owned.add(record["target"])
    for record in previous.get("generated", []):
        owned.add(record["target"])
    removed: list[str] = []
    for target in sorted(owned - keep):
        if not target.startswith(GENERATED_PREFIXES):
            raise ImportFailure(f"{target} is manifest-owned but outside the generated prefixes")
        path = root / target
        if path.is_file():
            path.unlink()
            removed.append(target)
    for prefix in GENERATED_PREFIXES:
        base = root / prefix
        if not base.is_dir():
            continue
        for child in sorted(base.rglob("*"), reverse=True):
            if child.is_dir() and not any(child.iterdir()):
                child.rmdir()
    return removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="import the pinned pstack tree")
    parser.add_argument("--upstream", required=True, help="checkout of the pinned repository")
    parser.add_argument("--root", default=str(REPO_ROOT), help="extension root to write into")
    parser.add_argument("--inventory", default=str(INVENTORY_FILE))
    args = parser.parse_args(argv)

    upstream = Path(args.upstream).expanduser().resolve()
    root = Path(args.root).expanduser().resolve()
    manifest_file = root / "source-manifest.json"
    if not (upstream / ".git").is_dir():
        raise ImportFailure(f"{upstream} is not a git checkout; pinned blobs cannot be verified")

    inventory = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    if inventory["commit"] != PINNED_COMMIT:
        raise ImportFailure(f"inventory pins {inventory['commit']}, importer pins {PINNED_COMMIT}")
    if inventory["repository"] != PINNED_REPOSITORY:
        raise ImportFailure(f"inventory names {inventory['repository']}, importer names {PINNED_REPOSITORY}")

    overrides = {str(path.relative_to(OVERRIDES_DIR)) for path in OVERRIDES_DIR.rglob("*") if path.is_file()}
    unused_overrides = overrides - set(T.OVERRIDE_REASONS)
    if unused_overrides:
        raise ImportFailure(f"overrides without a reason: {sorted(unused_overrides)}")
    missing_overrides = {path for path in T.OVERRIDE_REASONS if not (OVERRIDES_DIR / path).is_file()}
    if missing_overrides:
        raise ImportFailure(f"overrides declared but absent: {sorted(missing_overrides)}")

    sources: list[dict] = []
    for record in inventory["files"]:
        sources.append({"source": record["source"], "mode": record["mode"], "blob": record["blob"]})
    seen = {record["source"] for record in sources}
    for source, (target, _kind, reason) in T.COMPANION_FILES.items():
        listing = git(upstream, "ls-tree", PINNED_COMMIT, "--", source).decode("utf-8").strip().splitlines()
        matches = [line for line in listing if line.split("\t", 1)[-1] == source]
        if not matches:
            raise ImportFailure(f"companion {source} is not tracked at {PINNED_COMMIT[:12]}")
        meta = matches[0].split("\t")[0].split()
        sources.append({"source": source, "mode": meta[0], "blob": meta[2]})
        seen.add(source)

    if len(seen) != len(sources):
        raise ImportFailure("duplicate source paths in the inventory")

    if len(sources) != 162:
        raise ImportFailure(
            f"expected 158 upstream files plus 4 companions, found {len(sources)}"
        )

    records: list[dict] = []
    generated: list[dict] = []
    keep: set[str] = set()
    adapter_records: list[tuple[str, str]] = []

    for entry in sources:
        source = entry["source"]
        raw = verify_tracked(upstream, source, entry["blob"], entry["mode"])
        target = target_for(source)
        kind = classification(source)
        data, transforms = transform_source(source, raw)
        mode = 0o755 if entry["mode"] == "100755" else 0o644
        if data == raw and not transforms:
            transforms = []
        digest = write_file(root, target, data, mode)
        keep.add(target)
        if is_byte_identical(source) and data != raw:
            raise ImportFailure(f"{source} is in the byte-identical set but was modified")
        records.append(
            {
                "source": source,
                "source_mode": entry["mode"],
                "source_blob": entry["blob"],
                "target": target,
                "target_sha256": digest,
                "classification": kind,
                "transforms": transforms,
                "entrypoint": None,
            }
        )
        if kind == "command":
            name = Path(source).parent.name
            adapter_records.append((name, data.decode("utf-8")))

    records_by_source = {record["source"]: record for record in records}

    for name, skill_text in sorted(adapter_records):
        if not re.fullmatch(r"[a-z0-9-]+", name):
            raise ImportFailure(f"skill directory {name!r} is not a valid command name")
        description = frontmatter_description(skill_text, name)
        metadata = frontmatter_adapter_metadata(skill_text)
        target = f"commands/generated/speckit.pstack.{name}.md"
        digest = write_file(root, target, adapter_text(name, description, metadata).encode("utf-8"))
        keep.add(target)
        generated.append(
            {
                "target": target,
                "sha256": digest,
                "generator": "tools/import_upstream.py:adapter",
                "source": f"{UPSTREAM_SUBTREE}/skills/{name}/SKILL.md",
                "command": f"speckit.pstack.{name}",
            }
        )
        records_by_source[f"{UPSTREAM_SUBTREE}/skills/{name}/SKILL.md"]["entrypoint"] = target

    removed = cleanup_stale(root, keep, manifest_file)
    adapter_source = generated[0]["source"]

    manifest = {
        "schema": 1,
        "repository": PINNED_REPOSITORY,
        "commit": PINNED_COMMIT,
        "version": EXTENSION_VERSION,
        "generated_by": "tools/import_upstream.py",
        "inventory": "tools/source-inventory.json",
        "counts": {
            "sources": len(records),
            "upstream": len(records) - len(T.COMPANION_FILES),
            "companions": len(T.COMPANION_FILES),
            "commands": len(generated),
            "playbooks": sum(
                1
                for record in records
                if record["target"].startswith("resources/skills/poteto-mode/playbooks/")
            ),
            "agents": sum(1 for record in records if record["classification"] == "agent"),
            "dormant_skills": sum(
                1
                for record in records
                if record["classification"] == "dormant" and record["target"].endswith("/SKILL.md")
            ),
            "principles": sum(
                1
                for record in records
                if record["target"].startswith("resources/skills/principle-")
                and record["target"].endswith("/SKILL.md")
            ),
        },
        "files": records,
        "generated": generated,
    }
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "sources": len(records),
                "adapters": len(generated),
                "removed": removed,
                "manifest": str(manifest_file),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ImportFailure as exc:
        print(f"import failed: {exc}", file=sys.stderr)
        sys.exit(1)
