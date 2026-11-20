# 2026-11-19 - EL uncertainties without a source set to NOT ASSESSED

## Owner approval

The relative uncertainties in `plant/el.toml` have no source: the EL workbook
(`plant/sources/EL21_Electrolyser_Specs_Master_2026-11-12.xlsx`, EL 2.1 sheet, column G)
states no tolerance for these rows ('-' or a verification note only). As for PV
(2026-11-13) and FC (2026-11-19), they are set to 0.0 = NOT ASSESSED:

el.production_rate_NLh (was 0.02), el.power_operative_W (0.02), el.power_standby_W (0.05),
el.spec_energy_kWh_per_Nm3 (0.03), el.h2_purity (0.0005), el.water_consumption_mLh (0.1),
el.n_cells (0.05), el.faradaic_efficiency (0.03), el.startup_duration_s (0.15).
el.output_pressure_barg was already 0.0.

Values, units, statuses and effects are unchanged; each source text gains the
NOT ASSESSED note. This also removes the former faradaic band reaching 1.01 (> 1).

## Result effect

- The nameplate EL H2 route (`hydrogen/routen_nameplate.py`) reports uncertainty 0.0
  (NOT ASSESSED) instead of 0.03.
- P14 (`accounting/static_map.py`) classifies el.n_cells and el.faradaic_efficiency as
  NOT ASSESSED instead of assessed bands 0.05 / 0.03.

## Test change (owner-approved 2026-11-19)

`tests/test_accounting_static_map.py::test_input_bands_not_propagated_output_uncertainty`:
expectations for el.n_cells / el.faradaic_efficiency changed from ("assessed", 0.05) /
("assessed", 0.03) to ("NOT ASSESSED", 0.0). The old bands came unsourced from the first
upload (`1b8412d`, registry.py) and were copied into the test in `08d58ea`; no owner
decision on them is recorded. H2 values are unchanged (nominal values unchanged; P14 does
not propagate input bands).

## Open

- Other EL workbook review findings (pressure version, start-up duration basis, n_cells
  derivation, missing workbook values, workbook inconsistencies) are separate decisions.
