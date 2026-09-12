---
description: "poteto's agent style for concise, detailed responses, deliberate subagents, unslopped prose, simple code, and verified work. Use for poteto, speckit.pstack.poteto-mode, or requests to work in this style"
disable-model-invocation: true
---

# Poteto Mode (pstack)

Parse `$ARGUMENTS` before reading any pstack resource.

- For `on`, `off`, or `status`, run the matching fixed command through
  `.specify/extensions/pstack/runtime/pstack-native.py mode`. Return its result and
  stop. If the helper is absent or fails, load no resource and do not edit the
  instruction file by hand.
- For no arguments or a task, run
  `.specify/extensions/pstack/runtime/pstack-native.py mode status` first. Continue
  only when `extension.enabled` and `extension.resources_present` are both exactly
  `true`. Project-block readiness is not required for invocation-only session mode.
  Any failed check makes this command inert.

After that readiness check, read these files in order and follow the mode resource
for `$ARGUMENTS`:

1. `.specify/extensions/pstack/runtime/host-contract.md`
2. `.specify/extensions/pstack/resources/skills/poteto-mode/SKILL.md`
