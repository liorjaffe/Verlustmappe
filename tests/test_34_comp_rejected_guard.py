"""comp.* is REJECTED (DECISIONS D11) and must not feed the new core.

Weak text guard: the new-core packages do not exist yet and models/params.py is not
built, so this only scans source text. It passes vacuously while no new-core file exists.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

NEW_CORE = ("models", "sim", "scenarios", "calibration")
KEY_USE = re.compile(r"""["']comp\.""")


def new_core_files():
    out = []
    for d in NEW_CORE:
        base = os.path.join(ROOT, "src", "verlustmappe", d)
        for dp, _, fs in os.walk(base):
            out += [os.path.join(dp, f) for f in fs if f.endswith(".py")]
    return out


def test_all_comp_keys_are_rejected():
    from verlustmappe import registry as R
    keys = [k for k in R.REGISTRY if k.startswith("comp.")]
    assert len(keys) == 6, keys
    assert all(R.entry(k)["status"] == "REJECTED" for k in keys), keys


def test_stor_p_work_stays_usable():
    from verlustmappe import registry as R
    assert R.entry("stor.p_work_barg")["status"] != "REJECTED"


def test_new_core_does_not_read_comp_keys():
    hits = []
    for f in new_core_files():
        with open(f, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if KEY_USE.search(line) or ("by_status" in line and "REJECTED" in line):
                    hits.append(f"{os.path.relpath(f, ROOT)}:{n}")
    assert not hits, hits
