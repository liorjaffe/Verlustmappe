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


def test_pv_array_dependent_conversion_uses_eu_not_peak():
    result = pv_account(
        E_dc_measured_kWh=100.0, months=1, mode="measured", profile="F8_12.74kWp",
    )
    # Existing DC/AC cable factors: 100 * 0.99 * 0.971 * 0.995.
    assert result["e_ac_kWh"] == pytest.approx(95.648355, rel=0, abs=1e-12)
    conversion = next(bar for bar in result["bars"] if bar["stage"] == "Inverter conversion")
    assert conversion["kWh"] == pytest.approx(2.871, rel=0, abs=1e-12)


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
