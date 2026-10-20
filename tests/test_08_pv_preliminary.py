"""PV preliminary channel: physics back-checks against hand calculations and
the MEASURED SMA telemetry (the one real PV datapoint set we have)."""
import _path
import numpy as np
from verlustmappe.devices.pv_prelim_channel import pv_account, cell_temperature
from verlustmappe import registry as R

def main():
    # 1. cell temperature model: NOCT definition = 20 C ambient, 800 W/m2 -> NOCT
    assert abs(cell_temperature(20.0, 800.0) - 43.0) < 1e-9, cell_temperature(20.0, 800.0)
    # and the standard operating case 25 C ambient: T_cell = 48 C
    assert abs(cell_temperature(25.0, 800.0) - 48.0) < 1e-9
    # 2. temp derating: gamma -0.29%/K * (43-25) K = -5.22%
    gamma = R.get("pv.p_tc_pmax_per_K")
    assert abs((1 + gamma * 18.0) - (1 - 0.29/100*18)) < 1e-12
    # 3. loss chain closure: AC = STC * prod(factors) exactly as documented
    r = pv_account(H_poa_kWh_m2=100.0, A_array_m2=10.0, months=1)
    expected_ac = 100.0*10.0*0.22 * (1-R.get("pv.soiling_rel")) * (1-R.get("pv.mismatch_rel")) \
        * (1-R.get("pv.shading_rel")) * (1 + gamma*(r["T_cell_C"]-25.0)) \
        * (1 + R.get("pv.bifacial_gain_frac")) \
        * (1-R.get("cable.dc_loss_rel")) * R.get("inv_pv.eta_euro") * (1-R.get("cable.ac_loss_rel"))
    assert abs(r["e_ac_kWh"] - expected_ac) < 1e-9
    # 4. capture ratio definition: E_DC / E_STC
    assert abs(r["capture_ratio"] - r["e_dc_kWh"]/r["e_stc_kWh"]) < 1e-9
    # 5. every bar labelled PRELIM in preliminary mode (Rule 3)
    assert all(b["status"] == "PRELIM" for b in r["bars"])
    # 6. measured mode: bars stay but AC follows the measurement
    rm = pv_account(H_poa_kWh_m2=100.0, A_array_m2=10.0,
                    E_dc_measured_kWh=200.0, E_ac_measured_kWh=190.0, months=1, mode="measured")
    assert abs(rm["e_ac_kWh"] - 190.0) < 1e-9 and rm["mode"] == "measured"
    assert any(b["status"] == "MEASURED" for b in rm["bars"])
    print("PASS 08a PV prelim math: NOCT model, derating, chain closure, labels")

def backcheck_against_sma():
    """Compare the PRELIM inverter assumption against the MEASURED SMA telemetry."""
    import pandas as pd, os
    from verlustmappe.loaders.grafana import map_pv
    df = map_pv(pd.read_csv(os.path.join(_path.ROOT, "data/processed/pv_retro/pv_merged.csv"),
                            index_col=0, parse_dates=True))
    both = df[["dc_power_W", "ac_power_W"]].dropna()
    both = both[both["dc_power_W"] > 500]
    # measured energy-weighted conversion efficiency over the whole window:
    eta_measured = both["ac_power_W"].sum() / both["dc_power_W"].sum()
    eta_prelim = R.get("inv_pv.eta_euro")
    dev = abs(eta_measured - eta_prelim) / eta_measured
    print("PASS 08b inverter backcheck: measured (energy-weighted) %.4f vs PRELIM Euro %.4f -> deviation %.1f%%"
          % (eta_measured, eta_prelim, dev*100))
    # the PRELIM Euro value must be within 2% of the measured one (sanity, not proof:
    # different load distributions can legitimately shift Euro weighting)
    assert dev < 0.02, "PRELIM Euro efficiency inconsistent with own measured telemetry"
    # DC cable + MPPT cannot be separated in the measured data (inverter reports DC
    # at its terminals), so the DC-cable bar remains unverifiable - stated limit.
    return eta_measured

if __name__ == "__main__":
    main()
    backcheck_against_sma()
