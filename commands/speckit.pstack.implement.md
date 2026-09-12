---
description: "Implement tasks.md with pstack rigor: shape first, disjoint-write [P] batches, parent-applied verdicts, evidence-gated completion"
---

# Pstack Implement

Execute the feature's tasks.md the pstack way. This replaces the core implement step for this run. Same artifacts, same checkboxes; completion is evidence-gated and independent work fans out under disjoint writes.

## User Input

```text
$ARGUMENTS
```

## Pre-conditions

1. Resolve the feature directory: run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` and parse `FEATURE_DIR`.
2. Read `FEATURE_DIR/tasks.md` in full. Audit it against all five contract rules, not just Check presence. Any violation: run `__SPECKIT_COMMAND_PSTACK_TASKS__` first and re-read. Never fan out on an unaudited list.
3. Resolve dispatch roles: run `__SPECKIT_COMMAND_PSTACK_ROLES__`. Use its table for every subagent dispatch below.

## Per-task execution loop

Process tasks in file order within each phase; complete every task's Check before moving on.

For each unchecked task:

1. **Shape first.** If the task introduces or consumes a named data shape (type, schema, interface, config), define or re-read the shape before writing any consuming code. The shape change is part of this task's diff.

2. **Choose the lane.**
   - **Lane.** A `[P]` task with at least one other pending `[P]` task in the same phase dispatches in one batch through the swarm lane (roles table). Any other task runs in this session.
   - **Before dispatch.** Every `[P]` task in the batch must carry a `**Writes:**` line naming the files it will touch. Refuse the batch when a Writes line is missing or when any two lists overlap; that is a contract violation, run `__SPECKIT_COMMAND_PSTACK_TASKS__`. Inside a git work tree the tree must be clean before dispatch; stash or commit unrelated work first.
   - **Dispatch.** One subagent per task, at most `parallel.max_workers` concurrent. Each brief carries the task text verbatim, its Check line, its Writes list, the relevant plan.md and spec.md sections, and these rules: run the Check and report PASS or FAIL with a one-line output excerpt; list every file you touched; never edit tasks.md; never commit; touch nothing outside your Writes list.
   - **No subagent facility.** Run the batch's tasks serially in this session under the same rules, and say so in the report.
   - **Return.** The parent applies every verdict. Check each report's touched-files list against its Writes list and against `git status --short`; a file in the status output that no report names is a violation. Only then mark passing tasks `[X]` and write their evidence lines yourself.

3. **Prove, then check.** A task may be marked `[X]` only after its Check line was actually executed in this run (or by the subagent that owns it) and passed against the real artifact. Record one evidence line under the task:

   ```
   > pstack evidence (T007): `pytest tests/test_alloc.py::test_own_cap` passed, 4/4
   ```

   A check that cannot run yet (missing prerequisite task) blocks the task, not the evidence rule. Keep one pstack note line per task. A new note for a task replaces that task's previous pstack note line, it never appends.

4. **Boundary crossings get a design minute.** Before implementing a task that adds a public function/interface consumed by another module, settle the caller's usage and signature in one paragraph (caller, types, failure mode) before code. Do not spawn a design process for single-module tasks. For a boundary crossing, record the settled signature (caller, types, failure mode) in the task's note line alongside the evidence.

5. **Commit per unit.** Inside a git work tree, commit after each task or coherent `[P]` batch passes its check, staging exactly the task or batch's own files: the union of its Writes lists plus the tasks.md lines this parent just wrote (marks and evidence). Never stage by glob (`git add -A`, `git add .`). Use a conventional title naming the task ids. Outside a work tree, skip committing and say so once in the report.

## Stop conditions

- A check fails after two fix attempts: stop, leave the task unchecked, write the failure and hypothesis under the task as evidence, report.
- A subagent violates the contract (touched a file outside its Writes list, edited tasks.md, invented a check): inside a work tree, revert its files with `git checkout -- <files>`; outside a work tree, list its files in the report for manual removal. Then fix the task list and re-dispatch.
- Never mark a task complete without its evidence line. Unproven work is reported as remaining work, not partial success.

## Report

End with:

```
Implemented: <ids with evidence>
Blocked:     <ids, one-line reason each>
Next:        __SPECKIT_COMMAND_PSTACK_VERIFY__
```
