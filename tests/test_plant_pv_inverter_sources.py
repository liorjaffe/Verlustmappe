"""PV inverter transfers from the owner-assigned S6 workbook, not old TOML values."""

from pathlib import Path
import tomllib

import pytest

import _path
import xlsx_reader
from verlustmappe import registry as R
from verlustmappe.accounting.status import u_class
from verlustmappe.devices import PVInverter
from verlustmappe.devices.pv_array import pv_account


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "plant/sources/Inverter1_PV_Solis_S6-GR1P6K_Specs_Master.xlsx"


@pytest.mark.parametrize("key,row,percent", [
    ("inv_pv.eta_euro", 30, "97.1"),
    ("inv_pv.eta_peak", 29, "97.7"),
])
def test_efficiency_anchors_have_manufacturer_provenance(key, row, percent):
    sheets = xlsx_reader.load(WORKBOOK)
    cells = sheets["Master"][row]
    assert cells["C"]["v"] == percent
    assert cells["C"]["f"] is None
    assert cells["F"]["v"] == "DATASHEET"
    assert "PDF p.2" in cells["E"]["v"]
    assert "column 6K" in cells["E"]["v"]
    assert "Max. efficiency 97.7% / EU efficiency 97.1%" in sheets["Sources"][3]["B"]["v"]
    entry = R.entry(key)
    assert entry["value"] == float(percent) / 100
    assert entry["status"] == "DATASHEET"
    assert entry["uncertainty"] == 0.0
    assert u_class(key, entry["status"], entry["uncertainty"]) == "NOT ASSESSED"
    assert f"Master row {row}" in entry["source"]
    assert "p.2" in entry["source"]
    assert "column 6K" in entry["source"]
    assert f"'{percent}%'" in entry["source"]


def test_identity_is_model_and_serials_not_workbook_number():
    sheets = xlsx_reader.load(WORKBOOK)
    assert sheets["Master"][3]["C"]["v"] == "S6-GR1P6K"
    assert sheets["Master"][4]["C"]["v"] == "1802060225250009"
    assert sheets["Master"][5]["C"]["v"] == "1802060225250007"
    entry = R.entry("inv_pv.model")
    for text in ("S6-GR1P6K", "1802060225250007", "1802060225250009"):
        assert text in entry["value"]
    assert "Unit A has no reviewed nameplate" in entry["source"]


def test_no_foreign_efficiency_keys_or_band_are_registered():
    keys = {key for key in R.REGISTRY if key.startswith("inv_pv.")}
    assert keys == {
        "inv_pv.model", "inv_pv.eta_euro", "inv_pv.eta_peak",
        "inv_pv.standby_W", "inv_pv.mppt_efficiency",
    }


def test_night_bound_and_mppt_are_not_invented_point_values():
    sheets = xlsx_reader.load(WORKBOOK)
    assert sheets["Master"][35]["C"]["v"] == "<1"
    assert sheets["Master"][35]["G"]["v"] == "bound, not exact"
    for key in ("inv_pv.standby_W", "inv_pv.mppt_efficiency"):
        assert R.get(key) is None
        assert R.entry(key)["status"] == "BACKLOG"
    assert "'<1 W'" in R.entry("inv_pv.standby_W")["source"]
    for result in (
        PVInverter().account(e_dc_kWh=100.0),
        PVInverter().account(e_dc_kWh=100.0, e_ac_kWh=95.0),
    ):
        assert result["standby_kWh"] is None
        assert "missing" in result["note"].lower()


def test_interim_constant_has_independent_hundred_kwh_reference():
    # 100 kWh * 97.1/100 = 97.1 kWh AC; complementary conversion is 2.9 kWh.
    result = PVInverter().account(e_dc_kWh=100.0)
    assert result["e_ac_kWh"] == pytest.approx(97.1, rel=0, abs=1e-12)
    assert result["loss_kWh"] == pytest.approx(2.9, rel=0, abs=1e-12)
    assert result["eta_is_measured"] is False
    assert result["eta_status"] == "DATASHEET"
    assert result["eta_model_status"] == "DERIVED"
    assert result["uncertainty_rel"] is None
    for text in ("INTERIM", "curve BACKLOG", "no part-load coverage", "not verified for F8"):
        assert text in result["note"]


