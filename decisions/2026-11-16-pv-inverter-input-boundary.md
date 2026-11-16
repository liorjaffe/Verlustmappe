# 2026-11-16 - Provisional PV inverter-input boundary

The owner decided that until DC cable data is available, the PV-start path
begins at the inverter DC input. The upstream PV DC cable is outside this
provisional boundary, not assumed lossless. Its missing data does not block
results that start at the inverter input.

When suitable cable data is available, the cable is to be included. Its data,
loss model, allocation and the revised start boundary must be reviewed before
implementation; a registry value alone does not automatically change the
boundary. The estimated cable loss must not be subtracted a second time from
the measured inverter-input energy.

This supersedes the module/string-output boundary and related missing-cable
treatment in the prior decisions on DC cable data and generation deferral.
It does not establish the cable loss, a new value or a calculation formula.
It does not establish the AC measurement boundary or prove a direct supply
to the electrolyser.
