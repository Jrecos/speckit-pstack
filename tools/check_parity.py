#!/usr/bin/env python3
"""Independent parity check for the packaged pstack extension.

Answers one question: does the installed tree contain everything the manifest
claims, and does every reachable path actually resolve? It reads the packaged
files and the manifest, and with `--upstream` it re-verifies the pinned Git tree
the import came from.

    python3 tools/check_parity.py --upstream /path/to/cursor-plugins

Exit 0 means every check passed; exit 1 prints each problem on its own line.
Mutations are supposed to fail this: any edited resource, a renamed command, a
broken link, or a forbidden host token is a failure, not a warning.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PINNED_COMMIT = "889ec4b68fa5aab0e867dad71ec3fdf386ae48f3"
REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_FILE = REPO_ROOT / "source-manifest.json"

EXPECTED = {
    "sources": 162,
    "upstream": 158,
    "companions": 4,
    "commands": 47,
    "playbooks": 23,
    "agents": 2,
    "dormant_skills": 3,
    "principles": 23,
}

# Classes whose text must be free of host-specific or vendor-specific calls.
SCANNED_CLASSES = {"command", "agent", "reference", "doc", "dormant", "script"}

# A vendored tree keeps upstream wording; nothing shipped as a resource does.
PROVENANCE_CLASSES = {"provenance", "host-manifest"}

# Files whose upstream behaviour is host-independent runtime code, or a real
# bot-author detection, where the token is part of the behaviour rather than a
# call into a host product.
TOKEN_EXEMPT_PREFIXES = (
    "resources/skills/poteto-mode/scripts/watch-pr/",
    "resources/skills/poteto-mode/scripts/orch/",
    "resources/skills/poteto-mode/scripts/bun.lock",
    "resources/skills/poteto-mode/scripts/package.json",
)

FORBIDDEN_TOKEN_REASONS = [
    (r"pstack_agent|pstack_models|pstack_history", "OMP pstack device dependency"),
    (r"\bupdate_state\b", "Cursor routine API"),
    (r"api2\.cursor\.sh", "Cursor automation endpoint"),
    (r"\.cursor/", "Cursor store path"),
    (r"cursor-team-kit", "Cursor plugin dependency"),
    (r"\bsubagent_type\b", "Cursor Task schema field"),
    (r"\brun_in_background\b", "Cursor Task schema field"),
    (r"\bSendToUser\b|secret-request", "Cursor chat secret channel"),
    (r'environment: "cloud"', "Cursor cloud worker"),
    (r"Cursor cloud|cursor cloud", "Cursor cloud worker"),
    (r"grok-4\.6-fast-xhigh|claude-fable-5-1-thinking-max|gpt-5\.6-sol-max|claude-opus-5-thinking-xhigh", "vendor model slug used as a default"),
    (r"`/goal`", "Cursor goal facility"),
    (r"git show origin/main:(?:\.specify/extensions/pstack|pstack/skills)", "installed resource read through target-repository Git"),
    (r"(?<![A-Za-z0-9_.-])/add-plugin\b", "Cursor plugin installation command"),
    (r"built-in [`/]?automate\b|Automations editor", "Cursor automation creation flow"),
    (r"plugins\.pstack|\"pstack\"\s*:\s*\{\s*\"enabled\"", "Cursor settings activation"),
]

# Config files the installer creates in the project from these templates; they do
# not exist in the repository, so path references to them are expected.
RUNTIME_CONFIG_PATHS = {
    ".specify/extensions/pstack/pstack-config.yml",
    ".specify/extensions/pstack/pstack-models-config.yml",
}

HAND_WRITTEN_FILES = {
    "commands/speckit.pstack.mode-refresh.md",
    "extension.yml",
    "README.md",
    "LICENSE",
    ".gitignore",
    ".extensionignore",
    "pstack-config.template.yml",
    "pstack-models-config.template.yml",
    "source-manifest.json",
    "REVIEW-REPORT.txt",
    "INTEGRATION-INVENTORY.txt",
    "commands/speckit.pstack.implement.md",
    "commands/speckit.pstack.roles.md",
    "commands/speckit.pstack.tasks.md",
    "commands/speckit.pstack.verify.md",
    "runtime/host-contract.md",
    "runtime/host-contexts.json",
    "runtime/pstack-native.py",
    "workflows/dispatch.yml",
    "resources/dependencies/create-skill.md",
    "assets/banner.png",
}

LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
BACKTICK_PATH_RE = re.compile(
    r"`((?:\.specify/extensions/pstack/|resources/|runtime/|workflows/|commands/)[A-Za-z0-9_./<>-]+)`"
)
SCRIPT_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])((?:[A-Za-z0-9_.-]+/)*scripts/[A-Za-z0-9_./-]*[A-Za-z0-9_-])"
)
COMMAND_REF_RE = re.compile(r"/speckit\.pstack\.([a-z0-9-]+)")
COMMAND_TOKEN_RE = re.compile(r"__SPECKIT_COMMAND_([A-Z0-9_]+)__")

problems: list[str] = []


def fail(message: str) -> None:
    problems.append(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest() -> dict:
    if not MANIFEST_FILE.is_file():
        raise SystemExit("source-manifest.json is missing; run tools/import_upstream.py")
    return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))


def is_text(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".json", ".yaml", ".yml", ".ts", ".mjs", ".js", ".sh", ".txt"}


def check_manifest_counts(manifest: dict) -> None:
    for key, expected in EXPECTED.items():
        actual = manifest["counts"].get(key)
        if actual != expected:
            fail(f"manifest counts.{key} is {actual}, expected {expected}")
    if manifest["commit"] != PINNED_COMMIT:
        fail(f"manifest commit is {manifest['commit']}, expected {PINNED_COMMIT}")


def check_targets(manifest: dict) -> None:
    for record in manifest["files"]:
        path = REPO_ROOT / record["target"]
        if not path.is_file():
            fail(f"missing target {record['target']} (from {record['source']})")
            continue
        digest = sha256(path.read_bytes())
        if digest != record["target_sha256"]:
            fail(f"{record['target']} was modified after import (hash mismatch)")
    for record in manifest["generated"]:
        path = REPO_ROOT / record["target"]
        if not path.is_file():
            fail(f"missing generated file {record['target']}")
            continue
        if sha256(path.read_bytes()) != record["sha256"]:
            fail(f"{record['target']} was edited by hand (hash mismatch)")
    commands = [record for record in manifest["files"] if record["classification"] == "command"]
    if len(commands) != EXPECTED["commands"]:
        fail(f"manifest lists {len(commands)} command skills, expected {EXPECTED['commands']}")
    for record in commands:
        if not record.get("entrypoint"):
            fail(f"{record['source']} has no generated adapter")
    adapters = sorted(path.name for path in (REPO_ROOT / "commands" / "generated").glob("*.md"))
    if len(adapters) != EXPECTED["commands"]:
        fail(f"commands/generated holds {len(adapters)} adapters, expected {EXPECTED['commands']}")


def check_extension_manifest(manifest: dict) -> None:
    text = (REPO_ROOT / "extension.yml").read_text(encoding="utf-8")
    registered = re.findall(r"^\s*-\s*name:\s*(speckit\.[a-z0-9.-]+)\s*$", text, re.MULTILINE)
    files = re.findall(r"^\s*file:\s*(\S+)\s*$", text, re.MULTILINE)
    if len(registered) != len(set(registered)):
        fail("extension.yml registers a duplicate command name")
    generated = {record["command"] for record in manifest["generated"]}
    missing = sorted(generated - set(registered))
    if missing:
        fail(f"extension.yml does not register {len(missing)} generated adapter(s): {missing[:5]}")
    for name, path in zip(registered, files):
        if not (REPO_ROOT / path).is_file():
            fail(f"extension.yml registers {name} -> {path}, which does not exist")
    if len(registered) != len(files):
        fail("extension.yml has a different number of command names and files")
    for entry in re.findall(r"^\s*-\s*name:\s*(\S+)\s*$", text, re.MULTILINE):
        if entry.startswith("speckit.") and entry not in registered:
            fail(f"extension.yml command {entry} does not match the registration pattern")
    if "repository: https://github.com/Jrecos/speckit-pstack" not in text:
        fail("extension.yml does not name the authoritative Jrecos/speckit-pstack repository")
    for event in ("before_specify", "before_plan", "before_tasks", "before_implement"):
        match = re.search(rf"^  {event}:\n((?:    .*\n)+)", text, re.MULTILINE)
        if not match:
            fail(f"extension.yml is missing hook {event}")
            continue
        block = match.group(1)
        if "command: speckit.pstack.mode-refresh" not in block:
            fail(f"extension.yml hook {event} does not call mode-refresh")
        if "optional: false" not in block:
            fail(f"extension.yml hook {event} is not mandatory while pstack is enabled")


def check_command_references(manifest: dict) -> None:
    registered = set(re.findall(r"speckit\.pstack\.[a-z0-9-]+", (REPO_ROOT / "extension.yml").read_text(encoding="utf-8")))
    for path in sorted((REPO_ROOT / "commands").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for token in sorted(set(COMMAND_TOKEN_RE.findall(text))):
            # __SPECKIT_COMMAND_PSTACK_ROLES__ resolves to /speckit.pstack.roles:
            # the host joins the lower-cased segments with its own separator.
            name = "speckit." + token.lower().replace("_", ".")
            if name not in registered:
                fail(f"{path.relative_to(REPO_ROOT)} references {token}, which is not a registered command ({name})")
        for name in sorted(set(COMMAND_REF_RE.findall(text))):
            full = f"speckit.pstack.{name}"
            if full not in registered:
                fail(f"{path.relative_to(REPO_ROOT)} references /{full}, which is not registered")


def check_token_scan(manifest: dict) -> None:
    for record in manifest["files"]:
        if record["classification"] not in SCANNED_CLASSES:
            continue
        if record["target"].startswith(TOKEN_EXEMPT_PREFIXES):
            continue
        path = REPO_ROOT / record["target"]
        if not path.is_file() or not is_text(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern, reason in FORBIDDEN_TOKEN_REASONS:
            for match in re.finditer(pattern, text):
                line = text[: match.start()].count("\n") + 1
                fail(
                    f"{record['target']}:{line}: {reason} ({match.group(0)!r}) is not translated"
                )
                break


def resolve_reference(source_file: Path, target: str) -> bool:
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return True
    clean = target.split("#", 1)[0]
    if not clean or "<" in clean or "*" in clean:
        return True
    # Runtime config files, placeholder links (`url`), and template
    # interpolations (`${url}`) are not repository paths.
    if clean in RUNTIME_CONFIG_PATHS or not any(ch in clean for ch in "./"):
        return True
    if any(token in clean for token in ("$", "{", "}")):
        return True
    if clean.startswith(".specify/extensions/pstack/"):
        return (REPO_ROOT / clean[len(".specify/extensions/pstack/") :]).exists()
    if clean.startswith("/"):
        return True
    return (source_file.parent / clean).exists()


def check_reference_closure(manifest: dict) -> None:
    """Resolve links and path references inside runnable resources.

    Provenance and host-manifest copies are vendored archives kept byte-identical
    for attribution; their links point at the upstream repository layout, so they
    are deliberately not part of runnable closure.
    """
    for record in manifest["files"]:
        if record["classification"] in PROVENANCE_CLASSES:
            continue
        path = REPO_ROOT / record["target"]
        if not path.is_file() or not is_text(path):
            continue
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(REPO_ROOT))
        for link in sorted(set(LINK_RE.findall(text))):
            if not resolve_reference(path, link):
                fail(f"{rel}: link {link!r} does not resolve")
        for candidate in sorted(set(BACKTICK_PATH_RE.findall(text))):
            if candidate.endswith("/") and (REPO_ROOT / candidate).is_dir():
                continue
            if not resolve_reference(path, candidate):
                fail(f"{rel}: path reference {candidate!r} does not resolve")
        for literal in re.findall(r"`([^`\n]+)`", text):
            for script in sorted(set(SCRIPT_PATH_RE.findall(literal))):
                if not script.startswith(".specify/extensions/pstack/"):
                    fail(f"{rel}: runnable script reference {script!r} is not an installed path")
                elif not resolve_reference(path, script):
                    fail(f"{rel}: script reference {script!r} does not resolve at that exact path")


def check_accounting(manifest: dict) -> None:
    accounted = {record["target"] for record in manifest["files"]}
    accounted |= {record["target"] for record in manifest["generated"]}
    accounted |= HAND_WRITTEN_FILES
    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(REPO_ROOT)
        rel = str(relative)
        if (
            rel == ".git"
            or rel.startswith((".git/", "tools/", ".audit/", ".venv/"))
            or any(part in {"node_modules", "__pycache__"} for part in relative.parts)
            or path.suffix == ".pyc"
        ):
            continue
        if rel in accounted:
            continue
        fail(f"{rel} is neither imported, generated, nor a known hand-written file")


def check_upstream(upstream: Path, manifest: dict) -> None:
    def git(*args: str) -> str:
        result = subprocess.run(["git", "-C", str(upstream), *args], capture_output=True, check=False)
        if result.returncode != 0:
            raise SystemExit(f"git {' '.join(args)} failed: {result.stderr.decode().strip()}")
        return result.stdout.decode("utf-8")

    for record in manifest["files"]:
        source = record["source"]
        listing = [
            line for line in git("ls-tree", PINNED_COMMIT, "--", source).splitlines()
            if line.split("\t", 1)[-1] == source
        ]
        if not listing:
            fail(f"upstream {source} is not tracked at {PINNED_COMMIT[:12]}")
            continue
        blob = listing[0].split("\t")[0].split()[2]
        if blob != record["source_blob"]:
            fail(f"upstream {source} blob {blob} differs from the manifest's {record['source_blob']}")
    tracked = set(record["source"] for record in manifest["files"])
    if len(tracked) != EXPECTED["sources"]:
        fail(f"manifest covers {len(tracked)} sources, expected {EXPECTED['sources']}")


def check_manifest_reasons(manifest: dict) -> None:
    for record in manifest["files"]:
        for transform in record["transforms"]:
            if not transform.get("reason"):
                fail(f"{record['target']}: transform {transform.get('op')} has no reason")
        source = record["source"]
        if source.startswith("pstack/") and record["classification"] == "provenance":
            if record["transforms"]:
                fail(f"{record['target']}: provenance copies must stay upstream-identical")


def load_role_labels() -> tuple[str, ...]:
    """Read the role labels out of the runtime helper, the single source of truth."""
    text = (REPO_ROOT / "runtime" / "pstack-native.py").read_text(encoding="utf-8")
    block = re.search(r"ROLE_LABELS = \((.*?)\n\)", text, re.S)
    if not block:
        fail("runtime/pstack-native.py no longer declares ROLE_LABELS")
        return ()
    return tuple(re.findall(r'"([^"]+)"', block.group(1)))


def check_role_labels() -> None:
    labels = load_role_labels()
    if len(labels) != 17:
        fail(f"runtime declares {len(labels)} role labels, expected 17")
    contract = (REPO_ROOT / "runtime" / "host-contract.md").read_text(encoding="utf-8")
    for label in labels:
        if label not in contract:
            fail(f"role {label!r} has no caller: the shared host contract never names it")
    try:
        template = json.loads((REPO_ROOT / "pstack-models-config.template.yml").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"pstack-models-config.template.yml is not JSON-as-YAML: {exc}")
        return
    roles = template.get("roles", {})
    if sorted(roles) != sorted(labels):
        fail("the role map template's roles do not match the runtime's 17 labels")
    for role, models in roles.items():
        if not isinstance(models, list) or not models:
            fail(f"template role {role!r} has no selector")
    if not template.get("pool"):
        fail("template pool is empty; no selector would validate")
    if "dispatch" in template:
        fail("the role map template still declares a dispatch settings block")


def check_workload_role_callers() -> None:
    """Every workload role must have a real caller, not just a table row."""
    callers = {
        "resources/skills/poteto-mode/playbooks/feature.md": "feature, refactoring",
        "resources/skills/poteto-mode/playbooks/refactoring.md": "feature, refactoring",
        "resources/skills/poteto-mode/playbooks/bug-fix.md": "bug-fix",
        "resources/skills/poteto-mode/playbooks/perf-issue.md": "perf-issue",
        "resources/skills/poteto-mode/playbooks/hillclimb.md": "hillclimb",
        "resources/skills/architect/SKILL.md": "architect runners",
        "resources/skills/swarm/SKILL.md": "swarm workers",
        "resources/skills/how/SKILL.md": "how explorer",
        "resources/skills/why/SKILL.md": "why investigators",
        "resources/skills/reflect/SKILL.md": "reflect tooling",
        "resources/skills/arena/SKILL.md": "arena runners",
        "resources/skills/interrogate/SKILL.md": "interrogate reviewers",
    }
    for target, role in callers.items():
        path = REPO_ROOT / target
        if not path.is_file():
            fail(f"{target} is missing, so role {role!r} has no caller")
            continue
        if f"role `{role}`" not in path.read_text(encoding="utf-8"):
            fail(f"{target} does not name role `{role}`")


def check_skill_name_resolution() -> None:
    labels = load_role_labels()  # also proves the helper parsed before we trust it
    del labels
    packaged = {
        path.parent.name
        for path in (REPO_ROOT / "resources" / "skills").glob("*/SKILL.md")
    }
    dependencies = {
        path.stem for path in (REPO_ROOT / "resources" / "dependencies").glob("*.md")
    }
    contract = (REPO_ROOT / "runtime" / "host-contract.md").read_text(encoding="utf-8")
    if "resources/skills/<name>/SKILL.md" not in contract:
        fail("host-contract.md no longer states how a bare skill name resolves")
    contracts = [REPO_ROOT / "resources" / "skills", REPO_ROOT / "commands"]
    for root in contracts:
        for path in sorted(root.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            for name in sorted(set(re.findall(r"`/([a-z][a-z0-9-]+)`", text))):
                if name not in packaged and name not in dependencies:
                    fail(
                        f"{path.relative_to(REPO_ROOT)} names `/{name}`, which is neither a "
                        f"packaged skill nor a packaged dependency reference"
                    )


def require_markers(text: str, markers: tuple[str, ...], what: str) -> None:
    for marker in markers:
        if marker not in text:
            fail(f"{what} is missing {marker!r}")


def load_dispatch_request_keys() -> tuple[str, ...]:
    """Read the request keys out of the runtime helper, the single source of truth."""
    text = (REPO_ROOT / "runtime" / "pstack-native.py").read_text(encoding="utf-8")
    block = re.search(r"DISPATCH_REQUEST_KEYS = \((.*?)\)", text, re.S)
    if not block:
        fail("runtime/pstack-native.py no longer declares DISPATCH_REQUEST_KEYS")
        return ()
    return tuple(re.findall(r'"([^"]+)"', block.group(1)))


def check_dispatch_contract() -> None:
    workflow = (REPO_ROOT / "workflows" / "dispatch.yml").read_text(encoding="utf-8")
    required_workflow = (
        "dispatch-preflight",
        "dispatch-report-check",
        "{{ steps.preflight.output.data.integration }}",
        "{{ steps.preflight.output.data.model }}",
        "{{ steps.preflight.output.data.prompt }}",
        "PSTACK_DISPATCH_REQUEST",
        "timeout: 1200",
    )
    for marker in required_workflow:
        if marker not in workflow:
            fail(f"workflows/dispatch.yml is missing {marker!r}")
    if re.search(r"^inputs:", workflow, re.MULTILINE) or "inputs." in workflow:
        fail("workflows/dispatch.yml still has an independent input channel")
    if "PSTACK_REPORT_FILE" in workflow:
        fail("workflows/dispatch.yml still has the stale independent report-path channel")
    shell_runs = re.findall(r"^\s+run:\s*(.+)$", workflow, re.MULTILINE)
    expected_runs = [
        "python3 .specify/extensions/pstack/runtime/pstack-native.py dispatch-preflight",
        "python3 .specify/extensions/pstack/runtime/pstack-native.py dispatch-report-check",
    ]
    if shell_runs != expected_runs:
        fail(f"dispatch workflow shell commands are not the two fixed helper calls: {shell_runs}")

    expected_keys = ("integration", "role", "index", "model_source", "model", "prompt_file", "report_file")
    keys = load_dispatch_request_keys()
    if keys != expected_keys:
        fail(f"the runtime dispatch request keys are {keys}, expected the role-first seven {expected_keys}")
    runtime = (REPO_ROOT / "runtime" / "pstack-native.py").read_text(encoding="utf-8")
    if re.search(r'add_argument\(\s*"--model"', runtime):
        fail("dispatch-request still accepts a raw --model argument")
    for marker in (
        '"--role"',
        '"--index"',
        '"--parent-model"',
        '"--race-model"',
        '"panel"',
        '"choose-one"',
        '"single"',
        "report_must_be_absent=True",
        "prompt.parent != report.parent",
    ):
        if marker not in runtime:
            fail(f"runtime dispatch preflight is missing {marker!r}")

    contract = (REPO_ROOT / "runtime" / "host-contract.md").read_text(encoding="utf-8")
    for key in ("verdict", "check", "evidence", "files", "reason", "result"):
        if f"`{key}`" not in contract:
            fail(f"host-contract.md does not document report key {key!r}")
    for marker in (
        "dispatch-request",
        "PSTACK_DISPATCH_REQUEST",
        "files` | path strings",
        "reason` | always a string",
        "revalidates the seven keys",
        "rejected for a single-selector role",
        "--parent-model",
        "--race-model",
        "Workload classifier",
    ):
        if marker not in contract:
            fail(f"host-contract.md is missing dispatch contract marker {marker!r}")
    for role in ("feature, refactoring", "bug-fix", "perf-issue", "hillclimb", "hardest tasks", "judgment and prose"):
        if f"| `{role}` |" not in contract:
            fail(f"the workload classifier does not route {role!r}")
    if "PSTACK_REPORT_FILE" in contract:
        fail("host-contract.md still documents the stale report-path environment variable")
    for rel in (
        "runtime/host-contract.md",
        "README.md",
        "pstack-models-config.template.yml",
        "pstack-config.template.yml",
        "commands/speckit.pstack.implement.md",
        "commands/speckit.pstack.roles.md",
        "resources/skills/setup-pstack/SKILL.md",
    ):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        if "timeout_seconds" in text:
            fail(f"{rel} still promises a dispatch timeout setting")

    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    for record in manifest["files"]:
        if record["classification"] != "command":
            continue
        text = (REPO_ROOT / record["target"]).read_text(encoding="utf-8")
        if "subagent" not in text and "dispatch" not in text:
            continue
        adapter = record.get("entrypoint")
        if not adapter:
            fail(f"{record['target']} delegates but has no adapter")
            continue
        adapter_body = (REPO_ROOT / adapter).read_text(encoding="utf-8")
        if "host-contract.md" not in adapter_body:
            fail(f"{adapter} delegates but does not load the host contract")

    contract_agent = REPO_ROOT / "resources" / "agents" / "poteto-agent.md"
    if not contract_agent.is_file():
        fail("the poteto worker contract is missing")
    else:
        agent_text = contract_agent.read_text(encoding="utf-8")
        if "poteto-agent.md" not in contract:
            fail("host-contract.md does not point workers at the poteto agent contract")
        if "Never edit `tasks.md`, never commit" in agent_text:
            fail("the universal worker contract still forbids lifecycle-owner work")
        for marker in ("`result`", "`files` may be empty", "`reason`"):
            if marker not in agent_text:
                fail(f"the universal worker contract is missing {marker!r}")


def check_task_write_contract() -> None:
    """Every task declares its writes, and one contract states that rule."""
    contract = (REPO_ROOT / "runtime" / "host-contract.md").read_text(encoding="utf-8")
    require_markers(
        contract,
        ("Every task declares its writes", "**Writes:** []", "control metadata"),
        "host-contract.md task writes rule",
    )
    tasks = (REPO_ROOT / "commands" / "speckit.pstack.tasks.md").read_text(encoding="utf-8")
    require_markers(
        tasks,
        ("Every task lists every file it will write", "**Writes:** []", "Disjointness is a parallel rule"),
        "the tasks command writes rule",
    )
    implement = (REPO_ROOT / "commands" / "speckit.pstack.implement.md").read_text(encoding="utf-8")
    require_markers(
        implement,
        ("workload classifier", "carries a `**Writes:**` line, parallel", "`[]` is the correct list", "control metadata"),
        "the implement command writes rule",
    )


def check_command_invocation_tokens() -> None:
    """A registered body names a sibling by id or token, never by one host's slash form."""
    manifest = REPO_ROOT / "extension.yml"
    surfaces = [(path, str(path.relative_to(REPO_ROOT))) for path in sorted((REPO_ROOT / "commands").rglob("*.md"))]
    surfaces.append((manifest, "extension.yml"))
    for path, rel in surfaces:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if rel == "extension.yml" and not line.strip().startswith("description:"):
                continue
            match = re.search(r"/speckit\.[a-z0-9.-]+", line)
            if match:
                fail(
                    f"{rel}:{number}: hard-coded {match.group(0)!r} is one host's invocation "
                    "form; name the command id or use a __SPECKIT_COMMAND_*__ token"
                )
    contract = (REPO_ROOT / "runtime" / "host-contract.md").read_text(encoding="utf-8")
    if "__SPECKIT_COMMAND_<NAME>__" not in contract:
        fail("host-contract.md does not state how a command body names a sibling command")



