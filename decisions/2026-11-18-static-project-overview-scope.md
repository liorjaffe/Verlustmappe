# 2026-11-18 - Static project observer

The owner approved keeping the optional static observer in the same repository for access,
isolated under `tools/project_observer/`. The copied generator and semantics example remain
separate from `src/verlustmappe/`; the simulation does not import them, and they are not part
of CI or the normal workflow.

The observer is manually invoked for orientation. It reads code structure, plant TOML key
paths, selected status-marker lines, and an optional semantics file. It does not consume
simulation-run or measurement values, execute or change the plant model, alter parameters or
test expectations, calculate plant behavior, or validate physical flows, balances or results.
Static matches are navigation hints, not proof of runtime calls, data flow or physical
relationships. Uncertain or missing meaning remains open.

The bundled `semantics_example.toml` is illustrative and unverified, not project truth. After
the owner clarified that an external output path made the observer inconvenient, the approved
output location became `tools/project_observer/output/overview.html`. That exact output folder
is Git-ignored: the generated page remains accessible alongside the project without appearing
as a source change. The generator restricts output to this folder.

This approval is limited to the observer and example under `tools/project_observer/`, plus the
Git-ignored local output. Edit the generator or semantics input and regenerate; generated HTML
is not an editable source of truth. Runtime-data analysis, calculations, validation, CI
integration, changes to plant parameters or expected tests, and other expansions require a
separate owner decision.
