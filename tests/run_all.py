import subprocess, sys, glob, os
here = os.path.dirname(os.path.abspath(__file__))
fails = 0
# Script-style tests of the device models, by explicit name; pytest-style tests run via pytest -q
LEGACY = [
    "test_physics_constants_conversions.py",
    "test_hydrogen_routes.py",
    "test_loaders_regatron.py",
    "test_hydrogen_tank_thermal.py",
    "test_devices_pv_array_prelim.py",
    "test_loaders_solis.py",
    "test_devices_pv_array_f8.py",
    "test_devices_water.py",
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
