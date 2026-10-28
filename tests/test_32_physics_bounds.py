"""LAYER 3 - physical plausibility bounds, independent of vendor numbers.

These can FAIL for a physically impossible dataset even when every number was
transcribed correctly. They encode inequalities (2nd law, eta_vol <= 1,
stroke-rate limit), not point values.

Independence: this file has its OWN data access and its OWN physics, written via
mole amounts (n = pV/RT) instead of the ratio formulas used in test_31. Only
test_dual_implementations_agree imports test_31, and only to compare.

No threshold in this file is invented: every bound is an inequality that follows
from physics, or a value read from the workbook (Rule 8).
"""
import math
import re
import sys

import xlsx_reader as X

K = X.by_key()
R_GAS = 8.314462618        # J/(mol K), CODATA 2018 (exact in the 2019 SI)
P_N = 101325.0             # Pa, normal pressure
T_N = 273.15               # K
T_REF = 293.15             # K, 20 degC (stated in workbook formulas D133/D169)


def O(key):
    v = K[key]["O"]
    assert v is not None, f"{key}: no numeric value"
    return v


def mol(p_abs_bar, v_litre, t_k=T_REF):
    return p_abs_bar * 1e5 * v_litre * 1e-3 / (R_GAS * t_k)


def normal_litres(n_mol):
    return n_mol * R_GAS * T_N / P_N * 1e3


def w_iso_kwh_per_nm3(p_out_barg, p_in_barg=35):
    n_per_nm3 = P_N * 1.0 / (R_GAS * T_N)
    joule = n_per_nm3 * R_GAS * T_REF * math.log((p_out_barg + 1.01325) / (p_in_barg + 1.01325))
    return joule / 3.6e6


def path_b_ratio(pl, pi_barg):
    """Air per H2 via mole amounts: drive piston displaces i x gas volume at pL."""
    v1, v2 = O("hulc.s1.v_disp_cm3") / 1000, O("hulc.s2.v_disp_cm3") / 1000
    i1, i2 = O("hulc.s1.i"), O("hulc.s2.i")
    h1 = mol(35 + 1.01325, v1)
    h2 = mol(pi_barg + 1.01325, v2)
    air_mol = (h2 / h1) * mol(pl + 1.01325, i1 * v1) + mol(pl + 1.01325, i2 * v2)
    return normal_litres(air_mol) / normal_litres(h2)


def test_second_law_floor_for_every_air_path():
    """Electrical kWh per Nm3 H2 must exceed the isothermal compression work."""
    floor = w_iso_kwh_per_nm3(300)
    for key in ("energy.hulc_A_kwh_nm3", "energy.hulc_B_kwh_nm3"):
        assert O(key) > floor, f"{key}={O(key)} <= isothermal floor {floor:.4f}"


def test_implied_isothermal_efficiency_is_between_0_and_1():
    for key in ("energy.hulc_A_kwh_nm3", "energy.hulc_B_kwh_nm3"):
        assert 0 < w_iso_kwh_per_nm3(300) / O(key) < 1


def test_kaeser_shaft_below_electrical_input():
    """Physical order only: motor output < motor input; no invented spread limit."""
    assert O("kaeser.motor.p_out_kw") < O("kaeser.motor.p_in_rated_kw")
    assert 0.5 < O("kaeser.motor.eta") < 1.0       # a motor, not a heater or a perpetuum mobile


def test_dryer_power_is_positive_and_below_package_power():
    """Strict inequality only. 'Dryer included in dealer power' is an open question, so
    the upper bound is the package, not a made-up percentage."""
    assert 0 < O("kaeser.dryer.p_kw") < O("kaeser.p_package_dealer_kw")


def test_pathB_not_above_pathA():
    """B is a geometric lower bound (no pilot/purge air); A is a chart value."""
    assert O("hulc.airB.ratio_pl9") < O("hulc.airA.ratio_nm3_per_nm3")


def test_pathB_monotone_in_drive_pressure():
    r = [path_b_ratio(pl, 140) for pl in (4, 6, 8, 10)]
    assert all(a < b for a, b in zip(r, r[1:]))


def test_required_stroke_rate_below_frequency_limit():
    q_nl_min = O("hulc.mod.q_h2_max_nm3h") * 1000 / 60
    for stage, pin in (("s1", 35), ("s2", 140)):
        v = O(f"hulc.{stage}.v_disp_cm3") / 1000
        strokes = q_nl_min / normal_litres(mol(pin + 1.01325, v))
        assert strokes < O(f"hulc.{stage}.f_max_min")


def test_catalog_flow_points_below_geometric_maximum():
    """eta_vol <= 1: a catalogue flow can never exceed displacement x f_max.
    WEAK sanity bound (about 2x above the catalogue values); pA taken as absolute
    (the smaller bound), so it holds for either reading."""
    pts = {"s1": [(15, 200), (15, 130), (34, 500), (34, 400)],
           "s2": [(22, 145), (22, 105), (50, 355), (50, 290)]}
    for stage, lst in pts.items():
        v = O(f"hulc.{stage}.v_disp_cm3") / 1000
        f = O(f"hulc.{stage}.f_max_min")
        for pa, flow in lst:
            geo = normal_litres(mol(pa, v)) * f
            assert flow < geo, f"{stage} pA={pa}: {flow} >= {geo:.0f}"


def test_catalog_flow_points_text_matches_test_data():
    assert "pA15/pB40: 200" in K["hulc.s1.flow_points"]["C"]
    assert "pA50/pB120: 290" in K["hulc.s2.flow_points"]["C"]


def test_stroke_counters_are_flagged_as_undefined_evidence():
    """The workbook says the count definition is open. While that holds, the counters
    are NOT physical evidence and no assertion may be built on them. If this fails,
    the definition was closed: write the real counter test then."""
    for key in ("hulc.s1.counter_delta", "hulc.s2.counter_delta"):
        assert "definition" in K[key]["G"].lower(), key


def test_tank_limit_vs_stall_capability():
    """Stall at pL=9 exceeds the 300 bar tank limit: a shut-off/relief MUST bound it."""
    assert O("hulc.stall_tank_pl9_barg") > O("hulc.tank_limit_bar")


def test_kaeser_supply_below_hulc_A_demand_flagged():
    assert O("cap.hulc_A_h2_max_nm3h") < O("hulc.mod.q_h2_max_nm3h")


def test_rotex_pressure_not_above_any_quoted_limit():
    """Take every 'x bar' quoted in the same cell instead of a typed constant."""
    quoted = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?) bar", K["rotex.p_max_bar"]["C"])]
    assert quoted and O("rotex.p_max_bar") <= min(quoted)


def test_hulc_drive_air_below_booster_limit():
    assert O("hulc.air_prep.p_static_obs_bar") <= O("hulc.pl_max_bar")
    assert O("kaeser.p_operating_bar") <= O("kaeser.ps_bar")


def test_dual_implementations_agree():
    """The mole-based physics here must agree with the ratio formulas in test_31.
    Disagreement means one of the two derivations is wrong."""
    import test_31_hand_calcs as T21
    for pl, pi in ((6, 125), (9, 140), (6, 140)):
        assert abs(path_b_ratio(pl, pi) - T21.pathB_ratio(pl, pi)) < 1e-4
    assert abs(w_iso_kwh_per_nm3(300) - 0.0641) < 5e-5
    assert abs(w_iso_kwh_per_nm3(400) - 0.0728) < 5e-5


