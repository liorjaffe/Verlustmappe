# 2026-11-14 - PV DC cable data remains missing

## Owner decision

The DC cable loss and route length stay MISSING/BACKLOG until reviewed site
data is available. Do not retain or infer a loss percentage, route length, or
zero-loss assumption.

PV overview calculations may continue for values independent of the missing DC
cable loss. Modelled AC energy and dependent cable/inverter loss bars remain
MISSING; measured AC energy remains usable. This applies the existing
`CONTRACT.md` §7 rule that dependent totals remain open while independent
results stay visible.

## Rationale

No reviewed source or site data supports the former DC cable loss estimate.
Keeping the input missing preserves useful DC-side overview values without
presenting an unsupported AC result as complete.

The later owner decision in `2026-11-16-pv-inverter-input-boundary.md`
supersedes the affected PV-start boundary and treatment of the missing cable
loss. The cable inputs themselves remain BACKLOG.
