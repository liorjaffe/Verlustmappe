"""P14 ledger: independent dependency, domain, immutability and accounting checks."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from verlustmappe import registry
from verlustmappe.models.ledger import (
    ITEMS, Blocked, CauseCode, Computed, Item, Report, Role, Sign, computed, sum_compatible,
)
from verlustmappe.models.params import BlockedParameterError, ParamSet
from verlustmappe.models.static_map import Scenario, calculate


@pytest.fixture
def parameters():
    return ParamSet.from_registry(("el.n_cells", "el.faradaic_efficiency"))


@pytest.fixture
def scenario():
    return Scenario(2100, 8, 2700, 20, 1800, "owner-approved synthetic P14 case")


def registry_entry(monkeypatch, key, **changes):
    entry = dict(registry.REGISTRY[key])
    entry.update(changes)
    monkeypatch.setitem(registry.REGISTRY, key, entry)


def test_registry_snapshot_is_requested_immutable_and_run_local(scenario):
    before = deepcopy(registry.REGISTRY)
    parameters = ParamSet.from_registry(("el.n_cells", "el.faradaic_efficiency"))
    assert tuple(p.key for p in parameters.parameters) == ("el.n_cells", "el.faradaic_efficiency")
    with pytest.raises(KeyError):
        parameters["dry.vent_fraction"]
    with pytest.raises(FrozenInstanceError):
        parameters.parameters = ()
    with pytest.raises(FrozenInstanceError):
        parameters["el.n_cells"].value = 1
    with pytest.raises(FrozenInstanceError):
        scenario.stack_current_A = 9
    calculate(scenario, parameters, scope="full")
    assert registry.REGISTRY == before


def test_nested_capture_freezes_values_without_mutating_source(monkeypatch):
    source = {"stages": [1, 2]}
    monkeypatch.setitem(registry.REGISTRY, "synthetic", {
        "value": source, "unit": "-", "status": "GUESS", "uncertainty": 0,
    })
    snapshot = ParamSet.from_registry(("synthetic",))
    source["stages"].append(3)
    captured = snapshot["synthetic"].value
    assert captured["stages"] == (1, 2)
    with pytest.raises(TypeError):
        captured["other"] = 1


@pytest.mark.parametrize("state", ["REJECTED", "SUPERSEDED"])
def test_blocked_parameter_state_is_not_backlog(monkeypatch, parameters, state):
    registry_entry(monkeypatch, "el.n_cells", status=state)
    with pytest.raises(BlockedParameterError, match=state):
        ParamSet.from_registry(("el.n_cells", "el.faradaic_efficiency"))


def test_adapter_errors_are_not_caught_as_backlog():
    with pytest.raises(KeyError):
        ParamSet.from_registry(("not.a.registry.key",))
    with pytest.raises(BlockedParameterError, match="REJECTED"):
        ParamSet.from_registry(("comp.pressure_ratio",))
    with pytest.raises(ValueError, match="duplicate"):
        ParamSet.from_registry(("el.n_cells", "el.n_cells"))


@pytest.mark.parametrize("field,blocked_keys", [
    ("stack_current_A", {"hydrogen_amount_mol", "hydrogen_mass_kg", "hydrogen_lhv_energy_kWh"}),
    ("standby_time_s", {"el_standby_energy_kWh"}),
    ("operating_time_s", {"el_operating_energy_kWh", "hydrogen_amount_mol",
                          "hydrogen_mass_kg", "hydrogen_lhv_energy_kWh"}),
])
def test_missing_input_blocks_exact_declared_dependants(scenario, parameters, field, blocked_keys):
    report = calculate(replace(scenario, **{field: None}), parameters, scope="bounded")
    assert report.invalid
    assert {result.item.key for result in report.results
            if isinstance(result, Blocked)} == blocked_keys
    for result in report.results:
        if isinstance(result, Blocked):
            assert result.indication == "BACKLOG"
            assert not hasattr(result, "value")
            assert not hasattr(result, "evidence_status")
            assert not hasattr(result, "result_origin")
            assert any(cause.code == CauseCode.MISSING_REQUIRED_INPUT
                       and cause.dependency == field for cause in result.causes)
            assert all(cause.reason for cause in result.causes)
    mass = report["hydrogen_mass_kg"]
    if "hydrogen_mass_kg" in blocked_keys:
        assert isinstance(mass, Blocked)
        assert any(cause.code == CauseCode.BLOCKED_DEPENDENCY
                   and cause.dependency == "hydrogen_amount_mol" for cause in mass.causes)


def test_negative_input_distinct_from_d31_computed_sign(scenario, parameters):
    report = calculate(replace(scenario, el_ac_input_power_W=-5), parameters, scope="bounded")
    result = report["el_operating_energy_kWh"]
    assert report.invalid and isinstance(result, Blocked)
    assert {cause.code for cause in result.causes} == {CauseCode.INVALID_INPUT_DOMAIN}
    assert isinstance(report["hydrogen_amount_mol"], Computed)

    item = Item("synthetic_loss_kWh", "kWh", Role.LOSS, ())
    negative = computed(item, -1, ("GUESS",), (), ())
    assert isinstance(negative, Blocked)
    assert {cause.code for cause in negative.causes} == {CauseCode.INVALID_COMPUTED_SIGN}
    assert Report("bounded", (negative,), ()).invalid
    zero = computed(item, 0, ("GUESS",), (), ())
    assert isinstance(zero, Computed) and zero.value == 0


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), True, "8"])
def test_nonfinite_and_bad_types_are_integrity_errors(scenario, parameters, bad):
    with pytest.raises(ValueError, match="non-finite|expected a finite number"):
        calculate(replace(scenario, stack_current_A=bad), parameters, scope="bounded")


def test_nonfinite_computation_is_not_backlog(scenario, parameters):
    with pytest.raises(ValueError, match="non-finite"):
        calculate(replace(scenario, el_ac_input_power_W=1e308), parameters, scope="bounded")


def test_numeric_backlog_placeholder_is_unavailable_not_adapter_blocked(
    monkeypatch, scenario, parameters,
):
    registry_entry(monkeypatch, "el.n_cells", value=0, status="BACKLOG")
    copied = ParamSet.from_registry(("el.n_cells", "el.faradaic_efficiency"))
    result = calculate(scenario, copied, scope="bounded")["hydrogen_amount_mol"]
    assert isinstance(result, Blocked)
    assert {cause.code for cause in result.causes} == {CauseCode.UNAVAILABLE_PARAMETER}


def test_unknown_evidence_is_definition_error_not_backlog(monkeypatch, scenario, parameters):
    registry_entry(monkeypatch, "el.n_cells", status="UNKNOWN")
    with pytest.raises(ValueError, match="not in the D26 vocabulary"):
        calculate(scenario, ParamSet.from_registry(("el.n_cells", "el.faradaic_efficiency")),
                  scope="bounded")


def test_sum_roles_units_duplicate_and_blocking(scenario, parameters):
    report = calculate(scenario, parameters, scope="bounded")
    keys = ("el_operating_energy_kWh", "el_standby_energy_kWh")
    assert sum_compatible(report, keys) == pytest.approx(1.585, rel=1e-12)
    with pytest.raises(ValueError, match="accounting roles"):
        sum_compatible(report, ("el_operating_energy_kWh", "hydrogen_lhv_energy_kWh"))
    with pytest.raises(ValueError, match="incompatible units"):
        sum_compatible(report, ("hydrogen_mass_kg", "hydrogen_amount_mol"))
    with pytest.raises(ValueError, match="unique"):
        sum_compatible(report, ("el_operating_energy_kWh", "el_operating_energy_kWh"))
    with pytest.raises(ValueError, match="nonempty"):
        sum_compatible(report, ())
    missing = calculate(replace(scenario, standby_time_s=None), parameters, scope="bounded")
    assert isinstance(sum_compatible(missing, keys), Blocked)


def test_invalid_scope_provenance_units_and_requested_parameters(monkeypatch, scenario, parameters):
    with pytest.raises(ValueError, match="unknown declared scope"):
        calculate(scenario, parameters, scope="invented")
    with pytest.raises(ValueError, match="provenance"):
        replace(scenario, provenance="")
    with monkeypatch.context() as patch:
        registry_entry(patch, "el.n_cells", unit="W")
        with pytest.raises(ValueError, match="expected unit"):
            calculate(scenario, ParamSet.from_registry(("el.n_cells", "el.faradaic_efficiency")),
                      scope="bounded")
    with pytest.raises(KeyError):
        calculate(scenario, ParamSet.from_registry(("el.n_cells",)), scope="bounded")


def test_direct_paramset_injection_rejected_but_individual_params_replaceable(parameters):
    forged = replace(parameters["el.n_cells"], value=121)
    assert forged.value == 121
    with pytest.raises(TypeError):
        ParamSet((forged,))
    with pytest.raises(TypeError):
        ParamSet(parameters=(forged,))
    with pytest.raises(TypeError, match="from_registry"):
        ParamSet()
    with pytest.raises(TypeError):
        replace(parameters, parameters=(forged,))
    requested = ParamSet.from_registry(("el.n_cells",))
    assert tuple(p.key for p in requested.parameters) == ("el.n_cells",)
    assert requested["el.n_cells"].value == 120


def test_signed_storage_change_and_nonnegative_energy_follow_d31():
    storage = next(item for item in ITEMS if item.key == "storage_change_kWh")
    assert storage.sign == Sign.SIGNED
    change = computed(storage, -1, ("GUESS",), (), ())
    assert isinstance(change, Computed)
    assert change.value == -1

    energy = Item("synthetic_path_energy_kWh", "kWh", Role.ELECTRICAL_INPUT, ())
    assert energy.sign == Sign.NONNEGATIVE
    negative = computed(energy, -1, ("GUESS",), (), ())
    assert isinstance(negative, Blocked)
    assert {cause.code for cause in negative.causes} == {CauseCode.INVALID_COMPUTED_SIGN}
    assert Report("bounded", (negative,), ()).invalid


@pytest.mark.parametrize("key,unit", [
    ("storage_change_mol", "mol"),
    ("difference_kWh", "kWh"),
    ("relative_pressure_bar", "bar"),
    ("differential_pressure_bar", "bar"),
])
def test_other_d31_signed_quantities_use_explicit_classification(key, unit):
    item = Item(key, unit, Role.STORAGE, (), sign=Sign.SIGNED)
    result = computed(item, -1, ("GUESS",), (), ())
    assert isinstance(result, Computed)
    assert result.value == -1


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), True, "8"])
def test_signed_does_not_bypass_data_integrity(bad):
    storage = next(item for item in ITEMS if item.key == "storage_change_kWh")
    with pytest.raises(ValueError, match="non-finite|expected a finite number"):
        computed(storage, bad, ("GUESS",), (), ())
