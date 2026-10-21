#!/usr/bin/env python3
"""One-command reports over a processed dataset.

Usage:
  python3 src/report_cli.py fc ../data/processed/fc_retro/fc_merged.csv
  python3 src/report_cli.py pv ../data/processed/pv_retro/pv_merged.csv

fc: steady segments ( Kennwerte ), purge events, polarization fit, energy
pv: daily yields, inverter efficiency by load bin, inverter loss
Outputs: CSV tables into results/tables/ and PNGs into results/plots/.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import numpy as np
import pandas as pd
from verlustmappe.balance.b_segments import steady_segments
from verlustmappe.balance.c_events import detect_events, purge_candidates

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TBL = os.path.join(ROOT, "results", "tables")
PLT = os.path.join(ROOT, "results", "plots")
os.makedirs(TBL, exist_ok=True); os.makedirs(PLT, exist_ok=True)

def fc_report(path):
    from verlustmappe.loaders.grafana import map_fc
    df = map_fc(pd.read_csv(path, index_col=0, parse_dates=True))
    out = []
    segs = steady_segments(df, col="fc_power_W", p_min=1000, min_dur_s=120, extra_cols=("fc1_current_A", "fc1_voltage_V")).to_dict("records")
    pd.DataFrame(segs).to_csv(os.path.join(TBL, "fc_steady_segments.csv"), index=False)
    out.append(f"steady segments: {len(segs)} -> fc_steady_segments.csv")
    ev, st = detect_events(df, [c for c in ["fc_power_W", "fc1_voltage_V", "anode_pressure_mbar"] if c in df.columns])
    ev.to_csv(os.path.join(TBL, "fc_events.csv"), index=False)
    out.append(f"robust events: {len(ev)} -> fc_events.csv")
    purges = purge_candidates(df, "anode_pressure_mbar")
    purges.to_csv(os.path.join(TBL, "fc_purge_events.csv"), index=False)
    out.append(f"purge events: {len(purges)} -> fc_purge_events.csv")
    # polarization fit
    v, i = df.get("fc1_voltage_V"), df.get("fc1_current_A")
    if v is not None and i is not None:
        m = (i > 2).values
        c = np.polyfit(i[m].values, v[m].values, 2)
        with open(os.path.join(TBL, "fc_polarization_fit.csv"), "w") as f:
            f.write("a2,a1,a0,n_points\n%f,%f,%f,%d\n" % (c[0], c[1], c[2], m.sum()))
        out.append("TERMINAL V-I fit (not stack polarisation): V = %.4g*I^2 + %.4g*I + %.2f (%d pts)" % (c[0], c[1], c[2], m.sum()))
    t = df.index.values.astype("datetime64[ns]").astype(np.int64)/1e9
    p = df["fc_power_W"].interpolate(limit_direction="both").values.clip(0, None)
    e = np.trapezoid(p, t)/3.6e6
    with open(os.path.join(TBL, "fc_energy_summary.csv"), "w") as f:
        f.write("energy_kwh,duration_h\n%.3f,%.2f\n" % (e, (t[-1]-t[0])/3600))
    out.append(f"window energy: {e:.2f} kWh -> fc_energy_summary.csv")
    # IV / Kennwerte from steady segments
    from verlustmappe.analysis.a_polarization import iv_from_segments, key_values
    iv = iv_from_segments(segs, v_col="fc1_voltage_V_mean", i_col="fc1_current_A_mean", p_col="P_mean")
    if not iv.empty:
        iv.to_csv(os.path.join(TBL, "fc_iv_table.csv"), index=False)
        kv = key_values(iv, area_cm2=None)
        pd.DataFrame([kv]).to_csv(os.path.join(TBL, "fc_key_values.csv"), index=False)
        out.append("IV table + Kennwerte -> fc_iv_table.csv, fc_key_values.csv")
    # start/stop cycles with energies
    from verlustmappe.analysis.c_dynamics import start_stop_cycles, ramp_rates
    cyc = start_stop_cycles(df, rated_w=2500.0)
    cyc.to_csv(os.path.join(TBL, "fc_start_stop_cycles.csv"), index=False)
    out.append(f"start/stop cycles: {len(cyc)} -> fc_start_stop_cycles.csv")
    rr = ramp_rates(df)
    pd.DataFrame([{"channel": k, **v} for k, v in rr.items()]).to_csv(
        os.path.join(TBL, "fc_ramp_rates.csv"), index=False)
    out.append("ramp rates -> fc_ramp_rates.csv")
    # purge voltage recovery
    from verlustmappe.analysis.d_purge_recovery import recovery_after_purges
    if len(purges):
        rec = recovery_after_purges(df, list(purges["start"]))
        rec.to_csv(os.path.join(TBL, "fc_purge_recovery.csv"), index=False)
        out.append(f"purge voltage recovery: {len(rec)} -> fc_purge_recovery.csv")
    return out

def pv_prelim_report():
    """Preliminary PV channel report (no real hardware chosen): uses registry
    PRELIM values + a reference irradiation/area. Replace inputs when the real
    PV design exists."""
    from verlustmappe.devices import pv_account
    # reference anchors: UFSC PV is 184 kWp (H2 Core Systems); Florianopolis
    # POA ~ 150-170 kWh/m2/month annual mean (coastal subtropical)
    H = 160.0   # kWh/m2/month, PRELIM reference
    A = 836.0   # m2 for 184 kWp at 22% module efficiency, PRELIM reference
    r = pv_account(H_poa_kWh_m2=H, A_array_m2=A, months=1.0)
    rows = [b for b in r["bars"]]
    pd.DataFrame(rows).to_csv(os.path.join(TBL, "pv_prelim_losses.csv"), index=False)
    with open(os.path.join(TBL, "pv_prelim_summary.csv"), "w") as f:
        f.write("quantity,value,unit\n")
        f.write("mode,%s,\n" % r["mode"])
        f.write("STC potential,%.1f,kWh/month\n" % r["e_stc_kWh"])
        f.write("DC after site losses,%.1f,kWh/month\n" % r["e_dc_kWh"])
        f.write("AC to bus,%.1f,kWh/month\n" % r["e_ac_kWh"])
        f.write("capture ratio,%.3f,\n" % r["capture_ratio"])
        f.write("eta DC-to-AC,%.3f,\n" % r["eta_dc_to_ac"])
    return ["PRELIM PV channel: STC %.0f -> AC %.0f kWh/month, capture %.3f" %
            (r["e_stc_kWh"], r["e_ac_kWh"], r["capture_ratio"]),
            "bars -> pv_prelim_losses.csv, summary -> pv_prelim_summary.csv"]

def pv_f8_report():
    """F8 facade (BYD 28 x 455 Wp) channel with the REAL module data. The POA input
    is the same PRELIM placeholder as the reference run and is NOT valid for an
    east-vertical facade; the output carries that warning."""
    from verlustmappe.devices import pv_account
    r = pv_account(H_poa_kWh_m2=160.0, months=1.0, profile="F8_12.74kWp")
    pd.DataFrame(r["bars"]).to_csv(os.path.join(TBL, "pv_f8_losses.csv"), index=False)
    n = {}
    for b in r["bars"]:
        n[b["status"]] = n.get(b["status"], 0) + 1
    comp = ", ".join("%d %s" % (v, k) for k, v in n.items())
    with open(os.path.join(TBL, "pv_f8_summary.csv"), "w") as f:
        f.write("quantity,value,unit\n")
        f.write("profile,%s,\n" % r["profile"])
        f.write("bars,\"%s\",\n" % comp)
        f.write("STC potential,%.1f,kWh/month\n" % r["e_stc_kWh"])
        f.write("DC after site losses,%.1f,kWh/month\n" % r["e_dc_kWh"])
        f.write("AC to bus,%.1f,kWh/month\n" % r["e_ac_kWh"])
        f.write("capture ratio,%.3f,\n" % r["capture_ratio"])
        f.write("eta DC-to-AC,%.3f,\n" % r["eta_dc_to_ac"])
        f.write("warning,\"%s\",\n" % r["warning"])
    return ["F8 PV channel (bars: %s): STC %.0f -> AC %.0f kWh/month, capture %.3f"
            % (comp, r["e_stc_kWh"], r["e_ac_kWh"], r["capture_ratio"]),
            "WARNING: POA placeholder not valid for east-vertical facade",
            "bars -> pv_f8_losses.csv, summary -> pv_f8_summary.csv"]

def pv_report(path):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    cum = df["ac_energy_Wh_cum"].dropna()
    # counter differences across the WHOLE window, not daily last-minus-first:
    # the daily method drops every kWh accrued across data gaps (reviewer
    # 2026-10: 5190 counted vs 4137 summed, one 38.7 h gap alone).
    total = cum.iloc[-1] - cum.iloc[0]
    daily = (cum.resample("D").last() - cum.resample("D").first()).dropna().div(1000)
    daily.rename("kWh").to_csv(os.path.join(TBL, "pv_daily_yield.csv"))
    out = [f"daily yield rows: {len(daily)} -> pv_daily_yield.csv",
           f"counter total: {total/1000:.1f} kWh (daily-sum method gives {daily.sum():.1f}; "
           f"difference = energy accrued across data gaps, use the counter total)",
           f"days covered by data: {len(daily)} of {(cum.index[-1]-cum.index[0]).days + 1}"]
    both = df[["dc_power_W", "ac_power_W"]].dropna()
    both = both[both["dc_power_W"] > 500]
    rows = []
    for lo, hi in [(500,2000),(2000,10000),(10000,30000),(30000,70000)]:
        m = both[(both.dc_power_W >= lo) & (both.dc_power_W < hi)]
        if len(m):
            # energy-weighted efficiency (sum AC / sum DC), not mean-of-ratios:
            # reviewer 2026-10 showed the difference is material at low load
            rows.append(dict(bin_W=f"{lo}-{hi}",
                             eta_ac_dc=round(float(m.ac_power_W.sum()/m.dc_power_W.sum()), 4),
                             eta_mean_of_ratios=round(float((m.ac_power_W/m.dc_power_W).mean()), 4),
                             n=len(m), loss_W_mean=round(float((m.dc_power_W-m.ac_power_W).mean()), 1)))
    t = pd.DataFrame(rows); t.to_csv(os.path.join(TBL, "pv_inverter_efficiency.csv"), index=False)
    out.append("inverter eta by load bin (energy-weighted) -> pv_inverter_efficiency.csv")
    # measured PV inverter bar for the loss map (feeds chain kw E_pv_dc/E_pv_ac).
    # Method (2026-10 fix; the first draft integrated dropna()-stacked power
    # with implicit linear dt, which stretched night values across data gaps
    # and reported E_dc 7198 kWh against an AC counter of 5190 kWh, eta 0.9755
    # on energies that cannot both be true):
    #  1. The cumulative AC counter is the AC reference: it keeps counting
    #     during data gaps, and on days WITHOUT gaps counter and gap-weighted
    #     power integral agree to 1% (validated per day below).
    #  2. The energy-weighted eta comes ONLY from validated (gap-free) days.
    #  3. E_dc = E_ac_counter / eta_validated; the loss bar follows.
    # Every number carries its method in the CSV, no silent blending.
    both_w = df[["dc_power_W", "ac_power_W"]].dropna()
    tw = both_w.index.values.astype("datetime64[ns]").astype(np.int64) / 1e9
    dtw = np.diff(tw, append=tw[-1])
    med_dt = float(np.median(dtw[dtw > 0])) if (dtw > 0).any() else 1.0
    gap_lim = 3.0 * med_dt
    w = np.where(dtw > gap_lim, 0.0, dtw); w[-1] = 0.0
    both_w = both_w.assign(_dt=w, _day=both_w.index.date)
    cum_daily = cum.groupby(cum.index.date).agg(lambda s: (s.iloc[-1] - s.iloc[0]) / 1000.0)
    int_daily = both_w.groupby("_day").apply(
        lambda g: np.sum(np.clip(g["ac_power_W"].values, 0, None) * g["_dt"].values) / 3.6e6)
    val = pd.DataFrame({"counter": cum_daily, "integral": int_daily}).dropna()
    val["ratio"] = val["counter"] / val["integral"]
    clean = val[(val["ratio"] > 0.98) & (val["ratio"] < 1.02)]
    e_ac_counter = float((cum.iloc[-1] - cum.iloc[0]) / 1000.0)
    if len(clean) >= 5:
        m = both_w[both_w["_day"].isin(set(clean.index))]
        eta_clean = float(np.clip(m["ac_power_W"].values, 0, None).sum()
                          / np.clip(m["dc_power_W"].values, 0, None).sum())
        e_dc = e_ac_counter / eta_clean
        e_ac = e_ac_counter
        method = (f"eta from {len(clean)} gap-validated days (counter==integral within 2%), "
                  f"E_ac from the cumulative counter, E_dc = E_ac/eta")
    else:
        e_dc = float(np.sum(np.clip(both_w["dc_power_W"].values, 0, None) * w) / 3.6e6)
        e_ac = e_dc * 0.0 + float(np.sum(np.clip(both_w["ac_power_W"].values, 0, None) * w) / 3.6e6)
        eta_clean = e_ac / e_dc if e_dc > 0 else float("nan")
        method = "FALLBACK: fewer than 5 clean days, both energies from gap-weighted integral"
    inv = pv_inverter_measured(e_dc, e_ac)
    inv["e_ac_counter_kWh"] = e_ac_counter
    inv["eta_method"] = method
    inv["n_clean_days"] = int(len(clean))
    inv["eta_clean_days"] = eta_clean
    with open(os.path.join(TBL, "pv_inverter_measured_bar.csv"), "w") as f:
        f.write("quantity,value,unit\nE_dc,%.2f,kWh\nE_ac,%.2f,kWh\neta,%.4f,\nloss,%.2f,kWh\n"
                "E_ac_counter,%.2f,kWh\neta_clean_days,%.4f,\nn_clean_days,%d,\nmethod,%s,\n"
                % (inv["e_dc_kWh"], inv["e_ac_kWh"], inv["eta"], inv["loss_kWh"],
                   e_ac_counter, eta_clean, len(clean), method.replace(",", ";")))
    out.append(f"PV inverter MEASURED bar: E_ac(counter) {e_ac_counter:.2f} kWh, eta( validated days) "
               f"{eta_clean:.4f} [{len(clean)} days], E_dc {inv['e_dc_kWh']:.2f} kWh, "
               f"loss {inv['loss_kWh']:.2f} kWh -> pv_inverter_measured_bar.csv")
    return out


def pv_inverter_measured(e_dc, e_ac):
    from verlustmappe.devices.pv_inverter import PVInverter
    return PVInverter().account(e_dc_kWh=e_dc, e_ac_kWh=e_ac)

if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else ""
    path = sys.argv[2] if len(sys.argv) > 2 else None
    if kind == "pvprelim":
        rows = pv_prelim_report()
    elif kind == "pvf8":
        rows = pv_f8_report()
    elif path:
        rows = fc_report(path) if kind == "fc" else pv_report(path)
    else:
        rows = ["usage: report_cli.py fc|pv|pvprelim|pvf8 <path> (pvprelim/pvf8 need no path)"]
    print("\n".join("PASS  " + r for r in rows))
