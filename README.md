# Verlustmappe

Energy ledger of a market-standard pilot plant: PV → electrolyser → H₂ storage → fuel cell
→ AC. For each chosen static load point it should show where every kWh goes, which loss has
which cause, and which values are still missing.

**Entry:** [AGENTS.md](AGENTS.md) (map and rules) → [START.md](START.md) (current state) →
[CONTRACT.md](CONTRACT.md) (what applies).

| Folder | Content |
|---|---|
| `plant/` | one file per device: values, status, sources, open questions |
| `src/verlustmappe/devices/` | device models, one file per device |
| `src/verlustmappe/hydrogen/` | hydrogen amounts, real gas, tank temperature |
| `src/verlustmappe/models/` | core: status, validity, item list |
| `src/verlustmappe/loaders/` | reading measurement data (Solis, Regatron, Enapter) |
| `data/` | measurement data |
| `tests/` | checks; hand references under `tests/reference/hand/` |
| `decisions/` | reasons |
| `tools/` | plant tools (Regatron bridge, analyzer, server, plotters) |

Tests: `python tests/run_all.py` and `python -m pytest -q` (Python ≥ 3.11, numpy, pandas,
scipy, requests).

The state before the restart is available via the git tag `archive-2026-11`.
