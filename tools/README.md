# tools/ - interactive helpers (display & control, never paper numbers)

| Item | Role | Runs where |
|---|---|---|
| regatron/ | tested G5.BT blueprint + HTTP bridge + fast-log analyzer; the control & 20 Hz input channel | bridge on the Regatron PC; Lua in Enapter blueprint |
| fuelcell_analyzer.html | interactive CSV inspection (regions, IV, dynamics, degradation) | double-click locally, drag CSVs in |
| server.py + simulate_data.py + requirements_server.txt | live WebSocket feed for the HTML tool | PC with network access to the Gateway |
| auto_plot.py / auto_plot_interactive.py | quick single-file plotters | anywhere with pandas/matplotlib |

Rule: tools display and control. Numbers for the paper come only from
src/verlustmappe/ pipelines into results/.

`run_local_gates.py` is a development helper, not part of CI. Run it from
the project environment with an external log directory, for example:

```sh
python tools/run_local_gates.py --log-dir /tmp/verlustmappe-gates
```

It runs the legacy suite, pytest, `ci_guard.py` with `BASE_REF=origin/main`,
the README check, and staged/unstaged diff checks. It records each command's
output separately and exits nonzero if any command fails. CI continues to use
its own configured workflow and `ci_guard.py`.
