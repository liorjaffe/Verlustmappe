"""Independent hand calculation for P13 (integration D24). Stdlib only.

Imports nothing from `verlustmappe` and reads no legacy output (hand README rules 1 and 3).
Every case is computed here segment by segment from the definition in tasks/P13; the
expected values are also written out by hand in integration.md and asserted below.
Run: python3 tests/reference/hand/p13_hand_calc.py

Integral unit: y-unit * s (power in W gives J; kWh = J / 3.6e6, done by the caller).
"""
import math

FACTOR = 3.0        # D24: gap limit = max(FACTOR * nominal_dt_s, MAX_GAP_S)
MAX_GAP_S = 30.0    # D24 (legacy continuity value)


def gap_limit_s(nominal_dt_s):
    return max(FACTOR * nominal_dt_s, MAX_GAP_S)


def _result(valid, reason, value=None, covered_fraction=None, n_gaps=None, n_dropped=None):
    """One shape for every branch: all keys always present, not computable fields are None."""
    return dict(valid=valid, reason=reason, value=value, covered_fraction=covered_fraction,
                n_gaps=n_gaps, n_dropped=n_dropped)


def hand_integral(t, y, nominal_dt_s):
    """Reference procedure.
    1. Samples with a non-finite TIMESTAMP are dropped (counted in n_dropped); a NaN timestamp
       is a different problem from a NaN value but is handled the same way and reported the same
       way. The remaining timestamps define the window: span = t_last - t_first, also when the
       edge samples have non-finite values.
    2. Time must be non-decreasing over those samples (else INVALID).
    3. Samples with a non-finite VALUE are dropped (counted) before the segment walk; a
       timestamp that repeats with a different value is INVALID.
    4. Segments between the remaining samples: dt > limit is a gap, else trapezoid.
    Reasons: "no valid samples" = fewer than two finite samples remain; "no covered segment" =
    samples exist but no segment with positive time below the gap limit.
    Result keys always: valid, reason, value, covered_fraction, n_gaps, n_dropped (None where
    not computable)."""
    stamped = [(a, b) for a, b in zip(t, y) if math.isfinite(a)]
    n_bad_time = len(t) - len(stamped)
    for (t0, _), (t1, _) in zip(stamped, stamped[1:]):
        if t1 < t0:
            return _result(False, "non-monotonic time", n_dropped=n_bad_time)
    pts = [(a, b) for a, b in stamped if math.isfinite(b)]
    n_dropped = len(t) - len(pts)
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        if t1 == t0 and y1 != y0:
            return _result(False, "duplicate timestamp with conflicting values",
                           n_dropped=n_dropped)
    if len(pts) < 2:
        return _result(False, "no valid samples", n_dropped=n_dropped)
    lim = gap_limit_s(nominal_dt_s)
    value = covered = 0.0
    n_gaps = 0
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        dt = t1 - t0
        if dt > lim:
            n_gaps += 1
            continue
        value += 0.5 * (y0 + y1) * dt
        covered += dt
    if covered <= 0.0:
        return _result(False, "no covered segment", n_gaps=n_gaps, n_dropped=n_dropped)
    span = stamped[-1][0] - stamped[0][0]
    return _result(True, "", value, covered / span, n_gaps, n_dropped)


