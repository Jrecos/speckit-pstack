---
description: "Apply when tempted to ask 'should I do X?' on reversible work. Proceed, present the result, let the human course-correct after the fact; reserve confirmation for irreversible actions"
disable-model-invocation: true
---

# Principle Never Block On The Human (pstack)

Run the translated pstack skill named below. Load the shared host contract first,
because it owns role resolution, dispatch, report handling, and skill-name
resolution on this host:

`.specify/extensions/pstack/runtime/host-contract.md`

Then read the skill resource in full and follow it:

`.specify/extensions/pstack/resources/skills/principle-never-block-on-the-human/SKILL.md`

Every reference inside that resource is either relative to its own directory or an
explicit `.specify/extensions/pstack/` path, so both resolve from the project root.
The resources name pstack skills by their bare skill name (`how`, `unslop`). The
host contract maps every such name to its packaged resource path, and the extension's
own commands are registered as `speckit.pstack.<skill>`.

## Arguments

```text
$ARGUMENTS
```
