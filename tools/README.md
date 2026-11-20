# tools/ - interactive helpers (display & control, never paper numbers)

| Item | Role | Runs where |
|---|---|---|
| project_observer/ | optional static device-progress and code overview; manual, read-only; snapshot in Git-ignored `output/` or live view on 127.0.0.1 | local, on demand |
| list_open_uncertainties.py | manual read-only list of `uncertainty_open` items and unreviewed u = 0.0 parameters (CONTRACT §8) | local, on demand |
| regatron/ | tested G5.BT blueprint + HTTP bridge + fast-log analyzer; the control & 20 Hz input channel | bridge on the Regatron PC; Lua in Enapter blueprint |
| fuelcell_analyzer.html | interactive CSV inspection (regions, IV, dynamics, degradation) | double-click locally, drag CSVs in |
| server.py + simulate_data.py + requirements_server.txt | live WebSocket feed for the HTML tool | PC with network access to the Gateway |
| auto_plot.py / auto_plot_interactive.py | quick single-file plotters | anywhere with pandas/matplotlib |

Rule: tools display and control. Numbers for the paper come only from
src/verlustmappe/ pipelines into results/.

`project_observer/` is not imported by the simulation and is not part of CI or the
normal workflow. Run it explicitly; generated HTML stays in its Git-ignored
`project_observer/output/` folder for convenient local access. Its bundled
`semantics_example.toml` is unverified illustration only; static name matches are
navigation hints, not proof of calls or physical flows. See `project_observer/README.md`.

`run_local_gates.py` runs `tests/run_all.py`, pytest and `git diff --check` and keeps each command's output
in an external log directory; it exits nonzero if any check fails:

```sh
python tools/run_local_gates.py --log-dir /tmp/verlustmappe-gates
```
