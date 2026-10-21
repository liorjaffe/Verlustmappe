"""F8 facade PV array (BYD455MGEK-36, 28 modules): plain-arithmetic checks of the
registry entries, the string design against the Solis window, the capture ratio
and the plant-profile mechanism (default profile must stay unchanged)."""
import _path
from verlustmappe import registry as R
from verlustmappe.devices.pv_prelim_channel import pv_account, PLANT_PROFILES

def main():
    # array power from module count x nameplate (card: array power)
    n, p_mod = R.get("pv.n_modules"), 455.0
    assert n * p_mod == 12740 == R.get("pv.p_dc_stc_W")
    f8 = PLANT_PROFILES["F8_12.74kWp"]
    assert f8["p_dc_stc_W"] == 28 * 455
    # module area 2.094 x 1.038 m, array 28 modules
    area = 2.094 * 1.038 * 28
    assert abs(area - 60.86) < 0.01 and abs(f8["A_array_m2"] - 60.86) < 1e-9

    # string design 7 x 49.81 V Voc, cold check with gamma_Voc -0.360 %/K, Vmp
    voc, vmp, ns = 49.81, 41.79, 7
    assert abs(ns * voc - 348.67) < 1e-9
    cold = ns * voc * (1 + (-0.00360) * (10 - 25))
    assert abs(cold - 367.5) < 0.1 and cold < 500.0
    assert abs(ns * vmp - 292.53) < 1e-9 and 90.0 < ns * vmp < 480.0
    assert 11.72 < 32.0 and 10.50 < 13.0            # Isc / Imp limits of the Solis input
    # design-review flag: 6.37 kWp per inverter above the recommended 5.5 kW
    assert abs(12740 / 2 / 1000 - 6.37) < 1e-9 and abs(12740 / 10000 - 1.274) < 1e-9

    # status labels: flipped entries are DATASHEET, not deleted
    for k in ("pv.p_dc_stc_W", "pv.module_efficiency_STC", "pv.p_tc_pmax_per_K",
              "pv.noct_C", "pv.bifacial_gain_frac", "pv.degradation_per_year"):
        assert R.entry(k)["status"] == "DATASHEET", k
    assert R.get("pv.p_tc_pmax_per_K") == f8["gamma_pmax"] == -0.0038
    assert R.entry("pv.string_config")["status"] == "GUESS"

    # capture ratio with a real P_STC: E_dc / (H_poa * P_STC) for a synthetic day
    H = 5.0                                       # kWh/m2 (POA)
    e_dc = 0.82 * H * 12.74
    assert abs(e_dc / (H * 12.74) - 0.82) < 1e-12
    from verlustmappe.devices.pv_measured import PVSystem
    res = PVSystem().account(e_dc_kWh=e_dc, e_ac_kWh=e_dc * 0.95, H_poa_kWh_m2=H)
    assert any(abs(v - 0.82) < 1e-9 for v in res.values() if isinstance(v, float)), res

    # F8 profile: warning, real values, bars sum STC -> AC
    r = pv_account(H_poa_kWh_m2=160.0, profile="F8_12.74kWp")
    assert "POA placeholder not valid for east-vertical facade" in r["warning"]
    assert abs(r["e_stc_kWh"] - 160.0 * 60.86 * 0.209) < 1e-9
    assert abs(sum(b["kWh"] for b in r["bars"]) - (r["e_stc_kWh"] - r["e_ac_kWh"])) < 1e-6
    assert [b["status"] for b in r["bars"] if b["stage"] == "Cell temperature"] == ["DERIVED"]

    # review fix 4: monofacial F8 has no bifacial bar, the reference profile keeps it
    assert not any(b["stage"] == "Bifacial gain" for b in r["bars"])
    rr = pv_account(H_poa_kWh_m2=160.0, A_array_m2=836.0)
    assert any(b["stage"] == "Bifacial gain" for b in rr["bars"])

    # review fix 1: P_STC source is explicit
    legacy = PVSystem().account(e_dc_kWh=0.8 * 5.0 * 184.0, e_ac_kWh=700.0, H_poa_kWh_m2=5.0, p_stc_W=184000)
    assert abs(legacy["capture_ratio"] - 0.8) < 1e-12 and legacy["p_stc_source"] == "explicit p_stc_W argument"
    assert "F8 array" in res["p_stc_source"]

    # review fix 2: F8 isolated per serial number; station shared with F7
    try:
        from verlustmappe.loaders import solis_live as SL
    except ImportError:  # optional 'requests' dependency not installed
        SL = None
    if SL is not None:
        f8 = SL.f8_inverters()
        assert [e["inverter_sn"] for e in f8] == ["1802060225250007", "1802060225250009"]
        assert SL.F7_INVERTER_SN not in [e["inverter_sn"] for e in f8]

    # regression guard: default profile = former PRELIM values, no F8 warning
    d = pv_account(H_poa_kWh_m2=160.0, A_array_m2=836.0)
    ref = pv_account(H_poa_kWh_m2=160.0, A_array_m2=836.0, profile="reference_184kWp")
    assert d["e_ac_kWh"] == ref["e_ac_kWh"] and "east-vertical" not in d["warning"]
    assert abs(d["e_stc_kWh"] - 160.0 * 836.0 * 0.220) < 1e-9
    assert all(b["status"] == "PRELIM" for b in d["bars"])
    print("test_10 ok: F8 array, string design, profiles")

if __name__ == "__main__":
    main()
