"""Offline checks for the F8 SolisCloud live/history loaders."""
import _path
import os
import tempfile
import pandas as pd
from verlustmappe.loaders import solis_live as SL


def main():
    detail = SL._detail_to_row(
        {"pac": 4.02, "eTotal": 9.745}, pd.Timestamp("2026-10-22", tz="UTC"))
    assert detail["ac_power_W"] == 4020.0
    assert detail["ac_energy_Wh_cum"] == 9745000.0

    fake_data = [
        {"dataTimestamp": 1790064000000, "pac": 2690, "eToday": 0.8,
         "uPv1": 260.3, "iPv1": 9.1, "uPv2": 260.5, "iPv2": 9.4,
         "uPv3": 0, "iPv3": 0, "uPv4": 0, "iPv4": 0},
        {"dataTimestamp": 1790092800000, "pac": 500, "eToday": 23.1,
         "uPv1": 0, "iPv1": 0, "uPv2": 0, "iPv2": 0,
         "uPv3": 0, "iPv3": 0, "uPv4": 0, "iPv4": 0},
    ]
    original_call, original_credentials = SL._call, SL._credentials
    try:
        SL._call = lambda *args, **kwargs: {"data": fake_data}
        SL._credentials = lambda: ("k", "s")
        day = SL.solis_day_df("1802060225250007", "2026-09-15")
    finally:
        SL._call, SL._credentials = original_call, original_credentials
    assert list(day["ac_power_W"]) == [2690.0, 500.0]
    assert list(day["e_today_Wh"]) == [800.0, 23100.0]
    assert day["dc_power_W"].iloc[0] == 260.3 * 9.1 + 260.5 * 9.4
    assert pd.isna(day["dc_power_W"].iloc[1])

    assert SL.energy_kWh(pd.Series([4000.0] * 6), dt_s=300) == 2.0
    assert SL.energy_kWh(pd.Series([4000.0] * 12), dt_s=300) == 4.0

    timestamps = list(pd.date_range("2026-09-10", periods=50, freq="5min", tz="UTC"))
    timestamps += list(pd.date_range("2026-09-11", periods=50, freq="5min", tz="UTC"))
    full_dc = 23.9 * 3.6e6 / (50 * 300)
    low_dc = 0.376 * 3.6e6 / (50 * 300)
    fixture = pd.DataFrame({
        "ac_power_W": [1000.0] * 100,
        "e_today_Wh": [23100.0] * 50 + [300.0] * 50,
        "dc_power_W": [full_dc] * 50 + [low_dc] * 50,
    }, index=pd.DatetimeIndex(timestamps))
    original_range = SL.f8_range_dfs
    try:
        SL.f8_range_dfs = lambda start, end: {"1802060225250007": fixture}
        balance = SL.f8_day_balance("2026-09-10", "2026-09-11")
    finally:
        SL.f8_range_dfs = original_range
    full_days = balance[balance["e_ac_counter_kWh"] >= 5.0]
    assert len(full_days) == 1
    assert abs(full_days["eta_dc_ac"].median() - 23.9 / 23.1) < 1e-12
    assert "not an efficiency" in SL.__doc__

    from verlustmappe.reporting import report_cli as RC
    original_balance, original_tbl = SL.f8_day_balance, RC.TBL
    try:
        with tempfile.TemporaryDirectory() as outdir:
            RC.TBL = outdir

            def no_access(start, end):
                raise SL.SolisCloudError("credentials missing")

            SL.f8_day_balance = no_access
            skipped = RC.pv_f8_measured_report()
            assert skipped == [
                "pvf8measured: skipped (no SolisCloud access: "
                "set SOLISCLOUD_KEY_ID/SOLISCLOUD_KEY_SECRET)"
            ]
            assert os.listdir(outdir) == []

            SL.f8_day_balance = lambda start, end: balance
            report = RC.pv_f8_measured_report()
            assert len(report) == 2
            measured = pd.read_csv(os.path.join(outdir, "pv_f8_measured.csv"))
            assert list(measured.columns) == [
                "date", "sn", "e_ac_counter_kWh", "e_dc_channel_kWh", "eta_dc_ac"
            ]
            summary = pd.read_csv(os.path.join(outdir, "pv_f8_measured_summary.csv"))
            assert {"window", "metric", "inverter", "value", "unit", "status"} == set(summary.columns)
            assert "e_ac_counter_kWh: MEASURED" in set(summary["status"])
            assert "e_dc_channel_kWh: PRELIM (+3-4% bias vs counter, verified 2026-09-10..15)" in set(summary["status"])
            assert "eta_dc_ac: DIAGNOSTIC ONLY, not an efficiency" in set(summary["status"])
    finally:
        SL.f8_day_balance, RC.TBL = original_balance, original_tbl

    now = pd.Timestamp("2026-10-22 12:00:00", tz="UTC")
    assert not SL._is_stale((now - pd.Timedelta(minutes=10)).timestamp() * 1000, now)
    assert SL._is_stale((now - pd.Timedelta(minutes=40)).timestamp() * 1000, now)
    print("PASS 12 Solis live: conversions, daily curves, balance semantics, stale guard")


if __name__ == "__main__":
    main()
