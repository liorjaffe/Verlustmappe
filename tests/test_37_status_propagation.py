"""P12: status ranking, u class and weakest-wins in the new core (D26, D28).

Expected values come from the D26 text (hand-listed), not from the model. Parity with the legacy
register column is pinned per entry; the rule exists twice until the M6 teardown.
"""
import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

# D26(b): OWNER_DECISION entries and the two TOLERANCE_BAND keys
EXACT_KEYS = {
    "sys.n_rotex",
    "sys.p_h2_out_project_barg",
    "meas.p_sensor_fso_bar",
    "meas.p_sensor_thermal_bar_per_10K",
}


def test_ranking_order_matches_d26():
    from verlustmappe.models.status import EVIDENCE_ORDER
    assert EVIDENCE_ORDER == ("MEASURED", "CALIBRATED", "DATASHEET", "DATASHEET_SECONDARY",
                              "DERIVED", "PRELIM", "GUESS", "BACKLOG")


def test_weakest_of_mixed_lists():
    from verlustmappe.models.status import weakest
    assert weakest(["DATASHEET", "GUESS"]) == "GUESS"
    assert weakest(["DATASHEET", "GUESS", "BACKLOG"]) == "BACKLOG"
    assert weakest(["MEASURED", "DATASHEET_SECONDARY", "DATASHEET"]) == "DATASHEET_SECONDARY"
    assert weakest(["DERIVED"]) == "DERIVED"
    assert weakest(["PRELIM/ENVELOPE", "DERIVED"]) == "PRELIM"


def test_weakest_skips_owner_decision():
    from verlustmappe.models.status import weakest
    assert weakest(["OWNER_DECISION", "DATASHEET"]) == "DATASHEET"


def test_weakest_without_evidence_raises():
    from verlustmappe.models.status import weakest
    for empty in ([], ["OWNER_DECISION"], ["OWNER_DECISION", "OWNER_DECISION"]):
        with pytest.raises(ValueError, match="D26"):
            weakest(empty)


def test_unknown_status_raises_with_value():
    from verlustmappe.models.status import weakest, u_class
    with pytest.raises(ValueError, match="TYPO"):
        weakest(["DATASHEET", "TYPO"])
    with pytest.raises(ValueError, match="TYPO"):
        u_class("x", "TYPO", 0.1)
    with pytest.raises(ValueError, match="ENVELOPE"):
        weakest(["ENVELOPE"])


def test_weakest_rejects_blocked_statuses_with_value():
    from verlustmappe.models.status import weakest
    for bad in ("REJECTED", "SUPERSEDED"):
        with pytest.raises(ValueError, match=bad):
            weakest(["DATASHEET", bad])


def test_u_class_exact_set_and_bijection_with_u():
    from verlustmappe import registry as R
    from verlustmappe.models.status import u_class
    cls = {k: u_class(k, v["status"], v["uncertainty"]) for k, v in R.REGISTRY.items()}
    assert {k for k, c in cls.items() if c == "exact"} == EXACT_KEYS
    for k, c in cls.items():
        u = R.REGISTRY[k]["uncertainty"]
        assert (c == "assessed") == (u != 0.0)
        if c == "exact":
            assert u == 0.0


def test_u_class_derived_zero_is_not_assessed():
    from verlustmappe.models.status import u_class
    assert u_class("fc.poc_max_duration_s", "DERIVED", 0.0) == "NOT ASSESSED"
    assert u_class("any.key", "DERIVED", 0.0) == "NOT ASSESSED"
    assert u_class("any.key", "GUESS", 0.0) == "NOT ASSESSED"
    assert u_class("any.key", "OWNER_DECISION", 0.0) == "exact"
    assert u_class("any.key", "DATASHEET", 0.05) == "assessed"


def test_parity_with_register_column_over_all_entries():
    from verlustmappe import registry as R
    from verlustmappe.models.status import u_class
    from verlustmappe.reporting.make_register import u_class as legacy_u_class
    assert len(R.REGISTRY) == 109
    for k, v in R.REGISTRY.items():
        assert u_class(k, v["status"], v["uncertainty"]) == legacy_u_class(k, v), k


def test_u_class_of_rejected_entries_and_weakest_refuses_them():
    from verlustmappe import registry as R
    from verlustmappe.models.status import u_class, weakest
    # hand-listed (D26: 4 REJECTED with u = 0.0; the two efficiencies carry u = 0.4)
    expected = {
        "comp.pressure_ratio": "NOT ASSESSED",
        "comp.stroke_volume_cm3": "NOT ASSESSED",
        "comp.max_cycles_per_min": "NOT ASSESSED",
        "comp.min_suction_bar": "NOT ASSESSED",
        "comp.overall_efficiency": "assessed",
        "comp.specific_energy_kWh_per_Nm3": "assessed",
    }
    rejected = {k for k, v in R.REGISTRY.items() if v["status"] == "REJECTED"}
    assert rejected == set(expected)
    for k in rejected:
        v = R.REGISTRY[k]
        assert u_class(k, v["status"], v["uncertainty"]) == expected[k], k
        with pytest.raises(ValueError, match="REJECTED"):
            weakest([v["status"]])
    assert u_class("x", "SUPERSEDED", 0.0) == "NOT ASSESSED"
    assert u_class("x", "SUPERSEDED", 0.1) == "assessed"


def test_get_param_carries_u_class_and_leaves_registry_unchanged():
    from verlustmappe import registry as R
    from verlustmappe.models.params import get_param
    before = copy.deepcopy(R.REGISTRY)
    assert get_param("sys.n_rotex").u_class == "exact"
    assert get_param("meas.p_sensor_fso_bar").u_class == "exact"
    assert R.REGISTRY == before
