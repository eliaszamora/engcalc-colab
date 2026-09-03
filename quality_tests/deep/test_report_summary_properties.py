"""Deep Property Gate — Level A coverage for `report(...)` and `summary()`.

The bookkeeping is the whole feature: which names are in the table, in what order, and
what happens when one is marked twice. All three are decided here before EngCalc runs.

A summary that quietly reorders its rows, or keeps a stale value beside a corrected one,
is the worst kind of wrong in a memoria - it is plausible, and about the wrong number.
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from quality_tests.helpers import evaluate_cell

pytestmark = [pytest.mark.evidence_a, pytest.mark.quality_deep]

_NAMES = st.lists(
    st.sampled_from(["M_a", "M_b", "R_c", "R_d", "V_e", "d_f"]),
    min_size=1,
    max_size=6,
    unique=True,
)
_VALUE = st.integers(min_value=1, max_value=900).map(lambda n: n / 10)


def _sheet(names, values):
    lines = ["L := 6*m"]
    for name, value in zip(names, values):
        lines.append(f"{name} = {value}*L")
        lines.append(f"report({name})")
    lines.append("summary()")
    return "\n".join(lines)


@settings(max_examples=60)
@given(names=_NAMES, values=st.lists(_VALUE, min_size=6, max_size=6))
def test_the_summary_holds_every_reported_name_in_the_order_it_was_marked(names, values):
    """Order is the property. A table sorted alphabetically reads as a different memoria."""
    result = evaluate_cell(_sheet(names, values))
    assert [name for name, _value in result.entries] == names


@settings(max_examples=60)
@given(names=_NAMES, values=st.lists(_VALUE, min_size=6, max_size=6))
def test_each_row_carries_the_value_that_name_was_given(names, values):
    """`M_a = v*L` with `L := 6 m` is `6v` metres, computed here rather than read back.

    Names in the right order with the values shuffled between them would pass the
    property above and be exactly as wrong.
    """
    result = evaluate_cell(_sheet(names, values))
    for (name, quantity), value in zip(result.entries, values):
        assert name in names
        assert float(quantity.to("m").magnitude) == pytest.approx(value * 6, rel=1e-9)


@settings(max_examples=40)
@given(first=_VALUE, second=_VALUE)
def test_reporting_a_name_again_replaces_its_row_rather_than_adding_one(first, second):
    """A recomputed result is the same result, and a correction belongs where the reader
    expects it - not appended at the bottom beside the value it corrects.
    """
    assume(abs(first - second) > 0.5)

    result = evaluate_cell(
        "L := 6*m\n"
        f"M = {first}*L\n"
        "report(M)\n"
        f"M = {second}*L\n"
        "report(M)\n"
        "summary()"
    )
    assert [name for name, _value in result.entries] == ["M"]
    assert float(result.entries[0][1].to("m").magnitude) == pytest.approx(
        second * 6, rel=1e-9
    )


@settings(max_examples=40)
@given(names=_NAMES, values=st.lists(_VALUE, min_size=6, max_size=6))
def test_a_name_reported_late_keeps_its_first_position(names, values):
    """Marking a name again must not move it to the end.

    Replacement in place and replacement by append are the same table whenever the
    repeated name happened to be the last one, so the repeat here is always the first.
    """
    assume(len(names) >= 2)

    sheet = _sheet(names, values).replace("summary()", f"report({names[0]})\nsummary()")
    result = evaluate_cell(sheet)
    assert [name for name, _value in result.entries] == names