@pytest.mark.parametrize(
    "dc,ac,loss,eta,difference,residual,anomaly",
    [
        (100.0, 95.0, 2.9, 0.95, 5.0, 2.1, None),
        (100.0, 0.0, 2.9, 0.0, 100.0, 97.1, None),
        (100.0, 110.0, 2.9, 1.1, -10.0, -12.9, None),
        (0.0, 0.0, 0.0, None, 0.0, 0.0, None),
        (0.0, 1.0, None, None, None, None, "dc0_ac_nonzero"),
        (None, 1.0, None, None, None, None, None),
    ],
)
def test_measured_mode_separates_model_and_diagnostics(dc, ac, loss, eta, difference, residual, anomaly):
    result = PVInverter().account(e_dc_kWh=dc, e_ac_kWh=ac)
    assert result["e_dc_kWh"] == dc and result["e_ac_kWh"] == ac
    for key, expected in (("loss_kWh", loss), ("eta", eta),
                          ("dc_minus_ac_diagnostic_kWh", difference),
                          ("model_minus_measured_ac_diagnostic_kWh", residual)):
        if expected is None:
            assert result[key] is None
        else:
            assert result[key] == pytest.approx(expected, abs=1e-12)
    assert result["undefined_case"] == anomaly
    assert result["loss_status"] == ("MISSING" if loss is None else "INTERIM DERIVED")
    assert result["uncertainty_rel"] is None
    assert result["eta_status"] == ("DIAGNOSTIC" if eta is not None else "MISSING")
    assert result["eta_is_measured"] is False
    assert result["eta_based_on_measured_energies"] == (dc is not None and ac is not None and dc > 0)


@pytest.mark.parametrize("bad_dc", [-1.0, float("nan"), float("inf"), -float("inf"), True])
@pytest.mark.parametrize("consumer", ["inverter", "array", "system"])
def test_pv_consumers_reject_invalid_dc_measurements(bad_dc, consumer):
    from verlustmappe.devices.pv_array import PVSystem

    with pytest.raises(ValueError, match="dc.*finite.*nonnegative"):
        if consumer == "inverter":
            PVInverter().account(e_dc_kWh=bad_dc, e_ac_kWh=1.0)
        elif consumer == "array":
            pv_account(E_dc_measured_kWh=bad_dc, E_ac_measured_kWh=1.0, profile="F8_12.74kWp")
        else:
            PVSystem().account(e_dc_kWh=bad_dc, e_ac_kWh=1.0)


@pytest.mark.parametrize("bad_ac", [float("nan"), float("inf"), -float("inf"), True])
@pytest.mark.parametrize("consumer", ["inverter", "array", "system"])
def test_pv_consumers_reject_nonfinite_ac_measurements(bad_ac, consumer):
    from verlustmappe.devices.pv_array import PVSystem

    with pytest.raises(ValueError, match="ac.*finite"):
        if consumer == "inverter":
            PVInverter().account(e_dc_kWh=1.0, e_ac_kWh=bad_ac)
        elif consumer == "array":
            pv_account(E_dc_measured_kWh=1.0, E_ac_measured_kWh=bad_ac, profile="F8_12.74kWp")
        else:
            PVSystem().account(e_dc_kWh=1.0, e_ac_kWh=bad_ac)


def test_signed_ac_measurement_remains_visible_without_boundary_assumptions():
    result = PVInverter().account(e_dc_kWh=1.0, e_ac_kWh=-0.1)
    assert result["e_ac_kWh"] == -0.1
    assert result["eta_status"] == "DIAGNOSTIC"


def test_f8_measured_array_uses_terminal_model_not_measured_difference():
    result = pv_account(E_dc_measured_kWh=100.0, E_ac_measured_kWh=95.0,
                        profile="F8_12.74kWp")
    bar = next(b for b in result["bars"] if b["stage"] == "Inverter conversion")
    assert bar["kWh"] == pytest.approx(2.9, abs=1e-12)
    assert bar["status"] == "INTERIM DERIVED"
    assert result["dc_minus_ac_diagnostic_kWh"] == pytest.approx(5.0)
    assert result["eta_dc_to_ac_status"] == "DIAGNOSTIC"
    assert result["inverter_diagnostics"]["model_minus_measured_ac_diagnostic_kWh"] == pytest.approx(2.1)
    assert result["missing_parameters"] == []
    assert result["pv_start_boundary"] == "inverter_dc_input"
    assert result["dc_cable_status"] == "OUTSIDE_BOUNDARY"

    anomaly = pv_account(E_dc_measured_kWh=0.0, E_ac_measured_kWh=1.0,
                         profile="F8_12.74kWp")
    bar = next(b for b in anomaly["bars"] if b["stage"] == "Inverter conversion")
    assert bar["kWh"] is None and bar["status"] == "MISSING"
    assert anomaly["undefined_case"] == "dc0_ac_nonzero"
    assert anomaly["dc_minus_ac_diagnostic_kWh"] is None


