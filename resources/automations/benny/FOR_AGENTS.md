# benny automation intent

## what i want to automate

i want two scheduled agents that work together in one slack issue channel on a
scheduler or bot runner i supply.

### job 1: triage issue reports

- trigger: when someone posts a new top-level report in my configured source slack
  channel, start on that report and keep its original thread coordinates.
- behavior: read the thread and attachments, classify the report as a bug or
  performance issue, feature request, question or feedback, or reroute, and trace
  the likely owning layer before routing.
- tracker: search my configured tracker for duplicates, update a confident duplicate,
  and create a ticket only for a clear net-new bug.
- tools: use slack thread read and reply access, my configured tracker integration,
  and my optional routing map.
- outcome: post exactly one reply in the source thread with a short verdict and
  `[benny:bug]`, `[benny:performance]`, or `[benny:other]`. a bug or performance
  marker may include the tracker url.
- boundary: never post a root message in the source channel.

### job 2: reproduce and fix confirmed bugs

- trigger: start from the same new top-level report, or another supported trigger
  chosen during setup, then wait for the trusted triage marker in the original thread.
- gates: stop when someone clearly owns the fix. if an existing pull request or merged
  commit may fix the report, verify it instead of making a competing change.
- behavior: use my configured control adapter and feature map, reproduce the exact
  symptom twice through the real ui, and capture screenshots, video, and a read-only
  state cross-check.
- fix: verify existing pull requests without authoring over them. after a confirmed
  repro, attempt at most one bounded root-cause fix, use tdd when the test is cheap,
  smoke the blast radius, and open a draft pull request only when before-and-after
  proof passes.
- tools: use slack thread read and reply access, repository and history access, draft
  pull request creation, my configured tracker, and my control adapter.
- outcome: return evidence and a verified result in the source or optional operations
  threads, plus an optional draft pull request. keep updates concise.
- boundary: never post a root message in the source channel.

### shared rules

- keep the source channel and root thread coordinates immutable for the whole run.
- treat utility and debug bots as evidence, not delegation or fix ownership.
- subagents may help, but they cannot post to slack or receive slack credentials.
- commit this entire pack at `.specify/pstack/automations/benny/` in the target
  repository. its `SKILL.md` files are direct job instructions, not registered
  extension commands.
- install pstack as a Spec Kit extension in the target repository for shared
  dependencies such as `how`, `why`, `tdd`, `unslop`, and the required principles.
- each live prompt reads its committed operational file directly. do not use extension
  cache paths, copied excerpts, or command discovery for the dormant pack.
- keep user-owned configuration, feature maps, routing maps, and secrets outside
  `.specify/pstack/automations/benny/` so pack refreshes cannot overwrite them.
- fail closed when channel coordinates, tracker access, the control adapter, the
  feature map, or the supplied scheduler is missing or uncertain.
- open draft pull requests only. do not merge or deploy.

### my configuration

- source slack channel: `<channel>`
- optional operations channel: `<channel or none>`
- repository and default branch: `<repo>`, `<branch>`
- tracker: `<type, team, project, labels, intake status>`
- routing map: `<path or none>`
- triage identity: `<slack identity>`
- control skill: `<configured skill or adapter>`
- feature map: `<committed same-repo path outside the copied pack, or behavior to paraphrase>`
- models: `<concrete selectors for triage, reproduce, code, media review>`
- status emoji strings: `<seen, reproducing, reproduced, blocked, fixing, failed, pull request opened>`
- budgets: `<polling, verdict wait, follow-up, repro, rejection, fix>`
- optional bot token capability: `<none, file download, or editable operations status>`
- scheduler or bot runner: `<configured tool and job operations>`

start from [`configuration.example.yaml`](./templates/configuration.example.yaml) and
[`feature-map.example.md`](./skills/reproduce-and-fix-issues/references/feature-map.example.md).
copy and fill them outside this pack, for example under `.specify/pstack/benny/`.
keep secret values in the supplied runner's server-side secret store or environment.

## for the agent

the human enters setup by pointing the host agent at this file. do not look for or
invoke a discovered benny command.

1. ask which repository will run the jobs.
2. treat the directory containing this `FOR_AGENTS.md` as the source pack.
3. merge the entire source pack into
   `<target-repository>/.specify/pstack/automations/benny/`.
4. preserve every destination-only file. never delete unrelated files or overwrite
   user-owned configuration, feature maps, or routing maps.
5. when a source-managed destination file differs, review the diff and merge without
   discarding local edits. stop before replacing a file with ambiguous ownership.
6. verify the copied `FOR_AGENTS.md` and `skills/setup-benny/SKILL.md` exist in the
   target repository.
7. read and follow
   `.specify/pstack/automations/benny/skills/setup-benny/SKILL.md` in the target.

install pstack in the target with `specify extension add pstack` when
`specify extension list` does not show it. do not create an editor settings entry.
verify the shared resources from a fresh agent rooted in the target repository. do
not count files loaded from this session or a user-scoped installation.

tell me that the pack and every referenced secret-free configuration file must be
committed before either job is created. do not create or update a job until i
explicitly ask.

for first-time creation, use the documented create operation of the scheduler or bot
runner i supplied. create triage first, re-read its stored fields, then create repro.
keep both disabled. complete draft review, approval, and readiness for one job before
starting the next.

paraphrase this intent and the finished configuration into each job. the triage
prompt reads
`.specify/pstack/automations/benny/skills/triage-issue-reports/SKILL.md`. the repro
prompt reads
`.specify/pstack/automations/benny/skills/reproduce-and-fix-issues/SKILL.md`. use
those paths only after proving they are committed in the checkout the runner uses.

for existing jobs, query the supplied runner by stable name and repository, show the
field diff, and update the one existing record in place after approval. do not create
duplicates. use the setup file's run-once thread-safety test before enabling normal
traffic. if the supplied runner cannot inspect, create, update, run once, enable, and
disable jobs, report that exact prerequisite instead of inventing a backend.