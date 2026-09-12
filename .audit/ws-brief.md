# Brief: apply the five accepted review workstreams to speckit-pstack

You are editing the extension at /home/jreco/dev/speckit-pstack. Exactly seven files exist and you may touch six of them (never LICENSE, never create new files):

- extension.yml
- pstack-config.template.yml
- commands/speckit.pstack.roles.md
- commands/speckit.pstack.tasks.md
- commands/speckit.pstack.implement.md
- commands/speckit.pstack.verify.md
- README.md

Do not run formatters, linters, specify, or omp. The parent owns verification. Minimal diff: do not reword lines that these prescriptions do not change.

## Context you need

The extension ships four slash commands as markdown executed by an agent. Two lanes survive this review: `verify` (pstack role `interrogate reviewers`, readonly, a panel role needing an index) and `swarm` (pstack role `swarm workers`, poteto). The `tasks` and `implement` lanes are dead (no dispatch site ever resolves them; `tasks` runs inline in-session, `implement` runs in-session except `[P]` batches which use the swarm lane) and get deleted everywhere.

Cross-command references must use tokens (`__SPECKIT_COMMAND_PSTACK_ROLES__` etc), never hard-coded `/speckit.pstack.*` paths. Core speckit commands are referred to in prose only ("the core implement step"), never as a path.

## Tone rules (all prose you write or change)

- No em dash, no en dash, no hyphen used as a dash. Periods and commas only.
- No colon as a mid-sentence connector. A colon introducing a list or code block is fine.
- Sentence case headings, straight quotes, plain words. Never "utilize", "leverage", "ensure" where "make sure" or a concrete verb fits.
- No pipe characters inside markdown table cells.
- Imperative voice, condition before instruction, one thought per sentence.
- Keep `**Check:**` and new `**Writes:**` bold-label line format.

## File 1: pstack-config.template.yml (replace whole file)

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

## File 2: extension.yml

- `extension.description` becomes: "Task-contract rigor for spec-kit: verifiable-unit tasks with named acceptance checks, disjoint-write parallel batches, evidence-gated completion, independent re-proof"
- roles command description becomes: "Resolve pstack dispatch lanes (verify, swarm): pstack roles, yaml fallback, inline; gated sync via the pstack writer"
- tasks command description becomes: "Apply the pstack task contract to tasks.md: verifiable units, data-shape-first, honest parallel markers with declared writes"
- implement command description becomes: "Implement tasks.md with pstack rigor: shape first, disjoint-write [P] batches, parent-applied verdicts, evidence-gated completion"
- verify command description is unchanged. Nothing else in the manifest changes.

## File 3: commands/speckit.pstack.roles.md (restructure)

New structure, sections in this order.

### Intro and precedence

State that this command resolves which worker each dispatch lane uses, and that the lane table below is the one canonical table (the sync steps and README refer to it, they never repeat the mapping). Precedence is per lane, three levels:

