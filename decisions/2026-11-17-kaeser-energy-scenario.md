# 2026-11-17 - Separate Kaeser energy scenario

The owner prefers leaving unverified Kaeser/HULC electrical energy MISSING in
the ledger while also preparing a separately labelled provisional scenario.
This keeps a hypothetical estimate distinct from both a measured value and
the ledger result.

The owner approved a hypothetical air-volume-related scenario, not an
allocation of actual consumption. Its single calculation is
reference power x time x HULC chart air flow / nominal air delivery.
The assumed one-hour reference uses dealer power 6.2 kW at 11 bar and
manufacturer delivery 0.67 m3/min at 10 bar, converted conditionally to
about 616 NL/min. The pressure conflict, reference-volume assumptions and
dryer inclusion remain open. Nominal capacity is not measured total air flow.

At two EL x 500 NL/h, adjacent chart readings yield about 550 NL/min and
5.5 kWh; the older sparse chart anchors yield about 563.3 NL/min and
5.7 kWh. Both are graphical approximations under the same other assumptions;
the selected basis must accompany the result. The estimate does not establish
actual input power, other consumption or a physical bound. READY, network
leakage, Rotex, other consumers and startup are outside this calculation,
not measured as zero. It does not demonstrate sufficient supply.

Return no numerical result when demand exceeds nominal delivery, and do not
extrapolate below 10 NL/min H2 or outside the supplied chart range. These are
scenario calculation guards, not confirmed physical plant limits. Never pass
this value to the HULC measured-energy path or substitute it for missing ledger
energy. This decision does not change the REJECTED legacy fallback.

The owner approved a separate architecture step after workbook integration:
supported dry FAD conversion belongs in devices/kaeser.py; HULC interpolation,
the explicit module-addition assumption and both hard guards belong in
devices/h2_compressor.py. Scenario composition belongs in scenarios/kaeser.py,
not accounting: the existing accounting-to-device import ban stays unchanged.
The owner approved adding only "scenarios" to the package list in
tests/test_structure.py, plus a separate reverse-direction import guard:
accounting (including ledger) must not import scenarios.
Report must reject scenario objects and computed compression values while
the canonical compression basis remains unresolved. This API guard prevents
booking by relabelling; it is not a physical validation or a security boundary.

After the architecture commit, the owner deferred assessment of chart
applicability, module addition, reference-volume compatibility and actual
Kaeser consumption until the work is substantially complete and can be
reviewed in the overall-system context. Independent work may continue.
This is a scheduling decision, not approval of those assumptions or a change
to accounting rules: compression energy remains MISSING, the scenario remains
UNVERIFIED and all booking guards stay in place. Revisit these questions during
that overall assessment and before adopting any productive compression result.

The owner clarified that these provisional working assumptions are revisable,
not established plant truths. Source identity pins and historical regressions
preserve traceability, not physical validity. Better evidence may justify
reviewed changes to assumptions, inputs and model choices; the current scenario
must not silently become a runtime default or an accepted plant-energy model.

Following the critical review, the owner approved rejecting mutable curve
containers to preserve result provenance, resolving the reverse import guard
against each file's actual package (including nested package initializers),
and naming the existing linear scenario assumption in the result notes.
No monotonic-air-value guard or new physical constraint is adopted.

The owner separately approved replacing exactly two scenario energy test
references with independent Fraction derivations: (31/5)*550/(616126/1000)
and (31/5)*(1690/3)/(616126/1000) kWh. These deliberately use the rounded
fixture nominal 616.126 NL/min, not the full registry conversion
616.1259440673... NL/min. Absolute comparison tolerance 1e-12 kWh, relative
tolerance zero, covers floating-point arithmetic only, not physical uncertainty.
All other existing expected test values remain unchanged.

The legacy booster window-quantity clip without a visible result note is
recorded as an open result-impact finding, not repaired in this review task.
