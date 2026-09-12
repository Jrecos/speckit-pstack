---
description: "Apply the pstack task contract: rewrite tasks.md so every task is a verifiable unit with an explicit acceptance check"
---

# Pstack Tasks Contract

Audit and repair the current feature's `tasks.md` against the pstack contract. This command runs after task generation (manually, or as an `after_tasks` hook if the user opts in) and before any implementation. It does not design the feature; it makes the task list executable under rigor.

## User Input

```text
$ARGUMENTS
```

## Pre-conditions

1. Resolve the feature directory: run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` from the repo root and parse `FEATURE_DIR`. Abort with a plain error if no tasks.md exists.
2. Read `FEATURE_DIR/tasks.md` in full.

## The contract (audit every task against all five rules)

**R1 Verifiable unit.** Each task is small enough that one step can prove it done. A task needing more than one unrelated verification (a file of code AND a schema migration AND a doc) is split.

**R2 Named acceptance check.** Every task carries a `**Check:**` line naming the concrete proof: the exact command to run, the file/value to read, or the UI surface to exercise. "Works correctly" is not a check. If the proof cannot be named, the task is not ready (R1 again).

**R3 Data shape first.** Tasks that introduce a type, schema, table, interface, or config shape come before tasks that consume that shape, and each consuming task names the shape it consumes. If implementation order would force consumers to exist before producers, re-order.

**R4 Honest parallel markers.** A task gets `[P]` only when its acceptance check can pass while every other `[P]` task in the same phase also runs: no shared file writes, no shared migration, no ordering assumption. Stolen `[P]` markers are the direct cause of merge garbage in fan-out runs; when in doubt, remove the marker.

**R5 No silent scope.** A task that imports a library, adds a dependency, or changes the public surface of an existing module names that explicitly in its own text. If it cannot, split the dependency decision into its own task.

## Steps

1. **Audit.** Walk tasks.md top to bottom. For each violation record: task id, rule, one-line reason.

2. **Repair.** Rewrite tasks.md in place to satisfy the contract:
   - Split or merge tasks (R1), preserving the original ids where a task is unchanged.
   - Add or sharpen `**Check:**` lines (R2) deriving the proof from the task's own text plus plan.md; never invent a check the plan does not support.
   - Re-order so shape producers precede consumers (R3).
   - Strip or add `[P]` markers per R4.
   - Surface dependency/surface changes as explicit tasks (R5).
   - Keep the file's existing section structure and checkbox format intact; change as few lines as each fix requires.

3. **Report.** Output a change table:

```
| Task | Rule | Change |
|------|------|--------|
| T012 | R2   | added Check: pytest tests/test_alloc.py::test_own_cap |
```

Then one line: `Contract: N violations fixed, M tasks split, K [P] markers removed.`

4. **Hand off.** Next step is `__SPECKIT_COMMAND_PSTACK_IMPLEMENT__`.
