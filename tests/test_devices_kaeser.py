"""Dry ideal-gas conversion checks; not verification of the installed Kaeser."""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from verlustmappe.devices.kaeser import fad_to_normal_NL_min


@pytest.fixture
def conditions():
    return dict(inlet_pressure_abs_bar=1, inlet_temperature_K=293.15,
                normal_pressure_abs_bar=1.01325, normal_temperature_K=273.15)


def test_equal_conditions_only_change_volume_units(conditions):
    conditions.update(normal_pressure_abs_bar=1, normal_temperature_K=293.15)
    assert fad_to_normal_NL_min(0.67, **conditions) == pytest.approx(670)
    assert fad_to_normal_NL_min(0, **conditions) == 0


def test_reference_conversion_and_inverse(conditions):
    flow_NL_min = fad_to_normal_NL_min(0.67, **conditions)
    # Independent ideal-gas equality p_in*Q_in/T_in = p_N*Q_N/T_N.
    assert flow_NL_min * 1.01325 / 273.15 == pytest.approx(670 / 293.15)
    assert 616 < flow_NL_min < 617
    reverse = dict(
        inlet_pressure_abs_bar=1.01325, inlet_temperature_K=273.15,
        normal_pressure_abs_bar=1, normal_temperature_K=293.15,
    )
    assert fad_to_normal_NL_min(flow_NL_min / 1000, **reverse) == pytest.approx(670)


@pytest.mark.parametrize("field", [
    "inlet_pressure_abs_bar", "inlet_temperature_K",
    "normal_pressure_abs_bar", "normal_temperature_K",
])
@pytest.mark.parametrize("bad", [0, -1, True, float("nan"), float("inf"), "1"])
def test_invalid_reference_conditions_raise(conditions, field, bad):
    conditions[field] = bad
    with pytest.raises(ValueError):
        fad_to_normal_NL_min(0.67, **conditions)


@pytest.mark.parametrize("bad", [-1, True, float("nan"), float("inf"), "1"])
def test_invalid_flow_raises(conditions, bad):
    with pytest.raises(ValueError):
        fad_to_normal_NL_min(bad, **conditions)
