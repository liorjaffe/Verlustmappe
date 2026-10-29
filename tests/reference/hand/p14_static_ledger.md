# P14 - Independent hand reference: bounded static EL case

Owner approval: coordination chat, 2026-10-29. Reference-only writes and local
commits approved; post-commit owner comparison remains required.
References: SPEC AC1/AC7; D26/D34/D35; [approved P14 contract](../../../tasks/P14_static_ledger.md).
Reproduce: `python3 tests/reference/hand/p14_hand_calc.py` (stdlib only).

## 1. Purpose and limits

Independently derive EL operating AC energy, EL standby AC energy, produced
hydrogen amount, hydrogen mass and hydrogen LHV transport energy.

This is not a complete storage chain, closed energy balance, measured plant
performance, RTE, or AC1/AC8 acceptance. LHV energy is transport, not an additional
loss. No conversion loss is obtained by input-minus-output subtraction.
No production/legacy imports or outputs may generate these expectations.

## 2. Boundaries and synthetic inputs

Powers refer to the EL AC input boundary; current refers to the distinct DC stack.

| Input | Approved value | Evidence |
|---|---|---|
| el_ac_input_power_W | 2100 W | GUESS |
| stack_current_A | 8 A | GUESS |
| operating_time_s | 2700 s | GUESS |
| el_ac_standby_power_W | 20 W | GUESS |
| standby_time_s | 1800 s | GUESS |

These are synthetic reference assumptions, not operating defaults or verified
device conditions. Input uncertainty is unassessed; no band is invented.
Power/current are constant during their respective periods; operating and standby
periods do not overlap. Cell count and Faradaic efficiency are constant.
Start-up, purge, dryer, compression and storage effects are not quantified.

2100 / (120 * 2.0) = 8.75 A, not 8 A: the registry's consistency calculation is
not the current source. Do not infer stack current from AC power, form a stack
voltage from AC power and DC current, or infer their conversion loss.

## 3. Authorized EL assumptions

| Parameter | Value | Evidence | Existing uncertainty field |
|---|---|---|---|
| el.n_cells | 120 | GUESS | 0.05 |
| el.faradaic_efficiency | 0.98 | GUESS | 0.03 |

The owner's verbatim authorization in the P14 task applies unchanged.
These are declared assumptions, not confirmed facts. Existing positive uncertainty
fields are classified `assessed` but have no documented band basis; they are not
verified uncertainties. No output uncertainty propagation is performed.

Enapter cell-count confirmation and Faradaic-efficiency validation via stack
current plus an independent hydrogen basis remain open.

## 4. Independent constant basis

Use the existing [hand-constant derivations](constants.md), not model readbacks.

| Quantity | Reference value | Basis |
|---|---|---|
| F | 96485.33212 C/mol | Rounded CODATA display of e * N_A |
| M_H2 | 0.002016 kg/mol | Conventional 2 * 1.008; existing IUPAC 2021 source hint |
| LHV | 119.96 / 3.6 kWh/kg | Existing 119.96 MJ/kg basis, IEA/NIST source hints |
| J per kWh | 3600000 | 1000 * 3600 |
| Electrons per H2 molecule | 2 | Faraday reaction stoichiometry |

Exact SI product:
1.602176634e-19 * 6.02214076e23 = 96485.3321233100184 C/mol.
The selected display 96485.33212 is rounded, not an exact decimal representation.
Do not substitute NIST species molecular weight 2.01588 or a direct unrounded
enthalpy-to-LHV conversion. The approved path rounds to 119.96 MJ/kg, then converts.

Existing constant-source details remain under the SOURCES migration backlog,
not a new P14 blocker. No missing citation details or historical provenance are
invented; the migration is not claimed complete.

## 5. Hand calculations

For constant power and constant stack current:

- Operating energy = 2100 * 2700 / 3600000 = **1.575 kWh**.
- Standby energy = 20 * 1800 / 3600000 = **0.010 kWh**.
- H2 amount = 0.98 * 120 * 8 * 2700 / (2 * 96485.33212)
  = **13.1634516054770 mol**.
- H2 mass = unrounded amount * 0.002016 = **0.0265375184366417 kg**.
- H2 LHV transport = unrounded mass * (119.96 / 3.6)
  = **0.884289086572095 kWh**.

Use unrounded intermediate values, never displayed numbers as subsequent inputs.
This is not a time-variable-current integration model. Operating and standby
energy belong to the electrical input side; do not double-count children and totals.

