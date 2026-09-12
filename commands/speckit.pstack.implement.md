---
description: "Implement tasks.md with pstack rigor: data shape first, subagent fan-out for independent tasks, evidence-gated completion"
---

# Pstack Implement

Execute the feature's tasks.md the pstack way. This replaces `/speckit.implement` for this run. Same artifacts, same checkboxes, but completion is evidence-gated and independent work is fanned out.

## User Input

```text
$ARGUMENTS
```

## Pre-conditions

1. Resolve the feature directory: run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` and parse `FEATURE_DIR`.
2. Read `FEATURE_DIR/tasks.md` in full. If any task lacks a `**Check:**` line or the file violates the pstack contract, run `__SPECKIT_COMMAND_PSTACK_TASKS__` first and re-read.
3. Resolve dispatch roles: run `__SPECKIT_COMMAND_PSTACK_ROLES__`. Use its table for every subagent dispatch below.

## Per-task execution loop

Process tasks in file order within each phase; complete every task's Check before moving on.

For each unchecked task:

1. **Shape first.** If the task introduces or consumes a named data shape (type, schema, interface, config), define or re-read the shape before writing any consuming code. The shape change is part of this task's diff.

2. **Choose the lane.**
   - Task is `[P]` and at least one other pending `[P]` task exists in the same phase: dispatch each to a subagent in one batch (up to `parallel.max_workers` concurrent), each with: the task text verbatim, its Check line, the relevant plan.md and spec.md sections, and the instruction to run its Check and report the evidence. Dispatch through the roles table (`swarm` role for swarm tasks).
   - Otherwise implement in this session.
   - `[P]` dispatches write to disjoint files by construction (the tasks contract guarantees it). If a subagent reports touching a file another subagent owns, stop, un-mark both tasks, and re-run the contract.

3. **Prove, then check.** A task may be marked `[X]` only after its Check line was actually executed in this run (or by the subagent that owns it) and passed against the real artifact. Record one evidence line under the task:

   ```
   > pstack evidence (T007): `pytest tests/test_alloc.py::test_own_cap` passed, 4/4
   ```

   A check that cannot run yet (missing prerequisite task) blocks the task, not the evidence rule.

4. **Boundary crossings get a design minute.** Before implementing a task that adds a public function/interface consumed by another module, settle the caller's usage and signature in one paragraph (caller, types, failure mode) before code. Do not spawn a design process for single-module tasks.

5. **Commit per unit.** Inside a git work tree, commit after each task (or coherent `[P]` batch) passes its check, with a conventional title naming the task ids. Outside a work tree, skip committing and say so once in the report.

## Stop conditions

- A check fails after two fix attempts: stop, leave the task unchecked, write the failure and hypothesis under the task as evidence, report.
- A subagent's diff violates the contract (shared file, invented check): revert that subagent's work, fix the task list, re-dispatch.
- Never mark a task complete without its evidence line. Unproven work is reported as remaining work, not partial success.

## Report

End with:

```
Implemented: <ids with evidence>
Blocked:     <ids, one-line reason each>
Next:        __SPECKIT_COMMAND_PSTACK_VERIFY__
```
