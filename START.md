# START – current state (overwritten, never appended; at most 60 lines)
State: 2026-11-17 · branch `review/zwischenstand` · checkpoint; no merge into main.
## Goal
Energy ledger of the pilot plant (PV DC → H₂ → FC AC) per static load point; every number traced, gaps visible. Details: `CONTRACT.md` §1–§4.
## Restart progress
- [x] N0 archive tag `archive-2026-11`, branch, duplicates and `Differenz/` removed
- [x] N1 `AGENTS.md`, `START.md`, `CONTRACT.md`, `decisions/`
- [x] Agent workflow and documentation gates clarified; see `decisions/2026-11-13-agent-workflow-clarifications.md`.
- [x] N2 values in `plant/<device>.toml` (107 keys, owner-approved reference checked by test); real gas, loader tests, formats, workbook kept; legacy removed
- [x] Correction: device models (`devices/`, `hydrogen/`, `conversions`, `constants`) and their tests restored; analyses, old balance, Monte Carlo, reports stay in the archive
- [x] Architecture: `physics/`, `hydrogen/`, `devices/` (same names as `plant/`), `accounting/`, `loaders/`, `scenarios/`; no duplicate constants; tests named `test_<package>_<topic>.py`; `tests/test_structure.py` guards the layout
- [ ] N3 accounts A/B/C built on existing device models; rework only with a comparison test against the existing model.
- [ ] N4 `cases/F1.toml` and case report, immediately with MISSING items
- [ ] N5 owner reviews the branch and decides whether to merge
## Next step
The agreed Kaeser/HULC work block is complete; no immediate task remains in this block before independent work continues. This is a workflow checkpoint, not acceptance of a physically verified compression model. Select the next independent plant/model topic with the owner; do not reopen deferred questions automatically.
Workbook: canonical `plant/sources/Compressor_System_Specs_Master_v2.xlsx`, SHA-256 `07b082dbacf00dc6b9332d3d7ce0f262041003bdf3913cce0dacedad07a33145`; integration `38e04c1`, TOML/snapshot texts `d6fc860`. Older repository upload removed with owner approval; only one Compressor XLSX remains in the repository. Desktop copies are not maintained project sources.
Architecture `081df38`: dry FAD conversion in `devices/kaeser.py`; HULC interpolation, explicit module-addition assumption and hard guards in `devices/h2_compressor.py`; hypothetical formula only in `scenarios/kaeser.py`. Accounting import boundaries and Report booking guards enforced; legacy HULC energy path unchanged. Latest full code gates after approved review fixes: 436 passed, device scripts and both diff checks exit 0.
Review fixes: mutable point containers rejected; package-relative import checks include nested modules; linear scenario assumption explicit in notes. Two energy expectations independently derived with Fraction using rounded fixture nominal 616.126, owner-approved abs=1e-12/rel=0. Focused selection below: formerly 171 tests, now 182 passed; physical assumptions unchanged.
Focused command: `env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_devices_kaeser.py tests/test_scenarios_kaeser.py tests/test_accounting_ledger.py tests/test_physics_and_params.py tests/test_structure.py`.
Owner defers curve applicability, module addition, volume-basis compatibility and actual Kaeser consumption to the later overall-system assessment and better evidence, before any productive compression result is adopted. These are open review obligations, not blockers for independent work. Compression ledger energy stays MISSING; scenario remains UNVERIFIED and not bookable.
N4/F1 reports and unit grouping remain open; 9 EL is OWNER_DECISION, not site-verified.
Provisionality/deferral recorded in `4566906`, CONTRACT and `decisions/2026-11-17-{hulc-historical-air-ratio,kaeser-energy-scenario}.md`: 14.6 is an UNVERIFIED historical comparison only, never a runtime factor/default or accepted plant truth. Working assumptions remain revisable; historical tests and source pins establish traceability, not physical validity. Documentation structure check: 6 passed; both diff checks exit 0.
## Current limitations
- P14 is a bounded EL scenario; the A/B/C full-chain report is not implemented.
- Water pump energy is BACKLOG, not zero; independent RO results remain visible; accounting keeps water and filter energy blocked until connected.
- TOML is current plant/runtime truth; XLSX/documents are reviewable evidence and inputs.
- Storage: working-pressure key withdrawn; PS is only a limit; effective thermal mass open;
  TARA only; independent Route 2 PAUSED (DCT/Pt100 absent); static pVT and synthetic tests retained.
