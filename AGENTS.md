# AGENTS – Einstieg für jede KI (wird automatisch geladen)

Dieses Repository ist das einzige Gedächtnis des Projekts. Was nicht hier steht, gilt nicht.

## Arbeitsablauf
1. `START.md` lesen (Zustand, nächster Schritt, offene Fragen).
2. Frage in der Karte unten einordnen; nur die genannte Datei lesen.
3. Nur im Umfang des Auftrags arbeiten, auf einem Branch; nie selbst nach `main` mergen.
4. Einigungen mit dem Owner **in derselben Sitzung** in `CONTRACT.md` eintragen
   (umschreiben, nicht anhängen); die Begründung kommt nach `decisions/`.
5. `START.md` am Ende überschreiben (höchstens 60 Zeilen).
6. Gates ausführen und mit Exitcodes berichten.

## Karte: Frage → Datei
| Frage | Datei |
|---|---|
| Wo stehen wir, was ist als Nächstes zu tun? | `START.md` |
| Was gilt (Ziel, Umfang, Konten, Bilanz, Status)? | `CONTRACT.md` |
| Warum ist etwas so entschieden? | `decisions/` (nur bei Bedarf) |
| Welcher Wert, welche Quelle, was ist offen? | `plant/<gerät>.toml` (gelesen über `src/verlustmappe/registry.py`) |
| Wie wird gerechnet? | bis N3: `src/verlustmappe/models/`; danach `model/devices/<gerät>.py` |
| Ist es belegt? | passender Test unter `tests/` |
| Wie lese ich Messdaten? | `src/verlustmappe/loaders/` und `loaders/FORMATS.md` |
| Gerätewissen aus dem Altstand (nur beim Portieren) | `git show archive-2026-11:<pfad>` |

**Stoppregel:** Steht die Antwort nach der Karte nicht fest, nachfragen oder als UNVERIFIED
markieren, nicht weitersuchen. Fehlersuche darf dem Aufrufpfad folgen; jede Abweichung von
der Karte im Bericht begründen.

## Regeln
1. Keine Zahl erfinden. Fehlt ein Wert, ist er MISSING; nachfragen.
2. Werte und erwartete Testwerte ändert nur der Owner; die KI legt einen Vorschlag vor.
3. Erwartete Testwerte nie vom getesteten Modell berechnen; Herleitung steht im Test.
4. Kein Verlust als Differenz „Eingang minus Ausgang“.
5. Physikalische Größen über Funktions-/Dateigrenzen tragen die Einheit im Namen
   (`power_W`, `energy_kWh`, `time_s`).
6. Kein Begrenzen physikalischer Größen ohne Quelle und sichtbaren Hinweis.
7. Neue Datei nur, wenn dafür eine andere entfällt oder zusammengeführt wird.
8. Reviews: höchstens eine Runde je Entwurf. Befunde einordnen als Blocker,
   Ergebniswirkung oder Pflege; nur die ersten beiden werden umgesetzt.

## Gates (aus `.venv`)
`.venv/bin/python -m pytest -q` · `git diff --check` (beides: `tools/run_local_gates.py`)

## Bericht
Ergebnis (2–3 Zeilen) · Dateien mit Grund · Belege (Befehle und Exitcodes) · Commit ·
UNVERIFIED und Annahmen.
