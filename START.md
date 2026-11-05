# START – current state (overwritten, never appended; at most 60 lines)

State: 2026-11-05 · branch `neustart` · `main` unchanged until the owner merges.

## Goal
Energy ledger of the real pilot plant (PV DC → H₂ → FC AC) per static load point, every
number with its origin, gaps visible. Details: `CONTRACT.md` §1–§4.

## Restart progress
- [x] N0 archive tag `archive-2026-11`, branch, duplicates and `Differenz/` removed
- [x] N1 `AGENTS.md`, `START.md`, `CONTRACT.md`, `decisions/`
- [x] N2 values in `plant/<device>.toml` (16 files, 109 keys, equality proven by test);
      real gas, loader tests, formats, workbook kept; legacy removed
- [x] Correction: device models (`devices/`, `hydrogen/`, `conversions`, `constants`) and
      their tests restored; analyses, old balance, Monte Carlo, reports stay in the archive
- [ ] N3 accounts A/B/C built on the existing device models; a device is reworked only
      with a comparison test against the existing model
- [ ] N4 `cases/F1.toml` and case report, immediately with MISSING items
- [ ] N5 owner reviews the branch and merges

## Next step
Prepare N3: item list of accounts A and B for case F1, mapped to the existing
device models; list which inputs F1 needs from the owner.

## Open owner decisions
1. Remaining [V] items in `CONTRACT.md`: scope wording (§2), formula C (§4), status scheme (§8).
2. Value protection: the agent submits value changes only as proposals, the owner applies?

## Open plant questions (also under [open] in the device file)
- Filter pump (house grid): power and run time; registry has 0 W (`water.toml`)
- PV power F8: 12.74 kWp versus 12.78 kWp (`pv_array.toml`)
- PV inverter S6-GR1P6K: datasheet missing (`pv_inverter.toml`)
- H₂Core battery: 100 Ah/52 V versus 105 Ah/5 kWh/48 V (`fc_battery.toml`)
- Kaeser: input power, kWh meter, load hours; booster air demand at the operating point;
  manufacturer questions P-1 to P-3 (`booster.toml`)
- Solis DC channel reads 3–4 % above the counter (legacy finding), so diagnostic only
- Regatron fast logs: available? With or without the FC inverter on the bus?

## Already decided – do not reopen
No sun-driven control · PV surplus is not a loss · Kaeser in account B ·
H₂Core battery ≠ separate PV battery system · room infrastructure excluded ·
no central control (contained in devices) · AC8 dropped · losses never as a difference ·
missing value = no number · Regatron tools stay in `tools/`.
Source: `CONTRACT.md`, `decisions/`.
