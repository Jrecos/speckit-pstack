"""Translation tables for tools/import_upstream.py.

One data file so every edit to a copied upstream file is reviewable in one place:
the exact source text that changes, what it becomes, and why. The importer fails
loudly when a `find` string is absent or appears a different number of times than
declared, so upstream drift cannot pass silently.
"""

# Every reason string is the audit trail the source manifest records.
GLOBAL_REWRITES: list[tuple[str, str, str]] = [
    (
        r"~/\.cursor/rules/pstack-models\.mdc",
        ".specify/extensions/pstack/pstack-models-config.yml",
        "role map is project-local, not a machine-global Cursor rule file",
    ),
    (
        r"\.cursor/rules/pstack-models\.mdc",
        ".specify/extensions/pstack/pstack-models-config.yml",
        "role map is project-local, not a machine-global Cursor rule file",
    ),
    (
        r"~/\.cursor/skills/",
        ".specify/pstack/skills/",
        "project skills live in a project-owned directory, not the user's Cursor home",
    ),
    (
        r"\.cursor/skills/",
        ".specify/pstack/skills/",
        "project skills live in a project-owned directory, not the Cursor workspace layout",
    ),
    (
        r"\.cursor/automations/benny/",
        ".specify/pstack/automations/benny/",
        "benny pack installs into a project-owned path the extension can name",
    ),
    (
        r"\.cursor/benny/",
        ".specify/pstack/benny/",
        "benny user configuration is project-owned, outside the copied pack",
    ),
    (
        r"~/\.cursor/projects/\*/",
        "this workspace's transcript directory (`PSTACK_TRANSCRIPTS_DIR`)",
        "session history is read through an explicit workspace-scoped path, never another project's store",
    ),
    (
        r"\.cursor/worktrees/myrepo/x",
        ".worktrees/myrepo/x",
        "example worktree path is project-relative",
    ),
    (
        r"~/\.cursor/plugins/",
        "an installed skill root ",
        "no Cursor plugin store exists on a native Spec Kit install",
    ),
    (
        r"`AskQuestion`",
        "the host's question prompt",
        "the question tool is a host facility with a host-specific name",
    ),
    (
        r"(?<!`)\bAskQuestion\b",
        "the host's question prompt",
        "the question tool is a host facility with a host-specific name",
    ),
    (
        r"`subagent_type`: `generalPurpose`",
        "subagent: the host's general-purpose subagent",
        "subagent kinds are host-specific; the contract resolves them",
    ),
    (
        r"subagent_type: generalPurpose",
        "subagent: the host's general-purpose subagent",
        "subagent kinds are host-specific; the contract resolves them",
    ),
    (
        r"`Task` tool|the Task tool|Task tool",
        "the host subagent tool",
        "delegation goes through the host's own subagent facility",
    ),
    (
        r"`Task` subagent",
        "subagent",
        "delegation goes through the host's own subagent facility",
    ),
    (
        r"`Task` calls|`Task` call",
        "subagent dispatches",
        "delegation goes through the host's own subagent facility",
    ),
    (
        r"`Task` response body",
        "subagent report",
        "delegation goes through the host's own subagent facility",
    ),
    (
        r"`Task` prompts",
        "subagent prompts",
        "delegation goes through the host's own subagent facility",
    ),
    (
        r"spawn one Task subagent",
        "spawn one subagent",
        "delegation goes through the host's own subagent facility",
    ),
    (
        r"`run_in_background: true`",
        "dispatched in the background",
        "background dispatch is the host's own default, not a Task field",
    ),
    (
        r"Cursor's built-in `create-skill` skill",
        "the packaged create-skill guide (`.specify/extensions/pstack/resources/dependencies/create-skill.md`)",
        "the authoring guide ships with this extension instead of a Cursor built-in",
    ),
    (
        r"Cursor's built-in `create-skill` flow",
        "the packaged create-skill guide's draft/test/iterate flow",
        "the authoring guide ships with this extension instead of a Cursor built-in",
    ),
    (
        r"Cursor's built-in `create-skill`",
        "the packaged create-skill guide",
        "the authoring guide ships with this extension instead of a Cursor built-in",
    ),
    (
        r"`create-skill` \(Cursor's built-in for authoring SKILL\.md files\)",
        "the packaged create-skill guide (`.specify/extensions/pstack/resources/dependencies/create-skill.md`) for authoring SKILL.md files",
        "the authoring guide ships with this extension instead of a Cursor built-in",
    ),
    (
        r"Cursor's built-in babysit skill",
        "any host-provided skill whose description matches the same words",
        "no Cursor built-in is assumed to exist on the host",
    ),
    (
        r"`cursor-team-kit` plugin \(`/deslop`\)",
        "packaged deslop reference (`.specify/extensions/pstack/resources/dependencies/deslop.md`)",
        "the dependency ships inside this extension instead of a separate Cursor plugin",
    ),
    (
        r"`control-ui` or `control-cli` from `cursor-team-kit`",
        "the packaged `control-ui` or `control-cli` reference (`.specify/extensions/pstack/resources/dependencies/`)",
        "the dependency ships inside this extension instead of a separate Cursor plugin",
    ),
    (
        r"from `cursor-team-kit`",
        "from the packaged dependency references (`.specify/extensions/pstack/resources/dependencies/`)",
        "the dependency ships inside this extension instead of a separate Cursor plugin",
    ),
    (
        r"`cursor-team-kit` publishes",
        "the packaged dependency references publish",
        "the dependency ships inside this extension instead of a separate Cursor plugin",
    ),
    (
        r"`cursor-team-kit` too",
        "the packaged dependency references too",
        "the dependency ships inside this extension instead of a separate Cursor plugin",
    ),
    (
        r"the `cursor-team-kit` plugin",
        "the packaged dependency references",
        "the dependency ships inside this extension instead of a separate Cursor plugin",
    ),
    (
        r"`pstack-native\.py ([^`\n]+)`",
        r"`.specify/extensions/pstack/runtime/pstack-native.py \1`",
        "the runtime helper is invoked from its exact installed extension path",
    ),
]

GUIDE_COMMAND_NAMES = frozenset(
    {
        "architect",
        "arena",
        "automate-me",
        "blast-radius",
        "bro",
        "create-verification-skill",
        "figure-it-out",
        "how",
        "interrogate",
        "maintain-verification-skill",
        "make-bot-ui",
        "no-comments",
        "poteto-mode",
        "principle-attack-the-premise",
        "principle-boundary-discipline",
        "principle-build-the-lever",
        "principle-encode-lessons-in-structure",
        "principle-exhaust-the-design-space",
        "principle-experience-first",
        "principle-fix-root-causes",
        "principle-foundational-thinking",
        "principle-guard-the-context-window",
        "principle-laziness-protocol",
        "principle-make-operations-idempotent",
        "principle-migrate-callers-then-delete-legacy-apis",
        "principle-minimize-reader-load",
        "principle-model-the-domain",
        "principle-never-block-on-the-human",
        "principle-outcome-oriented-execution",
        "principle-prove-it-works",
        "principle-redesign-from-first-principles",
        "principle-separate-before-serializing-shared-state",
        "principle-sequence-verifiable-units",
        "principle-subtract-before-you-add",
        "principle-test-behavior-not-implementation",
        "principle-type-system-discipline",
        "recall",
        "reflect",
        "setup-pstack",
        "show-me-your-work",
        "swarm",
        "tdd",
        "teach",
        "technical-writing",
        "typescript-best-practices",
        "unslop",
        "why",
    }
)

