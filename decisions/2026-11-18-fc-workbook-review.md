# 2026-11-18 - FC workbook review

The owner approved a review edit set for
`plant/sources/Fuel_Cell_System_Specs_Master_2026-11-12.xlsx` (file name kept;
Overview A2 states the 18 Nov revision; Notes 18 lists the edits). Only the
workbook changed; no TOML, code or test values changed.

Owner decisions recorded here:

- The 34 SLPM nominal H2 flow per FCM-802 is owner-confirmed. Sources: manual
  p. 18 (at the manual rated power 2.4 kW) and Intelligent Energy
  correspondence of 16 Sep 2026 (verbatim, Sources No. 18). It is a
  manufacturer reference point, not a plant calibration. The SLPM T/p basis
  is not confirmed; the 25 Sep 2026 email exists only as a fragment.
- Fuel Cell row 31 (reference conditions) has the role "Model constant".
- The Hybrid Control undervoltage test-abort criterion (row 19) is ASSUMED:
  a project check against the factory restart logic (48 V / 60 s, 46 V,
  manual p. 24), not an FCM function; its duration stays undefined until the
  control code is frozen.
- Manufacturer and site confirmations are deferred, not dropped: Intelligent
  Energy (SLPM basis, two-module purge peak, meaning of the 150 W rated input,
  telemetry units), CAN read-back of the installed factory parameters, Green
  Tech (200 A vs 100 A, cell chemistry/count), site checks (battery variant,
  Solis AC input and grid charging, Lynx RJ10 supply, 1/4 in supply line vs IE
  1/2 in recommendation) and manual p. 12 (PFC inputs/outputs).
- The H2 mass flow meter is out of scope and is not reconsidered.

Not decided: D3b wording in `CONTRACT.md` §6 for the 0.94 FC inverter working
value; the workbook row-structure repair (shifted merged ranges on the Fuel
Cell sheet, empty Instruments rows 2-11, own rows for Restart Delay and
telemetry units).

Known TOML errors for the later rewrite from this workbook: `fc_battery.toml`
calls 48 V the target-voltage factory default (manual p. 24: 52 V);
`fc_inverter.toml` calls the PV-AC 93-95% range the discharge efficiency and
its +/-0.02 band has no source; `fc.toml` marks the manual POC duration as
DERIVED; workbook and TOML keys differ; workbook statuses must be mapped to
the CONTRACT §8 scheme.
