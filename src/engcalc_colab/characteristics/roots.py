from __future__ import annotations

from typing import Any

import sympy as sp

from ..errors import EngEvaluationError
from ..models import CharacteristicInterval, CharacteristicPoint
from .candidates import (
    _deduplicate_root_points,
    _evaluate_root_candidate,
    _solve_continuous_zero_set,
)
from .domain import AnalysisDomain, ContinuousRegion, _analysis_variable
from .piecewise_analysis import (
    _candidate_in_region,
    _partition_piecewise_regions,
    _piecewise_boundary_candidates,
    _point_is_covered_by_interval,
)


def _zero_interval_for_region(
    original_expression: sp.Expr,
    variable: sp.Symbol,
    region: ContinuousRegion,
    context,
    *,
    overrides: dict[str, Any] | None,
) -> CharacteristicInterval:
    midpoint = region.lower_quantity + (region.upper_quantity - region.lower_quantity) / 2
    sample_overrides = dict(overrides or {})
    sample_overrides[variable.name] = midpoint
    value_quantity = None
    try:
        _, value_quantity = context.evaluate_symbolic(
            original_expression,
            overrides=sample_overrides,
        )
    except EngEvaluationError:
        try:
            _, value_quantity = context.evaluate_symbolic(
                region.expression,
                overrides=sample_overrides,
            )
        except EngEvaluationError:
            value_quantity = None
    return CharacteristicInterval(
        lower_symbolic=region.lower_symbolic,
        upper_symbolic=region.upper_symbolic,
        lower_quantity=region.lower_quantity,
        upper_quantity=region.upper_quantity,
        role="roots",
        provenance="exact",
        value_symbolic=sp.Integer(0),
        value_quantity=value_quantity,
        lower_closed=region.lower_closed,
        upper_closed=region.upper_closed,
    )


def solve_roots_exact(
    expression,
    variable,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None = None,
    source_label: str | None = None,
):
    expression = sp.sympify(expression)
    variable = _analysis_variable(variable, expression)
    if not isinstance(variable, sp.Symbol):
        raise EngEvaluationError("roots variable must be a symbolic identifier")

    resolved_overrides = context.unit_literal_overrides(expression, overrides)

    if sp.simplify(expression) == 0:
        interval = CharacteristicInterval(
            lower_symbolic=domain.lower_symbolic,
            upper_symbolic=domain.upper_symbolic,
            lower_quantity=domain.lower_quantity,
            upper_quantity=domain.upper_quantity,
            role="roots",
            provenance="exact",
            value_symbolic=sp.Integer(0),
            value_quantity=None,
            lower_closed=True,
            upper_closed=True,
        )
        return (), (interval,), False

    if not expression.has(sp.Piecewise):
        return (
            _solve_continuous_zero_set(
                expression,
                variable,
                domain,
                context,
                overrides=resolved_overrides,
                source_label=source_label,
            ),
            (),
            False,
        )


    regions = _partition_piecewise_regions(
        expression,
        variable,
        domain,
        context,
        overrides=resolved_overrides,
    )
    points: list[CharacteristicPoint] = []
    intervals: list[CharacteristicInterval] = []
    unresolved_any = False

    for region in regions:
        branch_expression = sp.sympify(region.expression)
        if sp.simplify(branch_expression) == 0:
            intervals.append(
                _zero_interval_for_region(
                    expression,
                    variable,
                    region,
                    context,
                    overrides=resolved_overrides,
                )
            )
            continue

        region_domain = AnalysisDomain(
            lower_symbolic=region.lower_symbolic,
            upper_symbolic=region.upper_symbolic,
            lower_quantity=region.lower_quantity,
            upper_quantity=region.upper_quantity,
            unit=domain.unit,
        )
        for point in _solve_continuous_zero_set(
            branch_expression,
            variable,
            region_domain,
            context,
            overrides=resolved_overrides,
            source_label=source_label,
        ):
            if _candidate_in_region(point.x_quantity, region, domain):
                points.append(point)

    for candidate in _piecewise_boundary_candidates(
        expression,
        variable,
        domain,
        context,
        overrides=resolved_overrides,
    ):
        outcome = _evaluate_root_candidate(
            expression,
            variable,
            candidate,
            domain,
            context,
            overrides=resolved_overrides,
            source_label=source_label,
        )
        # Boundary probes are topology checks, not exact solver candidates. An
        # undefined Piecewise boundary remains a normal non-root as in 0.9.1.
        if outcome.point is not None:
            points.append(outcome.point)

    ordered_points = _deduplicate_root_points(points, domain)
    visible_points = tuple(
        point
        for point in ordered_points
        if not any(
            _point_is_covered_by_interval(point, interval, domain)
            for interval in intervals
        )
    )
    intervals.sort(
        key=lambda item: float(item.lower_quantity.to(domain.unit).magnitude)
    )
    return visible_points, tuple(intervals), unresolved_any
