# 2026-11-19 - EL nameplate: 35 barg version confirmed

## Owner approval

The owner photographed the nameplate of an installed EL 2.1 (19 Nov 2026 16:07, image
20261119_160707 in the owner library, S/N AA21122322SP1, 'Prod. Wk 51', cooling air) and
asked to work its information into the EL workbook and `plant/el.toml`.

- Pressure version: 'H2 OUTPUT PRESSURE 3.5 MPa' confirms the 35 barg version (workbook
  Notes 3 resolved). One unit photographed; the other eight are assumed identical.
- `el.output_pressure_barg`: value 35, status DATASHEET unchanged; source names the
  nameplate; effect now says device maximum, operating pressure regulated downstream and a
  case input or measurement. No code reads this key (no result effect).
- `el.h2_purity`: value and status unchanged; source names the nameplate and the confirmed
  version.
- Workbook (file name kept): Overview B2, EL rows 4, 26, 27, 29, 34, 40, Sources No. 13,
  Notes 3 and new Notes 14. SHA-256 before 4e8cf427..., final 84efda9f...

## Photo check

The owner then supplied the photo; the agent read it directly. All transcribed values
match (S/N partly cut at the top edge but legible). Additionally on the nameplate: WATER
INPUT PRESSURE 0.1-0.4 MPa (workbook row 34). The nameplate labels the power 'RATED POWER'.

## Not taken over from the external transcription

- '3.5 MPa = 35 bar ~ 34.8 barg' is wrong arithmetic (35 bar absolute would be about
  34.0 barg). The nameplate has no gauge/absolute marking; the datasheet states 'Up to
  35 barg' and the owner confirms barg (2026-11-19), so the value is taken as 35 barg.
- A production year 2021 is not on the transcription ('Prod. Wk 51' only); not recorded.
- 'Fits battery limits Rev. 05' is not supported: that revision states the serial range
  ELE2105XXA2ASV03 to ...XX, the nameplate S/N has a different format (Notes 14 b).

## Open

- Actual operating pressure; photo not in the repository.
- Overview A2 ('State: 30 Sep 2026') still conflicts with B2; separate workbook clean-up.
