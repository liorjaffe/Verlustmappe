"""Regatron fast-log loader: column mapping, sign convention, merge with Enapter."""
import _path, os, io
import numpy as np, pandas as pd
from verlustmappe.loaders.regatron import load_fastlog, active_window, align_with_enapter
from verlustmappe.devices import FuelCellSystem

def main():
    # synthetic fast-log row set in the EXACT bridge format (see _write_fast_log_row)
    rows = []
    t0 = pd.Timestamp("2026-09-22 13:00:00+00:00")
    for k in range(10):
        rows.append(",".join([
            (t0 + pd.Timedelta(seconds=k * 0.05)).isoformat(timespec="microseconds"),
            f"{t0.timestamp() + k * 0.05:.6f}", "cc", "30.0", "48.0",
            "49.1234", "49.1234", "-30.0000", "30.0000",   # signed NEGATIVE = sinking
            f"{49.1234*30:.3f}", "True", "False", "False", "False"]))
    csv = "\n".join(["timestamp_iso,epoch_s,mode,commanded_value,commanded_limit,voltage_v,raw_voltage_v,current_signed_a,current_mag_a,power_w,output_on,has_errors,has_warnings,estop_latched"] + rows) + "\n"
    p = os.path.join(_path.ROOT, "data", "raw", "_test_fastlog.csv")
    open(p, "w").write(csv)
    df = load_fastlog(p)
    assert df["load_current_A"].iloc[0] == 30.0        # sign flipped: positive = load draws
    assert df["bus_voltage_V"].iloc[0] == 49.1234
    act = active_window(df, 0.5)
    assert len(act) == 10
    # battery residual: load draws 30 A, FC terminals deliver 20 A -> residual +10 A = battery discharging into the bus (pipeline convention: positive = into the bus from the device under test's perspective)
    idx = df.index
    fcdf = pd.DataFrame({"fc_power_W": 48.0 * 20.0, "fc1_current_A": 10.0, "fc2_current_A": 10.0,
                         "load_current_A": df["load_current_A"].values}, index=idx)
    acc = FuelCellSystem().account(fcdf)
    res = acc["battery_current_residual_A"]
    assert res is not None and abs(np.nanmean(res) - 10.0) < 1e-9, res
    # merge with Enapter-style 1 Hz data
    en = pd.DataFrame({"fc_power_W": 1000.0}, index=pd.DatetimeIndex([t0], name=None))
    m = align_with_enapter(en, df)
    assert len(m) == 1 and abs(m["load_current_A"].iloc[0] - 30.0) < 1e-6
    os.remove(p)
    print("PASS 06 regatron loader: signs, active window, battery residual, Enapter merge")

if __name__ == "__main__": main()
