"""P13: integration (D24) and gate predicates (D25/D31).

Expected values are hand literals from tests/reference/hand/integration.md (p13_hand_calc.py),
not computed by the module under test. A parity check against the independent reference
procedure covers further series. Messages of raised errors are asserted, not only the raise.
"""
import dataclasses
import importlib.util
import math
import os
import random
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

NAN = float("nan")
INF = float("inf")


def _integrate(t, y, nominal=60):
    from verlustmappe.models.integration import integrate_trapezoid
    return integrate_trapezoid(t, y, nominal)


def _hand():
    spec = importlib.util.spec_from_file_location(
        "p13_hand_calc", os.path.join(ROOT, "tests", "reference", "hand", "p13_hand_calc.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_constants_are_the_d24_values():
    from verlustmappe.models import integration as I
    assert I.GAP_FACTOR == 3.0 and I.MAX_GAP_S == 30.0
    assert I.gap_limit_s(60) == 180.0 and I.gap_limit_s(1) == 30.0 and I.gap_limit_s(20) == 60.0


def test_constant_series():
    r = _integrate([0, 60, 120, 180, 240, 300], [1000.0] * 6)
    assert (r.valid, r.reason, r.value, r.covered_fraction, r.n_gaps, r.n_dropped) == (
        True, "", 300000.0, 1.0, 0, 0)


def test_ramp_trapezoid_and_rectangle_difference():
    t = [60 * i for i in range(61)]
    y = [3000.0 * ti / 3600.0 for ti in t]
    r = _integrate(t, y)
    assert r.value == pytest.approx(5.4e6, rel=1e-12)             # 1.5 kWh, analytic 0.5*3000*3600
    assert r.value / 3.6e6 == pytest.approx(1.5, rel=1e-12)
    rect_kWh = 1.475                                              # hand value, forward rectangles
    assert (r.value / 3.6e6 - rect_kWh) / rect_kWh == pytest.approx(0.025 / 1.475, rel=1e-9)


def test_gap_segments_the_series():
    r = _integrate([0, 60, 120, 600, 660, 720], [1000.0] * 6)
    assert r.value == 240000.0 and r.covered_fraction == pytest.approx(1 / 3) and r.n_gaps == 1


def test_nan_stretch_at_the_limit_is_not_a_gap_one_more_is():
    t = [0, 60, 120, 180, 240, 300]
    r = _integrate(t, [1000.0, 1000.0, NAN, NAN, 2000.0, 2000.0])
    assert (r.value, r.covered_fraction, r.n_gaps, r.n_dropped) == (450000.0, 1.0, 0, 2)
    r = _integrate(t, [1000.0, 1000.0, NAN, NAN, NAN, 2000.0])
    assert r.value == 60000.0 and r.covered_fraction == pytest.approx(0.2)
    assert (r.n_gaps, r.n_dropped) == (1, 3)


def test_constant_binds_for_short_nominal_and_factor_for_long():
    r = _integrate([0, 30, 61], [100.0] * 3, nominal=1)
    assert r.value == 3000.0 and r.covered_fraction == pytest.approx(30 / 61) and r.n_gaps == 1
    r = _integrate([0, 60, 121], [100.0] * 3, nominal=20)
    assert r.value == 6000.0 and r.n_gaps == 1


def test_two_samples_and_single_sample():
    r = _integrate([0, 60], [0.0, 600.0])
    assert r.value == 18000.0 and r.covered_fraction == 1.0
    r = _integrate([0], [5.0])
    assert (r.valid, r.reason, r.value) == (False, "no valid samples", None)


def test_duplicate_timestamps():
    r = _integrate([0, 60, 60, 120], [1000.0] * 4)
    assert r.value == 120000.0 and r.covered_fraction == 1.0
    r = _integrate([0, 60, 60, 120], [1000.0, 1000.0, 2000.0, 2000.0])
    assert (r.valid, r.reason, r.value) == (False, "duplicate timestamp with conflicting values", None)
    r = _integrate([0, 60, 60, 120], [1000.0, 1000.0, 1000.0 + 1e-12, 1000.0])
    assert not r.valid                                            # exact equality, no tolerance


def test_non_monotonic_time():
    r = _integrate([0, 60, 30], [1.0, 1.0, 1.0])
    assert (r.valid, r.reason, r.value, r.n_gaps, r.covered_fraction) == (
        False, "non-monotonic time", None, None, None)


def test_zero_coverage_is_invalid_never_zero():
    r = _integrate([0, 1000, 2000], [100.0] * 3)
    assert (r.valid, r.reason, r.value, r.n_gaps, r.covered_fraction) == (
        False, "no covered segment", None, 2, None)
    r = _integrate([0, 0, 0], [5.0, 5.0, 5.0])
    assert (r.valid, r.reason, r.value) == (False, "no covered segment", None)
    r = _integrate([0, 60, 120], [NAN] * 3)
    assert (r.valid, r.reason, r.value, r.n_dropped) == (False, "no valid samples", None, 3)


def test_span_is_the_input_span():
    r = _integrate([0, 60, 120, 180, 240, 300], [NAN, 1000.0, 1000.0, 1000.0, 1000.0, NAN])
    assert r.value == 180000.0 and r.covered_fraction == pytest.approx(0.6) and r.n_dropped == 2
    r = _integrate([0, 60, 120], [NAN, 1000.0, 1000.0])
    assert r.value == 60000.0 and r.covered_fraction == pytest.approx(0.5) and r.n_dropped == 1
    r = _integrate([0, 60, NAN, 120], [1000.0] * 4)
    assert r.value == 120000.0 and r.covered_fraction == 1.0 and r.n_dropped == 1


def test_one_result_shape_for_every_branch():
    keys = {f.name for f in dataclasses.fields(_integrate([0, 60], [1.0, 1.0]))}
    assert keys == {"valid", "reason", "value", "covered_fraction", "n_gaps", "n_dropped"}
    for t, y in (([0, 60, 30], [1.0] * 3), ([0], [1.0]), ([0, 1000], [1.0, 1.0]),
                 ([0, 0, 0], [1.0, 2.0, 3.0])):
        assert {f.name for f in dataclasses.fields(_integrate(t, y))} == keys


def test_result_is_immutable():
    r = _integrate([0, 60], [1.0, 1.0])
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.value = 0.0


def test_caller_errors_raise_with_message():
    from verlustmappe.models.integration import integrate_trapezoid
    with pytest.raises(ValueError, match="non-empty"):
        integrate_trapezoid([], [], 60)
    with pytest.raises(ValueError, match="equal length"):
        integrate_trapezoid([0, 1], [1.0], 60)
    for bad in (0.0, -1.0, NAN, INF):
        with pytest.raises(ValueError, match="nominal_dt_s"):
            integrate_trapezoid([0, 60], [1.0, 1.0], bad)


def test_parity_with_the_independent_reference_procedure():
    hand = _hand()
    from verlustmappe.models.integration import integrate_trapezoid
    with open(os.path.join(ROOT, "tests", "reference", "hand", "p13_hand_calc.py")) as f:
        assert not any(ln.lstrip().startswith(("import verlustmappe", "from verlustmappe"))
                       for ln in f), "reference must stay independent of the package"
    rng = random.Random(20261028)
    for _ in range(300):
        n = rng.randint(1, 12)
        t, acc = [], 0.0
        for _ in range(n):
            acc += rng.choice([0, 1, 20, 30, 31, 60, 61, 180, 181, 400])
            t.append(acc if rng.random() > 0.05 else NAN)
        if rng.random() < 0.1 and n > 1:
            t[rng.randrange(n)] = rng.choice([-5.0, t[0] if math.isfinite(t[0]) else 0.0])
        y = [rng.choice([0.0, 100.0, 1000.0, NAN]) for _ in range(n)]
        nominal = rng.choice([1, 20, 60])
        got = integrate_trapezoid(t, y, nominal)
        want = hand.hand_integral(t, y, nominal)
        for key in ("valid", "reason", "n_gaps", "n_dropped"):
            assert getattr(got, key) == want[key], (t, y, nominal, key)
        for key in ("value", "covered_fraction"):
            a, b = getattr(got, key), want[key]
            assert (a is None) == (b is None) and (a is None or a == pytest.approx(b, rel=1e-12))


def test_check_nonnegative_three_way():
    from verlustmappe.models.validity import check_nonnegative
    assert check_nonnegative(0.0, "e") is True and check_nonnegative(-0.0, "e") is True
    assert check_nonnegative(3.5, "e") is True and check_nonnegative(2, "e") is True
    assert check_nonnegative(-0.001, "e") is False and check_nonnegative(-1e-300, "e") is False
    assert check_nonnegative(-5, "e") is False                      # a verdict, never a raise


def test_check_nonnegative_caller_errors_name_the_problem():
    from verlustmappe.models.validity import check_nonnegative
    for bad in (NAN, INF, -INF):
        with pytest.raises(ValueError, match=r"energy_kWh: non-finite value"):
            check_nonnegative(bad, "energy_kWh")
    for bad, kind in (("1.0", "str"), (None, "NoneType"), (True, "bool"), ([1.0], "list")):
        with pytest.raises(ValueError, match=rf"energy_kWh: expected a finite number, got {kind}"):
            check_nonnegative(bad, "energy_kWh")


def test_time_is_monotonic():
    from verlustmappe.models.validity import time_is_monotonic
    assert time_is_monotonic([0, 60, 60, 120]) is True
    assert time_is_monotonic([0, 60, 30]) is False
    assert time_is_monotonic([0, NAN, 60]) is True
    assert time_is_monotonic([5]) is True and time_is_monotonic([]) is True


def test_monotonic_predicate_agrees_with_the_integrator():
    from verlustmappe.models.validity import time_is_monotonic
    for t in ([0, 60, 30], [0, 60, 60], [0, NAN, 60], [60, NAN, 30]):
        invalid = _integrate(t, [1.0] * len(t)).reason == "non-monotonic time"
        assert invalid == (not time_is_monotonic(t))
