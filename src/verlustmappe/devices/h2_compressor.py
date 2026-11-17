"""Air-driven HULC hydrogen compressor: two Maximator booster stages.

Stage 1 is HULC 140 / DLE15-H2; stage 2 is HULC 400 / DLE 30-H2.
This model estimates ideal work for the overall pressure change; it does not
model the two stages separately.

The boosters are driven by compressed air supplied by the electric Kaeser.
Kaeser electricity is an auxiliary consumption; its HULC share requires
allocation because the compressor also supplies other consumers.

  W_ideal = n R T ln(p2/p1)          minimum work (isothermal, IDEAL gas)
  eta_overall = W_ideal / E_air_compressor
Real-gas note: for H2 at 35->200 bar the ideal formula underestimates the true
work by ~5-8% (Z > 1). That error is inside the eta_overall GUESS band and is
documented here rather than corrected, because the GUESS dominates by an order
of magnitude. If the booster is ever metered, switch W to the real-gas form
(integral V dp with Z(p,T)).
The registered eta_overall is REJECTED (D11, wrong device basis DLE 30-2) and is
used ONLY so the frozen legacy-1.0 chain reproduces; see docs/94 C11.
Until E_air_compressor is metered, E is estimated as W_ideal / eta_GUESS.
"""
from dataclasses import dataclass
import math

from .. import registry as R
from ..physics import constants as C
from ..physics.conversions import isothermal_work_kWh, NL_to_mol
from ..hydrogen.temperature_model import isothermal_work_mol_integral


@dataclass(frozen=True)
class AirCurve:
    basis: str
    source: str
    points_NL_min: tuple[tuple[float, float], ...]


def _curve_number(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: expected a finite number")
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name}: expected a finite nonnegative number")
    return float(value)


def _air_at_flow_NL_min(curve: AirCurve, h2_flow_NL_min: float) -> float:
    if not isinstance(curve.basis, str) or not curve.basis.strip():
        raise ValueError("curve basis must be a nonempty string")
    if not isinstance(curve.source, str) or not curve.source.strip():
        raise ValueError("curve source must be a nonempty string")
    if len(curve.points_NL_min) < 2:
        raise ValueError("curve requires at least two points")
    points = tuple(
        (_curve_number(h2, "curve H2 flow NL/min"),
         _curve_number(air, "curve air flow NL/min"))
        for h2, air in curve.points_NL_min
    )
    if any(a[0] >= b[0] for a, b in zip(points, points[1:])):
        raise ValueError("curve H2 flows must be strictly increasing")
    if h2_flow_NL_min < 10:
        raise ValueError("H2 flow below 10 NL/min: chart extrapolation is not allowed")
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if x1 <= h2_flow_NL_min <= x2:
            return y1 + (y2 - y1) * (h2_flow_NL_min - x1) / (x2 - x1)
    raise ValueError("H2 flow outside supplied chart range: extrapolation is not allowed")


def chart_air_demand_NL_min(
    h2_flow_NL_min: float, module_140: AirCurve, module_400: AirCurve, *,
    assume_module_addition: bool, nominal_air_flow_NL_min: float,
) -> float:
    """Conditional curve sum, separate from AirDrivenBooster's energy path.

    The owner-approved scenario guards (decision 2026-11-17) prohibit
    extrapolation below 10 NL/min H2 and output above nominal air delivery.
    They are not confirmed physical plant limits. Applicability, module
    addition and volume-basis compatibility remain UNVERIFIED.
    """
    if assume_module_addition is not True:
        raise ValueError("module addition requires an explicit True assumption")
    flow_NL_min = _curve_number(h2_flow_NL_min, "H2 flow NL/min")
    nominal_NL_min = _curve_number(nominal_air_flow_NL_min, "nominal air flow NL/min")
    if nominal_NL_min == 0:
        raise ValueError("nominal air flow must be positive")
    if module_140.basis != module_400.basis:
        raise ValueError("module curve bases must match")
    air_NL_min = (_air_at_flow_NL_min(module_140, flow_NL_min)
                  + _air_at_flow_NL_min(module_400, flow_NL_min))
    if not math.isfinite(air_NL_min):
        raise ValueError("interpolated air flow must be finite")
    if air_NL_min > nominal_NL_min:
        raise ValueError("HULC air demand exceeds nominal delivery; no scenario result")
    return air_NL_min


