"""Regenerate docs/02_uncertainty_register.md from registry.py. Run after any registry edit."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from verlustmappe import registry as R

ORDER = {"REJECTED": -1, "BACKLOG": 0, "GUESS": 1, "PRELIM": 2, "DERIVED": 3, "OWNER_DECISION": 3.5,
         "DATASHEET_SECONDARY": 3.8, "DATASHEET": 4, "MEASURED": 5}

def main():
    rows = sorted(((v["status"], k, v) for k, v in R.REGISTRY.items()),
                  key=lambda r: (ORDER[r[0]], -float(r[2]["uncertainty"]) if isinstance(r[2]["uncertainty"], (int, float)) else 0))
    L = ["# Uncertainty register", "",
         "All assumptions in the model, sorted from weakest to strongest. Generated from",
         "`src/verlustmappe/registry.py` by `reporting/make_register.py`; edit the registry, not this file.", "",
         "Status: BACKLOG = placeholder, MUST be replaced. GUESS = assumption bounded only by literature/physics.",
         "PRELIM = typical-market value, real hardware not yet chosen. DERIVED = computed from",
         "other entries. DATASHEET = manufacturer claim. MEASURED = measured by us.",
         "OWNER_DECISION = project decision by the owner. DATASHEET_SECONDARY = secondary source with a known conflict.",
         "REJECTED = legacy-only, device basis wrong; never an input of the new core (DECISIONS D11).", "",
         "| Status | Key | Value | Unit | Rel. unc. | Source | What it drives |", "|---|---|---|---|---|---|---|"]
    for st, k, v in rows:
        L.append(f"| {st} | `{k}` | {v['value']} | {v['unit']} | {v['uncertainty']} | {v['source']} | {v['effect']} |")
    L += ["", "## The five weakest numbers and how to fix each", "",
          "1. `comp.overall_efficiency` (REJECTED, legacy-only, wrong device basis). The Kaeser air-compressor energy "
          "needs a meter (SIGMA CONTROL 2 kWh counter) during booster runs; no registry value replaces it until measured.",
          "2. `dry.vent_fraction` (GUESS +-50%). Bound with a long charge window: Faraday - tank-pV - known leaks.",
          "3. `el.n_cells` / `fc.n_cells` (GUESS). Ask the manufacturers; Faraday routes scale linearly with them.",
          "4. `meas.p_sensor_fso_bar` (DERIVED from the 0-400 bar range). Confirm the delivered DCT 541 label; the "
          "Route-2 pressure term scales linearly with it.",
          "5. `stor.volume_L` (DATASHEET, was wrongly labelled MEASURED). Hydrostatic or geometric confirmation "
          "of the 800 L nameplate value; valid only with `bundle_isolated`.",
          "", "## F8 PV array: open uncertainties (weakest first)", "",
          "1. Facade POA placeholder (dominant). The reference POA (160 kWh/m2/month) assumes near-optimal tilt; "
          "an east-vertical facade is morning-weighted with lower annual yield. Needs PVGIS, the Solis irradiance "
          "channel or a pyranometer.",
          "2. East-vertical shading (`pv.shading_rel`, PRELIM): unknown until the layout is surveyed.",
          "3. Soiling (`pv.soiling_rel`, PRELIM): vertical facade soils less than a tilted array; unmeasured.",
          "4. F8 PV inverter (2 x Solis S6-GR1P6K) efficiency: no datasheet registered yet; "
          "`inv_pv.eta_pv_ac_peak` and `inv_pv.eta_manual_range` are BACKLOG placeholders - "
          "the numbers 0.966 / 0.93-0.95 in them belong to the FC-side Solis S5-EO1P5K-48 and "
          "must NOT be used for the F8 S6 inverters (D6). `inv_pv.eta_euro` stays PRELIM "
          "(generic literature value, no F8-specific datasheet yet).",
          "4b. F8 station id 1298491919449567877 also hosts F7 (SN ...0011); per-inverter-SN filtering is "
          "mandatory before the measured channel goes live.",
          "5. String layout (`pv.string_config`, GUESS): 2 x 7 per inverter assumed; verify at the junction boxes.",
          "6. Imp discrepancy: nameplate 10.50 A vs MGK-36 datasheet 10.90 A (does not affect RTE, matters for fusing).",
          "7. Bifacial status (`pv.bifacial_gain_frac` = 0): 'MGEK' suffix on the nameplate vs monofacial MGK series.",
          "", "## Constants by construction (never present as measurements)", "",
          "- EL efficiency via the nameplate route = 62.4% LHV for any data.",
          "- FC efficiency via the nameplate route = 42.9% LHV for any data (a lower bound: nameplate says '<70 g/kWh')."]
    open(os.path.join(ROOT, "docs", "02_uncertainty_register.md"), "w").write("\n".join(L) + "\n")
    print("wrote docs/02_uncertainty_register.md with", len(rows), "entries")

if __name__ == "__main__": main()
