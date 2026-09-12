---
name: setup-benny
description: Configure Benny and prepare its triage and repro jobs. Use when installing Benny or changing its Slack, tracker, repository, routing, control, model, budget, or scheduler settings.
disable-model-invocation: true
---

# Set up Benny

Benny is a dormant automation pack inside pstack. The extension manifest does not
register these three `SKILL.md` files as commands. A person or a scheduled job reads
them from the target repository.

The human enters setup by pointing the host agent at `FOR_AGENTS.md`. The bootstrap
copies the whole pack into the target repository, then reads this file at
`.specify/pstack/automations/benny/skills/setup-benny/SKILL.md`.

Benny needs external configuration, Slack, issue-tracker, repository, control, and
scheduler capabilities. This extension does not provide those services. Never put a
secret value in extension files, prompts, or committed configuration. Do not create,
update, or enable a scheduled job until the user explicitly asks.

## 1. Copy the pack and install pstack

Do this before asking for Benny configuration.

Ask which repository will run the jobs. The source pack is the directory containing
`FOR_AGENTS.md`. The destination is
`<target-repository>/.specify/pstack/automations/benny/`.

Merge the entire source pack into the destination.

1. Create the destination when it is absent.
2. Copy every source file to the same relative path.
3. Preserve destination-only files. Never delete unrelated files during install or
   refresh.
4. Keep user-owned configuration, feature maps, and routing maps outside the
   destination. Never overwrite them.
5. When a source-managed file differs, inspect the diff and merge without discarding
   local edits. If ownership is ambiguous, stop before replacing it.
6. Verify the destination contains `FOR_AGENTS.md`, this setup file, both operational
   files, their references, and the templates.

If this file is already in the target destination, treat the copy as complete and
run the same verification.

Install pstack in the target as a Spec Kit extension. Use `specify extension list`
to detect it and `specify extension add pstack` when it is absent. Do not create or
edit an editor settings file. The extension manifest registers the shared commands.

Start a fresh agent rooted in the target repository. Verify that these packaged
resources resolve from the target's installed extension, not from this session or a
user-scoped copy.

- `how`
- `why`
- `tdd`
- `unslop`
- `principle-separate-before-serializing-shared-state`
- `principle-minimize-reader-load`
- `principle-guard-the-context-window`
- `principle-sequence-verifiable-units`
- `principle-fix-root-causes`
- `principle-prove-it-works`

If the extension is absent or any dependency does not resolve, stop setup and report
the failed prerequisite. Do not register the Benny directory as commands. It stays
dormant by design.

Tell the user that `.specify/pstack/automations/benny/` and every referenced
secret-free configuration file must be committed before either job is created.
Do not commit them unless the user asks.

A live job reads committed operational files by stable repository-relative paths.
It never embeds an extension cache path or a copy of an operational file.

## 2. Adapt the configuration

Open these copied examples.

- `../../templates/configuration.example.yaml`
- `../reproduce-and-fix-issues/references/feature-map.example.md`

Create user-owned copies outside `.specify/pstack/automations/benny/`. Examples are:

- Project config at `.specify/pstack/benny/configuration.yaml`
- Project feature map at `.specify/pstack/benny/feature-map.md`
- Project routing map at `.specify/pstack/benny/routing.md`
- User config at `~/.config/benny/configuration.yaml`
- User feature map at `~/.config/benny/feature-map.md`

Fill one feature-map section for every user-facing feature the repro job may drive.
Keep it at the user point of view. Do not freeze implementation details or current
code paths in the map.

Do not edit the examples inside the pack. Refreshes may update those files after
conflict review, but must never touch user-owned copies.

Prefer committed, secret-free files when a fresh scheduler checkout must read them.
Otherwise paraphrase required values into the job prompt. Reference a repository
file only after proving it is committed in the repository and revision the job runs.

## 3. Fill the required choices

Ask for or confirm:

- Source Slack channel ID
- Optional operations or status channel ID
- Repository URL and default branch
- Triage identity or Slack user ID
- Issue tracker type, team, project, labels, and intake status
- Tracker adapter or MCP actions
- Optional routing map path
- Required control skill name
- Required user-facing feature-map path
- Status emoji strings
- Pull request URL format
- Polling and effort budgets
- Concrete model selector for triage, repro, code work, and media review

Resolve model selectors through the project role map and prove the host accepts them.
Do not guess a selector and do not carry over a private default. The source channel,
triage identity, repository, tracker adapter, control skill, and feature map must be
explicit. Fail setup if any required value stays ambiguous.

Apply the packaged `unslop` skill to the final job names, descriptions, and prompt
shims before saving them.

## 4. Check integration and scheduler capabilities

The triage job needs:

- Read access to the configured source Slack channel and its threads
- Thread-reply access in that channel
- Attachment metadata and file download access when reports include media
- Search, read, create, and update access through the configured issue-tracker adapter

The repro job needs:

- Read access to the source thread
- Thread-reply access in the source channel
- Optional post and edit access in the configured operations channel
- Repository read and history access
- A pull request action that can open a draft pull request
- The configured control-adapter skill