def nonneg_verdict(value):
    """check_nonnegative reference (D31, three-way): True / False for finite numbers,
    'ValueError' for non-finite values or a non-number (caller error)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "ValueError"
    if not math.isfinite(value):
        return "ValueError"
    return value >= 0.0


def near(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(b))


def main():
    print("gap limits: nominal 60 ->", gap_limit_s(60), "s; nominal 1 ->", gap_limit_s(1),
          "s; nominal 20 ->", gap_limit_s(20), "s")
    assert gap_limit_s(60) == 180.0 and gap_limit_s(1) == 30.0 and gap_limit_s(20) == 60.0

    # A constant series: 1000 W for 300 s, 60 s sampling
    r = hand_integral([0, 60, 120, 180, 240, 300], [1000.0] * 6, 60)
    print("A constant:", r)
    assert r["value"] == 300000.0 and r["covered_fraction"] == 1.0 and r["n_gaps"] == 0

    # B ramp 0 -> 3000 W over 3600 s, 60 s sampling (61 samples): analytic 0.5*3000*3600
    t = [60 * i for i in range(61)]
    y = [3000.0 * ti / 3600.0 for ti in t]
    r = hand_integral(t, y, 60)
    exact_J = 0.5 * 3000.0 * 3600.0
    rect_J = sum(y[i] * 60.0 for i in range(60))       # forward rectangles (legacy style)
    print("B ramp: trapezoid", r["value"] / 3.6e6, "kWh; analytic", exact_J / 3.6e6,
          "kWh; forward rectangles", rect_J / 3.6e6, "kWh; deviation", (exact_J - rect_J) / rect_J)
    assert near(r["value"], 5.4e6) and near(rect_J, 5.31e6)
    assert near(r["value"] / 3.6e6, 1.5) and near(rect_J / 3.6e6, 1.475)
    assert near((exact_J - rect_J) / rect_J, 0.09 / 5.31)      # 1.695 %

    # C gap: 1000 W, samples 0, 60, 120, then 600, 660, 720 (gap 480 s > 180 s)
    r = hand_integral([0, 60, 120, 600, 660, 720], [1000.0] * 6, 60)
    print("C gap:", r)
    assert r["value"] == 240000.0 and near(r["covered_fraction"], 1 / 3) and r["n_gaps"] == 1

    # D NaN stretch, boundary: nan at 120, 180 -> 60 -> 240 is dt = 180 = limit, NOT a gap
    t = [0, 60, 120, 180, 240, 300]
    y = [1000.0, 1000.0, float("nan"), float("nan"), 2000.0, 2000.0]
    r = hand_integral(t, y, 60)
    print("D nan boundary:", r)
    assert r["value"] == 450000.0 and r["covered_fraction"] == 1.0
    assert r["n_gaps"] == 0 and r["n_dropped"] == 2

    # D2 NaN stretch one sample longer: 60 -> 300 is dt = 240 > 180, a gap
    y = [1000.0, 1000.0, float("nan"), float("nan"), float("nan"), 2000.0]
    r = hand_integral(t, y, 60)
    print("D2 nan gap:", r)
    assert r["value"] == 60000.0 and near(r["covered_fraction"], 60 / 300)
    assert r["n_gaps"] == 1 and r["n_dropped"] == 3

    # E limit with nominal 1 s: limit 30 s; dt = 30 passes, dt = 31 is a gap
    r = hand_integral([0, 30, 61], [100.0] * 3, 1)
    print("E nominal 1 s:", r)
    assert r["value"] == 3000.0 and near(r["covered_fraction"], 30 / 61) and r["n_gaps"] == 1
    # E2 nominal 20 s: limit 60 s (3 x 20 > 30); dt = 60 passes, dt = 61 is a gap
    r = hand_integral([0, 60, 121], [100.0] * 3, 20)
    print("E2 nominal 20 s:", r)
    assert r["value"] == 6000.0 and r["n_gaps"] == 1

    # F two samples ramp, and single sample
    r = hand_integral([0, 60], [0.0, 600.0], 60)
    print("F two samples:", r)
    assert r["value"] == 18000.0 and r["covered_fraction"] == 1.0
    r = hand_integral([0], [5.0], 60)
    print("F single sample:", r)
    assert not r["valid"] and r["reason"] == "no valid samples" and r["value"] is None

    # G duplicate timestamp with equal values: weight zero, allowed
    r = hand_integral([0, 60, 60, 120], [1000.0] * 4, 60)
    print("G equal duplicate:", r)
    assert r["value"] == 120000.0 and r["covered_fraction"] == 1.0
    # G2 duplicate timestamp with conflicting values: INVALID
    r = hand_integral([0, 60, 60, 120], [1000.0, 1000.0, 2000.0, 2000.0], 60)
    print("G2 conflicting duplicate:", r)
    assert not r["valid"] and r["reason"] == "duplicate timestamp with conflicting values"

    # J NaN at both edges: the span still runs over the edge timestamps (0..300), the valid
    # samples 60..240 give 3 segments = 180 s -> 0.6 (a span over the valid samples only: 1.0)
    nan = float("nan")
    r = hand_integral([0, 60, 120, 180, 240, 300], [nan, 1000.0, 1000.0, 1000.0, 1000.0, nan], 60)
    print("J nan at edges:", r)
    assert r["value"] == 180000.0 and near(r["covered_fraction"], 0.6) and r["n_dropped"] == 2
    # J1 first sample non-finite value: span 0..120 = 120 s, covered 60..120 = 60 s -> 0.5
    # (a span over the remaining samples would show 1.0 although the first half is unmeasured)
    r = hand_integral([0, 60, 120], [nan, 1000.0, 1000.0], 60)
    print("J1 nan first:", r)
    assert r["value"] == 60000.0 and near(r["covered_fraction"], 0.5) and r["n_dropped"] == 1
    # J2 non-finite timestamp: the sample is dropped and does not stretch the span
    r = hand_integral([0, 60, nan, 120], [1000.0] * 4, 60)
    print("J2 nan timestamp:", r)
    assert r["value"] == 120000.0 and r["covered_fraction"] == 1.0 and r["n_dropped"] == 1

    # K only duplicates: every dt = 0, equal values -> no segment with positive time
    r = hand_integral([0, 0, 0], [5.0, 5.0, 5.0], 60)
    print("K only duplicates:", r)
    assert not r["valid"] and r["reason"] == "no covered segment" and r["value"] is None

    # H non-monotonic time
    r = hand_integral([0, 60, 30], [1.0, 1.0, 1.0], 60)
    print("H non-monotonic:", r)
    assert not r["valid"] and r["reason"] == "non-monotonic time" and r["value"] is None
    assert r["n_gaps"] is None and r["covered_fraction"] is None

    # I zero coverage: every interval is a gap -> INVALID, never 0
    r = hand_integral([0, 1000, 2000], [100.0] * 3, 60)
    print("I zero coverage:", r)
    assert not r["valid"] and r["reason"] == "no covered segment" and r["value"] is None
    assert r["n_gaps"] == 2 and r["covered_fraction"] is None
    # I2 all samples non-finite
    r = hand_integral([0, 60, 120], [float("nan")] * 3, 60)
    print("I2 all non-finite:", r)
    assert not r["valid"] and r["reason"] == "no valid samples" and r["n_dropped"] == 3

    # L check_nonnegative (D31, three-way): False for negative, ValueError for non-finite or type
    inf = float("inf")
    assert nonneg_verdict(0.0) is True and nonneg_verdict(3.5) is True
    assert nonneg_verdict(-0.001) is False and nonneg_verdict(-1e-300) is False
    for bad in (nan, inf, -inf, "1.0", None, True):
        assert nonneg_verdict(bad) == "ValueError", bad

    # M one shape: every result carries the same keys
    keys = {"valid", "reason", "value", "covered_fraction", "n_gaps", "n_dropped"}
    for tt, yy in (([0, 60], [1.0, 1.0]), ([0, 60, 30], [1.0] * 3), ([0], [1.0]),
                   ([0, 1000], [1.0, 1.0]), ([0, 0, 0], [1.0, 2.0, 3.0])):
        assert set(hand_integral(tt, yy, 60)) == keys

    print("ALL HAND VALUES CONSISTENT")


if __name__ == "__main__":
    main()
