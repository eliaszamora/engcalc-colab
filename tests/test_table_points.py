import importlib

import pytest

from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.numeric import NumericContext


def _tables():
    return importlib.import_module("engcalc_colab.tables")


def _magnitudes(points, unit):
    return [point.to(unit).magnitude for point in points]


def test_uniform_zero_inherits_dimensional_endpoint_unit():
    ctx = NumericContext()
    points = _tables().normalize_uniform_points(
        ctx,
        ctx.ureg.Quantity(0),
        5 * ctx.ureg.m,
        ctx.ureg.Quantity(3),
    )
    assert _magnitudes(points, "m") == pytest.approx([0, 2.5, 5])


def test_uniform_zero_inherits_unit_from_lower_endpoint_too():
    ctx = NumericContext()
    points = _tables().normalize_uniform_points(
        ctx,
        5 * ctx.ureg.m,
        ctx.ureg.Quantity(0),
        3,
    )
    assert _magnitudes(points, "m") == pytest.approx([5, 2.5, 0])


def test_uniform_descending_range_preserves_requested_order():
    ctx = NumericContext()
    points = _tables().normalize_uniform_points(
        ctx,
        5 * ctx.ureg.m,
        1 * ctx.ureg.m,
        5,
    )
    assert _magnitudes(points, "m") == pytest.approx([5, 4, 3, 2, 1])


def test_uniform_dimensionless_range_remains_dimensionless():
    ctx = NumericContext()
    points = _tables().normalize_uniform_points(ctx, 0, 1, 3)
    assert [point.dimensionless for point in points] == [True, True, True]
    assert [point.magnitude for point in points] == pytest.approx([0, 0.5, 1])


def test_uniform_nonzero_dimensionless_endpoint_does_not_inherit_units():
    ctx = NumericContext()
    with pytest.raises(EngEvaluationError, match="table range endpoints have incompatible units"):
        _tables().normalize_uniform_points(ctx, 1, 5 * ctx.ureg.m, 3)


def test_uniform_incompatible_dimensional_endpoints_are_rejected():
    ctx = NumericContext()
    with pytest.raises(EngEvaluationError, match="table range endpoints have incompatible units"):
        _tables().normalize_uniform_points(ctx, 0 * ctx.ureg.m, 5 * ctx.ureg.s, 3)


@pytest.mark.parametrize("count", [1, 0, -2, 2.5, True])
def test_uniform_invalid_dimensionless_count_is_rejected(count):
    ctx = NumericContext()
    with pytest.raises(EngEvaluationError, match="table count must be a dimensionless integer >= 2"):
        _tables().normalize_uniform_points(ctx, 0, 1, count)


def test_uniform_dimensional_count_is_rejected():
    ctx = NumericContext()
    with pytest.raises(EngEvaluationError, match="table count must be a dimensionless integer >= 2"):
        _tables().normalize_uniform_points(ctx, 0, 1, 3 * ctx.ureg.m)


def test_explicit_magnitudes_use_declared_unit_once():
    ctx = NumericContext()
    points = _tables().normalize_explicit_points(
        ctx,
        [0, 1, 1.5, 2],
        ctx.ureg.m,
    )
    assert _magnitudes(points, "m") == pytest.approx([0, 1, 1.5, 2])


def test_explicit_declared_unit_converts_already_dimensional_points():
    ctx = NumericContext()
    points = _tables().normalize_explicit_points(
        ctx,
        [0, 50 * ctx.ureg.cm, 1],
        ctx.ureg.m,
    )
    assert _magnitudes(points, "m") == pytest.approx([0, 0.5, 1])


def test_explicit_fully_dimensional_mixed_compatible_units_normalize():
    ctx = NumericContext()
    points = _tables().normalize_explicit_points(
        ctx,
        [0 * ctx.ureg.m, 50 * ctx.ureg.cm, 1 * ctx.ureg.m],
    )
    assert _magnitudes(points, "m") == pytest.approx([0, 0.5, 1])


def test_explicit_leading_dimensionless_zero_inherits_later_dimensional_unit():
    ctx = NumericContext()
    points = _tables().normalize_explicit_points(
        ctx,
        [0, 50 * ctx.ureg.cm, 1 * ctx.ureg.m],
    )
    assert _magnitudes(points, "cm") == pytest.approx([0, 50, 100])


def test_explicit_all_dimensionless_points_remain_dimensionless():
    ctx = NumericContext()
    points = _tables().normalize_explicit_points(ctx, [0, 0.5, 1])
    assert [point.dimensionless for point in points] == [True, True, True]
    assert [point.magnitude for point in points] == pytest.approx([0, 0.5, 1])


def test_explicit_nonzero_dimensionless_mixed_with_dimensional_is_ambiguous():
    ctx = NumericContext()
    with pytest.raises(
        EngEvaluationError,
        match="nonzero dimensionless table point cannot be mixed with dimensional points",
    ):
        _tables().normalize_explicit_points(ctx, [0, 1, 2 * ctx.ureg.m])


def test_explicit_incompatible_dimensional_points_are_rejected():
    ctx = NumericContext()
    with pytest.raises(EngEvaluationError, match="table points have incompatible units"):
        _tables().normalize_explicit_points(ctx, [0 * ctx.ureg.m, 1 * ctx.ureg.s])


def test_explicit_declared_unit_rejects_incompatible_dimensional_point():
    ctx = NumericContext()
    with pytest.raises(EngEvaluationError, match="table points have incompatible units"):
        _tables().normalize_explicit_points(
            ctx,
            [0, 1 * ctx.ureg.s],
            ctx.ureg.m,
        )


def test_point_normalization_does_not_mutate_numeric_context():
    ctx = NumericContext()
    ctx.values["x"] = 9 * ctx.ureg.m
    before = dict(ctx.values)
    _tables().normalize_uniform_points(ctx, 0, 2 * ctx.ureg.m, 3)
    _tables().normalize_explicit_points(ctx, [0, 1, 2], ctx.ureg.m)
    assert ctx.values == before
