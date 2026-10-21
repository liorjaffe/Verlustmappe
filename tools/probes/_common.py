"""Helpers for the Verlustmappe probe scripts.

What this is:
  A set of independent checks against the code in src/verlustmappe. They report
  the CURRENT state, one line per finding:
    [BUG]  the problem is present right now
    [OK]   the check passes (positive checks, e.g. "physics constant is correct")
    [INFO] an observation about data or docs; nothing to fix in code
  After a change, re-run: the matching line should turn from [BUG] to [OK].

What this is NOT:
  Not a patch, not a test suite for tests/run_all.py, and nothing here is
  imported by the package. The one-line hint on each [BUG] says what to change;
  you decide whether and when.

Location: put this folder at <repo>/tools/probes/ (the repo root is found
automatically) or set VERLUSTMAPPE_REPO.
Run: python3 tools/probes/run_probes.py
Optional: pip install CoolProp (only the Z-table cross-check needs it).
"""
import os, sys
def _find_repo():
    env = os.environ.get("VERLUSTMAPPE_REPO")
    if env: return env
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.isdir(os.path.join(d, "src", "verlustmappe")): return d
        d = os.path.dirname(d)
    return os.path.join(os.path.dirname(d), "Verlustmappe")
REPO = _find_repo()
sys.path.insert(0, os.path.join(REPO, "src"))

RESULTS = []
def check(name, bug_present, hint="", detail=""):
    tag = "BUG" if bug_present else "OK"
    RESULTS.append((tag, name))
    print(f"[{tag}] {name}")
    if hint: print(f"    hint: {hint}")
    if detail: print(f"    {detail}")
def info(name, detail=""):
    print(f"[INFO] {name}" + (f"\n    {detail}" if detail else ""))
def summary():
    n = sum(1 for t, _ in RESULTS if t == "BUG")
    print(f"\n{n} open / {len(RESULTS)} checks")
def reset_volume(v=800.0):
    from verlustmappe import registry as R
    R.REGISTRY["stor.volume_L"]["value"] = v
