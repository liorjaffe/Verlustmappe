"""Independent storage temperature reference (owner-approved, 2026-11-13).

Basis: pV = ZnRT; the approved project approximation is
Z(T) = 1 + (Z20 - 1) * T0/T, with T0 = 293.15 K and Z20 = 1.192
at 300 bar ABSOLUTE. Z20 is the reviewed project-table anchor, not an
independently certified EOS datum. No implementation imports or outputs.

Substitution gives m(T) = A / [T + (Z20 - 1)*T0], A = pVM/R.
Thus d(ln m)/dT at T0 = -1/(Z20*T0). The ideal/fixed-Z reference
is -1/T0. These are LOCAL derivatives, not 20-to-21 C finite differences.

Owner uncertainty convention: a +/-10 K rectangular band gives
u_T = 10/sqrt(3) K. Fixed-Z first-order propagation gives u_T/T0.
For a fully common offset on both states this is also the APPROXIMATE
relative contribution for their difference; actual Z(T) dependence is
not included in that approved uncertainty approximation. Independent
3 K model allowance remains separate. No seasonal coverage is claimed.
"""

from decimal import Decimal, localcontext


with localcontext() as context:
    context.prec = 40
    TEMPERATURE_K = Decimal("293.15")
    Z20 = Decimal("1.192")
    BAND_K = Decimal("10")
    LOCAL_SENSITIVITY_PCT_PER_K = -Decimal(100) / (Z20 * TEMPERATURE_K)
    IDEAL_SENSITIVITY_PCT_PER_K = -Decimal(100) / TEMPERATURE_K
    STANDARD_TEMPERATURE_UNCERTAINTY_K = BAND_K / Decimal(3).sqrt()
    TEMPERATURE_UNCERTAINTY_REL = STANDARD_TEMPERATURE_UNCERTAINTY_K / TEMPERATURE_K
    MODEL_ALLOWANCE_REL = Decimal(3) / TEMPERATURE_K
    # Independent 50 -> 150 barg Route 2 example: pressure errors 2 bar each,
    # common volume u=0.005, Z-table u=0.01 amplified by p_end/pressure swing.
    PRESSURE_UNCERTAINTY_REL = Decimal(2) * Decimal(2).sqrt() / Decimal(100)
    Z_UNCERTAINTY_REL = Decimal("0.01") * Decimal("151.01325") / Decimal(100)
    ROUTE2_UNCERTAINTY_REL = (
        PRESSURE_UNCERTAINTY_REL**2 + Decimal("0.005")**2
        + Z_UNCERTAINTY_REL**2 + MODEL_ALLOWANCE_REL**2
        + TEMPERATURE_UNCERTAINTY_REL**2
    ).sqrt()


if __name__ == "__main__":
    for name in (
        "LOCAL_SENSITIVITY_PCT_PER_K", "IDEAL_SENSITIVITY_PCT_PER_K",
        "STANDARD_TEMPERATURE_UNCERTAINTY_K", "TEMPERATURE_UNCERTAINTY_REL",
        "MODEL_ALLOWANCE_REL", "ROUTE2_UNCERTAINTY_REL",
    ):
        print(f"{name} = {globals()[name]}")
