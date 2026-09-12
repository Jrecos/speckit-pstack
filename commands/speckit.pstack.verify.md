---
description: "Re-prove every completed task from live artifacts and uncheck phantom completions"
scripts:
  sh: ../../scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: ../../scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
  py: ../../scripts/python/check_prerequisites.py --json --require-tasks --include-tasks
---

# Pstack Verify

Independent re-proof of the feature. Every checked task's Check line runs again in this session against the live artifact. Trust no prior evidence line; the point is that a different pass reaches the same verdict.

Read the shared contract first: `.specify/extensions/pstack/runtime/host-contract.md`. Load the active mode as well: if `.specify/extensions/pstack/resources/skills/poteto-mode/SKILL.md` is present and the mode is active for this session, its rules govern how this command reports.

## User Input

```text
$ARGUMENTS
```

## Pre-conditions

1. Resolve the feature directory: run `{SCRIPT}` and parse `FEATURE_DIR`.
2. Read `FEATURE_DIR/tasks.md` in full.
3. Resolve the verification role before any delegation: `python3 .specify/extensions/pstack/runtime/pstack-native.py role-plan --role "interrogate reviewers" --index <n>`. `interrogate reviewers` is a `panel`, so `--index` exposes one configured leg and omitting it exposes all of them; the index is a configured selector index, never a worker ordinal. Report an empty role or a rejected selector as a configuration failure; never substitute a model, because a substituted model makes the independence claim false.
4. Read live tool availability before promising any surface: `python3 .specify/extensions/pstack/runtime/pstack-native.py capability-report`. A check whose surface the report marks `unavailable` is VOID with that reason, not a pass.

## Steps

1. **Enumerate the proof set.** Every checked task (match `[X]` case-insensitively, `[x]` counts) and its `**Check:**` line. A checked task with no Check line takes verdict VOID immediately, reason `no Check line`.

2. **Run each check and record a verdict.** Run each check in this session by default. When the host can dispatch and the phase's checks are expensive, delegate them through the `interrogate reviewers` role, one worker per configured entry, or the single leg named by `--index`, with each prompt/report pair from `.specify/extensions/pstack/runtime/pstack-native.py run-new --role "interrogate reviewers" --index <n>`. Allocate or dispatch it through the helper's role-first request when this host has only the workflow path; never hand the workflow a model of your own. A delegated verdict counts only when its report file passes `.specify/extensions/pstack/runtime/pstack-native.py report-check --report <path>`; a transcribed verdict without a report and its excerpt is self-report and does not count. Each verdict is one of:
   - `PASS`. The check ran and the result matched. Record a one-line excerpt of the actual output, and answer the masking question: what would make this check pass while the task is broken. Name it, or say nothing could.
   - `FAIL`. The check ran and the result differed. Record the actual output excerpt.
   - `VOID`. The check cannot run (target gone, test missing, command unknown, surface unavailable), or the task has no Check line.

3. **Uncheck phantoms.** Any `[X]` task that is `FAIL` or `VOID` gets unchecked in tasks.md, with the verdict and reason written under it. Keep one pstack note line per task. A new note replaces that task's previous pstack note line, it never appends.

   ```
   > pstack verify (T012): FAIL pytest tests/test_alloc.py::test_own_cap fails, cap ignored at line 40
   > pstack verify (T007): PASS pytest tests/test_alloc.py::test_own_cap passed, 4/4. Masking question, nothing could make this pass while the task is broken.
   ```

   Do not fix code here. A FAIL routes back to `__SPECKIT_COMMAND_PSTACK_IMPLEMENT__`. A VOID routes by cause: the Check line missing or unusable routes to `__SPECKIT_COMMAND_PSTACK_TASKS__` to repair the Check line, while the target or command gone, or a surface the capability report marks unavailable, routes to `__SPECKIT_COMMAND_PSTACK_IMPLEMENT__` to rebuild the artifact.

4. **Cross-check the surface.** Sibling tasks are the other tasks under the same phase heading. Run the deduplicated union of the phase's checks once. When any task in a phase ended unchecked, re-run every check in that phase; a FAIL from this pass is a new verdict, uncheck that task too and count it in M. For each PASS in a phase with an unchecked task, answer in the note line what would make the check pass while the task is broken. A same-artifact re-run catches shared-state regressions; it cannot prove a check's criteria were right, so record that limit with the verdict.

5. **Report.**

```
| Task | Check | Verdict |
|------|-------|---------|
| T007 | pytest tests/test_alloc.py::test_own_cap | PASS |
| T012 | cap honored in edge mirror | FAIL (unchecked) |

Verified: N passed, M failed (unchecked), K void (unchecked)
```

All PASS is the only green. M plus K above zero is not a partial success. Route FAILs through `__SPECKIT_COMMAND_PSTACK_IMPLEMENT__` and VOID Check lines through `__SPECKIT_COMMAND_PSTACK_TASKS__`, then re-run this command.
