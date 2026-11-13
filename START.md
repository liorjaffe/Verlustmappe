# START – current state (overwritten, never appended; at most 60 lines)

State: 2026-11-13 · branch `review/zwischenstand-2026-11-13` · checkpoint; no merge into main.

## Goal
Energy ledger of the pilot plant (PV DC → H₂ → FC AC) per static load point; every number traced, gaps visible. Details: `CONTRACT.md` §1–§4.

## Restart progress
- [x] N0 archive tag `archive-2026-11`, branch, duplicates and `Differenz/` removed
- [x] N1 `AGENTS.md`, `START.md`, `CONTRACT.md`, `decisions/`
- [x] N2 values in `plant/<device>.toml` (109 keys, owner-approved reference checked by test);
      real gas, loader tests, formats, workbook kept; legacy removed
- [x] Correction: device models (`devices/`, `hydrogen/`, `conversions`, `constants`) and
      their tests restored; analyses, old balance, Monte Carlo, reports stay in the archive
- [x] Architecture: `physics/`, `hydrogen/`, `devices/` (same names as `plant/`), `accounting/`,
      `loaders/`; no duplicate constants; tests named `test_<package>_<topic>.py`;
      `tests/test_structure.py` guards the layout
- [ ] N3 accounts A/B/C built on the existing device models; a device is reworked only
      with a comparison test against the existing model
- [ ] N4 `cases/F1.toml` and case report, immediately with MISSING items
- [ ] N5 owner reviews the branch and decides whether to merge

## Next step
Design the F1 case report around the PV-start path, EL-start path and auxiliary energy
perspectives in `CONTRACT.md` §4. Then scope the connections to existing device models
for accounts A and B; leave missing inputs visible. Do not delete or replace models,
data or sources as part of this step.

## Current limitations
- P14 is a bounded EL scenario; the A/B/C full-chain report is not implemented.
- Water pump energy is BACKLOG, not zero; independent RO results remain visible.
  The accounting inventory keeps water and filter energy blocked until connected.
- TOML is current plant/runtime truth; XLSX/documents are reviewable evidence and inputs.
- Storage: working-pressure key withdrawn; PS is only a limit; effective thermal mass open;
  TARA only; Pt100 path suspended, plan BACKLOG; static 20 degC, +/-10 K analysis opt-in only.
- Faraday mass remains computable; its uncertainty is open pending sourced, owner-approved
  stack-current uncertainty. Production-minus-delivered is diagnostic, not a booked loss.
- EL supply/H₂ leakage open; zero line-loss assumption and FC A/B allocation not implemented.
- Some plant values are also embedded in code; actual computation paths need checking.
- Sensitivity/reference/status checks: 34 pass; device scripts ALL PASS; pytest 251 pass, 5 known workbook failures.

## Open owner decisions
1. Remaining [V] items in `CONTRACT.md`: scope wording (§2), formula C (§4), status scheme (§8).
2. Plant-value changes and uncertainty wiring require explicit owner approval.

## Open plant questions (also under [open] in the device file)
- Filter pump (house grid): power, run time, exact Marte model and connection to BWT
  remain open (`water.toml`); determine power by nameplate or on-site measurement.
- PV: F8 12.74 versus 12.78 kWp (`pv_array.toml`); S6-GR1P6K datasheet missing (`pv_inverter.toml`)
- H₂Core battery: 100 Ah/52 V versus 105 Ah/5 kWh/48 V (`fc_battery.toml`)
- Kaeser: input power, kWh meter, load hours; booster air demand at the operating point;
  manufacturer questions P-1 to P-3 (`booster.toml`)
- Solis DC channel reads 3–4 % above the counter (legacy finding), so diagnostic only
- Regatron fast logs: available? With or without the FC inverter on the bus?

## Already decided – do not reopen
No sun-driven control · PV surplus is not a loss · Kaeser in account B · H₂Core battery ≠
separate PV battery · room infrastructure excluded · no central control · AC8 dropped ·
losses never as a difference · missing value = no number · Regatron tools stay in `tools/`.
Agent workflow: `AGENTS.md`. Sources: `CONTRACT.md`, `decisions/`.
