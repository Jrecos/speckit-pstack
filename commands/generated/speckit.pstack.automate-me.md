---
description: "Use for 'automate me', 'create/update/refresh my -mode skill', 'turn/capture my preferences or working style into a skill', or wanting agents to follow how the user works. Drafts or revises a personal -mode skill via create-skill + unslop, optionally pulling fresh evidence from recent transcripts"
disable-model-invocation: true
---

# Automate Me (pstack)

Run the translated pstack skill named below. Load the shared host contract first,
because it owns role resolution, dispatch, report handling, and skill-name
resolution on this host:

`.specify/extensions/pstack/runtime/host-contract.md`

Then read the skill resource in full and follow it:

`.specify/extensions/pstack/resources/skills/automate-me/SKILL.md`

Every reference inside that resource is either relative to its own directory or an
explicit `.specify/extensions/pstack/` path, so both resolve from the project root.
The resources name pstack skills by their bare skill name (`how`, `unslop`). The
host contract maps every such name to its packaged resource path, and the extension's
own commands are registered as `speckit.pstack.<skill>`.

## Arguments

```text
$ARGUMENTS
```
