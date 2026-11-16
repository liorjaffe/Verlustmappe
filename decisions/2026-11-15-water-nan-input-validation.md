# 2026-11-15 - Reject NaN water-model inputs

## Owner decision

Reject NaN and infinite values for water-model inputs instead of treating NaN
hydrogen production as an absent value and silently using the nominal-water
fallback. The owner confirmed this stricter behavior on 2026-11-15.

## Evidence and scope

Repository search found no caller intentionally passing NaN as a signal to
request the fallback. This does not establish that runtime data can never
contain NaN, for example from missing time-series samples; such callers remain
unverified. Existing tests did not cover NaN input behavior before the new
validation tests were added.

This decision covers input validation only. It does not decide the separate
nominal-fallback policy or change how callers should handle missing samples.
