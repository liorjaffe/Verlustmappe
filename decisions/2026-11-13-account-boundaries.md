# 2026-11-13 - Account boundaries and leakage

The owner confirms the PV and FC cable stages and the separation between
FC-inverter conversion in A and its auxiliary consumption in B. The actual
electrolyser supply route remains open. Internal auxiliary supply must remain
visible and must not be counted twice or treated as external merely because it
appears in B.

The owner confirms that the Kaeser supplies four Rotex and both HULC stages.
Hydrogen leakage and compressed-air leakage are separate media and must not be
combined. The owner withdrew the proposed zero-leakage assumptions for gas
lines and storage; unknown leakage remains open.

For gas lines from EL via HULC to storage, the owner assumes zero line pressure
and enthalpy losses, separately from leakage. This is a modelling assumption,
not a measurement; the stated rationale is short lines and dominant device
losses, neither independently verified here. Device losses remain separate.

The compressor workbook `plant/sources/Compressor_System_Specs_Master_v2.xlsx`
identifies an HP-seal service limit as an upper bound, not a measured operating
loss (0.5% of delivery rate; Master row 114; source S6, DLE manual table 3-6).
Air leakage and pilot/purge air are air-energy items, not H₂ loss. The cited
manual's serial-number scope and transferability to the installed H₂ units
remain open. The original manual was not available for independent checking.
Actual leakage is unknown; a future measurement, if pursued, is subject to its
measurement boundary and detection limit.

The workbook's Sources sheet does not contain a separate transferability field.
BACKLOG: when the original manual and applicable source documentation are
available, record the serial-number scope and applicability to the installed
units in the relevant source entries. No new registry values or test assertions
are introduced by this decision.