# Per-file edits. `count` is how many times `find` must appear; the importer
# refuses to guess. Every edit carries the reason it exists.
FILE_EDITS: dict[str, list[dict]] = {
    "pstack/skills/how/SKILL.md": [
        {
            "find": "- `subagent_type`: `generalPurpose`\n- `model`: your configured how-explorer model (default `grok-4.6-fast-xhigh`)\n- `readonly`: `true`",
            "replace": "- subagent: the host's general-purpose subagent\n- `model`: role `how explorer` from the project role map (`pstack-native.py role-plan --role \"how explorer\"`); omit the model when the leg inherits the current one\n- `readonly`: `true` (read-only where the host supports it)",
            "reason": "explorer model comes from the project role map, not a vendor default",
        },
        {
            "find": "- `subagent_type`: `generalPurpose`\n- `model`: your configured how-explainer model (default `claude-fable-5-1-thinking-max`)\n- `readonly`: `true`",
            "replace": "- subagent: the host's general-purpose subagent\n- `model`: role `how explainer` from the project role map (`pstack-native.py role-plan --role \"how explainer\"`); omit the model when the leg inherits the current one\n- `readonly`: `true` (read-only where the host supports it)",
            "reason": "explainer model comes from the project role map, not a vendor default",
            "count": 2,
        },
        {
            "find": "Spawn one Task subagent that explores and explains in one pass:",
            "replace": "Spawn one subagent that explores and explains in one pass:",
            "reason": "delegation uses the host subagent facility",
        },
        {
            "find": "spawn one Task subagent to synthesize their findings into one explanation:",
            "replace": "spawn one subagent to synthesize their findings into one explanation:",
            "reason": "delegation uses the host subagent facility",
        },
    ],
    "pstack/skills/why/SKILL.md": [
        {
            "find": "make your best guess from conversation context (open files, recent edits, cursor location, what was just discussed)",
            "replace": "make your best guess from conversation context (open files, recent edits, what was just discussed)",
            "reason": "editor cursor location is a Cursor-specific signal",
        },
        {
            "find": "Before spawning investigators, list the available MCPs from the Cursor environment. Use the available-tools map when present. Otherwise inspect the `mcps/` directory Cursor exposes for enabled MCP servers.",
            "replace": "Before spawning investigators, list the MCP servers this session actually has. Use the host's available-tools listing when present. Otherwise read the host's MCP configuration. A source you cannot reach is reported as unavailable, not assumed.",
            "reason": "MCP inventory is read from the live host, not a Cursor directory",
        },
        {
            "find": "- `subagent_type`: `generalPurpose`\n- `model`: your configured why-investigators model (default `grok-4.6-fast-xhigh`)\n- `readonly`: `false` (agent mode). **Do not use readonly/Ask mode.** It strips MCP access, which disables MCP-backed investigators entirely. Investigators still shouldn't write anything.",
            "replace": "- subagent: the host's general-purpose subagent\n- `model`: role `why investigators` from the project role map (`pstack-native.py role-plan --role \"why investigators\"`); omit the model when the leg inherits the current one\n- agent mode, not read-only: read-only mode strips MCP access on hosts that make MCP conditional, which disables MCP-backed investigators entirely. Investigators still should not write anything.",
            "reason": "investigator model comes from the project role map, not a vendor default",
        },
        {
            "find": "- `subagent_type`: `generalPurpose`\n- `model`: your configured why-synthesizer model (default `claude-fable-5-1-thinking-max`)\n- `readonly`: `false` (agent mode). The synthesizer's quality check spot-verifies citations, which can require MCP access. Readonly/Ask mode strips MCPs and defeats that.",
            "replace": "- subagent: the host's general-purpose subagent\n- `model`: role `why synthesizer` from the project role map (`pstack-native.py role-plan --role \"why synthesizer\"`); omit the model when the leg inherits the current one\n- agent mode, not read-only: the synthesizer's quality check spot-verifies citations, which can require MCP access, and read-only mode strips MCPs on hosts that make MCP conditional.",
            "reason": "synthesizer model comes from the project role map, not a vendor default",
        },
    ],
    "pstack/skills/swarm/SKILL.md": [
        {
            "find": "Fan out N parallel cloud workers. They may cover separate slices, race the same brief, or mix both.",
            "replace": "Fan out N parallel local workers. They may cover separate slices, race the same brief, or mix both.",
            "reason": "there is no cloud worker environment here, so the opening claims none",
        },
        {
            "find": "When a worker must start from a non-default pushed branch, pass `cloud_base_branch`.",
            "replace": "When a worker must start from a non-default branch, give it an isolated local worktree checked out at that branch. There is no cloud base-branch parameter: the worktree and the checkout are the native equivalent.",
            "reason": "cloud_base_branch is a Cursor cloud field with no native counterpart",
        },
        {
            "find": "4. Pick the worker model from `swarm workers` in `~/.cursor/rules/pstack-models.mdc` when present. Otherwise use `grok-4.6-fast-xhigh`. For a model race, name each arm's model up front.",
            "replace": "4. Resolve the worker model from role `swarm workers` in the project role map (`pstack-native.py role-plan --role \"swarm workers\"`). An empty role is a setup error, not a reason to pick a model yourself. For a model race, name each arm's model up front, and only `swarm workers` may carry an explicit race model: it must be concrete and already in the map's approved `pool`, and it is passed as `--race-model`, never as a free-form selector.",
            "reason": "worker model comes from the project role map, not a vendor default",
        },
        {
            "find": 'Spawn all N workers in one message with `subagent_type: generalPurpose`, `environment: "cloud"`, `run_in_background: true`, and the configured model. Use `environment: "local"` only when the worker needs access to something on the user\'s computer.',
            "replace": "Spawn all N workers in one batch with the host's general-purpose subagent, dispatched in the background, on the resolved model. There is no cloud environment here: the only worker environments are this machine and an isolated local worktree, and the work stops when the machine or the process stops. Say which one each worker used.",
            "reason": "Cursor cloud workers become native local workers, with the lost survival stated",
        },
        {
            "find": "3. Set N from the user or derive it from the shape. N is total workers, not the cloud concurrency limit.",
            "replace": "3. Set N from the user or derive it from the shape. N is total workers, not the concurrency limit; keep the in-flight count within the role map's `parallel.max_workers`.",
            "reason": "concurrency cap is the project role map's value, not a cloud limit",
        },
    ],
    "pstack/skills/arena/SKILL.md": [
        {
            "find": "Spawn all N subagents in one message with `run_in_background: true`, each with the task,",
            "replace": "Spawn all N subagents in one batch, dispatched in the background, each with the task,",
            "reason": "the arena's fan-out sentence must read as one instruction after background dispatch becomes host-neutral",
        },
        {
            "find": "3. Pick the runners. Use `arena runners` from `~/.cursor/rules/pstack-models.mdc` when present. Otherwise default to one each on `claude-fable-5-1-thinking-max`, `gpt-5.6-sol-max`, `grok-4.6-fast-xhigh`, `claude-opus-5-thinking-xhigh`. Spawn more when the arena covers multiple design directions. Same model N times when the work is generation-bound rather than judgment-sensitive.",
            "replace": "3. Pick the runners. Resolve role `arena runners` from the project role map (`pstack-native.py role-plan --role \"arena runners\"`), one runner per configured entry, duplicates preserved. An empty role is a setup error, not a reason to pick a model yourself. Spawn more when the arena covers multiple design directions. Same model N times when the work is generation-bound rather than judgment-sensitive.",
            "reason": "runner models come from the project role map, not vendor defaults",
        },
        {
            "find": "After all Phase B candidates complete, choose one model from the `arena cross-judge pool` in `~/.cursor/rules/pstack-models.mdc` when present. Otherwise use `claude-fable-5-1-thinking-max`, `gpt-5.6-sol-max`, `grok-4.6-fast-xhigh`, `claude-opus-5-thinking-xhigh`. Prefer a different model family from the parent's. Spawn one readonly judge subagent on that model.",
            "replace": "After all Phase B candidates complete, read the `arena cross-judge pool` with `config-show` and select one index from it: `interrogate`-style panels allocate every entry, but this role is choose-one and must never allocate the whole list. Require an explicit index whenever the pool holds more than one candidate, and pass that same index to `role-plan --role \"arena cross-judge pool\" --index <n>` (or to `run-new --index` and the dispatch request's `--index`). Prefer a different model family from the parent's. Spawn one read-only judge subagent on that model.",
            "reason": "a choose-one judge takes an explicit configured index and never fans out like a panel",
        },
    ],
    "pstack/skills/interrogate/SKILL.md": [
        {
            "find": "Launch all reviewers in a single message using the Task tool. Use the `interrogate reviewers` list from `~/.cursor/rules/pstack-models.mdc` when present, one reviewer per entry, extending or shrinking the Reviewer A/B/C/D labels below to the configured entry count. Otherwise use the table defaults.",
            "replace": "Launch all reviewers in one batch with the host subagent tool. Resolve role `interrogate reviewers` from the project role map (`pstack-native.py role-plan --role \"interrogate reviewers\"`), one reviewer per configured entry, duplicates preserved, extending or shrinking the Reviewer A/B/C/D labels below to the configured entry count. An empty role is a setup error, not a reason to reuse stale labels.",
            "reason": "reviewer models come from the project role map, not vendor defaults",
        },
        {
            "find": "| Subagent | Default model |\n|----------|---------------|\n| Reviewer A | `claude-fable-5-1-thinking-max` |\n| Reviewer B | `gpt-5.6-sol-max` |\n| Reviewer C | `grok-4.6-fast-xhigh` |\n| Reviewer D | `claude-opus-5-thinking-xhigh` |",
            "replace": "| Subagent | Model |\n|----------|-------|\n| Reviewer A | the role map's `interrogate reviewers` entry 1 |\n| Reviewer B | the role map's `interrogate reviewers` entry 2 |\n| Reviewer C | the role map's `interrogate reviewers` entry 3 |\n| Reviewer D | the role map's `interrogate reviewers` entry 4, when the role defines one |\n\nThe labels are a naming convention for a panel of at least one. With fewer configured entries, extend or shrink the labels to the configured count.",
            "reason": "the panel comes from the role map, so the table cannot name vendor defaults",
        },
        {
            "find": "- `subagent_type`: `generalPurpose`\n- `model`: the configured `interrogate reviewers` entry, or the table default with no configured line\n- `readonly`: `true`",
            "replace": "- subagent: the host's general-purpose subagent, read-only\n- `model`: this reviewer's `interrogate reviewers` entry from the role map; omit it for an inherit-parent entry",
            "reason": "reviewer dispatch uses the role map's panel entries",
        },
        {
            "find": "If a model slug is rejected as unresolvable when you try to spawn the subagent, check the valid slugs in the Task tool's error message, pick the closest equivalent (prefer the highest-reasoning tier of the same family), spawn with the valid slug, and open a separate PR to update the configured value or default table. Do not block the review on the slug issue. If the configured value is `inherit-parent` or `auto`, omit `model` instead. Never treat those aliases as broken slugs or enter this fallback for them.",
            "replace": "If the role map names a selector the host rejects, stop and report it. That is a configuration error to fix in the role map, not a licence to substitute a different model: a substituted model makes the diversity claim false. If the entry is `inherit-parent` or `auto`, omit `model`; never treat those aliases as broken selectors.",
            "reason": "silent model substitution would falsify the panel's diversity and is now refused",
        },
    ],
    "pstack/skills/reflect/SKILL.md": [
        {
            "find": "The parent finds its own transcript file before fanning out. The system prompt names the active workspace's `agent-transcripts/` directory. Use that path. Do not glob across `~/.cursor/projects/*/`. That crosses workspace boundaries and reads private chats from unrelated projects.",
            "replace": "The parent finds its own transcript before fanning out. `pstack-native.py paths` and `capability-report` say whether this host exposes session history and where. Read only this workspace's transcripts: never search another project's store, because that crosses workspace boundaries and reads private chats from unrelated projects.",
            "reason": "session history is read through the host's workspace-scoped location, not a Cursor store",
        },
        {
            "find": "```bash\nls -t <agent-transcripts>/*.jsonl <agent-transcripts>/*/*.jsonl <agent-transcripts>/*/subagents/*.jsonl 2>/dev/null | head -10\n```\n\nThree transcript layouts: legacy flat (`<id>.jsonl`), current nested (`<id>/<id>.jsonl`), and subagent (`<parent>/subagents/<child>.jsonl`).",
            "replace": "```bash\nls -t \"$PSTACK_TRANSCRIPTS_DIR\"/*.jsonl \"$PSTACK_TRANSCRIPTS_DIR\"/*/*.jsonl 2>/dev/null | head -10\n```\n\nLayouts vary by host and version: flat (`<id>.jsonl`), nested (`<id>/<id>.jsonl`), and host-specific subagent files. Read what the directory actually holds rather than assuming a layout.",
            "reason": "the transcript layout is host-specific; the resource stops hard-coding Cursor's",
        },
        {
            "find": "One message, three `Task` calls, `subagent_type: generalPurpose`, explicit `model:` on each, agent mode (`readonly: false`). Reviewers need MCP access for context lookups (tickets, chat threads, observability traces referenced in the transcript). Readonly strips MCPs.",
            "replace": "One batch, three subagent dispatches on the host's general-purpose subagent, each with its resolved role model, in agent mode rather than read-only. Reviewers need MCP access for context lookups (tickets, chat threads, observability traces referenced in the transcript), and read-only mode strips MCPs on hosts that make MCP conditional.",
            "reason": "reviewer dispatch follows the host contract and the role map",
        },
        {
            "find": "| Lens | `model` | Prompt template |\n|---|---|---|\n| Judgment | your configured reflect-judgment model (default `claude-fable-5-1-thinking-max`) | `references/judgment-reviewer.md` |\n| Tooling | your configured reflect-tooling model (default `gpt-5.6-sol-max`) | `references/tooling-reviewer.md` |\n| Divergent | your configured reflect-judgment model (default `claude-fable-5-1-thinking-max`) | `references/divergent-reviewer.md` |",
            "replace": "| Lens | `model` | Prompt template |\n|---|---|---|\n| Judgment | role `reflect judgment, divergent, synthesizer` | `references/judgment-reviewer.md` |\n| Tooling | role `reflect tooling` | `references/tooling-reviewer.md` |\n| Divergent | role `reflect judgment, divergent, synthesizer` | `references/divergent-reviewer.md` |\n\nResolve each role with `pstack-native.py role-plan --role \"<role>\"`; when the leg inherits the parent model, omit the model on native dispatch.",
            "reason": "reflect lens models come from the project role map, not vendor defaults",
        },
        {
            "find": "Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in the `Task` response body.",
            "replace": "Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in the subagent report.",
            "reason": "delegation returns through the host subagent facility",
        },
        {
            "find": "One `Task` call, `subagent_type: generalPurpose`, using your configured reflect-judgment model (default `claude-fable-5-1-thinking-max`), agent mode (`readonly: false`). The synthesizer's quality check includes spot-verifying citations, which can require MCP access. Readonly strips MCPs.",
            "replace": "One subagent dispatch on the host's general-purpose subagent, on role `reflect judgment, divergent, synthesizer`, in agent mode rather than read-only. The synthesizer's quality check includes spot-verifying citations, which can require MCP access, and read-only mode strips MCPs on hosts that make MCP conditional.",
            "reason": "synthesizer dispatch follows the role map and the host contract",
        },
        {
            "find": "- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to Cursor's built-in `create-skill` skill and run its draft / test / iterate loop.",
            "replace": "- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to the packaged create-skill guide (`.specify/extensions/pstack/resources/dependencies/create-skill.md`) and run its draft / test / iterate loop.",
            "reason": "the authoring guide ships with this extension",
        },
    ],
    "pstack/skills/reflect/references/divergent-reviewer.md": [
        {
            "find": "- `Read` tool calls against any `SKILL.md` file (workspace `.cursor/skills/`, user-level `~/.cursor/skills/`, or plugin-installed paths under `~/.cursor/plugins/`)\n- `Task` prompts that name a skill path",
            "replace": "- reads of any `SKILL.md` file the session can reach (project skills under `.specify/pstack/skills/`, packaged skills under `.specify/extensions/pstack/resources/skills/`)\n- subagent prompts that name a skill path",
            "reason": "skill locations are host- and project-owned, not Cursor store paths",
        }
    ],
    "pstack/skills/reflect/references/judgment-reviewer.md": [
        {
            "find": "- `Read` tool calls against any `SKILL.md` file (workspace `.cursor/skills/`, user-level `~/.cursor/skills/`, or plugin-installed paths under `~/.cursor/plugins/`)\n- `Task` prompts that name a skill path",
            "replace": "- reads of any `SKILL.md` file the session can reach (project skills under `.specify/pstack/skills/`, packaged skills under `.specify/extensions/pstack/resources/skills/`)\n- subagent prompts that name a skill path",
            "reason": "skill locations are host- and project-owned, not Cursor store paths",
        }
    ],
    "pstack/skills/reflect/references/tooling-reviewer.md": [
        {
            "find": "- `Read` tool calls against any `SKILL.md` file (workspace `.cursor/skills/`, user-level `~/.cursor/skills/`, or plugin-installed paths under `~/.cursor/plugins/`)\n- `Task` prompts that name a skill path",
            "replace": "- reads of any `SKILL.md` file the session can reach (project skills under `.specify/pstack/skills/`, packaged skills under `.specify/extensions/pstack/resources/skills/`)\n- subagent prompts that name a skill path",
            "reason": "skill locations are host- and project-owned, not Cursor store paths",
        }
    ],
    "pstack/skills/no-comments/SKILL.md": [
        {
            "find": '1. Spawn `Task` with `subagent_type: "Comment Sicko"`. Pass the scope. Do not restate its rules.',
            "replace": '1. Dispatch a subagent on the Comment Sicko contract at `.specify/extensions/pstack/resources/agents/comment-sicko.md`. Pass the scope. Do not restate its rules.',
            "reason": "the agent contract ships as a resource because Spec Kit registers no extension agents",
        }
    ],
    "pstack/skills/recall/SKILL.md": [
        {
            "find": "Transcripts live at `~/.cursor/projects/<slug>/agent-transcripts/<uuid>/<uuid>.jsonl`, where `<slug>` is the workspace path with the leading slash dropped and each \"/\" turned into \"-\" (so `/Users/you/proj` becomes `Users-you-proj`). Every line is one chat message.",
            "replace": "Transcripts live in this workspace's transcript directory, named by the host and reported by `pstack-native.py capability-report`. The layout varies by host and version, and every line is one chat message. `PSTACK_TRANSCRIPTS_DIR` carries the path when the host stores sessions outside the project.",
            "reason": "session history is host-owned; the Cursor store path and its slug rule no longer exist",
        },
        {
            "find": "Tell every subagent to order candidates by real modification time (`ls -t`) and never by UUID name,",
            "replace": "Tell every subagent to order candidates by real modification time (`ls -t`) and never by session id,",
            "reason": "session ids are host-specific identifiers, not UUIDs everywhere",
        },
        {
            "find": "5. Verify against live state. Take the PRs, branches, and tickets that the mining and the sweep surfaced and check them with `git` and `gh`.",
            "replace": "5. Verify against live state. Take the PRs, branches, and tickets that the mining and the sweep surfaced and check them with `git` and the forge CLI the capability report found (`gh`, or `origin` where it resolves).",
            "reason": "forge access is capability-checked rather than assumed",
        },
    ],
    "pstack/skills/create-verification-skill/SKILL.md": [
        {
            "find": "This skill generates that as a project-local skill (`.cursor/skills/verify-<app>/`) tailored to the repo.",
            "replace": "This skill generates that as one project-local skill (`verify-<app>/`) tailored to the repo, written into a single project skill directory this host discovers.",
            "reason": "a generated project skill has one canonical host-discovered location",
        },
        {
            "find": "Write `.cursor/skills/verify-<app>/SKILL.md` with YAML frontmatter (`name: verify-<app>` and a `description` that names the app, the surface, and when to reach for it — without frontmatter the skill never registers)",
            "replace": "Run `pstack-native.py paths` and take `skills_dirs`. Write `verify-<app>/SKILL.md` into exactly one of those directories, the first unless the user names another; do not also keep a copy under `.specify/pstack/skills/` and do not link the two. Only when `skills_dirs` lists nothing does the skill go under `.specify/pstack/skills/verify-<app>/`, and then the instruction file or the task brief must point at that path, because nothing discovers it. Either way it carries YAML frontmatter (`name: verify-<app>` and a `description` that names the app, the surface, and when to reach for it), and without frontmatter it never registers",
            "reason": "the skill is written into one host-discovered directory, with the fallback only when the host discovers none",
        },
        {
            "find": "Create `.cursor/skills/verify-<app>/features/README.md` plus one file per user-facing feature you can identify",
            "replace": "Create `features/README.md` in that same skill directory plus one file per user-facing feature you can identify",
            "reason": "the feature map lives inside the one canonical skill directory",
        },
    ],
    "pstack/skills/maintain-verification-skill/SKILL.md": [
        {
            "find": "Find the verification skill to maintain: the project-local skill whose body has launch/drive sections and a feature map (usually `.cursor/skills/verify-*/`). Several candidates → ask which one; none → stop and point at `/create-verification-skill` instead of inventing a target.",
            "replace": "Find the verification skill to maintain: the project-local skill whose body has launch/drive sections and a feature map, in one of the directories `skills_dirs` names in the `pstack-native.py paths` report, or under `.specify/pstack/skills/` when that list is empty. Several candidates → ask which one; none → stop and point at `speckit.pstack.create-verification-skill` instead of inventing a target.",
            "reason": "the target is located through the host's discovered directories and the native command name",
        }
    ],
    "pstack/skills/automate-me/SKILL.md": [
        {
            "find": "This skill orchestrates three others: an inline mining pass (see step 1), Cursor's built-in `create-skill` (authoring), and the **unslop** skill (prose discipline).",
            "replace": "This skill orchestrates three others: an inline mining pass (see step 1), the packaged create-skill guide (`.specify/extensions/pstack/resources/dependencies/create-skill.md`, authoring), and the **unslop** skill (prose discipline).",
            "reason": "the authoring guide ships with this extension",
        },
        {
            "find": "Look recursively for `.cursor/skills/**/*-mode/SKILL.md` and `~/.cursor/skills/*-mode/SKILL.md` matching the user's handle. Mode skills can live in a personal category directory (`.cursor/skills/<handle>/`), not only at the top level.",
            "replace": "Search every directory `skills_dirs` names in the `pstack-native.py paths` report for `**/*-mode/SKILL.md` matching the user's handle, and search `.specify/pstack/skills/**/*-mode/SKILL.md` only when that list is empty. A mode skill can sit in a category directory (`<skills_dir>/<handle>/`), not only at the top level.",
            "reason": "project skill locations are project- and host-owned",
        },
        {
            "find": "Locate the active workspace's transcripts before fanning out. The system prompt names the workspace's `agent-transcripts/` directory. Use only that path. Don't glob across `~/.cursor/projects/*/`.",
            "replace": "Locate this workspace's transcripts before fanning out: `pstack-native.py capability-report` says whether the host exposes them, and `PSTACK_TRANSCRIPTS_DIR` carries the path. Use only that path. Don't search another project's store.",
            "reason": "session history location is reported by the host, not assumed from a Cursor store",
        },
        {
            "find": "Mining misses intent that hasn't come up yet. Use the `AskQuestion` tool (structured multi-choice) rather than asking the user to type from scratch.",
            "replace": "Mining misses intent that hasn't come up yet. Use the host's question prompt with structured choices rather than asking the user to type from scratch.",
            "reason": "the question tool is a host facility",
        },
        {
            "find": "Use Cursor's built-in `create-skill` skill to author the skill. Placement:",
            "replace": "Use the packaged create-skill guide (`.specify/extensions/pstack/resources/dependencies/create-skill.md`) to author the skill. Placement:",
            "reason": "the authoring guide ships with this extension",
        },
        {
            "find": "- Path: preserve an existing mode skill's category. For a new mode, use `.cursor/skills/<handle>/<handle>-mode/SKILL.md` when the repo has an established personal category for that handle. Otherwise default to `.cursor/skills/<handle>-mode/SKILL.md` in the project (or `~/.cursor/skills/<handle>-mode/` if the user prefers a personal skill).",
            "replace": "- Path: preserve an existing mode skill's category. Otherwise write the new mode skill into exactly one directory from `skills_dirs` in the `pstack-native.py paths` report, the first unless the user names another, keeping the category directory when the repo has an established one for that handle. Only when `skills_dirs` is empty does it go under `.specify/pstack/skills/<handle>-mode/`, and then the instruction file or brief has to point at it. One file, one location: no second copy and no symlink. Then confirm discovery with that report's `discovery_check`.",
            "reason": "project skill locations are project- and host-owned",
        },
    ],
    "pstack/skills/show-me-your-work/SKILL.md": [
        {
            "find": "Read this run's transcript under the active workspace's `agent-transcripts/` directory (the system prompt names the path). Don't glob across `~/.cursor/projects/*/`. That reads unrelated private chats.",
            "replace": "Read this run's transcript from this workspace's transcript directory (`pstack-native.py capability-report` says whether the host exposes it; `PSTACK_TRANSCRIPTS_DIR` carries the path). Don't search another project's store: that reads unrelated private chats.",
            "reason": "session history location is host-reported, not a Cursor store path",
        }
    ],
    "pstack/skills/poteto-mode/playbooks/autonomous-run.md": [
        {
            "find": "2. Pick the wake mechanism using Cursor's `/loop` command (a built-in, not a pstack skill). An event to watch (CI, a merge, a ref advancing) gets a watcher subagent that wakes you on the event, with a long time-based heartbeat as fallback. No event gets a fixed-interval heartbeat sized to when the result is worth re-checking.",
            "replace": "2. Pick the wake mechanism from what the host actually has. `pstack-native.py capability-report` decides it: a host with a supervised long-lived process or loop facility gets a watcher that wakes on the event (CI, a merge, a ref advancing), with a long time-based heartbeat as fallback; a host with none gets one iteration per turn, driven by the user or by a supervised process the user started. No event gets a fixed-interval heartbeat sized to when the result is worth re-checking, and no run claims survival past the process that holds it.",
            "reason": "the durable wakeup is a checked host capability, not a Cursor built-in command",
        },
        {
            "find": "Do not park reversible work for the human or use `AskQuestion`.",
            "replace": "Do not park reversible work for the human or use the host's question prompt.",
            "reason": "the question tool is a host facility",
        },
    ],
    "pstack/skills/poteto-mode/playbooks/orchestrate.md": [
        {
            "find": "The loop is agentic end to end. Agents are spawned, resumed, and drained only through the Task tool.",
            "replace": "The loop is agentic end to end. Agents are spawned and drained only through the host's subagent facility, and a resume is a fresh dispatch with the stored brief plus current state.",
            "reason": "delegation uses the host subagent facility, and native workers have no resume channel",
        },
        {
            "find": "- **Worker / verifier.** Always `environment: \"cloud\"` unless the task needs this machine: `control-ui` or `control-cli` runtime verification (from `cursor-team-kit`). Reading local transcripts under `agent-transcripts/`. Simulators and local IDE state. Auth that exists only here. Cloud agents cannot read the local store, so their briefs inline what they need or point at repo paths. Prefer fewer, broader workers.",
            "replace": "- **Worker / verifier.** There is no cloud environment here. Every worker is a native subagent in an isolated local worktree, and it stops when the machine or the process stops, so nothing survives an interrupted host. Work that needs this machine's runtime (the packaged `control-ui` or `control-cli` reference, local transcripts under the workspace transcript directory, simulators, local IDE state, or auth that exists only here) always runs locally. Because no worker can read another's session, every brief inlines what the worker needs or points at repo paths. Prefer fewer, broader workers.",
            "reason": "cloud workers map to isolated local workers, with the lost survival stated explicitly",
        },
        {
            "find": "(nesting works to depth 3, and a nested spawn has the full Task schema including `environment`)",
            "replace": "(the host may cap nesting depth; check it and flatten when it is capped, and a nested spawn carries the same contract as a top-level one)",
            "reason": "nesting depth and the spawn schema are host properties, not Cursor's",
        },
        {
            "find": "- After a Cursor restart: local agents are dead, cloud work is not.",
            "replace": "- After a host restart: every native worker is dead. Only side effects that reached durable state (commits, pushed branches, PRs, store files) survive.",
            "reason": "no cloud workers exist to outlive a restart",
        },
        {
            "find": "- Never resume an agent to check on it. A resume restarts an idle agent. Probe read-only: the ledger, `units.tsv`, `gh`, pushed branches, the cloud agent's status in the Cursor dashboard. Transcript mtime is not liveness.",
            "replace": "- Never resume an agent to check on it; a resume restarts an idle worker and costs a full brief. Probe read-only: the ledger, `units.tsv`, the forge CLI, pushed branches, and the process table. Transcript mtime is not liveness.",
            "reason": "there is no cloud dashboard to poll; liveness comes from durable state and the process table",
        },
        {
            "find": "- Exactly one stacker per stack may run `gt`, serialized within its stack. Record the holder in the standing orders. Restacks run in cloud. A local restack at this scale takes the laptop down.",
            "replace": "- Exactly one stacker per stack may run `gt`, serialized within its stack. Record the holder in the standing orders. Restacks run in a local isolated worktree, serialized. A restack at this scale on the live checkout takes the machine down.",
            "reason": "cloud execution maps to isolated local worktrees",
        },
        {
            "find": "Verbatim paste is for cloud spawns and every resume.",
            "replace": "Verbatim paste is for every dispatch, and every resume is a fresh dispatch with the standing orders pasted.",
            "reason": "there are no cloud spawns; a native resume is a new dispatch",
        },
        {
            "find": "**Reply:** at checkpoints and close: the predicate and the count against it from `units.tsv` and `ledger.tsv`",
            "replace": "**Reply:** at checkpoints and close: the predicate and the count against it from `units.tsv` and `ledger.tsv`. Name the worker environment each unit used, since only local environments exist",
            "reason": "the reply states the local-only worker environment",
        },
    ],
    "pstack/skills/poteto-mode/playbooks/multi-phase-plan.md": [
        {
            "find": "The live block is mandatory.",
            "replace": "The live block is mandatory. Resolve role `swarm workers` before writing the plan, resolve an inheritance alias to the current concrete model, and replace every `<resolved swarm workers model>` placeholder with that selector.",
            "reason": "the plan validator needs the concrete model that will run each live lane",
        },
        {
            "find": "Ten lanes on `grok-4.6-fast-xhigh` at the PR head",
            "replace": "Ten lanes on `<resolved swarm workers model>` at the PR head",
            "reason": "the plan author fills a concrete model from the project role map",
            "count": 2,
        },
        {
            "find": "3. Explore in subagents with `subagent_type: \"poteto-agent\"` and an explicit model",
            "replace": "3. Explore in subagents on the poteto-agent contract (`.specify/extensions/pstack/resources/agents/poteto-agent.md`) with the concrete model resolved from the role map",
            "reason": "the agent contract ships as a resource and the model comes from the role map",
        },
        {
            "find": "5. Write under `/technical-writing` in full, then `/unslop`.",
            "replace": "5. Write under the packaged `technical-writing` skill in full, then apply the packaged `unslop` skill.",
            "reason": "resources name packaged skills instead of a host invocation form",
        },
        {
            "find": "6. Run `node pstack/skills/poteto-mode/scripts/check-plan.mjs <plan.md>`",
            "replace": "6. Run `node .specify/extensions/pstack/resources/skills/poteto-mode/scripts/check-plan.mjs <plan.md>`",
            "reason": "the executable is read from its installed extension path",
        },
        {
            "find": "**Control skill.** Pick it by surface. Browser, Electron, and web UIs use `control-ui` from `cursor-team-kit`. CLIs and TUIs use `control-cli` from `cursor-team-kit`.",
            "replace": "**Control skill.** Pick it by surface. Browser, Electron, and web UIs use the packaged `control-ui` reference (`.specify/extensions/pstack/resources/dependencies/control-ui.md`). CLIs and TUIs use the packaged `control-cli` reference (`.specify/extensions/pstack/resources/dependencies/control-cli.md`).",
            "reason": "the dependency ships inside this extension instead of a separate Cursor plugin",
        },
        {
            "find": "The program runs `pstack/skills/poteto-mode/playbooks/<execution playbook>.md`.",
            "replace": "The program runs `.specify/extensions/pstack/resources/skills/poteto-mode/playbooks/<execution playbook>.md`.",
            "reason": "the plan names the installed playbook path",
        },
        {
            "find": "- [ ] On the operator's go, arm a `/goal` with this exact text.",
            "replace": "- [ ] On the operator's go, record the program objective as the standing predicate, in the trail and in the coordinator's brief header, with this exact text.",
            "reason": "there is no `/goal` facility; the predicate lives in durable state",
        },
        {
            "find": "- [ ] Read these from trunk at program start. Re-read them at every tick.\n  - [ ] `git show origin/main:pstack/skills/poteto-mode/playbooks/<execution playbook>.md`\n  - [ ] `git show origin/main:pstack/skills/swarm/SKILL.md`\n  - [ ] `git show origin/main:<control skill path>`\n  - [ ] `git show origin/main:pstack/skills/poteto-mode/playbooks/opening-a-pr.md`\n  - [ ] `git show origin/main:pstack/skills/<each other leaf skill the program uses>`",
            "replace": "- [ ] Read these from the installed extension at program start. Re-read them at every tick.\n  - [ ] `.specify/extensions/pstack/resources/skills/poteto-mode/playbooks/<execution playbook>.md`\n  - [ ] `.specify/extensions/pstack/resources/skills/swarm/SKILL.md`\n  - [ ] `.specify/extensions/pstack/resources/dependencies/<control skill>.md`\n  - [ ] `.specify/extensions/pstack/resources/skills/poteto-mode/playbooks/opening-a-pr.md`\n  - [ ] `.specify/extensions/pstack/resources/skills/<each other leaf skill>/SKILL.md`",
            "reason": "installed extension resources are runtime files, not blobs on the target repository's trunk",
        },
        {
            "find": "- [ ] Arm the 30-minute audit tick. In a local session, a real terminal `/loop`. In a cloud root, a cloud-sleeper wake chain. Never leave the cadence to memory.",
            "replace": "- [ ] Arm the 30-minute audit tick only on a host that reports a supervised long-lived process or loop facility (`pstack-native.py capability-report`). Without one, the tick runs when the operator next addresses the coordinator, and the trail says so. Never leave the cadence to memory.",
            "reason": "the wake facility is capability-checked; cloud wake chains do not exist here",
        },
        {
            "find": "- [ ] Use this tick prompt, verbatim. \"Re-read the execution playbook from trunk and the armed /goal.",
            "replace": "- [ ] Use this tick prompt, verbatim. \"Re-read the execution playbook from the installed extension and the recorded program objective.",
            "reason": "the runtime contract comes from the installed resource and the objective from the trail",
        },
        {
            "find": "- [ ] Run `/deslop` before each commit and `/no-comments` before review.",
            "replace": "- [ ] Apply `.specify/extensions/pstack/resources/dependencies/deslop.md` before each commit and the packaged `no-comments` skill before review.",
            "reason": "the plan names packaged resources instead of Cursor command forms",
        },
        {
            "find": "- [ ] At the merge-ready head SHA, run the swarm per `pstack/skills/swarm/SKILL.md`.",
            "replace": "- [ ] At the merge-ready head SHA, run the swarm per `.specify/extensions/pstack/resources/skills/swarm/SKILL.md`.",
            "reason": "the plan names the installed swarm resource",
        },
        {
            "find": "Each live lane runs on its own cloud VM at the PR head. Drive through `control-ui` or `control-cli` from `cursor-team-kit`.",
            "replace": "Each live lane runs in its own isolated local worktree at the PR head, and stops when the machine stops. Drive through the packaged `control-ui` or `control-cli` reference (`.specify/extensions/pstack/resources/dependencies/`).",
            "reason": "cloud VMs map to isolated local worktrees with no survival claim",
        },
        {
            "find": "<Docs to read before editing. Which PRs get `pstack/skills/how/SKILL.md` and `pstack/skills/interrogate/SKILL.md`. The trail per `pstack/skills/show-me-your-work/SKILL.md`.>",
            "replace": "<Docs to read before editing. Which PRs get `.specify/extensions/pstack/resources/skills/how/SKILL.md` and `.specify/extensions/pstack/resources/skills/interrogate/SKILL.md`. The trail per `.specify/extensions/pstack/resources/skills/show-me-your-work/SKILL.md`.>",
            "reason": "the reading list names installed resource paths",
        },
    ],
    "pstack/skills/poteto-mode/playbooks/autopilot-full.md": [
        {
            "find": "On that go, arm a `/goal` with the full program objective. The goal continues across turns until the queue is done.",
            "replace": "On that go, record the full program objective as the standing predicate in the trail and in every owner brief. It continues across turns until the queue is done.",
            "reason": "there is no `/goal` facility; the objective lives in durable state",
        },
        {
            "find": "One Cursor cloud agent per PR owns build, the first push, a ready PR, self-proof on the real artifact",
            "replace": "One isolated local worker per PR owns build, the first push, a ready PR, self-proof on the real artifact",
            "reason": "cloud workers map to isolated local workers",
        },
        {
            "find": "A local root arms each tick as a real terminal `/loop`. The loop uses a monitored-shell 30-minute sleep and emits an output-notification sentinel. A cloud root uses the existing cloud-sleeper wake chain instead. Never leave the cadence to memory or lossy completion notifications.",
            "replace": "A host with a supervised long-lived process or loop facility (`pstack-native.py capability-report`) arms each tick as a real terminal process with a monitored 30-minute sleep. Without one, the tick runs when the operator next addresses the root. Never leave the cadence to memory or lossy completion notifications.",
            "reason": "the wake facility is capability-checked; cloud wake chains do not exist here",
        },
        {
            "find": "re-read this playbook from trunk with `git show origin/main:pstack/skills/poteto-mode/playbooks/autopilot-full.md`",
            "replace": "re-read this playbook directly at `.specify/extensions/pstack/resources/skills/poteto-mode/playbooks/autopilot-full.md`",
            "reason": "the runtime resource is the installed file, not a blob on the target repository's trunk",
        },
    
        {
            "find": "then re-read the armed `/goal`.",
            "replace": "then re-read the recorded program objective.",
            "reason": "there is no `/goal` facility; the objective lives in durable state",
        }
    ],
    "pstack/skills/poteto-mode/playbooks/autopilot-stack.md": [
        {
            "find": "One Cursor cloud agent per PR owns its change end to end:",
            "replace": "One isolated local worker per PR owns its change end to end:",
            "reason": "cloud workers map to isolated local workers",
        },
        {
            "find": "A local root arms each tick as a real terminal `/loop`. The loop uses a monitored-shell 30-minute sleep and emits an output-notification sentinel. A cloud root uses the existing cloud-sleeper wake chain instead.",
            "replace": "A host with a supervised long-lived process or loop facility (`pstack-native.py capability-report`) arms each tick as a real terminal process with a monitored 30-minute sleep. Without one, the tick runs when the operator next addresses the root.",
            "reason": "the wake facility is capability-checked; cloud wake chains do not exist here",
        },
        {
            "find": "re-read this playbook from trunk with `git show origin/main:pstack/skills/poteto-mode/playbooks/autopilot-stack.md`, then re-read the armed `/goal`.",
            "replace": "re-read `.specify/extensions/pstack/resources/skills/poteto-mode/playbooks/autopilot-stack.md` directly, then re-read the recorded program objective.",
            "reason": "the runtime resource is the installed file and the objective lives in the trail",
        },
        {
            "find": "On the operator's explicit go, arm a `/goal` with the full program objective. The goal continues across turns until the chain is done.",
            "replace": "On the operator's explicit go, record the full program objective as the standing predicate in the trail. It continues across turns until the chain is done.",
            "reason": "there is no `/goal` facility; the objective lives in durable state",
        },
    ],
    "pstack/skills/poteto-mode/playbooks/shipping.md": [
        {
            "find": "One subagent per PR, not batched, each a Cursor cloud agent, each exercising the real surface (`control-ui` or `control-cli` from `cursor-team-kit` as the change demands) against parent versus head.",
            "replace": "One subagent per PR, not batched, each an isolated local worker, each exercising the real surface (the packaged `control-ui` or `control-cli` reference as the change demands) against parent versus head.",
            "reason": "cloud workers map to isolated local workers and the dependency ships in the extension",
        }
    ],
    "pstack/skills/poteto-mode/playbooks/eval.md": [
        {
            "find": "Read each candidate's local transcript under the active workspace's `agent-transcripts/` directory (the system prompt names this path). Do not glob across `~/.cursor/projects/*/`. That crosses workspace boundaries and reads private chats from unrelated projects.",
            "replace": "Read each candidate's transcript from this workspace's transcript directory (`pstack-native.py capability-report` says whether the host exposes it; `PSTACK_TRANSCRIPTS_DIR` carries the path). Do not search another project's store: that crosses workspace boundaries and reads private chats from unrelated projects.",
            "reason": "session history location is host-reported, not a Cursor store path",
        }
    ],
    "pstack/skills/poteto-mode/playbooks/session-pickup.md": [
        {
            "find": "A local transcript under the active workspace's `agent-transcripts/` directory (the system prompt names the path. Do not glob across `~/.cursor/projects/*/`, that crosses workspace boundaries and reads private chats from unrelated projects), a cloud-agent URL, or a pushed branch.",
            "replace": "A transcript from this workspace's transcript directory (`pstack-native.py capability-report` says whether the host exposes it; `PSTACK_TRANSCRIPTS_DIR` carries the path. Do not search another project's store, that crosses workspace boundaries and reads private chats from unrelated projects), a pushed branch, or a handed-off brief from another agent.",
            "reason": "the source is a host-owned transcript or a branch, not a Cursor cloud-agent URL",
        }
    ],
    "pstack/skills/poteto-mode/playbooks/bug-fix.md": [
        {
            "find": "Drive a long or stubborn hunt with Cursor's `/loop` command.",
            "replace": "Drive a long or stubborn hunt with the wake mechanism the capability report found: a supervised loop on hosts that have one, otherwise one iteration per turn.",
            "reason": "the loop facility is capability-checked, not a Cursor built-in",
        }
    ],
    "pstack/skills/poteto-mode/playbooks/visual-parity.md": [
        {
            "find": "`/loop` per component until the diff is zero.",
            "replace": "Iterate per component until the diff is zero, using the host's loop facility when the capability report finds one and one pass per turn when it does not.",
            "reason": "the loop facility is capability-checked, not a Cursor built-in",
        }
    ],
    "pstack/skills/poteto-mode/playbooks/worktree-cleanup.md": [
        {
            "find": "since a hand-typed `myrepo-worktrees/x` misses one that lives at `.cursor/worktrees/myrepo/x`",
            "replace": "since a hand-typed `myrepo-worktrees/x` misses one that lives at `.worktrees/myrepo/x`",
            "reason": "the example worktree path is project-relative",
        },
        {
            "find": "`~/Library/Application Support/Cursor` (`state.vscdb.backup`, and `snapshots/roots/<root>` where a `<root>` named for a folder you opened as a workspace balloons)",
            "replace": "editor state caches (for example the host editor's own workspace storage), naming whichever exists on this machine",
            "reason": "the reclaim list must name caches that exist on the current machine",
        },
    ],
    "pstack/skills/poteto-mode/playbooks/opening-a-pr.md": [
        {
            "find": "Run `/deslop` from `cursor-team-kit` over the diff before commit.",
            "replace": "Run the packaged deslop reference (`.specify/extensions/pstack/resources/dependencies/deslop.md`) over the diff before commit.",
            "reason": "the dependency ships in the extension and the host resolves no Cursor plugin",
        },
        {
            "find": "Multiple `Task` calls on the same branch each get their own worktree, or `git fetch && git reset --hard origin/<branch>` between them.",
            "replace": "Multiple subagent dispatches on the same branch each get their own worktree, or `git fetch && git reset --hard origin/<branch>` between them.",
            "reason": "delegation uses the host subagent facility",
        },
    ],
    "pstack/skills/poteto-mode/playbooks/authoring-a-skill.md": [
        {
            "find": "1. Use the **create-skill** skill (Cursor's built-in for authoring SKILL.md files).",
            "replace": "1. Use the packaged create-skill guide (`.specify/extensions/pstack/resources/dependencies/create-skill.md`).",
            "reason": "the authoring guide ships with this extension",
        }
    ],
    "pstack/skills/poteto-mode/playbooks/feature.md": [
        {
            "find": "using your configured feature model (default `grok-4.6-fast-xhigh`)",
            "replace": "on role `feature, refactoring` from the project role map (`pstack-native.py role-plan --role \"feature, refactoring\"`); omit the model when the leg inherits the current one",
            "reason": "the delegate model comes from the project role map, not a vendor default",
        }
    ],
    "pstack/skills/poteto-mode/playbooks/refactoring.md": [
        {
            "find": "using your configured refactoring model (default `grok-4.6-fast-xhigh`)",
            "replace": "on role `feature, refactoring` from the project role map (`pstack-native.py role-plan --role \"feature, refactoring\"`); omit the model when the leg inherits the current one",
            "reason": "the delegate model comes from the project role map, not a vendor default",
        }
    ],
    "pstack/skills/poteto-mode/playbooks/bug-fix.md": [
        {
            "find": "using your configured bug-fix model (default `grok-4.6-fast-xhigh`)",
            "replace": "on role `bug-fix` from the project role map (`pstack-native.py role-plan --role \"bug-fix\"`); omit the model when the leg inherits the current one",
            "reason": "the delegate model comes from the project role map, not a vendor default",
        }
    ],
    "pstack/skills/poteto-mode/playbooks/perf-issue.md": [
        {
            "find": "using your configured perf-issue model (default `grok-4.6-fast-xhigh`)",
            "replace": "on role `perf-issue` from the project role map (`pstack-native.py role-plan --role \"perf-issue\"`); omit the model when the leg inherits the current one",
            "reason": "the delegate model comes from the project role map, not a vendor default",
        }
    ],
    "pstack/skills/poteto-mode/playbooks/hillclimb.md": [
        {
            "find": "using your configured hillclimb model (default `grok-4.6-fast-xhigh`)",
            "replace": "on role `hillclimb` from the project role map (`pstack-native.py role-plan --role \"hillclimb\"`); omit the model when the leg inherits the current one",
            "reason": "the delegate model comes from the project role map, not a vendor default",
        }
    ],
    "pstack/skills/architect/SKILL.md": [
        {
            "find": "Use your configured architect runners (defaults `claude-fable-5-1-thinking-max`, `gpt-5.6-sol-max`, `grok-4.6-fast-xhigh`, `claude-opus-5-thinking-xhigh`).",
            "replace": "Resolve role `architect runners` from the project role map (`pstack-native.py role-plan --role \"architect runners\"`), one runner per configured entry, duplicates preserved. An empty role is a setup error, not a reason to pick a model yourself.",
            "reason": "runner models come from the project role map, not vendor defaults",
        }
    ],



    "pstack/docs/guide/07-overnight.md": [{"find": "/loop until done. if you're truly stuck after a few hours, stop and write up why.", "replace": "run until it is done. if you're truly stuck after a few hours, stop and write up why.", "reason": "the overnight instruction no longer names a Cursor command"}],
    "pstack/docs/guide/10-recipes-and-pitfalls.md": [{"find": "with pinned cards reading /how, /tdd, and /loop above the counter.", "replace": "with pinned cards reading /how, /tdd, and the run instruction above the counter.", "reason": "image alt text no longer names a Cursor command"}],
    "pstack/skills/poteto-mode/playbooks/babysit.md": [{"find": "Run `drive` and `background` under `/loop` in dynamic mode.", "replace": "Run `drive` and `background` under the host's supervised loop when the capability report finds one, and one watch pass per turn when it does not.", "reason": "the watch loop is a capability-checked host facility, not a Cursor command"}],
    "pstack/skills/poteto-mode/playbooks/shipping.md": [{"find": "Hold the watch under `/loop` in dynamic mode.", "replace": "Hold the watch under the host's supervised loop when the capability report finds one, and one watch pass per turn when it does not.", "reason": "the watch loop is a capability-checked host facility, not a Cursor command"}],
    "pstack/skills/poteto-mode/playbooks/bug-fix.md": [{"find": "Drive a long or stubborn hunt with Cursor's `/loop` command.", "replace": "Drive a long or stubborn hunt with the wake mechanism the capability report found: a supervised loop on hosts that have one, otherwise one iteration per turn.", "reason": "the loop facility is capability-checked, not a Cursor built-in"}],
    "pstack/skills/poteto-mode/scripts/check-plan.mjs": [
        {
            "find": 'const LANES = "Ten lanes on `grok-4.6-fast-xhigh` at the PR head";',
            "replace": 'const LANES = /Ten lanes on `([^`\\n]+)` at the PR head/;\nconst LIVE_MODEL = process.env.PSTACK_LIVE_MODEL || "";',
            "reason": "the plan supplies a concrete resolved live-lane model, optionally pinned by the caller",
        },
        {
            "find": 'const PROGRAM_MARKERS = ["/goal", "git show origin/main:", /30[- ]minute/, "status message"];',
            "replace": 'const PROGRAM_MARKERS = ["standing predicate", "installed extension", /30[- ]minute/, "status message"];',
            "reason": "the program check matches the native standing predicate and installed-resource instructions",
        },
        {
            "find": 'if (!live.rest.includes(LANES)) fail(live.n, `${pr.title}: Verify, live lacks "${LANES}"`);',
            "replace": 'const liveHeader = live.rest.match(LANES);\n\tif (!liveHeader) fail(live.n, `${pr.title}: Verify, live lacks the ten-lane header`);\n\telse if (\n\t\t/[<>]/.test(liveHeader[1]) ||\n\t\tliveHeader[1] !== liveHeader[1].trim() ||\n\t\t/^(?:auto|default|parent|inherit[-_]parent)$/i.test(liveHeader[1])\n\t)\n\t\tfail(live.n, `${pr.title}: Verify, live must name a concrete resolved model`);\n\telse if (LIVE_MODEL && liveHeader[1] !== LIVE_MODEL)\n\t\tfail(live.n, `${pr.title}: Verify, live names ${liveHeader[1]}, expected ${LIVE_MODEL}`);',
            "reason": "requires the native ten-lane header and a concrete model, then checks an optional pin",
        },
    ],
    "pstack/skills/poteto-mode/scripts/worktree-audit.sh": [
        {
            "find": "# Transcripts dir: ~/.cursor/projects/<slugified-repo-path>/agent-transcripts.\nslug=$(printf '%s' \"$main_wt\" | sed 's#^/##; s#/#-#g')\ntranscripts=\"$HOME/.cursor/projects/$slug/agent-transcripts\"\nnow=$(date +%s)",
            "replace": """# Transcripts dir: this workspace only, named by PSTACK_TRANSCRIPTS_DIR. When it
# is unset or missing, the last-chat column stays empty and no worktree is called
# safe on transcript evidence (see the bucket rule below).
transcripts="${PSTACK_TRANSCRIPTS_DIR:-}"
now=$(date +%s)

# stat and date differ between GNU and BSD; try GNU first, then BSD.
mtime_of() {
	stat -c '%Y' "$1" 2>/dev/null || stat -f '%m' "$1" 2>/dev/null
}
format_mtime() {
	date -d "@$1" '+%Y-%m-%d' 2>/dev/null || date -r "$1" '+%Y-%m-%d' 2>/dev/null
}""",
            "reason": "the transcript source is this workspace's explicit path and stat/date work on GNU and BSD",
        },
        {
            "find": "\tlast=\"-\"; last_ts=0\n\tif [ -d \"$transcripts\" ]; then\n\t\tf=$(rg -l -e \"${wt}/\" -e \"${wt}\\\"\" \"$transcripts\" 2>/dev/null \\\n\t\t\t| xargs stat -f '%m %N' 2>/dev/null | sort -rn | head -1)\n\t\tif [ -n \"$f\" ]; then last_ts=$(echo \"$f\" | awk '{print $1}')\n\t\t\tlast=$(date -r \"$last_ts\" '+%Y-%m-%d' 2>/dev/null); fi\n\tfi\n\trecent=$([ \"$last_ts\" -gt 0 ] 2>/dev/null && [ $(( (now - last_ts) / 86400 )) -le 4 ] && echo yes || echo no)\n\n\tcase \"$dirty\" in wip:*) bucket=hold-wip ;; *)\n\t\tcase \"$pr\" in *OPEN*) bucket=hold-open-pr ;; *)\n\t\t\tif [ \"$recent\" = yes ]; then bucket=verify-recent-chat\n\t\t\telif [ \"$merged\" = YES ] || [ \"$pr\" != \"-\" ]; then bucket=safe\n\t\t\telse bucket=review; fi ;;\n\t\tesac ;;\n\tesac",
            "replace": """	last="-"; last_ts=0; transcripts_available=no
	if [ -n "$transcripts" ] && [ -d "$transcripts" ]; then
		scan=$(mktemp 2>/dev/null) || scan=""
		if [ -n "$scan" ]; then
			transcripts_available=yes
			rg_status=0
			rg -F -0 -l -e "${wt}/" -e "${wt}\\\"" "$transcripts" > "$scan" 2>/dev/null || rg_status=$?
			if [ "$rg_status" -gt 1 ]; then
				transcripts_available=no
			else
				while IFS= read -r -d '' transcript; do
					ts=$(mtime_of "$transcript") || { transcripts_available=no; last_ts=0; break; }
					if ! [[ "$ts" =~ ^[0-9]+$ ]]; then
						transcripts_available=no; last_ts=0; break
					fi
					if [ "$ts" -gt "$last_ts" ]; then last_ts=$ts; fi
				done < "$scan"
			fi
			rm -f "$scan"
		fi
	fi
	if [ "$last_ts" -gt 0 ]; then last=$(format_mtime "$last_ts") || last="?"; fi
	recent=$([ "$transcripts_available" = yes ] && [ "$last_ts" -gt 0 ] 2>/dev/null && [ $(( (now - last_ts) / 86400 )) -le 4 ] && echo yes || echo no)

	# Conservative bucket: without transcript evidence the audit can only say a
	# worktree is worth a look, never that it is safe to prune.
	case "$dirty" in wip:*) bucket=hold-wip ;; *)
		case "$pr" in *OPEN*) bucket=hold-open-pr ;; *)
			if [ "$transcripts_available" = no ]; then bucket=review-no-transcripts
			elif [ "$recent" = yes ]; then bucket=verify-recent-chat
			elif [ "$merged" = YES ] || [ "$pr" != "-" ]; then bucket=safe
			else bucket=review; fi ;;
		esac ;;
	esac""",
            "reason": "no worktree is bucketed safe on absent transcript evidence, and the mtime helpers are portable",
        },
    ],
    "pstack/automations/benny/skills/reproduce-and-fix-issues/SKILL.md": [
        {
            "find": "Prefer configured Cursor Slack actions. Use `BENNY_SLACK_BOT_TOKEN` only when the user configured it for a narrow missing capability such as editing this one status message. Never expose the token to a worker.",
            "replace": "Prefer the Slack tool the user configured. Use `BENNY_SLACK_BOT_TOKEN` only when the user configured it, for a narrow missing capability such as editing this one status message, and read it from the host's secret store. Never expose the token to a worker.",
            "reason": "Slack access is user-supplied and its credential stays server-side",
        }
    ],
    "pstack/automations/benny/skills/triage-issue-reports/references/routing.example.md": [
        {
            "find": "Copy this file outside `.cursor/automations/benny/`, for example to `.cursor/benny/routing.md`, and replace every placeholder.",
            "replace": "Copy this file outside `.specify/pstack/automations/benny/`, for example to `.specify/pstack/benny/routing.md`, and replace every placeholder.",
            "reason": "user-owned copies live outside the pack",
        }
    ],
    "pstack/automations/benny/skills/reproduce-and-fix-issues/references/feature-map.example.md": [
        {
            "find": "Copy this file outside `.cursor/automations/benny/`, for example to `.cursor/benny/feature-map.md`, and set `control.feature_map_path` to the copy.",
            "replace": "Copy this file outside `.specify/pstack/automations/benny/`, for example to `.specify/pstack/benny/feature-map.md`, and set `control.feature_map_path` to the copy.",
            "reason": "user-owned copies live outside the pack",
        }
    ],
    "pstack/automations/benny/skills/reproduce-and-fix-issues/references/control-adapter.md": [
        {
            "find": "Copy and fill [`feature-map.example.md`](./feature-map.example.md) outside `.cursor/automations/benny/` instead of editing the copied example.",
            "replace": "Copy and fill [`feature-map.example.md`](./feature-map.example.md) outside `.specify/pstack/automations/benny/` instead of editing the copied example.",
            "reason": "user-owned copies live outside the pack",
        }
    ],
    "pstack/automations/benny/templates/configuration.example.yaml": [
        {
            "find": "  map_path: \".cursor/benny/routing.md\"",
            "replace": "  map_path: \".specify/pstack/benny/routing.md\"",
            "reason": "benny user configuration is project-owned",
        },
        {
            "find": "  feature_map_path: \".cursor/benny/feature-map.md\"",
            "replace": "  feature_map_path: \".specify/pstack/benny/feature-map.md\"",
            "reason": "benny user configuration is project-owned",
        },
        {
            "find": "  prefer_cursor_actions: true",
            "replace": "  prefer_host_actions: true",
            "reason": "the key names the host's configured actions, not a Cursor-specific surface",
        },
    ],
    "pstack/automations/benny/templates/triage-automation-prompt.md": [
        {
            "find": "Read and follow `.cursor/automations/benny/skills/triage-issue-reports/SKILL.md` for this run.",
            "replace": "Read and follow `.specify/pstack/automations/benny/skills/triage-issue-reports/SKILL.md` for this run.",
            "reason": "the operational files are in the project-owned pack path",
        },
        {
            "find": "> Source material for the copied setup workflow. Paraphrase this intent into a built-in `automate` draft after `automate` confirms that the copied pack is committed in the repository where the automation will run.",
            "replace": "> Source material for the copied setup workflow. Turn this intent into a job request for the supplied scheduler only after proving the pack is committed in the repository and revision the job will run.",
            "reason": "job creation uses the supplied native scheduler rather than a nonexistent built-in",
        },
    ],
    "pstack/automations/benny/templates/reproduce-automation-prompt.md": [
        {
            "find": "Read and follow `.cursor/automations/benny/skills/reproduce-and-fix-issues/SKILL.md` for this run.",
            "replace": "Read and follow `.specify/pstack/automations/benny/skills/reproduce-and-fix-issues/SKILL.md` for this run.",
            "reason": "the operational files are in the project-owned pack path",
        },
        {
            "find": "> Source material for the copied setup workflow. Paraphrase this intent into a built-in `automate` draft after `automate` confirms that the copied pack is committed in the repository where the automation will run.",
            "replace": "> Source material for the copied setup workflow. Turn this intent into a job request for the supplied scheduler only after proving the pack is committed in the repository and revision the job will run.",
            "reason": "job creation uses the supplied native scheduler rather than a nonexistent built-in",
        },
    ],
    "pstack/automations/benny/README.md": [
        {
            "find": "benny gives you two cursor automations for slack issue reports.",
            "replace": "benny gives you two scheduled agents for slack issue reports, on a host that provides scheduling.",
            "reason": "the runtime is the host's scheduler where one exists",
        },
        {
            "find": "1. point cursor at [`FOR_AGENTS.md`](./FOR_AGENTS.md) and name the target repository.",
            "replace": "1. point the host agent at [`FOR_AGENTS.md`](./FOR_AGENTS.md) and name the target repository.",
            "reason": "the host agent is what reads the pack entry point",
        },
        {
            "find": "2. let setup merge this whole directory into the target at `.cursor/automations/benny/`.",
            "replace": "2. let setup merge this whole directory into the target at `.specify/pstack/automations/benny/`.",
            "reason": "the pack installs into a project-owned path",
        },
        {
            "find": "3. let setup enable pstack in the target repository's `.cursor/settings.json` for shared dependencies:",
            "replace": "3. let setup install the pstack spec-kit extension in the target repository (`specify extension add pstack`) for shared dependencies.",
            "reason": "activation is the installed Spec Kit extension",
        },
        {
            "find": "4. keep user-owned configuration outside the copied pack, for example in `.cursor/benny/`.",
            "replace": "4. keep user-owned configuration outside the copied pack, for example in `.specify/pstack/benny/`.",
            "reason": "user-owned data stays outside the copied pack",
        },
        {
            "find": "5. commit `.cursor/settings.json`, `.cursor/automations/benny/`, and any secret-free configuration before enabling either automation.",
            "replace": "5. commit `.specify/pstack/automations/benny/` and any secret-free configuration before enabling either job.",
            "reason": "the committed artifacts are the pack and its config",
        },
        {
            "find": "6. review each new automation draft or update existing automations in their editors. then send a harmless test report and verify every source-channel post stays in the original thread.",
            "replace": "6. review each new scheduler job request or update the existing jobs through the supplied scheduler. then use its run-once operation with a harmless test report and verify every source-channel post stays in the original thread.",
            "reason": "job review and canary execution use the supplied scheduler rather than an editor",
        },
    ],
    "pstack/docs/guide/01-setup.md": [
        {
            "find": "In this page you install the plugin, pick which models pstack uses, and run your first task.",
            "replace": "In this page you install the extension, pick which models pstack uses, and run your first task.",
            "reason": "pstack installs through the native Spec Kit extension command",
        },
        {
            "find": "## Install the plugin",
            "replace": "## Install the extension",
            "reason": "pstack installs as a Spec Kit extension",
        },
        {
            "find": "In a Cursor chat, run:",
            "replace": "In a terminal at the project root, run:",
            "reason": "installation uses the native Spec Kit CLI",
        },
        {
            "find": "```text\n/add-plugin pstack\n```",
            "replace": "```bash\nspecify extension add pstack\n```",
            "reason": "installation uses the native Spec Kit CLI instead of a Cursor command",
        },
        {
            "find": "Cursor confirms the plugin is installed.",
            "replace": "Confirm the extension with `specify extension list`.",
            "reason": "installation is a Spec Kit extension install",
        },
        {
            "find": "You only override what you care about. A role with no line in the rule keeps the skill's default. To restore a default later, delete that role's line, or just run `/setup-pstack` again.",
            "replace": "Every one of the 17 roles must have a non-empty selector list: `feature, refactoring`; `bug-fix`; `perf-issue`; `hillclimb`; `judgment and prose`; `hardest tasks`; `how explorer`; `how explainer`; `why investigators`; `why synthesizer`; `reflect tooling`; `reflect judgment, divergent, synthesizer`; `arena runners`; `arena cross-judge pool`; `swarm workers`; `architect runners`; and `interrogate reviewers`. A missing or empty role is an error, never a request for a hidden default. Most panel entries spawn one worker each; `arena cross-judge pool` selects exactly one judge from a different model family. To inherit the current model, set `inherit-parent` or `auto` explicitly. Run `/setup-pstack` again to change the map.",
            "reason": "the native role map is strict and has no per-skill fallback defaults",
        },
        {
            "find": "After setup, start a new chat. The model rule applies to new sessions.",
            "replace": "Every dispatch reads the saved role map, so changes apply without starting a new chat.",
            "reason": "the project role map is resolved for each native dispatch",
        },
        {
            "find": "Watch the todo list. Its first items are the matched playbook's steps copied in, the Feature playbook for this prompt. If `/poteto-mode` skips a step, the step stays in the list with `skip: <reason>`, so you can see what it chose not to do.",
            "replace": "Watch the ordered checklist. Its first items are the matched Feature playbook steps. If `/poteto-mode` skips one, it stays in the checklist with `skip: <reason>`.",
            "reason": "the visible contract is an ordered checklist, not a host-specific todo device",
        },
    ],
    "pstack/docs/guide/05-build-and-clean.md": [
        {
            "find": "The [Opening a PR playbook](../../skills/poteto-mode/playbooks/opening-a-pr.md) runs `/deslop` on the diff before each commit",
            "replace": "The [Opening a PR playbook](../../skills/poteto-mode/playbooks/opening-a-pr.md) applies the packaged deslop reference to the diff before each commit",
            "reason": "deslop is a packaged reference, not a registered command",
        },
        {
            "find": "`/deslop` ships in the `cursor-team-kit` plugin, not in pstack.",
            "replace": "The deslop reference ships inside this extension, at `.specify/extensions/pstack/resources/dependencies/deslop.md`.",
            "reason": "the dependency is packaged with the extension instead of a separate Cursor plugin",
        },
        {
            "find": "[`typescript-best-practices`](../../skills/typescript-best-practices/SKILL.md) has no slash command in your workflow. It loads whenever the agent touches a `.ts` or `.tsx` file and turns the type-system principles into concrete rules: discriminated unions, `unknown` at boundaries, exhaustive variants, schema-derived types.",
            "replace": "[`typescript-best-practices`](../../skills/typescript-best-practices/SKILL.md) preserves its `.ts`/`.tsx` path metadata for hosts that honor it. Hosts are not assumed to do so: Poteto mode explicitly loads the packaged `type-system-discipline` principle and then this skill before reading or editing TypeScript.",
            "reason": "the guide states the metadata caveat and the explicit TypeScript trigger",
        },
        {
            "find": "The division of labor is worth keeping straight. `/deslop` cleans slop out of the code, `/unslop` cleans it out of prose, and `/no-comments` hands the comments to a reviewer who didn't write them.",
            "replace": "The division of labor is worth keeping straight. The packaged deslop reference cleans slop out of code, `/unslop` cleans prose, and `/no-comments` hands comments to a reviewer who did not write them.",
            "reason": "deslop is a packaged reference, not a registered command",
        },
    ],
    "pstack/docs/guide/README.md": [
        {
            "find": "Install the plugin and pick your models.",
            "replace": "Install the Spec Kit extension and pick your models.",
            "reason": "the guide describes the native Spec Kit package",
        },
    ],
    "pstack/docs/guide/07-overnight.md": [
        {
            "find": "- `/loop` is Cursor's built-in wake mechanism, not a pstack skill. The [Autonomous run playbook](../../skills/poteto-mode/playbooks/autonomous-run.md) uses it to re-check the finish condition on events or a heartbeat.",
            "replace": "- The wake mechanism is whatever the host provides: `pstack-native.py capability-report` reports it. The [Autonomous run playbook](../../skills/poteto-mode/playbooks/autonomous-run.md) re-checks the finish condition on events or a heartbeat where a supervised loop exists, and one pass per turn where it does not.",
            "reason": "the durable wakeup is a checked host capability, not a Cursor built-in command",
        },
        {
            "find": "Give `/loop` a predicate that can pass or fail.",
            "replace": "Give the run a predicate that can pass or fail.",
            "reason": "the predicate belongs to the run, not a specific host command",
        },
    ],
    "pstack/docs/guide/09-make-it-yours.md": [
        {
            "find": "It drafts `.cursor/skills/<your-name>-mode/SKILL.md` through Cursor's built-in `create-skill` flow,",
            "replace": "It drafts `<your-name>-mode/SKILL.md` into a project skill directory your host discovers (`skills_dirs` from `pstack-native.py paths`) through the packaged create-skill guide's flow,",
            "reason": "project skills are project-owned and the authoring guide ships with the extension",
        },
        {
            "find": "which routes through Cursor's built-in `create-skill`,",
            "replace": "which routes through the packaged create-skill guide,",
            "reason": "the authoring guide ships with the extension",
        },
    ],
    "pstack/docs/guide/10-recipes-and-pitfalls.md": [
        {
            "find": "- **A vague finish condition.** \"make it better\" gives `/loop` nothing to check.",
            "replace": "- **A vague finish condition.** \"make it better\" gives a long run nothing to check.",
            "reason": "the finish condition belongs to the run, not a host command",
        },
    ],
}

