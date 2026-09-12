# Set up pstack

In this page you install the extension, pick which models pstack uses, and run your first task. Setup is one command plus a short conversation.

## Install the extension

In a terminal at the project root, run:

```bash
specify extension add pstack
```

Confirm the extension with `specify extension list`.

## Pick your models

Run:

```text
/speckit.pstack.setup-pstack
```

[`/speckit.pstack.setup-pstack`](../../skills/setup-pstack/SKILL.md) detects the models you have access to, shows you each role (code delegates, judgment, the review panels), and asks what you want. Answer the questions. It writes `.specify/extensions/pstack/pstack-models-config.yml`, a small rule every pstack skill reads.

Every one of the 17 roles must have a non-empty selector list: `feature, refactoring`; `bug-fix`; `perf-issue`; `hillclimb`; `judgment and prose`; `hardest tasks`; `how explorer`; `how explainer`; `why investigators`; `why synthesizer`; `reflect tooling`; `reflect judgment, divergent, synthesizer`; `arena runners`; `arena cross-judge pool`; `swarm workers`; `architect runners`; and `interrogate reviewers`. A missing or empty role is an error, never a request for a hidden default. Most panel entries spawn one worker each; `arena cross-judge pool` selects exactly one judge from a different model family. To inherit the current model, set `inherit-parent` or `auto` explicitly. Run `/speckit.pstack.setup-pstack` again to change the map.

You might be wondering what happens if you use Auto. Set a role to `inherit-parent` or `auto` and pstack omits the subagent `model` field, so the subagent inherits your parent chat model. Both values mean the same thing, and neither is a model slug. For most panel roles, one subagent runs per configured entry. `arena cross-judge pool` is the exception: the arena selects exactly one configured judge from a different model family. Setup also configures `swarm workers`, the default model for every `/speckit.pstack.swarm` worker; a model race may override it per arm, and only with a concrete model already in `pool`.

## Accept the verification offer, or don't

At the end of setup, `/speckit.pstack.setup-pstack` looks for a way to prove app behavior in your project, either a `verify-*` skill or an existing harness. If it finds neither, it offers once to generate one with [`/speckit.pstack.create-verification-skill`](../../skills/create-verification-skill/SKILL.md).

Say yes and it writes `verify-<app>/` into a project skill directory your host discovers, the list `skills_dirs` in the `.specify/extensions/pstack/runtime/pstack-native.py paths` report, a project-local skill that teaches agents to drive your app the way a user does. It proves the skill works once before handing it over. Say no and setup moves on. You can run `/speckit.pstack.create-verification-skill` yourself any time. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers when it earns its place.

Every dispatch reads the saved role map, so changes apply without starting a new chat.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
/speckit.pstack.poteto-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the ordered checklist. Its first items are the matched Feature playbook steps. If `/speckit.pstack.poteto-mode` skips one, it stays in the checklist with `skip: <reason>`.

From here you can type normal follow-ups. `/speckit.pstack.poteto-mode` is sticky. It stays on for the conversation until you opt out by saying so.

Next: [Route work through `/speckit.pstack.poteto-mode`](./02-poteto-mode.md).
