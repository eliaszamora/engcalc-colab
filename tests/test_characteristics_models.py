import ast
from dataclasses import FrozenInstanceError

import pytest

from engcalc_colab.models import (
    CharacteristicInterval,
    CharacteristicPoint,
    ExtremaResult,
    IntersectionsResult,
    ParsedStatement,
    RootsResult,
)


def _statement(source="roots(f(x), x, 0, 1)"):
    return ParsedStatement(
        line_no=1,
        source=source,
        target=None,
        parameters=None,
        expression=ast.parse(source, mode="eval"),
    )


def test_characteristic_point_is_frozen_and_preserves_typed_metadata():
    point = CharacteristicPoint(
        x_symbolic="L/2",
        x_quantity="3 m",
        value_symbolic="q*L**2/8",
        value_quantity="54 kN*m",
        provenance="exact",
        side="at",
        roles=("global_max",),
        source_label="M(x)",
    )

    assert point.roles == ("global_max",)
    assert point.provenance == "exact"
    with pytest.raises(FrozenInstanceError):
        point.side = "left"


@pytest.mark.parametrize("provenance", ["sampled", "approx", "", None])
def test_characteristic_point_rejects_unknown_provenance(provenance):
    with pytest.raises(ValueError, match="provenance"):
        CharacteristicPoint(
            x_symbolic=0,
            x_quantity=0,
            value_symbolic=0,
            value_quantity=0,
            provenance=provenance,
        )


@pytest.mark.parametrize("side", ["both", "interior", "", None])
def test_characteristic_point_rejects_unknown_side(side):
    with pytest.raises(ValueError, match="side"):
        CharacteristicPoint(
            x_symbolic=0,
            x_quantity=0,
            value_symbolic=0,
            value_quantity=0,
            provenance="exact",
            side=side,
        )


def test_characteristic_interval_validates_provenance_and_is_frozen():
    interval = CharacteristicInterval(
        lower_symbolic=0,
        upper_symbolic=1,
        lower_quantity="0 m",
        upper_quantity="1 m",
        role="roots",
        provenance="numeric",
        value_symbolic=0,
        value_quantity="0 kN",
    )
    assert interval.provenance == "numeric"
    with pytest.raises(FrozenInstanceError):
        interval.role = "coincident"

    with pytest.raises(ValueError, match="provenance"):
        CharacteristicInterval(
            lower_symbolic=0,
            upper_symbolic=1,
            lower_quantity=0,
            upper_quantity=1,
            role="roots",
            provenance="sampled",
        )


def test_roots_result_preserves_points_intervals_domain_and_statement():
    statement = _statement()
    point = CharacteristicPoint(0, 0, 0, 0, "exact")
    interval = CharacteristicInterval(0, 1, 0, 1, "roots")

    result = RootsResult(
        statement=statement,
        display_label="f(x)",
        variable="x",
        lower_quantity=0,
        upper_quantity=1,
        points=(point,),
        intervals=(interval,),
    )

    assert result.statement is statement
    assert result.points == (point,)
    assert result.intervals == (interval,)


def test_intersections_result_keeps_both_response_labels():
    result = IntersectionsResult(
        statement=_statement("intersections(f(x), g(x), x, 0, 1)"),
        left_label="f(x)",
        right_label="g(x)",
        variable="x",
        lower_quantity=0,
        upper_quantity=1,
        points=(),
    )

    assert (result.left_label, result.right_label) == ("f(x)", "g(x)")
    assert result.intervals == ()


def test_extrema_result_carries_explicit_unbounded_flags():
    result = ExtremaResult(
        statement=_statement("extrema(f(x), x, 0, 1)"),
        display_label="f(x)",
        variable="x",
        lower_quantity=0,
        upper_quantity=1,
        points=(),
        unbounded_above=True,
        unbounded_below=False,
    )

    assert result.unbounded_above is True
    assert result.unbounded_below is False
    assert result.intervals == ()
