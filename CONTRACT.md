# CONTRACT – was gilt

Einzige Quelle für „was gilt“. Wird bei jeder Änderung **umgeschrieben, nicht ergänzt**.
Begründungen stehen in `decisions/`, nie hier. Stand: 2026-11-05 (Neustart).

**[E]** vom Owner entschieden – gilt. **[V]** Vorschlag – gilt erst nach Owner-Entscheidung;
bis dahin nicht als Regel verwenden, sondern als offene Frage behandeln.
`(Dnn)` verweist auf die alte Entscheidung, aus der eine Regel übernommen ist (Archiv-Tag
`archive-2026-11`); sie muss nicht gelesen werden.

## 1 Ziel [E]

Für die reale Pilotanlage zeigen, wohin jede kWh geht. Je gewähltem statischem Lastpunkt
ein Bericht: Energieweg vom PV-DC bis zum AC-Ausgang des FC-Wechselrichters mit jedem
Verlust und seiner Ursache, daneben der Energiebedarf der Nebenverbraucher. Jede Zahl
trägt ihre Herkunft. Was fehlt, steht als fehlend da. Keine Forschung an Zell- oder
Stackdetails: marktübliche Geräte dürfen Black Boxes mit belegten Ein- und Ausgängen sein.

## 2 Umfang

- [E] Nur Geräte mit **direktem Einfluss auf die Produktion**. Raum- und
  Gebäudeinfrastruktur ist ausgeschlossen: Lüftung, Gaswarnung, Heizung, Frostschutz,
  Raumgeräte.
- [V] Prüfbare Formulierung: Ein Gerät gehört dazu, wenn es Energie umsetzt, um ein
  Prozessmedium herzustellen, umzuwandeln, aufzubereiten, zu fördern oder zu speichern
  (Strom der Kette, H₂, Prozesswasser, Druckluft).
- [E] PV-Quelle ist nur F8 („F8_Fachada Leste“, zwei Solis-Wechselrichter). Der PV-Datensatz
  vom Sept. 2026 (`pv_merged.csv`) ist ausgeschlossen und nie Evidenz (D33).
- [E] Keine sonnengeführte Produktion. PV-Überschuss gehört nicht zur Rechnung und ist kein
  Verlust.
- [E] Der Regatron ist ein Prüfstand, kein Anlagengerät. Er ist Messquelle (Schicht 3).
- [E] Der Vergleich mit dem Altstand (früher AC8) entfällt.

## 3 Schichten [E]

| Schicht | Eingabe | Aussage |
|---|---|---|
| 1 statisch | vorgegebene Lastpunkte (Prozentwerte sind nur Beispiele) | modelliert |
| 2 dynamisch | **vorgegebenes Lastprofil**; PV nur als Verfügbarkeit, keine Sonnensteuerung | modelliert |
| 3 validiert | Messfenster | „validiert“ nur für diese Fenster, innerhalb der Unsicherheit |

Konten A, B, C sind in allen Schichten gleich definiert. Vor Schicht 3 wird keine
Validierung behauptet (D34).

## 4 Konten

- **A – Serienpfad** [E Grundsatz, V Details]: PV-DC (Modul-/Stringausgang) → DC-Kabel →
  PV-Wechselrichter → AC → EL → Dryer → Booster → Speicher → FC (mit H₂Core-Batterie und
  DC-Bus) → FC-Wechselrichter → AC-Out. Real hängt der EL am Hausnetz; die Kette ist eine
  **Zurechnung** (eine PV-Scheibe wird dem Pfad zugeordnet), keine Behauptung physischer
  Direktversorgung.
- **B – Nebenverbraucher** [E]: Geräte, die real aus Hausnetz oder dem separaten
  PV-Batteriesystem versorgt werden, je Gerät mit Versorger und Phase. Das separate
  PV-Batteriesystem ist nur externer Lieferant; sein Inneres wird nicht modelliert. Der
  Kaeser (Verdichtung) liegt in B.
- [V] Abgrenzung A/B: A enthält Energie, die durch die Serienumwandlung fließt. B enthält
  jeden anderen elektrischen Verbrauch, auch Standby von Geräten des Serienpfads
  (EL, PV-WR, FC-WR) und Dryer-Strom.
