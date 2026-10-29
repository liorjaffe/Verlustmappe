# Sources and transferability

This file is the evidence index for externally sourced numeric inputs. A short source
description in `src/verlustmappe/registry.py` or another document is not a substitute for
the full entry required here.

## Current audit state

The existing registry contains source hints, but this repository does not yet have a
central, complete set of page/table references, short verbatim quotations, and
transferability assessments for every existing external number. Auditing and migrating
those existing entries is `BACKLOG`; do not infer missing citation details. Existing
registry values are not changed by this note.

CI checks that each newly added registry key is named in this file. A key's presence alone
does not establish that its source entry is complete or that the value is transferable.

## Entry format

### `<registry key>`

- **Value and unit:** `<exact registry value and unit>`
- **Source:** `<author/manufacturer, title, edition or publication date, URL/DOI>`
- **Location:** `<page, section, table, or figure>`
- **Verbatim quote:** `"<short exact excerpt supporting the value>"`
- **Source conditions:** `<pressure, temperature, load, drive type, boundary, etc.>`
- **Transferability:** `<same/different from this plant; explain relevant differences>`
- **Registry status and uncertainty:** `<status and uncertainty; explain the basis>`
- **Used by:** `<module/function and effect>`
- **Reviewer/date:** `<human reviewer and date>`

## New externally sourced entries

### F8 SolisCloud portal chart cadence (docs/03; D32)

