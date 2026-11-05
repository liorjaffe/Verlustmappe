"""Pure bounded EL scenario; no measurement-data imports or access (P14)."""

from dataclasses import dataclass, fields

from ..physics.constants import F_C_PER_MOL, J_PER_KWH, LHV_H2_KWH_PER_KG, M_H2_KG_PER_MOL
from .ledger import (
    BOUNDED_KEYS, ITEMS, Blocked, Cause, CauseCode, Computed, InputUncertainty,
    Report, Result, computed,
)
from .params import ParamSet
from .validity import check_nonnegative


def _number(value: object, key: str) -> float:
    check_nonnegative(value, key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key}: expected a finite number")
    return float(value)


@dataclass(frozen=True)
class Scenario:
    el_ac_input_power_W: float | None
    stack_current_A: float | None
    operating_time_s: float | None
    el_ac_standby_power_W: float | None
    standby_time_s: float | None
    provenance: str

    def __post_init__(self) -> None:
        if not isinstance(self.provenance, str) or not self.provenance.strip():
            raise ValueError("scenario provenance must be a nonempty string")


def calculate(scenario: Scenario, parameters: ParamSet, *, scope: str) -> Report:
    if scope not in ("bounded", "full"):
        raise ValueError(f"unknown declared scope: {scope!r}")

    values: dict[str, float] = {}
    causes: dict[str, tuple[Cause, ...]] = {}
    metadata: dict[str, tuple[str, str, str]] = {}
    bands: dict[str, float | None] = {}
    for field in fields(scenario):
        key = field.name
        if key == "provenance":
            continue
        value = getattr(scenario, key)
        metadata[key] = ("GUESS", "NOT ASSESSED", scenario.provenance)
        bands[key] = None
        if value is None:
            causes[key] = (Cause(CauseCode.MISSING_REQUIRED_INPUT, key,
                                 "required scenario input is absent"),)
        elif not check_nonnegative(value, key):
            causes[key] = (Cause(CauseCode.INVALID_INPUT_DOMAIN, key,
                                 "scenario input must be nonnegative; zero is valid"),)
        else:
            values[key] = _number(value, key)

    for key, unit in (("el.n_cells", "-"), ("el.faradaic_efficiency", "-")):
        parameter = parameters[key]
        if parameter.unit != unit:
            raise ValueError(f"{key}: expected unit {unit!r}, got {parameter.unit!r}")
        metadata[key] = (parameter.status, parameter.u_class, f"registry:{key}")
        bands[key] = parameter.uncertainty
        if parameter.status == "BACKLOG":
            causes[key] = (Cause(CauseCode.UNAVAILABLE_PARAMETER, key,
                                 "BACKLOG placeholder is not an available required value"),)
        elif not check_nonnegative(parameter.value, key):
            causes[key] = (Cause(CauseCode.INVALID_INPUT_DOMAIN, key,
                                 "registry input is outside its permitted nominal domain"),)
        elif key == "el.faradaic_efficiency" and parameter.value > 1:
            causes[key] = (Cause(CauseCode.INVALID_INPUT_DOMAIN, key,
                                 "registry input is outside its permitted nominal domain"),)
        elif key == "el.n_cells" and (
                parameter.value <= 0 or parameter.value % 1 != 0):
            causes[key] = (Cause(CauseCode.INVALID_INPUT_DOMAIN, key,
                                 "registry input is outside its permitted nominal domain"),)
        else:
            values[key] = _number(parameter.value, key)

    results: list[Result] = []
    for item in ITEMS:
        if scope == "bounded" and item.key not in BOUNDED_KEYS:
            continue
        if item.unresolved:
            results.append(Blocked(item, item.unresolved))
            continue
        blocked = tuple(cause for key in item.dependencies for cause in causes.get(key, ()))
        if blocked:
            result: Result = Blocked(item, blocked)
        else:
            if item.key == "el_operating_energy_kWh":
                value = values["el_ac_input_power_W"] * values["operating_time_s"] / J_PER_KWH
            elif item.key == "el_standby_energy_kWh":
                value = values["el_ac_standby_power_W"] * values["standby_time_s"] / J_PER_KWH
            elif item.key == "hydrogen_amount_mol":
                value = (values["el.faradaic_efficiency"] * values["el.n_cells"]
                         * values["stack_current_A"] * values["operating_time_s"]
                         / (2 * F_C_PER_MOL))
            elif item.key == "hydrogen_mass_kg":
                value = values["hydrogen_amount_mol"] * M_H2_KG_PER_MOL
            elif item.key == "hydrogen_lhv_energy_kWh":
                value = values["hydrogen_mass_kg"] * LHV_H2_KWH_PER_KG
            else:
                raise ValueError(f"no computation for declared item {item.key}")
            inputs = tuple((key, metadata[key]) for key in item.dependencies)
            uncertainties = tuple(InputUncertainty(key, data[1], bands[key])
                                  for key, data in inputs)
            provenance = tuple((key, data[2]) for key, data in inputs)
            # Derived dependencies retain the original input metadata, not an output u-class.
            for previous in results:
                if previous.item.key in item.dependencies and isinstance(previous, Computed):
                    uncertainties = previous.input_uncertainties
                    provenance = previous.provenance
            result = computed(item, value, tuple(data[0] for _, data in inputs),
                              uncertainties, provenance)
        results.append(result)
        if isinstance(result, Blocked):
            causes[item.key] = (
                Cause(CauseCode.BLOCKED_DEPENDENCY, item.key, "dependency is unquantified"),
                *result.causes,
            )
        else:
            values[item.key] = result.value
            metadata[item.key] = (result.evidence_status, "NOT ASSESSED", "derived")
            bands[item.key] = None

    return Report(scope, tuple(results), (
        "Bounded scenario is not full-chain AC1 or AC8 acceptance; no RTE or balance proof.",
        "No output uncertainty propagation, complete loss total, ranking or Sankey.",
        "Measurement-independent pure input path; no measurement-access boundary exists. "
        "No measurement data-path perturbation has been exercised.",
        "AC operating power and DC current are distinct; constant, non-overlapping periods.",
    ))
