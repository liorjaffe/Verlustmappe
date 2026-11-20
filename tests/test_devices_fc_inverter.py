"""FC inverter (review 2026-11-19, Nr. 3a-3c): modelled loss only, DC - AC diagnostic, status visible."""
import math

import pytest

import _path  # noqa: F401
from verlustmappe import registry as R
from verlustmappe.devices.fc_inverter import FCInverter

ETA = R.get("inv_fc.eta")


def test_model_mode_carries_the_registry_status():
    r = FCInverter().account(10.0)
    assert math.isclose(r["e_ac_kWh"], 10.0 * ETA) and math.isclose(r["loss_kWh"], 10.0 * (1 - ETA))
    assert r["loss_status"] == r["eta_status"] == R.entry("inv_fc.eta")["status"] == "GUESS"
    assert r["eta_is_measured"] is False and r["dc_minus_ac_diagnostic_kWh"] is None
    assert "DERIVED" not in r["note"]


def test_measured_ac_zero_is_a_measurement_not_missing():
    r = FCInverter().account(1.0, 0.0)
    assert r["e_ac_kWh"] == 0.0 and r["eta"] == 0.0 and r["eta_is_measured"] is True
    assert r["dc_minus_ac_diagnostic_kWh"] == 1.0
    assert math.isclose(r["loss_kWh"], 1.0 * (1 - ETA)) and r["loss_is_modelled"] is True


def test_measured_difference_is_diagnostic_not_booked():
    r = FCInverter().account(1.0, 0.9)
    assert math.isclose(r["eta"], 0.9)
    assert math.isclose(r["dc_minus_ac_diagnostic_kWh"], 0.1)
    assert math.isclose(r["loss_kWh"], 1.0 * (1 - ETA))
    assert math.isclose(r["model_minus_measured_ac_diagnostic_kWh"], ETA - 0.9)
    assert r["eta_status"].startswith("WINDOW")


def test_ac_none_is_model_mode():
    assert FCInverter().account(1.0, None)["eta_is_measured"] is False


def test_dc_zero_ac_nonzero_is_flagged():
    r = FCInverter().account(0.0, 0.2)
    assert r["undefined_case"] == "dc0_ac_nonzero"
    assert r["eta"] is None and r["loss_kWh"] is None and r["dc_minus_ac_diagnostic_kWh"] is None
    assert r["e_ac_kWh"] == 0.2 and r["loss_status"] == "MISSING"


def test_dc_zero_ac_zero():
    r = FCInverter().account(0.0, 0.0)
    assert r["eta"] is None and r["undefined_case"] is None
    assert r["loss_kWh"] == 0.0 and r["dc_minus_ac_diagnostic_kWh"] == 0.0


def test_model_mode_dc_zero_gives_zero_not_none():
    r = FCInverter().account(0.0)
    assert r["e_ac_kWh"] == 0.0 and r["loss_kWh"] == 0.0


def test_missing_dc():
    r = FCInverter().account(None, 0.5)
    assert r["eta"] is None and r["loss_kWh"] is None and r["e_ac_kWh"] == 0.5


@pytest.mark.parametrize("dc,ac", [(-1.0, None), (float("nan"), None), (True, None),
                                   ("1", None), (1.0, float("inf")), (1.0, False)])
def test_invalid_inputs_raise(dc, ac):
    with pytest.raises(ValueError):
        FCInverter().account(dc, ac)
