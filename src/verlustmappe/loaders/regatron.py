"""Loader for the Regatron bridge fast-log (bridge_logs/regatron_fastlog_*.csv).

The bridge samples the G5.BT's own channel at 20 Hz on a real clock, independent
of Enapter's ~1 Hz cloud polling. It provides what the pipeline was missing:
a MEASURED load-branch current on the hybrid bus.

Sign conventions (bridge README, CURRENT_SIGN_SINK = -1):
  current_signed_a < 0  -> the load SINKS current from the bus (normal operation)
  power_w              -> magnitude, always positive

Pipeline convention (see data dictionary): load_current_A positive = current
drawn by the load. Therefore load_current_A = -current_signed_a.

CAUTION (Regatron README, verbatim logic): the bridge measures the BUS/load
side, never the FCM output. battery current also flows on this bus. load_current_A
may only enter the pipeline as the load branch of the current balance
(FC terminal - load = battery residual), never as "fuel cell output".
"""
import numpy as np
import pandas as pd

FASTLOG_COLUMNS = ["timestamp_iso", "epoch_s", "mode", "commanded_value", "commanded_limit",
                   "voltage_v", "raw_voltage_v", "current_signed_a", "current_mag_a",
                   "power_w", "output_on", "has_errors", "has_warnings", "estop_latched"]

def load_fastlog(path):
    """One fast-log CSV -> UTC-indexed DataFrame in pipeline vocabulary."""
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    missing = {"voltage_v", "current_signed_a", "power_w"} - set(df.columns)
    if "timestamp_iso" not in df.columns and "epoch_s" not in df.columns:
        missing |= {"timestamp_iso"}
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    # epoch_s is exact UTC; timestamp_iso is naive LOCAL time written by the
    # bridge, so it is only a fallback for rows without a usable epoch.
    idx = (pd.to_datetime(df["timestamp_iso"], format="ISO8601", utc=True)
           if "timestamp_iso" in df.columns else pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns, UTC]"))
    if "epoch_s" in df.columns:
        epoch = pd.to_numeric(df["epoch_s"], errors="coerce")
        idx_epoch = pd.to_datetime(epoch, unit="s", utc=True)
        idx = pd.DatetimeIndex(idx_epoch.where(epoch.notna(), idx))
    out = pd.DataFrame(index=idx)
    out["bus_voltage_V"] = pd.to_numeric(df["voltage_v"], errors="coerce").to_numpy()
    signed = pd.to_numeric(df["current_signed_a"], errors="coerce")
    out["load_current_A"] = -signed.to_numpy()            # pipeline convention: positive = drawn by load
    out["load_power_W"] = pd.to_numeric(df["power_w"], errors="coerce").to_numpy()
    if "commanded_value" in df.columns:
        out["commanded_value"] = pd.to_numeric(df["commanded_value"], errors="coerce").to_numpy()
    out["mode"] = df["mode"]
    if "output_on" in df.columns:
        out["output_on"] = df["output_on"]
    if "estop_latched" in df.columns:
        out["estop_latched"] = df["estop_latched"]
    return out.sort_index()

def active_window(df, threshold_a=0.5):
    """Rows where the load actually drew current (for characteristic curves)."""
    return df[df["load_current_A"] > threshold_a]

def align_with_enapter(df_enapter, df_regatron, tolerance="1s"):
    """Inner-join the two sources on UTC time after nearest-neighbour alignment.
    Use this to pair 1 Hz Enapter telemetry with 20 Hz fast-log samples; the
    merge is on the SLOWER clock (Enapter), fast-log rows are interpolated."""
    a = df_enapter.sort_index()
    r = df_regatron.sort_index().reindex(a.index, method="nearest", tolerance=pd.Timedelta(tolerance))
    return a.join(r, how="inner")