def check_mode_protocol() -> None:
    mode_path = REPO_ROOT / "resources" / "skills" / "poteto-mode" / "SKILL.md"
    mode = mode_path.read_text(encoding="utf-8")
    for invocation in ("mode on", "mode off", "mode status"):
        if invocation not in mode:
            fail(f"the mode resource never invokes `{invocation}`")
    for phrase in ("control-only", "natural-language opt-out", "without changing project files"):
        if phrase not in mode:
            fail(f"the mode resource does not state its argument protocol ({phrase!r})")
    for marker in (".ts", "principle-type-system-discipline", "typescript-best-practices/SKILL.md"):
        if marker not in mode:
            fail(f"the mode resource does not explicitly trigger TypeScript rule {marker!r}")

    adapter_path = REPO_ROOT / "commands" / "generated" / "speckit.pstack.poteto-mode.md"
    if not adapter_path.is_file():
        fail("the Poteto mode adapter is missing")
    else:
        adapter = adapter_path.read_text(encoding="utf-8")
        status_at = adapter.find("mode status")
        resource_at = adapter.find("poteto-mode/SKILL.md")
        if status_at < 0 or resource_at < 0 or status_at > resource_at:
            fail("the Poteto mode adapter reads its resource before proving readiness")
        for marker in (
            "extension.enabled",
            "extension.resources_present",
            "Parse `$ARGUMENTS` before reading",
            "load no resource",
        ):
            if marker not in adapter:
                fail(f"the Poteto mode adapter is missing readiness marker {marker!r}")

    refresh = (REPO_ROOT / "commands" / "speckit.pstack.mode-refresh.md").read_text(encoding="utf-8")
    opt_out_at = refresh.find("natural-language Poteto opt-out")
    status_at = refresh.find("mode status")
    resource_at = refresh.find("poteto-mode/SKILL.md")
    if min(opt_out_at, status_at, resource_at) < 0 or not opt_out_at < status_at < resource_at:
        fail("mode-refresh does not check session opt-out and readiness before reading resources")
    if "project_mode.ready" not in refresh:
        fail("mode-refresh does not require project_mode.ready")
    contract = (REPO_ROOT / "runtime" / "host-contract.md").read_text(encoding="utf-8")
    for marker in (
        ".specify/extensions/pstack/runtime/pstack-native.py mode status",
        ".specify/extensions/pstack/resources/skills/poteto-mode/SKILL.md",
        "does not make OMP intercept unrelated commands globally",
    ):
        if marker not in contract:
            fail(f"host-contract.md is missing mode bootstrap marker {marker!r}")
    runtime = (REPO_ROOT / "runtime" / "pstack-native.py").read_text(encoding="utf-8")
    if "Before doing any task in this project, follow this sequence in order:" not in runtime:
        fail("the managed mode block is not an unconditional per-task bootstrap")


