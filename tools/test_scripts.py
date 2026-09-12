#!/usr/bin/env python3
"""Exercise the two adapted upstream scripts at their consumer boundary."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
MODE = PACKAGE / "resources/skills/poteto-mode"


class TranslatedScriptTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "node is required for the packaged plan checker")
    def test_native_plan_template_passes_and_missing_lane_fails(self):
        template = (MODE / "playbooks/multi-phase-plan.md").read_text()
        plan = template.split("````markdown\n", 1)[1].split("\n````", 1)[0]
        plan = re.sub(r"<[^>]*model[^>]*>", "provider/model", plan, flags=re.I)
        plan = re.sub(r"<[^>]+>", "native-proof", plan)
        with tempfile.TemporaryDirectory(prefix="pstack-plan-test-") as directory:
            path = Path(directory) / "plan.md"
            path.write_text(plan)
            command = ["node", str(MODE / "scripts/check-plan.mjs"), str(path)]
            valid = subprocess.run(command, text=True, capture_output=True, timeout=15)
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
            path.write_text(re.sub(r"^- \[ \] Lane 10\..*\n?", "", plan, flags=re.M))
            invalid = subprocess.run(command, text=True, capture_output=True, timeout=15)
            self.assertNotEqual(invalid.returncode, 0, invalid.stdout + invalid.stderr)

    @unittest.skipUnless(shutil.which("git") and shutil.which("bash") and shutil.which("rg"), "git, bash, and rg are required for the worktree audit")
    def test_recent_transcript_prevents_safe_prune_classification(self):
        with tempfile.TemporaryDirectory(prefix="pstack-worktree-test-") as directory:
            root = Path(directory)
            repo = root / "main repo"
            repo.mkdir()

            def git(*args):
                return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True, timeout=15)

            git("init", "-b", "main")
            git("-c", "user.name=Native proof", "-c", "user.email=native@example.invalid", "commit", "--allow-empty", "-m", "Disposable audit fixture")
            git("update-ref", "refs/remotes/origin/main", "HEAD")
            worktree = root / "recent worktree"
            git("worktree", "add", "-b", "recent", str(worktree))
            transcripts = root / "transcripts"
            transcripts.mkdir()
            (transcripts / "fresh transcript.jsonl").write_text(json.dumps({"cwd": str(worktree)}) + "\n")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            forge = bin_dir / "gh"
            forge.write_text("#!/bin/sh\nexit 1\n")
            forge.chmod(0o755)
            environment = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"], "PSTACK_TRANSCRIPTS_DIR": str(transcripts)}
            result = subprocess.run(["bash", str(MODE / "scripts/worktree-audit.sh"), str(repo)], env=environment, text=True, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            rows = [line.split("\t") for line in result.stdout.splitlines()]
            self.assertEqual([row[-1] for row in rows[1:]], [str(worktree)])
            observed = next(row for row in rows if row[-1] == str(worktree))
            self.assertEqual(observed[2], "YES", result.stdout)
            self.assertEqual(observed[7], "verify-recent-chat", result.stdout)
            self.assertTrue(worktree.is_dir())


if __name__ == "__main__":
    unittest.main()
