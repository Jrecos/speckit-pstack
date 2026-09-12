---
description: "Use for 'interrogate', 'adversarial review', 'multi-model review', 'challenge this', 'stress test this code', 'find blind spots', or 'tear this apart'. Multiple LLM reviewers challenge changes from independent angles"
disable-model-invocation: true
---

# Interrogate (pstack)

Run the translated pstack skill named below. Load the shared host contract first,
because it owns role resolution, dispatch, report handling, and skill-name
resolution on this host:

`.specify/extensions/pstack/runtime/host-contract.md`

Then read the skill resource in full and follow it:

`.specify/extensions/pstack/resources/skills/interrogate/SKILL.md`

Every reference inside that resource is either relative to its own directory or an
explicit `.specify/extensions/pstack/` path, so both resolve from the project root.
The resources name pstack skills by their bare skill name (`how`, `unslop`). The
host contract maps every such name to its packaged resource path, and the extension's
own commands are registered as `speckit.pstack.<skill>`.

## Arguments

```text
$ARGUMENTS
```
