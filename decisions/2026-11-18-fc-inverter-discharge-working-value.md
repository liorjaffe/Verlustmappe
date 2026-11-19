# 2026-11-18 - FC inverter discharge working value (D3b)

The owner approved the precise `CONTRACT.md` §6 wording for D3b. `inv_fc.eta`
is the Solis S5-EO1P5K-48 discharge-path efficiency: DC energy from the 48 V
FC/battery bus to the 230 V island AC output. The manufacturer publishes no
value for this path; the published 96.6% (datasheet) and 93-95% (manual) are
PV-AC peak figures.

Until measured, the 0.94 working value (midpoint of the manual PV-AC range,
earlier owner decision recorded in the Inverter2 workbook, sheet Master
row 44) may be used with status ASSUMED. It is not evidence, never MEASURED
or DATASHEET, and never calibrated; per §8 every result that uses it is at
most ASSUMED. Owner reasoning, not measured (Inverter2 D44): the discharge path
steps up from 40-60 V, so the value is more likely optimistic than
pessimistic, and peak efficiency is not operating-point efficiency.

`plant/fc_inverter.toml` conforms since the FC TOML rewrite of 2026-11-19
(GUESS, u = 0.0, limit keys `inv_fc.eta_envelope_lower` / `_upper`).

## Band (owner decision 2026-11-19, provisional)

The owner chose option (a) provisionally. Each limit is recorded on its own
with its own basis, so that new information can replace one limit without
reopening the other.

| Item | Value | Basis |
|---|---|---|
| Lower limit | 0.914 | No source. Owner convention: mirrored about the working value (0.94 - 0.026). |
| Working value | 0.94 | Midpoint of the manual PV-AC range 93-95%; owner decision (Inverter2, Master!D44). |
| Upper limit | 0.966 | Solis datasheet PV-AC peak; carried over to the discharge path by the owner assumption in Inverter2, Master!D44 that the 40-60 V step-up path is not better than the PV-AC peak. |

- Kind: envelope (owner construction). It is not evidence and does not
  define a distribution. Implied DC-AC loss: 3.4-8.6% of the DC energy
  (0.94 gives 6%).
- All three numbers come from the PV-AC path or are constructed from PV-AC
  figures. None of them is evidence for the discharge path.
- Scope: the energy-weighted mean DC-to-AC conversion efficiency over a
  balance period, excluding standby (`inv_fc.standby_W` stays a separate
  term). Part load and low load are not covered; there the real value may
  be below 0.914. The band is not tied to a kW range: inverter load follows
  the AC load, not the FC output.
- Status: ASSUMED per CONTRACT §6, recorded as GUESS in the active D26
  vocabulary (owner-approved §6 wording 2026-11-19, as for
  `stor.T_assumed_C`). The mapping changes only the label and relaxes no
  rule. By weakest-wins every result using `inv_fc.eta` is at most GUESS.
- TOML encoding (owner 2026-11-19): two separate limit keys, each with its
  own source text, next to `inv_fc.eta`. No distribution is adopted, so
  `inv_fc.eta` gets `uncertainty = 0.0` (NOT ASSESSED, as in
  decisions/2026-11-13_pv-inverter-efficiency.md) and the old
  `uncertainty = 0.02` is retired. Key names (rewrite 2026-11-19): `inv_fc.eta_envelope_lower`, `inv_fc.eta_envelope_upper`; subject to the later key renaming.
  The limits are not propagated automatically; using them (e.g. a lower and
  upper limit run) needs its own approved step. The absolute limits above
  stay the reference.

### What replaces it

- Measurement via the inverter LCD energy counters (Inverter2, Master rows 79
  and 85): eta = delta LoadE / delta BattDisChgE, with delta PV E = 0 and
  delta GridGetE = 0 in the window. First check the counter resolution (not
  documented; 0.1 kWh is only a hypothesis). The worst-case error is
  r/E_DC + r/E_AC: at r = 0.1 kWh about +/-1.9 points at 10 kWh, +/-1.0 at
  20 kWh, below +/-0.5 from about 40 kWh. Target at least 20 kWh per load
  point, preferably two or three load points. Without a cross-check against
  an independent measurement (Regatron or reference V/I) the result is at
  most secondary evidence, not MEASURED.
- A manufacturer statement on the discharge path replaces the upper limit
  and, if it gives a range, the lower limit.

### Revision log

| Date | Change | By |
|---|---|---|
| 2026-11-19 | Option (a) chosen provisionally: [0.914; 0.966], working value 0.94 | Owner |
| 2026-11-19 | Encoding: two limit keys, no distribution, `inv_fc.eta` u = 0.0 | Owner |
| 2026-11-19 | CONTRACT §6: ASSUMED recorded as GUESS (D26) while §8 is not in force; no rule relaxed | Owner |
| 2026-11-19 | Applied in `plant/fc_inverter.toml` (FC TOML rewrite) | Owner-approved list |
