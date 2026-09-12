# pstack host contract

Every pstack command and every worker it delegates to loads this file. It is the
one place that names how work is dispatched on this host, so no resource repeats
it. Read it before the skill or playbook you were invoked for.

## Where things live

| Thing | Path |
|---|---|
| This contract | `.specify/extensions/pstack/runtime/host-contract.md` |
| Runtime helper | `.specify/extensions/pstack/runtime/pstack-native.py` |
| Host mappings | `.specify/extensions/pstack/runtime/host-contexts.json` |
| Role map | `.specify/extensions/pstack/pstack-models-config.yml` |
| Legacy lane selectors | `.specify/extensions/pstack/pstack-config.yml` |
| Translated skills, playbooks, principles | `.specify/extensions/pstack/resources/` |
| Agent contracts | `.specify/extensions/pstack/resources/agents/` |
| Dispatch workflow | `.specify/extensions/pstack/workflows/dispatch.yml` |
| Per-run worker files | `.specify/pstack/runs/<timestamp>-<token>-<label>/` |

Run the helper as `python3 .specify/extensions/pstack/runtime/pstack-native.py <command>`.
A successful command prints one JSON object on stdout. A semantic failure prints
`{"error": ...}` on stderr and exits non-zero, and that JSON is the result you
branch on. A malformed command line is a different thing: argparse prints its own
usage text on stderr and exits non-zero, so usage text means the caller built the
command wrong, not that the helper reported a failure.

## Role resolution

The project role map holds the 17 upstream role labels. Resolve a role before
any delegation, never from memory of an earlier session:

```
python3 .specify/extensions/pstack/runtime/pstack-native.py role-plan --role "<label>"
```

The plan carries `kind`, `legs`, and `max_workers`. `kind` is `panel`,
`choose-one`, or `single`, and it describes how many configured selectors the role
holds. A leg is `{index, model, inherit}`. `inherit` true means the worker runs on
the current model, which the host expresses by omitting the model.

- `panel` (`arena runners`, `architect runners`, `interrogate reviewers`) holds an
  ordered selector list and runs one worker per configured entry, indices 1-based,
  duplicates preserved. An unindexed plan exposes every leg; `--index N` exposes
  the selected leg only.
- `choose-one` (`arena cross-judge pool`) holds a candidate list, and the caller
  selects exactly one configured entry, preferring a model family different from
  the parent and the runner panel. Inspect the configured pool with `config-show`
  before selecting an index, and require an explicit index when the choice is
  ambiguous. Never allocate every candidate the way a panel would.
- `single` is every other role: one configured selector, one worker per task.
- `inherit-parent` and `auto` are aliases for the current model. On native
  subagent dispatch, omit the model. On CLI dispatch, pass the concrete current
  model as `--parent-model`; the helper refuses an alias or an absent parent
  rather than letting the CLI choose a default.
- A selector outside the map's `pool` fails validation. There is no silent
  substitution and no fallback to a different model family.

Configuration commands, all project-local: `config-init`, `config-show`,
`config-set`, `config-save`, `config-migrate`. The `speckit.pstack.setup-pstack` command
owns the workflow around them, including the legacy lane selectors.

`config-show` reports `pristine`, using the same predicate migration does: true
when the map is absent or still the untouched scaffold, false once a role or the
pool has been customized. Setup always inspects
the legacy `.specify/extensions/pstack/pstack-config.yml` while setting up, whether
or not the role map already exists, so non-empty `roles.verify` or `roles.swarm`
values reach the user even when a scaffold is already in place. A pristine map
gets the migration proposal, unrelated metadata preserved, and the confirmed
atomic write; a customized map gets a delta for explicit reconciliation instead,
and migration never overwrites it. Re-running `config-migrate` with the values it
already applied is a byte-preserving no-op.

## Workload classifier

This table is the one mapping from work to role. The commands and the routed
skills route through it instead of keeping their own copies.

| Work | Role |
|---|---|
| Feature work and behavior-preserving refactors | `feature, refactoring` |
| Reproducing and fixing a defect | `bug-fix` |
| A measured performance change | `perf-issue` |
| Sustained metric improvement against a target | `hillclimb` |
| Prose, review judgment, release notes, PR and commit text | `judgment and prose` |
| Cross-cutting design, gnarly concurrency, subtle algorithms | `hardest tasks` |
| `how` exploration | `how explorer` |
| `how` synthesis | `how explainer` |
| `why` investigators | `why investigators` |
| `why` synthesis | `why synthesizer` |
| `reflect` tooling lens | `reflect tooling` |
| `reflect` judgment, divergent, and synthesis lenses | `reflect judgment, divergent, synthesizer` |
| `arena` candidate runners | `arena runners` |
| `arena` cross-judge | `arena cross-judge pool` |
| `swarm` workers | `swarm workers` |
| `architect` design runners | `architect runners` |
| `interrogate` reviewers | `interrogate reviewers` |

