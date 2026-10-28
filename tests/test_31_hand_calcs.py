"""LAYER 2 - independent hand calculations vs. workbook column O.

Every expected value is computed HERE from physical definitions and from
inputs read out of the workbook; no project model is imported (Rule 4).
Tolerance = half a unit in the last printed digit of the workbook number
(pure rounding), never a fitted band. Reading-error bands (+-25 NL/min for
the digitised charts) are the workbook's own stated uncertainty.

INDEPENDENCE CAVEAT: the formulas were written by the same author as the
review. A second person/tool must re-derive them (see the cross-check sheet).
"""
import math
import re
import sys
from decimal import Decimal

import xlsx_reader as X

P_N_BAR = 1.01325          # normal pressure, bar abs (ISO 2533 / DIN 1343)
T_N_K = 273.15
T_REF_K = 293.15           # 20 degC, stated in the workbook texts D10/D133/D169
K = X.by_key()


def O(key):
    v = K[key]["O"]
    assert v is not None, f"{key}: no numeric value"
    return v


def half_ulp(printed):
    """Half unit of the last printed decimal digit; safe for e-notation (1e-05)."""
    exp = Decimal(repr(printed)).as_tuple().exponent
    return 0.5 * 10 ** (exp if exp < 0 else 0)


def close(actual, key_or_value, tol=None):
    exp = O(key_or_value) if isinstance(key_or_value, str) else key_or_value
    t = half_ulp(exp) if tol is None else tol
    assert abs(actual - exp) <= t + 1e-12, f"{key_or_value}: hand={actual:.6g} xlsx={exp} tol={t}"


def gas_nl_per_dstroke(v_l, p_in_barg):
    """H2 (normal litres) delivered per double stroke at eta_vol = 1."""
    return v_l * (p_in_barg + P_N_BAR) / P_N_BAR * (T_N_K / T_REF_K)


def air_nl_per_dstroke(i, v_l, pl_barg):
    """Drive air (normal litres) per double stroke: drive piston = i x gas displacement."""
    return i * v_l * (pl_barg + P_N_BAR) / P_N_BAR * (T_N_K / T_REF_K)


# ---------- Kaeser / basis -------------------------------------------------
def test_fad_to_nm3():
    close((1 / P_N_BAR) * (T_N_K / T_REF_K), "sys.f_fad_to_nm3")


def test_kaeser_normal_flow():
    f = (1 / P_N_BAR) * (T_N_K / T_REF_K)
    close(O("kaeser.q_fad_m3min") * f * 60, "kaeser.q_nm3h")
    close(O("kaeser.q_fad_m3min") * f, 0.616, tol=0.0005)       # printed 0.616 Nm3/min


def test_motor_input_power_at_rated_point():
    close(O("kaeser.motor.p_out_kw") / O("kaeser.motor.eta"), "kaeser.motor.p_in_rated_kw")


def test_sc2_power_upper_bound():
    close(24 * O("kaeser.sc2_current_a"), "kaeser.p_sc2_max_w")


def test_specific_air_energy_dealer_basis():
    e_fad = O("kaeser.p_package_dealer_kw") / (O("kaeser.q_fad_m3min") * 60)
    close(e_fad, 0.154)
    close(e_fad / ((1 / P_N_BAR) * (T_N_K / T_REF_K)), "energy.e_air_kwh_nm3")


# ---------- HULC stall (zero flow) -----------------------------------------
# CAVEAT: pB = i*pL + pA is an UNVERIFIED manufacturer rule (row hulc.stall_formula);
# its pressure basis (gauge vs absolute) is not stated. These tests prove the table is
# the correct application of that rule, not that the rule is right.
def stall_tank_barg(pl):
    """Stage-wise force balance; every input is read from workbook keys, none typed in."""
    pa_in = O("sys.p_h2_in_barg")                                    # stage-1 inlet
    p_inter = min(O("hulc.m140.limits"), O("hulc.s1.i") * pl + pa_in)
    return min(O("hulc.m400.limits"), O("hulc.s2.i") * pl + p_inter)


# Literal hand results (15*pL+35 capped at 140; 30*pL + that, capped at 400).
STALL_BY_HAND = {6: 305, 7: 350, 8: 380, 9: 400, 10: 400}


