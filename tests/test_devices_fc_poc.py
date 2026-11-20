"""POC layer 1 (decisions/2026-11-19-fc-poc-plan.md): hand-checked arithmetic, no validation."""
import math

import pytest

import _path  # noqa: F401
from verlustmappe import registry as R
from verlustmappe.devices.fc import poc_layer1


def test_inputs_are_the_approved_values():
    assert R.get("fc.poc_case_rate_per_h") == 15 and R.entry("fc.poc_case_rate_per_h")["status"] == "GUESS"
    assert R.get("fc.poc_case_duration_s") == 12 and R.entry("fc.poc_case_duration_s")["status"] == "GUESS"
    assert R.get("fc.power_limit_W") == 2400
    assert R.get("bat.round_trip_efficiency") == 0.97
    assert "RECHECK" in R.entry("bat.round_trip_efficiency")["source"]


def test_hand_check_2000_W_one_module():
    r = poc_layer1(2000, 1)
    assert math.isclose(r["battery_Wh_per_event_per_module"], 2000 * 12 / 3600)   # 6.667 Wh
    assert math.isclose(r["battery_discharge_Wh_per_h"], 15 * 2000 * 12 / 3600)  # 100 Wh
    assert r["fully_recharged"] is True
    assert math.isclose(r["battery_recharge_Wh_per_h"], 100 / 0.97)
    assert math.isclose(r["battery_throughput_loss_Wh_per_h"], 100 / 0.97 - 100)  # 3.09 Wh
    assert math.isclose(r["battery_stock_change_Wh_per_h"], 0.0, abs_tol=1e-9)
    assert r["status"] == "GUESS"
    assert r["warnings"] == ()


def test_two_modules_double_energy_and_peak():
    one, two = poc_layer1(2000, 1), poc_layer1(2000, 2)
    for k in ("battery_discharge_Wh_per_h", "battery_throughput_loss_Wh_per_h"):
        assert math.isclose(two[k], 2 * one[k])
    assert two["battery_peak_W_if_coincident"] == 4000


def test_no_recharge_at_the_power_limit():
    r = poc_layer1(2400, 1)
    assert r["fully_recharged"] is False
    assert r["battery_recharge_Wh_per_h"] == 0.0
    assert math.isclose(r["battery_stock_change_Wh_per_h"], -120.0)
    assert r["battery_throughput_loss_Wh_per_h"] == 0.0


def test_recharge_threshold():
    r = poc_layer1(2000, 1)
    p_max = 2400 / (1 + 15 * 12 / (0.97 * 3420))
    assert math.isclose(r["P_max_W_for_full_recharge"], p_max)  # approx. 2276 W
    assert poc_layer1(p_max - 1, 1)["fully_recharged"] is True
    assert poc_layer1(p_max + 1, 1)["fully_recharged"] is False


def test_h2_is_missing_not_zero():
    r = poc_layer1(2000, 2)
    assert r["h2_g_per_event"] is None and r["h2_status"] == "MISSING"


def test_zero_load_is_valid():
    r = poc_layer1(0, 1)
    assert r["battery_discharge_Wh_per_h"] == 0.0 and r["fully_recharged"] is True


def test_above_power_limit_warns_not_clips():
    r = poc_layer1(2500, 1)
    assert r["P_W_per_module"] == 2500
    assert any("power limit" in w for w in r["warnings"])


@pytest.mark.parametrize("P,n", [(-1, 1), (float("nan"), 1), (True, 1), ("2000", 1),
                                 (2000, 0), (2000, 1.0), (2000, True)])
def test_invalid_inputs_raise(P, n):
    with pytest.raises(ValueError):
        poc_layer1(P, n)


@pytest.mark.parametrize("key,value", [("fc.poc_case_rate_per_h", -15), ("fc.poc_case_duration_s", -12),
                                       ("fc.power_limit_W", -2400)])
def test_negative_registry_inputs_raise(monkeypatch, key, value):
    import verlustmappe.devices.fc as F
    original = F.R.get
    monkeypatch.setattr(F.R, "get", lambda k: value if k == key else original(k))
    with pytest.raises(ValueError):
        poc_layer1(2000, 1)


@pytest.mark.parametrize("key", ["fc.poc_case_rate_per_h", "fc.poc_case_duration_s", "fc.power_limit_W"])
def test_zero_registry_inputs_are_valid(monkeypatch, key):
    import verlustmappe.devices.fc as F
    original = F.R.get
    monkeypatch.setattr(F.R, "get", lambda k: 0 if k == key else original(k))
    r = poc_layer1(2000, 1)
    if key == "fc.power_limit_W":
        assert r["fully_recharged"] is False and r["battery_recharge_Wh_per_h"] == 0.0
    else:
        assert r["battery_discharge_Wh_per_h"] == 0.0 and r["fully_recharged"] is True
