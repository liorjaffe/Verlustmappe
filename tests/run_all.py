import subprocess, sys, glob, os
here = os.path.dirname(os.path.abspath(__file__))
fails = 0
for f in sorted(glob.glob(os.path.join(here, "test_*.py"))):
    r = subprocess.run([sys.executable, f], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip()[-800:])
    fails += r.returncode != 0
print("ALL PASS" if not fails else f"{fails} FAILED"); sys.exit(fails)
