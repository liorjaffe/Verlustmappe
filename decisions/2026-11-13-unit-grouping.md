# 2026-11-13 - Owner static unit-grouping decision

## Scope and implementation boundary

Owner approval: 2026-11-13, following review of the proposed grouping rules.
Record the rule in `CONTRACT.md` section 5 and the N4 next step in `START.md`.
This change is documentation only: no runtime parameters, case schema, device
formulas, reference values or tests change.

Implement the case schema, numeric inventory parameters and F1 integration together
under N4, with scoped tests and owner-approved parameter-reference changes.
Do not independently extend `accounting/static_map.py` in this documentation task.

## Inventory is not operation

- Owner-reported installed inventory: **9 EL**, **2 FC modules**, **2 PV inverters**.
  Installed counts have not been independently verified on site
  ("installierte Stückzahlen nicht unabhängig vor Ort belegt").
- The nine EL are approved as an **OWNER_DECISION** modelling basis, dated
  2026-11-13, not as MEASURED or DATASHEET installation evidence.
  Introduce the numeric EL inventory parameter with N4, not in this change.
  Owner approval does not certify performance or supply capacity.
- `plant/fc.toml` describes two FC modules in its title, not a numeric inventory
  parameter. `plant/pv_inverter.toml` identifies two S6-GR1P6K units by model and
  serial numbers through the reviewed workbook; one nameplate is cited, the
  other unit is platform-only. Make the inventory consistently accessible in N4;
  do not infer active counts from titles or available telemetry columns.
- The proposed simplified status scheme in CONTRACT section 8 is still [V].
  This decision does not activate it or introduce an ASSUMED status.

## Per-phase states and independent anchors

Each static phase distinguishes active, standby and off units, consistent with
installed counts. State the operating point per active unit. Identical units at
the same point may form one group under a named identical-behaviour assumption;
different operating points require separate groups, not copied device code.

The existing EL anchor rule applies to every group: per-unit AC power, stack
current and standby power, plus group operating and standby durations, retain
their independent input basis. No duration is inferred from count alone.

Standby of series-path devices is account B consumption with actual supply
identified, never double counted. Off is a separate state, not standby:
zero requires an explicit full-shutdown assumption for the relevant supplies.
Without that basis, residual consumption remains missing rather than zero.

Set the FC operating point; derive its production duration from the mole balance.
Do not add a free FC production-duration input. For several FC groups with
different durations, declare a sequence or gas allocation: one total balance
does not determine several independent durations. The first case can use one
jointly operated FC group.

## Shared infrastructure and comparison cases

Sum the group demand and compute shared infrastructure exactly once at its own
operating point and duration. Preserve D13/D14: HULC air demand at the applicable
flow/pressure point; Kaeser variable consumption allocated by air quantity,
READY and network leakage separate, existing standby allocation unchanged.
Do not invent a parallel allocation rule or an unverified fixed/variable curve.

Higher throughput can distribute time-dependent consumption over more hydrogen;
it does not itself prove a better device efficiency. Keep missing curves open.
Compare explicitly either equal operating duration or equal hydrogen quantity.
Start with one EL reference group, then scale active counts while preserving
the stated single-unit point and checking supply and device capacities.

The arithmetic 9 x 500 NL/h = 4.5 Nm3/h versus the HULC "up to 5 Nm3/h"
rating is a nominal consistency check only, not installation evidence or proof
of capacity at the case pressure. Similarly, installed equipment does not
establish that the present PV path can supply every proposed EL load.

## Future PV expansion - BACKLOG, not current capacity

The owner may later add inverters of the same type connected to another PV
system with the same module type. Count, configuration, capacity, connection
and implementation date are not specified. Do not increase present PV supply
or change the current F8 scope. Even identical hardware requires a separate
source/measurement boundary and an approved scope change before integration.

## UNVERIFIED

Installed counts are not independently verified on site. Actual supply paths,
residual off-state consumption, HULC capacity at the case pressure and Kaeser
load-dependent consumption remain open. No scaling-efficiency benefit is
quantified or validated by this decision.
