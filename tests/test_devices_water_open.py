"""Water pump gap: independent quantities remain available (CONTRACT sec. 7)."""

import math
import tomllib
from pathlib import Path

import pytest

import _path
import xlsx_reader
from verlustmappe import registry
from verlustmappe.devices.water import WaterSystem


def test_workbook_inputs_and_pump_reference():
    root = Path(__file__).resolve().parents[1]
    workbook = xlsx_reader.load(str(root / "plant/sources/Water_System_Specs_Master.xlsx"))
    inputs = workbook["Inputs"]
    assert inputs[5]["B"]["v"] == "120"
    assert inputs[6]["B"]["v"] == "200"
    assert inputs[7]["B"]["v"] == "3"
    assert inputs[7]["C"]["v"] == "W (<3)"
    assert inputs[8]["B"]["v"] == "0.5"
    assert inputs[9]["E"]["v"] == "pump_W"
    assert not inputs[9].get("B", {}).get("v")
    assert "Energy Balance" not in workbook
    with (root / "plant/water.toml").open("rb") as stream:
        pump = tomllib.load(stream)["param"]["water.filter_train_power_W"]
    assert "Inputs B9" in pump["source"]


def test_missing_pump_and_independent_annual_ro_components():
    path = Path(__file__).resolve().parents[1] / "plant" / "water.toml"
    with path.open("rb") as stream:
        pump = tomllib.load(stream)["param"]["water.filter_train_power_W"]
    assert "value" not in pump
    assert pump["status"] == "BACKLOG"
    result = WaterSystem().account(duration_h=8760, water_consumed_L=3026.4)
    assert result["filter_train_energy_kWh"] is None
    assert result["filter_train_status"] == "BACKLOG"
    assert any("BACKLOG" in warning and "CONTRACT sec. 7" in warning
               for warning in result["warnings"])
    # 0.4 L/h * 7566 h / 120 L/h * 200 W / 1000.
    assert math.isclose(result["energy_kWh_production"], 5.044, abs_tol=1e-12)
    # 3 W * 8760 h / 1000; 3 W is the existing standby model basis.
    assert math.isclose(result["energy_kWh_standby"], 26.28, abs_tol=1e-12)
    assert math.isclose(result["feed_L"], 6052.8, abs_tol=1e-9)
    assert math.isclose(result["concentrate_L"], 3026.4, abs_tol=1e-9)


def test_absent_pump_parameter_is_open(monkeypatch):
    monkeypatch.delitem(registry.REGISTRY, "water.filter_train_power_W")
    result = WaterSystem().account(duration_h=2, water_consumed_L=0.4)
    assert result["filter_train_energy_kWh"] is None
    assert result["filter_train_status"] == "BACKLOG"
    assert any("BACKLOG" in warning and "CONTRACT sec. 7" in warning
               for warning in result["warnings"])
    assert math.isclose(result["energy_kWh_model"], 0.006666666666666667, abs_tol=1e-12)


def test_known_pump_power(monkeypatch):
    monkeypatch.setitem(registry.REGISTRY, "water.filter_train_power_W",
                        {"value": 50.0, "status": "MEASURED"})
    result = WaterSystem().account(duration_h=2, water_consumed_L=0.4)
    # 50 W * 2 h / 1000.
    assert result["filter_train_energy_kWh"] == 0.1
    assert result["filter_train_status"] == "MEASURED"


def test_independent_ro_calculation_hand_reference(monkeypatch):
    for key, value in (
            ("water.ro_perm_Lh", 120.0),
            ("water.ro_power_op_W", 200.0),
            ("water.wcf", 0.5)):
        monkeypatch.setitem(registry.REGISTRY[key], "value", value)
    result = WaterSystem().account(duration_h=1, water_consumed_L=12)
    assert result["ro_production_h"] == pytest.approx(0.1, rel=0, abs=1e-12)
    assert result["duty"] == pytest.approx(0.1, rel=0, abs=1e-12)
    assert result["energy_kWh_production"] == pytest.approx(0.02, rel=0, abs=1e-12)
    assert result["feed_L"] == pytest.approx(24, rel=0, abs=1e-12)
    assert result["concentrate_L"] == pytest.approx(12, rel=0, abs=1e-12)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1.0, True, "1"])
@pytest.mark.parametrize("parameter", [
    "water_consumed_L", "measured_kWh", "measured_water_L", "h2_produced_NL",
])
def test_invalid_nonnegative_inputs_are_rejected(parameter, value):
    with pytest.raises(ValueError, match=f"{parameter} must be a finite non-negative number"):
        WaterSystem().account(duration_h=1, **{parameter: value})


@pytest.mark.parametrize("duration_h", [0, -1, float("nan"), float("inf"), True, "1"])
def test_invalid_duration_is_rejected(duration_h):
    with pytest.raises(ValueError, match="duration_h must"):
        WaterSystem().account(duration_h=duration_h)


@pytest.mark.parametrize("key,value,message", [
    ("water.ro_perm_Lh", 0.0, "water.ro_perm_Lh must be > 0"),
    ("water.ro_perm_Lh", -1.0, "water.ro_perm_Lh must be a finite non-negative number"),
    ("water.wcf", 0.0, "water.wcf must be finite and in \\(0, 1\\]"),
    ("water.wcf", 1.1, "water.wcf must be finite and in \\(0, 1\\]"),
])
def test_invalid_capacity_and_wcf_are_rejected(monkeypatch, key, value, message):
    monkeypatch.setitem(registry.REGISTRY[key], "value", value)
    with pytest.raises(ValueError, match=message):
        WaterSystem().account(duration_h=1, water_consumed_L=1)


@pytest.mark.parametrize("value", ["unknown", True, float("nan"), float("inf"), -1.0])
def test_invalid_pump_power_is_rejected(monkeypatch, value):
    monkeypatch.setitem(registry.REGISTRY, "water.filter_train_power_W",
                        {"value": value, "status": "MEASURED"})
    with pytest.raises(ValueError, match="finite non-negative number or missing"):
        WaterSystem().account(duration_h=2, water_consumed_L=0.4)
