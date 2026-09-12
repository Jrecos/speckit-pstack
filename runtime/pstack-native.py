#!/usr/bin/env python3
"""Project-local runtime for the pstack Spec Kit extension.

Owns every fact a host needs that cannot be baked into a translated resource at
build time: the role map, role plans, capability reports, isolated run
directories, and the project mode block. Standard library only.

Run `pstack-native.py <command> --help` for the contract of one command. Every
command prints one JSON object on stdout. Failures print `{"error": ...}` on
stderr and exit non-zero, never a partial success.
"""

from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import json
import os
import re
import secrets
import sys
import stat
import time
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
CONFIG_NAME = "pstack-models-config.yml"
LEGACY_CONFIG_NAME = "pstack-config.yml"
HOST_CONTEXTS_NAME = "host-contexts.json"
MODE_START = "<!-- SPECKIT-PSTACK START -->"
MODE_END = "<!-- SPECKIT-PSTACK END -->"

# The 17 role labels, verbatim from upstream `setup-pstack`. Order is the
# upstream order and the order `config-init` writes.
ROLE_LABELS = (
    "feature, refactoring",
    "bug-fix",
    "perf-issue",
    "hillclimb",
    "judgment and prose",
    "hardest tasks",
    "how explorer",
    "how explainer",
    "why investigators",
    "why synthesizer",
    "reflect tooling",
    "reflect judgment, divergent, synthesizer",
    "arena runners",
    "arena cross-judge pool",
    "swarm workers",
    "architect runners",
    "interrogate reviewers",
)
PANEL_ROLES = frozenset({"arena runners", "architect runners", "interrogate reviewers"})
CHOOSE_ONE_ROLES = frozenset({"arena cross-judge pool"})
MULTI_SELECTOR_ROLES = PANEL_ROLES | CHOOSE_ONE_ROLES
INHERIT_ALIASES = frozenset({"inherit-parent", "auto"})

EXTENSION_DIR = Path(__file__).resolve().parent.parent
HOST_CONTEXTS_FILE = EXTENSION_DIR / "runtime" / HOST_CONTEXTS_NAME
CONFIG_TEMPLATE = EXTENSION_DIR / "pstack-models-config.template.yml"


class Failure(Exception):
    """A user-facing failure with a non-zero exit code."""

    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


# --------------------------------------------------------------------------
# paths and safe writes
# --------------------------------------------------------------------------


def project_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    override = os.environ.get("SPECIFY_INIT_DIR")
    if override:
        return Path(override).expanduser().resolve()
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".specify").is_dir():
            return candidate
    return current


def extension_dir(root: Path) -> Path:
    """Extension directory for this project, falling back to the running copy."""
    installed = root / ".specify" / "extensions" / "pstack"
    return installed if installed.is_dir() else EXTENSION_DIR


def checked_project_path(root: Path, path: Path, what: str) -> Path:
    """Return a lexical project path after rejecting escapes and symlinks."""
    resolved_root = root.resolve()
    candidate = Path(os.path.abspath(path))
    try:
        relative = candidate.relative_to(resolved_root)
    except ValueError:
        raise Failure(f"refusing to use a path outside the project root: {path} ({what})", 4) from None
    current = resolved_root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise Failure(f"refusing to use symlink {current} ({what})", 4)
    return candidate


def assert_writable_target(root: Path, path: Path, what: str) -> Path:
    """Reject a managed write that escapes the project or follows a symlink."""
    path = checked_project_path(root, path, what)
    if path.parent.exists() and not path.parent.is_dir():
        raise Failure(f"{path.parent} is not a directory for {what}", 4)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise Failure(f"cannot create {path.parent} for {what}: {exc}", 4) from exc
    return checked_project_path(root, path, what)


@contextmanager
def file_lock(path: Path, timeout: float = 5.0):
    """Hold a POSIX advisory lock without deleting or replacing its inode."""
    path.parent.mkdir(parents=True, exist_ok=True)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise Failure("pstack writes require POSIX O_NOFOLLOW support", 5)
    try:
        handle = os.open(path, os.O_CREAT | os.O_RDWR | nofollow, 0o600)
    except OSError as exc:
        raise Failure(f"cannot open regular lock {path} without following symlinks: {exc}", 5) from exc
    if not stat.S_ISREG(os.fstat(handle).st_mode):
        os.close(handle)
        raise Failure(f"lock path is not a regular file: {path}", 5)
    deadline = time.monotonic() + timeout
    locked = False
    try:
        while not locked:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN):
                    raise Failure(f"cannot lock {path}: {exc}", 5) from exc
                if time.monotonic() > deadline:
                    raise Failure(
                        f"could not acquire {path.name} within {timeout:g}s; "
                        "another pstack write is in progress",
                        5,
                    )
                time.sleep(0.05)
        yield
    finally:
        try:
            if locked:
                fcntl.flock(handle, fcntl.LOCK_UN)
        finally:
            os.close(handle)


class _Absent:
    """Expected state: the managed file must not exist yet."""

    def __repr__(self) -> str:  # pragma: no cover - diagnostics only
        return "ABSENT"


ABSENT = _Absent()


def hash_and_expect(content: bytes, existed: bool) -> str | _Absent:
    return hashlib.sha256(content).hexdigest() if existed else ABSENT


def expect_hash(path: Path) -> str | _Absent:
    """The expectation a caller derived from its own read of *path*."""
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ABSENT


