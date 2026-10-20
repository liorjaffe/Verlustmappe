# Fuel Cell Analyzer — Feature Roadmap

This tracks everything from your requirements list, organized into buildable phases.
Legend: ✅ already in the tool · 🔲 planned, not built yet · ⚠️ needs a data channel the tool doesn't model yet (temperature, pressure, H₂ flow, per-cell voltages, ...)

---

## Phase 0 — Foundation (built)
- ✅ Auto-detect Voltage / Current / Power columns from CSV headers
- ✅ Multi-dataset overlay (compare test runs side by side) — works for combining separate single-channel files (e.g. amps-only + volts-only + power-only) into one view
- ✅ Region marking on the time-series chart
- ✅ Per-region, per-dataset stats (mean, std dev, min, max, median, n, duration — duration shown to 0.1s for sub-2-minute regions)
- ✅ Region comparison table + CSV export
- ✅ Moving-average trend overlay
- ✅ Real datetime x-axis (handles ISO strings and epoch s/ms/µs/ns)
- ✅ Fixed: crash when combining 2-3 channel types at once ("f.rangemode" error) — caused by the range-slider being incompatible with our WebGL-accelerated lines; slider removed, pan + scroll-to-zoom + double-click-reset remain
- ✅ Fixed: re-uploading a file with the same name now replaces the old copy instead of silently duplicating it (this was very likely why old channels kept reappearing)
- ✅ Added: drag-and-drop file loading (in addition to the file picker) for loading several CSVs at once
- ✅ Added: precision-aware y-axis tick/hover formatting per channel, plus a visible zero-line, so a brief sign change (e.g. current going slightly negative at FC start-up) is never rounded away or missed visually
- 🔲 Live cursor readout of the value under the mouse while marking a region — this should already work via Plotly's built-in unified hover; flag it if it doesn't track live while you're actively dragging a selection box, and it'll get a dedicated fix
- 🔲 Explicit UI affordance for zooming into a very short (sub-second) event before marking it as a region — technically possible today via scroll-zoom + pan, but not obviously discoverable

## Phase 1 — I–V / Polarization module (next up, per your message)
- 🔲 I–V curve (Voltage vs. Current), I–P curve (Power vs. Current)
- 🔲 Current density axis (A/cm²) — needs active cell area as an input (per dataset)
- 🔲 Power density (W/cm²), specific power (W/kg) — needs stack weight input
- 🔲 Key operating points, auto-extracted: OCV, V at defined I, I at defined V, Maximum Power Point (P_max, I@MPP, V@MPP), rated/max current, rated/max power
- 🔲 dV/dI, dP/dI (local slope of the polarization curve)
- 🔲 Auto-generated "characteristic value table" (Kennwert-Tabelle) per dataset
- 🔲 Overlay multiple datasets/stacks on one I–V plot for direct comparison
- 🔲 Comparison at equal operating points (V at same I, P at same I, across datasets)