def test_stall_table_against_hand_literals():
    for pl, val in STALL_BY_HAND.items():
        assert stall_tank_barg(pl) == val, pl


def test_stall_table_matches_workbook():
    for pl, key in [(6, "hulc.stall_tank_pl6_barg"), (7, "hulc.stall_tank_pl7_barg"),
                    (8, "hulc.stall_tank_pl8_barg"), (9, "hulc.stall_tank_pl9_barg"),
                    (10, "hulc.stall_tank_pl10_barg")]:
        close(stall_tank_barg(pl), key, tol=0)


def test_stall_formula_text_still_the_one_reviewed():
    """Drift detector only (the same string is pinned in test_30); NOT evidence of correctness."""
    f = {f"D{r}": c.get("D", "") for r, c in X.master().items()}
    expect = "min(400, 30*pL + min(140, 15*pL + 35))"
    for ref in ("D119", "D120", "D121", "D122", "D123"):
        assert expect in f[ref], f"{ref}: {f[ref]}"


def test_pl_for_400_bar():
    close((O("hulc.m400.limits") - O("hulc.m140.limits")) / O("hulc.s2.i"), "hulc.pl_for_400_bar")


def test_module_limits_inside_booster_limits():
    assert O("hulc.m140.limits") <= O("hulc.s1.pb_max_bar")
    assert O("hulc.m400.limits") <= O("hulc.s2.pb_max_bar")
    assert O("hulc.pl_for_400_bar") <= O("hulc.pl_max_bar")


# ---------- Path B (geometry) ----------------------------------------------
# pI (interstage pressure) is NOT measured: hulc.p_interstage_bar is 'not available'.
# The workbook picks pI per row; it is encoded in the row title, parsed here, not typed.
def row_pi_barg(key):
    m = re.search(r"pI (\d+)", K[key]["B"])
    assert m, f"{key}: no pI in row title"
    return float(m.group(1))


def pathB_ratio(pl, pi_barg, p_in_barg=35):
    """Air per H2, from a stroke balance: stage 2 makes one stroke while stage 1 makes
    n1 = h2_s2 / h2_s1 strokes (mole balance through the interstage)."""
    v1, v2 = O("hulc.s1.v_disp_cm3") / 1000, O("hulc.s2.v_disp_cm3") / 1000
    i1, i2 = O("hulc.s1.i"), O("hulc.s2.i")
    h1 = gas_nl_per_dstroke(v1, p_in_barg)
    h2 = gas_nl_per_dstroke(v2, pi_barg)
    n1 = h2 / h1
    return (n1 * air_nl_per_dstroke(i1, v1, pl) + air_nl_per_dstroke(i2, v2, pl)) / h2


def test_pathB_gas_per_stroke():
    v1, v2 = O("hulc.s1.v_disp_cm3") / 1000, O("hulc.s2.v_disp_cm3") / 1000
    close(gas_nl_per_dstroke(v1, 35), "hulc.airB.s1_nl_per_dstroke")
    close(gas_nl_per_dstroke(v2, row_pi_barg("hulc.airB.ratio_pl6")), 13.91)
    close(gas_nl_per_dstroke(v2, 140), "hulc.airB.s2_nl_per_dstroke")


def test_pathB_ratios_at_the_pI_stated_in_each_row():
    close(pathB_ratio(6, row_pi_barg("hulc.airB.ratio_pl6")), "hulc.airB.ratio_pl6")
    close(pathB_ratio(9, row_pi_barg("hulc.airB.ratio_pl9")), "hulc.airB.ratio_pl9")


def test_pathB_is_a_lower_bound_for_every_pI_up_to_the_stated_one():
    """The ratio falls monotonically with pI, so the workbook's 'lower bound' label holds
    only for pI <= stated pI. Range start = lowest stage-2 inlet pressure from the workbook."""
    lo = int(O("hulc.s2.pa_min_bar"))
    for pl, key in ((6, "hulc.airB.ratio_pl6"), (9, "hulc.airB.ratio_pl9")):
        top = int(row_pi_barg(key))
        values = [pathB_ratio(pl, p) for p in range(lo, top + 1)]
        assert all(a > b for a, b in zip(values, values[1:])), "not monotone in pI"
        assert min(values) >= O(key) - half_ulp(O(key))