- [E] FC-Steuerung wird nach D22 im Serienpfad netto abgezogen:
  E_out_net = (E_fc_terminal − E_ctrl) · η_inv. Annahme: Bezug vom DC-Bus vor dem
  Wechselrichter; Messpunkt offen. Einmal gebucht.
- **C – Systemwirkungsgrad** [V Name und Formel]:
  η_sys = E_AC,out / (E_PV,DC,Anteil + E_B,extern + ΔS_Korrektur).
  Ausgabe erst, wenn Verdichtung und Batterie einen Status haben. Bis dahin [V]: A und B
  stehen nebeneinander mit eigener Summe, **ohne addierte Gesamtgröße**; A erscheint nie
  allein.
- [E] H₂Core-Batterie gehört zum FC-System. Sie ist nicht das separate PV-Batteriesystem
  für Nebenverbraucher. Batterieentladung darf nicht als Rückverstromung aus H₂ erscheinen.

## 5 Fall (Schicht 1)

- [V] Ein Fall enthält nur Eingaben, Annahmen und Begründungen. Alles Berechnete entsteht
  im Modell.
- [E] EL-Anker: AC-Leistung, Stackstrom, Betriebszeit, Standby-Leistung, Standby-Zeit.
  Keine dieser Größen wird ohne belegte Beziehung aus einer anderen abgeleitet.
- [E] Ein gewähltes Solis-Zeitfenster zeigt nur, dass genug PV-**Energie** da war. Es
  belegt keine zeitgleiche Leistung und keine reale Versorgung. [V] Die Auswahlregel des
  Fensters wird vorher festgehalten.
- [V] Der PV-Gesamtbetriebspunkt kommt aus dem Fenster. Wechselrichter und DC-Kabel werden
  bei Gesamtleistung bzw. Gesamtstrom gerechnet; der Verlust wird anteilig der Scheibe
  zugerechnet (Konvention, so benannt). Keine Umkehrfunktion nötig.
- [V] Jede Phasendauer hat eine Begründung: Betriebsvorgabe, Messbeobachtung oder
  bewusste Konvention.
- [V] FC-Betriebspunkt wird gesetzt; die FC-Dauer folgt aus der Molbilanz (sonst ist der
  Fall überbestimmt).
- [V] Zyklusschluss ist eine deklarierte Annahme in mol, keine Messung. Zwischenspeicher
  (Dryer-Hold-up, Puffer, Tank) werden als Annahme zusammengefasst.
- [V] Batterie: Anteil oder ΔS wird deklariert. Netto null ist nicht verlustfrei;
  Durchsatzverluste werden getrennt gerechnet.
- [E] Zustandsgrößen eines Betriebspunkts sind Eingaben: Tankdruck, Gastemperatur,
  Batterie-SoC, angeschlossenes Speichervolumen (800 L abgesperrt, sonst 1600 L).

## 6 Bilanzregeln

- [E] Verluste kommen aus eigener Physik oder Messung, **nie als Differenz**
  „Eingang minus Ausgang“.
- [E] Verbrauch ist kein Verlust. Speicheränderung ist kein Verlust. Ein ungeklärter Rest
  ist kein Verlust.
- [V] Molbilanz zuerst: n_Anfang + n_EL = n_Ende + n_FC + n_vent + n_leak + n_purge.
  Danach Energie: E_ein = E_aus + L + ΔS, mit ΔS = S_Ende − S_Anfang.
- [V] Ein Rest R ist nur Diagnose: an Stellen, wo dieselbe Größe zweimal unabhängig
  bestimmt ist. Im Modellfall nur als EL-Konsistenz (AC gegen V(I,T)·I plus
  Gleichrichterverlust).
- [V] Wärme ist in einer Vollenergiebilanz Abgabe, in einem Nutzenergiekonto Teil des
  Umwandlungsverlusts – nie beides.
- [V] Steckt ein Verbrauch schon in einem übergeordneten Messwert, wird er nicht noch
  einmal addiert (enthalten-in).
- [V] Verdichtung ist Verbrauch (Kaeser-Strom) und liegt nie im Speicherbestand.
- [E] Ideale Füllarbeit darf nur als so benannte Idealgasgröße erscheinen, nie als
  elektrische Verdichtungsenergie (D35).
- [E] Kaeser (D14): versorgt nur den HULC und die vier Rotex. Variabler Anteil nach
  Luftmenge (HULC / Rotex 1–4 / sonstige); READY-Standby und Netzleckage als eigene Posten;
  Leckage gehört zum Verteilnetz, nicht zum HULC. Standby nach Luftbezug, sonst gleich
  verteilt (Annahme). Kaeser-Eingangsleistung offen; 6,2 kW ist ein Händlerwert.
