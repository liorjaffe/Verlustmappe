"""Evidence status ranking, u class and weakest-wins for the new core (D26, D28).

No import of legacy modules. The u-class rule duplicates `reporting/make_register.u_class`
until the legacy teardown (M6); tests/test_37 pins parity. Unknown or blocked statuses raise,
there is no silent default.
"""

# D26 evidence_status, strongest first. The registry spells the sixth level "PRELIM".
EVIDENCE_ORDER = ("MEASURED", "CALIBRATED", "DATASHEET", "DATASHEET_SECONDARY", "DERIVED",
                  "PRELIM", "GUESS", "BACKLOG")
_ALIASES = {"PRELIM/ENVELOPE": "PRELIM"}

# D26(b)(iii): closed list; extend via DECISIONS only
TOLERANCE_BAND = ("meas.p_sensor_fso_bar", "meas.p_sensor_thermal_bar_per_10K")

# Registry source status, not an evidence status (D26): skipped by weakest()
OWNER_DECISION = "OWNER_DECISION"
# Registry states (D11, D28): classified by u_class like any numeric entry (D26(c)), but never
# an input of a result, so weakest() rejects them.
BLOCKED = ("REJECTED", "SUPERSEDED")


def _check(status, allow_blocked=False):
    s = _ALIASES.get(status, status)
    if allow_blocked and s in BLOCKED:
        return s
    if s not in EVIDENCE_ORDER and s != OWNER_DECISION:
        raise ValueError(f"status {status!r} is not in the D26 vocabulary (see DECISIONS.md); "
                         "REJECTED/SUPERSEDED entries must be blocked by the adapter (D28)")
    return s


def weakest(statuses):
    """Weakest evidence status of the inputs (D26: weakest-wins within evidence_status only).
    OWNER_DECISION inputs are skipped; if nothing else remains, raise: the classification of a
    purely owner-based result needs a DECISIONS entry (D26), not a code default."""
    ranked = [s for s in (_check(x) for x in statuses) if s != OWNER_DECISION]
    if not ranked:
        raise ValueError("no evidence status among the inputs (empty or OWNER_DECISION only); "
                         "D26 defines no default, classification needs a DECISIONS entry")
    return max(ranked, key=EVIDENCE_ORDER.index)


def u_class(key, status, uncertainty):
    """D26(b): 'assessed' (u != 0), 'exact' (u = 0.0 and OWNER_DECISION or TOLERANCE_BAND key),
    otherwise 'NOT ASSESSED'. DERIVED alone does not establish exactness. Total over the whole
    registry incl. REJECTED/SUPERSEDED (D26(c)); only unknown statuses raise."""
    _check(status, allow_blocked=True)
    if uncertainty != 0.0:
        return "assessed"
    if status == OWNER_DECISION or key in TOLERANCE_BAND:
        return "exact"
    return "NOT ASSESSED"