# Full-file replacements. A source file listed here is written from
# tools/overrides/<source path> instead of the transformed upstream bytes,
# because the host contract changes its structure rather than a phrase.
OVERRIDE_REASONS: dict[str, str] = {
    "pstack/skills/poteto-mode/SKILL.md": "mode entry, dispatch contract, and model defaults are host-native",
    "pstack/skills/setup-pstack/SKILL.md": "writes the project role map through the runtime helper, with an explicit legacy migration",
    "pstack/agents/poteto-agent.md": "the agent contract is read as a resource and mounted from the role map",
    "pstack/skills/make-bot-ui/SKILL.md": "webhook routine, secret request, and wake handling are gated external capabilities",
    "pstack/automations/benny/skills/setup-benny/SKILL.md": "scheduler creation and update use a supplied native runner instead of Cursor automation",
    "pstack/automations/benny/FOR_AGENTS.md": "the dormant pack activates through Spec Kit and hands jobs to a supplied native scheduler",
}

# Companion files from the same pinned commit, outside the upstream pstack tree.
COMPANION_FILES: dict[str, tuple[str, str, str]] = {
    "cursor-team-kit/LICENSE": (
        "resources/dependencies/LICENSE",
        "asset",
        "MIT license text for the packaged dependency references",
    ),
    "cursor-team-kit/skills/control-cli/SKILL.md": (
        "resources/dependencies/control-cli.md",
        "reference",
        "control reference for CLIs and TUIs, packaged because pstack routes to it",
    ),
    "cursor-team-kit/skills/control-ui/SKILL.md": (
        "resources/dependencies/control-ui.md",
        "reference",
        "control reference for browser, Electron, and web UIs, packaged because pstack routes to it",
    ),
    "cursor-team-kit/skills/deslop/SKILL.md": (
        "resources/dependencies/deslop.md",
        "reference",
        "pre-commit deslop checklist, packaged because every playbook routes to it",
    ),
}


