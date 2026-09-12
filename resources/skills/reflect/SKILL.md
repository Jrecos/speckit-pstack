---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
disable-model-invocation: true
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

## When to invoke

Invoke when the user says "reflect" or "/speckit.pstack.reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## Process

### 1. Locate the active transcript

The parent finds its own transcript before fanning out. `.specify/extensions/pstack/runtime/pstack-native.py paths` and `capability-report` say whether this host exposes session history and where. Read only this workspace's transcripts: never search another project's store, because that crosses workspace boundaries and reads private chats from unrelated projects.

```bash
ls -t "$PSTACK_TRANSCRIPTS_DIR"/*.jsonl "$PSTACK_TRANSCRIPTS_DIR"/*/*.jsonl 2>/dev/null | head -10
```

Layouts vary by host and version: flat (`<id>.jsonl`), nested (`<id>/<id>.jsonl`), and host-specific subagent files. Read what the directory actually holds rather than assuming a layout.

For each candidate, read the first JSONL line and check that `message.content[0].text` contains the conversation's opening user prompt. Take the matching path. If no path resolves, write a tight digest of the session and pass that instead.

### 2. Spawn three reviewers in parallel

One batch, three subagent dispatches on the host's general-purpose subagent, each with its resolved role model, in agent mode rather than read-only. Reviewers need MCP access for context lookups (tickets, chat threads, observability traces referenced in the transcript), and read-only mode strips MCPs on hosts that make MCP conditional.

| Lens | `model` | Prompt template |
|---|---|---|
| Judgment | role `reflect judgment, divergent, synthesizer` | `references/judgment-reviewer.md` |
| Tooling | role `reflect tooling` | `references/tooling-reviewer.md` |
| Divergent | role `reflect judgment, divergent, synthesizer` | `references/divergent-reviewer.md` |

Resolve each role with `.specify/extensions/pstack/runtime/pstack-native.py role-plan --role "<role>"`; when the leg inherits the parent model, omit the model on native dispatch.

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in the subagent report.

### 3. Synthesize

One subagent dispatch on the host's general-purpose subagent, on role `reflect judgment, divergent, synthesizer`, in agent mode rather than read-only. The synthesizer's quality check includes spot-verifying citations, which can require MCP access, and read-only mode strips MCPs on hosts that make MCP conditional. Use `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. The synthesizer returns a structured Accepted / Rejected / Backlog list.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, or runtime check, move it from Accepted to Backlog. See the **encode-lessons-in-structure** principle skill.

### 5. Apply

Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. For workflow dispatch, read that output from the validated report's non-empty `result`, not its evidence excerpt. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent in the org. Do not auto-apply.

Backlog items file to whatever devex / backlog tracker your team uses automatically. Only the Accepted list waits for approval.

For each approved Accepted item, follow the Routing field exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): parent does directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to the packaged create-skill guide (`.specify/extensions/pstack/resources/dependencies/create-skill.md`) and run its draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): hand to `create-skill` and run its description-optimization loop.
- `new skill via create-skill: <kebab-name>`: hand creation to `create-skill`. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done. Skip this step if it doesn't.

### 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
