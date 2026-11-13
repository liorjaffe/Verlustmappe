"""Independent hand-reference checks; reference committed before this test."""

import math
from pathlib import Path
import runpy

import pytest

import _path
import xlsx_reader
from verlustmappe import registry as R
from verlustmappe.devices import Tank
from verlustmappe.hydrogen import h2_from_tank_pressure
from verlustmappe.hydrogen.temperature_model import temperature_corrected_mass


ROOT = Path(__file__).resolve().parents[1]
HAND = runpy.run_path(str(ROOT / "tests/reference/hand/storage_temperature.py"))


def test_project_local_sensitivity_matches_independent_hand_derivative():
    temperature_C = 20.0
    step_K = 0.001
    mass_low = temperature_corrected_mass(300.0, 1000.0, temperature_C - step_K)
    mass_high = temperature_corrected_mass(300.0, 1000.0, temperature_C + step_K)
    derivative_pct_per_K = 100.0 * (math.log(mass_high) - math.log(mass_low)) / (2.0 * step_K)
    expected = float(HAND["LOCAL_SENSITIVITY_PCT_PER_K"])
    assert abs(derivative_pct_per_K - expected) < 1e-8
    assert round(expected, 3) == -0.286
    assert round(float(HAND["IDEAL_SENSITIVITY_PCT_PER_K"]), 3) == -0.341


def test_workbook_sensitivity_is_calculated_not_a_model_input():
    workbook = xlsx_reader.load(ROOT / "plant/sources/Storage_H2_System_Specs_Master.xlsx")
    row = workbook["Master"][42]
    assert row["I"]["v"] == "stor.dm_dt_pct_per_k"
    assert row["O"]["f"] is None
    assert float(row["O"]["v"]) == round(float(HAND["LOCAL_SENSITIVITY_PCT_PER_K"]), 3)
    assert row["F"]["v"] == "Calculated (from definitions)"
    for phrase in ("ESTIMATED mass", "MEASURED pressure", "ASSUMED temperature",
                   "not constant mass or leakage", "300 bar absolute", "1.192"):
        assert phrase in row["D"]["v"]
    assert "stor.dm_dt_pct_per_k" not in R.REGISTRY


def test_rectangular_band_standard_uncertainty_and_stock_contribution():
    result = Tank().stored(300.0, analyze_temperature_uncertainty=True)
    expected_K = float(HAND["STANDARD_TEMPERATURE_UNCERTAINTY_K"])
    expected_rel = float(HAND["TEMPERATURE_UNCERTAINTY_REL"])
    assert abs(result["temperature_standard_uncertainty_K"] - expected_K) < 1e-12
    assert abs(result["temperature_uncertainty_rel"] - expected_rel) < 1e-14
    assert abs(result["temperature_mass_standard_uncertainty_kg"]
               - result["kg"] * expected_rel) < 1e-12
    assert result["temperature_status"] == "GUESS"
    assert "not total mass uncertainty" in result["temperature_uncertainty_note"]


def test_common_offset_route2_matches_hand_budget_and_keeps_model_allowance_separate():
    result = h2_from_tank_pressure(
        50.0, 150.0, bundle_isolated=True, analyze_temperature_uncertainty=True)
    assert abs(result["temperature_assumption_uncertainty_rel"]
               - float(HAND["TEMPERATURE_UNCERTAINTY_REL"])) < 1e-14
    assert result["temperature_model_allowance_K"] == 3.0
    assert abs(result["temperature_model_allowance_rel"]
               - float(HAND["MODEL_ALLOWANCE_REL"])) < 1e-14
    assert abs(result["uncertainty_rel"] - float(HAND["ROUTE2_UNCERTAINTY_REL"])) < 1e-14
    assert result["uncertainty_incomplete"] is False
    assert result["evidence_status"] == "GUESS"
    assert result["origin"] == "computed"
    assert "owner model choice" in result["temperature_correlation_assumption"]
    assert "volume confirmation and measurement validation remain open" in result["uncertainty_note"]


@pytest.mark.parametrize("explicit_state", ["T_start_C", "T_end_C"])
def test_mixed_temperature_states_do_not_claim_complete_propagation(explicit_state):
    result = h2_from_tank_pressure(
        50.0, 150.0, bundle_isolated=True, analyze_temperature_uncertainty=True,
        **{explicit_state: 25.0})
    assert result["uncertainty_incomplete"] is True
    assert result["temperature_assumption_uncertainty_rel"] is None
    assert result["evidence_status"] == "GUESS"
    assert "total shown is partial" in result["uncertainty_note"]


def test_explicit_temperature_has_no_assumption_uncertainty_added():
    result = h2_from_tank_pressure(
        50.0, 150.0, T_start_C=20.0, T_end_C=20.0, bundle_isolated=True,
        analyze_temperature_uncertainty=True)
    assert result["temperature_standard_uncertainty_K"] is None
    assert result["temperature_assumption_uncertainty_rel"] == 0.0
    assert result["temperature_is_assumed"] is False


def test_static_main_run_has_no_automatic_band_or_mixed_source_blocker():
    stock = Tank().stored(300.0)
    route = h2_from_tank_pressure(50.0, 150.0, bundle_isolated=True)
    mixed = h2_from_tank_pressure(
        50.0, 150.0, T_start_C=25.0, bundle_isolated=True)
    for result in (stock, route, mixed):
        assert result["temperature_uncertainty_analysis_requested"] is False
        assert result["temperature_standard_uncertainty_K"] is None
        assert result["origin"] == "computed"
    assert stock["temperature_mass_standard_uncertainty_kg"] is None
    assert route["temperature_assumption_uncertainty_rel"] is None
    assert mixed["uncertainty_incomplete"] is False
    analyzed = h2_from_tank_pressure(
        50.0, 150.0, bundle_isolated=True, analyze_temperature_uncertainty=True)
    expected_increment = float(HAND["TEMPERATURE_UNCERTAINTY_REL"])**2
    assert abs(analyzed["uncertainty_rel"]**2 - route["uncertainty_rel"]**2
               - expected_increment) < 1e-14
    assert analyzed["kg"] == route["kg"]
    assert analyzed["T_used_C"] == route["T_used_C"]
