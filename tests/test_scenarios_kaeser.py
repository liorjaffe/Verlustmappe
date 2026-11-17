"""Independent checks for the isolated hypothetical scenario, not plant validation."""

from dataclasses import replace
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from verlustmappe.devices.h2_compressor import AirCurve, chart_air_demand_NL_min
from verlustmappe.scenarios.kaeser import KaeserScenario, calculate
from verlustmappe.accounting.ledger import Blocked, Computed, Report
from verlustmappe.accounting.params import ParamSet
from verlustmappe.accounting.static_map import Scenario, calculate as calculate_ledger


@pytest.fixture
def scenario():
    return KaeserScenario(
        h2_flow_NL_min=1000 / 60,
        module_140=AirCurve("adjacent graph readings", "workbook Master C128",
                            ((10, 150), (20, 175), (30, 200), (40, 250), (50, 280))),
        module_400=AirCurve("adjacent graph readings", "workbook Master C129",
                            ((10, 350), (20, 400), (30, 450), (40, 550), (50, 600))),
        nominal_air_flow_NL_min=616.126,
        reference_power_W=6200,
        operating_time_s=3600,
        reference_source="dealer 11 bar power; manufacturer 10 bar delivery, conditionally converted",
        assume_module_addition=True,
    )


def test_two_adjacent_readings_and_metadata(scenario):
    result = calculate(scenario)
    # 2/3 of the 10-to-20 interval: 150 + 25*2/3, 350 + 50*2/3.
    assert result.hulc_air_flow_NL_min == pytest.approx(550)
    assert result.scenario_energy_kWh == pytest.approx(5.5345822114)
    assert result.inputs == scenario
    assert result.inputs.module_140.basis == "adjacent graph readings"
    assert result.status == "HYPOTHETICAL / UNVERIFIED"
    for text in ("not a measurement", "11 bar", "10 bar", "not measured as zero", "not establish"):
        assert any(text in note.lower() for note in result.notes)


def test_historical_sparse_anchor_comparison(scenario):
    old = replace(
        scenario,
        module_140=AirCurve("historical sparse anchors", "workbook Master C128",
                            ((10, 150), (50, 280))),
        module_400=AirCurve("historical sparse anchors", "workbook Master C129",
                            ((10, 350), (50, 600))),
    )
    result = calculate(old)
    # 1/6 of the 10-to-50 interval: 150+130/6 + 350+250/6.
    assert result.hulc_air_flow_NL_min == pytest.approx(563 + 1 / 3)
    assert result.scenario_energy_kWh == pytest.approx(5.6687553098)
    assert result.inputs.module_400.basis == "historical sparse anchors"


def test_reject_outside_chart_including_single_el(scenario):
    for flow in (0, 500 / 60, 9.999, 51):
        with pytest.raises(ValueError, match="extrapolation"):
            calculate(replace(scenario, h2_flow_NL_min=flow))
    assert calculate(replace(scenario, h2_flow_NL_min=10)).hulc_air_flow_NL_min == 500


def test_capacity_guard_both_sides_and_exact_boundary(scenario):
    demand = 550
    with pytest.raises(ValueError, match="exceeds nominal"):
        calculate(replace(scenario, nominal_air_flow_NL_min=demand - 0.001))
    result = calculate(replace(scenario, nominal_air_flow_NL_min=demand))
    assert result.scenario_energy_kWh == pytest.approx(6.2)
    assert calculate(replace(scenario, nominal_air_flow_NL_min=demand + 0.001)).scenario_energy_kWh < 6.2
    with pytest.raises(ValueError, match="exceeds nominal"):
        calculate(replace(scenario, nominal_air_flow_NL_min=500))
    with pytest.raises(ValueError, match="exceeds nominal"):
        calculate(replace(scenario, h2_flow_NL_min=40))
    seven_hundred = replace(
        scenario,
        module_140=replace(scenario.module_140, points_NL_min=((10, 300), (20, 300))),
        module_400=replace(scenario.module_400, points_NL_min=((10, 400), (20, 400))),
    )
    with pytest.raises(ValueError, match="exceeds nominal"):
        calculate(seven_hundred)


