# Hand reference: ideal isothermal compression work (P10, item 2)

Derived independently of the implementation (hand README rules 1-3). Reproduce with
`python3 tests/reference/hand/p10_hand_calc.py` (stdlib only). Two DIFFERENT definitions exist
in the code; each is stated and checked on its own. They are not interchangeable.

## (A) Closed system, ideal gas: W = n R T ln(p2/p1)
Code: `conversions.isothermal_work_kWh`. Textbook form (compress a fixed amount once).
Active consumers: NONE in the chain. `devices/booster.py` imports it but never calls it; only
`tests/test_01` uses it. It carries no result today.
Hand value: 1 mol, 1 -> 10 bar, 293.15 K: R T ln 10 = 5612.29 J (test_01 pins 5612.0).

## (B) Fill integral, suction ps = p1
Code: `hydrogen/temperature_model.isothermal_work_mol_integral` (called from `devices/booster.py`).
Filling a vessel from p1 to p2: only (p2 - p1) V / (R T) mol are delivered, each compressed
from ps to the current vessel pressure p:

    W = V/(RT) * RT * integral_{p1}^{p2} ln(p/ps) dp,   n = (p2 - p1) V/(RT)
    w/RT = W/(n RT) = [p2 ln(p2/p1) - (p2 - p1)] / (p2 - p1) = p2/(p2 - p1) * ln(p2/p1) - 1   (ps = p1)

Check at p2 = 2 p1: 2 ln 2 - 1 = 0.386294. The closed form was also confirmed by midpoint
integration of (1/(p2-p1)) * integral ln(p/p1) dp (agreement to 6 digits).
This is NOT ln(p2/p1) - (1 - p1/p2) (that form divides by p2 instead of p2 - p1).

## Values (pressures ABSOLUTE; B per mol delivered, T = 293.15 K; kWh per Nm3 uses
## 1000 NL / 22.41397 L/mol = 44.6143 mol at the 0 degC normal basis, see constants.md)
| p1 -> p2 [bar abs] | A/RT | B/RT | B [J/mol] | B [kWh/Nm3] | Origin |
|---|---|---|---|---|---|
| 1 -> 2 | 0.693147 | 0.386294 | 941.5 | 0.01167 | hand check, 2:1 |
| 40 -> 200 | 1.609438 | 1.011797 | 2466.1 | 0.03056 | test_02 Bovo anchor |
| 10 -> 200 | 2.995732 | 2.153402 | 5248.7 | 0.06505 | information: A vs B gap |
| 36.01325 -> 141.01325 | 1.364967 | 0.833128 | 2030.7 | 0.02517 | 35 -> 140 barg, HULC stage 1 (D12) |
| 36.01325 -> 301.01325 | 2.123267 | 1.411817 | 3441.1 | 0.04265 | 35 -> 300 barg, project case (D12) |

Bovo point (test_02): 33.22 Nm3 = 1482.11 mol; B for 40 -> 200 bar abs at 293.15 K:
1.01530 kWh (test_02 pins 0.9 < W < 1.15). Note the mixed basis, which is legitimate but must
not be mistaken for a contradiction: the amount is on the 0 degC normal basis (22.41397 L/mol),
the work is evaluated at gas temperature 293.15 K.
The pairs from D12 are gauge pressures in the decision text; here they are converted with
+1.01325 bar, as `booster.account()` does. They are fill pairs with ps = p1; a real stage
compresses against the suction of the stage, which is a modelling choice of P11/P12, not of
this reference.

## Not a reference value
The "3.0 kWh for 33.22 Nm3, 10 -> 200 bar" anchor of the deleted `comp.overall_efficiency`
comment is not used (C11: unreliable). For orientation only: A at 293.15 K gives 3.006 kWh,
B gives 2.16 kWh for that point; the two definitions differ by about 28 %.
