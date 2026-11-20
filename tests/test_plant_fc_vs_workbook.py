"""FC TOMLs against their workbook rows: mapping, row label and status (transfer check, not truth).

Owner 2026-11-19: automatic transfer check instead of key renaming. Status only for now;
values need machine-readable value/unit columns in the FC workbook (separate decision).
Status mapping for the FC workbook: owner-approved 2026-11-19
(decisions/2026-11-18-fc-workbook-review.md). The Inverter2 workbook already uses the
D26 vocabulary.
"""
import re
from collections import Counter
from pathlib import Path

import _path  # noqa: F401
import xlsx_reader as X
from verlustmappe import registry as R

ROOT = Path(__file__).resolve().parents[1]
FC_XLSX = ROOT / "plant/sources/Fuel_Cell_System_Specs_Master_2026-11-12.xlsx"
INV_XLSX = ROOT / "plant/sources/Inverter2_FC_Solis_S5-EO1P5K-48_Specs_Master.xlsx"
FC_STATUS = {"Measured": "MEASURED", "Datasheet": "DATASHEET", "Calculated": "DERIVED",
             "Literature": "DATASHEET_SECONDARY", "Assumed": "GUESS"}
PREFIXES = ("fc.", "bat.", "inv_fc.")

# TOML key -> (workbook, sheet, row, label substring in column B, workbook key in column I or None)
MAP = {
    "fc.rated_power_W": ("fc", "Fuel Cell", 10, "Rated output", "fc.rated_power"),
    "fc.control_input_W_max": ("fc", "Fuel Cell", 12, "Rated input", "fc.aux_input_max"),
    "fc.power_limit_W": ("fc", "Fuel Cell", 18, "Factory output power limit", "fc.power_limit_config"),
    "fc.h2_consumption_g_per_kWh": ("fc", "Fuel Cell", 26, "Fuel consumption", "fc.h2_consumption_g_kwh"),
    "fc.poc_max_duration_s": ("fc", "Fuel Cell", 62, "Performance Optimisation Cycle", "fc.poc"),
    "fc.poc_max_rate_per_h": ("fc", "Fuel Cell", 62, "Performance Optimisation Cycle", "fc.poc"),
    "fc.has_internal_dcdc": ("fc", "Fuel Cell", 65, "Fault state", "fc.fault"),
    "fc.standby_uc_A": ("fc", "Fuel Cell", 75, "Delayed Stop Under-Current", "fc.factory.delayed_stop_uc"),
    "fc.standby_uc_qual_s": ("fc", "Fuel Cell", 76, "Delayed Stop UC Qualification",
                             "fc.factory.delayed_stop_uc_qual"),
    "bat.nominal_V": ("fc", "Internal Battery", 9, "Nominal voltage", None),
    "bat.capacity_Ah": ("fc", "Internal Battery", 11, "Rated capacity", None),
    "bat.round_trip_efficiency": ("fc", "Internal Battery", 18, "Round-trip efficiency", None),
    "inv_fc.model": ("inv", "Master", 3, "Model", "inv_fc.model"),
    "inv_fc.battery_V_range": ("inv", "Master", 10, "Battery voltage range", "inv_fc.v_batt_range"),
    "inv_fc.nominal_power_W": ("inv", "Master", 34, "Rated output power", "inv_fc.p_ac_rated"),
    "inv_fc.transfer_time_ms": ("inv", "Master", 40, "Transfer time", "inv_fc.transfer_time_s"),
    "inv_fc.eta_peak_pv_ac": ("inv", "Master", 43, "Peak efficiency (PV-AC path)", "inv_fc.eta_pv_ac_peak"),
    "inv_fc.eta_manual_range": ("inv", "Master", 43, "Peak efficiency (PV-AC path)", "inv_fc.eta_pv_ac_peak"),
    "inv_fc.eta": ("inv", "Master", 44, "Discharge-path efficiency", "inv_fc.eta"),
    "inv_fc.standby_W": ("inv", "Master", 50, "Standby / idle consumption", "inv_fc.standby_W"),
}