def atomic_write(path: Path, data: bytes | str, expect: str | _Absent) -> str:
    """Replace *path* atomically with *data*, only when its state matches *expect*.

    `expect` is a sha256 of the bytes the caller read, or ABSENT when the caller
    saw no file. There is no "skip the check" mode: the compare runs inside the
    lock, so two writers that both saw an absent file cannot both create it, and a
    writer whose read is stale re-reads and fails instead of clobbering the other.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    with file_lock(path.with_name(f"{path.name}.lock")):
        exists = path.exists()
        current = path.read_bytes() if exists else b""
        actual = hashlib.sha256(current).hexdigest() if exists else ABSENT
        if isinstance(expect, _Absent):
            if not isinstance(actual, _Absent):
                raise Failure(
                    f"{path.name} appeared after it was read (now {actual[:12]}); re-read and retry",
                    5,
                )
        elif isinstance(actual, _Absent):
            raise Failure(
                f"{path.name} disappeared after it was read; re-read and retry",
                5,
            )
        elif actual != expect:
            raise Failure(
                f"{path.name} changed since it was read "
                f"(expected {expect[:12]}, found {actual[:12]}); re-read and retry",
                5,
            )
        fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
            if exists:
                tmp.chmod(path.stat().st_mode & 0o7777)
            os.replace(tmp, path)
        finally:
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass
    return digest


def read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        raise Failure(f"missing file: {path}", 3) from None


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise Failure(f"missing file: {path}", 3) from None
    except UnicodeDecodeError as exc:
        raise Failure(f"{path} is not valid UTF-8: {exc}", 3) from exc


# --------------------------------------------------------------------------
# config
# --------------------------------------------------------------------------


def config_path(root: Path) -> Path:
    return root / ".specify" / "extensions" / "pstack" / CONFIG_NAME


def load_host_contexts() -> dict:
    try:
        data = json.loads(read_text(HOST_CONTEXTS_FILE))
    except json.JSONDecodeError as exc:
        raise Failure(f"{HOST_CONTEXTS_FILE} is not valid JSON: {exc}", 2) from exc
    if not isinstance(data, dict):
        raise Failure(f"{HOST_CONTEXTS_FILE} must contain a JSON object", 2)
    agents = data.get("agents")
    capabilities = data.get("capabilities")
    if not isinstance(agents, dict):
        raise Failure(f"{HOST_CONTEXTS_FILE} has no 'agents' mapping", 2)
    if not isinstance(capabilities, dict) or not all(
        isinstance(name, str) and isinstance(spec, dict)
        for name, spec in capabilities.items()
    ):
        raise Failure(f"{HOST_CONTEXTS_FILE} has a malformed 'capabilities' mapping", 2)
    for name, spec in capabilities.items():
        if "reason" in spec and not isinstance(spec["reason"], str):
            raise Failure(f"{HOST_CONTEXTS_FILE} capability {name!r} has a non-string reason", 2)
    string_fields = (
        "name",
        "instruction_file",
        "skills_dir_evidence",
        "commands_dir",
        "skills_dir_note",
        "discovery_check",
    )
    for integration, entry in agents.items():
        if not isinstance(integration, str) or not isinstance(entry, dict):
            raise Failure(f"{HOST_CONTEXTS_FILE} has a malformed agent entry", 2)
        for field in string_fields:
            if field in entry and not isinstance(entry[field], str):
                raise Failure(
                    f"{HOST_CONTEXTS_FILE} agent {integration!r} has a non-string {field!r}",
                    2,
                )
        for field in ("skills_dirs", "cli"):
            value = entry.get(field, [])
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise Failure(
                    f"{HOST_CONTEXTS_FILE} agent {integration!r} has a malformed {field!r}",
                    2,
                )
        statuses = entry.get("capabilities", {})
        if not isinstance(statuses, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in statuses.items()
        ):
            raise Failure(
                f"{HOST_CONTEXTS_FILE} agent {integration!r} has malformed capabilities",
                2,
            )
    return data


def active_integration(root: Path, explicit: str | None) -> tuple[str | None, str]:
    """Return (integration key, source of the key)."""
    if explicit:
        return explicit, "argument"
    init_options = root / ".specify" / "init-options.json"
    if init_options.is_file():
        try:
            payload = json.loads(read_text(init_options))
        except (Failure, json.JSONDecodeError):
            return None, "init-options.json unreadable"
        ai = payload.get("ai") if isinstance(payload, dict) else None
        if isinstance(ai, str) and ai.strip():
            return ai.strip(), "init-options.json"
        return None, "init-options.json names no active integration"
    return None, "no .specify/init-options.json"


def default_config() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "pool": ["inherit-parent"],
        "roles": {role: ["inherit-parent"] for role in ROLE_LABELS},
        "parallel": {"max_workers": 3},
    }


def parse_config(text: str, source: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise Failure(
            f"{source} is not the JSON-as-YAML role map ({exc}); run config-init, "
            f"or migrate selectors from the project-local {LEGACY_CONFIG_NAME} input",
            2,
        ) from exc
    if not isinstance(data, dict):
        raise Failure(f"{source} must contain a JSON object", 2)
    return data


def is_pristine(data: dict) -> bool:
    """True when the map is still the untouched scaffold from config-init."""
    if data.get("pool") != ["inherit-parent"]:
        return False
    roles = data.get("roles")
    if not isinstance(roles, dict):
        return False
    return all(roles.get(role) == ["inherit-parent"] for role in ROLE_LABELS)


def validate_config(data: dict) -> dict:
    """Return the normalized config or fail with every problem it found."""
    problems: list[str] = []
    version = data.get("schema_version", SCHEMA_VERSION)
    if version != SCHEMA_VERSION:
        problems.append(f"schema_version {version!r} is not {SCHEMA_VERSION}")

    pool = data.get("pool", [])
    if not isinstance(pool, list) or not all(isinstance(item, str) for item in pool):
        problems.append("pool must be a list of selector strings")
        pool = []
    elif any(not item.strip() for item in pool):
        problems.append("pool contains a blank selector")
    pool = [item.strip() for item in pool if item.strip()]

    roles = data.get("roles")
    if not isinstance(roles, dict):
        problems.append("roles must be a mapping of role label to selector list")
        roles = {}
    else:
        for role in roles:
            if role not in ROLE_LABELS:
                problems.append(f"roles has unknown role {role!r}")
        for role in ROLE_LABELS:
            if role not in roles:
                problems.append(f"roles is missing {role!r}")

    approved = set(pool)
    resolved: dict[str, list[str]] = {}
    for role, models in roles.items():
        if role not in ROLE_LABELS:
            continue
        if not isinstance(models, list) or not all(isinstance(m, str) for m in models):
            problems.append(f"roles[{role!r}] must be a list of selector strings")
            continue
        if not models:
            problems.append(f"roles[{role!r}] is empty; set a selector or 'inherit-parent'")
        if role not in MULTI_SELECTOR_ROLES and len(models) > 1:
            problems.append(
                f"roles[{role!r}] has {len(models)} entries; "
                "a single-selector role accepts exactly one configured selector"
            )
        for model in models:
            if not model.strip():
                problems.append(f"roles[{role!r}] contains a blank selector")
            elif model.strip() not in approved:
                problems.append(f"roles[{role!r}] selector {model!r} is outside pool {sorted(pool)}")
        resolved[role] = [model.strip() for model in models if model.strip()]

    parallel = data.get("parallel", {})
    if not isinstance(parallel, dict):
        problems.append("parallel must be a mapping")
        parallel = {}
    max_workers = parallel.get("max_workers", 3)
    if not isinstance(max_workers, int) or isinstance(max_workers, bool) or max_workers < 1:
        problems.append("parallel.max_workers must be an integer >= 1")
        max_workers = 3


    if problems:
        raise Failure("invalid pstack role map:\n  - " + "\n  - ".join(problems), 2)

    normalized = dict(data)
    normalized["schema_version"] = SCHEMA_VERSION
    normalized["pool"] = list(pool)
    normalized["roles"] = resolved
    normalized["parallel"] = {**parallel, "max_workers": max_workers}
    return normalized


def read_config(root: Path) -> tuple[dict, str]:
    path = checked_project_path(root, config_path(root), "the pstack role map")
    raw = read_bytes(path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Failure(f"{path} is not valid UTF-8: {exc}", 3) from exc
    return validate_config(parse_config(text, str(path))), hashlib.sha256(raw).hexdigest()


def write_config(root: Path, data: dict, expect: str | _Absent) -> str:
    path = assert_writable_target(root, config_path(root), "the pstack role map")
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    return atomic_write(path, text, expect)


def cmd_config_init(args: argparse.Namespace) -> dict:
    root = project_root(args.project_root)
    path = config_path(root)
    existed = path.exists()
    if existed and not args.force:
        raise Failure(
            f"{path} already exists; refusing to overwrite the role map "
            f"(use --force to reset it, or config-set/config-save to edit it)",
            5,
        )
    expected = expect_hash(path) if existed else ABSENT
    assert_writable_target(root, path, "the pstack role map")
    template = read_text(CONFIG_TEMPLATE) if CONFIG_TEMPLATE.is_file() else None
    data = validate_config(parse_config(template, str(CONFIG_TEMPLATE))) if template else default_config()
    sha = write_config(root, data, expected)
    return {
        "config": str(path),
        "sha256": sha,
        "roles": len(ROLE_LABELS),
        "replaced_existing": existed,
    }


def cmd_config_show(args: argparse.Namespace) -> dict:
    root = project_root(args.project_root)
    path = config_path(root)
    if path.exists():
        data, sha = read_config(root)
    else:
        data, sha = default_config(), None
    return {
        "config": str(path),
        "sha256": sha,
        "pristine": is_pristine(data),
        "data": data,
    }


def cmd_config_set(args: argparse.Namespace) -> dict:
    root = project_root(args.project_root)
    if args.role not in ROLE_LABELS:
        raise Failure(f"unknown role {args.role!r}; one of: {', '.join(ROLE_LABELS)}", 2)
    try:
        models = json.loads(args.models)
    except json.JSONDecodeError as exc:
        raise Failure(f"--models must be a JSON array of selectors: {exc}", 2) from exc
    if not isinstance(models, list) or not all(isinstance(m, str) for m in models):
        raise Failure("--models must be a JSON array of selector strings", 2)
    path = config_path(root)
    if path.exists():
        data, expected = read_config(root)
    else:
        data, expected = default_config(), ABSENT
    if args.expect_hash is not None:
        current = expected if isinstance(expected, str) else ABSENT
        if args.expect_hash != current:
            raise Failure(
                f"role map changed since it was read "
                f"(expected {args.expect_hash[:12]}, found {current if isinstance(current, str) else 'absent'}); "
                f"re-read and retry",
                5,
            )
    data["roles"][args.role] = models
    normalized = validate_config(data)
    sha = write_config(root, normalized, expected)
    return {"config": str(config_path(root)), "role": args.role, "models": models, "sha256": sha}


def cmd_config_save(args: argparse.Namespace) -> dict:
    root = project_root(args.project_root)
    payload_text = sys.stdin.read() if args.models_file in (None, "-") else read_text(Path(args.models_file))
    payload = parse_config(payload_text, args.models_file or "stdin")
    if not isinstance(payload.get("roles"), dict) or not payload["roles"]:
        raise Failure("--models-file must contain a JSON object with a non-empty 'roles' mapping", 2)
    path = config_path(root)
    if path.exists():
        existing, expected = read_config(root)
    else:
        existing, expected = default_config(), ABSENT
    if args.expect_hash is not None:
        current = expected if isinstance(expected, str) else ABSENT
        if args.expect_hash != current:
            raise Failure(
                f"role map changed since it was read "
                f"(expected {args.expect_hash[:12]}, found {current if isinstance(current, str) else 'absent'}); "
                f"re-read and retry",
                5,
            )
    merged = dict(existing)
    for key, value in payload.items():
        if key == "roles":
            merged["roles"] = {**existing.get("roles", {}), **value}
        elif key == "parallel" and isinstance(value, dict):
            merged["parallel"] = {**existing.get("parallel", {}), **value}
        else:
            merged[key] = value
    normalized = validate_config(merged)
    sha = write_config(root, normalized, expected)
    return {"config": str(path), "sha256": sha, "roles": sorted(normalized["roles"])}


def cmd_config_migrate(args: argparse.Namespace) -> dict:
    """Seed two roles from the project-local legacy migration input."""
    root = project_root(args.project_root)
    path = config_path(root)
    exists = path.exists()
    expected: str | _Absent = ABSENT
    if exists:
        existing, expected = read_config(root)
    else:
        existing = default_config()

    verify = [selector.strip() for selector in args.verify.split(",") if selector.strip()]
    swarm = [selector.strip() for selector in args.swarm.split(",") if selector.strip()]
    if not verify and not swarm:
        raise Failure(
            f"pass --verify and/or --swarm with selectors from the project-local "
            f"{LEGACY_CONFIG_NAME} migration input, or run config-init when it holds none",
            2,
        )
    if len(swarm) > 1:
        raise Failure(
            "--swarm supplied more than one selector, but 'swarm workers' is "
            "a single-selector role",
            2,
        )

    target_verify = verify or ["inherit-parent"]
    target_swarm = swarm or ["inherit-parent"]
    pristine = is_pristine(existing)
    if exists and not pristine:
        already_applied = (
            existing["roles"]["interrogate reviewers"] == target_verify
            and existing["roles"]["swarm workers"] == target_swarm
            and (
                args.max_workers is None
                or existing["parallel"]["max_workers"] == args.max_workers
            )
        )
        if not already_applied:
            raise Failure(
                f"{path} already holds customized selectors, so config-migrate will not "
                f"overwrite them. Migrate the values with config-set, one role at a time.",
                5,
            )
        normalized = existing
    else:
        data = dict(existing)
        data["pool"] = list(existing["pool"])
        data["roles"] = {
            role: list(models) for role, models in existing["roles"].items()
        }
        data["parallel"] = dict(existing["parallel"])
        for selector in verify + swarm:
            if selector not in data["pool"]:
                data["pool"].append(selector)
        data["roles"]["interrogate reviewers"] = target_verify
        data["roles"]["swarm workers"] = target_swarm
        if args.max_workers is not None:
            data["parallel"]["max_workers"] = args.max_workers
        normalized = validate_config(data)

    changed = not exists or normalized != existing
    result = {
        "dry_run": not args.write,
        "changed": changed,
        "config": str(path),
        "legacy": f".specify/extensions/pstack/{LEGACY_CONFIG_NAME}",
        "replaces_pristine_map": exists and pristine,
        "data": normalized,
    }
    if not args.write:
        return result
    if not changed:
        result["sha256"] = expected
        return result
    result["sha256"] = write_config(root, normalized, expected)
    return result


# --------------------------------------------------------------------------
# role plans
# --------------------------------------------------------------------------


def role_kind(role: str) -> str:
    if role in PANEL_ROLES:
        return "panel"
    if role in CHOOSE_ONE_ROLES:
        return "choose-one"
    return "single"


def selector_index(
    role: str,
    selectors: list[str],
    index: object,
    *,
    require_multi_index: bool,
) -> int | None:
    kind = role_kind(role)
    if kind == "single":
        if index is not None:
            raise Failure(f"role {role!r} is single-selector; --index is invalid", 2)
        return None
    if index is None:
        if require_multi_index or (kind == "choose-one" and len(selectors) > 1):
            raise Failure(
                f"role {role!r} has {len(selectors)} configured selectors; "
                "pass their 1-based --index",
                2,
            )
        return 1 if kind == "choose-one" else None
    if not isinstance(index, int) or isinstance(index, bool) or not 1 <= index <= len(selectors):
        raise Failure(
            f"role {role!r} has {len(selectors)} configured selectors; index {index!r} is out of range",
            2,
        )
    return index


def role_plan(root: Path, role: str, index: int | None, integration: str | None) -> dict:
    if role not in ROLE_LABELS:
        raise Failure(f"unknown role {role!r}; one of: {', '.join(ROLE_LABELS)}", 2)
    data, _ = read_config(root)
    selectors = data["roles"].get(role, [])
    if not selectors:
        raise Failure(
            f"role {role!r} is unconfigured; run the pstack setup command or "
            f"`pstack-native.py config-set --role {role!r} --models '[...]'`",
            2,
        )
    kind = role_kind(role)
    legs = [
        {
            "index": i + 1 if kind != "single" else None,
            "model": None if selector in INHERIT_ALIASES else selector,
            "inherit": selector in INHERIT_ALIASES,
        }
        for i, selector in enumerate(selectors)
    ]
    selected_index = selector_index(
        role,
        selectors,
        index,
        require_multi_index=False,
    )
    selected = (
        legs[0]
        if kind == "single"
        else legs[selected_index - 1]
        if selected_index is not None
        else None
    )
    plan = {
        "integration": integration,
        "role": role,
        "kind": kind,
        "legs": [selected] if selected is not None else legs,
        "selected_index": selected["index"] if selected else None,
        "max_workers": data["parallel"]["max_workers"],
    }
    if selected is not None:
        plan["leg"] = selected
    return plan


def extension_state(root: Path) -> dict:
    """Report whether the Spec Kit registry has pstack installed and enabled."""
    registry = root / ".specify" / "extensions" / ".registry"
    state = {
        "registry_present": registry.is_file(),
        "installed": False,
        "enabled": False,
        "version": None,
    }
    if not registry.is_file():
        return state
    try:
        data = json.loads(read_text(registry))
    except (Failure, json.JSONDecodeError):
        state["reason"] = "registry is unreadable; treat the extension as unregistered"
        return state
    if not isinstance(data, dict) or not isinstance(data.get("extensions"), dict):
        state["reason"] = "registry has a malformed 'extensions' mapping"
        return state
    if "pstack" not in data["extensions"]:
        state["reason"] = "registry has no pstack entry"
        return state
    entry = data["extensions"]["pstack"]
    if not isinstance(entry, dict):
        state["reason"] = "registry has a malformed pstack entry"
        return state
    enabled = entry.get("enabled", True)
    version = entry.get("version")
    if not isinstance(enabled, bool) or (
        version is not None and not isinstance(version, str)
    ):
        state["reason"] = "registry pstack metadata has invalid types"
        return state
    state["installed"] = True
    state["enabled"] = enabled
    state["version"] = version
    return state


def cmd_role_plan(args: argparse.Namespace) -> dict:
    root = project_root(args.project_root)
    integration, source = active_integration(root, args.integration)
    plan = role_plan(root, args.role, args.index, integration)
    plan["integration_source"] = source
    if args.dispatch == "cli":
        if not integration:
            raise Failure(
                f"CLI dispatch needs an active integration ({source}); "
                f"pass --integration or run `specify integration`",
                3,
            )
        leg = plan.get("leg")
        if leg is None:
            raise Failure(
                f"CLI dispatch resolves one {args.role!r} selector; pass --index",
                3,
            )
        if leg["inherit"]:
            if not args.parent_model or not args.parent_model.strip():
                raise Failure(
                    "selector is an inherit-parent alias and CLI dispatch needs the concrete "
                    "parent model; pass --parent-model <id> (native subagent dispatch omits the "
                    "model instead, which is the correct path for aliases)",
                    3,
                )
            parent_model = args.parent_model.strip()
            if parent_model.casefold() in INHERIT_ALIASES or any(
                ord(char) < 32 or ord(char) == 127 for char in parent_model
            ):
                raise Failure("--parent-model must be a concrete model id", 3)
            leg["model"] = parent_model
            leg["inherit"] = False
            leg["resolved_from"] = "parent-model"
        elif args.parent_model is not None:
            raise Failure("--parent-model is only valid for an inheritance alias", 3)
        plan["dispatch"] = "cli"
    else:
        if args.parent_model is not None:
            raise Failure("--parent-model is only valid with --dispatch cli", 3)
        plan["dispatch"] = "native"
    return plan


# --------------------------------------------------------------------------
# capabilities
# --------------------------------------------------------------------------


def cmd_capability_report(args: argparse.Namespace) -> dict:
    root = project_root(args.project_root)
    contexts = load_host_contexts()
    integration, source = active_integration(root, args.integration)
    agents = contexts.get("agents", {})
    entry = agents.get(integration) if integration else None
    report: dict = {
        "project_root": str(root),
        "integration": integration,
        "integration_source": source,
        "capabilities": {},
    }
    capabilities: dict[str, dict] = report["capabilities"]
    if not isinstance(entry, dict):
        reason = (
            "unknown Spec Kit integration; pstack runs invocation-only, "
            "mode on writes nothing"
        )
        for name in contexts.get("capabilities", {}):
            capabilities[name] = {"status": "unavailable", "reason": reason}
        report["invocation_only"] = True
        return report

    from shutil import which

    declared = contexts.get("capabilities", {})
    statuses = entry.get("capabilities", {})
    for name, spec in declared.items():
        capabilities[name] = {
            "status": statuses.get(name, "unavailable"),
            "reason": statuses.get(f"{name}_reason") or spec.get("reason", ""),
        }

    cli_names = entry.get("cli", [])
    found = [name for name in cli_names if which(name)]
    capabilities["cli"] = {
        "status": "available" if found else "unavailable",
        "reason": f"found {', '.join(found)}" if found else f"none of {', '.join(cli_names)} on PATH",
    }
    forge = [name for name in ("gh", "origin") if which(name)]
    capabilities["forge"] = {
        "status": "available" if forge else "unavailable",
        "reason": f"found {', '.join(forge)}" if forge else "neither gh nor origin on PATH",
    }
    instruction = entry.get("instruction_file")
    capabilities["project_context"] = {
        "status": "available" if instruction and (root / instruction).exists() else "degraded",
        "reason": (
            f"{instruction} present"
            if instruction and (root / instruction).exists()
            else f"{instruction or 'no instruction file'} not present yet; mode on creates it"
        ),
    }
    report["paths"] = cmd_paths(args)
    return report


# --------------------------------------------------------------------------
# runs
# --------------------------------------------------------------------------


def slugify(value: str) -> str:
    keep = [c if c.isalnum() else "-" for c in value.lower()]
    slug = "".join(keep).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "leg"




def cmd_run_new(args: argparse.Namespace) -> dict:
    root = project_root(args.project_root)
    integration, _ = active_integration(root, args.integration)
    plan = role_plan(root, args.role, args.index, integration)
    kind = plan["kind"]
    if args.legs is not None and args.legs < 1:
        raise Failure("--legs must be >= 1", 2)
    if kind != "single" and args.legs is not None:
        raise Failure(
            f"--legs only repeats a single-selector role; {args.role!r} is {kind}",
            2,
        )
    if kind == "single":
        count = args.legs or 1
        allocations = [(ordinal, plan["leg"]) for ordinal in range(1, count + 1)]
    else:
        legs = [plan["leg"]] if "leg" in plan else plan["legs"]
        allocations = list(enumerate(legs, start=1))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_token = secrets.token_hex(3)
    label = slugify(args.label) if args.label else slugify(args.role)
    run_dir = checked_project_path(
        root,
        root / ".specify" / "pstack" / "runs" / f"{stamp}-{run_token}-{label}",
        "run directory",
    )
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise Failure(f"cannot create run directory {run_dir}: {exc}", 4) from exc
    checked_project_path(root, run_dir, "run directory")
    if not run_dir.is_dir():
        raise Failure(f"run path is not a directory: {run_dir}", 4)
    out_legs = []
    for ordinal, leg in allocations:
        path_number = leg["index"] if leg["index"] is not None else ordinal
        stem = f"{label}-leg{path_number}"
        prompt_file = run_dir / f"{stem}-prompt.md"
        report_file = run_dir / f"{stem}-report.json"
        out_legs.append(
            {
                "ordinal": ordinal,
                "index": leg["index"],
                "model": leg["model"],
                "inherit": leg["inherit"],
                "prompt_file": str(prompt_file),
                "report_file": str(report_file),
            }
        )
    return {
        "run_dir": str(run_dir),
        "role": args.role,
        "kind": kind,
        "integration": integration,
        "max_workers": plan["max_workers"],
        "legs": out_legs,
    }


# --------------------------------------------------------------------------
# mode
# --------------------------------------------------------------------------


def mode_block_bytes(instruction_file: str) -> bytes:
    lines = [
        MODE_START,
        "## pstack Poteto mode (project bootstrap)",
        "",
        "This block is a bootstrap instruction, not proof that pstack is active.",
        "Before doing any task in this project, follow this sequence in order:",
        "",
        "1. If this session has already processed a natural-language Poteto opt-out or",
        "   `/speckit.pstack.poteto-mode off`, stop. Do not run the helper or reload mode.",
        "2. If `.specify/extensions/pstack/runtime/pstack-native.py` is absent, this block",
        "   is inert. Do not improvise or read another copy of the mode.",
        "3. Run `python3 .specify/extensions/pstack/runtime/pstack-native.py mode status`.",
        "   Do not read the mode resource before this check.",
        "4. Parse the JSON and continue only when `project_mode.ready` is exactly `true`.",
        "   Any command failure, malformed output, disabled registry entry, missing resource,",
        "   or false readiness makes this block inert for the task.",
        "5. Read `.specify/extensions/pstack/runtime/host-contract.md`, then read",
        "   `.specify/extensions/pstack/resources/skills/poteto-mode/SKILL.md` in full.",
        "6. Match the task to a playbook, then open that playbook before work starts.",
        "",
        f"This block is stored in `{instruction_file}`. Restore an inert installation with",
        "`specify extension enable pstack` or `specify extension add pstack`.",
        "",
        "Project bootstrap is removed by `/speckit.pstack.poteto-mode off`. Invocation-only",
        "mode (`/speckit.pstack.poteto-mode <task>`) needs no project block.",
        MODE_END,
    ]
    return "\n".join(lines).encode("utf-8")


def find_block(content: bytes, where: str) -> tuple[int, int] | None:
    """Return the byte span of the managed block, or None when it is absent."""
    start_marker = MODE_START.encode("utf-8")
    end_marker = MODE_END.encode("utf-8")
    starts = [index for index in range(len(content)) if content.startswith(start_marker, index)]
    ends = [index for index in range(len(content)) if content.startswith(end_marker, index)]
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        raise Failure(
            f"{where} has malformed pstack mode markers "
            f"({len(starts)} start, {len(ends)} end); fix the file by hand and retry",
            4,
        )
    return starts[0], ends[0] + len(end_marker)


def instruction_path(root: Path, contexts: dict, integration: str | None, explicit: str | None) -> tuple[Path, str]:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_absolute():
            path = root / path
        return checked_project_path(root, path, "the mode instruction file"), "argument"
    entry = contexts["agents"].get(integration) if integration else None
    if not isinstance(entry, dict) or not entry.get("instruction_file"):
        raise Failure(
            f"no project instruction file is known for integration {integration!r}; "
            f"mode on is invocation-only here. Add the block to your host's instruction file "
            f"by hand, or pass --instruction-file.",
            3,
        )
    path = checked_project_path(root, root / entry["instruction_file"], "the mode instruction file")
    return path, "host-contexts.json"


def cmd_mode(args: argparse.Namespace) -> dict:
    root = project_root(args.project_root)
    contexts = load_host_contexts()
    integration, source = active_integration(root, args.integration)
    entry = contexts["agents"].get(integration) if integration else None
    unmapped_status = (
        args.action == "status"
        and not args.instruction_file
        and (not isinstance(entry, dict) or not entry.get("instruction_file"))
    )
    if unmapped_status:
        path = None
        path_source = "unavailable"
        block = b""
    else:
        path, path_source = instruction_path(root, contexts, integration, args.instruction_file)
        relative = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        block = mode_block_bytes(relative)
    state = extension_state(root)
    mode_resource = checked_project_path(
        root,
        root / ".specify" / "extensions" / "pstack" / "resources" / "skills" / "poteto-mode" / "SKILL.md",
        "the installed Poteto mode resource",
    )
    resources_present = mode_resource.is_file()

    if args.action == "status":
        present = path.is_file() if path else False
        content = read_bytes(path) if present and path else b""
        span = find_block(content, str(path)) if present and path else None
        block_present = span is not None
        session = {"observable": False, "requested": args.session}
        if args.session != "unknown":
            session = {
                "observable": True,
                "active": args.session == "active",
                "reason": "reported by the running command for this session only",
            }
        return {
            "integration": integration,
            "integration_source": source,
            "instruction_file": str(path) if path else None,
            "instruction_file_source": path_source,
            "instruction_file_present": present,
            "extension": {**state, "resources_present": resources_present},
            "project_mode": {
                "active": block_present,
                "extension_enabled": state["enabled"],
                "ready": block_present and state["enabled"] and resources_present,
                "reason": (
                    "integration has no mapped instruction file"
                    if path is None
                    else "block present, extension enabled, and mode resource present"
                    if block_present and state["enabled"] and resources_present
                    else "no block"
                    if not block_present
                    else "block present but the registry reports pstack disabled"
                    if not state["enabled"]
                    else "block present but the installed mode resource is missing"
                ),
            },
            "session": session,
            "note": (
                "project mode is the managed block's presence plus an enabled registry entry; "
                "there is no second state flag. Another running session keeps whatever it "
                "already loaded until it next reads the instruction file."
            ),
        }

    if args.action == "on":
        if not state["installed"]:
            raise Failure(
                "pstack is not in .specify/extensions/.registry, so a project block would "
                f"point at nothing ({state.get('reason', 'no registry entry')}). Run "
                "`specify extension add pstack` first, or stay invocation-only.",
                5,
            )
        if not state["enabled"]:
            raise Failure(
                "the registry reports pstack disabled, so a project block would load a "
                "disabled extension. Run `specify extension enable pstack` first.",
                5,
            )
        if not resources_present:
            raise Failure(
                f"the registry reports pstack enabled, but {mode_resource} is missing. "
                "Repair the installation with `specify extension add pstack --force`.",
                5,
            )
        assert_writable_target(root, path, "the mode block")
        present = path.is_file()
        content = read_bytes(path) if present else b""
        expect = hash_and_expect(content, present)
        if find_block(content, str(path)) is not None:
            return {
                "changed": False,
                "reason": "mode block already present",
                "instruction_file": str(path),
                "sha256": expect,
            }
        # The leading newline belongs to the managed span so removal is exact.
        new_content = content + b"\n" + block + b"\n"
        sha = atomic_write(path, new_content, expect)
        return {"changed": True, "instruction_file": str(path), "sha256": sha}

    # action == "off"
    if not path.is_file():
        return {"changed": False, "reason": "no instruction file", "instruction_file": str(path)}
    assert_writable_target(root, path, "the mode block")
    content = read_bytes(path)
    expect = hashlib.sha256(content).hexdigest()
    span = find_block(content, str(path))
    if span is None:
        return {
            "changed": False,
            "reason": "no mode block present",
            "instruction_file": str(path),
            "sha256": expect,
        }
    start, end = span
    if start > 0 and content[start - 1 : start] == b"\n":
        start -= 1
    if content[end : end + 1] == b"\n":
        end += 1
    sha = atomic_write(path, content[:start] + content[end:], expect)
    return {"changed": True, "instruction_file": str(path), "sha256": sha}


REPORT_KEYS = ("verdict", "check", "evidence", "files", "reason")
REPORT_OPTIONAL_KEYS = ("result",)
PASS_VERDICTS = {"pass", "pass+notes", "pass with notes"}
FAIL_VERDICTS = {"fail", "issues", "blocked"}
ALL_VERDICTS = PASS_VERDICTS | FAIL_VERDICTS
DISPATCH_REQUEST_ENV = "PSTACK_DISPATCH_REQUEST"
DISPATCH_REQUEST_KEYS = (
    "integration",
    "role",
    "index",
    "model_source",
    "model",
    "prompt_file",
    "report_file",
)
MODEL_SOURCES = frozenset({"configured", "parent", "swarm-race"})


def extract_report_object(text: str) -> tuple[dict | None, str | None]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"the report is not a JSON document: {exc}"
    if not isinstance(payload, dict):
        return None, "the top-level JSON value is not an object"
    return payload, None


def path_argument(root: Path, value: str, what: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return checked_project_path(root, path, what)


def validate_report(root: Path, path: Path) -> dict:
    """Validate one worker report. This is the only verdict boundary."""
    path = checked_project_path(root, path, "worker report")
    if not path.is_file():
        raise Failure(f"report is missing: {path}", 6)
    text = read_text(path)
    problems: list[str] = []
    payload, parse_problem = extract_report_object(text)
    if payload is None:
        raise Failure(f"report {path} is malformed: {parse_problem}", 6)
    allowed = set(REPORT_KEYS) | set(REPORT_OPTIONAL_KEYS)
    extra = sorted(set(payload) - allowed)
    if extra:
        problems.append(f"unexpected keys: {', '.join(extra)}")
    for key in REPORT_KEYS:
        if key not in payload:
            problems.append(f"missing key {key!r}")
    verdict = payload.get("verdict")
    normalized = verdict.strip().lower() if isinstance(verdict, str) else ""
    if not normalized:
        problems.append("verdict must be a non-empty string")
    elif normalized not in ALL_VERDICTS:
        problems.append(f"verdict {verdict!r} is not one of {sorted(ALL_VERDICTS)}")
    for key in ("check", "evidence"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{key} must be a non-empty string")
    files = payload.get("files")
    if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
        problems.append("files must be a list of path strings")
    reason = payload.get("reason")
    if not isinstance(reason, str):
        problems.append("reason must be a string")
    elif normalized in FAIL_VERDICTS and not reason.strip():
        problems.append("reason must be non-empty for a failing verdict")
    if "result" in payload:
        result_text = payload["result"]
        if not isinstance(result_text, str) or not result_text.strip():
            problems.append("result must be a non-empty string when present")

    ok = not problems and normalized in PASS_VERDICTS
    result = {
        "report": str(path),
        "verdict": normalized or None,
        "ok": ok,
        "problems": problems,
    }
    if not ok:
        raise Failure(json.dumps(result, ensure_ascii=False), 6)
    return result


def cmd_report_check(args: argparse.Namespace) -> dict:
    root = project_root(args.project_root)
    return validate_report(root, path_argument(root, args.report, "worker report"))


def clean_dispatch_value(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise Failure(f"dispatch request {name!r} must be a non-empty string", 2)
    if value != value.strip():
        raise Failure(f"dispatch request {name!r} must not have surrounding whitespace", 2)
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise Failure(f"dispatch request {name!r} contains a control character", 2)
    return value

def dispatch_selector(data: dict, role: str, index: object) -> tuple[str, int | None]:
    if role not in ROLE_LABELS:
        raise Failure(f"unknown dispatch role {role!r}; one of: {', '.join(ROLE_LABELS)}", 2)
    selectors = data["roles"][role]
    selected_index = selector_index(
        role,
        selectors,
        index,
        require_multi_index=True,
    )
    offset = selected_index - 1 if selected_index is not None else 0
    return selectors[offset], selected_index


def concrete_dispatch_model(value: object, name: str) -> str:
    model = clean_dispatch_value(value, name)
    if model.casefold() in INHERIT_ALIASES:
        raise Failure(f"dispatch request {name!r} must be a concrete model id", 2)
    return model


def validate_dispatch_request(
    root: Path,
    payload: object,
    *,
    report_must_be_absent: bool,
) -> tuple[dict, Path, Path]:
    if not isinstance(payload, dict):
        raise Failure("dispatch request must be a JSON object", 2)
    missing = [key for key in DISPATCH_REQUEST_KEYS if key not in payload]
    extra = sorted(set(payload) - set(DISPATCH_REQUEST_KEYS))
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing keys: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected keys: {', '.join(extra)}")
        raise Failure("invalid dispatch request (" + "; ".join(details) + ")", 2)

    integration = clean_dispatch_value(payload["integration"], "integration")
    role = clean_dispatch_value(payload["role"], "role")
    model_source = clean_dispatch_value(payload["model_source"], "model_source")
    model = concrete_dispatch_model(payload["model"], "model")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", integration):
        raise Failure(f"dispatch integration {integration!r} is not a valid Spec Kit integration key", 2)
    if model_source not in MODEL_SOURCES:
        raise Failure(
            f"dispatch model_source {model_source!r} is not one of {sorted(MODEL_SOURCES)}",
            2,
        )

    data, _ = read_config(root)
    selector, selected_index = dispatch_selector(data, role, payload["index"])
    if model_source == "configured":
        if model not in data["pool"]:
            raise Failure(f"dispatch model {model!r} is outside the approved pool", 2)
        if selector in INHERIT_ALIASES:
            raise Failure(
                f"role {role!r} index {selected_index!r} inherits the parent model; "
                "model_source must be 'parent'",
                2,
            )
        if model != selector:
            owners = [
                configured_role
                for configured_role, selectors in data["roles"].items()
                if model in selectors
            ]
            if owners:
                raise Failure(
                    f"dispatch model {model!r} belongs to configured role(s) "
                    f"{', '.join(repr(owner) for owner in owners)}, not this role binding",
                    2,
                )
            raise Failure(
                f"stale dispatch binding for role {role!r} index {selected_index!r}: "
                f"configured model is {selector!r}, not {model!r}",
                2,
            )
    elif model_source == "parent":
        if selector not in INHERIT_ALIASES:
            raise Failure(
                f"role {role!r} index {selected_index!r} is configured as {selector!r}, "
                "not an inheritance alias",
                2,
            )
    else:
        if role != "swarm workers":
            raise Failure("model_source 'swarm-race' is only valid for role 'swarm workers'", 2)
        if model not in data["pool"]:
            raise Failure(f"swarm race model {model!r} is outside the approved pool", 2)

    prompt_value = clean_dispatch_value(payload["prompt_file"], "prompt_file")
    report_value = clean_dispatch_value(payload["report_file"], "report_file")
    prompt = path_argument(root, prompt_value, "dispatch prompt")
    report = path_argument(root, report_value, "dispatch report")
    runs = checked_project_path(root, root / ".specify" / "pstack" / "runs", "dispatch runs directory")
    if not runs.is_dir():
        raise Failure(f"dispatch runs directory is missing: {runs}; allocate it with run-new", 4)
    for path, label in ((prompt, "prompt_file"), (report, "report_file")):
        try:
            relative = path.relative_to(runs)
        except ValueError:
            raise Failure(f"dispatch {label} must be under {runs}: {path}", 4) from None
        if len(relative.parts) != 2:
            raise Failure(
                f"dispatch {label} must be inside one direct run directory under {runs}: {path}",
                4,
            )
    if prompt == report:
        raise Failure("dispatch prompt_file and report_file must be different paths", 4)
    if prompt.parent != report.parent:
        raise Failure("dispatch prompt_file and report_file must belong to the same run directory", 4)
    if not prompt.is_file():
        raise Failure(f"dispatch prompt is missing: {prompt}", 4)
    prompt_text = read_text(prompt)
    if not prompt_text.strip():
        raise Failure(f"dispatch prompt is empty: {prompt}", 4)
    if report_must_be_absent and report.exists():
        raise Failure(f"dispatch report already exists; allocate a fresh run instead: {report}", 4)

    request = {
        "integration": integration,
        "role": role,
        "index": selected_index,
        "model_source": model_source,
        "model": model,
        "prompt_file": str(prompt),
        "report_file": str(report),
    }
    return request, prompt, report


def dispatch_request_from_env(root: Path, *, report_must_be_absent: bool) -> tuple[dict, Path, Path]:
    raw = os.environ.get(DISPATCH_REQUEST_ENV)
    if raw is None:
        raise Failure(f"{DISPATCH_REQUEST_ENV} is not set", 2)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise Failure(f"{DISPATCH_REQUEST_ENV} is not valid JSON: {exc}", 2) from exc
    return validate_dispatch_request(root, payload, report_must_be_absent=report_must_be_absent)


def cmd_dispatch_request(args: argparse.Namespace) -> dict:
    root = project_root(args.project_root)
    role = clean_dispatch_value(args.role, "role")
    data, _ = read_config(root)
    selector, selected_index = dispatch_selector(data, role, args.index)
    if args.parent_model is not None and args.race_model is not None:
        raise Failure("--parent-model and --race-model are mutually exclusive", 2)
    if args.parent_model is not None:
        model_source = "parent"
        model = args.parent_model
    elif args.race_model is not None:
        model_source = "swarm-race"
        model = args.race_model
    else:
        if selector in INHERIT_ALIASES:
            raise Failure(
                f"role {role!r} index {selected_index!r} inherits the parent model; "
                "pass --parent-model with its concrete id",
                2,
            )
        model_source = "configured"
        model = selector
    payload = {
        "integration": args.dispatch_integration,
        "role": role,
        "index": selected_index,
        "model_source": model_source,
        "model": model,
        "prompt_file": args.prompt_file,
        "report_file": args.report_file,
    }
    request, _, _ = validate_dispatch_request(root, payload, report_must_be_absent=True)
    return request


def cmd_dispatch_preflight(args: argparse.Namespace) -> dict:
    root = project_root(args.project_root)
    request, prompt, report = dispatch_request_from_env(root, report_must_be_absent=True)
    brief = read_text(prompt).rstrip()
    report_literal = json.dumps(str(report), ensure_ascii=False)
    worker_prompt = (
        f"{brief}\n\n"
        "## Native dispatch completion contract\n\n"
        "Complete the brief above. The brief alone decides whether you may edit, commit, push, "
        "or own lifecycle work; this workflow adds no blanket restriction.\n\n"
        f"Before finishing, write exactly one JSON object to {report_literal}. "
        "The required keys are verdict, check, evidence, files, and reason. "
        "verdict is pass, pass+notes, pass with notes, fail, issues, or blocked. "
        "check and evidence are non-empty strings. files is a list of path strings and may be "
        "empty for read-only work. reason is always a string and must be non-empty for failure. "
        "For prose, research, or any complete response that does not fit the metadata, add the "
        "optional result key with a non-empty string. Do not add other keys."
    )
    return {
        "integration": request["integration"],
        "model": request["model"],
        "prompt": worker_prompt,
    }


def cmd_dispatch_report_check(args: argparse.Namespace) -> dict:
    root = project_root(args.project_root)
    _, _, report = dispatch_request_from_env(root, report_must_be_absent=False)
    return validate_report(root, report)


# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------


def cmd_paths(args: argparse.Namespace) -> dict:
    root = project_root(getattr(args, "project_root", None))
    contexts = load_host_contexts()
    integration, source = active_integration(root, getattr(args, "integration", None))
    entry = contexts["agents"].get(integration) if integration else None
    installed = extension_dir(root)
    instruction = entry.get("instruction_file") if isinstance(entry, dict) else None
    skills_dirs = entry.get("skills_dirs", []) if isinstance(entry, dict) else []
    return {
        "project_root": str(root),
        "integration": integration,
        "integration_source": source,
        "extension_dir": str(installed),
        "resources_dir": str(installed / "resources"),
        "instruction_file": str(root / instruction) if instruction else None,
        "skills_dirs": [str(root / candidate) for candidate in skills_dirs],
        "skills_dir_evidence": (
            entry.get("skills_dir_evidence") if isinstance(entry, dict) else None
        ),
        "skills_dir_fallback": str(root / ".specify" / "pstack" / "skills"),
        "skills_dir_note": (
            entry.get("skills_dir_note")
            if isinstance(entry, dict)
            else "unknown integration; write project skills under .specify/pstack/skills/ and register them explicitly"
        ),
        "discovery_check": (
            entry.get("discovery_check")
            if isinstance(entry, dict)
            else "unknown host: prove discovery in a session before claiming it"
        ),
        "extension": extension_state(root),
        "runs_dir": str(root / ".specify" / "pstack" / "runs"),
        "workflows": str(installed / "workflows" / "dispatch.yml"),
    }


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="pstack native runtime for Spec Kit projects")
    parser.add_argument("--project-root", help="project root (default: nearest ancestor with .specify/)")
    parser.add_argument("--integration", help="Spec Kit integration key (default: .specify/init-options.json)")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("config-init", help="create the JSON role map when absent")
    init.add_argument("--force", action="store_true", help="reset an existing role map to the template")
    init.set_defaults(func=cmd_config_init)

    show = sub.add_parser("config-show", help="validate and print the role map")
    show.set_defaults(func=cmd_config_show)

    setter = sub.add_parser("config-set", help="set one role's selectors atomically")
    setter.add_argument("--role", required=True)
    setter.add_argument("--models", required=True, help="JSON array, e.g. '[\"inherit-parent\"]'")
    setter.add_argument("--expect-hash", help="fail unless the current role map has this sha256")
    setter.set_defaults(func=cmd_config_set)

    save = sub.add_parser("config-save", help="merge a full role map from JSON on stdin or --models-file")
    save.add_argument("--models-file", help="path to a JSON role map; default stdin")
    save.add_argument("--expect-hash", help="fail unless the current role map has this sha256")
    save.set_defaults(func=cmd_config_save)

    migrate = sub.add_parser(
        "config-migrate",
        help=f"seed the JSON map from project-local {LEGACY_CONFIG_NAME} migration input",
    )
    migrate.add_argument("--verify", default="", help="migration-input roles.verify selectors, comma separated")
    migrate.add_argument("--swarm", default="", help="migration-input roles.swarm selectors, comma separated")
    migrate.add_argument("--max-workers", type=int, help="migration-input parallel.max_workers")
    migrate.add_argument("--write", action="store_true", help="persist; without it this is a dry run")
    migrate.set_defaults(func=cmd_config_migrate)

    plan = sub.add_parser("role-plan", help="resolve one role to its worker legs")
    plan.add_argument("--role", required=True)
    plan.add_argument("--index", type=int, help="1-based configured selector index")
    plan.add_argument("--dispatch", choices=("native", "cli"), default="native")
    plan.add_argument("--parent-model", help="concrete current model, required for alias legs on cli dispatch")
    plan.set_defaults(func=cmd_role_plan)

    caps = sub.add_parser("capability-report", help="report host mappings and local CLI availability")
    caps.set_defaults(func=cmd_capability_report)

    run = sub.add_parser("run-new", help="allocate an isolated run directory with per-leg paths")
    run.add_argument("--role", required=True)
    run.add_argument("--index", type=int, help="1-based configured selector index")
    run.add_argument("--legs", type=int, help="repeat count for a single-selector role")
    run.add_argument("--label", help="run label, default the role slug")
    run.set_defaults(func=cmd_run_new)
    request = sub.add_parser("dispatch-request", help="validate and print one role-bound dispatch request")
    request.add_argument("--integration", dest="dispatch_integration", required=True)
    request.add_argument("--role", required=True)
    request.add_argument("--index", type=int, help="1-based configured selector index")
    request.add_argument("--parent-model", help="concrete parent model for an inheritance alias")
    request.add_argument("--race-model", help="approved concrete model for a swarm race arm")
    request.add_argument("--prompt-file", required=True)
    request.add_argument("--report-file", required=True)
    request.set_defaults(func=cmd_dispatch_request)

    preflight = sub.add_parser("dispatch-preflight", help="validate PSTACK_DISPATCH_REQUEST for the workflow")
    preflight.set_defaults(func=cmd_dispatch_preflight)

    dispatched_report = sub.add_parser(
        "dispatch-report-check",
        help="validate the exact report named by PSTACK_DISPATCH_REQUEST",
    )
    dispatched_report.set_defaults(func=cmd_dispatch_report_check)


    mode = sub.add_parser("mode", help="manage the project mode block")
    mode.add_argument("action", choices=("on", "off", "status"))
    mode.add_argument("--instruction-file", help="override the mapped project instruction file")
    mode.add_argument(
        "--session",
        choices=("active", "inactive", "unknown"),
        default="unknown",
        help="what the running command knows about the current session's mode",
    )
    mode.set_defaults(func=cmd_mode)

    paths = sub.add_parser("paths", help="print resolved host paths")
    paths.set_defaults(func=cmd_paths)

    report = sub.add_parser("report-check", help="validate one worker report's verdict")
    report.add_argument("--report", required=True, help="path to the report file")
    report.set_defaults(func=cmd_report_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        payload = args.func(args)
    except Failure as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return exc.code
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
