"""Deep Property Gate — Level A coverage for unit literals reaching `numeric(...)`.

In the symbolic layer a unit is an ordinary free symbol, so `M = 5*kN` stores an
expression containing `kN`. 0.22.0 made `numeric` read it as the unit, which `:=` had
always done. The two paths disagreeing about the same question was the defect, so both
are checked here against arithmetic, and against each other.

Measured when that change went in: a counter on the new branch stayed at zero across the
whole ordinary suite. The corpus never reached it, which is why it needs properties of
its own rather than inheriting protection from anything else.
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from quality_tests.helpers import evaluate_cell

pytestmark = [pytest.mark.evidence_a, pytest.mark.quality_deep]

_MAGNITUDE = st.integers(min_value=1, max_value=5000).map(lambda n: n / 10)
_UNIT = st.sampled_from(["kN", "N", "mm", "m", "MPa", "GPa", "kg", "s"])


@settings(max_examples=80)
@given(magnitude=_MAGNITUDE, unit=_UNIT)
def test_a_symbolic_expression_carrying_a_unit_reaches_that_number(magnitude, unit):
    result = evaluate_cell(f"M = {magnitude}*{unit}\nnumeric(M)")
    assert float(result.quantity.to(unit).magnitude) == pytest.approx(
        magnitude, rel=1e-9
    )


@settings(max_examples=60)
@given(magnitude=_MAGNITUDE, unit=_UNIT)
def test_the_two_paths_give_the_same_quantity(magnitude, unit):
    """`a := 5*kN` and `b = 5*kN` then `numeric(b)` were different answers once.

    Level C, and the property that pins the defect rather than either path alone.
    """
    both = evaluate_cell(
        f"a := {magnitude}*{unit}\nb = {magnitude}*{unit}\nnumeric(b)"
    )
    assert float(both.quantity.to(unit).magnitude) == pytest.approx(
        magnitude, rel=1e-9
    )


@settings(max_examples=60)
@given(
    value=st.integers(min_value=1, max_value=900).map(lambda n: n / 10),
    factor=st.integers(min_value=2, max_value=9),
)
def test_a_defined_value_beats_the_unit_of_the_same_name(value, factor):
    """`m := 4.0` means the sheet's `m` is four, not metres.

    This is the precedence that makes the whole rule safe, and an implementation that
    resolved units first would return metres on a sheet that plainly said otherwise.
    Asserted dimensionless, because a wrong answer here carries a length.
    """
    result = evaluate_cell(f"m := {value}\nx = {factor}*m\nnumeric(x)")

    assert result.quantity.dimensionless
    assert float(result.quantity.magnitude) == pytest.approx(
        factor * value, rel=1e-9
    )


@settings(max_examples=40)
@given(first=st.sampled_from(["pp", "qq", "zz"]), second=st.sampled_from(["ww", "yy"]))
def test_a_name_that_is_not_a_unit_is_still_reported_missing(first, second):
    """The diagnostic that mattered most to keep.

    Resolving unit literals must never turn "you forgot to define this" into a number,
    and a property that only ever asked about units could not see that it had.
    """
    assume(first != second)

    from engcalc_colab.errors import EngEvaluationError

    with pytest.raises(EngEvaluationError) as excinfo:
        evaluate_cell(f"y = {first}*{second}\nnumeric(y)")
    message = str(excinfo.value)
    assert first in message and second in message
