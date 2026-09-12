---
description: "Resolve pstack dispatch lanes from the project role map and report what this host can actually dispatch"
---

# Pstack Roles

Resolve which worker each dispatch lane uses, from this project, with no machine-global state.

Read the shared contract first: `.specify/extensions/pstack/runtime/host-contract.md`. It owns the 17 role labels, their meanings, the alias rules, and the dispatch paths. This command never repeats them.

## User Input

```text
$ARGUMENTS
```

## Resolution order (per lane)

1. **The project role map.** `.specify/extensions/pstack/pstack-models-config.yml`, resolved through `python3 .specify/extensions/pstack/runtime/pstack-native.py role-plan --role "<label>"`. This is the source of truth for every lane. The plan's `kind` says how many configured selectors the role holds: `single`, `panel`, or `choose-one`.
2. **The host's own subagent facility**, when one exists, dispatched with the role plan's legs. A `panel` runs one worker per configured entry, indices 1-based, duplicates preserved, and only the selected leg when you passed `--index`. A `choose-one` role supplies exactly one judge chosen from its configured pool, which you inspect with `config-show` before selecting an index. A `single` role runs one worker. Resolve `--index` for a multi-selector lane only; a repeated single-selector worker's ordinal is not a selector index.
3. **The Spec Kit workflow path**, when no native subagent facility exists and the capability report's `cli` entry is available: `specify workflow run .specify/extensions/pstack/workflows/dispatch.yml` with the request the helper builds, never a model you supply. An `inherit-parent` leg needs `--parent-model` with the concrete current model; the helper refuses an alias, an absent parent, or a model belonging to another role.
4. **Inline in this session**, only when neither a native subagent facility nor the workflow path exists. Say so in the run's report; inline work is not independent verification.

An empty role, a selector outside `pool`, or a selector the host rejects is a hard failure to report. There is no cross-family substitution and no silent default.

## Canonical lane table

| Lane | Role | Dispatched by |
|---|---|---|
| workspace assembly | `swarm workers` | `__SPECKIT_COMMAND_PSTACK_IMPLEMENT__` parallel batches |
| independent verification | `interrogate reviewers` | `__SPECKIT_COMMAND_PSTACK_VERIFY__` check batches |
| implementation by workload | the host contract's workload classifier | per-task work in `__SPECKIT_COMMAND_PSTACK_IMPLEMENT__` |
| prose and release judgment | `judgment and prose` | documentation, PR and commit text, release notes |
| hardest design and algorithms | `hardest tasks` | cross-cutting design, concurrency, subtle algorithms |

The remaining roles belong to the routed skills that own them (`how`, `why`, `reflect`, `arena`, `architect`, `interrogate`). The host contract's classifier is the one canonical work-to-role mapping; this table does not replace it.

## Steps

1. **Show the current map.** Run `python3 .specify/extensions/pstack/runtime/pstack-native.py config-show` and print each role with its configured selectors and the model each selector resolves to, marking empty roles as needing configuration. The role's `kind` comes from `role-plan`, which the host contract defines. Use the same `config-show` response's `pristine` flag in step 3.
2. **Check this session.** Run `python3 .specify/extensions/pstack/runtime/pstack-native.py capability-report`, then inspect live tools or supplied harnesses for degraded surfaces. Print the observed status and reason, plus the paths block (`skills_dirs`, `runs_dir`, `instruction_file`). A static host mapping is not proof of live access.
3. **Set or migrate.** When a role needs a value, the `speckit.pstack.setup-pstack` command owns the write path. Inspect `.specify/extensions/pstack/pstack-config.yml` whenever it exists and its `roles.verify` or `roles.swarm` hold a non-empty value, whether or not the role map already exists: those legacy selectors are the user's earlier choices and they are surfaced before anything is written. When `config-show` reports `pristine` (the map is absent or still the untouched scaffold), show the migration proposal, preserve unrelated metadata, and use the confirmed atomic write. When the map is customized, show a delta for explicit reconciliation instead, and never run migration over it. Re-running `config-migrate` with the values already applied is a byte-preserving no-op.
4. **Report.** End with the resolved table for this machine, one line per lane naming the role, the selector or `inherit-parent`, and the dispatch path (`native subagent`, `workflow`, or `inline`). Name every lane that will run inline, because that is the run's independence limit.