## 6. Numerical comparison rules

For positive references: abs(actual - reference) <= rtol * abs(reference).

| Output | Relative tolerance |
|---|---|
| Operating AC energy | 1e-12 |
| Standby AC energy | 1e-12 |
| H2 amount | 2e-9 |
| H2 mass | 2e-9 |
| H2 LHV transport | 7e-6 |

These are comparison tolerances for known constant rounding plus numerical
execution, not physical uncertainties. They are tied to the current rounded
code constants F = 96485.332 and LHV = 33.322.

Both are rounded downward relative to the reference: the smaller F denominator
increases amount/mass by about 1.2437e-9 relatively. The smaller LHV factor
dominates the combined transport difference, about -6.6676e-6.
The 7e-6 threshold has about 5% headroom; reassess the rounding basis if constants
change. No automatic widening or change to AC8 tolerances is permitted.

For direct-product zero cases require numeric equality to zero. Decimal
exponents such as 0E-51 do not make a nonzero value. Never compare zero strings
or reprs, divide by a zero reference, or introduce a near-zero physical threshold.
The script formats output for display only; it does not normalize calculation values.

## 7. Zero and missing-input cases

### Z1 - Complete zero calculation

Set both AC powers and stack current to zero, retaining durations. All five
outputs are exactly zero, GUESS/SIMULATED. The narrow calculation is not INVALID
solely because values are zero. This is not a physical balance proof.

### Z2 - Isolated zero-current edge case

Only stack current is zero. H2 amount/mass/LHV are exactly zero; operating energy
is 1.575 kWh and standby energy is 0.010 kWh. This tests algebraic dependencies,
not a plausible operating point or closed balance.

### M1 - Missing stack current

Do not substitute zero. H2 amount/mass/LHV have no numeric value, carry a
blocked/absent marker with dependency reason per the approved task contract,
and have no computed-result evidence_status or result_origin.
Retain an unquantified-item BACKLOG indication under D35 section 2, local commit
`f23d9f8`; this is not evidence assigned to a computed result that does not exist.
Electrical energies remain visible; the declared scope is INVALID.

### M2 - Missing standby duration

Standby energy is blocked as in M1; operating energy and H2 results remain
visible. The declared scope is INVALID.

Keep absent expected observations (`observation_status = MISSING`), absent
scenario inputs and blocked dependent items distinct. Assumptions are not
observations. No zero, NaN, skipna or `or 0` substitutes.
The concrete typed absence representation requires implementation review.

## 8. Future measurement-independence and dependency tests

These are test requirements, not implemented or executed tests in this reference.

Test-only measurement columns: time_s, el_ac_input_power_W, stack_current_A.

| Environment | Records |
|---|---|
| No measurements | None |
| Fixture A | (0, 900, 3), (2700, 1100, 4) |
| Perturbed fixture B | (0, 300, 1), (2700, 1800, 6) |

All fixture values are synthetic. Times deliberately match the scenario
endpoints as an accidental-consumption trap. None of the fixture power/current
values equals the corresponding scenario value 2100 W or 8 A.
Keep scenario inputs identical: all five outputs, GUESS evidence and SIMULATED
origin must remain unchanged across environments.

The scalar calculation takes scenario inputs, not measurement records. Do not
add a production measurement channel solely for this test. Discarding fixtures
in a wrapper is not sufficient evidence: exercise any actual measurement-access
boundary on the invoked path and verify it is not consumed. If none exists,
report that architectural limit rather than claiming exercised data-path perturbation.

With fixtures unchanged:

- Double stack current: H2 amount/mass/LHV double; electrical energies unchanged.
- Double operating AC power: only operating energy doubles.
- Double standby duration: only standby energy doubles.

These check dependencies, not agreement with real plant measurements.

## 9. Reporting and separate obligations

Successful computed outputs carry GUESS and, subject to the independence check,
SIMULATED. Show unassessed scenario uncertainty and unchanged EL classifications.
No propagated output uncertainty, headline or measured-performance claim.
Do not sum input energy, chemical transport and losses into a single loss total.
Full-chain reports must expose unresolved required items; this narrow reference
does not establish AC1/AC8.

Open separately: Yodwong quotation/transferability; cell-count confirmation and
Faradaic-efficiency validation; dryer source/status discrepancy and applicability;
existing SOURCES migration; D25 mandatory channels; full-chain and historical AC8.
The channel-list gap does not block this measurement-free scalar reference.
