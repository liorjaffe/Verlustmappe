"""Minimal xlsx reader (stdlib only).

Reads the frozen workbook without openpyxl. Formula cells are returned with
their formula text and cached value separately. The 17 former pseudo-formula cells
(column D) were converted to plain text. Current inputs come from column O;
removed calculated values are explicitly historical references below.
"""
import hashlib
import os
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

# SHA-256 of the workbook state the drafts were written against.
EXPECTED_SHA256 = "07b082dbacf00dc6b9332d3d7ce0f262041003bdf3913cce0dacedad07a33145"

# Historical calculated column-O values, not inputs or results of the current
# workbook: git 3fae5d4, workbook SHA-256 839a34eb5068ba48f6ece87ebce62c535daf24966e81826e0c7c221c1dc9b755.
HISTORICAL_O = {
    "sys.f_fad_to_nm3": 0.9196,
    "kaeser.motor.p_in_rated_kw": 6.17,
    "kaeser.p_sc2_max_w": 36,
    "kaeser.q_nm3h": 37,
    "hulc.stall_tank_pl6_barg": 305,
    "hulc.stall_tank_pl7_barg": 350,
    "hulc.stall_tank_pl8_barg": 380,
    "hulc.stall_tank_pl9_barg": 400,
    "hulc.stall_tank_pl10_barg": 400,
    "hulc.pl_for_400_bar": 8.67,
    "hulc.airA.q_air_at_qmax_nlmin": 1215,
    "hulc.airA.ratio_nm3_per_nm3": 14.6,
    "hulc.airB.s1_nl_per_dstroke": 8.08,
    "hulc.airB.s2_nl_per_dstroke": 15.56,
    "hulc.airB.ratio_pl6": 4.59,
    "hulc.airB.ratio_pl9": 6.30,
    "rotex.v_per_actuation_8bar_l_anr": 0.99,
    "energy.w_iso_35_300_kwh_nm3": 0.0641,
    "energy.w_iso_35_400_kwh_nm3": 0.0728,
    "energy.e_air_kwh_nm3": 0.168,
    "energy.hulc_A_kwh_nm3": 2.45,
    "energy.hulc_B_kwh_nm3": 0.77,
    "cap.supply_nm3h": 37,
    "cap.hulc_A_h2_max_nm3h": 2.5,
    "cap.hulc_B_air_nm3h": 31.5,
}

DEFAULT_PATHS = [
    os.environ.get("XLSX_PATH", ""),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "plant", "sources", "Compressor_System_Specs_Master_v2.xlsx"),
]


def xlsx_path():
    for p in DEFAULT_PATHS:
        if p and os.path.isfile(p):
            return p
    raise FileNotFoundError("Compressor_System_Specs_Master_v2.xlsx not found in "
                            "plant/sources/; or set XLSX_PATH")


def sha256(path=None):
    with open(path or xlsx_path(), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load(path=None):
    """Return {sheet: {row: {col: {'v': str, 'f': str|None}}}}."""
    z = ZipFile(path or xlsx_path())
    names = z.namelist()
    shared = []
    if "xl/sharedStrings.xml" in names:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        shared = ["".join(t.text or "" for t in si.findall(".//m:t", NS))
                  for si in root.findall("m:si", NS)]
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.attrib["Id"]: r.attrib["Target"]
            for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    out = {}
    for sh in wb.findall("m:sheets/m:sheet", NS):
        target = rels[sh.attrib["{%s}id" % NS["r"]]]
        part = target.lstrip("/") if target.startswith("/") else "xl/" + target
        rows = {}
        for c in ET.fromstring(z.read(part)).findall(".//m:c", NS):
            v = c.find("m:v", NS)
            val = (v.text or "") if v is not None else ""
            kind = c.attrib.get("t")
            if kind == "s" and val:
                val = shared[int(val)]
            elif kind == "inlineStr":
                val = "".join(t.text or "" for t in c.findall(".//m:t", NS))
            f = c.find("m:f", NS)
            m = re.match(r"([A-Z]+)(\d+)", c.attrib["r"])
            rows.setdefault(int(m.group(2)), {})[m.group(1)] = {
                "v": val, "f": (f.text or "") if f is not None else None}
        out[sh.attrib["name"]] = rows
    return out


def master():
    """Master sheet as {row: {col: str}} with formula text kept in 'D' etc. as value=''."""
    rows = load()["Master"]
    return {r: {c: cell["v"] for c, cell in cols.items()} for r, cols in rows.items()}


def master_formulas():
    rows = load()["Master"]
    return {f"{c}{r}": cell["f"] for r, cols in rows.items()
            for c, cell in cols.items() if cell["f"] is not None}


def by_key():
    """{model_key: {'row', 'A'..'G', 'P', 'O': float|None, 'O_raw': str}}.

    Never raises on a bad column O: an unparsable value gives O=None and keeps
    O_raw, so a named test (test_O_column_is_numeric_or_empty) fails instead of
    the whole suite crashing at import time.
    """
    out = {}
    for r, cols in master().items():
        key = cols.get("I", "")
        if r == 1 or not key:
            continue
        raw = cols.get("O", "")
        try:
            o = float(raw) if raw not in ("", None) else None
        except ValueError:
            o = None
        out[key] = {"row": r, **{c: cols.get(c, "") for c in "ABCDEFGP"},
                    "O": o, "O_raw": raw}
    return out