A task that writes code and matches none of the code-workload lines is a
`feature, refactoring` dispatch; a task that writes no code is a
`judgment and prose` dispatch. `hardest tasks` covers a change whose difficulty
sits in the design or the concurrency, not in the file count. Never fall back to
one role for everything, and never invent a role outside the 17.

## Dispatch

Prefer the host's native subagent facility. It supplies the host's permission model
and real parallelism. The brief names this contract, the worker contract, the
routed skill or playbook, the task, its scope, its check, its report path, and its
lifecycle authority. The brief decides whether that worker may edit, commit, push,
merge, or update task state.

Use the Spec Kit workflow when no native subagent facility exists or the caller
asks for CLI dispatch. Allocate prompt and report paths first:

```
python3 .specify/extensions/pstack/runtime/pstack-native.py run-new --role "<label>"
```

`run-new --index N` allocates the pair for configured selector N of a
multi-selector role, and the returned leg keeps that configured `index` next to its
allocation `ordinal`. `--legs N` repeats a `single` role and is rejected for a
configured panel or choose-one role: it must never truncate or multiply configured
entries. A repeated single-selector run's ordinal is not a dispatch selector index.

Write the brief to the returned prompt path. Build the one authoritative dispatch
request with the helper, which is role-first: it derives the model from the role
map rather than accepting a raw model. It emits exactly `integration`, `role`,
`index`, `model_source`, `model`, `prompt_file`, and `report_file`, and rejects an
unapproved model, a model belonging to another configured role, a stale role/model
binding, an invalid role/index/source combination, a race override outside the
pool, path escapes, symlinks, cross-run paths, and an existing report:

```bash
request_json=$(
  python3 .specify/extensions/pstack/runtime/pstack-native.py dispatch-request \
    --integration "$integration" \
    --role "$role" \
    --prompt-file "$prompt_file" \
    --report-file "$report_file"
) || exit

PSTACK_DISPATCH_REQUEST="$request_json" \
  specify workflow run .specify/extensions/pstack/workflows/dispatch.yml --json
```

**One role, one index.** The request names the role and, for a multi-selector role,
the 1-based index of the configured selector to run. `--index` is required for the
four multi-selector roles (`arena runners`, `arena cross-judge pool`, `architect
runners`, `interrogate reviewers`) and rejected for a single-selector role. It is a
configured selector index, never a repeated worker's ordinal. Building the request
and preflighting it both reload and validate the role map.

**Model source.** `model_source` is derived from the flags you pass, and exactly one
source applies:

| Source | Flags | Rules |
|---|---|---|
| `configured` | none | the model comes from the role's selected config entry |
| `parent` | `--parent-model <concrete>` | only a currently configured inheritance alias may use it; the caller supplies the parent identity, because the helper cannot attest the live host's own model |
| `swarm-race` | `--race-model <concrete>` | only role `swarm workers`, and the model must be in the currently approved pool |

`--parent-model` is rejected when the role's selected entry is already concrete,
when the supplied value is itself an alias, or when it is absent: only a currently
configured inheritance alias may claim the parent's identity. `--race-model` is an
authorized override for role `swarm workers` whatever that role's configured
selector is, concrete or alias, because a race names its arms; it must be concrete
and already approved in the pool. Passing both flags at once is rejected. A race
never resolves an alias. Never let the integration CLI pick its default: a silently
different model falsifies the role map and any diversity claim based on it.

The workflow accepts no inputs. Its first fixed shell step reads
`PSTACK_DISPATCH_REQUEST`, revalidates the seven keys, and supplies trusted
`integration`, `model`, and `prompt` values directly to the prompt step. Its final
fixed shell step rereads the same environment value and validates that exact
report. No model selector or path is interpolated into a workflow shell command.

The workflow's prompt step timeout is the native Spec Kit prompt-step timeout, a
literal 1200 seconds in `.specify/extensions/pstack/workflows/dispatch.yml`.
Native Spec Kit 1.0.4 does not interpolate a step's timeout and offers no per-run
override, so no configuration value changes it, and it is not a process-tree
cancellation guarantee. The role map has no dispatch setting and nothing wraps the
workflow. A `dispatch` block left over from an older hand-edited map is unrelated
metadata: it is preserved byte-for-byte and read by nothing.

A run directory you create yourself works when it satisfies the same shape: one
direct child of the runs directory, a nonempty prompt, a fresh report, and no
symlinks. Allocation provenance adds no authorization; the path checks do.

Rules for both dispatch paths:

1. One leg owns one report file under its allocated run directory. Worker files
   live outside the extension, so an update cannot delete in-flight state.
