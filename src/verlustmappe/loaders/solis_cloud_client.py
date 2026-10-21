"""
Live feed from SolisCloud into your project (h2 verlustmappe).

Works at the user level with your own SolisCloud account.

SETUP (one time):
1. Log in at https://www.soliscloud.com
2. Service -> API Management -> Activate Now (identity check; Solis may
   approve via support ticket, which can take some days)
3. Copy your KeyID and KeySecret below.
4. pip install requests

Then:
    python solis_cloud_client.py
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Optional

import requests

# --------------------------------------------------------------------------
# CONFIG - fill in
# --------------------------------------------------------------------------
KEY_ID     = "your-keyid"          # SolisCloud -> Service -> API Management
KEY_SECRET = "your-keysecret"
API_URL    = "https://www.soliscloud.com:13333"

STATION_ID = "1298491919449567877"  # from your plant URL
INVERTER_SN = None                  # set your inverter sn here, e.g. "1802..."


# --------------------------------------------------------------------------
# Signing + request machinery (SolisCloud HMAC-SHA1 scheme)
# --------------------------------------------------------------------------
def _call(url_part: str, body: dict) -> dict:
    payload = json.dumps(body, separators=(",", ":"))
    md5 = base64.b64encode(hashlib.md5(payload.encode("utf-8")).digest()).decode()
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    sign_str = f"POST\n{md5}\napplication/json\n{now}\n{url_part}"
    sign = base64.b64encode(
        hmac.new(KEY_SECRET.encode(), sign_str.encode(), hashlib.sha1).digest()
    ).decode()
    headers = {
        "Content-MD5": md5,
        "Content-Type": "application/json;charset=UTF-8",
        "Date": now,
        "Authorization": f"API {KEY_ID}:{sign}",
    }
    r = requests.post(API_URL + url_part, headers=headers, data=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise RuntimeError(f"SolisCloud error: {data}")
    return data


# --------------------------------------------------------------------------
# Endpoints you will use
# --------------------------------------------------------------------------
def list_inverters(station_id: str = STATION_ID) -> dict:
    """Inverters of the plant; gives each inverter's own 'id' (needed below)."""
    return _call("/v1/api/inveterList", {"stationId": station_id, "pageNo": 1, "pageSize": 100})


def inverter_detail(inverter_id: str, sn: str) -> dict:
    """Live detail of ONE inverter (power, energy, temperatures, ...)."""
    return _call("/v1/api/inveterDetail", {"id": inverter_id, "sn": sn})


def station_real_kpi(station_id: str = STATION_ID) -> dict:
    """Live plant-level KPIs: current power, today's energy, ..."""
    return _call("/v1/api/getStationRealKpi", {"id": station_id})


def poll(interval_seconds: int = 300):
    """
    Generator yielding live data every `interval_seconds`.
    SolisCloud updates the values every ~5 minutes, so 300 s is the natural
    fastest rate; polling faster gets you repeated data.

    Usage:
        for snapshot in poll(300):
            kpi = snapshot["station"]
            print(kpi)          # feed this into your verlustmappe code
    """
    # discover the inverter's own id once
    inv_id = None
    if INVERTER_SN:
        invs = list_inverters().get("data", {}).get("inverterList", []) \
            or list_inverters().get("data", [])
        for inv in invs:
            if str(inv.get("sn")) == str(INVERTER_SN):
                inv_id = str(inv.get("id"))
                break
    while True:
        t0 = time.time()
        snapshot = {"time": time.time(), "station": station_real_kpi()}
        if INVERTER_SN and inv_id:
            snapshot["inverter"] = inverter_detail(inv_id, INVERTER_SN)
        yield snapshot
        rest = interval_seconds - (time.time() - t0)
        if rest > 0:
            time.sleep(rest)


# --------------------------------------------------------------------------
# Test run
# --------------------------------------------------------------------------
if __name__ == "__main__":
    print("Inverters of the plant:")
    invs = list_inverters()
    print(json.dumps(invs, indent=2)[:2000])

    print("\nStation KPIs right now:")
    print(json.dumps(station_real_kpi(), indent=2)[:2000])

    # Continuous feed:
    # for snapshot in poll(300):
    #     print(snapshot["station"])
