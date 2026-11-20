# 2026-11-19 - EL start-up as a separate line in account A

## Owner approval

1. EL start-up is its own case phase, separate from production and standby: number of
   starts, duration per start (`el.startup_duration_s` exists) and power during start-up.
2. Start-up energy is booked in account A as a separate line "EL start-up energy". It is
   not merged into the EL operating loss, so the EL efficiency stays a steady-operation
   value. Start-up power is not yet sourced and stays MISSING.
3. The EL's single AC input is split by phase in time, not by dividing the current:
   standby -> B; production -> the whole AC input in A, with the EL's own auxiliaries
   (pumps, control, fans) embedded and identified as such (CONTRACT §4).

## Rationale

The owner preferred the separate line as more detailed and closer to reality. It keeps
start-up effort visible, which later allows comparing partial load against start-stop
cycling. Subtracting standby power from operating power, or stack DC power from AC input,
would be a difference (CONTRACT §6) and physically wrong because auxiliaries behave
differently in operation and standby; such residuals are diagnostics only.

## Changes

`CONTRACT.md` §5 (EL start-up); observer: EL slot "start-up" and an A-card line.

## Open

- Source for the EL power during start-up.
- Whether the same pattern applies to other devices with start-up (FC, Kaeser, Rotex);
  only after the EL is settled.
