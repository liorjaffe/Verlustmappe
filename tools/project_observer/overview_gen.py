#!/usr/bin/env python3
"""Generate a static project overview as HTML (CONTRACT.md section 12).

The script does not calculate plant behaviour or modify project source files. It reads:
  - Python code via AST (classes, functions, parameters, calls, string constants)
  - plant/*.toml: key paths, the status/unit/source fields, [open] entries and whether a
    value field is present; value, uncertainty and other numeric contents are never emitted
  - START.md restart progress and known failures (checklist lines only)
  - documents (only lines containing markers such as BACKLOG, PAUSED, UNVERIFIED)
  - an optional engineer-maintained semantics file (semantics.toml)

Examples (from the repository root):
  python tools/project_observer/overview_gen.py --root .            # one-off snapshot
  python tools/project_observer/overview_gen.py --root . --serve    # live view on 127.0.0.1

The snapshot is written to tools/project_observer/output/overview.html (Git-ignored). The
live view regenerates the page on every browser reload, writes nothing, and ends with Ctrl+C.
"""
import argparse
import ast
import json
import re
import subprocess
import tomllib
from collections import Counter
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

MARKER = re.compile(r"\b(BACKLOG|PAUSED|MISSING|TODO|UNKLAR|UNVERIFIED)\b")
LIVE_HOST = "127.0.0.1"  # fixed by CONTRACT.md section 12; deliberately not configurable


# ---------- Read code (AST) ----------

def parse(path):
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return None


def dict_keys(fn):
    """Approximate string keys in dict literals and assignments such as r["key"] = ... ."""
    keys = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Dict):
            keys |= {k.value for k in n.keys
                     if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        elif (isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Store)
              and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str)):
            keys.add(n.slice.value)
    return sorted(keys)


def signature(fn):
    a = fn.args
    pos = a.posonlyargs + a.args
    args = pos + a.kwonlyargs
    defaults = [None] * (len(pos) - len(a.defaults)) + list(a.defaults) + list(a.kw_defaults)
    out = []
    for arg, d in zip(args, defaults):
        if arg.arg in ("self", "cls"):
            continue
        out.append({
            "name": arg.arg,
            "ann": ast.unparse(arg.annotation) if arg.annotation else "",
            "default": ast.unparse(d) if d is not None else "",
        })
    return out


def first_line(node):
    return (ast.get_docstring(node) or "").split("\n")[0]


def symbols(tree):
    out = []
    for n in tree.body:
        if isinstance(n, ast.ClassDef):
            methods = [
                {"name": m.name, "line": m.lineno, "args": signature(m), "keys": dict_keys(m)}
                for m in n.body
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and not m.name.startswith("_")
            ]
            out.append({"kind": "Class", "name": n.name, "line": n.lineno,
                        "doc": first_line(n), "methods": methods})
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("_"):
            out.append({"kind": "Function", "name": n.name, "line": n.lineno,
                        "doc": first_line(n), "args": signature(n), "keys": dict_keys(n)})
    return out


def identifiers(tree):
    """Collect names, attributes, parameters, and short strings for name matching."""
    s = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            s.add(n.id)
        elif isinstance(n, ast.Attribute):
            s.add(n.attr)
        elif isinstance(n, ast.arg):
            s.add(n.arg)
        elif isinstance(n, ast.keyword) and n.arg:
            s.add(n.arg)
        elif isinstance(n, ast.alias):
            s.add(n.name.split(".")[-1])
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) < 80:
            s.add(n.value)
    return s


