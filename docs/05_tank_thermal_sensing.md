# Tank thermal sensing: evidence, method, and the sensor option

Everything the tank temperature decision needs, from the papers in the
Storage H2 folder plus the DCT 541 datasheet.

## 1. What the papers establish

**de Miguel et al., IJHE 40 (2015) 6449-6458 (JRC Petten)** — compressed
hydrogen tanks, Type III and IV, 2-3 MPa to 78-84 MPa cycling:
- During FILLING the gas temperature is almost perfectly uniform (forced
  convection from the jet). One internal sensor is representative.
- During HOLD and EMPTYING the gas stratifies vertically; faster emptying
  means stronger stratification. Top+bottom pair needed.
- Gas heat-up on fill: Delta T_avg = 64-96 K (Type IV), 64-77 K (Type III,
  steel, like ours). Type III tolerates more than twice the fill rate before
  hitting the 85 C limit.
- External surface temperatures follow the gas with a delay (wall inertia);
  at slow emptying they converge to the gas temperature. Bosses respond
  faster than the surface; the REAR boss correlates best with mean gas T.
- Mass calculation in that paper: Redlich-Kwong EOS.
- SAE J2601 context (same folder): fill gas temperature limit 85 C, NWP
  definition at 15 C, max 125% NWP fill pressure.

**Fuel cell behaviour and energy balance on board a Hyundai Nexo** (Sery & Leduc, International Journal of Engine Research 32(2) 2021, DOI 10.1177/14680874211059046,
on-board consumption study) — the methodological gold for us:
- They faced the SAME problem: tank pressure is measured, gas temperature is
  not. Their three model settings bracket the truth: isothermal assumption
  OVERestimates consumed mass, adiabatic UNDERestimates it; only the model
  with heat exchange (GS_tank = 70 W/K, fitted on resting-period pressure
  decay) matched the fuel-cell-current reference.
- Their lumped model (eqs 2-3): m_H2 cv dT/dt = -m_H2 cp dT-term + GS_tank
  (T_amb - T); p V = Z m R T; Z, cp, cv from CoolProp; ODE solved with
  Runge-Kutta (SciPy).
- Their external temperature study: T3 (bottom pipe) tracked the mean gas
  temperature best.
- Their pressure-method bias vs the reference came precisely from the assumed
  tank temperature - the same failure mode our Route 2 would have.

**Metal hydride paper (same folder)**: same conclusion for solid-state
storage - outside-wall temperature approximates internal temperature only if
wall heat transfer is large or wall effects are neglected (Remark 1).

## 2. Our tank (from the nameplate photo)

VITKOVICE CYLINDERS S-16-50-22-27: UN 1049 compressed hydrogen, water volume
**800 L**, PS **300 bar / 65 C**, safety valve 330 bar, temperature limits
-20/+65 C, steel cylinder. Consequences:
- Tank volume BACKLOG resolved (was the placeholder 100 L).
- The 200/300 bar conflict is resolved as "PS 300 bar (nameplate), working
  pressure 200 bar (installer)".
- Steel (Type I-equivalent) wall: less stratification, faster wall response
  than Type IV composites, but 800 L is 10-13x the paper's vehicle tanks ->
  thermal inertia dominates; expect the gas to sit far from ambient for
  hours after a cycle.
- Our temperature limit is 65 C (nameplate), stricter than the 85 C
  vehicle limit.

## 3. The pressure sensor we already have

**BD Sensors DCT 541** (datasheet in the folder): H2-rated 316L transmitter,
RS485 Modbus RTU, accuracy 0.5% FSO (IEC 61298-2), thermal error 0.2% FSO
per 10 K, drift 0.1% FSO/year, 500 Hz measuring rate, 500 ms delay, hydrogen
embrittlement-resistant, oil/grease-free per ISO 15001.

Impact on Route 2 (registered in `registry.py`):
- Pressure reading error: +-0.5% FSO. On a 250-bar range: +-1.25 bar absolute
  per reading, amplified by p/(p2-p1) for mass differences. A 100-bar swing:
  amplification ~2 -> ~3.5% mass uncertainty from pressure alone (was ~2x
  worse with the manual gauge assumption of 2%).
- The 500 Hz rate means the sensor is never the bottleneck for our 20 Hz
  fast log; the 500 ms delay matters only for sub-second events.

## 4. The temperature sensor option (planned, not purchased)

Literature-based recommendation, in priority order:
1. **Bottom-pipe gas-well temperature** (Nexo's T3 position): tracked mean
   gas temperature best on-board. One well-type PT100 class A (IEC 60751:
   +-0.15 K + 0.002|T|) or type-K thermocouple in a thermowell in the gas
   outlet line.
2. **Top + bottom surface pair** (de Miguel): quantifies stratification
   during hold/empty; the MEAN of top and bottom surface temperatures is the
   stratification-robust estimate.
3. Optionally a second gas-well mid-height for redundancy.

Registry: `stor.temp_sensor_planned` (BACKLOG). Uncertainty budget for
Tier 2: sensor class A +-0.15-0.5 K + placement bias 1-3 K (boss/pipe vs gas
mean, from the papers' lag analysis) -> ~+-2 K total, versus +-3 K + fast-fill
bias for the Tier-1 ambient assumption.

## 5. What the pipeline does with this

`hydrogen/temperature_model.py` implements:
- `tier1_temperature()`: ambient assumption with the honest +-3 K term.
- `tier2_temperature()`: top/bottom mean with +-2 K placement term.
- `gs_fit_from_pressure_decay()`: Tier 3 - fits GS_tank and tau from
  resting-period pressure decay (Nexo method, three-parameter fit; the
  naive linearisation fails on non-converged decays and is only a fallback).
  Our 800 L steel tank should come out well above the Nexo's 70 W/K
  (larger surface area).
- `isothermal_adiabatic_bracket()`: the honesty bracket for Tier 1. For a
  50->200 bar swing with delta_T = 15 K: ~4% spread on the mass change.
  delta_T should be scaled to the fill rate (papers: 64-96 K on FAST fills,
  ~0 on slow ones).
- `h2_from_tank_pressure(..., tier=1/2)`: Route 2 now takes the tier, mixes
  the DCT 541 uncertainty (0.5% FSO, amplified) with the temperature tier.

## 6. What to buy / do next (decision list)

1. Enter the real ordered DCT 541 range into `meas.p_sensor_fso_bar`
   (ASSUMPTION currently 250 bar FSO).
2. Mount the DCT 541 close to the tank (short dead volume), read via Modbus
   RTU at >= 1 Hz into the fast log.
3. For the temperature option: bottom-pipe thermowell PT100 A + top/bottom
   surface pair. Cost is minor; the payoff is Tier 2 (+-2 K instead of the
   fast-fill bracket).
4. After installation: run one fill, let the tank REST, record pressure decay
   1 h -> `gs_fit_from_pressure_decay` gives GS_tank and tau. From then on
   Tier 3 works without any internal sensor: temperature from the model,
   validated by the fit quality (r2).
