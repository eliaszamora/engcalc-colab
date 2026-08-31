from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import sympy as sp
from pint.errors import DimensionalityError

from ..errors import EngEvaluationError
from ..models import CharacteristicPoint
from .domain import AnalysisDomain
from .fallback import _FALLBACK_X_DEDUP_REL_TOL, _fallback_roots


@dataclass(frozen=True)
class _ExactDiscovery:
    candidates: tuple[sp.Expr, ...]
    complete: bool

    def __iter__(self):
        # Backward-compatible internal unpacking: (candidates, unresolved).
        yield self.candidates
        yield not self.complete


@dataclass(frozen=True)
class _CandidateEvaluation:
    point: CharacteristicPoint | None
    needs_fallback: bool = False


def _coerce_exact_discovery(result) -> _ExactDiscovery:
    if isinstance(result, _ExactDiscovery):
        return result
    candidates, unresolved = result
    return _ExactDiscovery(tuple(candidates), complete=not bool(unresolved))


def _exact_real_solution_set(expression: sp.Expr, variable: sp.Symbol):
    equation = sp.Eq(expression, 0)
    try:
        solution_set = sp.solveset(equation, variable, domain=sp.S.Reals)
    except (NotImplementedError, ValueError, TypeError):
        solution_set = None

    if solution_set is sp.S.EmptySet:
        return _ExactDiscovery((), complete=True)
    if isinstance(solution_set, sp.FiniteSet):
        return _ExactDiscovery(tuple(solution_set), complete=True)
    if solution_set is sp.S.Reals:
        return _ExactDiscovery((), complete=True)

    # An unresolved solveset means any result from solve() is only a candidate
    # hint. It can improve exact provenance, but it cannot prove completeness.
    try:
        solutions = sp.solve(equation, variable)
    except (NotImplementedError, ValueError, TypeError):
        return _ExactDiscovery((), complete=False)

    if not solutions:
        return _ExactDiscovery((), complete=False)
    if isinstance(solutions, dict):
        solutions = [solutions.get(variable)]
    if not isinstance(solutions, (list, tuple, set, sp.FiniteSet)):
        solutions = [solutions]

    candidates: list[sp.Expr] = []
    for candidate in solutions:
        if candidate is None:
            continue
        candidate = sp.sympify(candidate)
        if variable in candidate.free_symbols:
            continue
        if candidate.is_real is False:
            continue
        candidates.append(candidate)
    return _ExactDiscovery(tuple(candidates), complete=False)


def _normalize_candidate_quantity(context, quantity, domain: AnalysisDomain):
    if quantity.dimensionless and not domain.lower_quantity.dimensionless:
        if float(quantity.magnitude) != 0.0:
            raise EngEvaluationError("root location has incompatible units")
        quantity = context.ureg.Quantity(0, domain.unit)
    try:
        return quantity.to(domain.unit)
    except DimensionalityError as exc:
        raise EngEvaluationError("root location has incompatible units") from exc


def _candidate_in_domain(quantity, domain: AnalysisDomain) -> bool:
    magnitude = float(quantity.to(domain.unit).magnitude)
    lower = float(domain.lower_quantity.magnitude)
    upper = float(domain.upper_quantity.magnitude)
    tolerance = 1e-12 * max(1.0, abs(lower), abs(upper), abs(upper - lower))
    return lower - tolerance <= magnitude <= upper + tolerance


