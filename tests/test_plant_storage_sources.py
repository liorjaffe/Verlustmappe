"""Storage transfers against workbook evidence and the owner's 2026-11-13 decisions."""

from pathlib import Path

import numpy as np
import pytest

import _path
import xlsx_reader
from verlustmappe import registry as R
from verlustmappe.devices import AirDrivenBooster, Tank
from verlustmappe.accounting.status import u_class
from verlustmappe.hydrogen import model_tank_pressure_change as h2_from_tank_pressure
from verlustmappe.hydrogen.temperature_model import gs_fit_from_pressure_decay, hot_end_fill_bracket


WORKBOOK = Path(__file__).resolve().parents[1] / "plant/sources/Storage_H2_System_Specs_Master.xlsx"


def test_tara_and_ps_match_nameplate_rows_not_calculated_rows():
    sheets = xlsx_reader.load(WORKBOOK)
    for key, row in (("stor.steel_mass_kg", 28), ("stor.p_max_barg", 16)):
        cells = sheets["Master"][row]
        entry = R.entry(key)
        assert cells["E"]["v"] == "[S1]"
        assert cells["F"]["v"] == "Nameplate"
        assert cells["O"]["f"] is None
        assert entry["value"] == float(cells["O"]["v"])
        assert entry["status"] == "DATASHEET"
    assert sheets["Sources"][2]["A"]["v"] == "S1"
    assert "20261001_083001" in sheets["Sources"][2]["C"]["v"]
    assert "TARA" in R.entry("stor.steel_mass_kg")["source"]
    assert "NOT thermally effective steel mass" in R.entry("stor.steel_mass_kg")["source"]


def test_planned_temperature_matches_decided_concept_not_installed_hardware():
    sheets = xlsx_reader.load(WORKBOOK)
    cells = sheets["Master"][56]
    assert cells["E"]["v"] == "[S7]"
    assert cells["F"]["v"] == "Project decision"
    assert "1 x Pt100 4-wire class A on the cylinder shell" in cells["C"]["v"]
    assert sheets["Sources"][8]["A"]["v"] == "S7"
    assert "00 CURRENT STATE" in sheets["Sources"][8]["B"]["v"]
    entry = R.entry("stor.temp_sensor_planned")
    assert entry["status"] == "BACKLOG"
    for text in ("1 x Pt100", "4-wire", "class A", "insulated cylinder shell",
                 "lower/middle", "near outlet valve", "NOT installed",
                 "no hardware ordered", "no measured tank temperature",
                 "Inline thermowell remains an open option"):
        assert text in entry["value"]
    assert "Master row 56" in entry["source"]


def test_route2_stays_sensor_free_and_requires_explicit_pressure_endpoints():
    result = h2_from_tank_pressure(50.0, 100.0, bundle_isolated=True)
    assert result["temperature_tier"] == 1
    assert result["T_used_C"] == (20.0, 20.0)  # Owner-approved model assumption, not measurement.
    with pytest.raises(TypeError):
        h2_from_tank_pressure(50.0, bundle_isolated=True)


def test_gs_fit_without_effective_steel_mass_remains_gas_only():
    time_s = np.arange(0.0, 3600.0, 60.0)
    pressure_abs_bar = 120.0 + 100.0 * np.exp(-time_s / 1800.0)
    result = gs_fit_from_pressure_decay(time_s, pressure_abs_bar, return_detail=True)
    assert result["GS_combined"] is None
    assert abs(result["tau_s"] - 1800.0) / 1800.0 < 0.02


def test_registered_temperature_is_a_scoped_rectangular_band_assumption():
    entry = R.entry("stor.T_assumed_C")
    assert entry["value"] == 20.0
    assert entry["unit"] == "degC"
    assert entry["status"] == "GUESS"
    assert entry["uncertainty"] == 0.019694704731012306
    assert u_class("stor.T_assumed_C", entry["status"], entry["uncertainty"]) == "assessed"
    assert "provisional storage/booster" in entry["source"]
    assert "rectangular band +/-10 K" in entry["source"]
    assert "actual" in entry["effect"].lower()
    assert "only with analyze_temperature_uncertainty=True" in entry["effect"]
    assert "Pt100 data path suspended" in R.entry("stor.temp_sensor_planned")["effect"]


def test_route2_rejects_sensor_tier_without_data():
    with pytest.raises(ValueError, match="tier=2 requires explicit"):
        h2_from_tank_pressure(50.0, 100.0, tier=2, bundle_isolated=True)


@pytest.mark.parametrize("channel", ["T_top_C", "T_bottom_C"])
def test_generic_single_temperature_input_stays_available(channel):
    result = h2_from_tank_pressure(
        50.0, 100.0, tier=2, bundle_isolated=True, **{channel: 30.0})
    assert result["T_used_C"] == (30.0, 30.0)
    assert result["temperature_is_assumed"] is False
    assert result["uncertainty_incomplete"] is False
    assert "not automatically measured" in result["temperature_source"]


def test_provisional_models_resolve_the_registry_not_a_literal_default():
    entry = R.entry("stor.T_assumed_C")
    original = entry["value"]
    try:
        entry["value"] = 21.0
        tank = Tank().stored(100.0)
        route = h2_from_tank_pressure(50.0, 100.0, bundle_isolated=True)
        booster = AirDrivenBooster().account(100.0, 35.0, 100.0, air_compressor_kWh=1.0)
        bracket = hot_end_fill_bracket(51.0, 101.0, 800.0)
        assert tank["T_used_C"] == 21.0
        assert route["T_used_C"] == (21.0, 21.0)
        assert booster["T_used_C"] == 21.0
        assert bracket["T_base_C"] == 21.0
        assert bracket["temperature_is_assumed"] is True
        for result in (tank, route, booster):
            assert result["temperature_is_assumed"] is True
            assert result["temperature_status"] == "GUESS"
            assert result["temperature_source"] == entry["source"]
        assert route["uncertainty_incomplete"] is False
        assert "no +/-10 K band analysis performed" in route["uncertainty_note"]
    finally:
        entry["value"] = original


def test_explicit_temperature_overrides_assumption_without_claiming_measurement():
    tank = Tank().stored(100.0, T_C=30.0)
    route = h2_from_tank_pressure(
        50.0, 100.0, T_start_C=30.0, T_end_C=31.0, bundle_isolated=True)
    booster = AirDrivenBooster().account(
        100.0, 35.0, 100.0, T_C=30.0, air_compressor_kWh=1.0)
    assert tank["T_used_C"] == 30.0
    assert route["T_used_C"] == (30.0, 31.0)
    assert booster["T_used_C"] == 30.0
    for result in (tank, route, booster):
        assert result["temperature_is_assumed"] is False
        assert "not automatically measured" in result["temperature_source"]


def test_partial_explicit_state_keeps_unassessed_correlation_visible_in_optional_analysis():
    result = h2_from_tank_pressure(
        50.0, 100.0, T_start_C=30.0, bundle_isolated=True,
        analyze_temperature_uncertainty=True)
    assert result["T_used_C"] == (30.0, 20.0)
    assert result["temperature_is_assumed"] is True
    assert result["uncertainty_incomplete"] is True
    assert result["temperature_assumption_uncertainty_rel"] is None
    assert "reassessment" in result["uncertainty_note"]
