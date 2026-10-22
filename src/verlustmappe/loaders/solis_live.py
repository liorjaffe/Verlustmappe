"""Live SolisCloud loader for Inverter 1 (PV side).

Inverter 1 converts the DC energy of the PV modules to AC for the
electrolyzer (PV -> AC -> EL). This loader queries the SolisCloud REST API
directly and returns the PV-path vocabulary (same names as grafana.PV_MAP),
so LivePipeline.push() can consume it unchanged:

  ac_power_W        inverter AC output towards the electrolyzer (MEASURED)
  e_today_Wh        daily energy (history loader)
  dc_V / dc_A       PV DC voltage / current (per MPPT), when reported
  ac_energy_Wh_cum  cumulative AC energy counter

F8 facade (Fachada Leste, BYD 28 x 455 Wp = 12.74 kWp): both units are
S6-GR1P6K string inverters serving the 28-module array (STATION_F8_A /
STATION_F8_B below; machine name verified via inveterList 2026-10-22).
Their PV-path vocabulary feeds the F8 profile of the preliminary channel
(devices/pv_prelim_channel.PLANT_PROFILES["F8_12.74kWp"], measured mode)
just like the SMA telemetry does for the big array, but via the
SolisCloud API.

Inverter 2 (battery/FC side, the LAST conversion loss in the chain) is
covered separately by loaders/solis.py (S5-EO1P5K-48: ac_out_W,
bus_voltage_V, batt_current_A, fc1/fc2_current_A). Do NOT feed this
loader's output into FCInverter.account().

UNITS (verified against live data 2026-10-22):
  inveterDetail:  pac in kW, eTotal assumed MWh (verify eTotalStr when the
                  inverter reports again)
  inverterDay:    pac/eToday come with per-record unit strings (pacStr /
                  eTodayStr) that MIX UNITS WITHIN ONE DAY (Wh in the
                  morning curve, kWh in the closing record); every value is
                  therefore normalised via its unit string, never via a
                  fixed factor.
A stale live value (no report for > 15 min) triggers a printed WARNING;
the last reported value is still returned.

Credentials: never hard-code them. Export before running:
    export SOLISCLOUD_KEY_ID="..."
    export SOLISCLOUD_KEY_SECRET="..."
(Both come from soliscloud.com -> Service -> API Management.)

Rate limit note: SolisCloud refreshes live values every ~5 min, so the
natural polling cadence is 300 s (poll_solis_live default).
"""
import os
import time
from typing import Optional

import pandas as pd
import requests

__all__ = ["solis_live_df", "poll_solis_live", "solis_day_df",
           "SolisCloudError", "f8_inverters", "f8_live_dfs", "f8_day_dfs"]

API_URL = "https://www.soliscloud.com:13333"

# True SolisCloud ids, as returned by the API (the metadata CSV rounds
# 17-digit ids, so its station ids look shared/wrong: trust the API).
DEFAULT_STATION_ID = "1298491919449567877"   # F8_Fachada Leste

STATION_F8_A = dict(station_id=DEFAULT_STATION_ID, inverter_sn="1802060225250007")
STATION_F8_B = dict(station_id=DEFAULT_STATION_ID, inverter_sn="1802060225250009")

# unit strings as delivered by the API -> factor to base unit (W / Wh)
_UNIT_FACTOR = {"w": 1.0, "kw": 1000.0, "mw": 1e6,
                "wh": 1.0, "kwh": 1000.0, "mwh": 1e6}


def f8_inverters() -> list:
    """The two F8 inverter entries. Always query per inverter SN: station-
    level calls mix all inverters of the station."""
    return [dict(STATION_F8_A), dict(STATION_F8_B)]