def _evaluate_root_candidate(
    expression: sp.Expr,
    variable: sp.Symbol,
    candidate: sp.Expr,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
    source_label: str | None,
) -> _CandidateEvaluation:
    fixed_overrides = context.unit_literal_overrides(expression, overrides)
    fixed_overrides = context.unit_literal_overrides(candidate, fixed_overrides)
    try:
        _, x_quantity = context.evaluate_symbolic(candidate, overrides=fixed_overrides)
    except EngEvaluationError:
        # A plausible exact candidate that EngCalc cannot physically evaluate is
        # not evidence that no root exists. The deterministic fallback must run.
        return _CandidateEvaluation(point=None, needs_fallback=True)

    try:
        x_quantity = _normalize_candidate_quantity(context, x_quantity, domain)
    except EngEvaluationError:
        # Dimensional incompatibility is a mathematical rejection, not an
        # incomplete-evaluation signal.
        return _CandidateEvaluation(point=None)
    if not _candidate_in_domain(x_quantity, domain):
        return _CandidateEvaluation(point=None)

    symbolic_value = sp.simplify(expression.subs(variable, candidate))
    exact_zero = symbolic_value == 0 or symbolic_value.is_zero is True

    sample_overrides = dict(fixed_overrides)
    sample_overrides[variable.name] = x_quantity
    try:
        _, value_quantity = context.evaluate_symbolic(
            expression,
            overrides=sample_overrides,
        )
    except EngEvaluationError:
        return _CandidateEvaluation(point=None, needs_fallback=True)

    if not exact_zero:
        try:
            numeric_zero = float(value_quantity.magnitude) == 0.0
        except (TypeError, ValueError, OverflowError):
            numeric_zero = False
        if not numeric_zero:
            return _CandidateEvaluation(point=None)

    return _CandidateEvaluation(
        point=CharacteristicPoint(
            x_symbolic=candidate,
            x_quantity=x_quantity,
            value_symbolic=sp.Integer(0) if exact_zero else symbolic_value,
            value_quantity=value_quantity,
            provenance="exact",
            side="at",
            roles=("root",),
            source_label=source_label,
        )
    )


def _ordered_unique_points(
    points: list[CharacteristicPoint],
    domain: AnalysisDomain,
) -> tuple[CharacteristicPoint, ...]:
    points.sort(
        key=lambda point: float(point.x_quantity.to(domain.unit).magnitude)
    )
    unique: list[CharacteristicPoint] = []
    span = abs(
        float(domain.upper_quantity.magnitude)
        - float(domain.lower_quantity.magnitude)
    )
    tolerance = 1e-12 * max(1.0, span)
    for point in points:
        if unique:
            current = float(point.x_quantity.to(domain.unit).magnitude)
            previous = float(unique[-1].x_quantity.to(domain.unit).magnitude)
            if math.isclose(current, previous, rel_tol=1e-12, abs_tol=tolerance):
                continue
        unique.append(point)
    return tuple(unique)


def _deduplicate_root_points(
    points: list[CharacteristicPoint],
    domain: AnalysisDomain,
) -> tuple[CharacteristicPoint, ...]:
    if not points:
        return ()
    points = sorted(
        points,
        key=lambda point: float(point.x_quantity.to(domain.unit).magnitude),
    )
    span = abs(
        float(domain.upper_quantity.to(domain.unit).magnitude)
        - float(domain.lower_quantity.to(domain.unit).magnitude)
    )
    tolerance = _FALLBACK_X_DEDUP_REL_TOL * max(1.0, span)
    unique: list[CharacteristicPoint] = []
    for point in points:
        if not unique:
            unique.append(point)
            continue
        current = float(point.x_quantity.to(domain.unit).magnitude)
        previous = float(unique[-1].x_quantity.to(domain.unit).magnitude)
        if math.isclose(current, previous, rel_tol=0.0, abs_tol=tolerance):
            if unique[-1].provenance == "numeric" and point.provenance == "exact":
                unique[-1] = point
            continue
        unique.append(point)
    return tuple(unique)


def _solve_continuous_zero_set(
    expression: sp.Expr,
    variable: sp.Symbol,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None = None,
    source_label: str | None = None,
) -> tuple[CharacteristicPoint, ...]:
    """Solve one continuous zero-set with exact-first/fallback merge semantics."""
    discovery = _coerce_exact_discovery(
        _exact_real_solution_set(expression, variable)
    )
    points: list[CharacteristicPoint] = []
    needs_fallback = not discovery.complete

    for candidate in discovery.candidates:
        outcome = _evaluate_root_candidate(
            expression,
            variable,
            sp.sympify(candidate),
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
        )
        needs_fallback = needs_fallback or outcome.needs_fallback
        if outcome.point is not None:
            points.append(outcome.point)

    if needs_fallback:
        points.extend(
            _fallback_roots(
                expression,
                variable,
                domain,
                context,
                overrides=overrides,
                source_label=source_label,
            )
        )
    return _deduplicate_root_points(points, domain)