def test_pathB_above_stated_pI_is_NOT_a_lower_bound():
    """Documents the boundary: at pI = 140 for the pL 6 row the ratio is below the stored 4.59."""
    assert pathB_ratio(6, 140) < O("hulc.airB.ratio_pl6")


# ---------- Path A (chart) ---------------------------------------------------
def interp(points, x):
    xs = sorted(points)
    for a, b in zip(xs, xs[1:]):
        if a <= x <= b:
            return points[a] + (points[b] - points[a]) * (x - a) / (b - a)
    raise ValueError("outside digitised range")


M140 = {10: 150, 50: 280, 80: 380, 100: 475, 200: 900}
M400 = {10: 350, 50: 600, 80: 800, 100: 975, 200: 1750}


def test_pathA_digitised_points_match_text():
    c128, c129 = K["hulc.airA.m140_curve"]["C"], K["hulc.airA.m400_curve"]["C"]
    for h2, air in M140.items():
        assert f"{h2}->{air}" in c128
    for h2, air in M400.items():
        assert f"{h2}->{air}" in c129


def test_pathA_interpolation_within_stated_reading_band():
    q = 5000 / 60                           # 5 Nm3/h in NL/min
    band = 25                               # workbook: 'Reading +-~25 NL/min'
    assert abs(interp(M140, q) - 390) <= band
    assert abs(interp(M400, q) - 825) <= band
    assert abs(interp(M140, q) + interp(M400, q) - O("hulc.airA.q_air_at_qmax_nlmin")) <= 2 * band


def test_pathA_ratio():
    close(O("hulc.airA.q_air_at_qmax_nlmin") / (5000 / 60), "hulc.airA.ratio_nm3_per_nm3", tol=0.05)


# ---------- energy chain & capacity -----------------------------------------
def test_isothermal_work():
    def w(p_out_barg, p_in_barg=35):
        # W per Nm3: p_N * V_N * (T/T_N) * ln(p2/p1), V_N = 1 m3
        j = P_N_BAR * 1e5 * (T_REF_K / T_N_K) * math.log((p_out_barg + P_N_BAR) / (p_in_barg + P_N_BAR))
        return j / 3.6e6
    close(w(300), "energy.w_iso_35_300_kwh_nm3")
    close(w(400), "energy.w_iso_35_400_kwh_nm3")


def test_hulc_electric_per_nm3():
    # tol 0.005 = half unit of the printed O; actual deviation of the rounded chain: 0.0028 / 0.0011
    e = O("energy.e_air_kwh_nm3")
    close(O("hulc.airA.ratio_nm3_per_nm3") * e, "energy.hulc_A_kwh_nm3", tol=0.005)
    close(O("hulc.airB.ratio_pl6") * e, "energy.hulc_B_kwh_nm3", tol=0.005)
    close(O("hulc.airB.ratio_pl9") * e, 1.06, tol=0.005)


def test_capacity_check():
    close(O("hulc.airA.ratio_nm3_per_nm3") * 5, 73, tol=0.5)
    close(O("cap.supply_nm3h") / O("hulc.airA.ratio_nm3_per_nm3"), "cap.hulc_A_h2_max_nm3h", tol=0.05)
    close(O("hulc.airB.ratio_pl6") * 5, 23, tol=0.5)
    close(O("hulc.airB.ratio_pl9") * 5, "cap.hulc_B_air_nm3h", tol=0.05)
    assert O("hulc.airA.ratio_nm3_per_nm3") * 5 > O("cap.supply_nm3h")      # A: supply-limited
    assert O("hulc.airB.ratio_pl9") * 5 < O("cap.supply_nm3h")              # B: not limited


# ---------- Rotex ------------------------------------------------------------
def test_rotex_air_per_actuation():
    out = O("rotex.air_out_l_anr_per_bar")
    p = O("rotex.p_max_bar")                 # 8 bar plate maximum
    assert abs(out * p - 0.88) < 0.005           # gauge rule
    close(out * (p + 1), "rotex.v_per_actuation_8bar_l_anr")    # gauge+1 rule: 0.99
    assert "0.88" in K["rotex.v_per_actuation_8bar_l_anr"]["C"]


