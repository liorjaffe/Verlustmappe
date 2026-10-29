"""The retired PV dataset label (DECISIONS D33) must not appear in the new core.

Word-boundary, case-sensitive: words like "mismatch" are not hits.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW_CORE = ("models", "sim", "scenarios", "calibration")
LABEL = re.compile(r"\bSMA\b")


def test_new_core_has_no_retired_label():
    hits = []
    for d in NEW_CORE:
        base = os.path.join(ROOT, "src", "verlustmappe", d)
        for dp, _, fs in os.walk(base):
            for f in fs:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(dp, f)
                with open(path, encoding="utf-8") as fh:
                    for n, line in enumerate(fh, 1):
                        if LABEL.search(line):
                            hits.append(f"{os.path.relpath(path, ROOT)}:{n}")
    assert not hits, hits


def test_guard_pattern_word_boundary():
    assert LABEL.search("the SMA dataset")
    assert not LABEL.search("mismatch")
