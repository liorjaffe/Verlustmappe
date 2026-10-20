"""Regenerate docs/02_uncertainty_register.md from registry.py. Run after any registry edit."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from verlustmappe import registry as R

ORDER = {"BACKLOG": 0, "GUESS": 1, "PRELIM": 2, "DERIVED": 3, "DATASHEET": 4, "MEASURED": 5}

def main():
    rows = sorted(((v["status"], k, v) for k, v in R.REGISTRY.items()),
                  key=lambda r: (ORDER[r[0]], -float(r[2]["uncertainty"]) if isinstance(r[2]["uncertainty"], (int, float)) else 0))
    L = ["# Uncertainty register", "",
         "All assumptions in the model, sorted from weakest to strongest. Generated from",
         "`src/verlustmappe/registry.py` by `reporting/make_register.py`; edit the registry, not this file.", "",
         "Status: BACKLOG = placeholder, MUST be replaced. GUESS = assumption bounded only by literature/physics.",
         "PRELIM = typical-market value, real hardware not yet chosen. DERIVED = computed from",
         "other entries. DATASHEET = manufacturer claim. MEASURED = measured by us.", "",
         "| Status | Key | Value | Unit | Rel. unc. | Source | What it drives |", "|---|---|---|---|---|---|---|"]
    for st, k, v in rows:
        L.append(f"| {st} | `{k}` | {v['value']} | {v['unit']} | {v['uncertainty']} | {v['source']} | {v['effect']} |")
    L += ["", "## The five weakest numbers and how to fix each", "",
          "1. `comp.overall_efficiency` (GUESS +-30%). Energy meter on the Kaeser air compressor during booster runs.",
          "2. `dry.vent_fraction` (GUESS +-50%). Bound with a long charge window: Faraday - tank-pV - known leaks.",
          "3. `el.n_cells` / `fc.n_cells` (GUESS). Ask the manufacturers; Faraday routes scale linearly with them.",
          "4. `meas.p_sensor_fso_bar` (ASSUMPTION 250-bar range). Confirm the ordered DCT 541 range; the Route-2 "
          "pressure term scales linearly with it.",
          "5. `stor.volume_L` (DATASHEET, was wrongly labelled MEASURED). Hydrostatic or geometric confirmation "
          "of the 800 L nameplate value.",
          "", "## Constants by construction (never present as measurements)", "",
          "- EL efficiency via the nameplate route = 62.4% LHV for any data.",
          "- FC efficiency via the nameplate route = 42.9% LHV for any data (a lower bound: nameplate says '<70 g/kWh')."]
    open(os.path.join(ROOT, "docs", "02_uncertainty_register.md"), "w").write("\n".join(L) + "\n")
    print("wrote docs/02_uncertainty_register.md with", len(rows), "entries")

if __name__ == "__main__": main()
