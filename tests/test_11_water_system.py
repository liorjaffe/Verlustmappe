"""Water system (BWT bestaqua 14ROC COFFEE + Popular Filtros train): physics
back-checks against the spec workbook, hand calculations, and part-load
scaling with the ACTUAL hydrogen production."""
import _path
import numpy as np
from verlustmappe.devices import WaterSystem
from verlustmappe import registry as R
from verlustmappe.hydrogen.route4_water import h2_from_water

def main():
    # 1. stoichiometric consistency: 0.5 Nm3/h H2 needs 0.4 L/h water
    stoich_L_per_kgH2 = 18.015 / 2.016            # L water per kg H2 = 8.936
    h2_kgh = 0.5 * 2.016 / 22.414                 # kg H2 per h at 0.5 Nm3/h
    expected_Lh = stoich_L_per_kgH2 * h2_kgh      # 0.402 L/h
    assert abs(expected_Lh - 0.4019) < 0.01, expected_Lh
    ds = R.get("el.water_consumption_mLh") / 1000.0
    assert abs(ds - expected_Lh) < 0.01, "datasheet 0.4 L/h should equal stoichiometric demand"
    r4 = h2_from_water(0.4)
    assert abs(r4["kg"] - 0.4 * 2.016 / 18.015) < 1e-12
    # registry: the datasheet '~400 mL/h' is the rounded presentation of the
    # stoichiometric minimum, not a separate (smaller) value
    spec = R.get("water.spec_water_L_per_NL")
    stoich = R.get("water.spec_water_L_per_NL_stoich")
    assert abs(spec - 0.4 / 500.0) < 0.01 * spec    # within datasheet rounding
    assert abs(spec - stoich) < 1e-9, "datasheet and stoichiometric values must coincide after unrounding"

    w50, wf = 250.0 * spec, 500.0 * spec   # 0.2009 L / 0.4019 L (datasheet 0.2 / 0.4 L, rounded)

    # 2. part load 50%: water demand follows the ACTUAL production
    a50 = WaterSystem().account(duration_h=1.0, h2_produced_NL=250.0)
    assert abs(a50["water_consumed_L"] - 250.0 * spec) < 1e-9, a50["water_consumed_L"]
    assert abs(a50["water_consumed_L"] - 0.2) < 0.01 * 0.2
    assert abs(a50["duty"] - w50 / 120.0) < 1e-12
    assert abs(a50["energy_kWh_production"] - w50 / 120.0 * 0.2) < 1e-12
    assert abs(a50["feed_L"] - 2 * w50) < 1e-12
    assert abs(a50["concentrate_L"] - w50) < 1e-12
    # stoichiometric cross-check at part load: 250 NL x 0.0008037 >= 0.2 L
    assert 250.0 * stoich >= a50["water_consumed_L"] - 1e-12

    # 3. zero production: no water, no production energy, standby still booked
    a0 = WaterSystem().account(duration_h=1.0, h2_produced_NL=0.0)
    assert a0["water_consumed_L"] == 0.0
    assert a0["energy_kWh_production"] == 0.0
    assert abs(a0["energy_kWh_standby"] - 0.003) < 1e-12
    assert abs(a0["energy_kWh_model"] - 0.003) < 1e-12

    # 4. full load via h2_produced_NL equals the old nominal picture
    af = WaterSystem().account(duration_h=1.0, h2_produced_NL=500.0)
    assert abs(af["water_consumed_L"] - wf) < 1e-9
    assert abs(af["duty"] - wf / 120.0) < 1e-12
    assert abs(af["energy_kWh_model"] - (wf / 120.0 * 0.2 + 0.003)) < 1e-12
    assert abs(af["feed_L"] - 2 * wf) < 1e-12
    assert abs(af["concentrate_L"] - wf) < 1e-12

    # 5. fallback (no H2 given): old datasheet x duration, with loud warning
    a = WaterSystem().account(duration_h=1.0)
    assert abs(a["water_consumed_L"] - 0.4) < 1e-9
    assert a["water_status"].startswith("DATASHEET")
    assert any("fallback" in w.lower() or "h2" in w.lower() for w in a["warnings"]), a["warnings"]

    # 6. filter train booked at 0 W (GUESS status) with a warning
    assert af["filter_train_energy_kWh"] == 0.0
    assert any("filter-train pump" in w for w in af["warnings"])

    # 7. measured energy/water replace the model, model stays visible
    am = WaterSystem().account(duration_h=10.0, measured_kWh=0.05, measured_water_L=4.0)
    assert am["energy_kWh"] == 0.05 and am["energy_is_measured"]
    assert am["water_status"] == "MEASURED" and abs(am["water_consumed_L"] - 4.0) < 1e-9
    assert not any("modelled" in w for w in (am["warnings"] or []))

    # 8. standby switchable: RO powered off with the EL
    asw = WaterSystem().account(duration_h=1.0, h2_produced_NL=500.0, ro_standby_always_on=False)
    assert abs(asw["energy_kWh_model"] - (wf / 120.0 * 0.2 + wf / 120.0 * 0.003)) < 1e-12

    # 9. annual extrapolation matches the workbook: 7566 FLH -> 27.7 kWh/yr
    a_y = WaterSystem().account(duration_h=7566.0, h2_produced_NL=500.0 * 7566.0)
    assert abs(a_y["energy_kWh_model"] - (wf * 7566 / 120.0 * 0.2 + 7566 * 0.003)) < 1e-6
    assert abs(a_y["energy_kWh_model"] - 27.742) < 0.05, a_y["energy_kWh_model"]

    # 10. water mass closure: permeate == EL demand (1:1, no buffer assumed)
    assert af["permeate_L"] == af["water_consumed_L"]
    print("test_11_water_system PASS")

if __name__ == "__main__":
    main()
