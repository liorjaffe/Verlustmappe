# START – Zustand (wird überschrieben, nie ergänzt; höchstens 60 Zeilen)

Stand: 2026-11-05 · Branch `neustart` · `main` unverändert bis zum Owner-Merge.

## Ziel
Energiekontenbuch der realen Pilotanlage (PV-DC → H₂ → FC-AC) je statischem Lastpunkt,
jede Zahl mit Herkunft, Lücken sichtbar. Details: `CONTRACT.md` §1–§4.

## Stand des Neustarts
- [x] N0 Archiv-Tag `archive-2026-11`, Branch, Duplikate und `Differenz/` entfernt
- [x] N1 `AGENTS.md`, `START.md`, `CONTRACT.md`, `decisions/`
- [x] N2 Werte in `plant/<gerät>.toml` (16 Dateien, 109 Schlüssel, Gleichheit per Test);
      Realgas, Loader-Tests, Formate, Arbeitsbuch gerettet; Altbestand entfernt
- [ ] N3 neuer Kern `model/` (physics, devices mit step/event, balance, views);
      P14-Fall wird erster Test von `el`; Tests nach Modulnamen
- [ ] N4 `cases/F1.toml` und Fallbericht, sofort mit MISSING-Posten
- [ ] N5 Owner prüft den Branch und mergt

## Nächster Schritt
N3 vorbereiten: Schnittstelle `step`/`event` und Postenliste für A/B an F1 festlegen;
dafür müssen die [V]-Punkte in `CONTRACT.md` §4–§6 entschieden sein.

## Offene Owner-Entscheidungen
1. Alle [V]-Punkte in `CONTRACT.md` (Abgrenzung A/B, Formel C, Fallregeln, Statusschema).
2. Werteschutz: KI legt Wertänderungen nur als Vorschlag ab, Owner übernimmt?

## Offene Anlagenfragen (stehen auch unter [open] in der jeweiligen Gerätedatei)
- Filterpumpe (Hausnetz): Leistung und Laufzeit; Registry führt 0 W (`water_pump.toml`)
- PV-Leistung F8: 12,74 kWp gegen 12,78 kWp (`pv_array.toml`)
- PV-WR S6-GR1P6K: Datenblatt fehlt (`pv_inverter.toml`)
- H₂Core-Batterie: 100 Ah/52 V gegen 105 Ah/5 kWh/48 V (`fc_battery.toml`)
- Kaeser: Eingangsleistung, kWh-Zähler, Laststunden; Booster-Luftbedarf am Betriebspunkt;
  Herstellerfragen P-1 bis P-3 (`booster.toml`)
- Solis-DC-Kanal liegt 3–4 % über dem Zähler (Altbefund), daher nur Diagnose
- Regatron-Fast-Logs: vorhanden? Mit oder ohne FC-WR am Bus?

## Bereits entschieden – nicht neu diskutieren
Keine Sonnensteuerung · PV-Überschuss ist kein Verlust · Kaeser in Konto B ·
H₂Core-Batterie ≠ separates PV-Batteriesystem · Raum-Infrastruktur ausgeschlossen ·
keine zentrale Steuerung (in Geräten enthalten) · AC8 entfällt · Verluste nie als
Differenz · fehlender Wert = keine Zahl · Regatron-Werkzeuge bleiben in `tools/`.
Quelle: `CONTRACT.md`, `decisions/`.