# Entries added after the initial table. Kept as explicit extends so a later
# addition can never shadow an existing entry for the same file.
FILE_EDITS["pstack/docs/guide/07-overnight.md"].append(
    {
        "find": "/loop until done. if you're truly stuck after a few hours, stop and write up why.",
        "replace": "run until it is done. if you're truly stuck after a few hours, stop and write up why.",
        "reason": "the overnight instruction no longer names a Cursor command",
    }
)

FILE_EDITS["pstack/docs/guide/10-recipes-and-pitfalls.md"].append(
    {
        "find": "with pinned cards reading /how, /tdd, and /loop above the counter.",
        "replace": "with pinned cards reading /how, /tdd, and the run instruction above the counter.",
        "reason": "image alt text no longer names a Cursor command",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/playbooks/shipping.md"].append(
    {
        "find": "One subagent per PR, not batched, each a Cursor cloud agent, each exercising the real surface (`control-ui` or `control-cli` from `cursor-team-kit` as the change demands) against parent versus head.",
        "replace": "One subagent per PR, not batched, each an isolated local worker, each exercising the real surface (the packaged `control-ui` or `control-cli` reference as the change demands) against parent versus head.",
        "reason": "cloud workers map to isolated local workers and the dependency ships in the extension",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/playbooks/bug-fix.md"].append(
    {
        "find": "using your configured bug-fix model (default `grok-4.6-fast-xhigh`)",
        "replace": "on role `bug-fix` from the project role map (`pstack-native.py role-plan --role \"bug-fix\"`); omit the model when the leg inherits the current one",
        "reason": "the delegate model comes from the project role map, not a vendor default",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/playbooks/feature.md"].append(
    {
        "find": "using your configured feature model (default `grok-4.6-fast-xhigh`)",
        "replace": "on role `feature, refactoring` from the project role map (`pstack-native.py role-plan --role \"feature, refactoring\"`); omit the model when the leg inherits the current one",
        "reason": "the delegate model comes from the project role map, not a vendor default",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/playbooks/refactoring.md"].append(
    {
        "find": "using your configured refactoring model (default `grok-4.6-fast-xhigh`)",
        "replace": "on role `feature, refactoring` from the project role map (`pstack-native.py role-plan --role \"feature, refactoring\"`); omit the model when the leg inherits the current one",
        "reason": "the delegate model comes from the project role map, not a vendor default",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/playbooks/perf-issue.md"].append(
    {
        "find": "using your configured perf-issue model (default `grok-4.6-fast-xhigh`)",
        "replace": "on role `perf-issue` from the project role map (`pstack-native.py role-plan --role \"perf-issue\"`); omit the model when the leg inherits the current one",
        "reason": "the delegate model comes from the project role map, not a vendor default",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/playbooks/hillclimb.md"].append(
    {
        "find": "using your configured hillclimb model (default `grok-4.6-fast-xhigh`)",
        "replace": "on role `hillclimb` from the project role map (`pstack-native.py role-plan --role \"hillclimb\"`); omit the model when the leg inherits the current one",
        "reason": "the delegate model comes from the project role map, not a vendor default",
    }
)

FILE_EDITS["pstack/skills/architect/SKILL.md"].append(
    {
        "find": "Use your configured architect runners (defaults `claude-fable-5-1-thinking-max`, `gpt-5.6-sol-max`, `grok-4.6-fast-xhigh`, `claude-opus-5-thinking-xhigh`).",
        "replace": "Resolve role `architect runners` from the project role map (`pstack-native.py role-plan --role \"architect runners\"`), one runner per configured entry, duplicates preserved. An empty role is a setup error, not a reason to pick a model yourself.",
        "reason": "runner models come from the project role map, not vendor defaults",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/playbooks/babysit.md"].append(
    {
        "find": "On GitHub, status comes from `scripts/watch-pr/watch-pr`.",
        "replace": "On GitHub, status comes from `.specify/extensions/pstack/resources/skills/poteto-mode/scripts/watch-pr/watch-pr`.",
        "reason": "the watcher executable is invoked from its installed extension path",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/playbooks/shipping.md"].append(
    {
        "find": "With GitHub, use `scripts/watch-pr/watch-pr --queued-stack --stack-prs <bottom>`",
        "replace": "With GitHub, use `.specify/extensions/pstack/resources/skills/poteto-mode/scripts/watch-pr/watch-pr --queued-stack --stack-prs <bottom>`",
        "reason": "the watcher executable is invoked from its installed extension path",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/playbooks/orchestrate.md"].append(
    {
        "find": "Use `bun scripts/orch/orch.ts` for bookkeeping",
        "replace": "Use `bun .specify/extensions/pstack/resources/skills/poteto-mode/scripts/orch/orch.ts` for bookkeeping",
        "reason": "the orchestration executable is invoked from its installed extension path",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/playbooks/worktree-cleanup.md"].append(
    {
        "find": "then run `scripts/worktree-audit.sh`",
        "replace": "then run `.specify/extensions/pstack/resources/skills/poteto-mode/scripts/worktree-audit.sh`",
        "reason": "the audit executable is invoked from its installed extension path",
    }
)

FILE_EDITS["pstack/skills/show-me-your-work/SKILL.md"].append(
    {
        "find": "Use the helper `scripts/log.sh <logfile> <phase> <decision> <why> <evidence> <result>`.",
        "replace": "Use the helper `.specify/extensions/pstack/resources/skills/show-me-your-work/scripts/log.sh <logfile> <phase> <decision> <why> <evidence> <result>`.",
        "reason": "the decision-log helper is invoked from its installed extension path",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/playbooks/opening-a-pr.md"].append(
    {
        "find": "A subagent that opens a PR runs `interrogate`, `/deslop`, and `/no-comments`.",
        "replace": "A subagent that opens a PR runs the packaged `interrogate` skill, the deslop reference at `.specify/extensions/pstack/resources/dependencies/deslop.md`, and `/no-comments`.",
        "reason": "the active playbook names packaged resources instead of an unregistered deslop command",
    }
)

FILE_EDITS["pstack/docs/guide/01-setup.md"].append(
    {
        "find": "You might be wondering what happens if you use Auto. Set a role to `inherit-parent` or `auto` and pstack omits the subagent `model` field, so the subagent inherits your parent chat model. Both values mean the same thing, and neither is a model slug. For a panel role the value is a list, and one subagent runs per entry, so the list length sets the panel size. Setup also configures `swarm workers`, the default model for every `/swarm` worker unless a race names a model for each arm.",
        "replace": "You might be wondering what happens if you use Auto. Set a role to `inherit-parent` or `auto` and pstack omits the subagent `model` field, so the subagent inherits your parent chat model. Both values mean the same thing, and neither is a model slug. For most panel roles, one subagent runs per configured entry. `arena cross-judge pool` is the exception: the arena selects exactly one configured judge from a different model family. Setup also configures `swarm workers`, the default model for every `/swarm` worker; a model race may override it per arm, and only with a concrete model already in `pool`.",
        "reason": "the setup guide states the one-judge cross-family arena contract",
    }
)

FILE_EDITS["pstack/docs/guide/05-build-and-clean.md"].append(
    {
        "find": "## Let the TypeScript rules load themselves",
        "replace": "## Load the TypeScript rules reliably",
        "reason": "path metadata is advisory, so the active mode also has an explicit trigger",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/playbooks/opening-a-pr.md"].append(
    {
        "find": "Cloud-agent PR tools default to draft, so set `draft: false` on every PR creation call. ",
        "replace": "",
        "reason": "the native playbook uses the selected local forge CLI and assumes no cloud-agent API",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/scripts/worktree-audit.sh"].extend(
    [
        {
            "find": "main_wt=$(git worktree list --porcelain | awk '/^worktree /{print $2; exit}')",
            "replace": "main_wt=$(git worktree list --porcelain | awk '/^worktree /{sub(/^worktree /, \"\"); print; exit}')",
            "reason": "porcelain worktree paths may contain spaces and must not be split into fields",
        },
        {
            "find": "git worktree list --porcelain | awk '/^worktree /{print $2}' | while read -r wt; do",
            "replace": "git worktree list --porcelain | awk '/^worktree /{sub(/^worktree /, \"\"); print}' | while IFS= read -r wt; do",
            "reason": "the audit preserves the complete porcelain path and disables read trimming",
        },
    ]
)

FILE_EDITS["pstack/skills/how/SKILL.md"].append(
    {
        "find": "Present the explainer's output to the user. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.",
        "replace": "Present the explainer's output to the user. For workflow dispatch, that output is the validated report's non-empty `result`, not its evidence excerpt. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.",
        "reason": "research consumers read the report result channel rather than verification metadata",
    }
)

FILE_EDITS["pstack/skills/why/SKILL.md"].append(
    {
        "find": "Take the synthesizer's output and present it to the user. You may lightly edit for clarity or add context from the conversation, but **do not rewrite the confidence language**.",
        "replace": "Take the synthesizer's output and present it to the user. For workflow dispatch, read the complete answer from the validated report's non-empty `result`, not its evidence excerpt. You may lightly edit for clarity or add context from the conversation, but **do not rewrite the confidence language**.",
        "reason": "research consumers read the report result channel rather than verification metadata",
    }
)

FILE_EDITS["pstack/skills/reflect/SKILL.md"].append(
    {
        "find": "Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval.",
        "replace": "Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. For workflow dispatch, read that output from the validated report's non-empty `result`, not its evidence excerpt.",
        "reason": "synthesis consumers read the report result channel rather than verification metadata",
    }
)

FILE_EDITS["pstack/automations/benny/README.md"].append(
    {
        "find": "```json\n{\n\t\"plugins\": {\n\t\t\"pstack\": { \"enabled\": true }\n\t}\n}\n```\n\n",
        "replace": "",
        "reason": "pstack activation is the native Spec Kit install, not an editor settings fragment",
    }
)

FILE_EDITS["pstack/skills/poteto-mode/playbooks/orchestrate.md"].append(
    {
        "find": "State reads and writes go through `scripts/orch/orch.ts` at drain points",
        "replace": "State reads and writes go through `.specify/extensions/pstack/resources/skills/poteto-mode/scripts/orch/orch.ts` at drain points",
        "reason": "every executable orch reference uses its exact installed extension path",
    }
)

FILE_EDITS["pstack/docs/guide/01-setup.md"].append(
    {
        "find": "Say yes and it writes `.cursor/skills/verify-<app>/`, a project-local skill that teaches agents to drive your app the way a user does.",
        "replace": "Say yes and it writes `verify-<app>/` into a project skill directory your host discovers, the list `skills_dirs` in the `pstack-native.py paths` report, a project-local skill that teaches agents to drive your app the way a user does.",
        "reason": "the guide points at the one host-discovered skill directory instead of a fixed project copy",
    }
)

FILE_EDITS["pstack/docs/guide/06-verify-and-ship.md"] = [
    {
        "find": "It writes `.cursor/skills/verify-<app>/`, agent-facing instructions with exact Launch, Doctor, Drive, Evidence, and Cleanup sections,",
        "replace": "It writes `verify-<app>/` into a project skill directory your host discovers (`skills_dirs` from `pstack-native.py paths`), agent-facing instructions with exact Launch, Doctor, Drive, Evidence, and Cleanup sections,",
        "reason": "the guide points at the one host-discovered skill directory instead of a fixed project copy",
    }
]

# Two edits for one file must never share a `find`, and an edit listed twice is a
# table mistake, not a second transformation. Both are enforced here so a later
# addition cannot silently shadow or duplicate an existing entry.
for _path, _edits in list(FILE_EDITS.items()):
    _deduped = []
    for _edit in _edits:
        if _edit not in _deduped:
            _deduped.append(_edit)
    _finds = [edit["find"] for edit in _deduped]
    if len(_finds) != len(set(_finds)):
        raise ValueError(f"duplicate edit anchors for {_path}")
    FILE_EDITS[_path] = _deduped
