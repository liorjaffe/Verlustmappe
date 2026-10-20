# Kritische Code-Review (wissenschaftlicher Standard)

Review-Umfang: alle uebernommenen Original-Dateien + eigene Module.
Methode: Unit-Harness (node) fuer die JS-Kernfunktionen gegen bekannte
Ground Truths; Zeilenreview der Berechnungswege; Kreuzcheck gegen
Enapter-/Geräte-Doku und Standard-Definitionen.

## Befunde HTML-Tool (fuelcell_analyzer.html)

1. trapzIntegral: KORREKT. Trapezregel mit exakter Boundary-Clipping,
   NaN-segmente werden uebersprungen (konservativ: laengeres Fenster ->
   keine Faelsch-Flaeche). Gegen 2000 W x 480 s = 960000 J verifiziert.
2. Effizienz-Definition: KORREKT. eta = E_el / (V_H2 * LHV|HHV);
   NL/min-Serie integriert ueber Zeit -> NL; /60-Konversion korrekt.
   Spezifischer Verbrauch NL/kWh konsistent.
   - Anmerkung: 2.995 Wh/NL (LHV) entspricht 33.30 kWh/kg statt 33.33,
     Delta 0.1 %, vernachlaessigbar, aber im Paper konsistent auf eine
     Konvention festlegen (33.33 kWh/kg LHV <=> 2.998 Wh/NL).
3. Kennwerte (ivCharacteristics): OCV = erster Punkt der Kurve, nicht
   Extrapolation auf I=0. Bei Segment-basierten Kurven ist das OK, muss
   im Paper so beschrieben werden ("OCV as lowest-current data point").
4. Degradation: V@fixes-I via Interpolation + lineare Regression,
   DOE/NREL-konform. KORREKT. mV/h- und %-/h-Skalierung geprueft.
5. Start/Stop-Zyklen: Schwellwert-basiert (% vom Maximum, nicht von der
   Nennleistung). Das ist robust, aber die Zyklenzahl haengt am maximalen
   Signal des Datensatzes. Im HTML-Tool OK (interaktiv), in der Pipeline
   ist die Nennleistung parametrisiert (besser).
6. Load Profile: zeitgewichtete Bins + Kapazitaetsfaktor, Methodik sauber.

## Befunde Pipeline-Module (Python)

1. event_analysis.py (uebernommen): Median/MAD z-Score, 1.4826-Skalierung,
   Settle-and-Hold-Recovery. Methodisch robuster als mean/std-Varianten.
   KORREKT. Eine Schwaeche (dokumentiert im Original): weniger sensibel
   auf langsame Drifts, by design.
2. dynamics.py: Unit-Fehler (J -> kWh statt Wh) gefunden und behoben;
   Zyklen-Energie jetzt gegen diskrete Ground Truth getestet.
   Start/Stop-Schwellwert = frac der Nennleistung (nicht des Maximums).
3. polarization.py: Kennwerte aus Stationaersegmenten (kein Sweep) -
   dV/dI ueber np.gradient nach Duplikat-Entfernung. OCV = kleinster
   gemessener Strom, konsistent zum HTML-Tool. KORREKT mit obiger
   Beschraenkung.
4. tank_pv.py: Realgasfaktor Z als konstanter GUESS (1.10 @ 200 bar).
   Fuer das Paper: Z als Funktion von p/T ersetzen oder tabellieren.
   Offener Punkt, im Registry markiert.
5. efficiency.py (HTML + Pipeline): H2-Telemetrie-Route ist NICHT
   unabhaengig vom electrical path (Enapter-interne Berechnung). Im
   Paper nur als Cross-Check, nie als primaere Effizienzquelle.

## Verbleibende Risiko-Punkte (offen, im Registry/Docs markiert)

- Z-Faktor konstant -> tabellierte Realgasdichte einbauen
- Keine unabhaengige H2-Messung -> Triangulation ist Pflicht, nicht Kuer
- Stack-zu-AC Zuordnung beim EL (PSU-Verluste) ungemessen
- Tankvolumen + Batteriekapazitaet = BACKLOG im Registry

## Physik-/Rechen-Audit Runde 2 (mit externen Referenzen)

Extern geprüft: NIST-Virialkoeffizienten (h2tools/Scribd-Tabelle), LHV/HHV-
Konventionen (h2data.de, EU-Eurostat, NAP), Faradaic-Effizienz-Literatur
(MDPI Energies 4792), Einheitskonverter (ionect).

Gefundene und behobene Fehler:

1. Z-FAKTOR (schwerwiegend): Registry-GUESS 1.10 @200 bar war zu niedrig.
   Virial-EOS mit NIST B(T)~15 cm3/mol gibt Z(200 bar, 20C) = 1.126,
   Z(300 bar) = 1.189. Bei 200 bar bedeutete die alte Konstante eine
   Massen-Fehlbias von ~2-3% in Route 2. BEHOBEN: gas_estimates/realgas.py,
   Z jetzt druck- und temperaturabhaengig; Restunsicherheit (~1%) in der
   Route-Unsicherheit konserviert. Tank-pV und Storage-Module umgestellt.

2. LHV-KONVENTION (0.1%): HTML 2.995 vs Pipeline 2.998 Wh/NL.
   Vereinheitlicht auf 2.998/3.542 Wh/NL (= 33.33/39.39 kWh/kg bei
   0.08988 kg/NL). Beide Tools jetzt konsistent; im Paper eine Konvention
   deklarieren (IEA: LHV = 33.3 kWh/kg, EU: 120.1 MJ/kg).

3. FLOW-EINHEITENFALLE (kritisch fuer Enapter-Daten): Der Flow-Detektor
   des HTML-Tools nimmt NL/min an. Enapter liefert NL/hour. Ein Export
   mit "NL/hour"-Header waere um Faktor 60 falsch in der Effizienz-Tabelle
   gelandet. Regex um NL/h-Erkennung erweitert + explizite Warnung im Code:
   Header mit /h muessen vor Nutzung umgerechnet oder der Header geprueft
   werden. Im report_cli (Python) ist die Einheit explizit (NL/h param).

4. Faradaic-Effizienz-Kontext (Literatur, MDPI): Shunt-Stroeme machen
   eta_F < 1; unsere 0.98-GUESS mit 2% Unsicherheit ist konservativ
   plausibel, bleibt aber GUESS bis Stack-Strom-Messung vorliegt.

Verifiziert korrekt (kein Handlungsbedarf):
- Faraday-Molmasse/Konstanten, Isotherme Verdichtungsarbeit, Trapez-
  Integration (JS+Python), Effizienz-Definitionen, Degradations-Fit,
  Kennwert-Extraktion, pV-Bilanz-Formalismus
