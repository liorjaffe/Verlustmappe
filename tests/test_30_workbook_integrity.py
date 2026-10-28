"""LAYER 1 - data integrity of the frozen workbook.

Proves only: the file is the file we think it is, and it is internally
well-formed. It does NOT prove any number is physically right.
Run: python3 test_30_workbook_integrity.py   (or pytest -q)

Pins in this file (FORMULAS, EXPECTED_O) are DRIFT DETECTORS copied from the
workbook: they make an unreviewed change visible, they are not evidence.
"""
import re
import sys

import xlsx_reader as X

EXPECTED_SHEETS = ["Overview", "Master", "Sources", "Corrections", "Open_Points"]
EXPECTED_LAST_MASTER_ROW = 191
EXPECTED_KEY_COUNT = 170
EXPECTED_SOURCE_IDS = {f"S{i}" for i in range(1, 28)}

# 17 description cells (column D, plain text since the workbook fix; formerly invalid <f> cells).
FORMULAS = {
    'D10': ' (1/1.01325)*(273.15/293.15); dry ideal gas, humidity ignored',
    'D27': ' kaeser.motor.p_out_kw / kaeser.motor.eta; motor only',
    'D30': ' 24 V x 1.5 A; upper bound for controller electronics in READY (PSU losses excluded)',
    'D37': ' kaeser.q_fad_m3min x sys.f_fad_to_nm3',
    'D119': ' min(400, 30*pL + min(140, 15*pL + 35)); equal pL on both stages assumed; zero flow at stall',
    'D120': ' min(400, 30*pL + min(140, 15*pL + 35)); equal pL on both stages assumed; zero flow at stall',
    'D121': ' min(400, 30*pL + min(140, 15*pL + 35)); equal pL on both stages assumed; zero flow at stall',
    'D122': ' min(400, 30*pL + min(140, 15*pL + 35)); equal pL on both stages assumed; zero flow at stall',
    'D123': ' min(400, 30*pL + min(140, 15*pL + 35)); equal pL on both stages assumed; zero flow at stall',
    'D124': ' (400-140)/30',
    'D132': ' 1215 / 83.3. Candidate primary L1 parameter (owner decision, see Open_Points)',
    'D133': ' 0.244 l x (35+1.01325)/1.01325 x 273.15/293.15; ideal gas, 20 degC suction, eta_vol = 1',
    'D169': ' p_N*(T/T_N)*ln(p_out,abs/p_in,abs); ideal gas, 20 degC. NOT electrical consumption',
    'D171': ' kaeser.p_package_dealer_kw / (kaeser.q_fad_m3min x 60); mixes 11 bar power and 10 bar flow (source conflict)',
    'D172': ' hulc.airA.ratio_nm3_per_nm3 x energy.e_air_kwh_nm3 (chart basis assumed Nm3)',
    'D173': ' hulc.airB.ratio x energy.e_air_kwh_nm3; lower bound',
    'D177': ' kaeser.q_nm3h (10 bar rating)',
}

# Rows where the numeric column O is NOT the first number printed in column C.
# Instead of switching the check off, each row pins the exact expected O and
# the reason, so a later change of O in these rows is still detected.
EXPECTED_O = {
    'kaeser.p_rated_nameplate_kw': (5.85, 'O = 5.5 + 0.35'),
    'kaeser.q_nm3h': (37.0, 'O = Nm3/h, C leads with Nm3/min'),
    'sys.p_h2_out_project_barg': (300.0, "C = '35 -> 300 barg', O = outlet"),
    'sys.p_h2_out_nameplate_barg': (400.0, "C = '35 -> 400 bar', O = outlet"),
    'kaeser.motor.eta': (0.892, 'C in percent, O fraction'),
    'hulc.s1.i': (15.0, "C = '1:15', O = 15"),
    'hulc.s2.i': (30.0, "C = '1:30', O = 30"),
    'hulc.s1.eps_max': (20.0, "C = '1:20', O = 20"),
    'hulc.s2.eps_max': (20.0, "C = '1:20', O = 20"),
    'hulc.h2_ratio_limit': (4.0, "C = '1:4', O = 4"),
    'hulc.airA.q_air_at_qmax_nlmin': (1215.0, 'O = 390 + 825'),
    'hulc.airB.s2_nl_per_dstroke': (15.56, 'C lists two values; O = upper (pI 140)'),
    'hulc.pl_max_bar': (10.0, "C = '1 - 10 bar', O = upper"),
    'kaeser.sc2_current_a': (1.5, "C = '24 V DC, 1.5 A', O = current"),
    'hulc.air_prep.p_max_bar': (10.0, "C = '1.0 MPa (10 bar)', O = bar"),
    'hulc.s2.counter_delta': (434.0, 'O = delta of two counter readings'),
    'hulc.s1.counter_delta': (1085.0, 'O = delta of two counter readings'),
    'cap.hulc_A_h2_max_nm3h': (2.5, "C = 'approx. 73 Nm3/h air ...; max H2 approx. 2.5'"),
    'cap.hulc_B_air_nm3h': (31.5, "C = 'approx. 23 - 32', O = 31.5 (upper)"),
    'energy.e_air_kwh_nm3': (0.168, "C = '0.154 kWh/m3 FAD = 0.168 kWh/Nm3', O = Nm3 value"),
    # OWNER QUESTION: text is coded as number 0 here; keep, or force O empty?
    'kaeser.has_idle': (0.0, "text 'not available' encoded as boolean 0"),
    'hulc.sys.p_electric_kw': (0.0, "text 'None (pneumatic)' encoded as 0 kW"),
    'hulc.leak_hp_seal_frac': (0.005, 'C in percent (0.5 %), O fraction'),
}

