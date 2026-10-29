"""Central P14 item inventory and explicit computed/blocked results (D35)."""

from dataclasses import dataclass, field
from enum import Enum

from .status import weakest
from .validity import check_nonnegative


class Role(str, Enum):
    ELECTRICAL_INPUT = "electrical_input"
    TRANSPORT = "transport"
    LOSS = "loss"
    AMOUNT = "amount"
    MASS = "mass"
    STORAGE = "storage"


class Sign(str, Enum):
    """D31 classification: path quantities versus signed changes/differences."""

    NONNEGATIVE = "nonnegative"
    SIGNED = "signed"


class CauseCode(str, Enum):
    MISSING_REQUIRED_INPUT = "missing_required_input"
    MISSING_REQUIRED_ITEM = "missing_required_item"
    BLOCKED_DEPENDENCY = "blocked_dependency"
    INVALID_INPUT_DOMAIN = "invalid_input_domain"
    INVALID_COMPUTED_SIGN = "invalid_computed_sign"
    UNRESOLVED_BASIS = "unresolved_basis"
    UNAVAILABLE_PARAMETER = "unavailable_parameter"


@dataclass(frozen=True)
class Cause:
    code: CauseCode
    dependency: str
    reason: str


@dataclass(frozen=True)
class Item:
    key: str
    unit: str
    role: Role
    dependencies: tuple[str, ...]
    required: bool = True
    condition: str = ""
    unresolved: tuple[Cause, ...] = ()
    sign: Sign = Sign.NONNEGATIVE


def _pending(
    key: str, role: Role, *bases: tuple[str, str], condition: str = ""
) -> Item:
    return Item(
        key, "kWh", role, tuple(name for name, _ in bases),
        required=not bool(condition), condition=condition,
        unresolved=tuple(Cause(CauseCode.UNRESOLVED_BASIS, name, reason)
                         for name, reason in bases),
        sign=Sign.SIGNED if role == Role.STORAGE else Sign.NONNEGATIVE,
    )


ITEMS = (
    Item("el_operating_energy_kWh", "kWh", Role.ELECTRICAL_INPUT,
         ("el_ac_input_power_W", "operating_time_s")),
    Item("el_standby_energy_kWh", "kWh", Role.ELECTRICAL_INPUT,
         ("el_ac_standby_power_W", "standby_time_s")),
    Item("hydrogen_amount_mol", "mol", Role.AMOUNT,
         ("stack_current_A", "operating_time_s", "el.n_cells", "el.faradaic_efficiency")),
    Item("hydrogen_mass_kg", "kg", Role.MASS, ("hydrogen_amount_mol",)),
    Item("hydrogen_lhv_energy_kWh", "kWh", Role.TRANSPORT, ("hydrogen_mass_kg",)),
    _pending("dryer_electrical_energy_kWh", Role.LOSS,
             ("dryer_model", "DATASHEET registry labels; SOURCES missing; applicability unresolved")),
    _pending("dryer_vent_energy_kWh", Role.LOSS,
             ("dryer_vent_model", "Vent/regeneration basis and permitted inputs unresolved")),
    _pending("water_energy_kWh", Role.ELECTRICAL_INPUT,
             ("water_basis", "RO process and wall-clock standby basis unresolved")),
    _pending("filter_energy_kWh", Role.ELECTRICAL_INPUT,
             ("filter_basis", "Supported power/time basis missing; GUESS zero not authorized")),
    _pending("compression_air_energy_kWh", Role.ELECTRICAL_INPUT,
             ("D13", "Air demand and operating conditions unresolved"),
             ("D14", "Kaeser electrical input and allocation unresolved")),
    _pending("ready_energy_kWh", Role.ELECTRICAL_INPUT,
             ("D14_ready", "Separate READY standby basis and allocation unresolved")),
    _pending("leakage_energy_kWh", Role.LOSS,
             ("D14_leakage", "Distribution leakage basis unresolved; not assigned to HULC")),
    _pending("fc_control_energy_kWh", Role.ELECTRICAL_INPUT,
             ("D22_control", "Control-energy basis and DC-bus assumption unresolved; netting P15")),
    _pending("fc_inverter_loss_kWh", Role.LOSS,
             ("D22_inverter", "Terminal/control basis and inverter model unresolved")),
    _pending("fc_inverter_standby_energy_kWh", Role.ELECTRICAL_INPUT,
             ("D23_standby", "Measurement and applicability not established"),
             condition="once measured (D23); currently not established"),
    _pending("el_conversion_loss_kWh", Role.LOSS,
             ("el_loss_physics", "Independent EL loss physics absent; no residual substitute")),
    _pending("fc_conversion_loss_kWh", Role.LOSS,
             ("fc_loss_physics", "Independent FC loss physics absent; no residual substitute")),
    _pending("storage_change_kWh", Role.STORAGE,
             ("storage_model", "Process boundaries and gas-state reconciliation unresolved")),
)
BOUNDED_KEYS = tuple(item.key for item in ITEMS[:5])


