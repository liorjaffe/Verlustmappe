"""Probe 2: loss map, RTE, devices, PV channel (demo cycle of test_03 as the reference case)."""
from _common import check, summary, reset_volume
import numpy as np, pandas as pd
from verlustmappe.balance.d_loss_map import loss_map
from verlustmappe.hydrogen import h2_from_tank_pressure as _tank
from verlustmappe.devices import ElectrolyzerUnit, PVSystem, pv_account
import inspect as _inspect
def h2_from_tank_pressure(*a, **k):
    if "bundle_isolated" in _inspect.signature(_tank).parameters: k.setdefault("bundle_isolated", True)
    return _tank(*a, **k)
reset_volume(1000.0)
n = 361; idx = pd.date_range("2026-01-01", periods=n, freq="60s")
dfc = pd.DataFrame({"power_W": np.full(n, 2400.0), "el_stack_current_A": np.full(n, 10.0)}, index=idx)
idx2 = pd.date_range("2026-01-02", periods=121, freq="60s")
dfd = pd.DataFrame({"fc_power_W": np.full(121, 2500.0), "fc1_stack_current_A": np.full(121, 19.39),
                    "fc2_stack_current_A": np.full(121, 19.39)}, index=idx2)
target = loss_map(dfc, dfd)["devices"]["EL"]["h2"]["kg"]; lo, hi = 50.0, 300.0
for _ in range(60):
    mid = (lo+hi)/2; lo, hi = (mid, hi) if h2_from_tank_pressure(50.0, mid)["kg"] < target else (lo, mid)
demo = loss_map(dfc, dfd, tank_p_start_barg=50.0, tank_p_end_barg=(lo+hi)/2, eta_inverter=0.96)

check("eta_inverter, which test_03 passes, is silently swallowed and 0.94 is used",
      demo["rte"]["breakdown"]["inverter_eta"] == 0.94,
      "d_loss_map.py: make eta_inverter an explicit parameter; do not let unknown kwargs vanish (**kw_e)",
      f"inverter eta actually used: {demo['rte']['breakdown']['inverter_eta']}")
check("FC control energy is counted for 1 module although 2 stack-current columns exist",
      abs(demo["devices"]["FC"]["control_energy_kWh_envelope"] - 0.3) < 1e-9,
      "devices/fuel_cell.py: count the modules from the stack-current columns as well",
      f"{demo['devices']['FC']['control_energy_kWh_envelope']} kWh = 150 W x 2 h x 1 module")
s = sum(b["kWh"] for b in demo["bars"]); gap = demo["rte"]["E_in_kWh"] - s - demo["rte"]["E_out_kWh"]
check("Loss map does not close: E_in != sum(bars) + E_out",
      abs(gap) > 0.1,
      "d_loss_map.py: in an open cycle the excess H2 consumption must appear as its own bar (or the map must refuse to close)",
      f"gap {gap:.3f} kWh")
check("A dryer-vent loss is booked although the tank holds 100% of production (no gas was lost)",
      abs(demo["h2_closure"]["gas_loss_estimate"]["fraction_of_production"]) < 1e-6
      and [b for b in demo["bars"] if "vent" in b["stage"]][0]["kWh"] > 0.3,
      "d_loss_map.py + test_03: book the vent only against the gas that actually left, or label the bar as an upper envelope not tied to this window")

c = dfc.copy(); c.iloc[:120, 0] = 20.0; c.iloc[:120, 1] = 0.0
el = ElectrolyzerUnit().account(c); l = loss_map(c, dfd)
check("Standby energy is counted twice in E_in (it is already inside E_EL)",
      abs(l["rte"]["E_in_kWh"] - (el["energy_in_kWh"] + l["rte"]["breakdown"]["DRY"] + l["rte"]["breakdown"]["CSU"] + el["standby_kWh"])) < 1e-9
      and el["standby_kWh"] > 0,
      "e_rte.storage_chain_rte: do not add E_standby again - it is a subset of E_el",
      f"standby {el['standby_kWh']:.3f} kWh inside E_EL {el['energy_in_kWh']:.3f}")

bad = loss_map(dfc, dfd, tank_p_start_barg=50, tank_p_end_barg=120)
check("No plausibility guards: a mismatched tank window gives RTE > 1 and a negative gas loss",
      bad["h2_balance"]["rte_closed"] > 1,
      "d_loss_map.py: raise or flag when rte_open/rte_closed > 1, gas loss < -uncertainty, or the tank window holds far more than production",
      f"rte_closed {bad['h2_balance']['rte_closed']:.2f}, gas loss {bad['h2_closure']['gas_loss_estimate']['fraction_of_production']*100:.0f}%")

try:
    PVSystem().account(100, 97, H_poa_kWh_m2=5); check("PVSystem.account crashes when irradiance is passed", False)
except KeyError as e:
    check("PVSystem.account crashes with KeyError when irradiance is passed", True,
          "devices/pv_measured.py + registry.py: add pv.p_dc_stc_W (BACKLOG, None) and guard `if pstc`", str(e))

r = pv_account(H_poa_kWh_m2=160, A_array_m2=836); sb = sum(b["kWh"] for b in r["bars"])
check("PRELIM PV bars do not sum to the STC-to-AC loss (the bifacial gain has no bar)",
      abs((r["e_stc_kWh"]-r["e_ac_kWh"]) - sb) > 100,
      "pv_prelim_channel.py: add a bifacial bar (negative loss) so the bars close on STC -> AC",
      f"loss {r['e_stc_kWh']-r['e_ac_kWh']:.0f} kWh vs bars {sb:.0f} kWh")
m = pv_account(E_dc_measured_kWh=1000, E_ac_measured_kWh=972)
inv = [b for b in m["bars"] if b["stage"] == "Inverter conversion"][0]
check("In measured mode the inverter bar is labelled MEASURED but is computed from the PRELIM 0.98 value",
      inv["status"] == "MEASURED" and abs(inv["kWh"] - 28) > 1,
      "pv_prelim_channel.py: in measured mode the inverter bar = E_dc_measured - E_ac_measured (that IS measured)",
      f"bar {inv['kWh']:.1f} kWh vs measured loss 28 kWh")
check("In measured mode a DC cable loss is subtracted although DC is measured AT the inverter",
      any(b["stage"] == "DC cable" and b["kWh"] > 0 for b in m["bars"]),
      "pv_prelim_channel.py: skip the DC/AC cable bars when DC and AC are measured at the inverter terminals")
summary()
