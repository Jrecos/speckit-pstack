---
description: "Apply the pstack task contract: rewrite tasks.md so every task is a verifiable unit with an explicit acceptance check and a declared writes list"
scripts:
  sh: ../../scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: ../../scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
  py: ../../scripts/python/check_prerequisites.py --json --require-tasks --include-tasks
---

# Pstack Tasks Contract

Audit and repair the current feature's `tasks.md` against the pstack contract. This command runs after task generation and before any implementation. It does not design the feature; it makes the task list executable under rigor.

Read the shared contract first: `.specify/extensions/pstack/runtime/host-contract.md`.

## User Input

```text
$ARGUMENTS
```

## Pre-Execution Checks

**Check for extension hooks (before task repair)**:

- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_tasks` key.
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- Skip any hook whose `command` is this command, `speckit.pstack.tasks`, or the core `speckit.tasks`. This command replaces the core step, so dispatching it again would recurse; the core step still fires the hooks for runs that use it.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above).
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently.

## Pre-conditions

1. Resolve the feature directory: run `{SCRIPT}` from the repo root and parse `FEATURE_DIR`. Abort with a plain error if no tasks.md exists.
2. Read `FEATURE_DIR/tasks.md` in full, and keep the pre-repair text: step 4 compares against it.

## The contract (audit every task against all five rules)

**R1 Verifiable unit.** Each task is small enough that one step can prove it done. A task needing more than one unrelated verification (a file of code AND a schema migration AND a doc) is split.

**R2 Named acceptance check.** Every task carries a `**Check:**` line naming the concrete proof: the exact command to run, the file/value to read, or the UI surface to exercise. "Works correctly" is not a check. If the proof cannot be named, the task is not ready (R1 again).

**R3 Data shape first.** Tasks that introduce a type, schema, table, interface, or config shape come before tasks that consume that shape, and each consuming task names the shape it consumes. If implementation order would force consumers to exist before producers, re-order.

**R4 Honest writes and parallel markers.** Every task lists every file it will write on a `**Writes:**` line, and `**Writes:** []` is the correct list for a task that writes no artifact, such as a read-only investigation. A task gets `[P]` only when its acceptance check can pass while every other `[P]` task in the same phase also runs. The marker is earned with data, not assertion: no two `[P]` tasks in the same phase may list the same file. Disjointness is a parallel rule, so a serial task may write a file a later serial task also rewrites. A shared file, a shared migration, or an ordering assumption means no marker. When in doubt, remove the marker. A worker's assigned report file is control metadata, never a Writes entry.

**R5 No silent scope.** A task that imports a library, adds a dependency, or changes the public surface of an existing module names that explicitly in its own text. If it cannot, split the dependency decision into its own task.

## Steps

1. **Audit.** Walk tasks.md top to bottom. For each violation record: task id, rule, one-line reason.

2. **Repair.** Rewrite tasks.md in place to satisfy the contract:
   - Split or merge tasks (R1), preserving the original ids where a task is unchanged.
   - When a task splits, its parts take suffix ids (T012 becomes T012a and T012b) so evidence stays addressable; unchanged tasks keep their ids.
   - Add or sharpen `**Check:**` lines (R2) deriving the proof from the task's own text plus plan.md; never invent a check the plan does not support.
   - Re-order so shape producers precede consumers (R3).
   - Strip or add `[P]` markers per R4.
   - Add or complete a `**Writes:**` line on every task, including serial ones, using `[]` for a task that writes no artifact. Remove a `[P]` marker whose file set is unknown or overlaps another `[P]` task in the same phase.
   - Surface dependency/surface changes as explicit tasks (R5).
   - Keep the file's existing section structure and checkbox format intact; change as few lines as each fix requires.

3. **Invalidate the proof of every task this repair changed.** A `[X]` mark and a `> pstack evidence` line are claims about a specific obligation. The repair changed that obligation, so the claim no longer covers it. For each task whose text, `**Check:**` line, `**Writes:**` line, `[P]` marker, phase position, or ids changed:
   - Uncheck it (`[X]` → `[ ]`) when the change alters what must be proven: a split, a merged obligation, a rewritten or newly added Check line, a changed Writes list, a moved phase that changes what runs concurrently.
   - Keep the mark only when the edit is provably proof-neutral: a typo, a wording change that leaves the check and the writes list byte-identical, or adding an R5 dependency note that the existing check already exercises.
   - Delete the task's previous `> pstack evidence` and `> pstack verify` note lines when you uncheck it, because a stale evidence line is what makes a changed task look finished.
   - State in the report which ids were unchecked and why, so the loss of prior proof is visible rather than silent.

4. **Verify the repair did not fabricate work.** Re-read the repaired tasks.md against the pre-repair text. Every check line must trace to the task's own text or to plan.md, and no task may appear or vanish beyond the splits, merges, and reorders you recorded.

5. **Report.** Output a change table:

```
| Task | Rule | Change |
|------|------|--------|
| T012 | R2   | added Check: pytest tests/test_alloc.py::test_own_cap |
```

Then one line: `Contract: N violations fixed, M tasks split, K [P] markers removed, W Writes lists added or corrected, J tasks unchecked (proof invalidated).`

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_tasks`, skip to the hand-off line.
- If it exists, read it and look for entries under the `hooks.after_tasks` key.
- If the YAML cannot be parsed or is invalid, skip hook checking silently.
- Filter out hooks where `enabled` is explicitly `false`, and skip any hook whose `command` is `speckit.pstack.tasks` or `speckit.tasks` (see the recursion rule above).
- Do not interpret or evaluate hook `condition` expressions; a non-empty `condition` is skipped and left to the HookExecutor implementation.
- For each executable hook, emit the mandatory or optional block exactly as in the pre-execution section, substituting the `after_tasks` hook's `extension`, `command`, `description`, and `prompt`. A mandatory hook MUST be invoked and awaited; emitting the block alone does not run it.

## Hand off

Next step is `__SPECKIT_COMMAND_PSTACK_IMPLEMENT__`.