Use only the Slack, tracker, forge, and control tools the user configured. The
optional `BENNY_SLACK_BOT_TOKEN` may fill one narrow gap such as editing one status
message or downloading an attachment. Keep it in the scheduler's server-side secret
store or environment. Never expose it to a worker or write it to YAML.

The scheduler or bot runner must support all of these capabilities:

- Trigger on a new top-level message in one named Slack channel
- Pass immutable channel, thread, message, and sender coordinates to the job
- Check out the configured repository and committed revision
- Run the committed prompt on one concrete supported model
- Expose only the configured Slack, tracker, forge, and control tools
- Keep secret values server-side
- Inspect, create, update, run once, enable, and disable a named job

Discover those operations from the configured scheduler or bot tool. Do not invent
an endpoint, CLI, deep link, or editor. If no supplied runner meets the contract,
finish the configuration and prompt artifacts but report that scheduling is blocked.
A manual run is not a scheduled job.

## 5. Prepare the routing map

If the user wants reroutes or owner pings:

1. Copy `../triage-issue-reports/references/routing.example.md` outside
   `.specify/pstack/automations/benny/`.
2. Replace every placeholder with public or organization-local values.
3. Keep owner pings off by default.
4. Allow a ping only for a configured feature owner or a confirmed likely regression
   author.

Without a routing map, triage may classify a report but must not guess a destination
or owner.

## 6. Verify the control adapter

Read `../reproduce-and-fix-issues/references/control-adapter.md` and the completed
feature map.

Confirm the named control skill can:

- Bring up the target app
- Navigate every mapped feature through the real UI
- Exercise mapped states through declared adapter actions
- Inspect state without forcing the result
- Capture screenshots
- Start and stop a recording
- Clean up its processes and temporary data

If any capability is missing, leave the repro job disabled. It must fail closed
rather than claim a reproduction it did not perform.

## 7. Create or update the scheduled jobs

Read `../../FOR_AGENTS.md` as the primary user-intent source. Read the matching
prompt template as secondary source material. Fill the configuration first.

Before any handoff, use the configured tools to discover the actual Slack channel,
repository, tracker, control adapter, and scheduler operations. Prove the pack and
every referenced configuration file are committed in the repository and revision
the scheduler will check out.

Build one complete job request at a time. Show a draft table with the job name,
trigger, source channel, repository and branch, concrete model, tools, committed
prompt path, budget, and enabled state. Obtain the user's explicit approval and
readiness before calling the scheduler's create or update operation.

### First-time creation

Create `benny-triage` first and keep it disabled.

- Read and follow
  `.specify/pstack/automations/benny/skills/triage-issue-reports/SKILL.md` on every
  run.
- Trigger on each new top-level report in the configured source Slack channel.
- Read the triggering thread and reply only inside it.
- Use the configured issue-tracker integration.
- Classify, inspect evidence, trace cause, deduplicate, and create only clear new
  bugs.
- End with one thread-only verdict carrying the configured `[benny:bug]`,
  `[benny:performance]`, or `[benny:other]` marker and optional tracker URL.
- Never post a source-channel root message.

After the scheduler returns the stored `benny-triage` job, re-read its actual fields
and compare them with the approved table. Then create `benny-reproduce`, disabled.

- Read and follow
  `.specify/pstack/automations/benny/skills/reproduce-and-fix-issues/SKILL.md` on
  every run.
- Trigger on the same new top-level reports in the configured source Slack channel.
- Use the configured repository and default branch.
- Read the source thread and reply only inside it.
- Include pull request creation and the configured tracker, control-adapter, and
  feature-map requirements.
- Wait for a trusted triage marker before acting.
- Reproduce the exact symptom twice through the mapped real UI and capture evidence.
- Verify an existing fix without authoring over it.
- Attempt an optional bounded fix only after confirmed reproduction. Open a draft
  pull request only when proof and checks pass.
- Never post a source-channel root message.

Re-read the stored repro job and compare it with the approved table. Do not enable
normal traffic yet.

### Existing jobs

Query the supplied scheduler by the stable job name and repository. Require exactly
one match for `benny-triage` and one for `benny-reproduce`. Zero matches is creation,
not update. More than one is a duplicate-state blocker.

Compare each stored job with the completed configuration and show a field-level
diff. After explicit approval, update the existing job in place through the
scheduler's documented update operation. Do not create a replacement. Leave both
jobs disabled until the test below passes.

## 8. Test thread safety

Use the scheduler's run-once or canary operation with a test channel and a harmless
test report. Confirm both stored prompts point at their exact committed operational
files before the run.

Verify:

1. Triage stores the root `thread_ts` and posts exactly one verdict as a reply.
2. The verdict contains one configured marker.
3. Repro accepts the marker only from the configured triage identity.
4. Repro keeps the same immutable source coordinates.
5. No source-channel root message appears.
6. A delegated worker cannot use any Slack write action.
7. Missing coordinates, a deleted parent, or a failed preflight produces no post and
   no tracker issue.

Enable normal traffic through the scheduler's documented enable operation only after
all seven checks pass. Re-read both stored jobs and report their identifiers,
revision, trigger, concrete model, and enabled state.