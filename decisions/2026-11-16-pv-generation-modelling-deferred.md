# 2026-11-16 - PV generation modelling deferred

The owner decided that work on modelling PV generation from irradiance and
module characteristics is deferred for now. The project focuses instead on
the energy chain starting from available PV DC energy.

Do not actively pursue the official MGTK datasheet, a clearer module nameplate,
rear-side energy gain, module temperature coefficient or degradation for
generation modelling while it remains deferred. These items remain unverified
or unresolved; deferral does not validate existing values or change any
parameter, assumption, model or result.

On 2026-11-16 the owner first approved an explicit opt-in for the old model,
then replaced that instruction: retain only a clearly marked, non-executable
generation-model placeholder with no plant profiles, values or defaults.
Preserve an available DC or AC reading when the other is missing; dependent
results remain MISSING rather than assuming a measurement boundary. The
historical F8 identifier selects the existing inverter model only; no
identifier means no inverter model is selected.

The owner approved removing the `PVSystem` capture-loss field: its reference
minus measured DC difference is not an independently established loss.
The optional capture ratio remains unchanged. This does not change measured
energies or the PV inverter's separate loss model.

At this decision the PV-start boundary remained the module/string output before
the DC cable; generation deferral did not authorize a boundary change or a
zero cable loss. The later owner decision in
`2026-11-16-pv-inverter-input-boundary.md` supersedes that boundary.
