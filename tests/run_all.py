import subprocess, sys, glob, os
here = os.path.dirname(os.path.abspath(__file__))
fails = 0
# D9(c): legacy script tests by explicit name; pytest-style tests (test_30+) run via pytest -q
LEGACY = [
    "test_01_constants_and_conversions.py",
    "test_02_hydrogen_routes.py",
    "test_03_full_chain.py",
    "test_04_real_fc_data.py",
    "test_05_analysis_methods.py",
    "test_06_regatron_loaders.py",
    "test_07_tank_thermal.py",
    "test_08_pv_preliminary.py",
    "test_09_solis_loader.py",
    "test_10_pv_f8.py",
    "test_11_water_system.py",
    "test_12_solis_live.py",
]
# C12: a script-style test file outside the list would pass silently under both runners
stray = [os.path.basename(f) for f in glob.glob(os.path.join(here, "test_*.py"))
         if os.path.basename(f) not in LEGACY and "def test_" not in open(f, encoding="utf-8").read()]
if stray:
    print(f"script-style test file outside the legacy list, use pytest style: {sorted(stray)}")
    sys.exit(1)
for name in LEGACY:
    r = subprocess.run([sys.executable, os.path.join(here, name)], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip()[-800:])
    fails += r.returncode != 0
print("ALL PASS" if not fails else f"{fails} FAILED"); sys.exit(fails)
