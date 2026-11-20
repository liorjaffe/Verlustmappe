# 2026-11-19 - Water Tank WTM 2.1: nameplate values apply

## Context

The plant has one Enapter Water Tank Module WTM 2.1 (properties: model WTM21, product
revision WTM21 REV1, product code WTM21A5V01, firmware 1.5.0.344782). It is installed in one
of the two racks with the electrolysers and dryers; water path RO permeate -> WTM 2.1 -> all
9 EL 2.1 (owner, 2026-11-19). It was missing from the water workbook and `plant/water.toml`.

## Owner decision

The values on the WTM nameplate (owner photo, S/N AT21..., Prod. Wk 42) apply:

| Parameter | Value | Datasheet WTM21-DTS-COM01_rev05 |
|---|---|---|
| Inlet water conductivity | < 20 uS/cm | "Maximum conductivity of 2 uS/cm" (stricter) |
| Power, standby / operative | 3 W / 35 W | same |
| Electrical input | 110/240 VAC, 50/60 Hz | AC 110-240 V |
| Water content | 40 L | 38.5 L (table), 38 L (text) |
| H2O inlet max pressure | 0.6 MPa | 0-6 barg |
| H2O outlet max pressure | 0.4 MPa | "up to 2.75 barg" = pump pressure-switch setting (footnote 1), a different quantity |

Datasheet deviations are kept in the workbook as reference only.

## Workbook

New tab "Water Tank WTM 2.1" in `plant/sources/Water_System_Specs_Master.xlsx`, Sources
No. 16-19, Notes 11, Overview row. SHA-256 before 0f7c17e3..., after adding the tab
f49b8562... (intermediate), after this decision d89d5536...

## Operation (owner, 2026-11-19)

The WTM is powered only while the EL are switched on (production and start-up phases),
like the dryers; it can technically be switched off separately but runs with the EL. It
is NOT a permanent base load. Model: WTM standby = 3 W x EL on-time (`el_on_h`); without
the on-time the standby value stays open. Workbook tab row 8 and Notes 11 corrected
(SHA-256 68e6c4fb...).

## Not decided / open

- Pump running time (`water.tank_pump_duty`): no source; stays empty (OPEN, never 0).
  The 35 W applying only while the demand pump runs is an inference from datasheet
  footnote 1.
- The 20 uS/cm limit is less strict than the datasheet 2 uS/cm; RO permeate conductivity
  is not measured (`water.perm_quality`).
- Gauge vs. absolute is not stated on the nameplate pressures.
- Datasheet depth 643 mm (table) vs 635 mm (drawing): not model-relevant, unresolved.
- `plant/water.toml` and `water.py` updated after owner approval (tank keys, chain checks).
- Photos not stored in the repository.
