---
description: "Check project-mode readiness before a core phase. Load it only when ready."
---

# Pstack Mode Refresh

This command is the mandatory pstack hook before the Spec Kit `specify`, `plan`,
`tasks`, and `implement` phases while the extension is enabled. It is a no-op when
project mode is off. It never dispatches another command or runs the phase itself.

## Steps

1. Check session state before any file or helper read. If this session already
   processed a natural-language Poteto opt-out or
   the `speckit.pstack.poteto-mode` command with `off`, say nothing and return to the
   phase. A ready
   project block must not reactivate an opted-out session.

2. Run the fixed readiness check.

   ```bash
   python3 .specify/extensions/pstack/runtime/pstack-native.py mode status --session unknown
   ```

   If the helper is absent, fails, or returns malformed JSON, load no pstack
   resource and continue the phase. Do not improvise the mode.

3. Read `project_mode.active` and `project_mode.ready` from that JSON.

   - `active` false means project mode is off. Say nothing and continue.
   - `active` true and `ready` false means the block is inert. Report the reason
     from the readiness result, load no mode resource, and continue.
   - `active` true and `ready` true means the mode may load.

4. On the ready branch only, read these files in order and in full.

   1. `.specify/extensions/pstack/runtime/host-contract.md`
   2. `.specify/extensions/pstack/resources/skills/poteto-mode/SKILL.md`

   Apply both for the rest of the session. Say in one line that project mode is
   active and how to opt out of this session without changing project files.

5. Continue the phase. This hook never edits `tasks.md`, the spec, or the plan.
