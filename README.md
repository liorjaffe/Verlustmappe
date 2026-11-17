# Verlustmappe

Energy ledger of a market-standard pilot plant: PV → electrolyser → H₂ storage → fuel cell
→ AC. For each chosen static load point it should show where every kWh goes, which loss has
which cause, and which values are still missing.

**Entry:** [AGENTS.md](AGENTS.md) (map and rules) → [START.md](START.md) (current state) →
[CONTRACT.md](CONTRACT.md) (what applies).

| Folder | Content |
|---|---|
| `plant/` | one file per device: values, status, sources, open questions |
| `src/verlustmappe/devices/` | device models, one file per device |
| `src/verlustmappe/hydrogen/` | hydrogen amounts, real gas, tank temperature |
| `src/verlustmappe/physics/` | constants, unit conversions, time integration |
| `src/verlustmappe/accounting/` | status, validity, item list, static case |
| `src/verlustmappe/loaders/` | reading measurement data (Solis, Regatron, Enapter) |
| `data/` | measurement data |
| `tests/` | checks; hand references under `tests/reference/hand/` |
| `decisions/` | reasons |
| `tools/` | plant tools (Regatron bridge, analyzer, server, plotters) |

Tests: `python tests/run_all.py` and `python -m pytest -q` (Python ≥ 3.11, numpy, pandas,
scipy, requests).

## Hypothetical Kaeser air-energy scenario

The `devices.kaeser` module only converts dry FAD with explicit reference
conditions; registered values and source conflicts remain in `plant/kaeser.toml`.
`devices.h2_compressor` owns chart interpolation, the explicit module-addition
assumption and capacity/extrapolation guards, separately from its legacy energy
path. `scenarios.kaeser` only composes these inputs and applies the
hypothetical energy formula; it is not a device consumption model.
For the approved two-EL example, the following compares both reading bases:

```sh
PYTHONPATH=src .venv/bin/python - <<'PY'
from verlustmappe import registry
from verlustmappe.devices.kaeser import fad_to_normal_NL_min
from verlustmappe.devices.h2_compressor import AirCurve
from verlustmappe.scenarios.kaeser import KaeserScenario, calculate

nominal_air_NL_min = fad_to_normal_NL_min(
    registry.get("kaeser.q_fad_m3min"),
    inlet_pressure_abs_bar=1, inlet_temperature_K=293.15,
    normal_pressure_abs_bar=1.01325, normal_temperature_K=273.15,
)
for basis, end_h2, air_140, air_400 in (
    ("adjacent graph readings", 20, 175, 400),
    ("historical sparse anchors", 50, 280, 600),
):
    result = calculate(KaeserScenario(
        h2_flow_NL_min=1000 / 60,
        module_140=AirCurve(basis, "workbook Master C128", ((10, 150), (end_h2, air_140))),
        module_400=AirCurve(basis, "workbook Master C129", ((10, 350), (end_h2, air_400))),
        nominal_air_flow_NL_min=nominal_air_NL_min,
        reference_power_W=registry.get("kaeser.p_package_dealer_kw") * 1000,
        operating_time_s=3600,
        reference_source="dealer 11 bar power; manufacturer 10 bar delivery, conditionally converted",
        assume_module_addition=True,
    ))
    print(result)
PY
```

The returned inputs, basis and notes are part of the result; they must not be
omitted when reporting it. `AirCurve.points_NL_min` requires a tuple of tuple
pairs; mutable lists are rejected to keep result provenance immutable.
The energy scaling is a linear scenario assumption, not a validated part-load
power curve or actual-consumption model. Delivery is a nominal manufacturer value, not
measured total flow. Power and flow sources differ in pressure; volume basis,
curve applicability, module addition and dryer inclusion remain unverified.
The API raises `ValueError` rather than extrapolating or calculating above
nominal capacity. These guards are scenario constraints, not plant limits.
The ledger remains blocked for compression energy. `Report` rejects both a
scenario object and a `Computed` value for the unresolved compression item,
including an attempted relabelling of scenario energy as a normal ledger result.
Neither this API nor the example passes energy into the HULC measured-energy path.

The state before the restart is available via the git tag `archive-2026-11`.
