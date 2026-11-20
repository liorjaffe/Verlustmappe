# 2026-11-19 - Register of open uncertainties (`uncertainty_open`)

## Owner approval

Many plant parameters carry an uncertainty that is currently unknown. They are collected
for a later detailed review instead of being forgotten behind 0.0:

1. Optional TOML field `uncertainty_open` per parameter: what is unknown about the
   uncertainty and which evidence could close it. Evidence routes are candidates, not
   findings or plans. Absent for exact constants or reviewed items without an open question.
2. `tools/list_open_uncertainties.py`: manual, read-only listing on stdout of registered
   items and of parameters with uncertainty 0.0 but no text yet (not reviewed). It prints
   no values or uncertainties and is not part of the simulation, CI or the observer.
3. Filled per device during each TOML review; EL first (all ten parameters, 2026-11-19).
   FC and PV entries follow; the blanket audit of unsourced u > 0 is attached to it.

## Rationale

0.0 currently means NOT ASSESSED, a bound, a constant or an exact definition; the number
alone cannot tell them apart. A separate list would drift from the TOML; the field keeps
the open item next to the value. The observer is not used because CONTRACT §12 forbids it
to read uncertainty contents.

## Changes

`CONTRACT.md` §8 (one sentence); `plant/el.toml`; `tools/list_open_uncertainties.py`;
`tools/README.md`; `tests/test_plant_uncertainty_open.py` (schema guard only).

## Note on el.faradaic_efficiency (Yodwong et al. 2020)

DOI 10.3390/en13184792 resolves to Energies 13(18), article 4792 (checked 2026-11-19);
the full text could not be fetched (HTTP 403). Paper contents reported in an external
review (PEM, 3 cells, up to 10.5 bar, measured range 0.9644-0.9999) are UNVERIFIED here.

Owner 2026-11-19: el.faradaic_efficiency keeps 0.98 as GUESS, because the stack-current
route must yield output; the source text now names it a working assumption without AEM
evidence and limits Yodwong to a PEM direction statement. Value, status and unit unchanged.
