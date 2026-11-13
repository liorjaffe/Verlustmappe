# 2026-11-13 - Owner PV inverter evidence and interim efficiency decision

## Scope and evidence

Reconstruct `plant/pv_inverter.toml` from the owner-assigned workbook first:
`plant/sources/Inverter1_PV_Solis_S6-GR1P6K_Specs_Master.xlsx`.
All four sheets reviewed; SHA-256
`8172f7f81ab22cb3f61edea6ab5cc51fb3003b673ba3a98fda7fcf0305853f78`.
The filename's numbering is not an identifier or evidence of present device order.
Do not seed parameters from the old TOML or the F8 system workbook.

Master rows 3-7 identify two F8 PV-side S6-GR1P6K units. Unit B
`1802060225250009` is supported by a cited nameplate; unit A
`1802060225250007` is platform-only. The S5-EO1P5K-48 belongs to the
separate FC-side device.

## Released values and modelling decision

- `inv_pv.eta_euro`: **0.980 PRELIM -> 0.971 DATASHEET**.
  Master row 30 / Sources row 3: Solis S6-GR1P(2.5-6)K datasheet,
  GBR V1.5 202507, page 2, Efficiency table, 6K column, quote
  **"EU efficiency 97.1%"**.
- `inv_pv.eta_peak`: **0.985 PRELIM -> 0.977 DATASHEET**.
  Master row 29 / Sources row 3, same page/column, quote
  **"Max. efficiency 97.7%"**. Peak reference only, not energy accounting.
- Transferability: manufacturer specifications for each S6-GR1P6K unit,
  not measured F8 efficiency or combined two-unit ratings.
- Owner decision, 2026-11-13: use **0.971 as an interim constant** in the
  static model while eta(P) remains BACKLOG (Master rows 31, 47).
  The anchor is DATASHEET; its constant-use modelling is DERIVED and
  explicitly interim, not a measured or validated operating-point curve.
- Replacement path: appropriately bounded F8 DC/AC measurement or a sourced
  F8-applicable efficiency curve. The legacy-array figures documented in
  `src/verlustmappe/devices/pv_inverter.py` are not F8 evidence.
- Low-load risk: constant EU efficiency may overestimate actual low-load
  efficiency and underestimate conversion losses. Direction and magnitude
  are not verified for F8. Neither sample extremes nor the unverified
  station-chart analysis prove a "mostly 2-5.5 kW" load distribution.

## No uncertainty band

The owner withdraws the proposed band and band registry key (corrected Rev 3).
EU and maximum efficiency are different metrics, not manufacturer tolerance
limits. A constructed 0.968-0.974 band would have midpoint 0.971; 0.974 is
the midpoint of the separate 0.971-0.977 anchor span. Neither is evidence
of guaranteed part-load coverage.

`ASSUMED` is not supported by the active D26 status vocabulary.
A numeric `uncertainty = 0.003` would not represent an absolute +/-0.3
percentage-point band: project uncertainties are relative, and interpreting
a band as standard uncertainty would require an approved distribution.
No band or distribution is adopted. Both anchors have `uncertainty = 0.0`,
meaning NOT ASSESSED, not exact or zero error. No automatic propagation.

## Other explicitly approved PV corrections

- Remove the two invalid S5-only efficiency entries from the PV namespace;
  no runtime readers were found. Do not alter FC-side data.
- Remove the unsupported separate MPPT efficiency point value; keep its
  parameter missing/BACKLOG, without an extra multiplicative efficiency.
- Master row 35 / Sources row 3: page 2, quote
  **"Self-consumption (night) <1 W"**, per unit, bound not exact.
  Remove the unsupported 5 W point estimate. Exact standby power/energy
  remains missing/BACKLOG; device output must not report zero standby.
  Account B applies; the workbook's supply interpretation is not independently
  established by the quoted power bound.
- Master row 12 supplies 120 V start-up voltage only. Startup energy remains
  open (rows 36, 50); no self-sufficient startup-energy model is inferred.
- Close D6 as a missing workbook citation, not as independent certification
  of the original PDF. Preserve the unrelated historical portal-cadence
  source block without using it for device parameters.

Only affected `inv_pv.*` reference entries are updated; no full regeneration,
no tolerance changes, and no foreign reference changes. Key count:
109 - 2 = **107**. Test changes have their own commit.
No other device or workbook changes are authorized here.

## UNVERIFIED

Original manufacturer PDFs, original nameplate image and API responses were
not independently inspected; provenance is the reviewed XLSX. External
Rev-D/M0 statements and the proposed daily-chart statistics are not verified
and are not acceptance evidence. Existing legacy measured-difference loss
booking and old PV-array design-limit checks remain out of scope.
