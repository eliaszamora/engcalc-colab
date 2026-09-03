"""Deep Property Gate — Level A coverage for Macaulay brackets `<x-a>^n`.

Measured motive: with the bracket permanently switched on — which ruins every beam
carrying a point load — `tools/gap_map.py` still reported 15 of 18 exercises running end
to end, entirely green. So did a bracket that opened one step early. The example
contracts in `tests/test_macaulay_brackets.py` catch both, but they catch them at the
offsets their author chose.

The oracle is the bracket's own definition in plain Python: zero before the offset, the
shifted power from there on. It never asks EngCalc, and never imports SymPy.
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from quality_tests.deep.strategies import distributed_load, span_length
from quality_tests.helpers import evaluate_cell, macaulay

pytestmark = [pytest.mark.evidence_a, pytest.mark.quality_deep]

_OFFSET = st.integers(min_value=50, max_value=750).map(lambda n: n / 100)
_ORDER = st.integers(min_value=0, max_value=3)
_STATION = st.integers(min_value=0, max_value=800).map(lambda n: n / 100)


@settings(max_examples=80)
@given(offset=_OFFSET, order=_ORDER, station=_STATION)
def test_a_bracket_is_zero_before_its_offset_and_the_shifted_power_after_it(
    offset, order, station
):
    assume(abs(station - offset) > 1e-3)

    result = evaluate_cell(
        f"b(x) = <x-{offset}>^{order}\nnumeric(subs(b(x), x, {station}))"
    )
    assert float(result.quantity.magnitude) == pytest.approx(
        macaulay(station, offset, order), rel=1e-9, abs=1e-9
    )


@settings(max_examples=60)
@given(load=distributed_load, span=span_length, position=st.floats(0.15, 0.85))
def test_a_simply_supported_beam_with_a_point_load_closes_at_the_far_support(
    load, span, position
):
    """`M(x) = R_A*x - P*<x-a>^1` must reach zero at x = L.

    The peak alone cannot see a bracket that never switches on: the term contributes
    nothing before the load either way. It is the far end that exposes it, where a
    silent bracket leaves the whole `P*(L-a)` hanging at a free support.
    """
    offset = round(span * position, 3)
    assume(0.05 < offset < span - 0.05)
    reaction = round(load * (span - offset) / span, 6)

    body = f"M(x) = {reaction}*x - {load}*<x-{offset}>^1\n"
    at_end = evaluate_cell(body + f"numeric(subs(M(x), x, {span}))")
    assert float(at_end.quantity.magnitude) == pytest.approx(0.0, abs=1e-6 * load * span)

    at_load = evaluate_cell(body + f"numeric(subs(M(x), x, {offset}))")
    assert float(at_load.quantity.magnitude) == pytest.approx(
        reaction * offset, rel=1e-9
    )


@settings(max_examples=60)
@given(offset=_OFFSET, order=st.integers(min_value=0, max_value=2), upper=_STATION)
def test_integrating_a_bracket_raises_its_order(offset, order, upper):
    """`integral(<x-a>^n, x, 0, b)` is `<b-a>^(n+1)/(n+1)`.

    The rule is built into SymPy's SingularityFunction, so this checks that EngCalc
    reaches it rather than that SymPy has it - a bracket handled as an ordinary power
    would integrate to the same expression without the switch, and agree everywhere
    beyond the offset while being wrong everywhere before it.
    """
    assume(upper > offset + 0.05 or upper < offset - 0.05)

    result = evaluate_cell(
        f"b(x) = <x-{offset}>^{order}\nS = integral(b(x), x, 0, {upper})\nnumeric(S)"
    )
    expected = macaulay(upper, offset, order + 1) / (order + 1)
    assert float(result.quantity.magnitude) == pytest.approx(
        expected, rel=1e-9, abs=1e-9
    )