## Phase 2 — Broaden the data model (built, partially)
- ✅ New channel types: Temperature, Pressure, Flow (H₂/air) — auto-detected the same way as V/I/P, and every existing tool (regions, comparison, trend, dynamic response) works with them automatically
- ✅ Manual override: any numeric column the auto-detector can't place shows up under "Unclassified columns" in the Time Series tab, with a dropdown to assign it a type by hand
- 🔲 Humidity, per-cell voltage as their own types (per-cell voltage specifically needs Phase 7's many-columns handling, not just a new type)
- 🔲 Per-dataset metadata (Test ID, FC ID, operating hours, cell count) — active area already exists, added in Phase 1
- Note: a column literally named just "P" still resolves to Power (existing convention) — a lone-letter Pressure column needs manual reassignment

## Phase 3 — Efficiency & fuel utilization (built)
- ✅ New "Efficiency" tab: LHV/HHV-selectable H&#8322; energy basis (2.995 / 3.54 Wh/NL)
- ✅ Efficiency vs. Current plot, per dataset
- ✅ Per-region (or whole-file) totals: H&#8322; used (NL), electrical energy (Wh), average efficiency (%), specific consumption (NL/kWh) — via trapezoidal integration, validated against a closed-form constant-power/flow test case
- ✅ Works with an explicit Power channel, or falls back to V&times;I when only those exist
- ✅ CSV export
- 🔲 Efficiency vs. Temperature (needs a temperature channel present alongside flow+power in the same file to plot; the calculation itself doesn't depend on temperature)
- 🔲 g/h H&#8322; consumption (currently NL-based only; easy to add given H&#8322; density if wanted)

## Phase 4 — Dynamic behavior (built)
- ✅ New "Dynamic Response" tab, reusing your marked regions
- ✅ Baseline (auto, from just before each region), extreme value/time within the region
- ✅ Rise/fall time (10%&ndash;90% transition)
- ✅ **Recovery time**: time from the extreme back to within a configurable tolerance % of baseline — the "how long until full power/current/voltage again" metric; clearly flags "did not recover in region" instead of guessing
- ✅ CSV export of the full dynamic-response table
- 🔲 Settling time / overshoot-undershoot beyond baseline after recovery, as separate metrics
- 🔲 Ramp rate (W/s, A/s, V/s) as a standalone metric (currently implicit in rise/fall time)
- 🔲 Behavior under load steps (fast vs. slow load changes) as a dedicated view

## Phase 5 — Start/Stop analysis (built)
- ✅ New "Start/Stop" tab: cycles auto-detected from Current (or Power) crossing a configurable % threshold
- ✅ Per cycle: start/stop time, duration, peak value, start-up time (10&ndash;90% rise), shutdown time (fall back to post-cycle baseline)
- ✅ Handles cycles close together correctly (baseline window clipped at the next cycle's start, validated by test)
- ✅ CSV export
- 🔲 Start-up/shutdown energy (Wh) — straightforward to add now that Efficiency's integration helper exists, just not wired in yet
- 🔲 Voltage/current/power trajectory *shape* during start/stop as its own mini-plot (currently table-only; the Time Series tab already shows the shape if you zoom to a cycle)

## Phase 6 — Temperature / Pressure / Gas cross-plots (built, partially)
- ✅ New "Cross-Plot" tab: any channel type vs. any channel type (Voltage, Current, Power, Temperature, Pressure, Flow), overlaid across all loaded datasets, with Pearson correlation per dataset
- ✅ Validated: pairs correctly, correlation math checked against known perfectly-correlated and anti-correlated synthetic series
- 🔲 Efficiency / H&#8322; consumption as pickable cross-plot axes (currently raw channels only — Efficiency tab already has its own vs.-Current plot; wiring it into this generic tool is a small follow-up)
- 🔲 Purge event detection & voltage-recovery-after-purge (a specialized case of the Stability tab's anomaly detection — could reuse that machinery once purge timing is identifiable in the data, e.g. a Purge-state channel or a load channel pattern)

## Phase 7 — Cell/stack balance (built)
- ✅ Auto-detects columns named "cell_1", "cell 2", "Zelle_3", etc. as per-cell voltage channels, separate from the main Voltage channel
- ✅ New "Cell Balance" tab: bar chart of each cell's average voltage (spot a weak cell at a glance), spread-over-time plot, summary table (overall min/max with which cell & when, average spread, worst cell)
- ✅ Validated with a synthetic 4-cell stack including one deliberately weak cell — correctly identified
- ✅ CSV export
- 🔲 Histogram/distribution view, coefficient of variation across cells, per-cell degradation over time (natural Phase-8 crossover)

## Phase 8 — Degradation / long-term operation (built)
- ✅ New "Degradation" tab: each dataset = one test session, with an editable "operating hours" field per dataset
- ✅ Tracks **voltage at a fixed current** across sessions (load-independent, the standard DOE/NREL-style degradation metric) — reuses the same interpolation as the I&ndash;V tab
- ✅ Scatter + linear-regression trend line, degradation rate reported in mV/h and %/h
- ✅ % change vs. first session per row
- ✅ CSV export
- Validated: linear regression checked against hand-computed slope/intercept; a synthetic 4-session degrading-voltage scenario reproduced the exact expected mV/h rate
- 🔲 Lifetime-to-X%-degradation projection, beginning-of-life vs. end-of-life side-by-side comparison

### Bugs found and fixed while building Phase 8
- The Cell Balance tab's button was never actually wired to a click handler — clicking it did nothing. Fixed.
- The Cross-Plot tab could crash if its dropdowns held an unexpected value; added a defensive check against the known channel-type list.

## Phase 9 — Load profile analysis (built)
- ✅ New "Load Profile" tab: rated power + min. stable power inputs
- ✅ Time-weighted bins (0&ndash;10%, 10&ndash;25%, 25&ndash;50%, 50&ndash;75%, 75&ndash;100%, &gt;100% of rated), shown as a bar chart
- ✅ Load factor (avg/peak), capacity factor (avg/rated), time above rated, time below min. stable
- ✅ Load-change count (configurable % threshold)
- ✅ CSV export
- Validated against a known 5-segment synthetic load profile; average load is time-weighted (energy/duration) to stay consistent with the bin methodology, same as Efficiency's approach

## Phase 10 — Stability & anomaly detection (built)
- ✅ New "Stability" tab: std dev, coefficient of variation (%), peak-to-peak, RMS per channel
- ✅ Steady-state detection: rolling-window std dev vs. overall std dev; reports time-to-first-steady and % of time steady
- ✅ Anomaly detection: flags consecutive-sample jumps beyond a configurable &sigma; threshold (of the point-to-point change distribution, not the raw signal) &mdash; catches sudden drops/spikes on any channel, not just current
- ✅ Both exportable as separate CSVs
- Validated with synthetic tests: a spike injection was caught exactly (in/out edges), and a signal that goes from noisy to quiet was correctly timed to when it settles
- 🔲 Deviation-from-reference-polarization-curve flagging (needs a saved reference curve to compare against — natural follow-up once you've got a "golden" I&ndash;V curve to store)

## Phase 11 — Multi-cell / multi-test comparison dashboard (built, core)
- ✅ New "Summary" tab: one row per loaded dataset (FC1 vs. FC2 vs. any others, side by side), pulling OCV, P<sub>max</sub>, avg. efficiency, cycle count, voltage CV%, cell spread, and operating hours from every other tab's already-tested logic
- ✅ Missing prerequisites show as a dash rather than a guessed/defaulted number
- ✅ CSV export
- Validated: a fully-populated dataset and a bare (voltage-only) dataset both produced correct, non-crashing rows
- 🔲 Relative difference (%) columns between two selected datasets
- 🔲 "Same operating point" comparison baked into this table (currently a separate step via the I&ndash;V tab's Query tool)

---

### Open questions before Phase 1 can be fully useful
1. Do your CSV exports include a **cell/active area** value anywhere (for A/cm²), or is that a constant you'd type in per dataset?
2. Are your I–V/polarization measurements **swept in one file** (current ramped step by step) or do you need me to derive them from **steady-state windows** you mark on a longer log (i.e. reuse the region-marking tool we already have)?

### Open questions before Phases 2–8 can start
3. Which of these does your equipment actually log today: temperature, pressure, H₂/air flow, humidity, individual cell voltages, operating-hours/Test-ID metadata? (No wrong answer if it's "just V/I/P for now" — tells me what to build first.)

## Phase 12 — Live data feed (built, not new to your original list, added on request)
- ✅ WebSocket client built into the tool, compatible with a companion FastAPI server (`server.py`, `simulate_data.py`, `requirements.txt` — separate download)
- ✅ Not active by default: hidden panel, requires clicking "+ Live data feed" then "Connect" — nothing connects automatically
- ✅ Each device becomes its own dataset, built with the *exact same shape* as a CSV upload, so every existing tab (Time Series, I–V, Dynamic Response, Efficiency, Start/Stop, Load Profile, Stability, Cross-Plot, Cell Balance) works on live data with no special-casing
- ✅ Backfills recent history on connect, then streams live; caps memory at 5000 points/device; batches UI refresh to at most once/second
- ✅ CSV upload and drag-and-drop remain fully independent and unaffected — both data sources can be active in the tool at the same time
- ⚠️ **Important**: the CSP on the hosted claude.ai link blocks WebSocket connections to `localhost`. Live feed only works when you run the **downloaded** HTML file directly (double-click it, or serve it from your own machine) — not through the claude.ai-hosted link. CSV upload works fine either way.
- 🔲 Reconnect-with-backoff, device enable/disable toggle wired into the UI (backend already supports it via `/api/devices/{id}/toggle`), a "recording" indicator

## Phase 13 — Auto Events: robust (median/MAD) event detection + steady segments (built)
Ported from a user-supplied Python/pandas module (same idea, reimplemented natively in JS; two real bugs found and fixed in the original Python file along the way — see `fc_event_analysis.py`, separately delivered).
- ✅ New "Auto Events" tab: pick any dataset + channel (including per-cell voltages), tune the detection config, click Analyze
- ✅ Deviation score = |value &minus; rolling median| &divide; rolling MAD (robust to the outliers it's trying to find, unlike mean/std-based methods)
- ✅ Events: merged/filtered runs above threshold, with plateau (median just before), depth, overshoot, and **settle-and-hold** recovery time (must stay within tolerance for a hold duration, not just touch it once)
- ✅ Steady segments: everything left over once events are removed, above a minimum duration, with mean/std
- ✅ **"+ Region" button** on every detected event and steady segment — promotes it straight into this tool's Region system, so it instantly feeds Dynamic Response, the Comparison table, IV steady-state mode, and Efficiency without manual dragging
- ✅ Plot with events (red) and steady segments (green) highlighted as bands
- ✅ Both tables exportable as CSV
- Validated: a clean isolated dip reproduces the same detection/recovery behavior as the Python reference almost exactly; a subtle slow-ramp case showed the algorithm is (by design) less sensitive to gradual drift than sharp transients — confirmed by inspecting the raw deviation scores, not a bug
- 🔲 Run across all channels of a dataset at once (currently one channel per analysis run, by design, to keep it fast and readable)