2. The worker writes its complete result atomically to the report path. Printed
   output is not a substitute.
3. A report is one JSON object. These five keys are required:

   | Key | Meaning |
   |---|---|
   | `verdict` | `PASS`, `PASS+NOTES`, `PASS WITH NOTES`, `FAIL`, `ISSUES`, or `BLOCKED` |
   | `check` | non-empty command or surface exercised |
   | `evidence` | non-empty excerpt of observed output |
   | `files` | path strings for files touched; an empty list is valid for read-only work |
   | `reason` | always a string; non-empty for a failing verdict |

   `result` is the only optional key. When present, it is a non-empty string with
   the complete prose, research, or other result that does not fit the metadata.
   No other keys are accepted. The original five-key report remains valid.
4. Validate a native worker report with:

   ```
   python3 .specify/extensions/pstack/runtime/pstack-native.py report-check --report <path>
   ```

   The workflow uses `dispatch-report-check` instead, which gets the path from the
   authoritative request. Both exit non-zero for a missing file, malformed JSON,
   a failing verdict, or an invalid shape. A process exit or `completed` state is
   never a verdict.
5. Keep the routing record and raw report path. An excerpt without its report path
   is not evidence.
6. Every task declares its writes. Each task in `tasks.md`, parallel or serial,
   carries a `**Writes:**` line listing every file it will write, and an explicit
   empty list (`**Writes:** []`) is the correct entry for a task that writes no
   artifact. Disjointness is a parallel rule: two `[P]` tasks in the same phase
   must not name the same file, while a serial task may write a file a later serial
   task also rewrites. A worker's assigned report file is control metadata, not a
   claimed task artifact: it never appears in a `Writes` list, and writing it is
   never a violation of one.

## What a worker must load

A worker's prompt file names, in order: this contract, the agent contract at
`.specify/extensions/pstack/resources/agents/poteto-agent.md` (or the contract the
routed skill names), the mode resource
`.specify/extensions/pstack/resources/skills/poteto-mode/SKILL.md` when the mode is active, the routed skill
or playbook resource for the work, and the principle leaves it applies. Point at
paths, do not paste long bodies. A worker that never loaded them is not a pstack
worker and its verdict does not count.

## Capabilities

Check, do not assume:

```
python3 .specify/extensions/pstack/runtime/pstack-native.py capability-report
```

The helper checks local CLI paths and reads host mappings. It cannot inspect the
current session's tool inventory, authentication, or permissions. A host name is
not proof of a working browser, terminal, or history source.

Each capability reports `available`, `degraded`, or `unavailable`, with a reason:

- `cli` describes the integration executable on PATH, not native subagents.
  Inspect the live host tools first. Use native subagents when present; otherwise
  use the workflow when its CLI path is available. Only when neither exists,
  run inline and disclose that this is not independent verification.
- `transcripts` degraded requires checking a workspace-scoped host history tool
  or a supplied `PSTACK_TRANSCRIPTS_DIR`. Without an accessible source, report no
  history instead of reconstructing it from memory.
- `browser` or `terminal` degraded requires checking the live tool inventory or
  an existing local harness and proving the required interaction. Ask for a
  missing harness only after checking what is already available.
- `scheduler` unavailable means no durable scheduler is wired in by default.
  A supplied scheduler must be inspected and proven before claiming a durable
  wakeup; a supervised local process alone does not survive hosts or restarts.
- `external_automation` unavailable means no endpoint is wired in by default.
  Inspect user-supplied endpoints, credentials, and tools before proceeding.
  If they are missing, stop that step and name them. Never invent a service call.

## Mode

Session mode and project mode have different lifetimes:

- **Session mode.** `/speckit.pstack.poteto-mode <task>` applies Poteto rules to
  the invocation and its delegates. It persists in that session until a clear
  natural-language opt-out. The opt-out records session mode as inactive and
  suppresses later bootstrap and hook reloads in that session, even while a
  project block remains ready. It does not change project files.
- **Project mode.** `/speckit.pstack.poteto-mode on` writes one managed block to
  the mapped instruction file. Explicit `off` removes exactly that block and
  leaves every other byte alone. `status` reports project, registry, resource,
  and caller-supplied session state separately.

The bootstrap block first runs `python3 .specify/extensions/pstack/runtime/pstack-native.py mode status` and reads no pstack
resource unless `project_mode.ready` is exactly true. Readiness requires one
well-formed block, an enabled `pstack` registry entry, and the installed mode
resource. A missing helper, malformed output, disabled extension, or missing
resource makes the block inert.

Unknown integrations stay invocation-only because `mode on` refuses to guess an
instruction file. Run explicit `off` before removing the extension. A leftover
block after removal must stay inert.

