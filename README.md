# Verlustmappe

Energiekontenbuch einer marktüblichen Pilotanlage: PV → Elektrolyseur → H₂-Speicher →
Brennstoffzelle → AC. Für jeden gewählten statischen Lastpunkt soll sichtbar werden, wohin
jede kWh geht, welcher Verlust welche Ursache hat und welche Werte noch fehlen.

**Einstieg:** [AGENTS.md](AGENTS.md) (Karte und Regeln) → [START.md](START.md) (aktueller
Stand) → [CONTRACT.md](CONTRACT.md) (was gilt).

| Ordner | Inhalt |
|---|---|
| `plant/` | eine Datei je Gerät: Werte, Status, Quellen, offene Fragen |
| `src/verlustmappe/models/` | Rechnung |
| `src/verlustmappe/loaders/` | Einlesen der Messdaten (Solis, Regatron, Enapter) |
| `data/` | Messdaten |
| `tests/` | Prüfungen, Handreferenzen unter `tests/reference/hand/` |
| `decisions/` | Begründungen |
| `tools/` | Anlagenwerkzeuge (Regatron-Bridge, Analyzer, Server, Plotter) |

Tests: `python -m pytest -q` (Python ≥ 3.11, numpy, pandas, requests).

Der Altstand vor dem Neustart ist über den git-Tag `archive-2026-11` abrufbar.
