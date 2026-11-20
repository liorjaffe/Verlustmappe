# 2026-11-19 - Island assumption: all electricity from PV via the PMS

## Owner statement

1. Physically, the electrolyser is fed by a power management system (PMS). The PMS is fed by
   the PV inverters and the grid connection and exchanges energy with batteries via their
   own inverter (lab figure: Fotovoltaica/UFSC, Fig. 3, "Schematic view of the electrolysis
   system").
2. For this project the lab is treated as an **island**: during the run times considered,
   all electricity comes from the PV modules, both the energy converted into hydrogen and
   the auxiliary energy of every device in and around the chain, down to the standby of
   the FC inverter.
3. The PMS is the common electricity source for all devices (water pump, EL, dryer, Kaeser,
   standby consumers and others).
4. The grid, the PV-side batteries and their inverter are not modelled.
5. Cable specifications and possibly PMS data and losses will follow.

## Recorded consequences

- The observer diagram (`tools/project_observer/topology.toml`) now shows PV inverters ->
  AC cable -> PMS -> EL. The PMS feeds the auxiliary line, and the separate
  "auxiliary supply" tile is removed. The redrawn diagram awaits owner review.
- `CONTRACT.md` §4 updated with explicit owner approval (2026-11-19): series path via AC
  cable -> PMS -> AC cable -> EL; island supply via the PMS with PV available without
  limit in every case phase (declared assumption); B supplied via the PMS; cable losses
  per segment, PMS losses from PMS data, split between A and B open. Owner-confirmed [E]:
  the PMS is the building's common power distribution, not a central plant control (§2).
- `plant/water.toml` still records the pump as supplied from the house grid, and
  `plant/ac_cable.toml` describes a cable PV inverter -> EL. Both are plant files and stay
  unchanged until the owner edits them.

## Later scenario (owner, not now)

Including the PV-side batteries (and their inverter at the PMS) is a possible additional
scenario, only after the project is complete on the normal supply path.

Using the whole BIPV (all facades and orientations, with its further inverters) instead of
F8 only is another possible scenario; deferred by the owner on 2026-11-19 because it raises
questions about the other inverters and is not needed while the simulation has fewer than
all nine EL units.

## Supply losses and C (owner approval, 2026-11-19)

Written to `CONTRACT.md` §4: losses of the stations A and B share (PV inverters, cable to the
PMS, PMS) are allocated pro rata to energy, a named convention that is not exact because
cable loss scales with current squared; a single-consumer cable carries its loss fully. B is
shown as "B at the device" and "B supply losses". Under the island assumption E_B,external
is B at the device plus B supply losses. Reason: treating B's path as lossless would load
the shared losses onto A alone and would count missing losses as zero (§7).

## Not yet written to CONTRACT

The PV inverter operating point from demand per phase (§5; owner: "plausible"), which would
replace the Solis window as supply evidence.

## Open

- Clarified 2026-11-19: "not modelling the inverters" means only the battery inverter at
  the PMS; the PV inverters (Solis) stay in the series path.