- **Value and unit:** `300 s` minimum observed interval; nominal grid derived under D32(a), not a registry parameter.
- **Source:** SolisCloud portal, `data/raw/Daily+Power+Station+Chart_29-10-2026.xls`, owner-provided export; SHA-256 `754740b3eb2e8f119bfa1b200fa2f0ae2c66b872c28bdc3166d416281d742621`.
- **Location:** Sheet `Daily Power Station Chart_29-10`; metadata rows 1, 3-4; column headings row 29; data rows 30-191. The filename date is 29-10-2026; the sheet title identifies the chart date as 28/10/2026.
- **Verbatim quote:** `Plant_28/10/2026Chart`; `Plant:F8_Fachada Leste`; `Installed Capacity:12.780kWp`; headers `Number`, `Time`, `Working State`, `PV(W)`; time cells include `05:45:00`, `05:50:00`, `05:55:00`, `19:05:00`, and `19:25:00`. The 162 readings yield 160 intervals of 300 s and one interval of 1200 s.
- **Source conditions:** F8 station portal daily chart for 28-10-2026; station total, with no per-inverter serial-number breakdown.
- **Transferability:** Supports the 300-s nominal grid for the F8 portal daily chart and the docs/03 SolisCloud daily-PV source under D32. It does not assert that every Solis interface emits timestamps exactly on that grid; the `inverterDay` API history is a separate jitter observation. The quoted capacity figure is verbatim file content for provenance; the F8 nameplate capacity remains 12.74 kWp (28 x 455 W) per the registry, pending a separate owner decision on the discrepancy.
- **Registry status and uncertainty:** N/A (analysis property, not a registry value); basis `grid-derived` under D32(a). The official SolisCloud API documentation was checked 2026-10-29: no endpoint-specific resolution statement for `inverterDay`; its `dataTimestamp` field is described as `Update time`. The general statement `Device data upload frequency: 5 minutes` is not endpoint-specific and is not used as the basis. See SolisCloud Developer Platform, [Data Access API (User Auth)](https://developer.soliscloud.com/guide/data-access-user.html).
- **Used by:** docs/03 nominal-sampling table.
- **Reviewer/date:** owner approved 2026-10-29.

## P05 workbook v2 entries (2026-10-27)

All entries below are transcribed from the owner workbook `Compressor_System_Specs_Master_v2.xlsx`
(SHA-256 `0aa9f8ed0618d9bfd61123055674418969e0d7479d63b962afb18944cfd942ae`), Master and Sources
sheets. The workbook carries document and page only, no verbatim quotes. Every quote field is
`BACKLOG`: the owner supplies it from the original PDF/photo. Uncertainty 0.0 follows existing
datasheet entries; transfer risk is stated per entry. Pressures: convention assumed gauge (barg),
see open point P-2.

Open points: (P-1) Maximator / H2 Core Systems: conditions of the TDS air-consumption chart
(gas pressures, booster version, purge/control air, volume basis, continuous vs intermittent).
(P-3) Same inquiry: an older Maximator repair manual (drawings dated 1985/1996) lists lower maximum pressures for the base types (DLE 15: 150 bar, DLE 30: 300 bar, instead of 300/600 in the current catalog); which limits apply to part numbers 3630.3019 / 3630.2374 (installed 2021)? (P-2) Same inquiry: are pressures in the DLE tables gauge or absolute? If absolute, the status
of the affected keys changes by decision.

### `sys.n_rotex`
- **Value and unit:** `4` (-)
- **Source:** owner statement, Air Valve chat 2026-10-27 [S26]
- **Location:** workbook Master row 4
- **Verbatim quote:** BACKLOG (owner statement, no document)
- **Source conditions:** equal type, pressure and switching of all four not yet confirmed
- **Transferability:** same plant
- **Registry status and uncertainty:** OWNER_DECISION, 0.0
- **Used by:** none yet (registry input only)
- **Reviewer/date:** owner, pending

### `sys.p_h2_out_project_barg`
- **Value and unit:** `300` barg
- **Source:** owner decision, this chat 2026-10-27 [S26]
- **Location:** workbook Master row 5; D12
- **Verbatim quote:** BACKLOG (owner decision)
- **Source conditions:** project case 35 -> 300 barg; storage limit 300 bar
- **Transferability:** same plant; differs from `stor.p_work_barg` = 200 (legacy-1.0), see D12
- **Registry status and uncertainty:** OWNER_DECISION, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `sys.p_h2_out_nameplate_barg`
- **Value and unit:** `400` barg (workbook unit "bar", gauge assumed, P-2)
- **Source:** HULC system nameplate photos [S1]
- **Location:** workbook Master row 6
- **Verbatim quote:** "HULC Compressor system for compression of hydrogen from 35bar to 400bar" (nameplate field "Benennung/ Designation"; original spelling without space before "bar"; owner transcription 2026-10-28 from two photos, identical)
- **Source conditions:** system nameplate, not a storage fill permission
- **Transferability:** same plant
- **Registry status and uncertainty:** DATASHEET (nameplate), 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `sys.p_h2_in_barg`
- **Value and unit:** `35` barg
- **Source:** HydroHulc TDS [S5] and owner statement [S26]
- **Location:** TDS p.2; workbook Master row 7
- **Verbatim quote:** TDS `HydroHulc_TDS_0012_9A-2` p.2, table row "Inlet pressure", column "Hulc 140": "<=35 bar"; nameplate: "from 35bar to 400bar" (owner transcription 2026-10-28)
- **Source conditions:** dryer DRY 2.1 output up to 35 barg; equal to the Hulc 140 inlet limit (workbook statement)
- **Transferability:** same plant; gauge convention assumed (P-2)
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.mod.q_h2_max_nm3h`
- **Value and unit:** `5` Nm3/h (= 83.3 NL/min)
- **Source:** HydroHulc TDS [S5]
- **Location:** TDS p.2 module table; workbook Master row 75
- **Verbatim quote:** TDS p.2 table row "Mass flow H2": "up to 5 Nm³/h" (identical in all four columns); body text: "This configuration will provide a gas outlet flow of 5Nm³/h Hydrogen per hour." (owner transcription 2026-10-28)
- **Source conditions:** "up to"; conditions not stated
- **Transferability:** same product, conditions open; maximum, not an operating point
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.m140.limits`
- **Value and unit:** `140` barg (outlet limit only; inlet limit is `sys.p_h2_in_barg`)
- **Source:** HydroHulc TDS [S5]
- **Location:** TDS p.2; workbook Master row 77
- **Verbatim quote:** TDS p.2, column "Hulc 140": row "Pressure class" "up to 140 bar"; row "Inlet pressure" "<=35 bar" (columns are positional in the extracted table; owner transcription 2026-10-28)
- **Source conditions:** module limit
- **Transferability:** same product; gauge assumed (P-2)
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.m400.limits`
- **Value and unit:** `400` barg (outlet limit only)
- **Source:** HydroHulc TDS [S5]
- **Location:** TDS p.2; workbook Master row 78
- **Verbatim quote:** TDS p.2, column "Hulc 400": row "Pressure class" "up to 400 bar"; row "Inlet pressure" "<=140 bar" (columns are positional in the extracted table; owner transcription 2026-10-28)
- **Source conditions:** module limit
- **Transferability:** same product; gauge assumed (P-2)
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.pl_max_barg`
- **Value and unit:** `10` barg (upper end of "1 - 10 bar", a range, not a setpoint)
- **Source:** Maximator gas boosters catalog [S7]
- **Location:** workbook Master row 108; catalog pages per Sources sheet (p.7-8, 16-19, 28-29)
- **Verbatim quote:** Maximator catalog p.16 (also p.18, "DLE...-2" section), list item above the base-type table: "Suitable for air drive pressures (pL) from 1 to 10 bar (14.5 to 145 psi)"; DLE 15 datasheet DB 01.02.02.02 p.1: "Air drive pressure pL: 1-10 bar / 14,5 - 145psi"; DLE 30 datasheet DB-01.02.02.26 p.1: "Air drive pressure pL: 1 - 10 bar / 14.5 - 145 psi" (owner transcription 2026-10-28)
- **Source conditions:** drive air pressure range
- **Transferability:** catalog value of the base type; gauge assumed (P-2); lower end (1 bar) not registered. Type-related permitted range, not a setpoint: DLE manual Tab. 3-4 leaves "Drive pressure pL" empty with footnote "a. Dependent on the gas booster design. Refer to the general drawing provided or rating plate."
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.s1.i`
- **Value and unit:** `15` (ratio 1:15)
- **Source:** Maximator catalog [S7], datasheet DLE 15 [S8]
- **Location:** workbook Master row 86
- **Verbatim quote:** Maximator catalog "Maximator Gas boosters EN" p.16, section "DLE... single stage, double acting, 1 air drive section", row "DLE 15", column "Pressure ratio i": "1:15"; DLE 15 datasheet: "Pressure ratio i: 1:15" (owner transcription 2026-10-28)
- **Source conditions:** DLE 15 base type
- **Transferability:** (base type) transfer to -H2, not verified against the -H2 datasheet
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.s1.v_disp_cm3`
- **Value and unit:** `244` cm3
- **Source:** [S7], [S8]
- **Location:** workbook Master row 87
- **Verbatim quote:** Maximator catalog "Maximator Gas boosters EN" p.16, section "DLE... single stage, double acting, 1 air drive section", row "DLE 15", column "Stroke volume** [cm³]": "244" (footnote: "Calculated stroke volume"); datasheet: "Displacement volume/double stroke: 244cm³" (owner transcription 2026-10-28)
- **Source conditions:** geometric, calculated by Maximator
- **Transferability:** (base type) transfer to -H2, not verified against the -H2 datasheet
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.s1.f_max_min`
- **Value and unit:** `120` 1/min
- **Source:** DLE 15 datasheet [S8]
- **Location:** workbook Master row 88
- **Verbatim quote:** DLE 15 datasheet, "Technical Data": "Maximum cycles: 120 / min" (owner transcription 2026-10-28)
- **Source conditions:** maximum cycle rate, base type
- **Transferability:** (base type) transfer to -H2, not verified against the -H2 datasheet
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.s1.pa_min_barg`
- **Value and unit:** `7` barg (workbook "7 / 300 bar": minimum gas inlet pressure; the 300 is not registered)
- **Source:** [S7]
- **Location:** workbook Master row 89
- **Verbatim quote:** Maximator catalog "Maximator Gas boosters EN" p.16, section "DLE... single stage, double acting, 1 air drive section", row "DLE 15", column "min. gas inlet pressure pAmin [bar]": "7" (psi: "102"); datasheet: "Minimum suction pressure pA: 7" (owner transcription 2026-10-28)
- **Source conditions:** base type
- **Transferability:** (base type) transfer to -H2, not verified against the -H2 datasheet; gauge assumed (P-2)
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.s1.pb_max_barg`
- **Value and unit:** `300` barg
- **Source:** [S7]
- **Location:** workbook Master row 90
- **Verbatim quote:** Maximator catalog "Maximator Gas boosters EN" p.16, section "DLE... single stage, double acting, 1 air drive section", row "DLE 15", column "max. working pressure pB*** [bar]": "300" (psi: "4350"); footnote: "Maximum permissible static working pressure"; datasheet: "Maximum outlet pressure pB: 300 bar" (owner transcription 2026-10-28)
- **Source conditions:** base-type limit; the module limits stage 1 to 140 bar
- **Transferability:** (base type) transfer to -H2, not verified against the -H2 datasheet; gauge assumed (P-2)
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.s2.i`
- **Value and unit:** `30` (ratio 1:30)
- **Source:** [S7], DLE 30 datasheet [S9]
- **Location:** workbook Master row 97
- **Verbatim quote:** Maximator catalog "Maximator Gas boosters EN" p.16, section "DLE... single stage, double acting, 1 air drive section", row "DLE 30", column "Pressure ratio i": "1:30"; DLE 30 datasheet: "Pressure ratio i: 1:30" (owner transcription 2026-10-28)
- **Source conditions:** DLE 30 base type
- **Transferability:** (base type) transfer to -H2, not verified against the -H2 datasheet
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.s2.v_disp_cm3`
- **Value and unit:** `120` cm3
- **Source:** [S7], [S9]
- **Location:** workbook Master row 98
- **Verbatim quote:** Maximator catalog "Maximator Gas boosters EN" p.16, section "DLE... single stage, double acting, 1 air drive section", row "DLE 30", column "Stroke volume** [cm³]": "120" (in³: "7,3"); datasheet: "Displacement volume/double stroke: 120 cm³ 7.3 in³" (owner transcription 2026-10-28)
- **Source conditions:** base type
- **Transferability:** (base type) transfer to -H2, not verified against the -H2 datasheet
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.s2.f_max_min`
- **Value and unit:** `120` 1/min
- **Source:** DLE 30 datasheet [S9]
- **Location:** workbook Master row 99
- **Verbatim quote:** DLE 30 datasheet, "Technical Data": "Maximum cycles: 120 / min" (owner transcription 2026-10-28)
- **Source conditions:** maximum cycle rate, base type
- **Transferability:** (base type) transfer to -H2, not verified against the -H2 datasheet
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.s2.pa_min_barg`
- **Value and unit:** `15` barg (workbook "15 / 600 bar": minimum gas inlet pressure)
- **Source:** [S7], [S9]
- **Location:** workbook Master row 100
- **Verbatim quote:** Maximator catalog "Maximator Gas boosters EN" p.16, section "DLE... single stage, double acting, 1 air drive section", row "DLE 30", column "min. gas inlet pressure pAmin [bar]": "15" (psi: "218"); datasheet: "Minimum suction pressure pA: 15 bar / 220 psi" (owner transcription 2026-10-28)
- **Source conditions:** base type
- **Transferability:** (base type) transfer to -H2, not verified against the -H2 datasheet; gauge assumed (P-2)
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `hulc.s2.pb_max_barg`
- **Value and unit:** `600` barg
- **Source:** [S7]
- **Location:** workbook Master row 101
- **Verbatim quote:** Maximator catalog "Maximator Gas boosters EN" p.16, section "DLE... single stage, double acting, 1 air drive section", row "DLE 30", column "max. working pressure pB*** [bar]": "600" (psi: "8700"); footnote: "Maximum permissible static working pressure"; datasheet: "Maximum outlet pressure pB: 600 bar / 8700 psi" (owner transcription 2026-10-28)
- **Source conditions:** base-type limit; the module limits stage 2 to 400 bar
- **Transferability:** (base type) transfer to -H2, not verified against the -H2 datasheet; gauge assumed (P-2)
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `kaeser.p_rated_nameplate_kw`
- **Value and unit:** `5.85` kW (workbook text "5.5 + 0.35 kW")
- **Source:** Kaeser SXC 8 nameplate photo [S10]
- **Location:** workbook Master row 19
- **Verbatim quote:** nameplate field "Bemessungsleistung 5,5 + 0,35 kW" (SXC 8, Material-Nr. 100692.11); the nameplate does not say what the 0,35 kW belong to (owner transcription 2026-10-28)
- **Source conditions:** assignment of the 0.35 kW is not documented; the sum is the registered value
- **Transferability:** same plant; the sum is an owner reading, to be confirmed
- **Registry status and uncertainty:** DATASHEET (nameplate), 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `kaeser.ps_barg`
- **Value and unit:** `11` barg
- **Source:** Kaeser nameplate photo [S10]
- **Location:** workbook Master row 35
- **Verbatim quote:** nameplate field "Max. Betriebsüberdruck PS 11,00 bar" (limit, not an operating point) (owner transcription 2026-10-28)
- **Source conditions:** nameplate pressure; observed line pressure is 8.1 bar (not registered)
- **Transferability:** same plant; gauge assumed (P-2)
- **Registry status and uncertainty:** DATASHEET (nameplate), 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `kaeser.q_fad_m3min`
- **Value and unit:** `0.67` m3/min FAD
- **Source:** Kaeser SXC compact brochure P-651/26D [S15]
- **Location:** workbook Master row 36
- **Verbatim quote:** Kaeser brochure P-651/26D (.10/24), technical data table (PDF p.6/7), row "SXC 8": "SXC 8 | 10 | 0,67 | 11 | 5,5 | CT 8 | +6 | 0,2 | 215 | 620 x 980 x 1480 | 69 | 300" (columns: Betriebsüberdruck 10, Volumenstrom Gesamtanlage 0,67, max. Überdruck 11); footnote: "*) Volumenstrom Gesamtanlage nach ISO 1217: 2009, Annex C/E, Ansaugdruck 1 bar (abs), Kühl- und Luftansaugtemperatur + 20 °C" (owner transcription 2026-10-28)
- **Source conditions:** 10 bar working pressure, 11 bar version, ISO 1217:2009 Annex C/E, inlet 1 bar abs, 20 degC
- **Transferability:** same type; ISO 1217 tolerance not stated; dealer lists the same flow at 11 bar
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `kaeser.p_package_dealer_kw`
- **Value and unit:** `6.2` kW
- **Source:** dealer listing 100692.11 [S16]
- **Location:** workbook Master row 28
- **Verbatim quote:** dealer listing (grobmotorik.org, "Schraubenkompressor Sxc 8 | 100692.11"): "Elektr. Leistungsaufnahme der Gesamtanlage bei 11,0 bar: 6,2 kW"; same listing: "Volumenstrom bei 11,0 bar: 0,67 m³/min (670 l/min.)"; "Ausführung mit SIGMA CONTROL Basic"; "Kältetrockner 0,28 kW" (owner transcription 2026-10-28)
- **Source conditions:** at 11 bar; dryer inclusion not stated. CONFLICT: the same listing gives 0.67 m3/min at 11 bar, the manufacturer gives 0.67 at 10 bar
- **Transferability:** secondary source with a known conflict; replace by measurement (SC2 kWh counter). Dealer attributes 0.67 m3/min and 6.2 kW both to 11.0 bar, manufacturer attributes 0.67 m3/min to 10 bar working pressure (11 bar = max. overpressure). Dealer controller variant ("SIGMA CONTROL Basic") conflicts with the installed SC2 (option C48, MCSIO); the photo governs. Inclusion of the refrigeration dryer in 6.2 kW not stated
- **Registry status and uncertainty:** DATASHEET_SECONDARY, 0.0 (uncertainty to be set by owner)
- **Used by:** none yet; basis of the derived Kaeser energy figure, which is workbook-only
- **Reviewer/date:** owner, pending