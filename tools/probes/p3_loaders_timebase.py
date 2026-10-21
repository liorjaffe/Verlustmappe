"""Probe 3: Monte Carlo, loaders, time bases, live feed."""
from _common import check, summary
import tempfile, numpy as np, pandas as pd
from verlustmappe import registry as R
from verlustmappe.loaders.grafana import load_grafana
from verlustmappe.loaders.solis import inverter_eta_measured
from verlustmappe.balance.a_modes import partition_modes, energy_by_mode
from verlustmappe.devices import ElectrolyzerUnit
from verlustmappe.live_feed import LivePipeline

keys = [k for k, v in R.REGISTRY.items() if isinstance(v["value"], (int, float)) and not isinstance(v["value"], bool)
        and v["uncertainty"] > 0 and v["status"] != "MEASURED"]
from verlustmappe.uncertainty.montecarlo import _draw_value
rng = np.random.default_rng(0)
neg = [k for k in keys if R.REGISTRY[k]["value"] < 0]
flipped = [k for k in neg if any(_draw_value(rng, k, R.REGISTRY[k], R.REGISTRY[k]["value"]) > 0 for _ in range(2000))]
check("Monte Carlo forces negative-valued entries positive (sign flip instead of relative draw)", bool(flipped),
      "uncertainty/montecarlo.py: draw v*(1 + N(0,u)) for negative-valued entries; only clip fractions into (0,1]", str(flipped))
draws = np.array([_draw_value(rng, "fc.faradaic_efficiency", dict(unit="-", uncertainty=0.02), 1.0) for _ in range(20000)])
check("MC clipping of eta_F = 1.00 +- 2% at 1.0 gives a one-sided distribution",
      np.mean(draws == 1.0) > 0.05,
      "uncertainty/montecarlo.py: use a truncated normal or beta draw for efficiencies capped at 1",
      f"share of draws exactly 1.0: {np.mean(draws == 1.0):.3f}, max {draws.max():.4f}")

d = tempfile.mkdtemp()
open(d+"/a.csv", "w").write('"Series";"Time";"Value"\n"Power";"2026-09-22 10:00:05";"1200,0"\n"Power";"2026-09-22 10:00:05";"1201,0"\n'
                            '"Voltage";"2026-09-22 10:00:05";"48,0"\n"Voltage";"2026-09-22 10:00:10";"48,1"\n')
try:
    load_grafana([d+"/a.csv"]); check("Grafana loader crashes on duplicate timestamps", False)
except ValueError as e:
    check("Grafana loader crashes on duplicate timestamps when 2+ series are present", True,
          "loaders/grafana.py: aggregate duplicates (groupby(level=0).mean()) instead of failing", str(e))
open(d+"/b.csv", "w").write('"Series";"Time";"Value"\n"Power";"2026-09-22 10:00:00";"1.234,5"\n"Power";"2026-09-22 10:00:05";"1200,0"\n')
check("Grafana loader silently drops '1.234,5' values (thousands separator)",
      len(load_grafana([d+"/b.csv"])) == 1,
      "loaders/grafana.py: strip thousand-separator dots before replacing the decimal comma; warn per dropped row")

idx = pd.date_range("2026-01-01", periods=3600, freq="1s", tz="UTC")
s = pd.DataFrame({"ac_out_W": 2000.0, "bus_voltage_V": 52.0,
                  "batt_current_A": np.r_[np.full(1800, 41.0), np.full(1800, 2.0)]}, index=idx)
e = inverter_eta_measured(s)
check("Solis 'measured' efficiency uses battery current only - but the FC feeds the same bus",
      e["eta"] > 1,
      "loaders/solis.py: DC input = bus_V x (I_FC1 + I_FC2 + I_battery), or read a real inverter DC current",
      f"eta = {e['eta']:.2f}")

i2 = pd.DatetimeIndex(list(pd.date_range("2026-01-01", periods=60, freq="1s")) +
                      list(pd.date_range("2026-01-01 05:00", periods=60, freq="1s")))
dd = pd.DataFrame({"power_W": np.full(120, 2400.0)}, index=i2)
ebm = energy_by_mode(partition_modes(dd, "power_W"), "power_W")
check("energy_by_mode bridges data gaps (np.gradient over a 5 h gap)",
      sum(ebm.values()) > 1.0,
      "balance/a_modes.energy_by_mode: use the gap weights from electrolyzer._sample_gaps",
      f"{sum(ebm.values()):.2f} kWh vs true 0.08 kWh (EL account: {ElectrolyzerUnit().account(dd)['energy_in_kWh']:.4f})")

n = 600; o = LivePipeline(dt_s=1.0).push(pd.DataFrame({"power_W": np.full(n, 2400.0), "el_stack_current_A": np.full(n, 10.0)},
                                                      index=pd.date_range("2026", periods=n, freq="5s")))
check("Live feed H2 rate divides by nominal dt_s instead of the real timestamps",
      o["el"]["h2_NLh"] > 1000,
      "live_feed.py: use the elapsed time from the index, not len(df)*dt_s",
      f"{o['el']['h2_NLh']:.0f} NL/h vs ~491 true")

import inspect, verlustmappe, os
bridge = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(verlustmappe.__file__))), "tools", "regatron", "regatron_bridge.py")
txt = open(bridge).read()
from verlustmappe.loaders import regatron
check("Bridge writes naive LOCAL time; the loader parses it as UTC (the exact epoch_s column is unused)",
      "datetime.fromtimestamp(now_wall).isoformat" in txt and "epoch_s" not in inspect.getsource(regatron.load_fastlog),
      "loaders/regatron.py: index from epoch_s (pd.to_datetime(df.epoch_s, unit='s', utc=True)); timestamp_iso only as fallback")
summary()
