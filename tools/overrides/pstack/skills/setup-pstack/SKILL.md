---
name: setup-pstack
description: Configure which models pstack uses per role. Detects the model selectors your host actually accepts and writes the project role map that every pstack dispatch reads. Use for /speckit.pstack.setup-pstack, "configure pstack models", or changing pstack's model choices.
---

# Setup pstack

Write the project role map at `.specify/extensions/pstack/pstack-models-config.yml`.
It holds one entry per pstack role and is what the runtime helper resolves before
every dispatch. Nothing is written to a machine-global file, and nothing outside
this project changes.

The helper owns every write, so the map stays valid JSON, atomically replaced, and
identical on a re-run:

```bash
python3 .specify/extensions/pstack/runtime/pstack-native.py <command>
```

## Steps

### 1. Detect the selectors this host accepts

Enumerate the model selectors the host will actually accept for a delegated
worker. That is the dependable source: the host's own model list, the agent
descriptors the host exposes, or the selectors already recorded in this project's
`pstack-models-config.yml` when it exists. If you cannot detect any, ask the user
to paste the selectors they have. Never write a selector you have not confirmed is
available. The aliases `inherit-parent` and `auto` mean the worker runs on the
current model; they are supported aliases, but still require approval in `pool`.

### 2. Load current state

```bash
python3 .specify/extensions/pstack/runtime/pstack-native.py config-show
```

Read two things from that response: the map itself, and its top-level `pristine`
flag, which is the same predicate migration uses. `pristine` true means the map is
absent or still the untouched scaffold; false means a role or the pool has already
been customized.

Then inspect the legacy lane file `.specify/extensions/pstack/pstack-config.yml`
whenever it exists, whether or not the role map is already present. When its
`roles.verify` or `roles.swarm` holds a non-empty value, that value is the user's
earlier choice and step 3 surfaces it before anything is written. A scaffold in the
role map is not a reason to skip that inspection.

### 3. Legacy lane selectors

The legacy file is migration input only. Nothing reads it at runtime, and a header
comment an older install left in your copy is historical, not an instruction.

Read the legacy YAML yourself. It is ordinary YAML with `roles.verify`,
`roles.swarm`, and `parallel.max_workers`. Do not hand-write the new map: pass the
values to the helper, which validates them and prints the map it would write.

```bash
python3 .specify/extensions/pstack/runtime/pstack-native.py config-migrate \
  --verify "<legacy roles.verify>" --swarm "<legacy roles.swarm>" \
  --max-workers <legacy parallel.max_workers>
```

The migration maps `roles.verify` to `interrogate reviewers` and `roles.swarm` to
`swarm workers`. It adds migrated selectors to `pool` and preserves unrelated
metadata and the worker cap already in a pristine role map. More than one legacy
swarm selector is ambiguous: the helper rejects it instead of silently truncating
the list. Report those selectors and require one explicit choice before the write.

Which branch you are on decides the write:

- **`pristine` true.** Show the migration proposal with the legacy values marked,
  preserve unrelated metadata, then re-run with `--write` to use the confirmed
  atomic write path. Re-running the same migration with the values it already
  applied is a byte-preserving no-op.
- **`pristine` false.** The map is customized. Show a delta between the legacy
  values and the current map for explicit reconciliation, and never run migration
  over it: overwriting a customized map would discard choices the user made here.
- **No legacy selectors.** Run `config-init` instead when the map is absent.

```bash
python3 .specify/extensions/pstack/runtime/pstack-native.py config-init
```

### 4. Map and confirm

Confirm the approved `pool` first, using the existing pool as the starting point.
Availability is not approval; include aliases only when approved too.
Then show every role with its current selector, marking any concrete selector
not in the detected set as needing a choice. Ask whether to accept as-is or
change specific roles, offering only selectors in the confirmed pool. Prefer the
host's structured question prompt over free text.

The 17 role labels, in the order the helper writes them:

```
feature, refactoring
bug-fix
perf-issue
hillclimb
judgment and prose
hardest tasks
how explorer
how explainer
why investigators
why synthesizer
reflect tooling
reflect judgment, divergent, synthesizer
arena runners
arena cross-judge pool
swarm workers
architect runners
interrogate reviewers
```

Roles come in three kinds. The host contract defines them, and `role-plan` reports a role's `kind`; `config-show` lists the selectors without it. `panel`
roles (`arena runners`, `architect runners`, `interrogate reviewers`) hold ordered
lists, one worker per entry, duplicates preserved, and one team member per index.
`arena cross-judge pool` is `choose-one`: the arena selects exactly one configured
judge, preferring a model family different from the parent's, and never allocates
the whole list. Every other role is `single`, so it resolves one selector; `swarm
workers` supplies that selector to every swarm task unless a race names a model for
each arm.

### 5. Validate

Every concrete selector written must be in the detected set, and the helper
refuses any selector outside `pool`, including `inherit-parent` and `auto`. If a
chosen selector is not available, stop and ask again rather than substituting one.

### 6. Write the role map

Read `config-show` again after any initialization or migration. Build the complete
document from its `data`, replacing `pool` with the confirmed pool and `roles`
with all 17 confirmed lists. Preserve unrelated settings and metadata.

Send that document on stdin to one atomic save, using the hash from the same
`config-show` response:

```bash
python3 .specify/extensions/pstack/runtime/pstack-native.py config-save --expect-hash <sha256>
```

If the compare fails, reload and reconcile the intervening changes before
confirming and saving again. Do not publish a partially updated role map. A role
map the helper creates is owner-private, and an existing one keeps its mode; the
compare-and-swap runs under the persistent `<config>.lock` sidecar, which pstack
never deletes.

Shape it writes, shown here as a small fragment so the semantics are visible:

```json
{
  "schema_version": 1,
  "pool": ["inherit-parent", "<selector>", "<another selector>"],
  "roles": {
    "bug-fix": ["<selector>"],
    "arena runners": ["<selector>", "<another selector>"],
    "swarm workers": ["inherit-parent"]
  },
  "parallel": { "max_workers": 3 }
}
```

There is no dispatch timeout to set. The workflow's prompt step uses native Spec
Kit's own timeout, a literal in
`.specify/extensions/pstack/workflows/dispatch.yml`, and Native Spec Kit 1.0.4
offers no per-run override. A `dispatch` block an older hand-edited map still
carries is preserved as unrelated metadata and read by nothing; setup does not
normalize it away.

Re-running setup rewrites the same file, so the project stays idempotent. Reinstall
and upgrade keep the file: it is a preserved top-level config, not packaged content.

### 7. Confirm

Tell the user the project role map was written, where it lives, and that it applies
to this project only. `disable-model-invocation` and mode settings are unrelated:
this command only changes model routing.

### 8. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*`
skill in a directory `.specify/extensions/pstack/runtime/pstack-native.py paths` lists under `skills_dirs`, or an
existing harness). If not, offer once: "want a project-local verification skill, so
agents can drive the app the way a user does and prove changes work? I can generate
one with `__SPECKIT_COMMAND_PSTACK_CREATE_VERIFICATION_SKILL__`." On yes, run it, and
let it write one skill into one discovered directory. On no, move on without
pushing.
