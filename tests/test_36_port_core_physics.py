"""P11: ported constants and fill work, params adapter.

Expected values are the P10 hand values (tests/reference/hand/), not model output. The legacy
comparison is the regression required by AGENTS (ported physics exists twice until M6).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import pytest

# Hand values, tests/reference/hand/isothermal_work.md (B, T = 293.15 K, mol delivered)
HAND_B_RT = {(1.0, 2.0): 0.386294, (40.0, 200.0): 1.011797,
             (36.01325, 141.01325): 0.833128, (36.01325, 301.01325): 1.411817}
R_HAND = 8.31446261815324   # k_B * N_A, hand/constants.md
KWH_PER_J = 1.0 / 3.6e6


def test_work_matches_hand_values():
    from verlustmappe.models.temperature_model import isothermal_fill_work_kWh
    for (p1, p2), f in HAND_B_RT.items():
        expected_kWh = f * R_HAND * 293.15 * KWH_PER_J   # per mol
        assert isothermal_fill_work_kWh(1.0, p1, p2, 293.15).work_kWh == pytest.approx(expected_kWh, rel=1e-6), (p1, p2)


def test_bovo_point_hand_value():
    from verlustmappe.models.temperature_model import isothermal_fill_work_kWh
    n_mol = 33.22e3 / 22.41397
    assert isothermal_fill_work_kWh(n_mol, 40.0, 200.0, 293.15).work_kWh == pytest.approx(1.0153037, rel=1e-5)


def test_work_matches_legacy():
    from verlustmappe.models.temperature_model import isothermal_fill_work_kWh
    from verlustmappe.hydrogen.temperature_model import isothermal_work_mol_integral as legacy
    cases = [(1000.0, 20.0, 200.0, 293.15, None), (1000.0, 100.0, 200.0, 293.15, 35.0),
             (1000.0, 20.0, 200.0, 293.15, 35.0), (500.0, 10.0, 30.0, 300.0, 40.0),
             (500.0, 50.0, 40.0, 293.15, None), (500.0, 20.0, 30.0, 293.15, 35.0)]
    for mol, p1, p2, T, ps in cases:
        assert isothermal_fill_work_kWh(mol, p1, p2, T, ps).work_kWh == pytest.approx(legacy(mol, p1, p2, T, ps), rel=1e-12, abs=0)


def test_exact_zero_is_flagged():
    from verlustmappe.models.temperature_model import isothermal_fill_work_kWh
    for args in [(500.0, 50.0, 40.0, 293.15, None), (500.0, 20.0, 30.0, 293.15, 35.0)]:
        r = isothermal_fill_work_kWh(*args)
        assert r.work_kWh == 0.0 and r.exactly_zero and r.reason
    r = isothermal_fill_work_kWh(500.0, 20.0, 200.0, 293.15)
    assert r.work_kWh > 0 and not r.exactly_zero and r.reason == ""
    with pytest.raises(Exception):
        r.work_kWh = 1.0   # frozen


def test_work_domain_errors():
    from verlustmappe.models.temperature_model import isothermal_fill_work_kWh
    with pytest.raises(ValueError):
        isothermal_fill_work_kWh(1.0, 20.0, float("nan"), 293.15)
    with pytest.raises(ValueError):
        isothermal_fill_work_kWh(1.0, 20.0, 200.0, 293.15, p_suction_abs_bar=0.0)


def test_constants_match_legacy_and_hand():
    from verlustmappe.models import constants as N
    from verlustmappe import constants as L
    for name in ("M_H2_KG_PER_MOL", "F_C_PER_MOL", "R_J_PER_MOL_K", "V_MOL_NL_PER_MOL", "RHO_H2_KG_PER_NL",
                 "LHV_H2_KWH_PER_KG", "HHV_H2_KWH_PER_KG", "LHV_H2_WH_PER_NL", "HHV_H2_WH_PER_NL",
                 "J_PER_KWH", "J_PER_WH", "PA_PER_BAR", "P_ATM_BAR"):
        assert getattr(N, name) == getattr(L, name), name
    # hand/constants.md
    assert N.R_J_PER_MOL_K == pytest.approx(8.31446261815324, rel=1e-9)
    assert N.F_C_PER_MOL == pytest.approx(96485.33212331, rel=2e-9)
    assert N.V_MOL_NL_PER_MOL == pytest.approx(22.41397, rel=2e-6)
    assert N.RHO_H2_KG_PER_NL == pytest.approx(8.99439e-5, rel=2e-6)
    assert N.LHV_H2_KWH_PER_KG == pytest.approx(119.96 / 3.6, rel=1e-5)
    assert N.LHV_H2_WH_PER_NL == pytest.approx(2.99713, rel=2e-5)


def test_barg_to_abs():
    from verlustmappe.models.constants import barg_to_abs_bar
    assert barg_to_abs_bar(0.0) == 1.01325
    assert barg_to_abs_bar(35.0) == pytest.approx(36.01325, abs=1e-12)
    assert barg_to_abs_bar(300.0) == pytest.approx(301.01325, abs=1e-12)


def test_adapter_blocks_rejected_and_passes_status():
    from verlustmappe.models.params import get_param, BlockedParameterError, Param
    with pytest.raises(BlockedParameterError):
        get_param("comp.overall_efficiency")
    with pytest.raises(KeyError):
        get_param("does.not.exist")
    p = get_param("kaeser.p_package_dealer_kw")   # u = 0.0 stays readable, status is passed on
    assert isinstance(p, Param) and p.status and p.uncertainty == 0.0
    with pytest.raises(Exception):
        p.value = 0   # frozen


def test_adapter_blocks_every_rejected_or_superseded_entry():
    # D28: general guard now that the adapter exists (test_34 covers comp.* only)
    from verlustmappe import registry as R
    from verlustmappe.models.params import get_param, BlockedParameterError
    blocked = [k for k, v in R.REGISTRY.items() if v["status"] in ("REJECTED", "SUPERSEDED")]
    assert len(blocked) >= 6   # the six comp.* keys at 2026-10-28
    for k in blocked:
        with pytest.raises(BlockedParameterError):
            get_param(k)
    for k, v in R.REGISTRY.items():
        if v["status"] not in ("REJECTED", "SUPERSEDED"):
            assert get_param(k).status == v["status"], k


def test_adapter_does_not_write_back():
    from verlustmappe import registry as R
    from verlustmappe.models.params import get_param
    before = dict(R.REGISTRY["el.n_cells"])
    get_param("el.n_cells")
    assert R.REGISTRY["el.n_cells"] == before


def test_new_core_imports_no_legacy_except_registry_in_params():
    legacy = r"(hydrogen|devices|balance|analysis|loaders|uncertainty|reporting|conversions|live_feed|constants)"
    pat = re.compile(rf"^\s*(from\s+\.\.\s*(import\s+)?{legacy}\b|from\s+verlustmappe\.{legacy}\b|import\s+verlustmappe\.{legacy}\b)", re.M)
    base = os.path.join(ROOT, "src", "verlustmappe", "models")
    for f in os.listdir(base):
        if f.endswith(".py"):
            text = open(os.path.join(base, f)).read()
            assert not pat.search(text), f
    params = open(os.path.join(base, "params.py")).read()
    assert "from .. import registry" in params
