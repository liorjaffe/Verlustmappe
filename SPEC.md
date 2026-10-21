# Project specification

## Purpose

Verlustmappe estimates the energy losses and round-trip efficiency of the UFSC
photovoltaic-to-hydrogen-to-fuel-cell island system. Its results must expose their
source, uncertainty, and status rather than present assumptions as measurements.

## Scope and sources of truth

- The project overview, current boundaries, and reading guide are in [README.md](README.md).
- Device parameters, their values, units, uncertainty, and status live in
  `src/verlustmappe/registry.py`.
- Every externally sourced number needs a detailed citation and transferability note in
  [SOURCES.md](SOURCES.md).
- Plant-specific choices and approved changes are recorded in [DECISIONS.md](DECISIONS.md).
- The current code and its tests are the executable definition of implemented behavior.

## Acceptance principles

- Do not invent missing values or operating requirements; record them as `BACKLOG`.
- Keep independently computed energy and hydrogen balances honest; do not book an
  unexplained residual as a physical loss.
- Test expected behavior against independent calculations or cited evidence.
- Generate README demo values from the project demo; do not edit generated values by hand.
- Run `python3 tests/run_all.py` and require its final `ALL PASS` result.

Open technical questions remain in the project documentation and task files. This
specification does not resolve them or approve changes to registry values.
