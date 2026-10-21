"""Probe 4: committed data, cited sources, and things planned but not in the code yet."""
from _common import check, info, summary, REPO
import os, numpy as np, pandas as pd
from verlustmappe.loaders.grafana import map_fc
from verlustmappe.hydrogen.temperature_model import isothermal_work_mol_integral, temperature_corrected_mass
from verlustmappe import registry as R

pv = pd.read_csv(os.path.join(REPO, "data/processed/pv_retro/pv_merged.csv"), index_col=0, parse_dates=True)
check("PV data: the grid_Hz column contains a counter-like value in its first rows",
      (pv["grid_Hz"] > 1000).any(),
      "fix the merge that produced data/processed/pv_retro/pv_merged.csv (column mix-up in the head rows)",
      f"max grid_Hz = {pv['grid_Hz'].max():.2f}")
dt = pv.index.to_series().diff().dt.total_seconds()
info(f"PV data is {dt.median()/60:.0f}-min sampled: low-load efficiency bins may come from non-simultaneous DC/AC snapshots")
info(f"PV dataset peak {pv['ac_power_W'].max()/1e3:.1f} kW is far below the building array: this file covers one inverter/sub-array, "
     "so do not compare it with a whole-array reference")

fc = map_fc(pd.read_csv(os.path.join(REPO, "data/processed/fc_retro/fc_merged.csv"), index_col=0, parse_dates=True))
f = fc.dropna(subset=["fc_power_W", "run_hours", "total_run_energy"])
t = (f.index - f.index[0]).total_seconds().values
on = (np.diff(t) == 5) & (f["fc_power_W"].values[:-1] > 500)
rate = np.median(np.diff(f["run_hours"].values)[on] / 5)
dd = open(os.path.join(REPO, "docs/03_data_dictionary.md")).read()
check("Data dictionary labels run_hours as hours, but it advances 1.0 per SECOND of operation",
      abs(rate - 1) < 0.01 and "| `run_hours`, `total_run_energy` | h," in dd,
      "docs/03_data_dictionary.md: unit is s; note in the entry that the counter advances 1.0 per second of operation",
      f"median d(run_hours)/dt = {rate:.3f}")
J = np.trapezoid(f["fc_power_W"].values, t); cnt = f["total_run_energy"].values[-1] - f["total_run_energy"].values[0]
info(f"'total_run_energy' tracks terminal energy at ~{J/cnt:.2f} J/count ({J/1e6:.2f} MJ / {cnt:.0f} counts). "
     "Inferred unit, not confirmed: a free cross-check for E_out once the unit is verified")

# the registry's compression anchor vs its own cited source
detail = []; etas = []
T = 293.15
for nm3 in (33.22, 33.22-(1.86+0.75*(9.08-1.86))):
    mol = nm3/22.414*1000
    for ps in (40.0, 10.0):
        w = isothermal_work_mol_integral(mol, 40, 200, T, p_suction_abs_bar=ps)
        if ps == 10.0: etas += [w/56.36, w/100.2]
        detail.append(f"{nm3:.2f} Nm3, suction {ps:.0f} bar: W_ideal {w:.2f} kWh -> eta {w/56.36*100:.2f}% / {w/100.2*100:.2f}%")
val = R.get("comp.overall_efficiency"); band = R.entry("comp.overall_efficiency")["uncertainty"]
check("comp.overall_efficiency is inconsistent with its own cited source (Bovo IJHE 2023, Tab. 3)",
      min(etas) > val*(1+band),
      "registry.py: recompute from the paper's own numbers (10-bar booster inlet, 56.36/100.2 kWh compression, fill-integral "
      "ideal work) and widen the band - the two measured cycles alone differ by x1.8",
      f"registered {val} +-{band}; recomputed range " + "\n    " + "\n    ".join(detail))

m_gas = temperature_corrected_mass(201.01325, 800, 20)
ratio = (1430*0.47 + m_gas*10.3) / (m_gas*10.3)
import inspect as _insp
from verlustmappe.hydrogen.temperature_model import gs_fit_from_pressure_decay as _gs
check("GS fit uses the gas heat capacity only; the steel of the tank(s) stores far more heat",
      ratio > 3 and "steel_mass_kg" not in _insp.signature(_gs).parameters,
      "temperature_model.gs_fit_from_pressure_decay: add m_steel*c_steel (parameter steel_mass_kg, c ~ 0.46-0.48 kJ/kgK) "
      "to the heat capacity; report the gas-only and combined tau",
      f"gas {m_gas:.1f} kg -> {m_gas*10.3:.0f} kJ/K; steel up to ~{1430*0.47:.0f} kJ/K incl. frame -> GS low by UP TO x{ratio:.1f}")
st = str(R.get("stor.type"))
check("Registry describes the store as ONE steel cylinder; it is a 16 x 50 L bundle (two bundles on site, sensors on one)",
      "16" not in st and "bundle" not in st.lower(),
      "registry.py stor.type + route2_tank_pv.py: model bundles; add a required isolation flag so V = 800 L only holds "
      "while the instrumented bundle is valved off from the second one", f"stor.type = '{st}'")
readme = open(os.path.join(REPO, "README.md")).read()
info("README says the tank temperature sensor is 'not yet purchased' - matches the current plan; update the wording the day it is installed")
import glob
has_leak = any("leak" in open(f).read().lower() and "def " in open(f).read() and "night" in open(f).read().lower()
               for f in glob.glob(os.path.join(REPO, "src/verlustmappe/**/*.py"), recursive=True))
info("No night-decay leak-rate function exists yet (planned: leak rate from the overnight pressure curve, "
     "separated from thermal relaxation - fit p/(Z T), not raw p)")
summary()
