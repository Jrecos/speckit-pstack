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

1. **Enumerate the proof set.** Every `[X]` task and its `**Check:**` line. A checked task with no Check line is a finding (F1), not something to skip.

2. **Re-run each check.** Execute each Check in this session. Batch independent checks into one subagent dispatch per phase when a dispatch table resolves (via `__SPECKIT_COMMAND_PSTACK_ROLES__`, `verify` role); otherwise run them directly. Each verdict is one of:
   - `PASS` — check ran and observed the expected result.
   - `FAIL` — check ran and observed something else. Include actual output.
   - `VOID` — check cannot run (target gone, test missing, command unknown).

3. **Uncheck phantoms.** Any `[X]` task that is `FAIL` or `VOID` gets unchecked in tasks.md, with the verdict and reason written under it:

   ```
   > pstack verify (T012): FAIL — pytest tests/test_alloc.py::test_own_cap fails: cap ignored at line 40
   ```

   Do not fix code here. Re-proof only; fixing routes back through `__SPECKIT_COMMAND_PSTACK_IMPLEMENT__`.

4. **Cross-check the surface.** Beyond per-task checks, verify the whole feature still holds together:
   - The full check suite the tasks collectively imply runs green (deduplicate Check lines, run once).
   - No check passes because another task's work masks it (re-run any check whose sibling task is now unchecked).

5. **Report.**

```
| Task | Check | Verdict |
|------|-------|---------|
| T007 | pytest tests/test_alloc.py::test_own_cap | PASS |
| T012 | cap honored in edge mirror | FAIL (unchecked) |

Verified: N passed, M failed (unchecked), K void (unchecked)
Next: fix failures via __SPECKIT_COMMAND_PSTACK_IMPLEMENT__, then re-run this command
```

All PASS is the only green. M + K > 0 is not a partial success.
