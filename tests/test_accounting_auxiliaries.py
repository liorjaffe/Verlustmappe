"""Full-scope ledger items for the EL-coupled auxiliaries (owner, 2026-11-19/20).

Synthetic P14 case (2100 W, 8 A, 2700 s operation, 20 W / 1800 s standby) plus one start.
Hand values from the approved P14 hydrogen amount and plant/*.toml.
"""
from copy import deepcopy

import pytest

import _path  # noqa: F401
from verlustmappe import registry
from verlustmappe.accounting.ledger import Blocked, CauseCode, Computed
from verlustmappe.accounting.params import ParamSet
from verlustmappe.accounting.static_map import Scenario, calculate

H2_MOL = 13.1634516054770            # approved P14 hand value (tolerance 2e-9)
H2_NM3 = H2_MOL * 22.414 / 1000.0    # 0.29504...
ON_S = 2700 + 1 * 990                # operating time + 1 start x el.startup_duration_s
KEYS = ("el.n_cells", "el.faradaic_efficiency", "el.startup_duration_s",
        "dryer.spec_energy_kWh_Nm3", "water.spec_water_L_per_NL", "water.ro_perm_Lh",
        "water.ro_power_op_W", "water.ro_power_standby_W", "water.tank_power_standby_W",
        "water.tank_power_op_W", "water.tank_pump_duty")


@pytest.fixture
def scenario():
    return Scenario(2100, 8, 2700, 20, 1800, "owner-approved synthetic P14 case", n_starts=1)


@pytest.fixture
def mutable_registry():
    original = deepcopy(registry.REGISTRY)
    try:
        yield registry.REGISTRY
    finally:
        registry.REGISTRY.clear()
        registry.REGISTRY.update(original)


def _full(scenario, keys=KEYS):
    return calculate(scenario, ParamSet.from_registry(keys), scope="full")


def test_dryer_energy_is_production_coupled(scenario):
    result = _full(scenario)["dryer_electrical_energy_kWh"]
    assert isinstance(result, Computed)
    assert result.value == pytest.approx(0.045 * H2_NM3, rel=2e-9)      # ~0.01328 kWh
    assert result.evidence_status == "GUESS"                              # scenario inputs
    assert "dryer.spec_energy_kWh_Nm3" in {u.key for u in result.input_uncertainties}
    assert "stack_current_A" in {u.key for u in result.input_uncertainties}


def test_water_energy_ro_production_plus_standby_over_on_time(scenario):
    result = _full(scenario)["water_energy_kWh"]
    assert isinstance(result, Computed)
    water_L = 0.0008037 * H2_MOL * 22.414
    expected = water_L / 120.0 * 200.0 / 1000.0 + 3.0 * ON_S / 3.6e6
    assert result.value == pytest.approx(expected, rel=2e-9)
    keys = {u.key for u in result.input_uncertainties}
    assert {"n_starts", "el.startup_duration_s", "water.ro_power_standby_W"} <= keys


def test_start_up_time_extends_auxiliary_on_time(scenario):
    from dataclasses import replace
    one = _full(scenario)["water_energy_kWh"].value
    three = _full(replace(scenario, n_starts=3))["water_energy_kWh"].value
    assert three - one == pytest.approx(3.0 * 2 * 990 / 3.6e6, rel=1e-9)


def test_tank_energy_blocked_by_backlog_pump_duty(scenario):
    result = _full(scenario)["water_tank_energy_kWh"]
    assert isinstance(result, Blocked)
    assert ("unavailable_parameter", "water.tank_pump_duty") in {
        (c.code.value, c.dependency) for c in result.causes}


def test_tank_energy_with_known_pump_duty(scenario, mutable_registry):
    mutable_registry["water.tank_pump_duty"].update(value=0.1, status="MEASURED")
    result = _full(scenario)["water_tank_energy_kWh"]
    assert isinstance(result, Computed)
    assert result.value == pytest.approx((3.0 + 35.0 * 0.1) * ON_S / 3.6e6, rel=1e-12)


def test_missing_start_count_blocks_on_time_items_only():
    scenario = Scenario(2100, 8, 2700, 20, 1800, "owner-approved synthetic P14 case")
    report = _full(scenario)
    assert isinstance(report["dryer_electrical_energy_kWh"], Computed)
    water = report["water_energy_kWh"]
    assert isinstance(water, Blocked)
    assert (CauseCode.MISSING_REQUIRED_INPUT, "n_starts") in {
        (c.code, c.dependency) for c in water.causes}


def test_unrequested_parameter_blocks_visibly(scenario):
    report = _full(scenario, keys=("el.n_cells", "el.faradaic_efficiency"))
    dryer = report["dryer_electrical_energy_kWh"]
    assert isinstance(dryer, Blocked)
    assert ("unavailable_parameter", "dryer.spec_energy_kWh_Nm3") in {
        (c.code.value, c.dependency) for c in dryer.causes}


def test_core_keys_still_required_and_bounded_scope_unchanged(scenario):
    with pytest.raises(KeyError):
        calculate(scenario, ParamSet.from_registry(("el.n_cells",)), scope="bounded")
    bounded = calculate(scenario, ParamSet.from_registry(KEYS), scope="bounded")
    assert {r.item.key for r in bounded.results} == {
        "el_operating_energy_kWh", "el_standby_energy_kWh", "hydrogen_amount_mol",
        "hydrogen_mass_kg", "hydrogen_lhv_energy_kWh"}


def test_vent_stays_blocked_with_concrete_reason(scenario):
    vent = _full(scenario)["dryer_vent_energy_kWh"]
    assert isinstance(vent, Blocked)
    assert any("30 NL/h" in c.reason and "47 NL" in c.reason for c in vent.causes)


def test_limits_state_plant_level_allocation(scenario):
    limits = _full(scenario).limits
    assert any("plant-level equipment" in limit for limit in limits)
    assert any("990 vs 1260 s open" in limit for limit in limits)