class SolisCloudError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Signing + request machinery (SolisCloud user-level HMAC-SHA1 scheme)
# ---------------------------------------------------------------------------
def _call(key_id: str, key_secret: str, url_part: str, body: dict) -> dict:
    import base64
    import hashlib
    import hmac
    import json
    from datetime import datetime, timezone

    payload = json.dumps(body, separators=(",", ":"))
    md5 = base64.b64encode(hashlib.md5(payload.encode("utf-8")).digest()).decode()
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    sign_str = f"POST\n{md5}\napplication/json\n{now}\n{url_part}"
    sign = base64.b64encode(
        hmac.new(key_secret.encode(), sign_str.encode(), hashlib.sha1).digest()
    ).decode()
    headers = {
        "Content-MD5": md5,
        "Content-Type": "application/json;charset=UTF-8",
        "Date": now,
        "Authorization": f"API {key_id}:{sign}",
    }
    try:
        r = requests.post(API_URL + url_part, headers=headers, data=payload, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        raise SolisCloudError(f"request failed: {e}") from e
    data = r.json()
    if not data.get("success"):
        raise SolisCloudError(f"SolisCloud rejected the call: {data}")
    return data


def _credentials() -> tuple:
    key_id = os.getenv("SOLISCLOUD_KEY_ID")
    key_secret = os.getenv("SOLISCLOUD_KEY_SECRET")
    if not key_id or not key_secret:
        raise SolisCloudError(
            "set SOLISCLOUD_KEY_ID and SOLISCLOUD_KEY_SECRET in the environment "
            "(soliscloud.com -> Service -> API Management)"
        )
    return key_id, key_secret


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
def list_inverters(station_id: str) -> list:
    key_id, key_secret = _credentials()
    data = _call(key_id, key_secret, "/v1/api/inveterList",
                 {"stationId": station_id, "pageNo": 1, "pageSize": 100})
    return data.get("data", {}).get("page", {}).get("records", [])


def inverter_detail(inverter_id: str, sn: str) -> dict:
    key_id, key_secret = _credentials()
    return _call(key_id, key_secret, "/v1/api/inveterDetail",
                 {"id": inverter_id, "sn": sn}).get("data", {})


# ---------------------------------------------------------------------------
# Live detail: API field -> pipeline vocabulary (PV path, names as in
# grafana.PV_MAP). inveterDetail reports pac in kW (pacStr "kW", verified);
# the live detail of this firmware does NOT carry dcPow/dcV/dcA under those
# names. eTotal factor assumes MWh; verify with eTotalStr when data flows.
# ---------------------------------------------------------------------------
_DETAIL_MAP = [
    ("pac",    "ac_power_W",        1000.0),        # kW -> W
    ("eTotal", "ac_energy_Wh_cum",  1_000_000.0),   # MWh -> Wh (ASSUMED)
]

def _num(field) -> Optional[float]:
    if isinstance(field, dict):
        field = field.get("value")
    try:
        return float(field)
    except (TypeError, ValueError):
        return None


def _detail_to_row(detail: dict, ts: pd.Timestamp) -> dict:
    row = {}
    for api_key, col, factor in _DETAIL_MAP:
        v = _num(detail.get(api_key))
        if v is not None:
            row[col] = v * factor
    return {"ts": ts, **row}


# ---------------------------------------------------------------------------
# Public loaders (pipeline vocabulary out)
# ---------------------------------------------------------------------------
def solis_live_df(station_id: str = None,
                  inverter_sn: str = None,
                  inverter_id: str = None) -> pd.DataFrame:
    """
    One live snapshot as a single-row DataFrame, UTC-indexed, in the PV
    vocabulary (ac_power_W, ...). Prints a WARNING when the value is stale
    (inverter offline; last report older than 15 min).

    inverter_id is the SolisCloud internal id (from list_inverters), NOT the
    serial number. If only inverter_sn is given it is resolved per call.
    """
    _credentials()  # fail fast with a clear message
    station_id = station_id or os.getenv("SOLISCLOUD_STATION_ID", DEFAULT_STATION_ID)
    inverter_sn = inverter_sn or os.getenv("SOLISCLOUD_INVERTER_SN")

    if not inverter_sn:
        raise SolisCloudError(
            "pass inverter_sn (e.g. one of the F8 serials) or set "
            "SOLISCLOUD_INVERTER_SN; station-level KPIs mix all strings"
        )

    if inverter_id is None:
        for inv in list_inverters(station_id):
            if str(inv.get("sn")) == str(inverter_sn):
                inverter_id = str(inv.get("id"))
                break
        if inverter_id is None:
            raise SolisCloudError(f"sn {inverter_sn} not found in station {station_id}")

    detail = inverter_detail(inverter_id, inverter_sn)
    ts = pd.Timestamp.now(tz="UTC")

    # staleness guard: the endpoint returns the LAST reported value even for
    # an offline inverter, so make that visible instead of passing it off
    # as live data.
    data_ts = _num(detail.get("dataTimestamp"))
    if data_ts and (pd.Timestamp.now(tz="UTC")
                    - pd.to_datetime(data_ts, unit="ms", utc=True)) > pd.Timedelta(minutes=15):
        print("WARNING: inverter data is STALE (last report "
              f"{pd.to_datetime(data_ts, unit='ms', utc=True)}); value is not live")

    df = pd.DataFrame([_detail_to_row(detail, ts)]).set_index("ts")
    df.index.name = "time"
    return df


def poll_solis_live(interval_s: int = 300, **kwargs):
    """
    Generator yielding a live snapshot DataFrame every interval_s, ready for
    LivePipeline.push(). 300 s matches the SolisCloud ~5 min refresh.

    Example:
        from verlustmappe.loaders.solis_live import poll_solis_live
        from verlustmappe.live_feed import LivePipeline

        pipe = LivePipeline(dt_s=300, window_s=3600)
        for df in poll_solis_live(300, inverter_sn="1802060225250007"):
            out = pipe.push(df)
    """
    while True:
        t0 = time.time()
        yield solis_live_df(**kwargs)
        rest = interval_s - (time.time() - t0)
        if rest > 0:
            time.sleep(rest)


# ---------------------------------------------------------------------------
# History: daily 5-min curve of one inverter (/v1/api/inverterDay).
# money is required by the endpoint but irrelevant for us; timeZone -3 = UTC-03.
# pac and eToday arrive with per-record unit strings that can mix units
# within one day, so every value is normalised via pacStr / eTodayStr.
# ---------------------------------------------------------------------------
def solis_day_df(inverter_sn: str, date: str,
                 station_id: str = None,
                 inverter_id: str = None) -> pd.DataFrame:
    """
    Historical intraday curve for ONE inverter on ONE day (date 'YYYY-MM-DD',
    in plant local time). Returns UTC-indexed DataFrame:
      ac_power_W, e_today_Wh, dc_V_mppt1..4, dc_A_mppt1..4, dc_power_W
      (this inverter uses MPPT 1 and 2, channels 3/4 stay 0).

    UNITS (verified 2026-09-15 data): inverterDay reports pac in W and
    eToday in kWh; the unit strings (pacStr/eTodayStr) are EMPTY in these
    records, so fixed factors are used.
    dc_power_W is computed from the measured MPPT channels (sum of uPv*iPv)
    and is the DC-side input for the inverter efficiency account.
    """
    key_id, key_secret = _credentials()
    station_id = station_id or DEFAULT_STATION_ID
    body = {"sn": str(inverter_sn), "money": "BRL",
            "time": date, "timeZone": -3}
    if inverter_id:
        body["id"] = int(inverter_id)
    data = _call(key_id, key_secret, "/v1/api/inverterDay", body).get("data", [])
    rows = []
    for rec in data if isinstance(data, list) else []:
        ts_raw = _num(rec.get("dataTimestamp"))
        if ts_raw is None:
            continue
        row = {"ts": pd.to_datetime(ts_raw, unit="ms", utc=True)}
        pac = _num(rec.get("pac"))
        if pac is not None:
            row["ac_power_W"] = pac                 # inverterDay: W (verified)
        et = _num(rec.get("eToday"))
        if et is not None:
            row["e_today_Wh"] = et * 1000.0         # inverterDay: kWh (verified)
        for i in range(1, 5):
            u_v, u_c = _num(rec.get(f"uPv{i}")), _num(rec.get(f"iPv{i}"))
            if u_v is not None:
                row[f"dc_V_mppt{i}"] = u_v
            if u_c is not None:
                row[f"dc_A_mppt{i}"] = u_c
        # DC power from the measured MPPT channels (uPv*iPv per MPPT, summed)
        terms = [row[f"dc_V_mppt{i}"] * row[f"dc_A_mppt{i}"]
                 for i in range(1, 5)
                 if f"dc_V_mppt{i}" in row and f"dc_A_mppt{i}" in row]
        if terms:
            row["dc_power_W"] = sum(terms)
        rows.append(row)                            # <- bleibt die letzte Zeile der Schleife
    df = pd.DataFrame(rows).set_index("ts").sort_index()
    df.index.name = "time"
    return df



def f8_live_dfs() -> dict:
    """One live snapshot per F8 inverter, keyed by serial number. Always
    queries per inverter SN, so no other station's data can leak in."""
    return {e["inverter_sn"]: solis_live_df(station_id=e["station_id"],
                                            inverter_sn=e["inverter_sn"])
            for e in f8_inverters()}


def f8_day_dfs(date: str) -> dict:
    """Historical day curve for BOTH F8 inverters, keyed by serial number."""
    return {e["inverter_sn"]: solis_day_df(e["inverter_sn"], date,
                                           station_id=e["station_id"])
            for e in f8_inverters()}
# ---------------------------------------------------------------------------
# Simulation helpers: multi-day history, DC power from MPPT channels,
# energy integration. All outputs stay in the pipeline vocabulary.
# ---------------------------------------------------------------------------
def f8_range_dfs(start: str, end: str) -> dict:
    """
    Multi-day history for BOTH F8 inverters: {sn: concatenated DataFrame}
    over the inclusive date range (e.g. '2026-08-01' .. '2026-09-15').
    Two API calls per day, well inside the rate limit.
    """
    out = {e["inverter_sn"]: [] for e in f8_inverters()}
    for day in pd.date_range(start, end, freq="D"):
        for sn, df in f8_day_dfs(day.strftime("%Y-%m-%d")).items():
            out[sn].append(df)
    return {sn: pd.concat(v).sort_index() for sn, v in out.items() if v}


def energy_kWh(power_series, dt_s: float = 300.0) -> float:
    """
    Energy of a (near-)uniformly sampled power series in kWh.
    Samples come in ~5 min steps; 300 s is the nominal dt.
    """
    return float(power_series.dropna().sum() * dt_s / 3.6e6)
def f8_day_balance(start: str, end: str) -> pd.DataFrame:
    """
    Daily energy balance per F8 inverter over a date range.
    Columns (per day and sn):
      e_ac_counter_kWh  MEASURED AC energy (eToday counter, daily max)
      e_dc_channel_kWh  PRELIM DC energy (uPv*iPv channels, +3-4% bias
                        vs counter, verified 2026-09-10..15)
      eta_dc_ac         e_dc_channel / e_ac_counter; NOT an efficiency
                        (DC channels read high); diagnostic only.
    """
    rows = []
    for sn, df in f8_range_dfs(start, end).items():
        for date, g in df.groupby(df.index.date):
            g = g.dropna(subset=["ac_power_W"])
            if len(g) < 50:
                continue
            e_cnt = g["e_today_Wh"].max() / 1000.0 if "e_today_Wh" in g else None
            e_dc = energy_kWh(g["dc_power_W"]) if "dc_power_W" in g else None
            rows.append(dict(sn=sn, date=str(date),
                             e_ac_counter_kWh=e_cnt,
                             e_dc_channel_kWh=e_dc,
                             eta_dc_ac=(e_dc / e_cnt) if (e_dc and e_cnt) else None))
    return pd.DataFrame(rows)