1. pstack present and the lane's role line is configured. Dispatch through that pstack role. The lane's yaml selector is inert while this holds.
2. Otherwise (pstack absent, or the lane's role line unconfigured). Use the lane's `roles.<lane>` yaml selector when non-empty, dispatched as a subagent on that model by whatever mechanism the harness provides.
3. Empty or missing. Run inline in this session, no subagent.

### Canonical lane table

| Lane | pstack role | Agent kind | Dispatched by |
|---|---|---|---|
| verify | `interrogate reviewers` | readonly | `speckit.pstack.verify` check batches |
| swarm | `swarm workers` | poteto | `speckit.pstack.implement` `[P]` batches |

Below the table, one paragraph on resolution mechanics: resolve through the pstack agent resolution for the role, `pstack_agent {role, index, kind}` where that device exists. The verify lane is a panel role and requires an index; use its first entry when the caller does not name one. Where the device does not exist in the session, the session's own pstack role resolution names the agent to use.

### User Input (unchanged shape)

### Steps

1. **Detect pstack.** The pstack plugin is present when its rule file exists (`~/.omp/agent/rules/pstack-models.md`) or the session resolves pstack roles. Check existence only. Never read or parse the file's contents; its format is closed and parser-validated, and the sync path goes through the device instead. Note whether each mapped role line is configured; an unconfigured lane falls through to the next precedence level.
2. **Read the fallback config.** Load `.specify/extensions/pstack/pstack-config.yml`. Read `roles.verify`, `roles.swarm`, and `parallel.max_workers`. `max_workers` must be an integer of at least 1; when it is not, report it as invalid and use 3. When the file is missing, create it with exactly the content below and say so:

   (inline the same yaml block as the template, verbatim, as a fenced code block)

3. **Report the resolved table**, one row per lane plus the parallel row. Source is one of pstack, fallback, inline, with the worker in the last column. Keep the fenced-table shape the current file uses. No pipes inside cells.

### Sync mode

Intro: `sync` moves non-empty yaml selectors into the mapped pstack roles through the pstack plugin's own writer. It never hand-edits the rule file. Only the two lanes above sync, because only they have dispatch sites.

1. **Detect pstack** as in step 1. Absent: print "Nothing to sync: no pstack role rule exists on this machine. The project yaml is already the config." and stop.
2. **Collect selectors.** From the fallback config, take `verify` and `swarm` whose selectors are non-empty. None: print "Nothing to sync: every yaml selector is empty." and stop.
3. **Read the current map** with the `pstack_models` device, action `show`. Never parse the rule file by hand. The device is unavailable: print that reason and stop with nothing written. Tell the user to save this printed map if they want a restore reference; it is the only one this command produces.
4. **Build the next map.** Keep every role entry and the pool exactly as shown, except the roles mapped to the collected lanes per the canonical table above. The selector replaces the role's entries. Replacing a multi-entry panel role (verify) with one selector shrinks that panel.
5. **Gate.** Print the full next map, every role line exactly as `save` will receive it, not only the changed lines. Print one explicit line when a panel shrinks, naming the role and the entry count before and after. Print the changed roles as `role: <old> -> <new>`. State that the write is global to this machine, and that `/setup-pstack` re-derives recommendations and does not restore the previous map; the step 3 output is the restore reference. Then end the turn asking the user to reply with the single word `sync` to proceed. Only a bare affirmative next user message counts as consent. A reply containing arguments or conditions does not count; re-print the gate and wait again. In a non-interactive session, print the gate and stop with nothing written, saying consent is impossible here.
6. **Save.** Call the device with action `save`, passing the full role map and the unchanged pool. Report the outcome verbatim. A selector outside the approved pool fails validation before anything is published; report the error and stop, nothing is half-written.

Delete the old mapping table inside sync step 4 (it now points at the canonical table). Delete the sentence "Every downstream dispatch ... run __SPECKIT_COMMAND_PSTACK_ROLES__ first." from step 3 of the old file; replace with one sentence that downstream dispatch in implement and verify resolves through this table, and implement and verify themselves tell the agent to run this command first when no table is in hand.

## File 4: commands/speckit.pstack.tasks.md

- Opening paragraph: delete the parenthetical about the `after_tasks` hook. It reads "This command runs after task generation and before any implementation."
- R4 becomes: "**R4 Honest parallel markers.** A task gets `[P]` only when its acceptance check can pass while every other `[P]` task in the same phase also runs. The marker is earned with data, not assertion: the task lists every file it will write on a `**Writes:**` line, and no two `[P]` tasks in the same phase list the same file. A shared file, a shared migration, or an ordering assumption means no marker. When in doubt, remove the marker."
- Repair step gains two bullets: one that adds or completes `**Writes:**` lines on every `[P]` task and removes the marker where the file set is not known; one for split ids: when a task splits, its parts take suffix ids (T012 becomes T012a and T012b) so evidence stays addressable; unchanged tasks keep their ids.
- Everything else keeps its current shape.

## File 5: commands/speckit.pstack.implement.md

- Intro paragraph: "Execute the feature's tasks.md the pstack way. This replaces the core implement step for this run. Same artifacts, same checkboxes; completion is evidence-gated and independent work fans out under disjoint writes."
- Pre-condition 2 becomes: "Read FEATURE_DIR/tasks.md in full. Audit it against all five contract rules, not just Check presence. Any violation: run `__SPECKIT_COMMAND_PSTACK_TASKS__` first and re-read. Never fan out on an unaudited list."
- Per-task loop, replace step 2 with a Choose-the-lane block containing these five labeled parts:
  - **Lane.** A `[P]` task with at least one other pending `[P]` task in the same phase dispatches in one batch through the swarm lane (roles table). Any other task runs in this session.
  - **Before dispatch.** Every `[P]` task in the batch must carry a `**Writes:**` line naming the files it will touch. Refuse the batch when a Writes line is missing or when any two lists overlap; that is a contract violation, run `__SPECKIT_COMMAND_PSTACK_TASKS__`. Inside a git work tree the tree must be clean before dispatch; stash or commit unrelated work first.
  - **Dispatch.** One subagent per task, at most `parallel.max_workers` concurrent. Each brief carries the task text verbatim, its Check line, its Writes list, the relevant plan.md and spec.md sections, and these rules: run the Check and report PASS or FAIL with a one-line output excerpt; list every file you touched; never edit tasks.md; never commit; touch nothing outside your Writes list.
  - **No subagent facility.** Run the batch's tasks serially in this session under the same rules, and say so in the report.
  - **Return.** The parent applies every verdict. Check each report's touched-files list against its Writes list and against `git diff --name-only`; a file changed that no report names is a violation. Only then mark passing tasks `[X]` and write their evidence lines yourself.
- Step 3 (Prove, then check) gains the supersession rule: one pstack note line per task; a new note for a task replaces that task's previous pstack note line, it never appends.
- Step 4 (design minute): add at the end: for a boundary crossing, record the settled signature (caller, types, failure mode) in the task's note line alongside the evidence.
- Step 5 (Commit per unit) becomes: "Inside a git work tree, commit after each task or coherent `[P]` batch passes its check, staging exactly the files the task or batch wrote (the union of its Writes lists), never `git add -A` or `git add .`. Use a conventional title naming the task ids. Outside a work tree, skip committing and say so once in the report."
- Stop conditions, the middle bullet becomes: "A subagent violates the contract (touched a file outside its Writes list, edited tasks.md, invented a check): inside a work tree, revert its files with `git checkout -- <files>`; outside a work tree, list its files in the report for manual removal. Then fix the task list and re-dispatch."

## File 6: commands/speckit.pstack.verify.md

- Step 1 becomes: "Enumerate the proof set. Every checked task (match `[X]` case-insensitively, `[x]` counts) and its `**Check:**` line. A checked task with no Check line takes verdict VOID immediately, reason `no Check line`."
- Step 2 becomes a run-and-verdict block: "Run each check in this session by default. Delegate a phase's checks through the verify lane only when the dispatch returns each verdict with the raw output excerpt it observed; transcribed verdicts without excerpts are self-report and do not count. Each verdict is one of:
  - `PASS`. The check ran and the result matched. Record a one-line excerpt of the actual output, and answer the masking question: what would make this check pass while the task is broken. Name it, or say nothing could.
  - `FAIL`. The check ran and the result differed. Record the actual output excerpt.
  - `VOID`. The check cannot run (target gone, test missing, command unknown), or the task has no Check line."
- Step 3 (Uncheck phantoms) gains: one pstack note line per task; a new note replaces that task's previous pstack note line, never appends. And the routing sentence becomes: "Do not fix code here. A FAIL routes back to `__SPECKIT_COMMAND_PSTACK_IMPLEMENT__`. A VOID routes to `__SPECKIT_COMMAND_PSTACK_TASKS__` to repair the Check line first; implement cannot fix Check text."
- Step 4 becomes: "Cross-check the surface. Sibling tasks are the other tasks under the same phase heading. Run the deduplicated union of the phase's checks once. When any task in a phase ended unchecked, re-run every check in that phase; a FAIL from this pass is a new verdict, uncheck that task too and count it in M. This is where a check that passes only because a sibling masks it shows up."
- Report block: keep the table; the trailing prose becomes "All PASS is the only green. M plus K above zero is not a partial success. Route FAILs through `__SPECKIT_COMMAND_PSTACK_IMPLEMENT__` and VOID Check lines through `__SPECKIT_COMMAND_PSTACK_TASKS__`, then re-run this command." Keep the example note line shape (`> pstack verify (T012): FAIL ...`), adding a PASS example with its excerpt and masking answer.

## File 7: README.md

Restructure to this content, keeping the Install section as is.

- Intro: keep the first paragraph, then add a scope-cut paragraph: "This extension carries the task-contract subset of pstack rigor: verifiable units, named acceptance checks, evidence-gated completion, and parallel batches with declared disjoint writes. Poteto's playbooks and the remaining principles are out of scope."
- Commands table: keep, it is accurate.
- Task contract section: five rules updated to match the command file, R4 with the Writes requirement in one line.
- Implementation section: describe the loop as it now works. Shape first, in-session by default, `[P]` batches through the swarm lane with Writes-list disjointness enforced by the dispatcher, subagents never write tasks.md and never commit, the parent applies verdicts, checks touched files against `git diff --name-only`, commits stage only the batch's files, evidence lines supersede.
- Verification section: re-runs every checked task's check in-session, PASS needs a recorded output excerpt plus the masking question, phantom completions get unchecked, VOID Check lines route to the tasks command for repair.
- Roles and dispatch: state per-lane precedence correctly in prose (a lane with a configured pstack role uses it and its yaml selector is inert; otherwise the yaml selector when non-empty; otherwise inline), name the two lanes and their pstack roles in a small table identical to the canonical one, and say the canonical table lives in the roles command. Describe sync honestly: prints the full next map and a panel-shrink line, waits for a separate affirmative message as consent, the write is machine-global, `/setup-pstack` does not restore the prior map, the printed pre-sync map is the restore reference.
- Requirements: spec-kit >= 1.0.0, plus "Tested on OMP with bash. Commands render for other agents through spec-kit's token resolution. `[P]` batches need a harness with a subagent facility; without one they run serially in-session."

## Acceptance criteria (self-check before reporting)

- grep the six files: no `tasks` or `implement` lane rows or yaml keys anywhere; no `after_tasks`; no `principle-driven`; no `swarm tasks` phrase; no `|` inside table cells; no em dash (—) or en dash (–); no hard-coded `/speckit.pstack.` or `/speckit.implement` paths outside the template yml comment; tokens `__SPECKIT_COMMAND_` intact wherever a cross-reference exists.
- The inline yaml block in roles.md matches the template's roles and parallel keys exactly.
- extension.yml still valid yaml, version unchanged.

Report back: per file, one line on what changed; then the grep self-check output.