def calls(tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
            if name:
                yield name, n.lineno


# ---------- Documents and Git ----------

def marker_lines(path):
    out = []
    try:
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if MARKER.search(line):
                out.append({"line": i, "text": line.strip()[:200]})
    except (OSError, UnicodeDecodeError):
        pass
    return out


def git_info(root):
    try:
        run = lambda *c: subprocess.run(["git", *c], cwd=root, capture_output=True,
                                        text=True, timeout=5).stdout.strip()
        return {"commit": run("rev-parse", "--short", "HEAD"),
                "branch": run("branch", "--show-current"),
                "dirty": bool(run("status", "--porcelain"))}
    except Exception:
        return {}


def start_state(path):
    """Checklist lines of 'Restart progress' and bullet lines of 'Known failures'."""
    progress, failures, section = [], [], None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return {"found": False, "progress": [], "failures": []}
    for line in lines:
        if line.startswith("## "):
            section = line[3:].strip().lower()
            continue
        m = re.match(r"- \[([ xX])\] (.*)", line)
        if section == "restart progress" and m:
            progress.append({"done": m.group(1) != " ", "text": m.group(2).strip()})
        elif section == "known failures" and line.startswith("- "):
            failures.append(line[2:].strip())
    return {"found": True, "progress": progress, "failures": failures}


# ---------- Plant TOML (no values) ----------

def strings_in(obj):
    """All string leaves of an [open] block, in order."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in strings_in(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in strings_in(v)]
    return []


def plant_device(path, root):
    """Read one plant file. Only labels and text fields leave this function; never values."""
    rel = path.relative_to(root).as_posix()
    dev = {"stem": path.stem, "file": rel, "title": "", "params": [], "open": [], "errors": [],
           "unverified": 0, "unverified_at": []}
    try:
        raw = path.read_text(encoding="utf-8")
        data = tomllib.loads(raw)
    except (tomllib.TOMLDecodeError, OSError, UnicodeDecodeError) as e:
        dev["errors"].append(f"cannot read: {e}")
        return dev
    # UNVERIFIED locator: count, line number and enclosing table name only; no line text emitted
    table = "(top level)"
    for i, line in enumerate(raw.splitlines(), 1):
        head = re.match(r"\s*\[\[?\s*([^\[\]]+?)\s*\]\]?\s*(#.*)?$", line)
        if head:
            table = head.group(1)
        n = len(re.findall(r"\bUNVERIFIED\b", line))
        if n:
            dev["unverified_at"].append({"line": i, "table": table, "count": n})
    dev["unverified"] = sum(x["count"] for x in dev["unverified_at"])
    title = data.get("device", {}).get("title")
    dev["title"] = title if isinstance(title, str) else ""
    params = data.get("param", {})
    if not isinstance(params, dict):
        dev["errors"].append("[param] is not a table")
        params = {}
    for key, p in params.items():
        if not isinstance(p, dict):
            dev["errors"].append(f"param {key!r} is not a table")
            continue
        text = lambda f: p[f] if isinstance(p.get(f), str) else ""
        status = text("status")
        if not status:
            dev["errors"].append(f"param {key!r} has no text status")
        dev["params"].append({
            "key": key, "status": status or "(no status)", "unit": text("unit"),
            "source": text("source"), "has_value": "value" in p,
        })
    if "open" in data:
        dev["open"] = strings_in(data["open"])
    return dev


# ---------- Topology (owner-maintained display semantics) ----------

MEDIA = ("dc", "ac", "h2", "water", "air", "aux")
NODE_KINDS = ("device", "outside", "terminal", "supply", "unassessed")
SLOTS = ("in", "out", "eta", "loss", "stock", "elec", "air", "ctrl", "eout", "total")


def is_point(p):
    return (isinstance(p, list) and len(p) == 2
            and all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in p))


def load_topology(path, plant_stems):
    """Read the diagram description; problems are reported, never silently dropped."""
    topo = {"found": False, "path": str(path), "reviewed": False, "descriptions_reviewed": False,
            "units": {}, "layout": {},
            "nodes": [], "edges": [], "buses": [], "errors": []}
    if not path.exists():
        return topo
    topo["found"] = True
    try:
        t = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError, UnicodeDecodeError) as e:
        topo["errors"].append(f"cannot read: {e}")
        return topo
    err = topo["errors"].append
    topo["reviewed"] = t.get("reviewed") is True
    topo["descriptions_reviewed"] = t.get("descriptions_reviewed") is True
    units = t.get("units", {})
    topo["units"] = {k: v for k, v in units.items() if k in MEDIA and isinstance(v, str)}
    for k in units:
        if k not in MEDIA:
            err(f"units: unknown medium {k!r}")
    for k in MEDIA:
        if k not in topo["units"]:
            err(f"units: no unit for medium {k!r}")
    lay = t.get("layout", {})
    for k in ("width", "height", "node_w", "node_h"):
        if not isinstance(lay.get(k), int):
            err(f"layout.{k} missing or not an integer")
    topo["layout"] = {k: lay.get(k) for k in ("width", "height", "node_w", "node_h")}
    for k, fallback in (("node_h_flow", "node_h"), ("height_flow", "height")):
        topo["layout"][k] = lay[k] if isinstance(lay.get(k), int) else topo["layout"][fallback]
    ids = set()
    for n in t.get("node", []):
        nid = n.get("id")
        if not isinstance(nid, str) or nid in ids:
            err(f"node id missing or duplicate: {nid!r}")
            continue
        if not all(isinstance(n.get(k), int) for k in ("x", "y")):
            err(f"node {nid}: x/y missing")
            continue
        kind = n.get("kind", "device")
        if kind not in NODE_KINDS:
            err(f"node {nid}: unknown kind {kind!r}")
        plant = n.get("plant", "")
        if plant and plant not in plant_stems:
            err(f"node {nid}: plant file {plant!r}.toml not found")
            plant = ""
        slots = n.get("slots", [])
        bad = [x for x in slots if x not in SLOTS] if isinstance(slots, list) else ["(not a list)"]
        if bad:
            err(f"node {nid}: unknown slots {bad}")
            slots = [x for x in slots if x in SLOTS] if isinstance(slots, list) else []
        ids.add(nid)
        if not n.get("description"):
            err(f"node {nid}: no description")
        topo["nodes"].append({"slots": slots, "account": str(n.get("account", "")),
                              "description": str(n.get("description", "")), "id": nid, "label": str(n.get("label", nid)), "sub": str(n.get("sub", "")),
                              "plant": plant, "kind": kind, "x": n["x"], "y": n["y"],
                              "basis": str(n.get("basis", ""))})
    for b in t.get("bus", []):
        pts = b.get("points", [])
        if b.get("medium") not in MEDIA or len(pts) < 2 or not all(is_point(p) for p in pts):
            err(f"bus with invalid medium or points: {b.get('medium')!r}")
            continue
        topo["buses"].append({"medium": b["medium"], "points": pts})
    for i, e in enumerate(t.get("edge", []), 1):
        src, dst, med = e.get("from"), e.get("to"), e.get("medium")
        ok = True
        if med not in MEDIA:
            err(f"edge {i}: unknown medium {med!r}"); ok = False
        if dst not in ids:
            err(f"edge {i}: unknown target {dst!r}"); ok = False
        if src is not None and src not in ids:
            err(f"edge {i}: unknown source {src!r}"); ok = False
        if src is None and not is_point(e.get("from_point")):
            err(f"edge {i}: needs from or from_point"); ok = False
        via = e.get("via", [])
        if not all(is_point(p) for p in via):
            err(f"edge {i}: invalid via points"); ok = False
        if not e.get("basis"):
            err(f"edge {i}: no basis given")
        if ok:
            topo["edges"].append({"from": src, "from_point": e.get("from_point"), "to": dst,
                                  "medium": med, "via": via, "both": e.get("both") is True,
                                  "assess": e.get("assess") is not False,
                                  "value_at_station": e.get("value_at_station") is True,
                                  "label": str(e.get("label", "")), "basis": str(e.get("basis", "")),
                                  "label_side": "left" if e.get("label_side") == "left" else "right"})
    return topo


# ---------- Build ----------

def build(a):
    root = Path(a.root).expanduser().resolve()
    pkg = root / a.pkg
    mods, trees = {}, {}

    for p in sorted(pkg.rglob("*.py")):
        if p.name == "__init__.py":
            continue
        tree = parse(p)
        if tree is None:
            continue
        mid = p.relative_to(pkg).with_suffix("").as_posix()
        trees[mid] = tree
        mods[mid] = {
            "id": mid, "stem": p.stem, "group": mid.split("/")[0] if "/" in mid else "(root)",
            "path": p.relative_to(root).as_posix(), "symbols": symbols(tree),
            "calls_to": set(), "called_by": {}, "tests": set(), "toml": [],
            "markers": marker_lines(p), "signals": [], "_ids": identifiers(tree),
        }

    owners = {}
    for mid, m in mods.items():
        for s in m["symbols"]:
            owners.setdefault(s["name"], []).append(mid)

    def link(file_rel, tree, own_mid=None):
        for name, line in calls(tree):
            o = owners.get(name, [])
            if len(o) != 1 or o[0] == own_mid:
                continue
            tgt = mods[o[0]]
            if own_mid:
                mods[own_mid]["calls_to"].add(o[0])
            if file_rel.startswith(a.tests + "/"):
                tgt["tests"].add(file_rel)
            else:
                e = tgt["called_by"].setdefault((file_rel, name), {
                    "file": file_rel, "symbol": name, "module": own_mid, "lines": []})
                if len(e["lines"]) < 5:
                    e["lines"].append(line)

    test_ids = {}
    for mid, tree in trees.items():
        link(mods[mid]["path"], tree, mid)
    for d in a.extra:
        for p in sorted((root / d).rglob("*.py")):
            tree = parse(p)
            if tree is None:
                continue
            rel = p.relative_to(root).as_posix()
            link(rel, tree)
            if rel.startswith(a.tests + "/"):
                test_ids[rel] = identifiers(tree)

    docs = []
    for d in a.docs:
        p = root / d
        if p.exists():
            for ml in marker_lines(p):
                docs.append({"file": d, **ml})
    for m in mods.values():
        names = [s["name"] for s in m["symbols"]] + [m["stem"] + ".py"]
        m["doc_markers"] = [x for x in docs if any(n in x["text"] for n in names)]

    # Plant devices and their static progress facts
    devices = []
    for p in sorted((root / a.plant).glob("*.toml")):
        dev = plant_device(p, root)
        stem, keys = dev["stem"], {x["key"] for x in dev["params"]}
        model = f"devices/{stem}"
        refs = sorted(mid for mid, m in mods.items()
                      if mid != model and (m["_ids"] & keys or model in m["calls_to"]))
        tests = set(mods[model]["tests"]) if model in mods else set()
        tests |= {t for t, ids in test_ids.items() if ids & keys}
        for m in mods.values():
            if p.stem == m["stem"] or p.stem in m["_ids"]:
                m["toml"].append({"file": dev["file"], "keys": sorted(keys)})
        mentions = (f"{stem}.toml", f"devices/{stem}.py", f"devices/{stem}`")
        dev.update({
            "model": model if model in mods else "",
            "scenario": f"scenarios/{stem}" if f"scenarios/{stem}" in mods else "",
            "refs": refs, "accounting_refs": [r for r in refs if r.startswith("accounting/")],
            "tests": sorted(tests),
            "labels": sorted(Counter(x["status"] for x in dev["params"]).items()),
            "doc_lines": [x for x in docs if any(t in x["text"] for t in mentions)],
        })
        devices.append(dev)

    # Engineer-maintained semantics and matching against code
    signals = []
    sem_path = (root / a.semantics).resolve()
    if sem_path.exists():
        sem = tomllib.loads(sem_path.read_text(encoding="utf-8"))

        def resolve(ref):
            return [i for i in mods if i == ref or mods[i]["stem"] == ref]

        for s in sem.get("signal", []):
            where = ([s["produced_in"]] if s.get("produced_in") else []) + list(s.get("consumed_in", []))
            checks = []
            for cn in s.get("code_names", []):
                missing = [w for w in where if not any(cn in mods[i]["_ids"] for i in resolve(w))]
                checks.append({"name": cn, "missing_in": missing})
            signals.append({**s, "checks": checks})
            for role, refs in (("produced in", [s.get("produced_in")]), ("consumed in", s.get("consumed_in", []))):
                for r in refs:
                    for i in resolve(r) if r else []:
                        mods[i]["signals"].append({"name": s["name"], "role": role})
    topo = load_topology((root / a.topology).resolve(), {d["stem"] for d in devices})
    order = [n["plant"] for n in topo["nodes"] if n["plant"]]
    rank = {s: i for i, s in enumerate(order)}
    devices.sort(key=lambda d: (rank.get(d["stem"], len(rank)), d["stem"]))

    out = []
    for m in mods.values():
        m = dict(m)
        m.pop("_ids")
        m["calls_to"] = sorted(m["calls_to"])
        m["called_by"] = sorted(m["called_by"].values(), key=lambda e: (e["file"], e["symbol"]))
        m["tests"] = sorted(m["tests"])
        out.append(m)

    return {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "git": git_info(root),
        "start": start_state(root / "START.md"), "devices": devices,
        "topology": topo,
        "modules": out, "signals": signals, "doc_markers": docs,
        "semantics_found": sem_path.exists(), "semantics_path": str(sem_path),
    }


# ---------- HTML ----------

TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Project Observer</title>
<style>
:root{--bg:#fafaf9;--panel:#f0f0ed;--ink:#1c2226;--mute:#5f686e;--line:#dcddd8;--accent:#1f5f8b;--chip:#e6e7e2;--warn:#8a5a00;--node:#ffffff;--node-edge:#4a5358;
--m-dc:#c45f00;--m-ac:#6237a8;--m-h2:#0a7d76;--m-water:#2a74c4;--m-air:#6f7d1c;--m-aux:#c0175a;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#171a1c;--panel:#1f2326;--ink:#e5e7e5;--mute:#9aa3a8;--line:#32383c;--accent:#82b9e0;--chip:#2a2f33;--warn:#e0b25c;--node:#22272a;--node-edge:#9aa3a8;
--m-dc:#f39a3d;--m-ac:#b49af2;--m-h2:#3fd0c3;--m-water:#78b3f2;--m-air:#bccb62;--m-aux:#f2689f;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{background:var(--panel);border-bottom:1px solid var(--line);padding:10px 20px}
header .top{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 16px}
header h1{font-size:16px;margin:0}
.mode{font-size:12px;font-weight:600;padding:1px 7px;border:1px solid var(--line);border-radius:10px}
.prog{display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:6px;font-size:13px}
.prog span{white-space:nowrap}
.disc{font-size:12.5px;color:var(--mute);margin-top:4px}
.fail{font-size:12.5px;color:var(--warn);margin-top:4px}
nav.tabs{display:flex;gap:2px;padding:0 20px;border-bottom:1px solid var(--line)}
nav.tabs a{padding:8px 12px;color:var(--mute);text-decoration:none;border-bottom:2px solid transparent}
nav.tabs a.on{color:var(--ink);border-bottom-color:var(--accent);font-weight:600}
main{padding:14px 20px 40px;max-width:1300px}
h2{font-size:15px;margin:22px 0 6px} h3{font-size:14px;margin:16px 0 4px}
.mute{color:var(--mute)} .mono,.path{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:4px 0}
th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--mute);font-weight:600;white-space:nowrap} td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tbody tr.row{cursor:pointer} tbody tr.row:hover{background:var(--panel)}
.chip{display:inline-block;background:var(--chip);border-radius:4px;padding:0 6px;margin:1px 3px 1px 0;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;white-space:nowrap}
.note{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:8px 12px;margin:8px 0;font-size:13px}
a.l{color:var(--accent)} :focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.err{color:var(--warn)}
.cols{display:grid;grid-template-columns:220px 1fr;gap:20px}
.cols nav a{display:block;padding:2px 6px;border-radius:4px;color:var(--ink);text-decoration:none}
.cols nav a.on{background:var(--chip)} .cols nav h3{color:var(--mute);font-size:12px;margin:10px 0 2px}
ul.q{margin:4px 0;padding-left:20px}
.diagram{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--bg);padding:8px}
.diagram svg{display:block;width:100%;min-width:900px;height:auto}
svg .nd rect{fill:var(--node);stroke:var(--node-edge);stroke-width:1.3}
svg .nd.outside rect{fill:none;stroke-dasharray:6 4}
svg .nd.supply rect{fill:var(--panel);stroke:var(--m-aux);stroke-width:1.6}
svg .nd.terminal rect{fill:var(--panel)}
svg .nd.unassessed rect{fill:none;stroke:var(--mute);stroke-dasharray:2 3}
svg .nd.unassessed .t{fill:var(--mute)} svg .nd.unassessed .s{font-style:italic}
svg .faded{opacity:.4}
svg .nd .t{font:600 13px system-ui,-apple-system,"Segoe UI",sans-serif;fill:var(--ink)}
svg .nd .s{font:11px system-ui,-apple-system,"Segoe UI",sans-serif;fill:var(--mute)}
svg a .nd{cursor:pointer} svg a:hover .nd rect,svg a:focus .nd rect{stroke:var(--accent);stroke-width:2.4}
svg .fl{fill:none;stroke-linejoin:round}
svg .lb{font:11px system-ui,-apple-system,"Segoe UI",sans-serif;paint-order:stroke;stroke:var(--bg);stroke-width:4px;stroke-linejoin:round}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:6px;overflow:hidden;margin:2px 0 10px}
.seg a{padding:5px 14px;text-decoration:none;color:var(--mute);font-size:13px}
.seg a.on{background:var(--accent);color:var(--bg);font-weight:600}
svg .sk{font:11px system-ui,-apple-system,"Segoe UI",sans-serif;fill:var(--mute)}
svg .sv{font:600 10.5px ui-monospace,Menlo,Consolas,monospace;fill:var(--warn)}
svg .pill rect{fill:var(--bg);stroke-width:1.2} svg .pill text{font:600 9.5px ui-monospace,Menlo,Consolas,monospace;fill:var(--warn)}
.accts{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin:12px 0}
.acct{border:1px solid var(--line);border-radius:8px;padding:10px 14px;background:var(--panel)}
.acct h3{margin:0 0 6px;font-size:14px} .acct dl{display:grid;grid-template-columns:1fr auto;gap:3px 12px;margin:0;font-size:13px}
.acct dd{margin:0;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;color:var(--warn);font-weight:600}
.stage{display:grid;grid-template-columns:minmax(0,1fr);gap:14px;align-items:start}
.stage.sel{grid-template-columns:minmax(0,1fr) 320px}
@media (max-width:1100px){.stage.sel{grid-template-columns:minmax(0,1fr)}}
.card{border:1px solid var(--line);border-radius:8px;background:var(--panel);padding:12px 14px;font-size:13px;position:sticky;top:8px}
.card .hd{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.card h3{margin:0;font-size:15px} .card .x{text-decoration:none;color:var(--mute);font-size:16px;line-height:1}
.card h4{margin:12px 0 4px;font-size:12px;color:var(--mute);font-weight:600;text-transform:uppercase;letter-spacing:.03em}
.card p{margin:4px 0} .card .acc{display:inline-block;margin-top:4px;font-size:11.5px;padding:0 7px;border:1px solid var(--line);border-radius:9px;color:var(--mute)}
.card ul{margin:2px 0;padding-left:0;list-style:none} .card li{margin:3px 0;display:flex;gap:7px;align-items:baseline}
.card li .sw{flex:none;width:18px;height:0;border-top-width:3px;border-top-style:solid;transform:translateY(-3px)}
.card .u{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11.5px;color:var(--mute)}
.card .draft{font-size:11.5px;color:var(--warn)}
svg .nd.on rect{stroke:var(--accent);stroke-width:2.6}
.legend{display:flex;flex-wrap:wrap;gap:6px 22px;margin:10px 2px;font-size:13px}
.legend span{display:inline-flex;align-items:center;gap:7px}
@media (max-width:760px){.cols{grid-template-columns:1fr}header,main{padding-left:16px;padding-right:16px}}
</style></head><body>
<header id="hdr"></header>
<nav class="tabs" id="tabs"></nav>
<main id="main"></main>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const h = (t, a = {}, ...c) => {
  const e = document.createElement(t);
  for (const [k, v] of Object.entries(a)) k === 'class' ? e.className = v : e.setAttribute(k, v);
  for (const x of c.flat(Infinity)) if (x != null && x !== false) e.append(x.nodeType ? x : document.createTextNode(String(x)));
  return e;
};
const chips = arr => arr.map(x => h('span', {class: 'chip'}, x));
const table = (head, rows, opts = {}) => rows.length
  ? h('div', {class: 'scroll'}, h('table', {}, h('thead', {}, h('tr', {}, head.map(x => h('th', {}, x)))),
      h('tbody', {}, rows.map(r => r))))
  : h('p', {class: 'mute'}, opts.empty || 'Nothing found.');
const tr = (cells, attrs = {}) => h('tr', attrs, cells.map(c => c && c.nodeName === 'TD' ? c : h('td', {}, c)));
const num = x => h('td', {class: 'n'}, x);
const link = (href, text) => h('a', {class: 'l', href}, text);
const byId = Object.fromEntries(D.modules.map(m => [m.id, m]));
const byDev = Object.fromEntries(D.devices.map(d => [d.stem, d]));
const main = () => document.getElementById('main');

function renderHeader() {
  const g = D.git, s = D.start, live = D.mode === 'live';
  const hdr = document.getElementById('hdr');
  hdr.replaceChildren(
    h('div', {class: 'top'}, h('h1', {}, 'Project Observer'),
      h('span', {class: 'mode'}, live ? 'Live — reload to refresh' : 'Snapshot — may be outdated'),
      h('span', {class: 'mute'}, 'Generated ' + D.generated),
      g.commit ? h('span', {class: 'mono'}, (g.branch || '?') + ' @ ' + g.commit) : null,
      h('span', {}, g.dirty ? 'uncommitted changes' : 'clean worktree')),
    s.found ? h('div', {class: 'prog'}, s.progress.map(p =>
      h('span', {title: p.text}, (p.done ? '☑ ' : '☐ ') + p.text.split(/[ ;:]/)[0]))) : h('div', {class: 'err'}, 'START.md not found'),
    s.failures.length ? h('div', {class: 'fail'}, 'Known failures (START.md): ' + s.failures.join(' · ')) : null,
    h('div', {class: 'disc'}, 'Display only, not a review or assessment. Progress columns are static file facts and name matches, ',
      'not proof of correct modelling or booking. Status labels are shown verbatim without ranking. No parameter values are read.'));
}

function renderTabs(cur) {
  const t = document.getElementById('tabs');
  t.replaceChildren(...[['plant', 'Plant'], ['devices', 'Devices'], ['open', 'Open items'], ['code', 'Code']].map(([k, label]) =>
    h('a', {href: '#' + k, class: cur === k ? 'on' : ''}, label)));
}

// ----- Plant diagram -----
const NS = 'http://www.w3.org/2000/svg';
const s = (t, a = {}, ...c) => {
  const e = document.createElementNS(NS, t);
  for (const [k, v] of Object.entries(a)) e.setAttribute(k, v);
  c.flat(Infinity).forEach(x => x != null && x !== false && e.append(x.nodeType ? x : document.createTextNode(String(x))));
  return e;
};
const MEDIA = {
  h2:    {label: 'Hydrogen', w: 5},
  water: {label: 'Process water', w: 3.5},
  air:   {label: 'Compressed air', w: 3, dash: '9 5'},
  dc:    {label: 'DC electricity, series path', w: 2.6},
  ac:    {label: 'AC electricity, series path', w: 2.6},
  aux:   {label: 'Auxiliary electricity (account B)', w: 2, dash: '4 3'},
};
const lineAttrs = m => ({class: 'fl', stroke: 'var(--m-' + m + ')', 'stroke-width': MEDIA[m].w,
  ...(MEDIA[m].dash ? {'stroke-dasharray': MEDIA[m].dash} : {})});

function attach(r, p) {  // point on rectangle r facing point p (orthogonal layout)
  if (p[0] >= r.x && p[0] <= r.x + r.w) return [p[0], p[1] < r.y ? r.y : r.y + r.h];
  if (p[1] >= r.y && p[1] <= r.y + r.h) return [p[0] < r.x ? r.x : r.x + r.w, p[1]];
  return [r.x + r.w / 2, r.y + r.h / 2];
}

const SLOT_LABEL = {in: 'in', out: 'out', eta: 'η', loss: 'loss', stock: 'Δ stock', elec: 'electricity',
  air: 'drive air', ctrl: 'FC control', eout: 'E AC out', total: 'total B'};
const MISSING = 'MISSING';

function stationCard(T, n, flow) {
  const name = id => (T.nodes.find(x => x.id === id) || {}).label || id;
  const u = med => h('span', {class: 'u'}, '[' + (T.units[med] || '?') + ']');
  const sw = med => h('span', {class: 'sw', style: `border-top-color:var(--m-${med});border-top-style:${MEDIA[med].dash ? 'dashed' : 'solid'}`});
  const item = (e, text) => h('li', {}, sw(e.medium), h('span', {}, MEDIA[e.medium].label.replace(', series path', ''), ' ', u(e.medium),
    ' ', text, e.label ? h('span', {class: 'mute'}, ' · ' + e.label) : null, e.assess ? null : h('span', {class: 'mute'}, ' · not assessed')));
  let ins = [], outs = [], aux = [];
  T.edges.forEach(e => {
    if (e.to === n.id) (e.medium === 'aux' ? aux : ins).push(item(e, e.from ? 'from ' + name(e.from) : 'from auxiliary line'));
    if (e.from === n.id) outs.push(item(e, 'to ' + name(e.to)));
    if (e.both && e.to === n.id) outs.push(item(e, 'to ' + name(e.from)));
    if (e.both && e.from === n.id) ins.push(item(e, 'from ' + name(e.to)));
  });
  if (n.id === 'aux_supply') outs = T.edges.filter(e => e.medium === 'aux' && !e.from).map(e => item(e, 'to ' + name(e.to)));
  const list = (title, arr) => arr.length ? [h('h4', {}, title), h('ul', {}, arr)] : null;
  const dev = n.plant ? byDev[n.plant] : null;
  const back = '#' + (flow ? 'flow' : 'plant');
  return h('aside', {class: 'card', 'aria-label': n.label},
    h('div', {class: 'hd'}, h('h3', {}, n.label), h('a', {class: 'x', href: back, title: 'Close'}, '✕')),
    n.sub ? h('div', {class: 'mute'}, n.sub) : null,
    n.account ? h('span', {class: 'acc'}, n.account === 'A' ? 'Account A · series path' : n.account === 'B' ? 'Account B · auxiliary'
      : n.account === 'outside' ? 'Outside the provisional boundary' : n.account) : null,
    h('h4', {}, 'What happens'), h('p', {}, n.description || '–'),
    T.descriptions_reviewed ? null : h('div', {class: 'draft'}, 'Draft text, owner review pending.'),
    list('In', ins), list('Out', outs), list('Auxiliary energy (B)', aux),
    h('h4', {}, 'Key parameters'), h('p', {class: 'mute'}, 'Not filled yet; selection follows after the pending plant-file changes.'),
    h('h4', {}, 'Basis'), h('p', {class: 'mute', style: 'font-size:12px'}, n.basis),
    dev ? h('p', {style: 'margin-top:10px'}, link('#device/' + n.plant, 'Device details →'),
      h('span', {class: 'mute'}, ' · ' + (dev.open.length + dev.doc_lines.length) + ' open · ' + dev.unverified + ' UNVERIFIED')) : null);
}

function plant(flow, selId) {
  const m = main(); m.replaceChildren();
  const T = D.topology, L = T.layout;
  if (!T.found) { m.append(h('p', {class: 'err'}, 'No topology file at ' + T.path)); return; }
  const sfx = selId ? '/' + selId : '';
  m.append(h('div', {class: 'seg', role: 'tablist'},
    h('a', {href: '#plant' + sfx, class: flow ? '' : 'on'}, 'Structure'), h('a', {href: '#flow' + sfx, class: flow ? 'on' : ''}, 'Energy flow')));
  m.append(h('p', {class: 'mute'}, flow
      ? ['Value slots per station and flow. ', h('strong', {}, 'No results file: every value is MISSING. '),
         'Values will only come from an approved src pipeline result (planned case F1, N4); this page computes nothing.']
      : 'What flows where, from PV to the FC inverter output. No amounts. ',
    ' Click a station for its description. ', T.reviewed ? 'Topology owner-reviewed.'
      : h('span', {class: 'err'}, 'Topology transcribed by an agent from CONTRACT §4 and plant file titles; not owner-reviewed.')));
  if (T.errors.length) m.append(h('ul', {class: 'q err'}, T.errors.map(e => h('li', {}, 'Topology: ' + e))));
  if (!L.width) return;
  const NH = flow ? L.node_h_flow : L.node_h;
  const rect = Object.fromEntries(T.nodes.map(n => [n.id, {x: n.x, y: n.y, w: L.node_w, h: NH}]));
  const center = r => [r.x + r.w / 2, r.y + r.h / 2];
  const svg = s('svg', {viewBox: `0 0 ${L.width} ${flow ? L.height_flow : L.height}`, role: 'img', 'aria-label': 'Plant flow diagram'});
  const defs = s('defs');
  Object.keys(MEDIA).forEach(k => defs.append(s('marker', {id: 'mk-' + k, viewBox: '0 0 10 10', refX: 9, refY: 5,
    markerWidth: k === 'h2' ? 3.2 : 5, markerHeight: k === 'h2' ? 3.2 : 5, orient: 'auto-start-reverse', markerUnits: 'strokeWidth'},
    s('path', {d: 'M0,0 L10,5 L0,10 z', fill: 'var(--m-' + k + ')'}))));
  svg.append(defs);
  const flows = s('g'), labels = s('g'), nodes = s('g');
  T.buses.forEach(b => flows.append(s('polyline', {...lineAttrs(b.medium), points: b.points.map(p => p.join(',')).join(' ')})));
  T.edges.forEach(e => {
    const to = rect[e.to];
    const first = e.via[0] || center(to);
    const start = e.from_point || attach(rect[e.from], first);
    const last = e.via.length ? e.via[e.via.length - 1] : start;
    const pts = [start, ...e.via, attach(to, last)];
    const attrs = {...lineAttrs(e.medium), points: pts.map(p => p.join(',')).join(' '), 'marker-end': `url(#mk-${e.medium})`};
    if (e.both) attrs['marker-start'] = `url(#mk-${e.medium})`;
    if (!e.assess) attrs.class += ' faded';
    flows.append(s('polyline', attrs, s('title', {}, MEDIA[e.medium].label + (e.assess ? '' : ' (not assessed)') + ' — ' + e.basis)));
    if (!e.from) flows.append(s('circle', {cx: start[0], cy: start[1], r: 3.2, fill: 'var(--m-' + e.medium + ')'}));
    if (e.label) {
      let best = 0, seg = [pts[0], pts[1]];
      for (let i = 1; i < pts.length; i++) {
        const len = Math.abs(pts[i][0] - pts[i - 1][0]) + Math.abs(pts[i][1] - pts[i - 1][1]);
        if (len > best) { best = len; seg = [pts[i - 1], pts[i]]; }
      }
      const mx = (seg[0][0] + seg[1][0]) / 2, my = (seg[0][1] + seg[1][1]) / 2;
      const vertical = seg[0][0] === seg[1][0];
      const left = e.label_side === 'left';
      labels.append(s('text', {class: 'lb', fill: 'var(--m-' + e.medium + ')',
        x: vertical ? mx + (left ? -6 : 6) + (flow && !left && e.medium !== 'aux' ? 26 : 0) : mx,
        y: vertical ? my + 4 : my - (flow && e.medium !== 'aux' ? 12 : 6),
        'text-anchor': vertical ? (left ? 'end' : 'start') : 'middle'}, e.label));
    }
    if (flow && e.medium !== 'aux' && e.assess && !e.value_at_station) {  // quantity slot on the longest segment; aux amounts are listed under B
      let len = -1, a, b;
      for (let i = 1; i < pts.length; i++) {
        const l = Math.abs(pts[i][0] - pts[i - 1][0]) + Math.abs(pts[i][1] - pts[i - 1][1]);
        if (l > len) { len = l; a = pts[i - 1]; b = pts[i]; }
      }
      const px = (a[0] + b[0]) / 2, py = (a[1] + b[1]) / 2;
      labels.append(s('g', {class: 'pill'}, s('rect', {x: px - 26, y: py - 7.5, width: 52, height: 15, rx: 7.5, stroke: 'var(--m-' + e.medium + ')'}),
        s('text', {x: px, y: py + 3.5, 'text-anchor': 'middle'}, MISSING), s('title', {}, MEDIA[e.medium].label + ': amount MISSING')));
    }
  });
  T.nodes.forEach(n => {
    const r = rect[n.id], cx = r.x + r.w / 2;
    const body = flow
      ? [s('text', {class: 't', x: cx, y: r.y + 19, 'text-anchor': 'middle'}, n.label),
         n.kind === 'unassessed' ? s('text', {class: 's', x: cx, y: r.y + 44, 'text-anchor': 'middle'}, 'not assessed') : null,
         n.slots.map((k, i) => [s('text', {class: 'sk', x: r.x + 10, y: r.y + 37 + i * 15}, SLOT_LABEL[k]),
           s('text', {class: 'sv', x: r.x + r.w - 10, y: r.y + 37 + i * 15, 'text-anchor': 'end'}, MISSING)])]
      : [s('text', {class: 't', x: cx, y: r.y + (n.sub ? 25 : 34), 'text-anchor': 'middle'}, n.label),
         n.sub ? s('text', {class: 's', x: cx, y: r.y + 42, 'text-anchor': 'middle'}, n.sub) : null];
    const g = s('g', {class: 'nd ' + n.kind + (n.id === selId ? ' on' : '')},
      s('rect', {x: r.x, y: r.y, width: r.w, height: r.h, rx: n.kind === 'terminal' ? Math.min(r.h / 2, 18) : 7}),
      body,
      s('title', {}, n.label + (n.sub ? ' — ' + n.sub : '') + '\nClick for description'));
    nodes.append(s('a', {href: '#' + (flow ? 'flow' : 'plant') + '/' + n.id}, g));
  });
  svg.append(flows, labels, nodes);
  const sel = T.nodes.find(n => n.id === selId);
  m.append(h('div', {class: 'stage' + (sel ? ' sel' : '')}, h('div', {class: 'diagram'}, svg), sel ? stationCard(T, sel, flow) : null));
  const sample = k => { const e = s('svg', {width: 42, height: 12, viewBox: '0 0 42 12'});
    e.append(s('line', {...lineAttrs(k), x1: 2, y1: 6, x2: 40, y2: 6})); return e; };
  const box = dash => { const e = s('svg', {width: 26, height: 16, viewBox: '0 0 26 16'});
    e.append(s('rect', {x: 1, y: 1, width: 24, height: 14, rx: 3, fill: 'none', stroke: 'var(--node-edge)', ...(dash ? {'stroke-dasharray': dash === 'dot' ? '2 3' : '4 3'} : {})})); return e; };
  m.append(h('div', {class: 'legend'}, Object.entries(MEDIA).map(([k, v]) => h('span', {}, sample(k), v.label)),
    h('span', {}, box(true), 'Outside the provisional boundary (CONTRACT §4)'),
    T.nodes.some(n => n.kind === 'unassessed') ? h('span', {}, box('dot'), 'Not assessed until clarified by the owner') : null));
  if (flow) {
    const name = id => (T.nodes.find(n => n.id === id) || {}).label || id;
    const series = T.nodes.filter(n => n.kind === 'device' && n.slots.includes('loss'));  // inside the boundary, with a loss slot
    const bItems = T.edges.filter(e => e.medium === 'aux').map(e => name(e.to) + (e.label ? ' — ' + e.label : ''));
    const dl = rows => h('dl', {}, rows.flatMap(([k, v]) => [h('dt', {}, k), h('dd', {}, v)]));
    m.append(h('div', {class: 'accts'},
      h('div', {class: 'acct'}, h('h3', {}, 'A — series path'),
        dl([['E in (PV DC share, allocation)', MISSING], ['E AC out (FC inverter)', MISSING],
            ...series.map(n => ['loss ' + n.label, MISSING]),
            ['battery stock change', MISSING]])),
      h('div', {class: 'acct'}, h('h3', {}, 'B — auxiliary consumers'),
        dl([...bItems.map(x => [x, MISSING]), ['total B', MISSING]]),
        T.nodes.filter(n => n.kind === 'unassessed').map(n => h('p', {class: 'mute', style: 'margin:6px 0 0;font-size:12.5px'},
          n.label + ': not assessed until clarified by the owner.'))),
      h('div', {class: 'acct'}, h('h3', {}, 'C — system efficiency'),
        h('p', {class: 'mute', style: 'margin:0;font-size:13px'}, 'Not reported until compression and battery have a status (CONTRACT §4). ',
          'A and B are shown side by side without a summed total. While any item is MISSING, dependent totals stay open (§7).'))));
  }
  m.append(h('p', {class: 'mute'}, 'Hover a line or box for its basis. Dots mark where a consumer is tapped from the auxiliary line; ',
    'which supplier (house grid, separate PV battery system, internal bus) feeds each consumer is still open, except the water pump (house grid).'));
}

// ----- Devices -----
function devices() {
  const m = main(); m.replaceChildren();
  m.append(h('p', {class: 'mute'}, D.devices.length + ' files in plant/. ',
    D.topology.found ? 'Order follows the plant diagram; files not in it come last.' : 'Alphabetical order (no topology file).',
    ' Click a row for details.'));
  const head = ['Device', 'Params with value', 'Model module', 'Test files', 'Accounting refs', 'Validated (layer 3)', 'Status labels (count)', 'UNVERIFIED', 'Open', 'Read errors'];
  const rows = D.devices.map(d => {
    const withV = d.params.filter(p => p.has_value).length;
    const open = d.open.length + d.doc_lines.length;
    const r = tr([
      h('td', {}, h('strong', {}, d.stem), d.title ? h('div', {class: 'mute'}, d.title) : null),
      num(withV + ' / ' + d.params.length),
      h('td', {}, d.model ? 'yes' : '–', d.scenario ? h('div', {class: 'mute'}, '+ scenario') : null),
      num(d.tests.length || '–'), num(d.accounting_refs.length || '–'), num('–'),
      h('td', {}, chips(d.labels.map(([k, n]) => k + ' ' + n))),
      num(d.unverified || '–'), num(open || '–'),
      h('td', {class: d.errors.length ? 'n err' : 'n'}, d.errors.length || '–'),
    ], {class: 'row', tabindex: '0'});
    const go = () => location.hash = '#device/' + d.stem;
    r.addEventListener('click', go); r.addEventListener('keydown', e => e.key === 'Enter' && go());
    return r;
  });
  m.append(table(head, rows));
  m.append(h('div', {class: 'note'},
    h('strong', {}, 'Columns. '), 'Params with value: parameters whose TOML entry has a value field / all parameters (the value itself is not read). ',
    'Model module: src/verlustmappe/devices/<name>.py exists. Test files: tests calling the model module or naming a parameter key. ',
    'Accounting refs: modules in accounting/ naming a parameter key or calling the model module — not proof of correct booking. ',
    'Validated: always empty until layer-3 validation exists (CONTRACT §3, D34). UNVERIFIED: occurrences of the word anywhere in the TOML file; the device page lists line numbers and TOML tables (no text). ',
    'Open: [open] entries plus marker lines in documents naming the file.'));
}

function device(stem) {
  const d = byDev[stem], m = main(); m.replaceChildren();
  if (!d) return devices();
  m.append(h('p', {}, link('#devices', '← Devices')),
    h('h2', {}, d.stem + (d.title ? ' — ' + d.title : '')), h('div', {class: 'path mute'}, d.file));
  if (d.errors.length) m.append(h('h3', {class: 'err'}, 'Read errors'), h('ul', {class: 'q err'}, d.errors.map(e => h('li', {}, e))));
  m.append(h('h3', {}, 'Parameters'));
  m.append(table(['Key', 'Status', 'Unit', 'Value field', 'Source'], d.params.map(p =>
    tr([h('span', {class: 'mono'}, p.key), h('span', {class: 'chip'}, p.status), p.unit, p.has_value ? 'present' : 'absent', p.source]))));
  m.append(h('h3', {}, 'UNVERIFIED mentions in ' + d.file));
  m.append(table(['Line', 'TOML table', 'Count'], d.unverified_at.map(x => tr([num(x.line), h('span', {class: 'mono'}, x.table), num(x.count)])),
    {empty: 'None.'}));
  m.append(h('h3', {}, 'Open entries in TOML'));
  m.append(d.open.length ? h('ul', {class: 'q'}, d.open.map(q => h('li', {}, q))) : h('p', {class: 'mute'}, 'None.'));
  m.append(h('h3', {}, 'Document lines naming this file'));
  m.append(table(['File', 'Line', 'Text'], d.doc_lines.map(x => tr([x.file, x.line, x.text])), {empty: 'None.'}));
  m.append(h('h3', {}, 'Code'));
  m.append(h('p', {}, 'Model module: ', d.model ? link('#code/' + d.model, d.model) : '–',
    d.scenario ? [' · Scenario: ', link('#code/' + d.scenario, d.scenario)] : null));
  m.append(h('p', {}, 'Referenced by: ', d.refs.length ? d.refs.flatMap(r => [link('#code/' + r, r), ' ']) : '–'));
  m.append(h('p', {}, 'Tests: ', d.tests.length ? chips(d.tests) : '–'));
}

// ----- Open items -----
function openItems() {
  const m = main(); m.replaceChildren();
  const used = new Set();
  D.devices.forEach(d => {
    d.doc_lines.forEach(x => used.add(x.file + ':' + x.line));
    if (!d.open.length && !d.doc_lines.length) return;
    m.append(h('h3', {}, link('#device/' + d.stem, d.stem), d.title ? h('span', {class: 'mute'}, ' — ' + d.title) : null));
    if (d.open.length) m.append(h('ul', {class: 'q'}, d.open.map(q => h('li', {}, q, h('span', {class: 'mute'}, '  (' + d.file + ' [open])')))));
    if (d.doc_lines.length) m.append(h('ul', {class: 'q'}, d.doc_lines.map(x => h('li', {}, x.text, h('span', {class: 'mute'}, '  (' + x.file + ':' + x.line + ')')))));
  });
  const rest = D.doc_markers.filter(x => !used.has(x.file + ':' + x.line));
  m.append(h('h2', {}, 'Marker lines in documents not tied to a plant file'));
  m.append(table(['File', 'Line', 'Text'], rest.map(x => tr([x.file, num(x.line), x.text]))));
  const code = D.modules.filter(x => x.markers.length);
  m.append(h('h2', {}, 'Marker lines in code'));
  m.append(table(['Module', 'Line', 'Text'], code.flatMap(x => x.markers.map(k => tr([link('#code/' + x.id, x.id), num(k.line), k.text])))));
}

// ----- Code (static structure) -----
const SIG_HEAD = ['Signal', 'Kind', 'Unit', 'Basis', 'Time window', 'Code match', 'Status'];
const signalRows = list => list.map(s => tr([
  s.name, s.kind || '', s.unit || '', s.basis || '', s.window || '',
  s.checks.length ? s.checks.map(c => h('div', {}, c.name + (c.missing_in.length ? ' missing in: ' + c.missing_in.join(', ') : ' found')))
    : h('span', {class: 'mute'}, 'no code names'),
  s.confirmed ? 'confirmed' : h('span', {class: 'err'}, 'unconfirmed')]));

function codeNav(cur) {
  const groups = {};
  D.modules.forEach(m => (groups[m.group] ||= []).push(m));
  return h('nav', {}, link('#code', 'Overview'), Object.keys(groups).sort().map(g => [h('h3', {}, g),
    groups[g].map(m => h('a', {href: '#code/' + m.id, class: cur === m.id ? 'on' : ''}, m.stem))]));
}

function code(id) {
  const x = byId[id], body = h('div', {});
  main().replaceChildren(h('div', {class: 'cols'}, codeNav(id), body));
  if (!x) {
    body.append(h('p', {class: 'mute'}, D.modules.length + ' modules. Calls, callers and test references are AST name matches, not proof of runtime calls or data flow.'));
    body.append(h('h2', {}, 'Signals with semantics'));
    body.append(D.semantics_found ? table(SIG_HEAD, signalRows(D.signals))
      : h('p', {class: 'mute'}, 'No semantics file at ' + D.semantics_path));
    return;
  }
  body.append(h('h2', {}, x.id), h('div', {class: 'path mute'}, x.path));
  body.append(h('h3', {}, 'Classes and functions'));
  x.symbols.forEach(s => {
    body.append(h('p', {}, h('strong', {}, s.name), ' ', h('span', {class: 'mute'}, s.kind + ', line ' + s.line + (s.doc ? ' · ' + s.doc : ''))));
    (s.methods || [s]).forEach(f => body.append(h('div', {class: 'mono'},
      (s.methods ? s.name + '.' : '') + f.name + '(' + f.args.map(a => a.name + (a.ann ? ': ' + a.ann : '')).join(', ') + ')')));
  });
  const sigs = D.signals.filter(s => x.signals.some(r => r.name === s.name));
  if (sigs.length) body.append(h('h3', {}, 'Signals with semantics'), table(SIG_HEAD, signalRows(sigs)));
  body.append(h('h3', {}, 'Calls'), h('p', {}, x.calls_to.length ? x.calls_to.flatMap(c => [link('#code/' + c, c), ' ']) : '–'));
  body.append(h('h3', {}, 'Called by'));
  body.append(table(['File', 'Symbol', 'Lines'], x.called_by.map(e => tr([e.module ? link('#code/' + e.module, e.module) : e.file, e.symbol, e.lines.join(', ')]))));
  body.append(h('h3', {}, 'Tests'), h('p', {}, x.tests.length ? chips(x.tests) : '–'));
  body.append(h('h3', {}, 'Plant files'), h('p', {}, x.toml.length ? x.toml.flatMap(t => {
    const st = t.file.split('/').pop().replace('.toml', '');
    return [byDev[st] ? link('#device/' + st, t.file) : t.file, ' '];
  }) : '–'));
  if (x.markers.length || x.doc_markers.length) {
    body.append(h('h3', {}, 'Marker lines'));
    body.append(table(['File', 'Line', 'Text'], [...x.markers.map(k => tr([x.path, num(k.line), k.text])), ...x.doc_markers.map(k => tr([k.file, num(k.line), k.text]))]));
  }
}

function route() {
  const hash = decodeURIComponent(location.hash.slice(1));
  const [view, ...rest] = hash.split('/'), arg = rest.join('/');
  const tab = view === 'device' ? 'devices' : ['devices', 'open', 'code'].includes(view) ? view : 'plant';
  renderTabs(tab);
  if (view === 'device') device(arg);
  else if (view === 'flow') plant(true, arg);
  else if (view === 'open') openItems();
  else if (view === 'code') code(arg);
  else if (view === 'devices') devices();
  else plant(false, arg);
  if (!['plant', 'flow'].includes(view) || !['plant', 'flow'].includes(lastView)) window.scrollTo(0, 0);
  lastView = view;
}
let lastView = null;
renderHeader();
window.addEventListener('hashchange', route);
route();
</script></body></html>
"""


def render(data, mode):
    payload = json.dumps({**data, "mode": mode}, ensure_ascii=False).replace("</", "<\\/")
    return TEMPLATE.replace("__DATA__", payload)


def serve(a, port):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0] not in ("/", "/index.html"):
                self.send_error(404)
                return
            try:
                body, code = render(build(a), "live").encode("utf-8"), 200
            except Exception as e:  # show the failure instead of a stale page
                body, code = f"Observer build failed: {type(e).__name__}: {e}".encode("utf-8"), 500
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8" if code == 200 else "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    httpd = HTTPServer((LIVE_HOST, port), Handler)
    print(f"Live view: http://{LIVE_HOST}:{port}/  (reload to refresh, Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="Project root")
    ap.add_argument("--pkg", default="src/verlustmappe", help="Package directory relative to the project root")
    ap.add_argument("--extra", nargs="*", default=["tools", "tests"], help="Additional folders to scan for callers")
    ap.add_argument("--tests", default="tests", help="Test directory name")
    ap.add_argument("--plant", default="plant", help="Directory containing plant TOML files")
    ap.add_argument("--docs", nargs="*", default=["CONTRACT.md", "START.md"], help="Documents to scan for markers")
    ap.add_argument("--semantics", default="../_overview/semantics.toml", help="Semantics file")
    ap.add_argument("--topology", default="tools/project_observer/topology.toml", help="Plant diagram description")
    ap.add_argument(
        "--out",
        default="tools/project_observer/output/overview.html",
        help="HTML output file (inside tools/project_observer/output/)",
    )
    ap.add_argument("--serve", action="store_true", help=f"Serve a live view on {LIVE_HOST} instead of writing a file")
    ap.add_argument("--port", type=int, default=8765, help="Port for --serve (default 8765)")
    a = ap.parse_args()

    if a.serve:
        serve(a, a.port)
        return

    root = Path(a.root).expanduser().resolve()
    out = (root / a.out).resolve()
    allowed_output = (root / "tools/project_observer/output").resolve()
    if out.parent != allowed_output:
        ap.error(f"--out must be directly inside {allowed_output}")

    data = build(a)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(data, "snapshot"), encoding="utf-8")
    print(f"{len(data['devices'])} plant files, {len(data['modules'])} modules, "
          f"{len(data['signals'])} signals -> {out}")
    if not data["semantics_found"]:
        print(f"Note: no semantics file found at {data['semantics_path']}")


if __name__ == "__main__":
    main()