@dataclass(frozen=True)
class InputUncertainty:
    key: str
    classification: str
    band: float | None


@dataclass(frozen=True)
class Computed:
    item: Item
    value: float
    evidence_status: str
    result_origin: str
    input_uncertainties: tuple[InputUncertainty, ...]
    provenance: tuple[tuple[str, str], ...]
    output_uncertainty_propagated: bool = False


@dataclass(frozen=True)
class Blocked:
    item: Item
    causes: tuple[Cause, ...]
    indication: str = "BACKLOG"


Result = Computed | Blocked


def computed(
    item: Item, value: float, statuses: tuple[str, ...],
    input_uncertainties: tuple[InputUncertainty, ...],
    provenance: tuple[tuple[str, str], ...],
) -> Result:
    if not isinstance(item.sign, Sign):
        raise ValueError(f"{item.key}: unknown D31 sign classification {item.sign!r}")
    evidence_status = weakest(statuses)
    nonnegative = check_nonnegative(value, item.key)
    if item.sign == Sign.NONNEGATIVE and not nonnegative:
        return Blocked(item, (Cause(CauseCode.INVALID_COMPUTED_SIGN, item.key,
                                   "D31 computed/modelled quantity is negative"),))
    return Computed(item, value, evidence_status, "SIMULATED",
                    input_uncertainties, provenance)


@dataclass(frozen=True)
class Report:
    scope: str
    results: tuple[Result, ...]
    limits: tuple[str, ...]
    validation_causes: tuple[Cause, ...] = field(init=False)

    def __post_init__(self) -> None:
        if self.scope not in ("bounded", "full"):
            raise ValueError(f"unknown declared scope {self.scope!r}")
        present = {result.item.key for result in self.results}
        missing = tuple(
            Cause(CauseCode.MISSING_REQUIRED_ITEM, item.key,
                  f"Required item is absent from {self.scope} report")
            for item in ITEMS
            if item.required and (self.scope == "full" or item.key in BOUNDED_KEYS)
            and item.key not in present
        )
        object.__setattr__(self, "validation_causes", missing)

    @property
    def invalid(self) -> bool:
        required = {item.key for item in ITEMS if item.required
                    and (self.scope == "full" or item.key in BOUNDED_KEYS)}
        return bool(self.validation_causes) or any(
            isinstance(result, Blocked)
            and (result.item.key in required or result.item.required)
            for result in self.results
        )

    def __getitem__(self, key: str) -> Result:
        for result in self.results:
            if result.item.key == key:
                return result
        raise KeyError(key)


def sum_compatible(report: Report, keys: tuple[str, ...]) -> float | Blocked:
    """Explicit, unique, same-role/unit leaves only; blockers survive aggregation."""
    if not keys or len(set(keys)) != len(keys):
        raise ValueError("aggregation requires nonempty, unique leaf keys")
    results = tuple(report[key] for key in keys)
    if len({(result.item.unit, result.item.role) for result in results}) != 1:
        raise ValueError("cannot aggregate incompatible units or accounting roles")
    blocked = tuple(result for result in results if isinstance(result, Blocked))
    if blocked:
        dependencies = tuple(sorted(keys))
        item = Item(
            f"aggregate:{dependencies!r}", results[0].item.unit, results[0].item.role,
            dependencies, required=any(result.item.required for result in results),
            sign=Sign.SIGNED if any(result.item.sign == Sign.SIGNED for result in results)
            else Sign.NONNEGATIVE,
        )
        causes = {cause for result in blocked for cause in result.causes}
        causes.update(
            Cause(CauseCode.BLOCKED_DEPENDENCY, result.item.key,
                  "Aggregate depends on blocked item")
            for result in blocked
        )
        return Blocked(item, tuple(sorted(
            causes, key=lambda cause: (cause.code.value, cause.dependency, cause.reason),
        )))
    total = sum(result.value for result in results if isinstance(result, Computed))
    check_nonnegative(total, "aggregate")
    return total
