---
description: "Implement tasks.md with pstack rigor: shape first, disjoint-write [P] batches, parent-applied verdicts, evidence-gated completion"
scripts:
  sh: ../../scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: ../../scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
  py: ../../scripts/python/check_prerequisites.py --json --require-tasks --include-tasks
---

# Pstack Implement

Execute the feature's tasks.md the pstack way. This replaces the core implement step for this run. Same artifacts, same checkboxes; completion is evidence-gated and independent work fans out under disjoint writes.

Read the shared contract first: `.specify/extensions/pstack/runtime/host-contract.md`. It owns role resolution, dispatch, the report shape, and what this host can actually do.

## User Input

```text
$ARGUMENTS
```

## Pre-Execution Checks

**Check for extension hooks (before implementation)**:

- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_implement` key.
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- Skip any hook whose `command` is this command, `speckit.pstack.implement`, or the core `speckit.implement`. This command replaces the core step, so dispatching it again would recurse.
- Do not interpret or evaluate hook `condition` expressions; a non-empty `condition` is skipped and left to the HookExecutor implementation.
- Emit the optional or mandatory hook block exactly as the core step specifies, and for a mandatory hook actually invoke it and wait before starting the loop.
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently.

## Pre-conditions

1. Resolve the feature directory: run `{SCRIPT}` from the repo root and parse `FEATURE_DIR`.
2. Read `FEATURE_DIR/tasks.md` in full. Audit it against all five contract rules, not just Check presence. Any violation: run `__SPECKIT_COMMAND_PSTACK_TASKS__` first and re-read. Never fan out on an unaudited list.
3. Resolve every dispatch role with `python3 .specify/extensions/pstack/runtime/pstack-native.py role-plan --role "<label>"`, using the host contract's workload classifier and its role kinds. The plan's `kind` says whether the role is `single`, `panel`, or `choose-one`; pass `--index` only for a multi-selector role, and choose exactly one index for `choose-one`. An empty role, or a selector the host rejects, stops the run with that error; never substitute a model.
4. Read `FEATURE_DIR/plan.md`. A durable API or interface decision (a signature, a shape, a boundary contract) belongs there, not only in an evidence line. If a task depends on such a decision and plan.md does not carry it, record the decision in plan.md before implementing that task.

## Workspace state before any dispatch

Serial and parallel task writes must be known before the first write. Establish ownership explicitly:

1. **Record the starting state.** `git status --short`, `git diff --stat`, `git stash list`. Note anything already in the index or working tree that is not yours.
2. **Never stash or commit unrelated work to get a clean tree.** Cleanliness is not a goal; provable ownership is. Another writer's uncommitted change stays where it is.
3. **Never recover with a whole-file `git checkout -- <file>` or `git restore <file>`.** That discards every uncommitted change in the file, including work that is not yours. Stop the writers first, preserve the diff, then decide.
4. **When the tree is shared, isolate.** Put a parallel batch in its own git worktree off the current commit, so a worker cannot touch the parent's files. Inside a worktree, one writer per file set.
5. **Know your writes.** The batch's union of `**Writes:**` lists is the set this run may modify. A file in `git status` that no task names is someone else's; leave it and report it. Each worker's assigned report file is outside that set: it is control metadata under the run directory, never a claimed task artifact.
6. **Commit only your own changes, and only when ownership is provable.** Stage exactly the union of the batch's Writes lists plus the tasks.md lines this parent wrote. Never stage by glob (`git add -A`, `git add .`). If the ownership of a change cannot be shown, do not commit it; report it instead. Outside a git work tree, skip committing and say so once.

## Per-task execution loop

Process tasks in file order within each phase; complete every task's Check before moving on.

For each unchecked task:

1. **Shape first.** If the task introduces or consumes a named data shape (type, schema, interface, config), define or re-read the shape before writing any consuming code. The shape change is part of this task's diff.

2. **Choose and dispatch the lane.**
   - **Workload role.** Route the task through the host contract's workload
     classifier. Do not keep a second list here. `feature, refactoring` covers
     new behavior and behavior-preserving refactors, `bug-fix` a defect,
     `perf-issue` a measured slowdown, `hillclimb` sustained metric work,
     `hardest tasks` a change whose difficulty is the design, and
     `judgment and prose` docs, commit messages, and release text.
   - **Parallel lane.** A `[P]` task with at least one other pending `[P]` task
     in the same phase joins one batch through `swarm workers`.
   - **Sequential lane.** Every other task still gets one worker. Allocate one
     run with `.specify/extensions/pstack/runtime/pstack-native.py run-new --role
     "<workload role>"`, dispatch that worker, and wait for its report before
     moving to the next task. Saying a task runs "on" a role without allocating
     and dispatching that worker is not role dispatch. `run-new --legs` repeats a
     single-selector worker; the run ordinal it returns distinguishes repeated
     prompt/report pairs and is not a configured selector index.
   - **Before dispatch.** Every task brief carries a `**Writes:**` line, parallel
     or serial, and `[]` is the correct list for a task that writes no artifact.
     Refuse a parallel batch when a Writes line is missing or two `[P]` lists in
     the same phase overlap; disjointness is a parallel rule, so a serial task may
     touch a file a later serial task also touches. Run
     `__SPECKIT_COMMAND_PSTACK_TASKS__` to repair that contract. Establish
     the workspace state above before the first write, isolating a parallel
     batch in a worktree when the tree is shared.
   - **Brief.** Carry the task text verbatim, its Check and Writes lines, the
     relevant plan and spec sections, the agent contract at
     `.specify/extensions/pstack/resources/agents/poteto-agent.md`, and the
     report path. Implement workers never edit `tasks.md`, never commit, and
     touch nothing outside their Writes list. They run the task's scoped Check,
     but not project-wide suites, linters, or builds while another writer is
     active.
   - **Parallel dispatch.** Start one worker per task in one batch, bounded by
     `parallel.max_workers`. Allocate distinct paths with `run-new --role
     "swarm workers" --legs <batch-size>`.
   - **Sequential dispatch.** Start exactly one worker through the resolved
     workload role and drain it before starting the next task.
   - **CLI dispatch.** When this host has no native subagent facility, build the
     one authoritative request from the role and let the workflow run the leg:

     ```bash
     request_json=$(
       python3 .specify/extensions/pstack/runtime/pstack-native.py dispatch-request \
         --integration "$integration" \
         --role "<workload role>" \
         --prompt-file "$prompt_file" \
         --report-file "$report_file"
     ) || exit

     PSTACK_DISPATCH_REQUEST="$request_json" \
       specify workflow run .specify/extensions/pstack/workflows/dispatch.yml --json
     ```

     The helper derives the model from the role map, so never pass a model of your
     own. Add `--index <n>` only for a multi-selector role. A role whose selected
     entry is `inherit-parent` or `auto` needs `--parent-model <concrete current
     model>`. Only role `swarm workers`
     may pass `--race-model <concrete approved model>`, and that override does not
     depend on the role's configured selector. Both flags together are rejected,
     and so is either flag anywhere else.
   - **Reports.** A worker writes required `verdict`, `check`, `evidence`,
     `files`, and string `reason` keys. It may add non-empty string `result`.
     Validate native reports with
     `.specify/extensions/pstack/runtime/pstack-native.py report-check --report
     <path>`. CLI workflow reports are checked from the authoritative
     `PSTACK_DISPATCH_REQUEST`. Missing, malformed, or failing reports fail the
     leg even when the worker process exits zero. A worker's assigned report path
     is control metadata, not a task artifact: it is not a Writes entry and writing
     it is never a violation.
   - **No dispatch facility.** Run tasks serially in this session under the same
     write and check restrictions, and report that the work was not an
     independent delegate.
   - **Return.** The parent applies every verdict. Check reported files against
     Writes and `git status --short`. A changed file no report owns is a
     violation. Only then mark passing tasks `[X]` and write their evidence.

3. **Prove, then check.** A task may be marked `[X]` only after its Check line was actually executed in this run (or by the worker that owns it) and passed against the real artifact. Record one evidence line under the task, with the report path it came from:

   ```
   > pstack evidence (T007): `pytest tests/test_alloc.py::test_own_cap` passed, 4/4 (report .specify/pstack/runs/20260912T101500Z-a1b2c3-swarm-workers/swarm-workers-leg1-report.json)
   ```

   A check that cannot run yet (missing prerequisite task) blocks the task, not the evidence rule. Keep one pstack note line per task. A new note for a task replaces that task's previous pstack note line, it never appends.

4. **Boundary crossings get the architect workflow.** Before implementing a task that adds or changes a public function, interface, schema, or module boundary consumed elsewhere, run the **architect** skill at that boundary: build the traced model of every system the change touches (the `how` skill over the affected subsystem, and `why` when the change redefines ownership or layering), state the caller's usage and the illegal states, produce two or three competing sketches, pick a base, and record the settled signature (caller, types, failure mode) in plan.md and in the task's note line. Single-module tasks need no design pass; a boundary crossing does, and a one-paragraph shortcut is not the architect workflow.

5. **Commit per unit.** Inside a git work tree, commit after each task or coherent `[P]` batch passes its check, staging exactly the files the ownership rules above allow. Use a conventional title naming the task ids. Outside a work tree, skip committing and say so once in the report.

## Stop conditions

- A check fails after two fix attempts: stop, leave the task unchecked, write the failure and hypothesis under the task as evidence, report.
- A worker violates the contract (touched a file outside its Writes list, edited tasks.md, invented a check, produced no report): stop the batch, preserve its diff, and identify exactly which files it wrote before changing anything. Inside an isolated worktree, keep the worktree and list the offending files; do not run a whole-file checkout to make the tree look clean. Then fix the task list and re-dispatch.
- Never mark a task complete without its evidence line. Unproven work is reported as remaining work, not partial success.

## Post-execution integration

The parent, not a worker, runs the project-wide checks once every parallel writer has stopped: the full test suite, the linters, and the build the repo declares. A worker skipping them mid-batch is correct; the parent skipping them is not.

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_implement`, skip to the Report.
- If it exists, read it and look for entries under the `hooks.after_implement` key.
- If the YAML cannot be parsed or is invalid, skip hook checking silently.
- Filter out hooks where `enabled` is explicitly `false`, and skip any hook whose `command` is `speckit.pstack.implement` or `speckit.implement`.
- Do not interpret or evaluate hook `condition` expressions; a non-empty `condition` is skipped and left to the HookExecutor implementation.
- Emit each executable hook's block exactly as the pre-execution section specifies, and for a mandatory hook actually invoke it and wait.

## Report

End with:

```
Implemented: <ids with evidence>
Blocked:     <ids, one-line reason each>
Workspace:   <isolation used, files left untouched that the run did not own>
Project checks: <the commands the parent ran after integration, and their result>
Next:        __SPECKIT_COMMAND_PSTACK_VERIFY__
```
