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

Open: the band is owner-stated and not yet chosen; the current
`plant/fc_inverter.toml` entry (status DERIVED, +/-0.02 without source) does
not yet conform and is corrected in the FC TOML rewrite. The replacing
measurement is planned via the inverter LCD energy counters (Inverter2,
Master row 79); counter resolution and grid-input effects must be checked
first.
