"""Dryers DRY 2.1 coupled to H2 production (owner decisions 2026-11-19).

Hand calculations; values from plant/dryer.toml (2 units, 0.045 kWh/Nm3, 200 W rated,
10 W standby, 2.5 Nm3/h, purge maxima 30 NL/h and 47 NL per shutdown).
"""
import math

import pytest

import _path  # noqa: F401
from verlustmappe.devices.dryer import Dryer

FULL_1H_NL = 9 * 500.0   # 9 EL at nominal 500 NL/h for 1 h = 4.5 Nm3


def test_energy_value_is_production_coupled():
    r = Dryer().account(duration_h=1.0, throughput_NL=FULL_1H_NL, el_on_h=1.0)
    assert math.isclose(r["energy_kWh"], 0.045 * 4.5, rel_tol=1e-12)        # 0.2025 kWh
    assert r["energy_kWh"] == r["energy_kWh_model"] and not r["energy_is_measured"]
    half = Dryer().account(duration_h=1.0, throughput_NL=FULL_1H_NL / 2, el_on_h=1.0)
    assert math.isclose(half["energy_kWh"], r["energy_kWh"] / 2, rel_tol=1e-12)


def test_energy_envelope_two_units_on_time():
    r = Dryer().account(duration_h=24.0, throughput_NL=6 * FULL_1H_NL, el_on_h=6.0)
    env = r["energy_envelope"]
    assert math.isclose(env["lower_kWh"], 10 * 2 * 6.0 / 1000.0, rel_tol=1e-12)   # 0.12
    assert math.isclose(env["upper_kWh"], 200 * 2 * 6.0 / 1000.0, rel_tol=1e-12)  # 2.4
    assert env["lower_kWh"] <= r["energy_kWh_model"] <= env["upper_kWh"]          # 1.215
    assert env["label"].startswith("ENVELOPE, not a value")


def test_envelope_without_on_time_uses_window_and_opens_lower():
    r = Dryer().account(duration_h=24.0, throughput_NL=6 * FULL_1H_NL)
    assert r["energy_envelope"]["lower_kWh"] is None
    assert math.isclose(r["energy_envelope"]["upper_kWh"], 200 * 2 * 24.0 / 1000.0)
    assert "EL on-time unknown" in r["energy_envelope"]["label"]


def test_start_up_without_production_is_flagged_not_clipped():
    r = Dryer().account(duration_h=1.0, throughput_NL=0.0, el_on_h=0.5)
    assert r["energy_kWh"] == 0.0
    assert any("below the standby floor" in w and "not clipped" in w for w in r["warnings"])


def test_gas_loss_open_with_envelope():
    r = Dryer().account(duration_h=1.0, throughput_NL=FULL_1H_NL, el_on_h=1.0, n_shutdowns=2)
    assert r["gas_loss_NL"] is None and r["gas_loss_status"] == "BACKLOG"
    assert r["gas_loss_kWh_LHV"] is None
    env = r["gas_loss_envelope"]
    assert env["lower_NL"] == 0.0
    assert math.isclose(env["upper_regen_NL"], 30 * 2 * 1.0)      # 60 NL
    assert math.isclose(env["upper_shutdown_NL"], 47 * 2)         # 94 NL
    assert math.isclose(env["upper_NL"], 154.0)
    assert any("purge loss OPEN" in w and "CONTRACT sec. 7" in w for w in r["warnings"])


def test_shutdown_bound_open_without_event_count():
    r = Dryer().account(duration_h=1.0, throughput_NL=FULL_1H_NL, el_on_h=1.0)
    assert r["gas_loss_envelope"]["upper_shutdown_NL"] is None
    assert r["gas_loss_envelope"]["upper_NL"] is None
    assert any("shutdown event count not given" in w for w in r["warnings"])


def test_measured_values_replace_model():
    r = Dryer().account(duration_h=1.0, throughput_NL=FULL_1H_NL, el_on_h=1.0,
                        measured_kWh=0.3, measured_gas_loss_NL=20.0)
    assert r["energy_kWh"] == 0.3 and r["energy_is_measured"]
    assert r["gas_loss_NL"] == 20.0 and r["gas_loss_status"] == "MEASURED"
    assert r["gas_loss_kWh_LHV"] > 0
    assert not any("modelled from 0.045" in w for w in r["warnings"])


def test_capacity_check():
    ok = Dryer().account(duration_h=1.0, throughput_NL=FULL_1H_NL, el_on_h=1.0)
    assert ok["checks"]["total_capacity"]["status"] == "PASS"       # 4.5 <= 2 x 2.5
    # EL 1-5 on one dryer: 5 x 500 NL/h = 2.5 Nm3/h vs 2.5 Nm3/h rating -> PASS, no margin
    assert ok["checks"]["per_unit_capacity"]["status"] == "PASS"
    assert "at the rating limit" in ok["checks"]["per_unit_capacity"]["detail"]
    assert any("exactly at its rated drying rate" in w for w in ok["warnings"])
    over = Dryer().account(duration_h=1.0, throughput_NL=6000.0, el_on_h=1.0)
    assert over["checks"]["total_capacity"]["status"] == "FAIL"     # 6.0 > 5.0
    assert any("capacity check FAILED" in w for w in over["warnings"])


@pytest.mark.parametrize("kwargs", [
    dict(duration_h=0.0, throughput_NL=1.0),
    dict(duration_h=1.0, throughput_NL=-1.0),
    dict(duration_h=1.0, throughput_NL=1.0, el_on_h=2.0),
    dict(duration_h=1.0, throughput_NL=1.0, n_shutdowns=float("inf")),
])
def test_input_guards(kwargs):
    with pytest.raises(ValueError):
        Dryer().account(**kwargs)
