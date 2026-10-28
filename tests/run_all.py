import subprocess, sys, glob, os
here = os.path.dirname(os.path.abspath(__file__))
fails = 0
# D9(c): legacy script tests only; pytest-style tests (test_30+) run via pytest -q
legacy = glob.glob(os.path.join(here, "test_0*.py")) + glob.glob(os.path.join(here, "test_1[0-2]*.py"))
for f in sorted(legacy):
    r = subprocess.run([sys.executable, f], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip()[-800:])
    fails += r.returncode != 0
print("ALL PASS" if not fails else f"{fails} FAILED"); sys.exit(fails)
