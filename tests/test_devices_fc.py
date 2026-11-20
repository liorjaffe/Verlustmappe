"""FuelCellSystem channel selection: only fcN_ columns are FC modules (review 2026-11-19, Nr. 1)."""
import math

import pandas as pd

import _path  # noqa: F401
from verlustmappe import registry as R
from verlustmappe.devices.fc import FuelCellSystem

IDX = pd.date_range("2026-01-01", periods=11, freq="s", tz="UTC")


def _frame(**cols):
    return pd.DataFrame({"fc_power_W": 1000.0, **cols}, index=IDX)


def test_battery_and_inverter_currents_are_not_fc_modules():
    base = dict(fc1_current_A=10.0, fc2_current_A=10.0, load_current_A=24.0)
    plain = FuelCellSystem().account(_frame(**base))
    extra = FuelCellSystem().account(_frame(**base, batt_current_A=4.0, dc_input_A=24.0))
    assert list(plain["battery_current_residual_A"]) == [4.0] * 11
    assert list(extra["battery_current_residual_A"]) == [4.0] * 11
    assert math.isclose(extra["control_energy_kWh_envelope"], plain["control_energy_kWh_envelope"])
    # two modules over 10 observed seconds at the 150 W nameplate maximum
    expected = 2 * R.get("fc.control_input_W_max") / 1000.0 * 10.0 / 3600.0
    assert math.isclose(plain["control_energy_kWh_envelope"], expected)


def test_one_module_with_battery_column():
    r = FuelCellSystem().account(_frame(fc1_current_A=2.0, load_current_A=4.0, batt_current_A=2.0))
    assert list(r["battery_current_residual_A"]) == [2.0] * 11
    assert math.isclose(r["control_energy_kWh_envelope"],
                        R.get("fc.control_input_W_max") / 1000.0 * 10.0 / 3600.0)


def test_non_fc_stack_column_does_not_switch_to_the_faraday_route():
    r = FuelCellSystem().account(_frame(fc1_current_A=10.0, el_stack_current_A=5.0))
    assert r["efficiency_is_measured"] is False
