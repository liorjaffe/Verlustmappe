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

No new numeric source entries were added as part of the agent-governance setup.

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
- **Verbatim quote:** BACKLOG
- **Source conditions:** drive air pressure range
- **Transferability:** catalog value of the base type; gauge assumed (P-2); lower end (1 bar) not registered
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
- **Verbatim quote:** BACKLOG
- **Source conditions:** assignment of the 0.35 kW is not documented; the sum is the registered value
- **Transferability:** same plant; the sum is an owner reading, to be confirmed
- **Registry status and uncertainty:** DATASHEET (nameplate), 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `kaeser.ps_barg`
- **Value and unit:** `11` barg
- **Source:** Kaeser nameplate photo [S10]
- **Location:** workbook Master row 35
- **Verbatim quote:** BACKLOG
- **Source conditions:** nameplate pressure; observed line pressure is 8.1 bar (not registered)
- **Transferability:** same plant; gauge assumed (P-2)
- **Registry status and uncertainty:** DATASHEET (nameplate), 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `kaeser.q_fad_m3min`
- **Value and unit:** `0.67` m3/min FAD
- **Source:** Kaeser SXC compact brochure P-651/26D [S15]
- **Location:** workbook Master row 36
- **Verbatim quote:** BACKLOG
- **Source conditions:** 10 bar working pressure, 11 bar version, ISO 1217:2009 Annex C/E, inlet 1 bar abs, 20 degC
- **Transferability:** same type; ISO 1217 tolerance not stated; dealer lists the same flow at 11 bar
- **Registry status and uncertainty:** DATASHEET, 0.0
- **Used by:** none yet
- **Reviewer/date:** owner, pending

### `kaeser.p_package_dealer_kw`
- **Value and unit:** `6.2` kW
- **Source:** dealer listing 100692.11 [S16]
- **Location:** workbook Master row 28
- **Verbatim quote:** BACKLOG
- **Source conditions:** at 11 bar; dryer inclusion not stated. CONFLICT: the same listing gives 0.67 m3/min at 11 bar, the manufacturer gives 0.67 at 10 bar
- **Transferability:** secondary source with a known conflict; replace by measurement (SC2 kWh counter)
- **Registry status and uncertainty:** DATASHEET_SECONDARY, 0.0 (uncertainty to be set by owner)
- **Used by:** none yet; basis of the derived Kaeser energy figure, which is workbook-only
- **Reviewer/date:** owner, pending