---
description: "Generate a project-local verification skill that drives your app the way a user does — any language, framework, or platform. Use for speckit.pstack.create-verification-skill, 'make a control skill for this repo', or when a project has no scripted way to prove UI/CLI/service behavior"
disable-model-invocation: true
---

# Create Verification Skill (pstack)

Run the translated pstack skill named below. Load the shared host contract first,
because it owns role resolution, dispatch, report handling, and skill-name
resolution on this host:

`.specify/extensions/pstack/runtime/host-contract.md`

Then read the skill resource in full and follow it:

`.specify/extensions/pstack/resources/skills/create-verification-skill/SKILL.md`

Every reference inside that resource is either relative to its own directory or an
explicit `.specify/extensions/pstack/` path, so both resolve from the project root.
The resources name pstack skills by their bare skill name (`how`, `unslop`). The
host contract maps every such name to its packaged resource path, and the extension's
own commands are registered as `speckit.pstack.<skill>`.

## Arguments

```text
$ARGUMENTS
```
