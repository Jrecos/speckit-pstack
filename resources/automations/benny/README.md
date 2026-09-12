# benny

benny gives you two scheduled agents for slack issue reports, on a host that provides scheduling. one triages each report. the other reproduces confirmed bugs and may prepare a small draft fix.

the files in this directory are dormant setup and automation sources. they do not appear as slash skills.

## set it up

1. point the host agent at [`FOR_AGENTS.md`](./FOR_AGENTS.md) and name the target repository.
2. let setup merge this whole directory into the target at `.specify/pstack/automations/benny/`. it must preserve destination-only files and review conflicts instead of overwriting local edits.
3. let setup install the pstack spec-kit extension in the target repository (`specify extension add pstack`) for shared dependencies.

4. keep user-owned configuration outside the copied pack, for example in `.specify/pstack/benny/`. adapt [`configuration.example.yaml`](./templates/configuration.example.yaml) and [`feature-map.example.md`](./skills/reproduce-and-fix-issues/references/feature-map.example.md).
5. commit `.specify/pstack/automations/benny/` and any secret-free configuration before enabling either job.
6. review each new scheduler job request or update the existing jobs through the supplied scheduler. then use its run-once operation with a harmless test report and verify every source-channel post stays in the original thread.