def test_scenario_does_not_unblock_ledger(scenario):
    calculate(scenario)
    ledger = calculate_ledger(
        Scenario(2100, 8, 2700, 20, 1800, "synthetic ledger case"),
        ParamSet.from_registry(("el.n_cells", "el.faradaic_efficiency")),
        scope="full",
    )
    for key in ("compression_air_energy_kWh", "ready_energy_kWh", "leakage_energy_kWh"):
        assert isinstance(ledger[key], Blocked)


@pytest.mark.parametrize("scope", ["bounded", "full"])
def test_scenario_value_cannot_be_booked_as_compression(scenario, scope):
    result = calculate(scenario)
    ledger = calculate_ledger(
        Scenario(2100, 8, 2700, 20, 1800, "synthetic ledger case"),
        ParamSet.from_registry(("el.n_cells", "el.faradaic_efficiency")),
        scope="full",
    )
    forged = Computed(
        ledger["compression_air_energy_kWh"].item, result.scenario_energy_kWh,
        "GUESS", "SIMULATED", (), (),
    )
    results = tuple(forged if entry.item.key == forged.item.key else entry
                    for entry in ledger.results)
    with pytest.raises(ValueError, match="compression_air_energy_kWh.*unresolved"):
        Report(scope, results, ())
    with pytest.raises(ValueError, match="expected Computed or Blocked"):
        Report("bounded", (result,), ())


@pytest.mark.parametrize("assumption", [False, None, 1, "yes"])
def test_module_addition_requires_explicit_assumption(scenario, assumption):
    with pytest.raises(ValueError, match="explicit True"):
        calculate(replace(scenario, assume_module_addition=assumption))


def test_guards_apply_at_device_curve_boundary(scenario):
    arguments = dict(
        module_140=scenario.module_140, module_400=scenario.module_400,
        assume_module_addition=True, nominal_air_flow_NL_min=550,
    )
    assert chart_air_demand_NL_min(1000 / 60, **arguments) == pytest.approx(550)
    with pytest.raises(ValueError, match="extrapolation"):
        chart_air_demand_NL_min(500 / 60, **arguments)
    with pytest.raises(ValueError, match="exceeds nominal"):
        chart_air_demand_NL_min(20, **arguments)


def test_single_energy_formula_units_and_zero_duration(scenario):
    # 3.6 kW * 0.5 h * (550 / 1100) = 0.9 kWh, not 900 Wh.
    synthetic = replace(
        scenario, reference_power_W=3600, operating_time_s=1800,
        nominal_air_flow_NL_min=1100,
    )
    assert calculate(synthetic).scenario_energy_kWh == pytest.approx(0.9)
    assert calculate(replace(synthetic, operating_time_s=0)).scenario_energy_kWh == 0
    with pytest.raises(ValueError, match="finite"):
        calculate(replace(synthetic, reference_power_W=1e308, operating_time_s=1e308))


@pytest.mark.parametrize("field,value", [
    ("h2_flow_NL_min", float("nan")), ("h2_flow_NL_min", -1),
    ("nominal_air_flow_NL_min", 0), ("nominal_air_flow_NL_min", float("inf")),
    ("reference_power_W", -1), ("reference_power_W", True),
    ("operating_time_s", -1), ("operating_time_s", float("nan")),
    ("reference_source", ""),
])
def test_invalid_inputs_raise(scenario, field, value):
    with pytest.raises(ValueError):
        calculate(replace(scenario, **{field: value}))


def test_invalid_curve_and_mixed_bases_raise(scenario):
    bad_curves = (
        replace(scenario.module_140, basis=""),
        replace(scenario.module_140, source=""),
        replace(scenario.module_140, points_NL_min=((10, 150),)),
        replace(scenario.module_140, points_NL_min=((10, 150), (10, 175))),
        replace(scenario.module_140, points_NL_min=((10, -1), (20, 175))),
        replace(scenario.module_140, points_NL_min=((10, 150), (20, float("nan")))),
        replace(scenario.module_140, basis="different"),
    )
    for curve in bad_curves:
        with pytest.raises(ValueError):
            calculate(replace(scenario, module_140=curve))
