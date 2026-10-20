
## Status nach voller Integration (Pipeline-Seite)

Phase 1  Kennwerte/IV:        FERTIG (analysis/polarization.py, report_cli)
Phase 3  Effizienz-Erweiter.: FERTIG (efficiency_vs_temperature, g-Umrechnung)
Phase 4  Dynamik-Erweiter.:   FERTIG (ramp_rates, max slew)
Phase 5  Start/Stop-Energie:  FERTIG (start_stop_cycles mit Wh je Phase)
Phase 6  Purge-Recovery:      FERTIG (recovery_after_purges: Dip + Zeit bis 1%-Toleranz)
Phase 8  Degradation:         FERTIG (mV/h, %/h, Lifetime-to-X%)
Phase 10 Referenz-Abweichung: FERTIG (deviation_from_reference, 2%-Band)
Phase 11 Relative Diff:       FERTIG (relative_diff)
Phase 7  Zellbilanz:          bleibt im HTML-Tool (keine Zellkanäle in Telemetrie)
Phase 12 Live-Feed:           bleibt im HTML-Tool (server.py/simulate_data.py integriert)
Phase 13 Events:              FERTIG, kanonisch in Pipeline (event_analysis.py)

Offene Datenabhängigkeiten (nicht Code-Lücken):
- Zellflaeche/Stapelgewicht fuer A/cm^2 und W/kg: manuelle Eingabe, Registry-BACKLOG
- Referenz-IV-Kurve: entsteht aus dem ersten sauberen Kennlinien-Tag
- Degradation benoetigt mehrere Sessions mit Betriebsstunden
