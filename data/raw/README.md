Source exports and evidence go here (Grafana exports, SolisCloud pulls, photos of gauge readings).
Do not edit source files in this folder. Loaders read from here and write to data/processed/.
Large API pulls are committed as per-file gzip with a SHA-256 manifest of the uncompressed
saved JSON. Verify a file by comparing `gzip -cd <file>.json.gz | shasum -a 256` with its
entry in `MANIFEST.sha256`. The manifest hashes the saved JSON representation, not the original
HTTP response bytes. Future pulls use the same per-file compression and manifest convention.

solis_f8/: SolisCloud `inverterDay` API responses, saved as compact JSON from the parsed API
response, one file per
F8 inverter (SN 1802060225250007 and ...0009) and day, pulled 2026-10-28 read-only (endpoint
called via `loaders/solis_live._call`). Range 2026-01-01..2026-10-27: 528 files, 74 832 records,
0 records without `dataTimestamp`. Days 2026-09-17..2026-10-22: the API returned empty lists for
both inverters (cause unknown, verified); no file is written for empty days.
Parsed CSVs (loader mapping, UTC index) are in data/processed/solis_f8/.
