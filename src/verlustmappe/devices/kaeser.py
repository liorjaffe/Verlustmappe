"""Conditional dry ideal-gas FAD conversion; no compressor energy model.

Plant values and their source conflicts remain in plant/kaeser.toml. Delivery
pressure is not the inlet/reference pressure used in this volume conversion.
"""

import math


def fad_to_normal_NL_min(
    fad_flow_m3_min: float, *, inlet_pressure_abs_bar: float,
    inlet_temperature_K: float, normal_pressure_abs_bar: float,
    normal_temperature_K: float,
) -> float:
    """Convert dry FAD using Q_N = Q_FAD * p_in/p_N * T_N/T_in.

    All reference conditions must be supplied. Humidity and real-gas effects
    are excluded; this does not establish compatibility with a HULC chart or
    delivery at a different operating pressure.
    """
    for name, value in (
        ("fad_flow_m3_min", fad_flow_m3_min),
        ("inlet_pressure_abs_bar", inlet_pressure_abs_bar),
        ("inlet_temperature_K", inlet_temperature_K),
        ("normal_pressure_abs_bar", normal_pressure_abs_bar),
        ("normal_temperature_K", normal_temperature_K),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name}: expected a finite number")
        if not math.isfinite(value) or value < 0 or (name != "fad_flow_m3_min" and value == 0):
            raise ValueError(f"{name}: invalid flow or absolute reference condition")
    flow_NL_min = (fad_flow_m3_min * 1000 * inlet_pressure_abs_bar
                   / normal_pressure_abs_bar * normal_temperature_K / inlet_temperature_K)
    if not math.isfinite(flow_NL_min):
        raise ValueError("normal flow must be finite")
    return flow_NL_min