def test_other_pv_profiles_do_not_use_f8_inverter_model():
    from verlustmappe.devices.pv_array import PVSystem

    result = pv_account(E_dc_measured_kWh=100.0, E_ac_measured_kWh=95.0)
    bar = next(b for b in result["bars"] if b["stage"] == "Inverter conversion")
    assert bar["kWh"] is None and bar["status"] == "MISSING"
    assert result["dc_minus_ac_diagnostic_kWh"] == 5.0
    system = PVSystem().account(e_dc_kWh=100.0, e_ac_kWh=95.0)
    assert system["inverter_loss_kWh"] is None
    assert system["dc_minus_ac_diagnostic_kWh"] == 5.0
    assert system["inverter_eff_status"] == "DIAGNOSTIC"
    anomaly = PVSystem().account(e_dc_kWh=0.0, e_ac_kWh=1.0)
    assert anomaly["undefined_case"] == "dc0_ac_nonzero"
    assert anomaly["dc_minus_ac_diagnostic_kWh"] is None


@pytest.mark.parametrize("dc,ratio", [(10.0, 0.5), (30.0, 1.5)])
def test_pv_system_capture_ratio_never_emits_a_difference_as_a_loss(dc, ratio):
    from verlustmappe.devices.pv_array import PVSystem

    # 2 kWh/m2 * 10 kW = 20 kWh reference; include both sides of that reference.
    result = PVSystem().account(e_dc_kWh=dc, e_ac_kWh=9.0,
                                H_poa_kWh_m2=2.0, p_stc_W=10000.0)
    assert result["e_dc_kWh"] == dc
    assert result["e_ac_kWh"] == 9.0
    assert result["capture_ratio"] == pytest.approx(ratio)
    assert result["p_stc_source"] == "explicit p_stc_W argument"
    assert result["inverter_loss_kWh"] is None
    assert "pv_capture_loss_kWh" not in result
    without_irradiance = PVSystem().account(e_dc_kWh=dc, e_ac_kWh=9.0)
    assert "pv_capture_loss_kWh" not in without_irradiance
    assert "capture_ratio" not in without_irradiance


def test_s6_design_limits_are_traceable_and_assumptions_are_conditional():
    master = xlsx_reader.load(WORKBOOK)["Master"]
    assert master[9]["C"]["v"] == "9"
    assert master[10]["C"]["v"] == "600"
    assert master[13]["C"]["v"] == "90-520"
    assert master[14]["C"]["v"] == "14 / 14"
    assert master[15]["C"]["v"] == "22 / 22"
    assert 7 * 49.81 < 600 < 14 * 49.81
    assert 14 * 455 / 1000 < 9
    assert 20 * 455 / 1000 > 9


def test_workbook_registry_correction_is_historical_and_implemented():
    sheets = xlsx_reader.load(WORKBOOK)
    row = sheets["Master"][33]
    assert row["F"]["v"] == "DECIDED"
    assert "removed, not retained as BACKLOG" in row["D"]["v"]
    assert "24b5f73" in row["E"]["v"] and "378880f" in row["E"]["v"]
    assert "implemented 2026-11-13" in sheets["Notes"][4]["B"]["v"]


def test_pv_array_keeps_partial_measurements_missing_without_blocking_on_cable():
    result = pv_account(
        E_dc_measured_kWh=100.0, months=1, mode="measured", profile="F8_12.74kWp",
    )
    assert result["e_dc_kWh"] == 100.0
    assert result["e_ac_kWh"] is None
    assert result["missing_parameters"] == []
    assert result["pv_start_boundary"] == "inverter_dc_input"
    assert result["dc_cable_status"] == "OUTSIDE_BOUNDARY"
    assert all(bar["status"] == "MISSING" and bar["kWh"] is None
               for bar in result["bars"] if bar["stage"] in (
                   "Inverter conversion", "AC cable"))
    assert not any(bar["stage"] == "DC cable" for bar in result["bars"])

    measured = pv_account(
        E_dc_measured_kWh=100.0, E_ac_measured_kWh=95.0,
        months=1, mode="measured", profile="F8_12.74kWp",
    )
    assert measured["e_ac_kWh"] == pytest.approx(95.0, rel=0, abs=1e-12)
    assert not any(bar["stage"] == "DC cable" for bar in measured["bars"])
    assert "not assumed lossless" in measured["warning"]


def test_generation_model_requires_explicit_opt_in():
    with pytest.raises(NotImplementedError, match="generation modelling is deferred"):
        pv_account(H_poa_kWh_m2=160.0, profile="F8_12.74kWp")
    with pytest.raises(NotImplementedError, match="generation modelling is deferred"):
        pv_account(H_poa_kWh_m2=160.0, mode="preliminary", profile="F8_12.74kWp")


