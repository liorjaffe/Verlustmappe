# Library - reference documents (PDF)

Background documents kept for traceability. Runtime truth is `plant/*.toml`; reviewed
evidence is in the workbooks next to this folder. **Open a PDF here only when the owner
explicitly asks for it** (AGENTS.md map). Add one entry per file; do not rename files.

## Walter_2024_RBENS_PV-electrolysis-operating-behavior.pdf

- Walter, G.; Diel, S.; Rufino Júnior, C. A.; Schweiger, H.-G.; Bessa, I. V.; Mallmann, M.;
  Oliveira, A. K. V.; Santos, D. O.; Rüther, R. (2024): Operating behavior of a
  photovoltaic-driven electrolysis system. Revista Brasileira de Energia Solar 15(1), 82-92.
  DOI 10.59627/rbens.2024v15i1 (as cited in the EL workbook). 11 pages, SHA-256
  `207a34327bfb6260c148d962af9f47f5822233459c20f10c0a3b86e85c4219fa`.
- Content: measurements on one EL 2.1 of this plant (Fotovoltaica/UFSC, 9 x EL 2.1,
  2 x DRY 2.1). AC power by Fluke 435-II; H2 flow from the EL's internal analysis function
  (calculated, not metered). Cold start 100 % (Fig. 5), production rates 60/80/100 %
  (Fig. 7, 8), warm starts after 30/60 min (Fig. 9, 10), specific energy over time (Fig. 6),
  load steps 100<->60 % (Fig. 11). Plant description: PMS, water tank & filter, rooftop
  rainwater (sec. 2.1, Fig. 2-4).
- Cited by: `el.startup_duration_s` (`plant/el.toml`); EL workbook (start-up rows, Sources).
- Owner 2026-11-20: data may serve a later first calibration (not yet); owner intends to
  supply the exact underlying data. Curves are digitisable only (approx. +/-50 W, +/-10 s).
