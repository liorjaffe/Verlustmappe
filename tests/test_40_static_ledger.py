"""P14 ledger: independent dependency, domain, immutability and accounting checks."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from verlustmappe import registry
from verlustmappe.models.ledger import (
    ITEMS, Blocked, Cause, CauseCode, Computed, Item, Report, Role, Sign, computed, sum_compatible,
)
from verlustmappe.models.params import BlockedParameterError, ParamSet
from verlustmappe.models.static_map import Scenario, calculate


@pytest.fixture
def parameters():
    return ParamSet.from_registry(("el.n_cells", "el.faradaic_efficiency"))


@pytest.fixture
def scenario():
    return Scenario(2100, 8, 2700, 20, 1800, "owner-approved synthetic P14 case")


@pytest.mark.parametrize("case", ["empty_full", "relabeled_bounded", "thinned_bounded"])
def test_required_item_absence_invalidates_report(scenario, parameters, case):
    bounded = calculate(scenario, parameters, scope="bounded")
    bounded_keys = {
        "el_operating_energy_kWh", "el_standby_energy_kWh",
        "hydrogen_amount_mol", "hydrogen_mass_kg", "hydrogen_lhv_energy_kWh",
    }
    full_additional_required = {
        "dryer_electrical_energy_kWh", "dryer_vent_energy_kWh", "water_energy_kWh",
        "filter_energy_kWh", "compression_air_energy_kWh", "ready_energy_kWh",
        "leakage_energy_kWh", "fc_control_energy_kWh", "fc_inverter_loss_kWh",
        "el_conversion_loss_kWh", "fc_conversion_loss_kWh", "storage_change_kWh",
    }
    if case == "empty_full":
        report = Report("full", (), ())
        missing = bounded_keys | full_additional_required
    elif case == "relabeled_bounded":
        report = replace(bounded, scope="full")
        missing = full_additional_required
    else:
        report = replace(bounded, results=bounded.results[:2])
        missing = {"hydrogen_amount_mol", "hydrogen_mass_kg", "hydrogen_lhv_energy_kWh"}
    assert report.invalid, f"{case}: absent required items must invalidate the report"
    assert {(cause.code.value, cause.dependency) for cause in report.validation_causes} == {
        ("missing_required_item", key) for key in missing
    }


@pytest.mark.parametrize("status", ["UNKNOWN", "REJECTED", "SUPERSEDED"])
@pytest.mark.parametrize("value", [-1, 0, 1])
def test_status_definition_error_precedes_negative_short_circuit(status, value):
    item = Item("synthetic_energy_kWh", "kWh", Role.ELECTRICAL_INPUT, ())
    with pytest.raises(ValueError, match="not in the D26 vocabulary"):
        computed(item, value, (status,), (), ())


def test_aggregate_preserves_all_blockers_and_identity(scenario, parameters):
    report = calculate(
        replace(scenario, el_ac_input_power_W=None, standby_time_s=None),
        parameters, scope="bounded",
    )
    keys = ("el_operating_energy_kWh", "el_standby_energy_kWh")
    forward = sum_compatible(report, keys)
    reverse = sum_compatible(report, tuple(reversed(keys)))
    assert isinstance(forward, Blocked) and isinstance(reverse, Blocked)
    expected_roots = {"el_ac_input_power_W", "standby_time_s"}
    for aggregate in (forward, reverse):
        assert {cause.dependency for cause in aggregate.causes
                if cause.code == CauseCode.MISSING_REQUIRED_INPUT} == expected_roots
        assert {cause.dependency for cause in aggregate.causes
                if cause.code == CauseCode.BLOCKED_DEPENDENCY} == set(keys)
        assert set(aggregate.item.dependencies) == set(keys)
        assert aggregate.item.key not in keys
        assert len(aggregate.causes) == len(set(aggregate.causes))
    assert forward.causes == reverse.causes
    assert forward.item == reverse.item


def test_inventory_requiredness_cannot_be_overridden_by_result(scenario, parameters):
    report = calculate(replace(scenario, stack_current_A=None), parameters, scope="bounded")
    results = tuple(replace(result, item=replace(result.item, required=False))
                    if isinstance(result, Blocked) else result for result in report.results)
    with pytest.raises(ValueError, match="central inventory"):
        replace(report, results=results)


def test_calculated_reports_have_complete_required_coverage(scenario, parameters):
    bounded = calculate(scenario, parameters, scope="bounded")
    full = calculate(scenario, parameters, scope="full")
    assert not bounded.validation_causes and not bounded.invalid
    assert not full.validation_causes and full.invalid
    conditional = "fc_inverter_standby_energy_kWh"
    without_conditional = replace(
        full, results=tuple(result for result in full.results if result.item.key != conditional),
    )
    assert not without_conditional.validation_causes


@pytest.mark.parametrize("values", [(-1, -1), (1, -2)])
def test_signed_sums_remain_numeric_without_sign_gate(values):
    items = tuple(Item(key, "kWh", Role.STORAGE, (), sign=Sign.SIGNED)
                  for key in ("first_change_kWh", "second_change_kWh"))
    results = tuple(computed(item, value, ("GUESS",), (), ())
                    for item, value in zip(items, values))
    assert all(isinstance(result, Computed) for result in results)
    report = Report("bounded", results, ())
    total = sum_compatible(report, ("first_change_kWh", "second_change_kWh"))
    assert isinstance(total, (int, float)) and not isinstance(total, bool)
    assert total == (-2 if values == (-1, -1) else -1)


@pytest.mark.parametrize("signed_key", ["first", "second"])
def test_blocked_aggregate_any_signed_and_shared_cause_deduplication(signed_key):
    items = tuple(
        Item(key, "kWh", Role.STORAGE, (),
             sign=Sign.SIGNED if key == signed_key else Sign.NONNEGATIVE)
        for key in ("first", "second")
    )
    cause = Cause(CauseCode.MISSING_REQUIRED_INPUT, "shared_input", "Missing shared input")
    report = Report("bounded", tuple(Blocked(item, (cause,)) for item in items), ())
    aggregate = sum_compatible(report, ("first", "second"))
    reverse = sum_compatible(report, ("second", "first"))
    assert isinstance(aggregate, Blocked) and isinstance(reverse, Blocked)
    assert aggregate == reverse
    assert aggregate.item.sign == Sign.SIGNED
    assert aggregate.causes.count(cause) == 1
    assert len(aggregate.causes) == 3


def test_inventory_signs_match_explicit_d31_requirements():
    assert {item.key: item.sign for item in ITEMS} == {
        "el_operating_energy_kWh": Sign.NONNEGATIVE,
        "el_standby_energy_kWh": Sign.NONNEGATIVE,
        "hydrogen_amount_mol": Sign.NONNEGATIVE,
        "hydrogen_mass_kg": Sign.NONNEGATIVE,
        "hydrogen_lhv_energy_kWh": Sign.NONNEGATIVE,
        "dryer_electrical_energy_kWh": Sign.NONNEGATIVE,
        "dryer_vent_energy_kWh": Sign.NONNEGATIVE,
        "water_energy_kWh": Sign.NONNEGATIVE,
        "filter_energy_kWh": Sign.NONNEGATIVE,
        "compression_air_energy_kWh": Sign.NONNEGATIVE,
        "ready_energy_kWh": Sign.NONNEGATIVE,
        "leakage_energy_kWh": Sign.NONNEGATIVE,
        "fc_control_energy_kWh": Sign.NONNEGATIVE,
        "fc_inverter_loss_kWh": Sign.NONNEGATIVE,
        "fc_inverter_standby_energy_kWh": Sign.NONNEGATIVE,
        "el_conversion_loss_kWh": Sign.NONNEGATIVE,
        "fc_conversion_loss_kWh": Sign.NONNEGATIVE,
        "storage_change_kWh": Sign.SIGNED,
    }


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


@pytest.mark.parametrize("first", [True, False])
@pytest.mark.parametrize("kind", ["computed_and_blocked", "different_values", "identical"])
def test_report_rejects_duplicate_result_keys(scenario, parameters, kind, first):
    bounded = calculate(scenario, parameters, scope="bounded")
    original = bounded["el_operating_energy_kWh"]
    if kind == "computed_and_blocked":
        duplicate = Blocked(original.item, (Cause(
            CauseCode.MISSING_REQUIRED_INPUT, "el_ac_input_power_W", "Duplicate entry"),))
    elif kind == "different_values":
        duplicate = replace(original, value=999.0)
    else:
        duplicate = original
    results = (duplicate,) + bounded.results if first else bounded.results + (duplicate,)
    with pytest.raises(ValueError, match="duplicate.*el_operating_energy_kWh"):
        Report("bounded", results, ())


@pytest.mark.parametrize("key,change", [
    ("el_operating_energy_kWh", {"sign": Sign.SIGNED}),
    ("hydrogen_mass_kg", {"dependencies": ()}),
    ("hydrogen_amount_mol", {"unit": "kmol"}),
    ("hydrogen_lhv_energy_kWh", {"role": Role.LOSS}),
    ("storage_change_kWh", {"required": False}),
    ("fc_inverter_standby_energy_kWh", {"condition": ""}),
    ("dryer_electrical_energy_kWh", {"unresolved": ()}),
])
def test_report_rejects_noncanonical_known_item_definition(scenario, parameters, key, change):
    full = calculate(scenario, parameters, scope="full")
    results = tuple(replace(result, item=replace(result.item, **change))
                    if result.item.key == key else result for result in full.results)
    with pytest.raises(ValueError, match=f"{key}.*central inventory"):
        Report("full", results, ())


def test_report_rejects_signed_redefinition_carrying_negative_energy(scenario, parameters):
    bounded = calculate(scenario, parameters, scope="bounded")
    signed = replace(bounded["el_operating_energy_kWh"].item, sign=Sign.SIGNED)
    negative = computed(signed, -1, ("GUESS",), (), ())
    assert isinstance(negative, Computed)
    results = tuple(negative if result.item.key == signed.key else result
                    for result in bounded.results)
    with pytest.raises(ValueError, match="el_operating_energy_kWh.*central inventory"):
        Report("bounded", results, ())


@pytest.mark.parametrize("required", [True, False])
def test_unknown_extra_item_stays_visible_and_only_required_blocker_invalidates(
        scenario, parameters, required):
    bounded = calculate(scenario, parameters, scope="bounded")
    assert not bounded.invalid
    extra = Blocked(
        Item("synthetic_extra_kWh", "kWh", Role.LOSS, ("synthetic_basis",), required=required),
        (Cause(CauseCode.UNRESOLVED_BASIS, "synthetic_basis", "Synthetic extra item"),),
    )
    report = Report("bounded", bounded.results + (extra,), ())
    assert not report.validation_causes
    assert report["synthetic_extra_kWh"] == extra
    assert report.invalid is required


def _plain_cause_codes(item):
    return replace(item, unresolved=tuple(replace(cause, code=cause.code.value)
                                          for cause in item.unresolved))


@pytest.mark.parametrize("key,retype", [
    pytest.param("el_operating_energy_kWh",
                 lambda item: replace(item, sign=item.sign.value), id="sign_as_str"),
    pytest.param("hydrogen_lhv_energy_kWh",
                 lambda item: replace(item, role=item.role.value), id="role_as_str"),
    pytest.param("el_standby_energy_kWh",
                 lambda item: replace(item, required=int(item.required)), id="required_as_int"),
    pytest.param("dryer_electrical_energy_kWh", _plain_cause_codes, id="cause_code_as_str"),
])
def test_report_rejects_equal_but_retyped_known_item(scenario, parameters, key, retype):
    full = calculate(scenario, parameters, scope="full")
    canonical = next(item for item in ITEMS if item.key == key)
    retyped = retype(canonical)
    assert retyped == canonical, "precondition: Python equality alone accepts the retyped item"
    results = tuple(replace(result, item=retyped) if result.item.key == key else result
                    for result in full.results)
    with pytest.raises(ValueError, match=f"{key}.*central inventory"):
        Report("full", results, ())


def test_doubled_operating_time_doubles_electrical_and_faraday_results(scenario, parameters):
    baseline = calculate(scenario, parameters, scope="bounded")
    doubled = calculate(
        replace(scenario, operating_time_s=2 * scenario.operating_time_s),
        parameters, scope="bounded",
    )
    for key in (
        "el_operating_energy_kWh", "hydrogen_amount_mol",
        "hydrogen_mass_kg", "hydrogen_lhv_energy_kWh",
    ):
        base_result = baseline[key]
        doubled_result = doubled[key]
        assert isinstance(base_result, Computed)
        assert isinstance(doubled_result, Computed)
        assert doubled_result.value / base_result.value == pytest.approx(
            2.0, rel=1e-14, abs=0.0,
        )


def test_zero_operating_time_zeros_electrical_and_faraday_results(scenario, parameters):
    zero = calculate(replace(scenario, operating_time_s=0), parameters, scope="bounded")
    for key in (
        "el_operating_energy_kWh", "hydrogen_amount_mol",
        "hydrogen_mass_kg", "hydrogen_lhv_energy_kWh",
    ):
        zero_result = zero[key]
        assert isinstance(zero_result, Computed)
        assert zero_result.value == 0


def test_negative_registry_parameter_has_exact_domain_cause_and_propagates(
        monkeypatch, scenario):
    registry_entry(monkeypatch, "el.faradaic_efficiency", value=-0.98)
    parameters = ParamSet.from_registry(("el.n_cells", "el.faradaic_efficiency"))
    report = calculate(scenario, parameters, scope="bounded")
    assert report.invalid
    for key in ("hydrogen_amount_mol", "hydrogen_mass_kg", "hydrogen_lhv_energy_kWh"):
        result = report[key]
        assert isinstance(result, Blocked)
        assert any(cause.code == CauseCode.INVALID_INPUT_DOMAIN
                   and cause.dependency == "el.faradaic_efficiency"
                   for cause in result.causes)


@pytest.mark.parametrize(
    "key",
    ["el.n_cells", "el.faradaic_efficiency"],
)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param("not-a-number", id="string"),
        pytest.param(True, id="true"),
        pytest.param(False, id="false"),
        pytest.param(float("nan"), id="nan"),
        pytest.param(float("inf"), id="positive-infinity"),
        pytest.param(float("-inf"), id="negative-infinity"),
    ],
)
def test_non_numeric_boolean_and_nonfinite_registry_parameters_raise_value_error(
        scenario, key, value):
    original = deepcopy(registry.REGISTRY[key])
    try:
        registry.REGISTRY[key]["value"] = value
        parameters = ParamSet.from_registry(("el.n_cells", "el.faradaic_efficiency"))
        with pytest.raises(ValueError):
            calculate(scenario, parameters, scope="bounded")
    finally:
        registry.REGISTRY[key] = original


def test_report_rejects_invalid_scope_with_complete_results(scenario, parameters):
    bounded = calculate(scenario, parameters, scope="bounded")
    assert not bounded.invalid
    with pytest.raises(ValueError, match="unknown declared scope"):
        Report("invented", bounded.results, bounded.limits)


def test_aggregate_rejects_overflow_from_finite_results(scenario, parameters):
    bounded = calculate(scenario, parameters, scope="bounded")
    first = Item("finite_large_a_kWh", "kWh", Role.ELECTRICAL_INPUT, ())
    second = Item("finite_large_b_kWh", "kWh", Role.ELECTRICAL_INPUT, ())
    first_result = computed(first, 1e308, ("GUESS",), (), ())
    second_result = computed(second, 1e308, ("GUESS",), (), ())
    assert isinstance(first_result, Computed) and math.isfinite(first_result.value)
    assert isinstance(second_result, Computed) and math.isfinite(second_result.value)
    report = Report("bounded", bounded.results + (first_result, second_result), ())
    assert not report.invalid
    with pytest.raises(ValueError, match="non-finite"):
        sum_compatible(report, (first.key, second.key))


@pytest.mark.parametrize("statuses", [(), ("OWNER_DECISION",)])
@pytest.mark.parametrize("value", [-1.0, 1.0])
def test_computed_requires_evidence_status_before_sign_handling(statuses, value):
    item = next(item for item in ITEMS if item.key == "el_operating_energy_kWh")
    with pytest.raises(ValueError, match="D26"):
        computed(item, value, statuses, (), ())


def test_inventory_item_keys_are_unique():
    keys = tuple(item.key for item in ITEMS)
    assert len(keys) == len(set(keys))
