"""PV generation placeholder remains empty, unavailable and separate from measurements."""
import _path
from verlustmappe.devices import pv_array


def main():
    assert not hasattr(pv_array, "PLANT_PROFILES")
    assert not hasattr(pv_array, "DEFAULT_PROFILE")
    assert not hasattr(pv_array, "cell_temperature")
    cases = (
        lambda: pv_array.pv_account(H_poa_kWh_m2=100.0, A_array_m2=10.0),
        lambda: pv_array.pv_account(H_poa_kWh_m2=100.0, A_array_m2=10.0, enable_generation_model=True),
        lambda: pv_array.pv_account(mode="preliminary", enable_generation_model=True, profile="F8_12.74kWp"),
        lambda: pv_array.pv_account(E_dc_measured_kWh=100.0, E_ac_measured_kWh=95.0,
                                    enable_generation_model=True),
    )
    for call in cases:
        try:
            call()
        except NotImplementedError as exc:
            assert "deferred and not implemented" in str(exc)
        else:
            raise AssertionError("generation placeholder accepted a model request")

    measured = pv_array.pv_account(H_poa_kWh_m2=100.0,
                                   E_dc_measured_kWh=100.0, E_ac_measured_kWh=95.0)
    assert measured["e_dc_kWh"] == 100.0 and measured["e_ac_kWh"] == 95.0
    assert measured["profile"] is None
    assert measured["e_stc_kWh"] is None and measured["T_cell_C"] is None
    assert "irradiation was not used" in measured["warning"]
    assert all(bar["stage"] not in ("Soiling", "Mismatch", "Shading",
                                    "Cell temperature", "Bifacial gain")
               for bar in measured["bars"])
    print("PASS PV generation placeholder: unavailable, no plant profiles, measured path intact")


if __name__ == "__main__":
    main()
