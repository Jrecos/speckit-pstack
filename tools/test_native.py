#!/usr/bin/env python3
"""Behavioral regressions for the project-local pstack CLI."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]


class NativeRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pstack-native-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "project"
        self.extension = self.root / ".specify/extensions/pstack"
        shutil.copytree(PACKAGE, self.extension, ignore=shutil.ignore_patterns(".git", ".audit", "__pycache__", "node_modules"))
        (self.root / ".specify/init-options.json").write_text(json.dumps({"integration": "omp"}))
        self.registry = self.root / ".specify/extensions/.registry"
        self.registry.write_text(json.dumps({"schema_version": "1.0", "extensions": {"pstack": {"enabled": True, "version": "0.2.0"}}}))
        self.cli = [sys.executable, str(self.extension / "runtime/pstack-native.py"), "--project-root", str(self.root), "--integration", "omp"]
        self.call("config-init")
        self.config = self.extension / "pstack-models-config.yml"

    def call(self, *args, ok=True, stdin=None, env=None):
        result = subprocess.run(
            self.cli + list(args),
            input=stdin,
            text=True,
            capture_output=True,
            timeout=15,
            env=env,
        )
        self.assertEqual(result.returncode == 0, ok, (args, result.stdout, result.stderr))
        self.assertNotIn("Traceback", result.stderr)
        return json.loads(result.stdout) if ok else result

    def test_host_name_does_not_prove_live_browser_access(self):
        report = self.call("capability-report")
        self.assertNotEqual(report["capabilities"]["browser"]["status"], "available")

    def test_malformed_host_and_registry_metadata_fail_closed(self):
        contexts = self.extension / "runtime/host-contexts.json"
        valid_contexts = contexts.read_bytes()
        malformed_contexts = (
            "[",
            json.dumps({"agents": [], "capabilities": {}}),
            json.dumps({"agents": {"omp": {"cli": "omp"}}, "capabilities": {}}),
            json.dumps({"agents": {"omp": {}}, "capabilities": {"browser": []}}),
        )
        for payload in malformed_contexts:
            contexts.write_text(payload)
            self.call("capability-report", ok=False)
        contexts.write_bytes(valid_contexts)

        self.call("mode", "on")
        malformed_registries = (
            "[]",
            json.dumps({"extensions": []}),
            json.dumps({"extensions": {"pstack": {"enabled": "yes"}}}),
        )
        for payload in malformed_registries:
            self.registry.write_text(payload)
            status = self.call("mode", "status")
            self.assertFalse(status["extension"]["installed"])
            self.assertFalse(status["project_mode"]["ready"])
            self.call("mode", "on", ok=False)

    def test_mode_preserves_unmanaged_bytes_and_disabled_state(self):
        target = self.root / "AGENTS.md"
        for original in (b"", b"no newline", b"\r\noriginal\r\n", b"\n\n\noriginal\n\n\n"):
            target.write_bytes(original)
            self.call("mode", "on")
            active = target.read_bytes()
            self.assertFalse(self.call("mode", "on")["changed"])
            self.call("mode", "status")
            self.assertEqual(target.read_bytes(), active)
            self.call("mode", "off")
            self.assertEqual(target.read_bytes(), original)
            self.assertFalse(self.call("mode", "off")["changed"])
        self.call("mode", "on")
        registry = json.loads(self.registry.read_text())
        registry["extensions"]["pstack"]["enabled"] = False
        self.registry.write_text(json.dumps(registry))
        self.assertFalse(self.call("mode", "status")["project_mode"]["ready"])
        self.call("mode", "on", ok=False)
        self.call("mode", "off")

    def test_project_writes_and_reports_cannot_escape(self):
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        sentinel = outside / "AGENTS.md"
        sentinel.write_bytes(b"untouched\r\n")
        (self.root / "linked").symlink_to(outside, target_is_directory=True)
        for target in ("../outside/AGENTS.md", "linked/AGENTS.md", str(sentinel)):
            self.call("mode", "on", "--instruction-file", target, ok=False)
            self.call("mode", "off", "--instruction-file", target, ok=False)
        self.assertEqual(sentinel.read_bytes(), b"untouched\r\n")
        report = outside / "report.json"
        report.write_text(json.dumps(self.report(files=["artifact.txt"])))
        for target in ("../outside/report.json", "linked/report.json", str(report)):
            self.call("report-check", "--report", target, ok=False)
        lock = self.config.with_name(self.config.name + ".lock")
        if lock.exists():
            lock.unlink()
        lock.symlink_to(outside / "must-not-be-created")
        before = self.config.read_bytes()
        self.call("config-set", "--role", "bug-fix", "--models", '["inherit-parent"]', ok=False)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse((outside / "must-not-be-created").exists())
        runs = self.root / ".specify/pstack/runs"
        runs.parent.mkdir(parents=True, exist_ok=True)
        runs.symlink_to(outside, target_is_directory=True)
        self.call("run-new", "--role", "bug-fix", ok=False)
        self.assertEqual(sorted(p.name for p in outside.iterdir()), ["AGENTS.md", "report.json"])

    def test_role_kinds_indices_and_rejected_updates(self):
        shown = self.call("config-show")
        self.assertTrue(shown["pristine"])
        self.assertNotIn("dispatch", shown["data"])
        self.call(
            "config-save",
            stdin=json.dumps(
                {
                    "pool": ["inherit-parent", "auto"],
                    "roles": {"bug-fix": ["inherit-parent"]},
                }
            ),
        )
        self.call(
            "config-set",
            "--role",
            "arena runners",
            "--models",
            '["inherit-parent", "auto", "inherit-parent"]',
        )
        plan = self.call("role-plan", "--role", "arena runners")
        self.assertEqual(plan["kind"], "panel")
        self.assertEqual([leg["index"] for leg in plan["legs"]], [1, 2, 3])
        self.assertNotIn("timeout_seconds", plan)
        self.call("role-plan", "--role", "arena runners", "--dispatch", "cli", ok=False)
        resolved = self.call(
            "role-plan",
            "--role",
            "arena runners",
            "--index",
            "2",
            "--dispatch",
            "cli",
            "--parent-model",
            "provider/model",
        )
        self.assertEqual(resolved["leg"]["model"], "provider/model")
        self.assertEqual([leg["index"] for leg in resolved["legs"]], [2])

        panel_run = self.call("run-new", "--role", "arena runners")
        self.assertEqual(panel_run["kind"], "panel")
        self.assertNotIn("timeout_seconds", panel_run)
        self.assertEqual([leg["index"] for leg in panel_run["legs"]], [1, 2, 3])
        indexed_run = self.call("run-new", "--role", "arena runners", "--index", "2")
        self.assertEqual([leg["index"] for leg in indexed_run["legs"]], [2])
        self.assertEqual([leg["ordinal"] for leg in indexed_run["legs"]], [1])
        self.call("run-new", "--role", "arena runners", "--legs", "1", ok=False)

        self.call(
            "config-set",
            "--role",
            "arena cross-judge pool",
            "--models",
            '["inherit-parent", "auto"]',
        )
        self.call("role-plan", "--role", "arena cross-judge pool", ok=False)
        judge = self.call(
            "role-plan",
            "--role",
            "arena cross-judge pool",
            "--index",
            "2",
        )
        self.assertEqual(judge["kind"], "choose-one")
        self.assertEqual([leg["index"] for leg in judge["legs"]], [2])
        self.call("run-new", "--role", "arena cross-judge pool", ok=False)
        judge_run = self.call(
            "run-new",
            "--role",
            "arena cross-judge pool",
            "--index",
            "2",
        )
        self.assertEqual(judge_run["kind"], "choose-one")
        self.assertEqual([leg["index"] for leg in judge_run["legs"]], [2])
        request_keys = {
            "integration",
            "role",
            "index",
            "model_source",
            "model",
            "prompt_file",
            "report_file",
        }
        judge_leg = judge_run["legs"][0]
        Path(judge_leg["prompt_file"]).write_text("Choose the strongest candidate.")
        judge_request = self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "arena cross-judge pool",
            "--index",
            str(judge_leg["index"]),
            "--parent-model",
            "parent/live",
            "--prompt-file",
            judge_leg["prompt_file"],
            "--report-file",
            judge_leg["report_file"],
        )
        self.assertEqual(set(judge_request), request_keys)
        self.assertEqual(judge_request["index"], 2)
        self.assertEqual(judge_request["model_source"], "parent")
        self.call(
            "run-new",
            "--role",
            "arena cross-judge pool",
            "--index",
            "2",
            "--legs",
            "2",
            ok=False,
        )

        repeated = self.call("run-new", "--role", "bug-fix", "--legs", "2")
        self.assertEqual(repeated["kind"], "single")
        self.assertEqual([leg["index"] for leg in repeated["legs"]], [None, None])
        self.assertEqual([leg["ordinal"] for leg in repeated["legs"]], [1, 2])
        single_requests = []
        for leg in repeated["legs"]:
            Path(leg["prompt_file"]).write_text("Implement the assigned slice.")
            request = self.call(
                "dispatch-request",
                "--integration",
                "omp",
                "--role",
                "bug-fix",
                "--parent-model",
                "parent/live",
                "--prompt-file",
                leg["prompt_file"],
                "--report-file",
                leg["report_file"],
            )
            self.assertEqual(set(request), request_keys)
            single_requests.append(request)
        self.assertEqual([request["index"] for request in single_requests], [None, None])
        self.call("run-new", "--role", "bug-fix", "--index", "1", ok=False)

        before = self.config.read_bytes()
        for models in ('[""]', '[" "]', '["outside-pool/model"]', '[]', '[true]'):
            self.call("config-set", "--role", "bug-fix", "--models", models, ok=False)
            self.assertEqual(self.config.read_bytes(), before)
        self.call(
            "config-set",
            "--role",
            "swarm workers",
            "--models",
            '["inherit-parent", "auto"]',
            ok=False,
        )
        self.assertEqual(self.config.read_bytes(), before)
        self.call(
            "config-set",
            "--role",
            "bug-fix",
            "--models",
            '["auto"]',
            "--expect-hash",
            "0" * 64,
            ok=False,
        )
        self.assertEqual(self.config.read_bytes(), before)
        for payload in (
            {"roles": {"bug-fix": 3}},
            {"roles": {"bug-fix": ["auto"]}, "parallel": []},
        ):
            self.call("config-save", stdin=json.dumps(payload), ok=False)
            self.assertEqual(self.config.read_bytes(), before)
        self.call(
            "config-save",
            stdin=json.dumps(
                {
                    "pool": ["provider/concrete"],
                    "roles": {"bug-fix": ["inherit-parent"]},
                }
            ),
            ok=False,
        )
        self.assertEqual(self.config.read_bytes(), before)
        self.config.unlink()
        self.call("config-save", stdin=json.dumps({"roles": {"bug-fix": 3}}), ok=False)
        self.assertFalse(self.config.exists())

    def test_config_hashes_original_bytes_and_writes_after_crlf_input(self):
        self.call("config-save", stdin=json.dumps({"pool": ["inherit-parent", "auto"], "roles": {"bug-fix": ["inherit-parent"]}}))
        import hashlib

        self.config.write_bytes(self.config.read_bytes().replace(b"\n", b"\r\n"))
        expected = hashlib.sha256(self.config.read_bytes()).hexdigest()
        self.assertEqual(self.call("config-show")["sha256"], expected)
        self.call("config-set", "--role", "bug-fix", "--models", '["auto"]', "--expect-hash", expected)
        self.assertEqual(self.call("config-show")["data"]["roles"]["bug-fix"], ["auto"])

    def test_config_show_exposes_an_absent_map_as_pristine(self):
        self.config.unlink()
        shown = self.call("config-show")
        self.assertTrue(shown["pristine"])
        self.assertIsNone(shown["sha256"])
        self.assertEqual(shown["data"]["roles"]["bug-fix"], ["inherit-parent"])

    def test_legacy_migration_is_persisted_idempotent_and_conflict_safe(self):
        data = json.loads(self.config.read_text())
        data["user_note"] = {"owner": "keep this metadata"}
        self.config.write_text(json.dumps(data))
        self.assertTrue(self.call("config-show")["pristine"])
        args = (
            "config-migrate",
            "--verify",
            "provider/reviewer",
            "--swarm",
            "provider/worker",
            "--max-workers",
            "2",
            "--write",
        )
        migrated = self.call(*args)
        self.assertTrue(migrated["changed"])
        persisted = self.call("config-show")
        self.assertFalse(persisted["pristine"])
        self.assertEqual(
            persisted["data"]["roles"]["interrogate reviewers"],
            ["provider/reviewer"],
        )
        self.assertEqual(
            persisted["data"]["roles"]["swarm workers"],
            ["provider/worker"],
        )
        self.assertEqual(persisted["data"]["parallel"]["max_workers"], 2)
        self.assertEqual(
            persisted["data"]["user_note"],
            {"owner": "keep this metadata"},
        )

        before = self.config.read_bytes()
        repeated = self.call(*args)
        self.assertFalse(repeated["changed"])
        self.assertEqual(self.config.read_bytes(), before)
        self.call(
            "config-migrate",
            "--verify",
            "different/model",
            "--swarm",
            "provider/worker",
            "--max-workers",
            "2",
            "--write",
            ok=False,
        )
        self.assertEqual(self.config.read_bytes(), before)

    def test_legacy_alias_migration_preserves_explicit_selection(self):
        self.call("config-migrate", "--swarm", "auto", "--write")
        plan = self.call("role-plan", "--role", "swarm workers")
        self.assertTrue(plan["leg"]["inherit"])
        self.assertIn("auto", self.call("config-show")["data"]["pool"])

    @staticmethod
    def report(**overrides):
        return {"verdict": "PASS", "check": "python3 inspect.py", "evidence": "Observed correct bytes", "files": [], "reason": "", **overrides}

    def test_readonly_reports_pass_but_missing_failed_or_malformed_reports_do_not(self):
        report = self.root / "report.json"
        self.call("report-check", "--report", str(report), ok=False)
        report.write_text(json.dumps(self.report()))
        self.assertTrue(self.call("report-check", "--report", str(report))["ok"])
        report.write_text(json.dumps(self.report(result="## Explanation\nThe file is read as UTF-8, then stripped.\n")))
        self.assertTrue(self.call("report-check", "--report", str(report))["ok"])
        for payload in (self.report(verdict="FAIL", reason="bytes differ"), self.report(evidence=""), self.report(files="artifact.txt"), self.report(reason=3), {"verdict": "PASS"}):
            report.write_text(json.dumps(payload))
            self.call("report-check", "--report", str(report), ok=False)
        report.write_text("broken JSON {")
        self.call("report-check", "--report", str(report), ok=False)
        report.write_text("```json\n" + json.dumps(self.report()) + "\n```\n")
        self.call("report-check", "--report", str(report), ok=False)

    def test_dispatch_request_is_role_bound_and_preflight_revalidates_it(self):
        self.call(
            "config-save",
            stdin=json.dumps(
                {
                    "pool": [
                        "inherit-parent",
                        "provider/configured",
                        "provider/arena",
                        "provider/race",
                        "provider/swarm",
                        "provider/other",
                    ],
                    "roles": {
                        "bug-fix": ["provider/configured"],
                        "judgment and prose": ["provider/other"],
                        "arena runners": ["provider/arena", "inherit-parent"],
                        "swarm workers": ["inherit-parent"],
                    },
                }
            ),
        )
        run = self.root / ".specify/pstack/runs/proof"
        run.mkdir(parents=True)
        prompt = run / "brief with spaces.txt"
        prompt.write_text("Inspect the artifact and report the observed result.")
        report = run / "report with spaces.json"
        paths = (
            "--prompt-file",
            str(prompt),
            "--report-file",
            str(report),
        )

        configured = self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "bug-fix",
            *paths,
        )
        self.assertEqual(
            set(configured),
            {
                "integration",
                "role",
                "index",
                "model_source",
                "model",
                "prompt_file",
                "report_file",
            },
        )
        self.assertIsNone(configured["index"])
        self.assertEqual(configured["model_source"], "configured")
        self.assertEqual(configured["model"], "provider/configured")
        self.assertEqual(Path(configured["prompt_file"]), prompt)
        self.assertEqual(Path(configured["report_file"]), report)

        parent = self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "swarm workers",
            "--parent-model",
            "parent/live",
            *paths,
        )
        self.assertEqual(set(parent), set(configured))
        self.assertEqual(parent["model_source"], "parent")
        self.assertEqual(parent["model"], "parent/live")
        self.call(
            "config-set",
            "--role",
            "swarm workers",
            "--models",
            '["provider/swarm"]',
        )
        race = self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "swarm workers",
            "--race-model",
            "provider/race",
            *paths,
        )
        self.assertEqual(set(race), set(configured))
        self.assertEqual(race["model_source"], "swarm-race")
        self.assertEqual(race["model"], "provider/race")

        for invalid in ("inherit-parent", "auto"):
            self.call(
                "dispatch-request",
                "--integration",
                "omp",
                "--role",
                "swarm workers",
                "--parent-model",
                invalid,
                *paths,
                ok=False,
            )
        self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "bug-fix",
            "--parent-model",
            "parent/live",
            *paths,
            ok=False,
        )
        self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "bug-fix",
            "--race-model",
            "provider/race",
            *paths,
            ok=False,
        )
        self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "swarm workers",
            "--race-model",
            "provider/unapproved",
            *paths,
            ok=False,
        )
        self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "swarm workers",
            "--parent-model",
            "parent/live",
            "--race-model",
            "provider/race",
            *paths,
            ok=False,
        )

        self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "arena runners",
            *paths,
            ok=False,
        )
        indexed = self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "arena runners",
            "--index",
            "1",
            *paths,
        )
        self.assertEqual(indexed["index"], 1)
        inherited_index = self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "arena runners",
            "--index",
            "2",
            "--parent-model",
            "parent/live",
            *paths,
        )
        self.assertEqual(inherited_index["index"], 2)
        self.assertEqual(inherited_index["model_source"], "parent")
        self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "bug-fix",
            "--index",
            "1",
            *paths,
            ok=False,
        )

        usage_error = self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "bug-fix",
            "--model",
            "provider/configured",
            *paths,
            ok=False,
        )
        self.assertIn("usage:", usage_error.stderr)

        env = {**os.environ, "PSTACK_DISPATCH_REQUEST": json.dumps(configured)}
        preflight = self.call("dispatch-preflight", env=env)
        self.assertEqual(preflight["model"], "provider/configured")
        forged = {
            **configured,
            "role": "judgment and prose",
            "model": "provider/configured",
        }
        self.call(
            "dispatch-preflight",
            env={**os.environ, "PSTACK_DISPATCH_REQUEST": json.dumps(forged)},
            ok=False,
        )
        unapproved = {**configured, "model": "provider/unapproved"}
        self.call(
            "dispatch-preflight",
            env={**os.environ, "PSTACK_DISPATCH_REQUEST": json.dumps(unapproved)},
            ok=False,
        )
        self.call(
            "config-set",
            "--role",
            "bug-fix",
            "--models",
            '["provider/other"]',
        )
        self.call("dispatch-preflight", env=env, ok=False)

        other = run.parent / "other"
        other.mkdir()
        self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "judgment and prose",
            "--prompt-file",
            str(prompt),
            "--report-file",
            str(other / "report.json"),
            ok=False,
        )
        self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "judgment and prose",
            "--prompt-file",
            str(prompt),
            "--report-file",
            str(self.root / "report.json"),
            ok=False,
        )
        report.write_text(json.dumps(self.report()))
        self.call(
            "dispatch-request",
            "--integration",
            "omp",
            "--role",
            "judgment and prose",
            *paths,
            ok=False,
        )


if __name__ == "__main__":
    unittest.main()
