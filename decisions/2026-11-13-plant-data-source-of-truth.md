# 2026-11-13 - Plant parameter and evidence sources

The owner clarifies the data hierarchy:

- `plant/<device>.toml` is the current project/runtime source of truth for plant parameters.
- XLSX workbooks and referenced documents provide inputs and evidence for those parameters;
  they are not immutable truth. The owner may revise source files or correct transferred
  values when evidence or review shows an error.
- Parameter transfers must be traceable and critically checked, including physical
  plausibility. Unverified values and conflicts remain open and are brought to the owner;
  no plausible value is silently invented or accepted merely because it appears in a workbook.
- This update applies to the already maintained `plant/system.toml` and `plant/water.toml`.
  Other device TOMLs remain untouched until their own review/update is requested.