def check_native_adaptations() -> None:
    typescript = REPO_ROOT / "commands" / "generated" / "speckit.pstack.typescript-best-practices.md"
    if not typescript.is_file():
        fail("the TypeScript adapter is missing")
    else:
        text = typescript.read_text(encoding="utf-8")
        for marker in ('"**/*.ts"', '"**/*.tsx"', "disable-model-invocation: true"):
            if marker not in text:
                fail(f"the TypeScript adapter is missing metadata {marker!r}")

    extension_text = (REPO_ROOT / "extension.yml").read_text(encoding="utf-8")
    registered = set(re.findall(r"speckit\.pstack\.([a-z0-9-]+)", extension_text))
    guides = REPO_ROOT / "resources" / "docs" / "guide"
    for path in sorted(guides.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for name in sorted(
            set(re.findall(r"(?<![A-Za-z0-9.])/(?!speckit\.pstack\.)([a-z][a-z0-9-]+)", text))
        ):
            if name in registered or name in {"add-plugin", "automate", "deslop", "goal"}:
                fail(f"{path.relative_to(REPO_ROOT)} still uses active non-native command /{name}")
    setup_guide = (guides / "01-setup.md").read_text(encoding="utf-8")
    for role in load_role_labels():
        if role not in setup_guide:
            fail(f"the active setup guide does not require role {role!r}")

    benny_root = REPO_ROOT / "resources" / "automations" / "benny"
    setup_benny = (benny_root / "skills" / "setup-benny" / "SKILL.md").read_text(encoding="utf-8")
    for marker in (
        "scheduler",
        "run-once",
        "disabled",
        "server-side secret",
        "Slack",
        "forge",
    ):
        if marker not in setup_benny:
            fail(f"setup-benny does not state native scheduler requirement {marker!r}")
    benny_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(benny_root.rglob("*.md"))
    )
    for pattern in (r"built-in [`/]?automate\b", r"Automations editor", r"\.cursor/settings", r"plugins\.pstack"):
        if re.search(pattern, benny_text, re.IGNORECASE):
            fail(f"Benny still contains Cursor-only activation path {pattern!r}")

    implement = (REPO_ROOT / "commands" / "speckit.pstack.implement.md").read_text(encoding="utf-8")
    require_markers(
        implement,
        (
            "Sequential dispatch",
            "run-new --role",
            "swarm workers",
            "workload classifier",
            "dispatch-request",
            "--parent-model",
            "--race-model",
        ),
        "the implement command",
    )

    check_plan = REPO_ROOT / "resources" / "skills" / "poteto-mode" / "scripts" / "check-plan.mjs"
    plan_template = REPO_ROOT / "resources" / "skills" / "poteto-mode" / "playbooks" / "multi-phase-plan.md"
    check_text = check_plan.read_text(encoding="utf-8")
    template_text = plan_template.read_text(encoding="utf-8")
    if "PSTACK_LIVE_MODEL" not in check_text:
        fail("check-plan does not accept an optional concrete live-model pin")
    for marker in ("installed extension", "standing predicate"):
        if marker not in check_text or marker not in template_text:
            fail(f"check-plan and its template are not synchronized on {marker!r}")
    if "<resolved swarm workers model>" not in template_text:
        fail("the plan template does not require the author to replace its model placeholder")

    worktree_audit = (
        REPO_ROOT / "resources" / "skills" / "poteto-mode" / "scripts" / "worktree-audit.sh"
    ).read_text(encoding="utf-8")
    for marker in ('sub(/^worktree /, "")', "while IFS= read -r wt", "rg -F -0 -l"):
        if marker not in worktree_audit:
            fail(f"worktree audit is missing path-safe scan marker {marker!r}")

    for skill in ("how", "why", "reflect"):
        body = (REPO_ROOT / "resources" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        if "validated report's non-empty `result`" not in body:
            fail(f"{skill} does not consume the workflow report result")

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    arena = (REPO_ROOT / "resources" / "skills" / "arena" / "SKILL.md").read_text(encoding="utf-8")
    require_markers(arena, ("Spawn one read-only judge", "must never allocate the whole list"), "the arena cross-judge contract")
    if "never allocate the whole list" not in readme:
        fail("README.md does not state the arena choose-one contract")


def check_skill_location_contract() -> None:
    """A generated project skill has one discovered home, or the declared fallback."""
    contract = (REPO_ROOT / "runtime" / "host-contract.md").read_text(encoding="utf-8")
    require_markers(
        contract,
        ("skills_dirs", "skills_dir_fallback", "exactly one of them", "second editable copy"),
        "host-contract.md project skill location",
    )
    for rel in (
        "resources/skills/create-verification-skill/SKILL.md",
        "resources/skills/maintain-verification-skill/SKILL.md",
        "resources/skills/automate-me/SKILL.md",
        "resources/skills/setup-pstack/SKILL.md",
        "resources/dependencies/create-skill.md",
    ):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        if "skills_dirs" not in text:
            fail(f"{rel} does not resolve the project skill location from skills_dirs")
    if "link it there" in contract:
        fail("host-contract.md still tells a generator to link a duplicate skill")


def check_legacy_migration_contract() -> None:
    """Migration input is read once, and an applied migration is a no-op."""
    contract = (REPO_ROOT / "runtime" / "host-contract.md").read_text(encoding="utf-8")
    require_markers(contract, ("pristine", "byte-preserving no-op", "role-first"), "host-contract.md migration contract")
    setup = (REPO_ROOT / "resources" / "skills" / "setup-pstack" / "SKILL.md").read_text(encoding="utf-8")
    require_markers(
        setup,
        ("pristine", "byte-preserving no-op", "never run migration"),
        "setup-pstack migration contract",
    )
    template = (REPO_ROOT / "pstack-config.template.yml").read_text(encoding="utf-8")
    if "sync" in template:
        fail("the legacy config template still promises a roles sync")
    for stale in ("fallback dispatch config", "Consulted when a lane's pstack role is unconfigured"):
        if stale in template:
            fail(f"the legacy config template still claims a runtime fallback ({stale!r})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="check the packaged pstack tree")
    parser.add_argument("--upstream", help="checkout of the pinned repository to re-verify against")
    args = parser.parse_args(argv)

    manifest = load_manifest()
    manifest_checks = (
        check_manifest_counts,
        check_targets,
        check_extension_manifest,
        check_command_references,
        check_token_scan,
        check_reference_closure,
        check_accounting,
        check_manifest_reasons,
    )
    project_checks = (
        check_role_labels,
        check_skill_name_resolution,
        check_workload_role_callers,
        check_dispatch_contract,
        check_task_write_contract,
        check_command_invocation_tokens,
        check_skill_location_contract,
        check_legacy_migration_contract,
        check_mode_protocol,
        check_native_adaptations,
    )
    for check in manifest_checks:
        check(manifest)
    for check in project_checks:
        check()
    if args.upstream:
        check_upstream(Path(args.upstream).expanduser().resolve(), manifest)

    summary = {
        "checks_run": len(manifest_checks) + len(project_checks) + (1 if args.upstream else 0),
        "problems": len(problems),
        "sources": manifest["counts"]["sources"],
        "commands": manifest["counts"]["commands"],
        "playbooks": manifest["counts"]["playbooks"],
    }
    for problem in problems:
        print(problem)
    print(json.dumps(summary, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