# TOML keys with no workbook row, each with its basis
NOT_IN_WORKBOOK = {
    "fc.n_cells": "assumption; IE stack specification not public",
    "fc.faradaic_efficiency": "assumption; no crossover",
    "fc.poc_case_rate_per_h": "owner convention, decisions/2026-11-19-fc-poc-plan.md",
    "fc.poc_case_duration_s": "owner convention, decisions/2026-11-19-fc-poc-plan.md",
    "inv_fc.eta_envelope_lower": "owner convention, decisions/2026-11-18-fc-inverter-discharge-working-value.md",
    "inv_fc.eta_envelope_upper": "owner decision, decisions/2026-11-18-fc-inverter-discharge-working-value.md",
}

# Known workbook/TOML status deviations: the TOML follows a later owner rule; the workbook
# still needs the owner-approved update. Each must remain a real deviation (stale check).
KNOWN_STATUS_DEVIATIONS = {
}

# Workbook rows with a model key that are not transferred to a TOML (workbook-only evidence)
FC_WORKBOOK_ONLY = set("""
fc.rated_current fc.output_voltage_range fc.nominal_voltage fc.voltage_range fc.current_limit
fc.target_voltage fc.supply_pressure fc.purge_flow fc.purge_event fc.h2_consumption_ref_conditions
fc.ambient_temp_range fc.humidity_derate fc.altitude_derate fc.software_states fc.startup_time
fc.hybrid_architecture fc.standby fc.restart fc.overload fc.factory.target_output_voltage
fc.factory.delayed_start_uv fc.factory.delayed_start_qual fc.factory.immediate_start_uv
fc.factory.delayed_stop_ov fc.factory.delayed_stop_ov_qual fc.factory.deny_start_uv
fc.factory.system_index fc.factory.output_voltage_rise_rate fc.factory.min_output_voltage
fc.factory.hard_set_output_voltage fc.factory.restart_delay fc.net_efficiency_gap
fc.purge_loss_g_event fc.poc_loss_wh_event fc.standby_cycle_loss_wh fc.internal_bop_aux_w
fc.part_load_efficiency_curve
""".split())
INV_WORKBOOK_ONLY = set("""
inv_fc.sn inv_fc.manufacturer inv_fc.on_site inv_fc.position inv_fc.identity_guard
inv_fc.bus_compatibility inv_fc.i_batt_max inv_fc.batt_fuse inv_fc.batt_cable inv_fc.batt_comms
inv_fc.startup_source inv_fc.batt_settings inv_fc.pv_v_max inv_fc.pv_mppt_range
inv_fc.pv_mppt_full_load inv_fc.pv_mppt_number inv_fc.pv_i_max inv_fc.pv_isc_max
inv_fc.pv_charge_i_max inv_fc.pv_power_max_recommended inv_fc.ac_in_v inv_fc.ac_in_i_max
inv_fc.ac_in_p_max inv_fc.ac_charge_i_max inv_fc.ac_installation inv_fc.v_ac_rated
inv_fc.f_ac_rated inv_fc.i_ac_max inv_fc.surge_kva inv_fc.thdv inv_fc.backup_enable
inv_fc.eta_rule inv_fc.eta_measured_rule inv_fc.eta_curve inv_fc.test_note
inv_fc.standby_accounting inv_fc.poc_relevance inv_fc.poc_measurement inv_fc.protections
inv_fc.protection_class inv_fc.service_wait_s inv_fc.surface_temp_c inv_fc.display
inv_fc.work_mode inv_fc.special_settings inv_fc.comms inv_fc.datalogger_status
inv_fc.lcd_counters inv_fc.loader inv_fc.parallel inv_fc.dimensions inv_fc.environment
inv_fc.installation inv_fc.standards inv_fc.marks inv_fc.battery_compatibility
inv_fc.warranty inv_fc.eta_measurement inv_fc.startup_energy_wh inv_fc.ac_cable_loss
inv_fc.eta_curve_measurement inv_fc.standby_W_measurement inv_fc.standby_accounting_backlog
inv_fc.lcd_counters_campaign
""".split())

