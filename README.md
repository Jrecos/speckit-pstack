# pstack for spec-kit

A [spec-kit](https://github.com/github/spec-kit) extension that brings [pstack](https://github.com/cursor/plugins/tree/main/pstack) rigor to the spec-driven workflow. Spec-kit decides what to build; this extension enforces how the tasks get implemented: every task is a verifiable unit with a named proof, independent tasks fan out to subagents, and no task is done until its check passes against the real artifact.

Adapted from poteto's pstack (MIT). See LICENSE.

## Install

```bash
specify extension add pstack --from https://github.com/jreco/speckit-pstack/archive/refs/tags/v0.1.0.zip
```

For development, install from a local checkout:

```bash
specify extension add --dev /path/to/speckit-pstack
```

## Commands

The commands replace the corresponding core steps. Run them instead of the built-ins.

| Command | Replaces | What it enforces |
|---|---|---|
| `/speckit.pstack.tasks` | runs after `/speckit.tasks` | The task contract (below) |
| `/speckit.pstack.implement` | `/speckit.implement` | Shape-first, evidence-gated, fanned-out execution |
| `/speckit.pstack.verify` | none (new gate) | Independent re-proof of every checked task |
| `/speckit.pstack.roles` | none (setup) | Role-to-model dispatch mapping |

## The task contract

`/speckit.pstack.tasks` audits and repairs `tasks.md` against five rules:

1. **Verifiable unit.** Each task is small enough that one step proves it done.
2. **Named acceptance check.** Every task carries a `**Check:**` line with the exact command, value, or surface that proves it.
3. **Data shape first.** Producers of a shape precede its consumers.
4. **Honest parallel markers.** `[P]` only when the task's check passes while every other `[P]` task in the phase also runs.
5. **No silent scope.** New dependencies and public-surface changes are named in the task text.

## Implementation with rigor

`/speckit.pstack.implement` executes the task list. For each task it defines the data shape before consuming code, dispatches `[P]` batches to subagents (up to `parallel.max_workers` from the config), marks a task `[X]` only after its check ran and passed, and records one evidence line under the task. Failures stop after two fix attempts and are reported as remaining work.

## Verification

`/speckit.pstack.verify` re-runs every checked task's check in a fresh pass and unchecks any task whose proof now fails or cannot run. All PASS is the only green.

## Roles and dispatch

Subagent dispatch resolves in this order:

1. **pstack plugin present.** Lanes map onto real pstack roles: `tasks` to "judgment and prose" (general), `implement` to "feature, refactoring" (poteto), `verify` to "interrogate reviewers" (readonly), `swarm` to "swarm workers" (poteto). Model choices come from the pstack role rule owned by `/setup-pstack`.
2. **No pstack.** Fallback to `.specify/extensions/pstack/pstack-config.yml`: each lane uses `roles.<lane>` (a plain model selector string), or runs inline when empty.

`/speckit.pstack.roles` prints the resolved table.

`/speckit.pstack.roles sync` pushes non-empty yaml selectors into the mapped pstack roles through the pstack plugin's own writer (`pstack_models save`). It reads the current map, shows a before/after diff for each changed role line, and saves atomically after you confirm. A selector outside the approved pool fails validation and nothing is written. The write is global to the machine. The command never hand-edits the rule file.

## Requirements

- spec-kit >= 1.0.0
- An OMP integration project (tested against `--integration omp`); commands render for other agents via spec-kit's standard token resolution, but subagent fan-out only degrades gracefully on agents without a subagent facility
