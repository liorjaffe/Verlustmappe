"""Registry entries equal their workbook row (transfer of value, unit, status; not truth).

Scope per DECISIONS D15: registered are the workbook statuses Datasheet, Nameplate,
Datasheet (base type), Project decision, Dealer. Calculated/Observed rows stay workbook-only.
"""
import os
import sys

import xlsx_reader as X

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

# Longest prefix first: 'Datasheet (base type)' must not be swallowed by 'Datasheet'.
STATUS_MAP = {
    "Datasheet (base type)": "DATASHEET",
    "Project decision": "OWNER_DECISION",
    "Dealer": "DATASHEET_SECONDARY",
    "Nameplate": "DATASHEET",  # AGENTS.md: a nameplate value is a DATASHEET value
    "Datasheet": "DATASHEET",
}
UNIT_ALIASES = {("bar", "barg")}  # D15: gauge convention, assumption P-2

REGISTRY_KEY_MAP = {k: k for k in [
    "sys.n_rotex", "sys.p_h2_out_project_barg", "sys.p_h2_out_nameplate_barg", "sys.p_h2_in_barg",
    "hulc.mod.q_h2_max_nm3h", "hulc.m140.limits", "hulc.m400.limits",
    "kaeser.p_rated_nameplate_kw", "kaeser.q_fad_m3min", "kaeser.p_package_dealer_kw",
]}
REGISTRY_KEY_MAP.update({"hulc.pl_max_bar": "hulc.pl_max_barg", "kaeser.ps_bar": "kaeser.ps_barg"})
for _s in ("s1", "s2"):
    for _f in ("i", "v_disp_cm3", "f_max_min"):
        REGISTRY_KEY_MAP[f"hulc.{_s}.{_f}"] = f"hulc.{_s}.{_f}"
    for _f in ("pa_min", "pb_max"):
        REGISTRY_KEY_MAP[f"hulc.{_s}.{_f}_bar"] = f"hulc.{_s}.{_f}_barg"

# Datasheet-class rows deliberately NOT registered in P05. Calculated/Observed rows need no entry.
NOT_REGISTERED = {k: "not registered in P05 (workbook-only, D15 scope)" for k in [
    "kaeser.supply", "kaeser.i_full_load_a", "kaeser.motor.p_out_kw", "kaeser.motor.eta",
    "kaeser.sc2_current_a", "kaeser.v_receiver_l", "kaeser.has_idle",
    "kaeser.dryer.p_kw", "kaeser.dryer.pdp_c", "kaeser.dryer.dp_bar",
    "hulc.air_prep.p_max_bar", "hulc.sys.p_electric_kw", "hulc.mod.air_ref_condition",
    "hulc.h2_ratio_limit", "hulc.leak_hp_seal_frac", "hulc.airA.el21_nlmin",
    "rotex.p_max_bar", "rotex.air_out_l_anr_per_bar", "rotex.air_in_l_anr_per_bar",
    "rotex.weight_kg", "rotex.life_cycles", "reg.harris.kv",
]}
NOT_REGISTERED["hulc.s1.eps_max"] = "value 20 is for other gases; H2 limit unconfirmed"
NOT_REGISTERED["hulc.s2.eps_max"] = "value 20 is for other gases; H2 limit unconfirmed"


def status_prefix(status):
    s = status.strip().lower()
    for prefix in STATUS_MAP:
        if s.startswith(prefix.lower()):
            return prefix
    return None


def numeric_keys():
    return {k: d for k, d in X.by_key().items()
            if d["O"] is not None and not d["F"].strip().lower().startswith("open")}


def is_workbook_only_status(status):
    return status.strip().lower().startswith(("calculated", "observed"))


def test_map_is_not_empty():
    assert len(REGISTRY_KEY_MAP) == 22


def test_every_numeric_row_is_mapped_or_excluded():
    missing = [k for k, d in numeric_keys().items()
               if k not in REGISTRY_KEY_MAP and k not in NOT_REGISTERED
               and not is_workbook_only_status(d["F"])]
    assert not missing, f"unclassified numeric rows: {missing}"


def test_exclusion_lists_have_no_stale_or_overlapping_keys():
    wb = numeric_keys()
    assert set(REGISTRY_KEY_MAP) <= set(wb), set(REGISTRY_KEY_MAP) - set(wb)
    assert set(NOT_REGISTERED) <= set(wb), set(NOT_REGISTERED) - set(wb)
    assert not set(REGISTRY_KEY_MAP) & set(NOT_REGISTERED)


def test_mapped_rows_have_a_decided_status():
    wb = numeric_keys()
    bad = [k for k in REGISTRY_KEY_MAP if status_prefix(wb[k]["F"]) is None]
    assert not bad, f"mapped rows with status not in STATUS_MAP: {bad}"


def test_value_unit_status_equal():
    from verlustmappe import registry as R
    wb = numeric_keys()
    for xk, rk in REGISTRY_KEY_MAP.items():
        d, e = wb[xk], R.entry(rk)
        assert abs(e["value"] - d["O"]) <= 1e-12 * max(1, abs(d["O"])), f"{xk}: value"
        assert e["unit"] == d["P"] or (d["P"], e["unit"]) in UNIT_ALIASES, \
            f"{xk}: unit workbook={d['P']!r} registry={e['unit']!r}"
        assert e["status"] == STATUS_MAP[status_prefix(d["F"])], f"{xk}: status {e['status']}"


def test_no_registry_entry_without_a_workbook_row():
    from verlustmappe import registry as R
    mapped = set(REGISTRY_KEY_MAP.values())
    new = [k for k in R.REGISTRY
           if k.split(".")[0] in ("kaeser", "hulc", "rotex", "sys", "cap", "energy") and k not in mapped]
    assert not new, new
