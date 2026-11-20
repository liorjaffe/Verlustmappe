"""WTM 2.1 water tank in the water chain RO -> WTM -> 9 EL (owner, 2026-11-19).

Hand calculations; values from plant/water.toml and plant/el.toml.
"""
import math

import pytest

import _path  # noqa: F401
from verlustmappe import registry as R
from verlustmappe.devices.water import WaterSystem

SPEC = 0.0008037                   # L water per NL H2
FULL_1H_NL = 9 * 500.0             # 9 EL at nominal 500 NL/h for 1 h
WATER_1H = FULL_1H_NL * SPEC       # 3.61665 L


def _set(monkeypatch, key, value, status="DATASHEET"):
    entry = dict(R.REGISTRY[key])
    entry.update(value=value, status=status)
    monkeypatch.setitem(R.REGISTRY, key, entry)


def test_full_load_tank_energy_standby_and_open_pump():
    r = WaterSystem().account(duration_h=1.0, h2_produced_NL=FULL_1H_NL, el_on_h=1.0)
    assert math.isclose(r["water_consumed_L"], 3.61665, rel_tol=1e-12)
    # 3 W x 1 h EL on-time
    assert math.isclose(r["tank_energy_kWh_standby"], 0.003, abs_tol=1e-15)
    assert r["tank_standby_basis"].startswith("EL on-time")
    # pump running time is BACKLOG: no value, no total
    assert r["tank_pump_energy_kWh"] is None
    assert r["tank_pump_status"] == "BACKLOG"
    assert r["tank_energy_kWh"] is None and r["tank_energy_kWh_model"] is None
    assert any("WTM pump energy OPEN" in w and "CONTRACT sec. 7" in w for w in r["warnings"])


def test_standby_follows_el_on_time_not_window():
    # WTM is powered only while the EL are on (owner, 2026-11-19): 3 W x 6 h, not x 24 h
    r = WaterSystem().account(duration_h=24.0, h2_produced_NL=5 * FULL_1H_NL, el_on_h=6.0)
    assert math.isclose(r["tank_energy_kWh_standby"], 0.018, rel_tol=1e-12)
    assert math.isclose(r["tank_pump_energy_envelope"]["upper_kWh"], 35.0 * 6.0 / 1000.0,
                        rel_tol=1e-12)
    assert r["tank_pump_energy_envelope"]["label"].endswith("EL on-time.")


def test_standby_open_without_el_on_time():
    r = WaterSystem().account(duration_h=24.0, h2_produced_NL=5 * FULL_1H_NL)
    assert r["tank_energy_kWh_standby"] is None
    assert r["tank_standby_basis"].startswith("OPEN")
    assert any("WTM standby OPEN" in w for w in r["warnings"])
    # upper bound falls back to the window, labelled as such
    assert math.isclose(r["tank_pump_energy_envelope"]["upper_kWh"], 35.0 * 24.0 / 1000.0,
                        rel_tol=1e-12)
    assert "EL on-time unknown" in r["tank_pump_energy_envelope"]["label"]


def test_el_on_time_guard():
    with pytest.raises(ValueError):
        WaterSystem().account(duration_h=1.0, h2_produced_NL=FULL_1H_NL, el_on_h=2.0)


def test_pump_envelope_hand_calculation():
    r = WaterSystem().account(duration_h=1.0, h2_produced_NL=FULL_1H_NL)
    t_min = 3.61665 / (3.8 * 60.0)                # 0.0158625 h
    assert math.isclose(r["tank_pump_min_h"], t_min, rel_tol=1e-12)
    env = r["tank_pump_energy_envelope"]
    assert math.isclose(env["lower_kWh"], 35.0 * t_min / 1000.0, rel_tol=1e-12)  # ~0.555 Wh
    assert math.isclose(env["upper_kWh"], 0.035, rel_tol=1e-12)
    assert env["label"].startswith("ENVELOPE, not a value")
    assert "operative power whenever it runs" in env["label"]


def test_ro_energy_unchanged_by_tank_and_refill_levels(monkeypatch):
    base = WaterSystem().account(duration_h=24.0, h2_produced_NL=24 * FULL_1H_NL)
    _set(monkeypatch, "water.tank_refill_start_L", 20.0)
    _set(monkeypatch, "water.tank_refill_stop_L", 38.0)
    batched = WaterSystem().account(duration_h=24.0, h2_produced_NL=24 * FULL_1H_NL)
    for key in ("ro_production_h", "energy_kWh_model", "feed_L", "concentrate_L"):
        assert batched[key] == base[key]


def test_refill_cycles_hand_calculation(monkeypatch):
    _set(monkeypatch, "water.tank_refill_start_L", 20.0)
    _set(monkeypatch, "water.tank_refill_stop_L", 38.0)
    r = WaterSystem().account(duration_h=24.0, h2_produced_NL=24 * FULL_1H_NL)
    water = 24 * WATER_1H                          # 86.7996 L
    assert math.isclose(r["tank_refill_L"], 18.0)
    assert math.isclose(r["tank_refills"], water / 18.0, rel_tol=1e-12)          # 4.82
    assert math.isclose(r["tank_refill_interval_h"], 18.0 / WATER_1H, rel_tol=1e-12)  # 4.98 h
    assert math.isclose(r["tank_ro_h_per_refill"], 18.0 / 120.0, rel_tol=1e-12)  # 0.15 h


