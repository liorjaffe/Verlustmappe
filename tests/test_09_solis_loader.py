"""Solis inverter loader: column mapping, sign convention, measured eta."""
import _path, os
import numpy as np, pandas as pd
from verlustmappe.loaders.solis import load_solis, inverter_eta_measured
from verlustmappe.devices.inverter import FCInverter

def main():
    t0 = pd.Timestamp("2026-10-07 10:00:00+00:00")
    hdr = "Timestamp,AC output power (W),Battery voltage (V),Battery current (A),AC voltage (V)"
    rows = []
    for k in range(60):
        rows.append(",".join([(t0 + pd.Timedelta(seconds=k)).isoformat(),
                              f"{2000.0:.0f}", "52.0", f"{40.0:.1f}", "230.0"]))
    p = os.path.join(_path.ROOT, "data", "raw", "_test_solis.csv")
    open(p, "w").write("\n".join([hdr] + rows) + "\n")
    df = load_solis(p)
    assert "ac_out_W" in df.columns and "bus_voltage_V" in df.columns
    assert abs(df["ac_out_W"].iloc[0] - 2000.0) < 1e-6
    assert df["batt_current_A"].iloc[0] == 40.0        # + = discharge into bus
    eta = inverter_eta_measured(df)
    # expected: E_in = 52*40*60s, E_out = 2000*60s -> eta = 2000/(52*40)
    assert abs(eta["eta"] - 2000.0/(52.0*40.0)) < 1e-6, eta
    # measured mode flips the inverter
    acc = FCInverter().account(e_dc_in_kWh=eta["e_dc_in_kWh"], e_ac_measured_kWh=eta["e_ac_kWh"])
    assert acc["eta_is_measured"] and abs(acc["eta"] - eta["eta"]) < 1e-6
    os.remove(p)
    print("PASS 09 solis loader: mapping, discharge sign, measured eta %.3f flips inverter to MEASURED" % eta["eta"])

if __name__ == "__main__": main()
