# START – Zustand (wird überschrieben, nie ergänzt; höchstens 60 Zeilen)

Stand: 2026-11-05 · Branch `neustart` · `main` unverändert bis zum Owner-Merge.

## Ziel
Energiekontenbuch der realen Pilotanlage (PV-DC → H₂ → FC-AC) je statischem Lastpunkt,
jede Zahl mit Herkunft, Lücken sichtbar. Details: `CONTRACT.md` §1–§4.

## Stand des Neustarts
- [x] N0 Archiv-Tag `archive-2026-11`, Branch, Duplikate und `Differenz/` entfernt
- [x] N1 `AGENTS.md`, `START.md`, `CONTRACT.md`, `decisions/2026-11-05_neustart.md`
- [ ] N2 Altbestand entfernen; Werte aus `registry.py` + `SOURCES.md` per Skript nach
      `plant/<gerät>.toml`, Test auf Wertgleichheit; Loader, Konstanten, Integration,
      Temperaturmodell und Realgas (`hydrogen/z_realgas.py` mit Testwerten) umziehen
- [ ] N3 neuer Kern `model/` (physics, devices mit step/event, balance, views);
      P14-Fall wird erster Test von `el`
- [ ] N4 `cases/F1.toml` und Fallbericht, sofort mit MISSING-Posten
- [ ] N5 Owner prüft den Branch und mergt

## Nächster Schritt
N2 vorbereiten: Behalten-Liste und Löschliste als einen Commit-Plan vorlegen; Owner gibt frei.

## Offene Owner-Entscheidungen
1. Alle [V]-Punkte in `CONTRACT.md` (Abgrenzung A/B, Formel C, Fallregeln, Statusschema).
2. Werteschutz: KI legt Wertänderungen nur als Vorschlag ab, Owner übernimmt?

## Offene Anlagenfragen (nur der Owner kann sie beantworten)
- Gerätezählung: welche Prozessgeräte es gibt und wer sie versorgt
- PV-Leistung F8: 12,74 kWp (28 × 455 W) gegen 12,78 kWp in der Solis-Stationsliste
- PV-WR S6-GR1P6K: Datenblatt fehlt (D6)
- H₂Core-Batterie: 100 Ah/52 V in der Registry gegen 105 Ah/5 kWh/48 V im Datenblatt (D10)
- Kaeser: Eingangsleistung, kWh-Zähler, Laststunden; Booster-Luftbedarf am Betriebspunkt
- Filterpumpe (Hausnetz): Leistung und Laufzeit
- Solis-DC-Kanal: was misst er genau? Regatron-Fast-Logs: vorhanden, mit/ohne FC-WR am Bus?

## Bereits entschieden – nicht neu diskutieren
Keine Sonnensteuerung · PV-Überschuss ist kein Verlust · Kaeser in Konto B ·
H₂Core-Batterie ≠ separates PV-Batteriesystem · Raum-Infrastruktur ausgeschlossen · keine zentrale Steuerung (in Geräten enthalten) ·
AC8 entfällt · Verluste nie als Differenz · fehlender Wert = keine Zahl ·
Regatron-Werkzeuge bleiben in `tools/`. Quelle: `CONTRACT.md`, `decisions/`.