@pytest.mark.parametrize("invalid_opt_in", ["yes", 1, None])
def test_generation_model_opt_in_must_be_boolean(invalid_opt_in):
    with pytest.raises(ValueError, match="enable_generation_model must be a bool"):
        pv_account(H_poa_kWh_m2=160.0, enable_generation_model=invalid_opt_in)


def test_measured_path_excludes_generation_outputs_even_with_irradiance():
    result = pv_account(H_poa_kWh_m2=160.0, E_dc_measured_kWh=100.0,
                        E_ac_measured_kWh=95.0, profile="F8_12.74kWp")
    assert result["e_dc_kWh"] == 100.0
    assert result["e_ac_kWh"] == 95.0
    assert result["e_stc_kWh"] is None
    assert result["T_cell_C"] is None
    assert result["capture_ratio"] is None
    assert "irradiation was not used" in result["warning"]
    assert not any(bar["stage"] in ("Soiling", "Mismatch", "Shading",
                                    "Cell temperature", "Bifacial gain")
                   for bar in result["bars"])
    inverter = next(bar for bar in result["bars"] if bar["stage"] == "Inverter conversion")
    assert inverter["kWh"] == pytest.approx(2.9, abs=1e-12)
    assert result["dc_minus_ac_diagnostic_kWh"] == 5.0


@pytest.mark.parametrize("dc,ac", [(100.0, None), (0.0, None), (None, 95.0)])
@pytest.mark.parametrize("cable_loss", [None, 0.01])
def test_partial_measurements_do_not_invoke_generation_or_assume_boundary(monkeypatch, dc, ac, cable_loss):
    original_get = R.get
    monkeypatch.setattr(R, "get", lambda key: cable_loss if key == "cable.dc_loss_rel" else original_get(key))
    result = pv_account(H_poa_kWh_m2=160.0, E_dc_measured_kWh=dc, E_ac_measured_kWh=ac,
                        profile="F8_12.74kWp")
    assert result["mode"] == "measured"
    assert result["e_dc_kWh"] == dc
    assert result["e_ac_kWh"] == ac
    assert result["e_stc_kWh"] is None
    assert result["capture_ratio"] is None
    assert result["pv_start_boundary"] == "inverter_dc_input"
    assert result["dc_cable_status"] == "OUTSIDE_BOUNDARY"
    assert result["missing_parameters"] == []
    assert "incomplete measured DC/AC pair" in result["warning"]
    assert all(bar["kWh"] is None and bar["status"] == "MISSING" for bar in result["bars"])
    assert not any(bar["stage"] == "DC cable" for bar in result["bars"])


@pytest.mark.parametrize("cable_loss", [None, 0.01])
def test_inverter_input_boundary_does_not_apply_upstream_cable_loss(monkeypatch, cable_loss):
    original_get = R.get
    monkeypatch.setattr(R, "get", lambda key: cable_loss if key == "cable.dc_loss_rel" else original_get(key))
    result = pv_account(E_dc_measured_kWh=100.0, E_ac_measured_kWh=95.0,
                        profile="F8_12.74kWp")
    assert result["e_dc_kWh"] == 100.0
    assert result["e_ac_kWh"] == 95.0
    assert result["pv_start_boundary"] == "inverter_dc_input"
    assert result["dc_cable_status"] == "OUTSIDE_BOUNDARY"
    assert result["missing_parameters"] == []
    assert [bar["stage"] for bar in result["bars"]] == ["Inverter conversion"]
    assert result["bars"][0]["kWh"] == pytest.approx(100.0 * (1 - 0.971))
    assert "outside this provisional boundary, not assumed lossless" in result["warning"]


def test_workbook_identity_and_interim_decision_are_recorded():
    with (ROOT / "plant/pv_inverter.toml").open("rb") as fh:
        plant = tomllib.load(fh)
    assert plant["notes"]["workbook_sha256"] == xlsx_reader.sha256(WORKBOOK)
    assert "INTERIM" in plant["notes"]["constant_use"]
    assert "curve BACKLOG" in plant["notes"]["constant_use"]
    assert "No band adopted" in plant["notes"]["uncertainty"]
    assert all("datasheet missing" not in question for question in plant["open"]["questions"])
    decision = (ROOT / "decisions/2026-11-13_pv-inverter-efficiency.md").read_text()
    assert "0.980 PRELIM -> 0.971 DATASHEET" in decision
    assert "0.985 PRELIM -> 0.977 DATASHEET" in decision
    assert "No uncertainty band" in decision
