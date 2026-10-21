"""Run all four probes. python3 tools/probes/run_probes.py  (CoolProp optional, for the Z check)."""
import subprocess, sys, os
here = os.path.dirname(os.path.abspath(__file__))
for f in ("p1_hydrogen_physics.py", "p2_loss_map_devices.py", "p3_loaders_timebase.py", "p4_data_and_sources.py"):
    print("#" * 10, f); sys.stdout.flush()
    subprocess.run([sys.executable, os.path.join(here, f)])
