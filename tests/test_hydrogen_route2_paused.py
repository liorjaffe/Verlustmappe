"""Independent Route 2 unavailable; synthetic storage physics remains usable."""

import pytest

import _path
from verlustmappe import registry as R
from verlustmappe.devices import Tank
from verlustmappe.hydrogen import (
    compare_routes, h2_from_tank_pressure, model_tank_pressure_change,
)


def test_route2_returns_no_countercheck_quantities_even_with_scenario_inputs():
    result = h2_from_tank_pressure(
        50.0, 150.0, T_start_C=20.0, T_end_C=20.0, bundle_isolated=True)
    assert result["availability"] == "UNAVAILABLE"
    assert "DCT 541 and Pt100 are not installed" in result["reason"]
    for key in ("mol", "kg", "NL", "kWh_LHV", "uncertainty_rel"):
        assert result[key] is None
    assert result["independent_of"] == []
    assert result["uncertainty_incomplete"] is True


def test_paused_route_and_static_stock_do_not_depend_on_planned_pressure_accuracy():
    entry = R.REGISTRY.pop("meas.p_sensor_fso_bar")
    try:
        assert h2_from_tank_pressure(50.0, 150.0)["kg"] is None
        assert Tank().stored(100.0)["kg"] > 0.0
    finally:
        R.REGISTRY["meas.p_sensor_fso_bar"] = entry


@pytest.mark.parametrize("tank", [
    {"route": "tank_pv", "kg": None, "availability": "UNAVAILABLE"},
    {"route": "tank_pv", "kg": 1.0, "uncertainty_rel": 0.01},
    {"route": "tank_pv_minus_losses", "kg": 1.0, "uncertainty_rel": 0.01},
    {"route": "tank_pv_model", "kg": 1.0, "uncertainty_rel": 0.01},
    {"route": "water", "kg": 1.0, "uncertainty_rel": 0.01,
     "validation_eligible": False},
])
def test_paused_or_synthetic_entries_cannot_vote_or_create_residual(tank):
    production = {"route": "faraday_el", "kg": 1.0, "uncertainty_rel": 0.01}
    result = compare_routes([production, tank])
    assert result["n_independent"] == 0
    assert result["mean_kg"] is None
    assert "production_minus_delivered_residual" not in result
    assert result["unavailable_routes"][0]["route"] == "tank_pv"


def test_model_is_retained_but_never_independent_evidence():
    model = model_tank_pressure_change(50.0, 150.0, bundle_isolated=True)
    assert model["kg"] > 0.0
    assert model["route"] == "tank_pv_model"
    assert model["validation_eligible"] is False
    assert model["independent_of"] == []
    assert "hypothetical planned DCT 541 accuracy" in model["note"]
    result = compare_routes([model, dict(model)])
    assert result["n_independent"] == 0


def test_available_non_tank_routes_still_compare():
    result = compare_routes([
        {"route": "faraday_el", "kg": 1.0, "uncertainty_rel": 0.1},
        {"route": "water", "kg": 1.0, "uncertainty_rel": 0.1},
        h2_from_tank_pressure(50.0, 150.0),
    ])
    assert result["n_independent"] == 2
    assert result["mean_kg"] == 1.0
    assert "production_minus_delivered_residual" not in result
