"""Minimal xlsx reader (stdlib only). DRAFT, not part of the repo.

Reads the frozen workbook without openpyxl. Formula cells are returned with
their formula text and cached value separately. The 17 former pseudo-formula cells
(column D) were converted to plain text (see test_20); numbers come from column O.
"""
import hashlib
import os
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

# SHA-256 of the workbook state the drafts were written against.
EXPECTED_SHA256 = "0aa9f8ed0618d9bfd61123055674418969e0d7479d63b962afb18944cfd942ae"

DEFAULT_PATHS = [
    os.environ.get("XLSX_PATH", ""),
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "Compressor_System_Specs_Master_v2.xlsx"),
]


def xlsx_path():
    for p in DEFAULT_PATHS:
        if p and os.path.isfile(p):
            return p
    raise FileNotFoundError("put Compressor_System_Specs_Master_v2.xlsx next to these "
                            "files or set XLSX_PATH")


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