- Faraday mass remains computable; uncertainty is open pending sourced, owner-approved stack-current uncertainty. Production-minus-delivered is diagnostic, not a booked loss.
- EL supply/H₂ leakage open; zero line-loss assumption and FC A/B allocation not implemented.
- Extra PV inverters on another array: future BACKLOG only, no current capacity/scope change.
- Legacy guard scripts `tools/ci_guard.py` and `tools/make_readme_demo.py` are absent in this tree.
## Known failures
- None in the 2026-11-17 full wrapper; all five previously listed workbook tests passed after integration.

## Open owner decisions
1. Remaining [V] items: `CONTRACT.md` scope (§2), formula C (§4), status (§8); plant-value and uncertainty changes need approval.
2. Water I/O: separate measured feed/permeate; legacy `measured_water_L` means permeate; add pump runtime, leave energy MISSING until known.
3. Check whether 200 W includes controls before standby modelling; fallback open; `duty > 1` should warn and report unmet water.
4. Water evidence: WCF/spec-water uncertainty and status; measured-energy uncertainty `0.02` source. NaN H2 rejection is owner-confirmed; runtime NaN callers remain UNVERIFIED.

## Open plant questions (also under [open] in the device file)
- Filter pump (house grid): power, run time, exact Marte model and connection to BWT open (`water.toml`); determine power by nameplate or on-site measurement.
- PV: 28 modules and 12.74 kWp owner-decided; Solis station list reports 12.78 kWp; S6 0.971/0.977 DATASHEET, EU constant interim, no band; eta(P)/standby/MPPT open (`pv_inverter.toml`); DC cable loss and route length BACKLOG (`pv_dc_cable.toml`).
- PV generation modelling is an empty, non-executable placeholder: `decisions/2026-11-16-pv-generation-modelling-deferred.md`; module source review deferred.
- PV starts provisionally at inverter DC input; cable outside boundary, not zero. Revisit with reviewed data: `decisions/2026-11-16-pv-inverter-input-boundary.md`. AC sign/boundary and residual causes remain open.
- H₂Core battery: 100 Ah/52 V versus 105 Ah/5 kWh/48 V (`fc_battery.toml`)
- Kaeser/HULC: input power, load hours and P-1 to P-3 open. Source cleanup distinguishes transcriptions, independent checks and UNVERIFIED evidence; workbook review remains separate. Conditional Path A versus lower-bound Path B remains unresolved.
- Kaeser/HULC: original .10/24 brochure, photos/chats, installed identity and URL durability remain UNVERIFIED; agent-checked technical fields and P-3 manual cited; owner review pending.
- Workbook review: prior hash-change origin and missing Bovo/S28 revision remain open; current workbook identity is pinned above. D12 is recorded in `decisions/2026-11-05_restart.md`.
- HULC: max-flow and nine-EL comparisons are illustrative; actual drive pressure, counter definition, stroke-count plausibility and P-3 limits remain open before use.
- Deferred owner decisions: status of base-type data, representation/interpretation of zero uncertainty, FAD unit/schema and pressure references; snapshot prose design. Current values/statuses/units unchanged, not newly approved.
- HULC: model without air energy uses REJECTED eta=0.03; no-window ideal work uses fill integral despite constant-outlet docstring. Window throughput above computed window amount is silently reduced without a visible result note (measured-energy path can return warning=None); source/meaning and result impact require owner review. Legacy fixes deferred, not approved by scenario work.
- HULC review: base DLE 15/30 values match manufacturer sheets, H2 variant transfer and bar/barg remain UNVERIFIED; 5 Nm3/h is a maximum, not a measured operating point.
- `PVSystem` no longer reports reference-minus-DC as a loss. Solis 3–4% difference unverified; cause open.
- Regatron fast logs: available? With or without the FC inverter on the bus?

## Already decided – do not reopen
No sun-driven control · PV surplus is not a loss · Kaeser in account B · H₂Core battery ≠ separate PV battery · room infrastructure excluded · no central control · AC8 dropped · losses never as a difference · missing value = no number · Regatron tools stay in `tools/`.
