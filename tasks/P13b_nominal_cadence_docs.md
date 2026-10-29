# P13b: nominal sampling cadence per source

**References:** D24 (integration gap rule), D32 (qualification of source cadence), D33 (F8-only
PV boundary and exclusion of the Sept 2026 PV dataset).
**Status:** Complete; documentation and evidence checked on 2026-10-29.

## Goal

Document source-qualified nominal intervals for D24 in `docs/03_data_dictionary.md`. Keep a
source's nominal interval distinct from observed timestamp statistics and from the interval
configured by our own polling or calculation code.

## Final write scope

- `docs/03_data_dictionary.md`: nominal interval table and current SolisCloud history wording.
- `docs/94_known_defects_legacy.md`: the C20 F8 cadence clarification.
- `HANDOFF.md`: outcome, remaining bridge quantification, and timestamp merge policy.
- `SOURCES.md`: owner-approved source entry for the F8 portal chart (protected path; explicit
  owner approval on 2026-10-29).
- `tasks/P13b_nominal_cadence_docs.md`: final task record (owner-authorized scope extension).

The uploaded portal export and the existing raw/processed SolisCloud history were read-only
evidence; they were not edited by this task. No registry, SPEC, DECISIONS, code, or tests were
changed by P13b.

## Decisions and evidence

- D24 remains unchanged: a gap is `dt_s > max(3 * nominal_dt_s, 30 s)`. Gaps segment the series;
  covered fraction is reported. D32 says source cadence is a data-analysis property documented
  here, not a registry parameter, and changes require a DECISIONS entry.
- D32(a) accepts a demonstrated source grid when each interval is exactly the grid interval or an
  exact multiple of it, and the grid interval is the smallest interval observed. No timestamp
  rounding or jitter tolerance was introduced.
- The F8 portal export is
  `data/raw/Daily+Power+Station+Chart_29-10-2026.xls` (SHA-256
  `754740b3eb2e8f119bfa1b200fa2f0ae2c66b872c28bdc3166d416281d742621`). The filename date is
  2026-10-29; the sheet identifies the chart date as 2026-10-28. It names station
  `F8_Fachada Leste` and contains 162 readings: 160 intervals of 300 s and one interval of
  1200 s. The smallest interval is 300 s, so the portal chart satisfies D32(a).
- The sheet's `Installed Capacity:12.780kWp` is quoted as source content only. The registry
  remains 12,740 W (28 x 455 W = 12.74 kWp); resolving this discrepancy requires a separate
  owner decision and was not part of P13b.
- The official SolisCloud Developer Platform User-Auth documentation was checked on 2026-10-29.
  It describes `inverterDay`'s `dataTimestamp` as "Update time" but provides no endpoint-specific
  resolution. Its general "Device data upload frequency: 5 minutes" statement is not treated as
  an endpoint resolution or as the nominal basis.
- The F8 API history is documented only as an observation: 74,304 intervals, median 299.965 s,
  97.8% in the 290-310 s band, 13 intervals >900 s, and no non-positive intervals. The
  calculation sorts raw `dataTimestamp` values within each daily API response before UTC
  conversion. Both raw JSON and processed CSV readings give 13 intervals >900 s; the earlier
  count of 11 was an incorrect calculation.
- D33 excludes the Sept 2026 PV dataset from evidence; `pv_merged.csv` and its back-check were
  removed per owner decision. F8 is the only PV source in scope.

## Final cadence table

| Source | Nominal interval | Basis / open point |
|---|---:|---|
| Regatron fast log | 0.05 s (20 Hz) | Code-anchored target `FAST_LOG_HZ = 20.0`; not a guaranteed device rate. The 30 s D24 floor dominates its gap limit. |
| FC retro export | BACKLOG | The 5 s grid in the merged processed file does not establish source cadence; raw-source provenance is unavailable. |
| EL (Enapter) | BACKLOG | No source-specific logging interval or raw EL time series is available. |
| SolisCloud F8 daily PV source | 300 s | D32(a) grid-derived from the F8 portal chart; API timestamp jitter is reported separately, not rounded. |
| Tank DCT 541 | BACKLOG | "500 Hz capable" is a capability, not a logging interval. |

## D24 consequence and remaining backlog

At nominal 300 s, the gap threshold is 900 s. Intervals of 600 s or 900 s are bridged linearly;
intervals strictly greater than 900 s are gaps. The portal chart has one 1200-s interval; the
API history has 13 intervals >900 s. This is D24's existing behavior, not a new per-source
exception.

Remaining BACKLOG: "reconstructed bridging share on the PV path, to be quantified on the first
measured week; a per-source multiplier remains a DECISIONS option."

Timestamp merge policy: preserve native source timestamps; do not snap them onto an artificial
grid before D24 timestamp validation. Deposited F8 history had no non-positive intervals.

## Acceptance evidence

- `.venv/bin/python tests/run_all.py` with `.venv/bin` on `PATH`: `ALL PASS`.
- `.venv/bin/python -m pytest -q`: `109 passed`.
- `BASE_REF=origin/main .venv/bin/python tools/ci_guard.py`: passed, 22 test files.
- `.venv/bin/python tools/make_readme_demo.py --check`: generated demo matches.
- `git diff --check`: passed.
