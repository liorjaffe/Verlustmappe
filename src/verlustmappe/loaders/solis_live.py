"""Live SolisCloud loader for Inverter 1 (PV side).

Inverter 1 converts the DC energy of the PV modules to AC for the
electrolyzer (PV -> AC -> EL). This loader queries the SolisCloud REST API
directly and returns the PV-path vocabulary (same names as grafana.PV_MAP),
so LivePipeline.push() can consume it unchanged:

  ac_power_W        inverter AC output towards the electrolyzer (MEASURED)
  dc_power_W        PV DC power, when the API reports it
  dc_V / dc_A       PV DC voltage / current, when reported
  ac_energy_Wh_cum  cumulative AC energy counter

Inverter 2 (battery/FC side, the LAST conversion loss in the chain) is
covered separately by loaders/solis.py (S5-EO1P5K-48: ac_out_W,
bus_voltage_V, batt_current_A, fc1/fc2_current_A). Do NOT feed this
loader's output into FCInverter.account().

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

__all__ = ["solis_live_df", "poll_solis_live", "SolisCloudError"]

API_URL = "https://www.soliscloud.com:13333"

DEFAULT_STATION_ID = "1298491919449567877"   # PV plant (Inverter 1 strings F1-F8)


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
    d = data.get("data", {})
    if isinstance(d, dict):
        return d.get("inverterList", []) or d.get("rows", [])
    return d or []


def inverter_detail(inverter_id: str, sn: str) -> dict:
    key_id, key_secret = _credentials()
    return _call(key_id, key_secret, "/v1/api/inveterDetail",
                 {"id": inverter_id, "sn": sn}).get("data", {})


# ---------------------------------------------------------------------------
# API field -> pipeline vocabulary (PV path, names as in grafana.PV_MAP).
# SolisCloud nests values as {"value": ..., "unit": ...}. VERIFY once with
# inverter_detail() and adjust here if your firmware uses other keys:
# pac = AC active power, dcPow = DC power, eTotal = cumulative energy.
# ---------------------------------------------------------------------------
_DETAIL_MAP = [
    ("pac",    "ac_power_W"),
    ("dcPow",  "dc_power_W"),
    ("dcV",    "dc_V"),
    ("dcA",    "dc_A"),
    ("eTotal", "ac_energy_Wh_cum"),
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
    for api_key, col in _DETAIL_MAP:
        v = _num(detail.get(api_key))
        if v is not None:
            row[col] = v
    return {"ts": ts, **row}


# ---------------------------------------------------------------------------
# Public loaders (pipeline vocabulary out)
# ---------------------------------------------------------------------------
def solis_live_df(station_id: str = None,
                  inverter_sn: str = None,
                  inverter_id: str = None) -> pd.DataFrame:
    """
    One live snapshot of Inverter 1 as a single-row DataFrame, UTC-indexed,
    in the PV vocabulary (ac_power_W, dc_power_W, ...).

    inverter_id is the SolisCloud internal id (from list_inverters), NOT the
    serial number. If only inverter_sn is given it is resolved per call.
    """
    _credentials()  # fail fast with a clear message
    station_id = station_id or os.getenv("SOLISCLOUD_STATION_ID", DEFAULT_STATION_ID)
    inverter_sn = inverter_sn or os.getenv("SOLISCLOUD_INVERTER_SN")

    if not inverter_sn:
        raise SolisCloudError(
            "pass inverter_sn (the serial of Inverter 1) or set "
            "SOLISCLOUD_INVERTER_SN; plant-level KPIs mix all PV strings"
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
        for df in poll_solis_live(300, inverter_sn="<sn of inverter 1>"):
            out = pipe.push(df)
    """
    while True:
        t0 = time.time()
        yield solis_live_df(**kwargs)
        rest = interval_s - (time.time() - t0)
        if rest > 0:
            time.sleep(rest)
