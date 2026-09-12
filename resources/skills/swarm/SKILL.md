---
name: swarm
description: "Fan out N parallel workers, drain them, and return one report. Use for /speckit.pstack.swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
disable-model-invocation: true
---

# Swarm

Fan out N parallel local workers. They may cover separate slices, race the same brief, or mix both. The parent waits, aggregates, and returns one report.

## Start

Open a todolist with one entry per phase before launching anything.

1. Frame
2. Fan out
3. Aggregate
4. Report

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare `first pass`, `rank all`, or `best-of` before spawning.
3. Set N from the user or derive it from the shape. N is total workers, not the concurrency limit; keep the in-flight count within the role map's `parallel.max_workers`.
4. Resolve the worker model from role `swarm workers` in the project role map (`.specify/extensions/pstack/runtime/pstack-native.py role-plan --role "swarm workers"`). An empty role is a setup error, not a reason to pick a model yourself. For a model race, name each arm's model up front, and only `swarm workers` may carry an explicit race model: it must be concrete and already in the map's approved `pool`, and it is passed as `--race-model`, never as a free-form selector.
5. Give each worker its own writable output when it writes.

## Phase B: Fan out

Spawn all N workers in one batch with the host's general-purpose subagent, dispatched in the background, on the resolved model. There is no cloud environment here: the only worker environments are this machine and an isolated local worktree, and the work stops when the machine or the process stops. Say which one each worker used.

When a worker must start from a non-default branch, give it an isolated local worktree checked out at that branch. There is no cloud base-branch parameter: the worktree and the checkout are the native equivalent.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence.

If a worker drops out, proceed with N-1 and note it.

## Phase C: Aggregate

Read the terminal results. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts.

## Phase D: Report

Return one consolidated in-chat report with the table, issue one-liners, gaps or dropouts, and the race rule when used.