- [E] HULC-Luftbedarf (D13): Herstellerkurve als Funktion des H₂-Flusses am
  Anlagenbetriebspunkt; Betriebspunkt offen. 14,6 Nm³/Nm³ gilt nur bei Maximalfluss und
  ist keine Grenze. Geometrie (4,59–6,30) ist eine physikalische Untergrenze.
- [E] FC-Wechselrichter, Entladepfad (D3b): PV-AC-Datenblattwerte gelten dafür nicht.
  Bis zur Messung nie MEASURED.

## 7 Fehlende Werte und Gültigkeit [E]

- Fehlt ein Wert, gibt es keine Zahl: nicht null, nicht weggelassen, kein Standardwert.
  Abhängige Summen, Bilanzen und Kennzahlen bleiben ebenfalls offen. Unabhängige Ergebnisse
  bleiben sichtbar (D35).
- Anteile nur über quantifizierte Posten und mit genanntem Nenner. Keine Aussage „größter
  Verlust“ und kein vollständiges Sankey, solange Posten fehlen (D35).
- Berechnete Pfadgrößen (Energie, Leistung, Masse, Stoffmenge, Fluss, Absolutdruck,
  Absoluttemperatur) dürfen nicht negativ sein. Vorzeichenbehaftet sind Änderungen und
  Differenzen. Vorzeichen roher Messkanäle sind kein Fehler (D25, D31).
- Nicht monoton steigende Zeit ist ungültig (D25).
- Kein Begrenzen (clip, min, max) physikalischer Größen ohne Quelle und ohne sichtbaren
  Hinweis im Ergebnis.
- EL: Faraday-Wirkungsgrad endlich in [0, 1]; Zellzahl endlich, positiv, ganzzahlig.
  Verletzungen blockieren die H₂-Ergebnisse; nicht-numerische, boolesche oder nicht
  endliche Werte sind Datenfehler und lösen eine Ausnahme aus (D36).
- Fehlt ein Pflichtkanal (Schicht 3), ist die betroffene Route ungültig, nicht automatisch
  alles (D31).

## 8 Status

- [V] Neues Schema: `status` = MEASURED > DATASHEET > SECONDARY > ASSUMED > MISSING;
  das schwächste Eingangsglied bestimmt das Ergebnis. `origin` = measured | computed.
  `u_kind` = none | band | envelope. u = 0 heißt „nicht bewertet“, außer ausdrücklich
  anders angegeben.
- Bis zur Entscheidung gilt das Vokabular der bestehenden `registry.py` unverändert.
- [E] Die Schlüssel `comp.*` (falsches Gerät Maximator DLE 30-2) dürfen in neuem Code nie
  verwendet werden (D11).

## 9 Messdaten (Schicht 3) [E]

- Integration: Trapez innerhalb gültiger Segmente; Lücke, wenn
  dt > max(3 × nominelles Intervall, 30 s); abgedeckter Anteil wird ausgewiesen (D24).
- Nominelles Abtastintervall nur aus einem nachgewiesenen Exportraster der Quelle;
  F8: 300 s. Zeitstempel werden nicht auf ein Raster gerundet (D32).
- Zyklusschluss gemessen: CLOSED, wenn |Δn| ≤ 5 % · n_ref und u(Δn) ≤ 5 % · n_ref,
  n_ref = max(n_zu, n_ab); sonst NOT VERIFIABLE. Der Drucksensor DCT 541 dient nur diesem
  Urteil, nicht der Kalibrierung; bis zum Wiederholbarkeitstest ist gemessener Schluss
  NOT VERIFIABLE (D20, D8).
- Tankdruck und Gastemperatur sind bis zur Nachrüstung simulierte Zustände (D8).
- Erster Kalibrierkandidat: FC-Klemmenkennlinie aus Regatron-Sweeps (D4). Der
  Regatron-Strom ist Bus-/Lastseite, nie FC-Ausgang.

## 10 Veröffentlichung [E]

Jede Zahl erscheint mit Status, Schicht und Annahmen. Ein berechneter Wert darf nie wie
ein gemessener aussehen. „Validiert“ nur aus Schicht 3 und nur für die geprüften Fenster.
