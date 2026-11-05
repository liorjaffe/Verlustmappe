# CONTRACT – what applies

The single place for "what applies". **Rewrite on every change, never append.**
Reasons live in `decisions/`, never here. State: 2026-11-05 (restart).

**[E]** decided by the owner – applies. **[V]** proposal – applies only after an owner
decision; until then treat it as an open question, not as a rule.
`(Dnn)` names the old decision a rule was taken from (tag `archive-2026-11`); it does not
need to be read.

## 1 Goal [E]

Show for the real pilot plant where every kWh goes. For each chosen static load point, one
report: the energy path from PV DC to the AC output of the FC inverter with every loss and
its cause, next to the energy demand of the auxiliary consumers. Every number carries its
origin. Missing values are shown as missing. No research into cell or stack details:
market-standard devices may be black boxes with documented inputs and outputs.

## 2 Scope

- [E] Only devices with a **direct influence on production**. Room and building
  infrastructure is excluded: ventilation, gas detection, heating, frost protection,
  room equipment.
- [E] There is no central plant control (PLC, control computer). Controls are built into
  the devices and are not devices of their own. Their consumption belongs to the device;
  where a device reports it separately (FC control, §4), it is booked there.
- [V] Testable wording: a device is in scope if it converts energy to produce, convert,
  treat, move or store a process medium (chain electricity, H₂, process water, compressed
  air).
- [E] The only PV source is F8 ("F8_Fachada Leste", two Solis inverters). The Sept 2026 PV
  dataset (`pv_merged.csv`) is excluded and never evidence (D33).
- [E] No sun-driven production. PV surplus is not part of the calculation and is not a loss.
- [E] The Regatron is a test bench, not a plant device. It is a measurement source (layer 3).
- [E] The comparison with the legacy state (formerly AC8) is dropped.

## 3 Layers [E]

| Layer | Input | Statement |
|---|---|---|
| 1 static | given load points (percentages are examples only) | modelled |
| 2 dynamic | **given load profile**; PV only as availability, no sun-driven control | modelled |
| 3 validated | measurement windows | "validated" only for those windows, within uncertainty |

Accounts A, B, C are defined identically in all layers. No validation is claimed before
layer 3 (D34).

## 4 Accounts

- **A – series path** [E]: PV DC (module/string output) → DC cable →
  PV inverter → AC → EL → dryer → booster → storage → FC (with H₂Core battery and DC bus) →
  FC inverter → AC out. In reality the EL is supplied from the house grid; the chain is an
  **allocation** (a slice of PV is assigned to the path), not a claim of physical direct
  supply.
- **B – auxiliary consumers** [E]: devices actually supplied from the house grid or the
  separate PV battery system, each with its supplier and phase. The separate PV battery
  system is only an external supplier; its internals are not modelled. The Kaeser
  (compression) is in B.
- [E] A/B boundary: A contains energy that flows through the series conversion. B contains
  every other electrical consumption, including standby of series-path devices (EL, PV
  inverter, FC inverter) and dryer electricity.
- [E] FC control is netted in the series path per D22:
  E_out_net = (E_fc_terminal − E_ctrl) · η_inv. Assumption: drawn from the DC bus before
  the inverter; measurement point open. Booked once.
- **C – system efficiency** [V name and formula; E reporting rule]:
  η_sys = E_AC,out / (E_PV,DC,share + E_B,external + ΔS_correction).
  [E] Reported only once compression and battery have a status. Until then A and B are
  shown side by side with their own totals, **without a summed total**; A never appears
  alone.
- [E] The H₂Core battery belongs to the FC system. It is not the separate PV battery system
  for auxiliary consumers. Battery discharge must not appear as reconversion from H₂.

## 5 Case (layer 1)

- [E] A case contains only inputs, assumptions and justifications. Everything computed
  comes from the model.
- [E] EL anchor: AC power, stack current, operating time, standby power, standby time.
  None of them is derived from another without a documented relation.
- [E] A chosen Solis time window shows only that enough PV **energy** was available. It
  does not prove simultaneous power or real supply. [E] The window selection rule is
  recorded beforehand.
- [E] The PV total operating point comes from the window. Inverter and DC cable are
  computed at total power or total current; the loss is allocated pro rata to the slice
  (a convention, named as such). No inverse function needed.
- [E] Every phase duration has a justification: operating requirement, measured
  observation or deliberate convention.
- [E] The FC operating point is set; the FC duration follows from the mole balance
  (otherwise the case is overdetermined).
- [E] Cycle closure is a declared assumption in mol, not a measurement. Intermediate
  storage (dryer hold-up, buffer, tank) is lumped as an assumption.
