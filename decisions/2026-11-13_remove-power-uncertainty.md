# 2026-11-13 - Remove power uncertainty from the Faraday route

The owner approves the following changes:

1. Remove `meas.power_rel_unc`, which is not an uncertainty of the stack-current
   measurement used by the Faraday route. Keep the Faraday production and consumption
   formulas unchanged.
2. Report the Faraday `uncertainty_rel` as `None` and mark it incomplete until a sourced
   stack-current uncertainty is explicitly wired with owner approval. Do not calculate a
   partial quadrature as if it were the route's total uncertainty.
3. Add `meas.current_rel_unc` to `plant/system.toml` as `BACKLOG`, without a value. It is
   only a candidate input; do not wire it into a calculation until sourced and approved.
4. Route agreement statistics require at least two complete routes in the same quantity
   group. Incomplete routes do not contribute to weighting or numeric residual uncertainty.
   The production-minus-delivered amount and fraction remain visible; its uncertainty is
   `None` while either route's uncertainty is incomplete.
5. Name production minus delivered `production_minus_delivered_residual`. It is diagnostic
   only; purge, vent and leakage are possible causes, not findings, and the residual is
   never booked as a loss.

The registry snapshot is regenerated from the loaded plant registry; the total key count
remains 109 because one parameter is replaced by one BACKLOG key.