_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")
# A number not glued to letters/digits/dots on the left ("M400" is not 400).
_NUMBER = re.compile(r"(?<![A-Za-z0-9.])[-+]?\d+(?:\.\d+)?")


def first_number(text):
    m = _NUMBER.search(_THOUSANDS.sub("", text))
    return float(m.group()) if m else None


def test_file_identity():
    assert X.sha256() == X.EXPECTED_SHA256, "workbook changed: re-run the whole review"


def test_sheet_names():
    assert list(X.load().keys()) == EXPECTED_SHEETS


def test_master_row_count_and_contiguity():
    rows = sorted(X.master())
    assert rows == list(range(1, EXPECTED_LAST_MASTER_ROW + 1))


def test_model_keys_unique_and_wellformed():
    seen, dup = set(), []
    for r, cols in X.master().items():
        k = cols.get("I", "")
        if r == 1 or not k:
            continue
        assert re.fullmatch(r"[a-z0-9_]+(\.[A-Za-z0-9_]+)+", k), f"row {r}: bad key {k!r}"
        if k in seen:
            dup.append(k)
        seen.add(k)
    assert not dup, f"duplicate keys: {dup}"
    assert len(seen) == EXPECTED_KEY_COUNT, f"expected {EXPECTED_KEY_COUNT} keys, found {len(seen)}"


def test_every_key_row_has_status_and_source():
    for key, d in X.by_key().items():
        assert d["F"].strip(), f"{key} (row {d['row']}): empty Data status"
        assert d["E"].strip(), f"{key} (row {d['row']}): empty Source"


def test_every_cited_source_exists():
    src_rows = X.load()["Sources"]
    have = {c["A"]["v"] for r, c in src_rows.items() if r > 1 and "A" in c}
    assert have == EXPECTED_SOURCE_IDS, have ^ EXPECTED_SOURCE_IDS
    for key, d in X.by_key().items():
        for sid in re.findall(r"\[(S\d+)\]", d["E"]):
            assert sid in have, f"{key}: cites missing {sid}"


def test_O_column_is_numeric_or_empty():
    bad = [(k, d["row"], d["O_raw"]) for k, d in X.by_key().items()
           if d["O_raw"] not in ("", None) and d["O"] is None]
    assert not bad, f"non-numeric text in column O: {bad}"


def test_open_rows_carry_no_number():
    """Rule 1: unknown means no number (never a plausible placeholder)."""
    for key, d in X.by_key().items():
        if d["F"].strip().lower().startswith("open"):
            assert d["O"] is None, f"{key}: status Open but numeric value {d['O']}"


def test_no_real_formula_cells_remain():
    """The 17 prose cells were invalid Excel formulas (#NAME?/repair dialog); none may come back."""
    assert X.master_formulas() == {}


def test_description_text_is_pinned_for_all_17():
    """Drift detector: any edit of these texts must be re-reviewed by a human."""
    m = X.master()
    changed = {k: m[int(k[1:])].get("D") for k in FORMULAS if m[int(k[1:])].get("D") != FORMULAS[k]}
    assert not changed, changed


def test_calculated_rows_name_their_formula():
    for key, d in X.by_key().items():
        if d["F"].lower().startswith("calculated"):
            assert d["D"].strip(), f"{key}: calculated row without formula/description"


def test_numeric_O_matches_first_number_in_C_unless_pinned():
    bad = []
    for key, d in X.by_key().items():
        if d["O"] is None or key in EXPECTED_O:
            continue
        n = first_number(d["C"])
        if n is None or abs(n - d["O"]) > 1e-9:
            bad.append((key, d["C"][:40], d["O"]))
    assert not bad, bad


def test_pinned_O_values_unchanged():
    keys = X.by_key()
    for k, (val, why) in EXPECTED_O.items():
        assert k in keys, f"pinned key vanished: {k}"
        assert keys[k]["O"] == val, f"{k}: O={keys[k]['O']} expected {val} ({why})"


def test_every_pin_is_necessary():
    """A pin whose O already equals the first number in C is dead weight: remove it."""
    keys = X.by_key()
    dead = [k for k in EXPECTED_O if k in keys and keys[k]["O"] is not None
            and first_number(keys[k]["C"]) is not None
            and abs(first_number(keys[k]["C"]) - keys[k]["O"]) <= 1e-9]
    assert not dead, dead


def test_open_points_and_corrections_not_empty():
    wb = X.load()
    assert len(wb["Open_Points"]) == 11 and len(wb["Corrections"]) == 22


def test_l3_backlog_is_unmeasured():
    """No measurement may appear in J..N until an owner-approved measurement exists."""
    rows = X.master()
    for r in range(182, 192):
        for col in "JKLMN":
            assert rows[r].get(col, "") == "", f"row {r} col {col} now filled: needs a measurement protocol"


