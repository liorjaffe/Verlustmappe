# 2026-11-16 - PV inverter measured mode

The owner approved an interim modelled PV inverter conversion loss using
measured inverter-terminal DC energy times (1 - 0.971). The anchor remains
the DATASHEET EU efficiency; constant application is an interim model, not a
measured efficiency or a validated part-load curve. Its uncertainty is not
assessed.

DC minus AC and modelled AC minus measured AC are diagnostics, not booked
losses. Their causes are not established; the reported DC-channel bias is not
independently verified. The AC measurement boundary remains open.

In measured mode with DC = 0 and AC nonzero, preserve the measurements,
return no eta, model loss or DC-minus-AC diagnostic, and flag
`dc0_ac_nonzero`. With DC = AC = 0, eta remains undefined, the interim model
loss is zero and this anomaly is absent. Missing DC leaves eta and model loss
missing. No tolerance threshold is adopted. This decision does not change the
FC inverter.

The measured-energy ratio is diagnostic; `eta_is_measured` must not identify
it as a verified inverter efficiency. The separate
`eta_based_on_measured_energies` flag records its input provenance.
Negative or non-finite DC energy and non-finite AC energy are invalid inputs;
finite signed AC values remain visible while the AC sign convention is open.