# Duplicate model keys in the Inverter2 workbook: rows 80-82 and 85 renamed 2026-11-19 (owner)
INV_KNOWN_DUPLICATES = {}


def _sheets():
    return {"fc": X.load(FC_XLSX), "inv": X.load(INV_XLSX)}


def _cell(sheets, wb, sheet, row, col):
    return sheets[wb][sheet].get(row, {}).get(col, {}).get("v", "").strip()


def _workbook_status(wb, raw):
    # "Nameplate" = DATASHEET in the Inverter2 workbook, as in the compressor workbook (owner 2026-11-19)
    return FC_STATUS.get(raw) if wb == "fc" else {"Nameplate": "DATASHEET"}.get(raw, raw)


def _keyed_rows(rows):
    return [(r, c["I"]["v"].strip()) for r, c in sorted(rows.items())
            if r > 1 and c.get("I", {}).get("v", "").strip()]


def test_every_fc_toml_key_is_mapped_or_explained():
    keys = {k for k in R.REGISTRY if k.startswith(PREFIXES)}
    assert keys == set(MAP) | set(NOT_IN_WORKBOOK), keys ^ (set(MAP) | set(NOT_IN_WORKBOOK))
    assert not set(MAP) & set(NOT_IN_WORKBOOK)


def test_mapped_rows_have_the_expected_label_and_key():
    sheets = _sheets()
    for key, (wb, sheet, row, label, wb_key) in MAP.items():
        assert label in _cell(sheets, wb, sheet, row, "B"), (key, sheet, row)
        if wb_key is not None:
            assert _cell(sheets, wb, sheet, row, "I") == wb_key, (key, sheet, row)


def test_status_equals_workbook_status_or_is_a_known_deviation():
    sheets = _sheets()
    for key, (wb, sheet, row, _, _) in MAP.items():
        expected = _workbook_status(wb, _cell(sheets, wb, sheet, row, "F"))
        actual = R.entry(key)["status"]
        if key in KNOWN_STATUS_DEVIATIONS:
            assert actual != expected, f"{key}: deviation resolved, remove it from the list"
        else:
            assert actual == expected, f"{key}: TOML {actual} vs workbook {expected} ({sheet} row {row})"


def test_fc_workbook_sources_cite_their_row():
    for key, (wb, sheet, row, _, _) in MAP.items():
        if wb != "fc":
            continue
        source = R.entry(key)["source"]
        cited = {int(n) for m in re.finditer(rf"{sheet} rows? ([\d\-, ]+)", source)
                 for a, _, b in re.findall(r"(\d+)(-(\d+))?", m.group(1))
                 for n in range(int(a), int(b or a) + 1)}
        assert row in cited, f"{key}: source does not cite {sheet} row {row}"


def test_every_keyed_workbook_row_is_classified():
    sheets = _sheets()
    mapped = {v[4] for v in MAP.values() if v[4]}
    for wb, sheet, only in (("fc", "Fuel Cell", FC_WORKBOOK_ONLY), ("inv", "Master", INV_WORKBOOK_ONLY)):
        keys = {k for _, k in _keyed_rows(sheets[wb][sheet])}
        prefix = "fc." if wb == "fc" else "inv_fc."
        unclassified = keys - mapped - only
        stale = only - keys
        assert not unclassified, f"{sheet}: new workbook keys to classify: {sorted(unclassified)}"
        assert not stale, f"{sheet}: stale workbook-only keys: {sorted(stale)}"
        assert not (only & {m for m in mapped if m.startswith(prefix)})


def test_workbook_duplicate_keys_are_only_the_known_ones():
    sheets = _sheets()
    fc_counts = Counter(k for _, k in _keyed_rows(sheets["fc"]["Fuel Cell"]))
    assert not [k for k, n in fc_counts.items() if n > 1]
    inv_rows = _keyed_rows(sheets["inv"]["Master"])
    dupes = {k: [r for r, kk in inv_rows if kk == k]
             for k, n in Counter(k for _, k in inv_rows).items() if n > 1}
    assert dupes == INV_KNOWN_DUPLICATES