def test_refill_levels_open_by_default():
    r = WaterSystem().account(duration_h=1.0, h2_produced_NL=FULL_1H_NL)
    assert r["tank_refills"] is None and r["tank_refill_interval_h"] is None
    assert any("WTM refill levels OPEN" in w for w in r["warnings"])


@pytest.mark.parametrize("start, stop", [(30.0, 20.0), (20.0, 20.0), (10.0, 41.0)])
def test_invalid_refill_levels_raise(monkeypatch, start, stop):
    _set(monkeypatch, "water.tank_refill_start_L", start)
    _set(monkeypatch, "water.tank_refill_stop_L", stop)
    with pytest.raises(ValueError):
        WaterSystem().account(duration_h=1.0, h2_produced_NL=FULL_1H_NL)


def test_tank_level_change_sets_permeate():
    r = WaterSystem().account(duration_h=1.0, h2_produced_NL=FULL_1H_NL, tank_level_change_L=10.0)
    assert math.isclose(r["permeate_L"], WATER_1H + 10.0, rel_tol=1e-12)
    assert math.isclose(r["ro_production_h"], (WATER_1H + 10.0) / 120.0, rel_tol=1e-12)
    assert math.isclose(r["feed_L"], 2 * (WATER_1H + 10.0), rel_tol=1e-12)
    assert r["permeate_basis"] == "EL demand + tank level change"
    steady = WaterSystem().account(duration_h=1.0, h2_produced_NL=FULL_1H_NL)
    assert steady["permeate_L"] == steady["water_consumed_L"]
    assert steady["permeate_basis"].startswith("steady state")


def test_tank_level_change_guards():
    with pytest.raises(ValueError):
        WaterSystem().account(duration_h=1.0, h2_produced_NL=FULL_1H_NL, tank_level_change_L=-10.0)
    with pytest.raises(ValueError):
        WaterSystem().account(duration_h=1.0, measured_water_L=4.0, tank_level_change_L=1.0)
    with pytest.raises(ValueError):
        WaterSystem().account(duration_h=1.0, tank_level_change_L=float("nan"))


def test_measured_tank_energy_and_known_duty(monkeypatch):
    m = WaterSystem().account(duration_h=1.0, h2_produced_NL=FULL_1H_NL, measured_tank_kWh=0.01)
    assert m["tank_energy_kWh"] == 0.01 and m["tank_energy_is_measured"]
    _set(monkeypatch, "water.tank_pump_duty", 0.1, status="MEASURED")
    d = WaterSystem().account(duration_h=1.0, h2_produced_NL=FULL_1H_NL, el_on_h=1.0)
    # 3 W x 1 h + 35 W x 0.1 x 1 h EL on-time
    assert math.isclose(d["tank_pump_energy_kWh"], 0.0035, rel_tol=1e-12)
    assert math.isclose(d["tank_energy_kWh"], 0.0065, rel_tol=1e-12)
    assert not any("WTM pump energy OPEN" in w for w in d["warnings"])


def test_chain_checks_pass_and_open():
    c = WaterSystem().account(duration_h=1.0, h2_produced_NL=FULL_1H_NL)["chain_checks"]
    assert {k: v["status"] for k, v in c.items()} == {
        "ro_capacity_vs_design_demand": "PASS",        # 120 L/h vs 9 x 0.4 = 3.6 L/h
        "ro_permeate_vs_tank_inlet_flow": "PASS",      # 2 L/min vs > 0.28 L/min
        "el_count_vs_tank_rating": "PASS",             # 9 vs up to 11
        "tank_outlet_vs_el_inlet_pressure": "PASS",    # 2.75 barg in 1-4 barg
        "ro_permeate_pressure_vs_tank_inlet": "OPEN",  # permeate pressure undocumented
    }


def test_chain_check_fail_is_warned(monkeypatch):
    _set(monkeypatch, "water.n_el_supplied", 12, status="OWNER_DECISION")
    r = WaterSystem().account(duration_h=1.0, h2_produced_NL=FULL_1H_NL)
    assert r["chain_checks"]["el_count_vs_tank_rating"]["status"] == "FAIL"
    assert any("water chain check FAILED: el_count_vs_tank_rating" in w for w in r["warnings"])


def test_ro_production_beyond_el_on_time_is_warned():
    # 30 L permeate needs 0.25 h RO time; EL on only 0.1 h
    r = WaterSystem().account(duration_h=1.0, water_consumed_L=30.0, el_on_h=0.1)
    assert any("RO production time exceeds the EL on-time" in w for w in r["warnings"])
    assert math.isclose(r["energy_kWh_standby"], 3.0 * 0.1 / 1000.0, rel_tol=1e-12)
