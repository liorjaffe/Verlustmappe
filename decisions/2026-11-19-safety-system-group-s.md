# 2026-11-19 - H2 safety system as account S (prepared)

## Owner approval

1. The H2 safety system is brought into scope as a separate group **S**: room ventilation
   (CELAB), H2 sensors and the four Rotex. `CONTRACT.md` §2 no longer excludes ventilation
   and gas detection; §4 defines S.
2. S is shown separately from B, so B stays the production-related auxiliary consumption.
   S is supplied via the PMS like everything else (island assumption,
   `2026-11-19-island-supply-via-pms.md`).
3. Prepared only: no calculation, model module or case input until the owner releases it.
4. Ventilation: the owner will measure it directly; the result is to be used as a constant
   consumption. H2 sensors: details follow from the owner.
5. The four Rotex move from "not assessed" in the Kaeser context to S. Their air share of
   the Kaeser (D14) belongs to S; they stay not assessed until the owner clarifies them.

## Changes

- `CONTRACT.md` §2 (scope) and §4 (account S).
- New files `plant/ventilation.toml` and `plant/h2_sensors.toml`: skeletons with title and
  open items only, no parameters (rule 11: S needs a place for the owner's measurement and
  sensor details; the observer and device-progress view read plant files by name).
- Observer: S frame with ventilation, H2 sensors and Rotex; faded taps from the PMS
  auxiliary line; S card in the energy-flow view, excluded from B.

## Open

- S's share of the shared supply losses and whether or how S enters C.
- Rotex role; H2 sensor details; ventilation measurement method and result.
