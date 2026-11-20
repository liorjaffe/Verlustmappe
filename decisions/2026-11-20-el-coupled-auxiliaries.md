# 2026-11-20 - RO, WTM and dryers run only with the EL; EL-to-dryer assignment

## Owner statements

- The BWT RO, the WTM 2.1 water tank and the two DRY 2.1 dryers are powered only while
  the EL are switched on (production and start-up phases). They can technically be switched
  off separately but run together with the EL. None of them is a permanent base load.
- EL 1-5 are connected to one dryer, EL 6-9 to the second.
- Dryer electrical value = 0.045 kWh/Nm3 x H2 throughput (2026-11-19); 10 W standby and
  200 W rated per unit only bound it.

## Implementation

- `devices/water.py`: `ro_standby_always_on` removed; RO and WTM standby = standby power x
  `el_on_h`; without `el_on_h` they stay open (CONTRACT sec. 7). Warning if RO production
  time exceeds the EL on-time.
- `devices/dryer.py`: production-coupled energy, 10/200 W envelopes over `el_on_h`, purge
  loss BACKLOG with envelope (30 NL/h, 47 NL per shutdown), total and per-unit capacity
  checks. New `dryer.max_el_per_unit` = 5: 5 x 500 NL/h = 2.5 Nm3/h equals the dryer rating,
  PASS with zero margin at nominal EL output (warned).
- `plant/water.toml` (`water.ro_power_standby_W` source/effect), `plant/dryer.toml`,
  water workbook (RO standby row and Notes 3 wording) corrected.
- Tests: expectations that encoded the permanent RO standby (8760 h window) updated to the
  EL on-time.

## Ledger hookup (owner approval 2026-11-20)

- Scenario gets `n_starts` (default None). Auxiliary on-time = `operating_time_s` +
  `n_starts` x `el.startup_duration_s` (start-up as its own phase, decision 2026-11-19; only
  the time is needed, the missing EL start-up power does not block the auxiliaries).
- Full scope only; the bounded P14 result is unchanged.
  - `dryer_electrical_energy_kWh` = 0.045 kWh/Nm3 x Faraday H2 (computed).
  - `water_energy_kWh` = RO production for the stoichiometric water of the Faraday H2 +
    RO standby x on-time (computed; blocked without `n_starts`).
  - new `water_tank_energy_kWh` = (WTM standby + 35 W x pump duty) x on-time; blocked while
    `water.tank_pump_duty` is BACKLOG. Kept separate so the open pump does not block the RO.
  - `dryer_vent_energy_kWh` stays blocked, reason now concrete (no sourced purge loss).
- Registry keys not requested in the ParamSet block the dependent item
  (UNAVAILABLE_PARAMETER) instead of raising; `el.n_cells` and `el.faradaic_efficiency`
  remain mandatory.
- Derived dependencies now contribute their input metadata and direct inputs their own
  (previously a derived dependency replaced all input metadata); bounded P14 results are
  unaffected because their items have a single derived dependency.
- Report limits state: auxiliaries are booked as plant-level equipment over the scenario
  on-time (no per-EL allocation for multi-EL operation); 0.045 kWh/Nm3 vs 200 W and
  990 vs 1260 s remain open.

## Open

- Per-EL allocation of plant-level auxiliaries once the multi-EL (9 EL) case exists.
- WTM pump duty, refill levels, dryer purge: telemetry.
