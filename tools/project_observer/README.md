# Project observer

This optional, manually started tool shows where each plant device stands and gives a
navigational overview of the Python structure. It is isolated under `tools/`; the
simulation does not import it, and it is not part of CI or the normal workflow. Rules:
`CONTRACT.md` §12, `decisions/2026-11-18-static-project-overview-scope.md` and
`decisions/2026-11-18-observer-status-fields-and-live-view.md`.

## What it reads

- Python source via AST (structure, calls, string constants such as parameter keys).
- `plant/*.toml`: key paths, `status`, `unit`, `source`, `[open]` entries, whether a
  `value` field is present, and the word UNVERIFIED (count, line numbers and enclosing TOML
  table, no text). Values, uncertainties and other numeric contents are never emitted. Plant
  files are only read, never written.
- `START.md` restart checklist and known failures; marker lines (BACKLOG, PAUSED, MISSING,
  TODO, UNKLAR, UNVERIFIED) in `CONTRACT.md` and `START.md`.
- `topology.toml` in this folder: nodes, flows and layout of the plant diagram, each with
  its basis in `CONTRACT.md` §4 or plant file titles. It is a display aid, not project truth,
  and records whether the owner has reviewed it. Nodes of kind `unassessed` and edges with
  `assess = false` are shown faded and are deliberately not assessed.
- An optional semantics TOML (`signal` entries).

It does not execute the model or consume simulation-run or measurement values. Progress
columns and code links are static name matches: they do not prove runtime calls, data
flow, correct booking or physical relationships. Status labels are shown verbatim, as
counts, without ranking or colour grading.

## Views

- **Plant** (start page): flow diagram from PV to the FC inverter output with distinct
  line styles for DC, AC, hydrogen, process water, compressed air and auxiliary electricity
  (account B). No amounts. Clicking a station opens a card beside the diagram: what happens
  (agent draft until `descriptions_reviewed = true`), account, incoming, outgoing and
  auxiliary flows with units (derived from the diagram edges and `[units]`), basis, and a
  link to the device details. Key parameters are not filled yet.
  A toggle switches to **Energy flow**: the same diagram with value slots per station
  (in, out, η, loss, ...; defined per node in `topology.toml`) and per flow, plus accounts
  A and B side by side and C as not reported. There is no results file yet, so every slot
  shows MISSING; the observer computes nothing and never fills in example numbers.
- **Devices**: one row per plant file, in diagram order, with parameters having a value / all parameters,
  model module, test files, accounting references, layer-3 validation (empty until it
  exists), status labels, UNVERIFIED count and open items. Click a row for details.
- **Open items**: `[open]` entries and document marker lines, grouped by device.
- **Code**: modules, calls, callers, tests and semantics signals.

## Run

From the repository root, either a live view that regenerates on every reload
(nothing is written; stop with Ctrl+C):

```sh
python tools/project_observer/overview_gen.py --root . --serve
```

then open `http://127.0.0.1:8765/`; or a one-off snapshot written to the Git-ignored
`tools/project_observer/output/overview.html`:

```sh
python tools/project_observer/overview_gen.py --root .
```

The live view binds to `127.0.0.1` only. A snapshot is labelled as such and may be
outdated; the header always shows generation time, branch, commit and worktree state.
Nothing starts the observer automatically. To change the contents, edit the generator or
the semantics TOML; manual edits to generated HTML are overwritten.

The bundled `semantics_example.toml` is an unverified example, not project truth; pass it
with `--semantics tools/project_observer/semantics_example.toml` only to preview. Its
entries must not be used as evidence or model inputs.