The four manifest hooks are mandatory while the extension is enabled and each runs
the same readiness check. They are no-ops when project mode is off or the current
session opted out. They run through the Spec Kit phase hook executor. Installing
pstack does not make OMP intercept unrelated commands globally; OMP project-mode
activation comes from the managed instruction block.

## Calling another pstack skill

Two different names, and neither is a host-global plugin skill:

- **A packaged resource.** Bare names inside the translated resources (`how`,
  `why`, `unslop`, `no-comments`, `technical-writing`, `create-verification-skill`,
  `swarm`, `arena`, `architect`, `interrogate`, `reflect`, `recall`, `tdd`, and the
  `principle-*` leaves) mean
  `.specify/extensions/pstack/resources/skills/<name>/SKILL.md`. Read that file and
  follow it. Do not look for a host-installed skill of the same name; if the host
  has one, it is a different artifact and the packaged resource is authoritative
  for pstack work.
- **A registered command.** Extension commands are named `speckit.pstack.<name>`,
  and the host resolves that name to whatever invocation form it uses. A pstack
  command body names a sibling command by that id, and adds the Spec Kit token
  `__SPECKIT_COMMAND_<NAME>__` only when the name has no hyphen
  (`__SPECKIT_COMMAND_PSTACK_TASKS__` renders as the host's own form for
  `speckit.pstack.tasks`). The registrar substitutes the token's segments with the
  host's prefix and separator, so `__SPECKIT_COMMAND_PSTACK_POTETO_MODE__` would
  render as a name that does not exist; a hyphenated command is named by its id
  instead. No command body carries a hard-coded `/speckit....` invocation, because
  that is one host's form and breaks on the next.
- **A resource.** A translated resource
  under `.specify/extensions/pstack/resources/` is read at runtime, not registered,
  so a token in it would never be substituted. A resource names a sibling by its
  bare skill name (resolution above) or by its command id `speckit.pstack.<name>`,
  and a guide showing what a user types names the host's own form, because that is
  the reader's surface.

### TypeScript trigger

The TypeScript adapter preserves upstream `paths: ["**/*.ts", "**/*.tsx"]` and
`disable-model-invocation: true` metadata. A host may use that metadata for scoped
loading, but pstack does not claim every registrar implements path triggers.
Therefore the mode and every worker brief must explicitly load
`principle-type-system-discipline` first and then
`resources/skills/typescript-best-practices/SKILL.md` before reading or editing a
`.ts` or `.tsx` file.

## Project skills this extension generates

Some skills write a project skill (`create-verification-skill`,
`maintain-verification-skill`, `automate-me`). The location is host data, not a
constant:

```
python3 .specify/extensions/pstack/runtime/pstack-native.py paths
```

`skills_dirs` lists the directories this host actually discovers project skills
from, `skills_dir_evidence` names where that mapping came from, and
`discovery_check` names how to prove discovery. Use exactly one of them as the
canonical location for a generated project skill: the first entry, unless the user
names another. One skill is one file in one directory.

When `skills_dirs` is empty, this host discovers no project skills at all: write
the skill under `skills_dir_fallback` (`.specify/pstack/skills/`) and point the
instruction file or the task brief at that exact path, because nothing loads it
automatically. Do not keep a second editable copy of the same skill, and do not
symlink one location to the other; a duplicate is the version that silently goes
stale.

Then run the host's own listing in a fresh session and confirm the skill loaded.
Report it as active only after that; claiming discovery without the check would be
a lie.

## Writes and locks

- Every managed write is a compare-and-swap under a POSIX advisory lock. Each
  managed file has one persistent sidecar lock, `<name>.lock`, that pstack owns.
- The sidecars are permanent. pstack never unlinks one, because removing the inode
  while a writer holds or waits on the lock lets a second writer believe it is
  exclusive. A sidecar with no writer is idle, not stale; leave it in place.
- New files pstack writes are owner-private: locks are created `0600`, and a file
  pstack creates is private too. An existing managed file keeps its own mode across
  a rewrite. Nothing in pstack needs multi-user access, so nothing widens a file it
  writes to `0644`.

## Boundaries

- The runtime helper requires POSIX advisory locks through Python's `fcntl`
  module. Linux, macOS, and WSL satisfy this prerequisite. Native Windows does
  not.
- No provider runtime ships here. Dispatch uses the host or the Spec Kit workflow
  engine. The workflow's prompt-step timeout is the native Spec Kit timeout, a
  literal in `.specify/extensions/pstack/workflows/dispatch.yml`; it is not
  configurable and it is not a
  process-tree cancellation guarantee.
- No host-specific device is required. OMP device descriptors may inform agent
  selection, but no pstack command depends on one.
- No cloud survival, cross-machine state, dashboard, or OS-level automation
  channel is claimed. A resource names the local equivalent and its limit.
