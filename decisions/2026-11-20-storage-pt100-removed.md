# 2026-11-20 - Storage Pt100 tank temperature sensor removed from the project

## Owner statement

The Pt100 on the storage cylinder will not be installed. All measurement options that
depended on it are dropped; the sensor is removed from the project. Places that stop
working are to be reported to the owner, not worked around.

Supersedes the temperature-concept parts of `decisions/2026-11-13-storage-data.md`
(single shell Pt100 as BACKLOG concept, suspended data path, inline-well option).

## Changes

- `plant/storage.toml`: key `stor.temp_sensor_planned` removed (registry 132 -> 131);
  Pt100 and inline-thermowell open questions removed; notes reworded.
- `CONTRACT.md` storage section: temperature-concept rule replaced by the removal; Route 2
  pause reason no longer names a planned Pt100.
- Code texts only (no computation change): `hydrogen/temperature_model.py`,
  `hydrogen/route2_tank_pv.py` (Route 2 reason string), `devices/h2_compressor.py`,
  `devices/storage.py`; `loaders/FORMATS.md` planned `tank_T_*` channels removed.
- Tests: snapshot count 131; Pt100 concept test replaced by a removal check; Route 2 reason
  assertion updated.
- Unchanged: `stor.T_assumed_C` = 20 degC GUESS with the +/-10 K band; tier-2 helper for
  explicitly supplied synthetic temperatures; Storage Master literature row (now row 56,
  key `stor.t_sensor.literature`, S14).

## Workbooks (owner: the sensor no longer appears in the project)

- `Storage_H2_System_Specs_Master.xlsx`: Master rows 56-59 (concept, inline alternative,
  supplier constraints, quote) deleted, literature row moves 60 -> 56; Corrections rows 8, 9,
  11 deleted (row 10 -> 8); Open_Points rows 2-3 deleted; S7 and S13 descriptions and the
  Overview L3 line no longer mention the sensor; unused shared strings blanked; filter range
  and print-area names adjusted.
- `Fuel_Cell_System_Specs_Master_2026-11-12.xlsx`: Route 2 note (3 cells) reworded.
- Older decision records keep their historical wording; this file supersedes them.

## Consequence

- Without any tank temperature measurement, Route 2 (independent tank pV countercheck) can
  only be reactivated with another approved temperature determination (e.g. the tier-3
  GS_tank model, not implemented). Storage and booster stay on the 20 degC assumption.
