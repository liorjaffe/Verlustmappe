"""Pipeline against the real FC telemetry of 2026-09-22 (data/processed/fc_retro)."""
import _path, os
import pandas as pd
from verlustmappe.loaders.grafana import map_fc
from verlustmappe.balance.b_segments import steady_segments
from verlustmappe.balance.c_events import detect_events, purge_candidates
from verlustmappe.devices import FuelCellSystem

def main():
    df = map_fc(pd.read_csv(os.path.join(_path.ROOT, "data/processed/fc_retro/fc_merged.csv"), index_col=0, parse_dates=True))
    segs = steady_segments(df, "fc_power_W", p_min=1000, min_dur_s=120, extra_cols=("fc1_current_A", "fc1_voltage_V"))
    assert len(segs) >= 10, len(segs)
    pur = purge_candidates(df, "anode_pressure_mbar", min_drop_mbar=150)
    assert len(pur) >= 3
    acc = FuelCellSystem().account(df.dropna(subset=["fc_power_W"]))
    assert not acc["efficiency_is_measured"]          # terminal current is not stack current
    assert acc["warning"] is not None
    print("PASS 04 real FC data: %d steady segments, %d purge candidates, E_out %.2f kWh, eta=%.1f%% (%s)"
          % (len(segs), len(pur), acc["energy_out_kWh"], acc["efficiency_LHV"]*100, acc["h2"]["route"]))

if __name__ == "__main__": main()
