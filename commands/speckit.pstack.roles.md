---
description: "Resolve pstack dispatch lanes: real pstack plugin roles when present, yaml fallback, else inline"
---

# Pstack Roles

Resolve which worker each dispatch lane uses. The lane table below is the one canonical table for that mapping. The sync steps and the README refer to it and never repeat it. Precedence is per lane, three levels:

1. pstack present and the lane's role line is configured. Dispatch through that pstack role. The lane's yaml selector is inert while this holds.
2. Otherwise (pstack absent, or the lane's role line unconfigured). Use the lane's `roles.<lane>` yaml selector when non-empty, dispatched as a subagent on that model by whatever mechanism the harness provides.
3. Empty or missing. Run inline in this session, no subagent.

## Canonical lane table

| Lane | pstack role | Agent kind | Dispatched by |
|---|---|---|---|
| verify | `interrogate reviewers` | readonly | `speckit.pstack.verify` check batches |
| swarm | `swarm workers` | poteto | `speckit.pstack.implement` `[P]` batches |

Resolve a lane through the pstack agent resolution for its role, `pstack_agent {role, index, kind}` where that device exists. The verify lane is a panel role and requires an index. Use its first entry when the caller does not name one. Where the device does not exist in the session, the session's own pstack role resolution names the agent to use.

## User Input

```text
$ARGUMENTS
```

## Steps

1. **Detect pstack.** The pstack plugin is present when its rule file exists (`~/.omp/agent/rules/pstack-models.md`) or the session resolves pstack roles. Check existence only. Never read or parse the file's contents. Its format is closed and parser-validated, and the sync path goes through the device instead. Note whether each mapped role line is configured. An unconfigured lane falls through to the next precedence level.

2. **Read the fallback config.** Load `.specify/extensions/pstack/pstack-config.yml`. Read `roles.verify`, `roles.swarm`, and `parallel.max_workers`. `max_workers` must be an integer of at least 1. When it is not, report it as invalid and use 3. When the file is missing, create it with exactly the content below and say so:

   ```yaml
   # pstack for spec-kit - fallback dispatch config.
   # Installed to .specify/extensions/pstack/pstack-config.yml (edit there).
   #
   # Consulted when a lane's pstack role is unconfigured or pstack is absent.
   # A non-empty selector can be pushed into the pstack role with
   # /speckit.pstack.roles sync; that write is machine-global and gated.

   roles:
     # Fallback model selectors for harnesses with no pstack. Empty = inline.
     verify: ""
     swarm: ""

   parallel:
     max_workers: 3   # concurrent subagents per [P] batch
   ```

3. **Report the resolved table**, one row per lane plus the parallel row. Source is one of pstack, fallback, inline, with the worker in the last column. Keep the fenced-table shape the current file uses. No pipes inside cells.

```
| Lane     | Source                       | Worker                     |
|----------|------------------------------|----------------------------|
| verify   | pstack or fallback or inline | <pstack role, model, or -> |
| swarm    | pstack or fallback or inline | <pstack role, model, or -> |
| parallel | config                       | max_workers=<n>            |
```

Downstream dispatch in the implement and verify commands resolves through this table, and those commands tell the agent to run this command first when no table is in hand.

## Sync mode

Run with `sync` in `$ARGUMENTS`. `sync` moves non-empty yaml selectors into the mapped pstack roles through the pstack plugin's own writer. It never hand-edits the rule file. Only the two lanes above sync, because only they have dispatch sites.

1. **Detect pstack** as in step 1. Absent: print "Nothing to sync: no pstack role rule exists on this machine. The project yaml is already the config." and stop.
2. **Collect selectors.** From the fallback config, take `verify` and `swarm` whose selectors are non-empty. None: print "Nothing to sync: every yaml selector is empty." and stop.
3. **Read the current map** with the `pstack_models` device, action `show`. Never parse the rule file by hand. The device is unavailable: print that reason and stop with nothing written. Tell the user to save this printed map if they want a restore reference. It is the only one this command produces.
4. **Build the next map.** Keep every role entry and the pool exactly as shown, except the roles mapped to the collected lanes per the canonical table above. The selector replaces the role's entries. Replacing a multi-entry panel role (verify) with one selector shrinks that panel.
5. **Gate.** Print the full next map, every role line exactly as `save` will receive it, not only the changed lines. Print one explicit line when a panel shrinks, naming the role and the entry count before and after. Print the changed roles as `role: <old> -> <new>`. State that the write is global to this machine, and that `/setup-pstack` re-derives recommendations and does not restore the previous map. The step 3 output is the restore reference. Then end the turn asking the user to reply with the single word `write` to proceed. Only a bare affirmative next user message counts as consent, and `write` is the only word that counts, because `sync` would re-invoke this command. A reply containing arguments or conditions does not count. Re-print the gate and wait again. In a non-interactive session, print the gate and stop with nothing written, saying consent is impossible here.
6. **Save.** Call the device with action `save`, passing the full role map and the unchanged pool. Report the outcome verbatim. A selector outside the approved pool fails validation before anything is published. Report the error and stop, nothing is half-written.
