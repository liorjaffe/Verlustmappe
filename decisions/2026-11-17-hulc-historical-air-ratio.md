# 2026-11-17 - Historical HULC air ratio

The owner approved clarifying CONTRACT section 6: the 14.6 Nm3 air per
Nm3 H2 is a historical estimate for the former 5 Nm3/h example, not a
general factor or an operating limit. The origin of its addends 390 and
825 NL/min is unclear. This does not establish a manufacturer value,
curve applicability, supply sufficiency or a new runtime parameter.

The owner explicitly clarified that retaining this historical comparison is
provisional and UNVERIFIED, not approval of 14.6 as physical truth or as an
input to the plant calculation. No runtime constant, default or fallback is
introduced. Its literal in the historical workbook regression documents a
past calculation only; passing that test does not validate the ratio.
Reassess the comparison when better evidence is available and during the
later overall-system review. A revision requires explicit review of affected
documentation and tests, not preservation of the historical assumption as truth.

Evidence at the time of the initial clarification: compressor workbook
Master rows 131-132, SHA-256
`c5585d5f4e6b73458c524106cdbc5b8002b67d57c1139220a9a704d30f1f1218`;
`plant/h2_compressor.toml` [layer1_evidence] distinguishes the historical
estimate from interpolation of the recorded points.
The subsequent approved migration-text batch is in the current workbook,
SHA-256 `07b082dbacf00dc6b9332d3d7ce0f262041003bdf3913cce0dacedad07a33145`;
it explicitly records the unclear origin of the historical addends.
