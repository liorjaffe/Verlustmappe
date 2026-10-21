# Water system in the balance (BWT bestaqua 14ROC COFFEE + Popular Filtros train)

Status: **DATASHEET** (energies modelled from datasheets, scaled by actual
H2 production) / one open **GUESS**. Spec workbook:
`Water_System_Specs_Master.xlsx` (library, EL 2.1 folder, 2026-10-21).
Sources: BWT EBA (imported), unit nameplate photos, EL 2.1 datasheet /
battery limits / owner's manual.

## What it is

The water chain feeding the EL 2.1 "H2O IN" port: BWT bestaqua 14ROC COFFEE
reverse-osmosis unit (s/n 187716/0073, June 2022) downstream of a Popular
Filtros central cartridge train (resin / activated carbon / 1 um / 5 um,
"marte" housing). The EL refills automatically via its H2O IN solenoid valve
(Battery limits sec. 7.1).

## Why it is in the RTE at all

It consumes electricity: the RO unit draws 200 W in operation and <3 W in
standby, and the standby is CONTINUOUS. Only the production energy scales
with the actual H2 production (part load); the standby is a time-based base
load. At the electrolyser's 7,566 full-load hours per year this is
27.7 kWh/yr: 5.0 kWh actual pumping (0.4 L/h demand needs the 120 L/h RO
for only 0.33% of each hour) plus 22.7 kWh always-on standby. Against the
electrolyser's 18,158 kWh/yr this is ~0.15% - small but real, and it belongs
on the charge side of the RTE because the electrolyser cannot run without it.

## Water scope (no energy, part of the plant balance)

At the factory Water Conversion Factor of ~50%, 0.4 L/h permeate requires
0.8 L/h raw feed; 0.4 L/h goes to drain as concentrate. Annual: 3,026 L
permeate, 6,053 L feed, 3,026 L concentrate.

## Stoichiometric consistency

The water demand is the STOICHIOMETRIC MINIMUM scaled by the actual
production: `water.spec_water_L_per_NL = 0.0008037 L/NL`
(9.0 g water per g H2, same ratio as `hydrogen/route4_water.py`; the
datasheet "~400 mL/h" is this value rounded to 0.4 L/h at 500 NL/h).
Purges, bleeds and off-spec water ADD on top. When no H2 production is
given, the model falls back loudly to nominal 0.4 L/h x duration.

## Registry entries (`water.*`)

| key | value | status |
|---|---|---|
| water.ro_perm_Lh | 120 L/h | DATASHEET |
| water.ro_power_op_W | 200 W | DATASHEET |
| water.ro_power_standby_W | 3 W | DATASHEET (<3) |
| water.wcf | 0.5 | DATASHEET |
| water.spec_water_L_per_NL | 0.0008037 L/NL | DATASHEET (rounded), DERIVED exact |
| water.spec_water_L_per_NL_stoich | 0.0008037 L/NL | DERIVED (cross-check) |
| water.filter_train_power_W | 0 W | GUESS (open item) |

## Model and its replacement

`devices/water_system.py::WaterSystem.account(duration_h, ...)`:
water demand priority: measured water > caller override > H2-production-
scaled > nominal fallback (with warning). Energy:
E = t_prod x 200 W + t_on x 3 W, t_prod = water_demand / 120 L/h, t_on =
duration (standby always on; set `ro_standby_always_on=False` if the RO is
switched off with the EL). `measured_kWh` (plug meter) and
`measured_water_L` (BWT app inlet/outlet litre counters or a water meter)
flip the bars to MEASURED and replace the model; the model stays visible as
`energy_kWh_model`.

## Where it sits in the loss map

`balance/d_loss_map.py` books two bars after the dryer:
- "Water system (RO unit)" - MEASURED or DATASHEET model
- "Water filter train (resin/carbon/micron)" - GUESS status (0 W until the
  pump question is resolved)

Both flow into `storage_chain_rte(..., E_water_kWh=...)` and into the fair
closed-cycle denominator. The `e_rte.py` breakdown carries WATER.

## Open items

1. Meter the RO unit (plug meter) -> MEASURED bar; read BWT app water
   counters for `measured_water_L`.
2. Verify whether the photographed pump (bomba panel) is in the water path
   to the RO; if yes, record its nameplate power in
   `water.filter_train_power_W`.
3. RO permeate conductivity: the BWT RO does not by itself guarantee the
   EL's <5 uS/cm input limit at all times; verify on site.