- [E] Battery: share or ΔS is declared. Net zero is not loss-free; throughput losses are
  computed separately.
- [E] State quantities of an operating point are inputs: tank pressure, gas temperature,
  battery SoC, connected storage volume (800 L isolated, otherwise 1600 L).

## 6 Balance rules

- [E] Losses come from their own physics or from measurement, **never as a difference**
  "input minus output".
- [E] Consumption is not a loss. A storage change is not a loss. An unexplained residual is
  not a loss.
- [E] Mole balance first: n_start + n_EL = n_end + n_FC + n_vent + n_leak + n_purge.
  Then energy: E_in = E_out + L + ΔS, with ΔS = S_end − S_start.
- [E] A residual R is only a diagnostic: where the same quantity is determined twice
  independently. In a model case only as EL consistency (AC versus V(I,T)·I plus rectifier
  loss).
- [E] Heat is an output in a full energy balance and part of the conversion loss in a
  useful-energy account – never both.
- [E] A consumption already contained in a higher-level reading is not added again
  (contained-in).
- [E] Compression is consumption (Kaeser electricity) and never part of the stored stock.
- [E] Ideal fill work may only appear as a named ideal-gas quantity, never as electrical
  compression energy (D35).
- [E] Kaeser (D14): supplies only the HULC and the four Rotex. Variable share by air
  quantity (HULC / Rotex 1–4 / other); READY standby and network leakage as separate
  items; leakage belongs to the distribution network, not to the HULC. Standby by air draw,
  otherwise split equally (assumption). Kaeser input power open; 6.2 kW is a dealer value.
- [E] HULC air demand (D13): manufacturer curve as a function of H₂ flow at the plant
  operating point; operating point open. 14.6 Nm³/Nm³ applies only at maximum flow and is
  not a bound. Geometry (4.59–6.30) is a physical lower bound.
- [E] FC inverter, discharge path (D3b): PV-AC datasheet values do not apply. Never
  MEASURED until measured.

## 7 Missing values and validity [E]

- A missing value gives no number: not zero, not omitted, no default. Dependent totals,
  balances and figures stay open as well. Independent results stay visible (D35).
- Shares only over quantified items and with a named denominator. No "largest loss" and no
  complete Sankey while items are missing (D35).
- Computed path quantities (energy, power, mass, amount, flow, absolute pressure, absolute
  temperature) must not be negative. Changes and differences are signed. Signs of raw
  measurement channels are not an error (D25, D31).
- Non-monotonic time is invalid (D25).
- No limiting (clip, min, max) of physical quantities without a source and a visible note
  in the result.
- EL: Faraday efficiency finite in [0, 1]; cell count finite, positive, integer. Violations
  block the H₂ results; non-numeric, boolean or non-finite values are data errors and raise
  an exception (D36).
- A missing mandatory channel (layer 3) invalidates the affected route, not automatically
  everything (D31).

## 8 Status

- [V] New scheme: `status` = MEASURED > DATASHEET > SECONDARY > ASSUMED > MISSING; the
  weakest input determines the result. `origin` = measured | computed.
  `u_kind` = none | band | envelope. u = 0 means "not assessed" unless stated otherwise.
- Until decided, the status in `plant/<device>.toml` applies (1:1 from the old registry).
- [E] Most values still lack a page reference and verbatim quote; that is open work, not a
  confirmation of the values.
- [E] The `comp.*` keys (wrong device, Maximator DLE 30-2) must never be used in new code
  (D11).

## 9 Measurement data (layer 3) [E]

- Integration: trapezoid within valid segments; gap if dt > max(3 × nominal interval,
  30 s); the covered fraction is reported (D24).
- Nominal sampling interval only from a demonstrated export grid of the source; F8: 300 s.
  Timestamps are not snapped to a grid (D32).
- Measured cycle closure: CLOSED if |Δn| ≤ 5 % · n_ref and u(Δn) ≤ 5 % · n_ref,
  n_ref = max(n_in, n_out); otherwise NOT VERIFIABLE. The DCT 541 pressure sensor serves
  only this verdict, not calibration; until the repeatability test, measured closure is
  NOT VERIFIABLE (D20, D8).
- Tank pressure and gas temperature are simulated states until the retrofit (D8).
- First calibration candidate: FC terminal characteristic from Regatron sweeps (D4). The
  Regatron current is bus/load side, never FC output.

## 10 Publication [E]

Every number appears with status, layer and assumptions. A computed value must never look
like a measured one. "Validated" only from layer 3 and only for the checked windows.