class AirDrivenBooster:
    def account(self, throughput_NL, p_in_barg, p_out_barg, T_C=None, air_compressor_kWh=None,
                p_tank_start_barg=None, p_tank_end_barg=None):
        """Compressor work for moving throughput_NL of gas into storage.

        Since 2026-10 the ideal work uses the mole-weighted integral over the
        tank fill path (isothermal_work_mol_integral): the old single-shot
        formula nRT ln(p2/p1) applied at the arithmetic mean pressure overstated
        a 20->200 bar fill by ~21% and understated 100->200 bar by ~16%.
        Pass p_tank_start_barg / p_tank_end_barg (the storage window) and the
        integral runs against the suction pressure p_in_barg (EL output).
        Without a window the single-shot form at (p_in -> p_out) is kept, which
        is the correct assumption when all gas is compressed at once.
        Missing temperature uses stor.T_assumed_C (GUESS), not Pt100/telemetry."""
        temperature_is_assumed = T_C is None
        if temperature_is_assumed:
            T_C = R.get("stor.T_assumed_C")
        temperature = dict(
            T_used_C=T_C, temperature_is_assumed=temperature_is_assumed,
            temperature_source=R.entry("stor.T_assumed_C")["source"]
            if temperature_is_assumed else "explicitly supplied; not automatically measured",
            temperature_status="GUESS" if temperature_is_assumed else None)
        mol = NL_to_mol(throughput_NL)
        p_in_abs = p_in_barg + C.P_ATM_BAR
        p_out_abs = p_out_barg + C.P_ATM_BAR
        if p_tank_start_barg is not None and p_tank_end_barg is not None:
            w_ideal = isothermal_work_mol_integral(
                mol, p_tank_start_barg + C.P_ATM_BAR, p_tank_end_barg + C.P_ATM_BAR,
                T_C + 273.15, p_suction_abs_bar=p_in_abs)
            # consistency: if the throughput EXCEEDS what the tank window holds,
            # the surplus arrives before the window opens (or after it closes);
            # the honest floor is the work of the window mass itself.
            from ..physics.conversions import mol_from_pVT
            from ..hydrogen.z_realgas import z_h2 as _z
            p1a, p2a = p_tank_start_barg + C.P_ATM_BAR, p_tank_end_barg + C.P_ATM_BAR
            mol_window = (mol_from_pVT(p2a, R.get("stor.volume_L") / 1000.0,
                                       T_C + 273.15, _z(p2a, T_C))
                          - mol_from_pVT(p1a, R.get("stor.volume_L") / 1000.0,
                                         T_C + 273.15, _z(p1a, T_C)))
            if mol > mol_window > 0:
                w_ideal = isothermal_work_mol_integral(
                    mol_window, p1a, p2a, T_C + 273.15, p_suction_abs_bar=p_in_abs)
                mol = mol_window
                throughput_NL = mol_window * C.V_MOL_NL_PER_MOL
        elif p_out_abs > p_in_abs:
            w_ideal = isothermal_work_mol_integral(mol, p_in_abs, p_out_abs, T_C + 273.15)
        else:
            w_ideal = 0.0   # storage below suction pressure: no compression needed
        if air_compressor_kWh is not None:
            return dict(unit="CSU", ideal_work_kWh=w_ideal, energy_kWh=air_compressor_kWh,
                        overall_efficiency=w_ideal / air_compressor_kWh if air_compressor_kWh else None,
                        energy_is_measured=True, warning=None, **temperature)
        eta = R.get("comp.overall_efficiency")
        return dict(unit="CSU", ideal_work_kWh=w_ideal, energy_kWh=w_ideal / eta,
                    overall_efficiency=eta, energy_is_measured=False,
                    uncertainty_rel=R.entry("comp.overall_efficiency")["uncertainty"],
                    warning="compression energy = ideal work / REJECTED legacy efficiency (D11); meter the Kaeser (D14)",
                    **temperature)
