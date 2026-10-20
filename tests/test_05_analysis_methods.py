"""Tests for all Phase 1/3/4/5/6/8/10/11 pipeline modules, synthetic ground truth."""
import sys, os
import _path
import numpy as np, pandas as pd
from verlustmappe.analysis.a_polarization import iv_from_segments, key_values, compare_at_operating_point, deviation_from_reference
from verlustmappe.analysis.b_efficiency import efficiency_vs_temperature, nl_to_g
from verlustmappe.analysis.c_dynamics import ramp_rates, start_stop_cycles
from verlustmappe.analysis.d_purge_recovery import recovery_after_purges
from verlustmappe.analysis.e_degradation import degradation_sessions, lifetime_to_x_pct
from verlustmappe.analysis.f_compare import summary_table, relative_diff

def main():
    # --- Phase 1: IV from synthetic steady segments (known linear curve V = 48 - 0.1*I) ---
    segs = [dict(I_mean=i, V_mean=48 - 0.1 * i, P_mean=i * (48 - 0.1 * i)) for i in (5, 10, 20, 30, 40, 50)]
    iv = iv_from_segments(segs)
    assert len(iv) == 6 and abs(iv["dVdI_V_per_A"].mean() + 0.1) < 1e-9
    kv = key_values(iv, i_ref_a=25, area_cm2=100.0, stack_weight_kg=15.0)
    assert abs(kv["V_at_Iref_V"] - 45.5) < 1e-6
    assert kv["j_at_MPP_A_per_cm2"] == 0.5
    cmp_df = compare_at_operating_point({"FC1": iv, "FC2": iv}, [10, 30])
    assert abs(cmp_df.iloc[0]["V_at_10A"] - 47.0) < 1e-6
    print("PASS  Phase 1 IV/Kennwerte: OCV=%.1f V, V@25A=%.2f V, Pmax=%.0f W" %
          (kv["OCV_V"], kv["V_at_Iref_V"], kv["Pmax_W"]))

    # reference deviation (Phase 10 part): 2% band
    dev = deviation_from_reference(iv, iv)
    assert not dev["deviation_flag"].any()
    ref = iv.copy(); ref["V_mean"] = ref["V_mean"] * 0.95
    dev2 = deviation_from_reference(iv, ref)
    assert dev2["deviation_flag"].any()
    print("PASS  Phase 10 reference deviation: flagged correctly")

    # --- Phase 3: efficiency vs temperature (synthetic: eta constant 0.55, T ramp) ---
    n = 600
    idx = pd.date_range("2026-01-01", periods=n, freq="60s")
    h2 = np.full(n, 60.0)                      # NL/h
    p = np.full(n, 55000.0)                    # W -> chem 60 NL/h * 2.995 Wh/NL = 179.7 W... 
    # make consistent: chem = 60*2.995 = 179.7 W; power 99 W -> eta 0.55
    p = np.full(n, 99.0)
    T = np.linspace(20, 60, n)
    df3 = pd.DataFrame({"power_W": p, "h2_NLh": h2, "T_C": T}, index=idx)
    eff = efficiency_vs_temperature(df3, "power_W", "h2_NLh", "T_C")
    assert abs(eff["eta_mean"].mean() - 0.55) < 0.01
    assert abs(nl_to_g(1000.0) - 89.97) < 0.1
    print("PASS  Phase 3 efficiency vs T: eta=%.3f, 1000 NL = %.1f g" % (eff["eta_mean"].mean(), nl_to_g(1000)))

    # --- Phase 4/5: ramp rates + start/stop energy ---
    n2 = 1200
    idx2 = pd.date_range("2026-01-02", periods=n2, freq="1s")
    p2 = np.zeros(n2)
    p2[100:600] = 2000.0                            # one cycle: 500 s at 2 kW
    p2[100:110] = np.linspace(0, 2000, 10)          # 10 s ramp-up
    p2[590:600] = np.linspace(2000, 0, 10)          # 10 s ramp-down
    df4 = pd.DataFrame({"fc_power_W": p2, "fc1_current_A": p2 / 48, "fc1_voltage_V": np.full(n2, 48)},
                       index=idx2)
    rr = ramp_rates(df4)
    assert rr["fc_power_W"]["ramp_up_per_s"] is not None
    cyc = start_stop_cycles(df4, threshold_frac=0.1, rated_w=2500.0)
    assert len(cyc) == 1
    c0 = cyc.iloc[0]
    # energy: trapezoid over ramp edges; expected ~ 2000W*480s + 2*(ramp area 10000 J) 
    # expectation uses the same discrete signal + threshold semantics
    thr = 0.1 * 2500
    on = p2 > thr
    a_disc = int(np.argmax(on)); b_disc = int(np.max(np.where(on)[0])) + 1
    t_disc = np.arange(n2, dtype=float)
    expected_wh = np.trapezoid(p2[a_disc:b_disc], t_disc[a_disc:b_disc]) / 3600.0
    assert abs(c0["energy_cycle_Wh"] - expected_wh) < 0.5, (c0["energy_cycle_Wh"], expected_wh)
    peak_disc = a_disc + int(np.argmax(p2[a_disc:b_disc]))
    exp_up = np.trapezoid(p2[a_disc:peak_disc+1], t_disc[a_disc:peak_disc+1]) / 3600.0  # inclusive
    assert abs(c0["energy_startup_Wh"] - exp_up) < 0.1, (c0["energy_startup_Wh"], exp_up)
    print("PASS  Phase 4/5: cycle energy %.1f Wh (expected %.1f), startup %.2f Wh" %
          (c0["energy_cycle_Wh"], expected_wh, c0["energy_startup_Wh"]))

    # --- Phase 6: purge recovery ---
    v = np.full(600, 48.0)
    v[200:212] -= 1.2                                # purge dip 1.2 V
    df5 = pd.DataFrame({"fc1_voltage_V": v}, index=idx2[:600])
    pr = recovery_after_purges(df5, [idx2[200]])
    assert len(pr) == 1 and abs(pr.iloc[0]["dip_V"] - 1.2) < 0.05
    print("PASS  Phase 6 purge recovery: dip %.2f V, recovery %s s" %
          (pr.iloc[0]["dip_V"], pr.iloc[0]["recovery_s"]))

    # --- Phase 8: degradation + lifetime projection ---
    s1 = pd.DataFrame({"I": [10, 30, 50], "V": [47.0, 45.0, 43.0]})
    s2 = s1.copy(); s2["V"] -= 0.2                   # -0.2 V at every point
    s3 = s2.copy(); s3["V"] -= 0.2
    deg = degradation_sessions({"t0": s1, "t1": s2, "t2": s3}, i_target=30, hours={"t0": 0, "t1": 500, "t2": 1000})
    assert abs(deg["mV_per_h"].iloc[-1] + 0.4) < 1e-3   # -0.2 V per 500 h = -0.4 mV/h
    lt = lifetime_to_x_pct(deg, x_pct=10.0)
    # 10% of 45 V = 4.5 V = 4500 mV at 0.4 mV/h = 11250 h
    assert abs(lt - 11250) < 50, lt
    print("PASS  Phase 8 degradation: %.3f mV/h, lifetime to -10%%: %.0f h" % (deg["mV_per_h"].iloc[-1], lt))

    # --- Phase 11: summary + relative diff ---
    summ = summary_table([dict(dataset="FC1", Pmax_W=2500, eta=0.5), dict(dataset="FC2", Pmax_W=2400, eta=0.48)])
    rd = relative_diff(summ, "FC1", "FC2")
    assert abs(rd["d_Pmax_W_pct"].iloc[0] + 4.0) < 1e-6
    print("PASS  Phase 11 summary + relative diff: Pmax d=%.1f%%" % rd["d_Pmax_W_pct"].iloc[0])

if __name__ == "__main__":
    main()
