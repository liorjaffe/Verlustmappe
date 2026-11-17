"""Separate hypothetical HULC air-related energy scenario; not a ledger item."""

from dataclasses import dataclass
import math

from ..physics.constants import J_PER_KWH
from ..devices.h2_compressor import AirCurve, chart_air_demand_NL_min
from ..accounting.validity import check_nonnegative


@dataclass(frozen=True)
class KaeserScenario:
    h2_flow_NL_min: float
    module_140: AirCurve
    module_400: AirCurve
    nominal_air_flow_NL_min: float
    reference_power_W: float
    operating_time_s: float
    reference_source: str
    assume_module_addition: bool


@dataclass(frozen=True)
class ScenarioResult:
    inputs: KaeserScenario
    hulc_air_flow_NL_min: float
    scenario_energy_kWh: float
    status: str
    notes: tuple[str, ...]


def _finite_nonnegative(value: float, name: str) -> float:
    if not check_nonnegative(value, name):
        raise ValueError(f"{name}: must be nonnegative")
    return float(value)


def calculate(scenario: KaeserScenario) -> ScenarioResult:
    """Return a conditional scenario, or raise ValueError without a numeric result."""
    h2_flow_NL_min = _finite_nonnegative(scenario.h2_flow_NL_min, "H2 flow NL/min")
    nominal_NL_min = _finite_nonnegative(scenario.nominal_air_flow_NL_min, "nominal air flow NL/min")
    power_W = _finite_nonnegative(scenario.reference_power_W, "reference power W")
    time_s = _finite_nonnegative(scenario.operating_time_s, "operating time s")
    if nominal_NL_min == 0:
        raise ValueError("nominal air flow must be positive")
    if not isinstance(scenario.reference_source, str) or not scenario.reference_source.strip():
        raise ValueError("reference source must be a nonempty string")
    air_NL_min = chart_air_demand_NL_min(
        h2_flow_NL_min, scenario.module_140, scenario.module_400,
        assume_module_addition=scenario.assume_module_addition,
        nominal_air_flow_NL_min=nominal_NL_min,
    )
    energy_kWh = power_W * time_s / J_PER_KWH * (air_NL_min / nominal_NL_min)
    if not math.isfinite(energy_kWh):
        raise ValueError("scenario energy must be finite")
    return ScenarioResult(
        scenario, air_NL_min, energy_kWh, "HYPOTHETICAL / UNVERIFIED",
        (
            "Not a measurement, actual energy allocation, ledger value, or physical bound.",
            "Scenario energy = reference power x operating time x HULC air flow / nominal delivery.",
            "Nominal delivery is not measured total air flow; compatible volume bases are unverified.",
            "Example sources conflict: dealer power at 11 bar versus manufacturer delivery at 10 bar.",
            "Chart applicability, module addition and dryer inclusion are unverified.",
            "READY, network leakage, Rotex, other consumers and startup are outside this calculation, not measured as zero.",
            "Demand below nominal delivery does not establish sufficient supply.",
        ),
    )
