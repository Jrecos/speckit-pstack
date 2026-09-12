---
description: "Re-prove every completed task from live artifacts and uncheck phantom completions"
---

# Pstack Verify

Independent re-proof of the feature. Every checked task's Check line runs again in this session against the live artifact. Trust no prior evidence line; the point is that a different pass reaches the same verdict.

## User Input

```text
$ARGUMENTS
```

## Pre-conditions

1. Resolve the feature directory: run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` and parse `FEATURE_DIR`.
2. Read `FEATURE_DIR/tasks.md` in full.

## Steps

1. **Enumerate the proof set.** Every checked task (match `[X]` case-insensitively, `[x]` counts) and its `**Check:**` line. A checked task with no Check line takes verdict VOID immediately, reason `no Check line`.

2. **Run each check and record a verdict.** Run each check in this session by default. Delegate a phase's checks through the verify lane only when the dispatch returns each verdict with the raw output excerpt it observed; transcribed verdicts without excerpts are self-report and do not count. Each verdict is one of:
   - `PASS`. The check ran and the result matched. Record a one-line excerpt of the actual output, and answer the masking question: what would make this check pass while the task is broken. Name it, or say nothing could.
   - `FAIL`. The check ran and the result differed. Record the actual output excerpt.
   - `VOID`. The check cannot run (target gone, test missing, command unknown), or the task has no Check line.

3. **Uncheck phantoms.** Any `[X]` task that is `FAIL` or `VOID` gets unchecked in tasks.md, with the verdict and reason written under it. Keep one pstack note line per task. A new note replaces that task's previous pstack note line, it never appends.

   ```
   > pstack verify (T012): FAIL pytest tests/test_alloc.py::test_own_cap fails, cap ignored at line 40
   > pstack verify (T007): PASS pytest tests/test_alloc.py::test_own_cap passed, 4/4. Masking question, nothing could make this pass while the task is broken.
   ```

   Do not fix code here. A FAIL routes back to `__SPECKIT_COMMAND_PSTACK_IMPLEMENT__`. A VOID routes to `__SPECKIT_COMMAND_PSTACK_TASKS__` to repair the Check line first; implement cannot fix Check text.

4. **Cross-check the surface.** Sibling tasks are the other tasks under the same phase heading. Run the deduplicated union of the phase's checks once. When any task in a phase ended unchecked, re-run every check in that phase; a FAIL from this pass is a new verdict, uncheck that task too and count it in M. This is where a check that passes only because a sibling masks it shows up.

5. **Report.**

```
| Task | Check | Verdict |
|------|-------|---------|
| T007 | pytest tests/test_alloc.py::test_own_cap | PASS |
| T012 | cap honored in edge mirror | FAIL (unchecked) |

Verified: N passed, M failed (unchecked), K void (unchecked)
```

All PASS is the only green. M plus K above zero is not a partial success. Route FAILs through `__SPECKIT_COMMAND_PSTACK_IMPLEMENT__` and VOID Check lines through `__SPECKIT_COMMAND_PSTACK_TASKS__`, then re-run this command.
