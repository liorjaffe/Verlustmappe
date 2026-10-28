# Hand reference: constants (P10, item 1)

Derived independently of the implementation (hand README rules 1-3). Reproduce with
`python3 tests/reference/hand/p10_hand_calc.py` (stdlib only, no `verlustmappe` import).

## Normal volume basis (project decision, workbook-only)
0 degC, 1.01325 bar abs, dry (DIN 1343). All Nm3 / NL use this basis unless a row says FAD
(Kaeser: 1 bar abs, 20 degC) or ANR (Rotex: 1 bar, 20 degC, 65 % RH).
Source: workbook `Compressor_System_Specs_Master_v2.xlsx` (SHA-256
`0aa9f8ed0618d9bfd61123055674418969e0d7479d63b962afb18944cfd942ae`), Master sheet, row
"Normal volume basis", key `sys.volume_basis`, status "Project decision", layer `-`
(workbook-only, no registry key: the entry carries text, not a number, D15), source cells
`[S27] [S23] [S15]`. UNVERIFIED here: the S27 and S23 entries (only S15 appears in SOURCES.md).

## Values
| Quantity | Hand value | Derivation |
|---|---|---|
| R | 8.314462618 J/(mol K) | k_B * N_A = 1.380649e-23 * 6.02214076e23 (CODATA 2018, exact) |
| F | 96485.33212 C/mol | e * N_A = 1.602176634e-19 * 6.02214076e23 (exact) |
| V_mol(NL) | 22.41397 L/mol | R * 273.15 / 101325 Pa * 1000 |
| rho_H2,NL | 8.99439e-5 kg/NL | M_H2 / V_mol = 2.016e-3 / 22.41397 |
| LHV | 33.32222 kWh/kg | 119.96 MJ/kg / 3.6 |
| LHV per NL | 2.99713 Wh/NL | 33.32222 * 8.99439e-5 * 1000 |
| J per kWh | 3.6e6 | 1000 W * 3600 s |
| Pa per bar | 1e5 | definition |

## Inputs taken over, not derived here
M_H2 = 2.016e-3 kg/mol (2 x 1.008, IUPAC 2021 standard atomic weight) and LHV 119.96 MJ/kg
(IEA, NIST) are the provenances already cited in `constants.py`; no new source is introduced.

## Known differences to the rounded values in `constants.py` (information, not a defect)
F: 96485.332 vs 96485.33212 (relative 1.3e-9). V_mol: 22.414 vs 22.41397 (relative 1.4e-6).
Comparison tolerances for the port are set by the P11 tests, not here.
