"""D26 uncertainty classification (u = 0.0): expected sets are hand-listed, not computed by u_class.

Pinned counts change only together with a DECISIONS entry (registry change, AGENTS rule 2).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

# D26(b): OWNER_DECISION entries and the two TOLERANCE_BAND keys (2026-10-28)
EXACT_KEYS = {
    "sys.n_rotex",
    "sys.p_h2_out_project_barg",
    "meas.p_sensor_fso_bar",
    "meas.p_sensor_thermal_bar_per_10K",
}


def _classes(registry):
    from verlustmappe.reporting.make_register import u_class
    return {k: u_class(k, v) for k, v in registry.items()}


def test_exact_set_is_exactly_the_four_entries():
    from verlustmappe import registry as R
    cls = _classes(R.REGISTRY)
    assert {k for k, c in cls.items() if c == "exact"} == EXACT_KEYS


def test_exact_and_assessed_are_bijective_with_u():
    from verlustmappe import registry as R
    cls = _classes(R.REGISTRY)
    for k in EXACT_KEYS:
        assert R.REGISTRY[k]["uncertainty"] == 0.0, k
    for k, v in R.REGISTRY.items():
        if v["uncertainty"] > 0:
            assert cls[k] == "assessed", k
        else:
            assert cls[k] in ("exact", "NOT ASSESSED"), k


def test_pinned_counts():
    from verlustmappe import registry as R
    cls = _classes(R.REGISTRY)
    assert len(cls) == 109
    assert sum(c == "assessed" for c in cls.values()) == 46
    assert sum(c == "exact" for c in cls.values()) == 4
    assert sum(c == "NOT ASSESSED" for c in cls.values()) == 59


def test_known_not_assessed_entries():
    from verlustmappe import registry as R
    cls = _classes(R.REGISTRY)
    assert cls["fc.poc_max_duration_s"] == "NOT ASSESSED"  # DERIVED alone is not exact (D26)
    assert cls["kaeser.p_package_dealer_kw"] == "NOT ASSESSED"
    assert cls["comp.pressure_ratio"] == "NOT ASSESSED"  # REJECTED entries are classified too


def test_synthetic_entries_on_a_local_copy():
    from verlustmappe.reporting.make_register import u_class
    base = {"unit": "-", "source": "x", "effect": "x"}
    assert u_class("a.b", {**base, "value": 1, "status": "DATASHEET", "uncertainty": 0.1}) == "assessed"
    assert u_class("a.b", {**base, "value": 1, "status": "DATASHEET", "uncertainty": 0.0}) == "NOT ASSESSED"
    assert u_class("a.b", {**base, "value": 1, "status": "DERIVED", "uncertainty": 0.0}) == "NOT ASSESSED"
    assert u_class("a.b", {**base, "value": 1, "status": "OWNER_DECISION", "uncertainty": 0.0}) == "exact"
    assert u_class("a.b", {**base, "value": 1, "status": "OWNER_DECISION", "uncertainty": 0.2}) == "assessed"
