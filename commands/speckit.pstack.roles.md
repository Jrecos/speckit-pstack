---
description: "Resolve pstack dispatch lanes: real pstack plugin roles when present, yaml fallback, else inline"
---

# Pstack Roles

Resolve which worker each dispatch lane uses. The extension owns the lane-to-pstack-role mapping; the pstack plugin owns the model choices. Precedence:

1. **pstack plugin present** (its role rule exists and parses, or pstack agent resolution is available in this session). Lanes map onto real pstack roles:

| Lane      | pstack role            | Agent kind |
|-----------|------------------------|------------|
| tasks     | `judgment and prose`   | general    |
| implement | `feature, refactoring` | poteto     |
| verify    | `interrogate reviewers`| readonly   |
| swarm     | `swarm workers`        | poteto     |

   Dispatch through the pstack agent resolution for that role (`pstack_agent {role, kind}` where the tool exists; otherwise the prepared native agent the mapping names). Panel roles resolve to their first entry.

2. **No pstack.** Fallback to `.specify/extensions/pstack/pstack-config.yml`: each lane uses `roles.<lane>` (a plain model selector string) when non-empty, dispatched as a subagent on that model by whatever mechanism this harness provides.

`sync` moves non-empty yaml selectors into the mapped pstack roles through the pstack plugin's own writer. It never hand-edits the rule file. See Sync mode.

## User Input

```text
$ARGUMENTS
```

## Steps

1. **Detect pstack.** Check `~/.omp/agent/rules/pstack-models.md` (or this session's pstack role resolution). Note whether the four mapped role lines are configured; an unconfigured role line falls through to the next precedence level for that lane.

2. **Read the fallback config.** Load `.specify/extensions/pstack/pstack-config.yml` if present; read the `roles` selector strings and `parallel.max_workers`. If the file is missing, copy `pstack-config.template.yml` into place and say so.

3. **Report the resolved table**, exactly:

```
| Lane      | Source              | Worker                      |
|-----------|---------------------|-----------------------------|
| tasks     | pstack|fallback|inline | <pstack role / model / -> |
| implement | pstack|fallback|inline | <...>                      |
| verify    | pstack|fallback|inline | <...>                      |
| swarm     | pstack|fallback|inline | <...>                      |
| parallel  | config              | max_workers=<n>             |
```

Every downstream dispatch in `speckit.pstack.implement` and `speckit.pstack.verify` MUST route through this table. If this command has not run in this session, run `__SPECKIT_COMMAND_PSTACK_ROLES__` first.

## Sync mode

Run with `sync` in `$ARGUMENTS`. The yaml selectors you edited become the pstack role lines, without hand-editing the rule file.

1. **Detect pstack** as in step 1. Absent: print "Nothing to sync: no pstack role rule exists on this machine. The project yaml is already the config." and stop.
2. **Collect selectors.** From the fallback config, take every lane whose `roles.<lane>` selector is non-empty. None: print "Nothing to sync: every yaml selector is empty." and stop.
3. **Read the current map** with the `pstack_models` device, action `show`. Never parse the rule file by hand. The device is unavailable in this session: print that reason and stop with nothing written.
4. **Build the next map.** Keep every role entry and the pool exactly as shown, except the role mapped to each collected lane:

   | Lane      | pstack role             |
   |-----------|-------------------------|
   | tasks     | `judgment and prose`    |
   | implement | `feature, refactoring`  |
   | verify    | `interrogate reviewers` |
   | swarm     | `swarm workers`         |

   The selector replaces the role's entries. Replacing a multi-entry panel role (verify) with one selector shrinks that panel; the diff in the next step shows it.
5. **Confirm.** Print every changed role line as `role: <old> -> <new>`. If none changed, print "Already in sync; nothing to write." and stop. State that the write is global (every project on this machine) and reversible by re-running `/setup-pstack`. Proceed only after an explicit yes.
6. **Save.** Call the device with action `save`, passing the full role map and the unchanged pool. Report the outcome verbatim. A selector outside the approved pool fails validation before publication; report the error and stop, nothing is half-written.
