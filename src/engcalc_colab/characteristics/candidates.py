from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import sympy as sp
from pint.errors import DimensionalityError

from ..errors import EngEvaluationError, NoRealValueError
from ..models import CharacteristicPoint
from .domain import AnalysisDomain
from .fallback import (
    _FALLBACK_X_DEDUP_REL_TOL,
    _fallback_response_profile,
    _fallback_roots,
    _fallback_validated_residual,
)


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


def closed_form_factors(expression, variable: sp.Symbol):
    """The factors of a polynomial in `variable` worth solving in closed form, and the
    highest degree among those that are not - or `(None, None)` when there is nothing to
    set aside and SymPy is asked as it always was.

    Not worth it: degree five or more, with names besides `variable` in the coefficients.
    A three-storey building's frequency equation `det(K - ω² M)` is of degree six in `ω`
    with six names in it, and SymPy's exact solver expanded Cardano's formula for it until
    the notebook was killed - sampled in `solveset` → `roots` → `_try_decompose` →
    `expand`. Abel and Ruffini say a quintic has no formula in general, and where one
    exists nobody reads it. A quartic keeps its closed form: a two-storey building's
    equation is one and solves in under a second. Plain-number coefficients are left to
    SymPy, which handles them with `CRootOf`.

    By factor and not by the whole: `(x - a)(x⁵ + b x + 1)` has the exact root `a`, and a
    contract from the 0.9.2 audit holds it. Factoring the four-storey equation takes
    0.1 s; the degree test before it takes 5 ms.
    """
    expression = sp.sympify(expression)
    if not expression.is_polynomial(variable):
        return None, None
    # A fast path, and only that: the factor loop below decides the same thing for a
    # polynomial with no names or a degree under five, after factoring it. Mutation says
    # so - lowering this bound or dropping the names test changes no answer - and it is
    # kept for the reason #143 kept its structural fast path: every root, extremum and
    # intersection on a page passes through here.
    if not (expression.free_symbols - {variable}) or sp.degree(expression, variable) < 5:
        return None, None
    try:
        factors = sp.factor_list(expression, variable)[1]
    except Exception:
        # SymPy's factoriser raises on some Float coefficients - "unsupported operand
        # type(s) for *: 'PolyElement' and 'PolyElement'" for `x⁵ + b x + 1.0`. Then the
        # whole polynomial is the one factor, and the numeric search finds its roots.
        factors = [(expression, 1)]
    solvable: list[sp.Expr] = []
    missing = 0
    for factor, _multiplicity in factors:
        degree = sp.degree(factor, variable)
        if degree <= 0:
            continue
        if degree >= 5 and factor.free_symbols - {variable}:
            missing = max(missing, int(degree))
        else:
            solvable.append(factor)
    return (tuple(solvable), missing) if missing else (None, None)


def _exact_real_solution_set(expression: sp.Expr, variable: sp.Symbol):
    # Common factors out first. `1.2 qD (L/2 - x) + 1.6 qL (L/2 - x)` solved as written is
    # floating point, `0.5 L`, a block away from an extrema that writes the same midspan
    # `L/2`; as `(L/2 - x)(1.2 qD + 1.6 qL)` the root is `L/2`. `factor_terms` and not
    # `simplify`, which the extrema analysis uses: a thousandth of a second on a
    # four-storey frequency equation where `simplify` takes a seventh.
    expression = sp.factor_terms(expression)
    solvable, missing = closed_form_factors(expression, variable)
    if missing:
        # The factors that have a closed form are solved as ever, and the discovery is
        # incomplete, so the numeric search the caller falls back to finds the rest.
        candidates: list[sp.Expr] = []
        for factor in solvable:
            candidates.extend(_exact_real_solution_set(factor, variable).candidates)
        return _ExactDiscovery(tuple(candidates), complete=False)
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

    # SymPy can express a finite exhaustive candidate family as an intersection
    # with Reals when parameter values decide whether individual candidates are
    # real, e.g. Intersection({-sqrt(-a), sqrt(-a)}, Reals).  That shape is still
    # complete: evaluate each finite candidate against the registered numeric
    # context and discard the ones that become complex.  Do not generalize this
    # to arbitrary polynomial solve() output: a Union containing a ConditionSet
    # can coexist with a finite factor, so solve() may expose only a partial hint.
    if isinstance(solution_set, sp.Intersection):
        finite_parts = [
            part for part in solution_set.args if isinstance(part, sp.FiniteSet)
        ]
        remaining_parts = [
            part for part in solution_set.args if not isinstance(part, sp.FiniteSet)
        ]
        if (
            len(finite_parts) == 1
            and remaining_parts
            and all(part is sp.S.Reals for part in remaining_parts)
        ):
            return _ExactDiscovery(tuple(finite_parts[0]), complete=True)

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
    residual_profile=None,
) -> _CandidateEvaluation:
    fixed_overrides = context.unit_literal_overrides(expression, overrides)
    fixed_overrides = context.unit_literal_overrides(candidate, fixed_overrides)
    try:
        _, x_quantity = context.evaluate_symbolic(candidate, overrides=fixed_overrides)
    except NoRealValueError:
        # A complex candidate location never lies inside a real analysis domain.
        # solve() offers such candidates when a registered parameter leaves the
        # sign of a radicand undetermined, e.g. sqrt(-a) for x**2 + a. A rejection,
        # like the units below - not a candidate that could not be evaluated.
        return _CandidateEvaluation(point=None)
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
        if residual_profile is None:
            try:
                residual_profile = _fallback_response_profile(
                    expression,
                    variable,
                    domain,
                    context,
                    overrides=fixed_overrides,
                )
            except EngEvaluationError:
                return _CandidateEvaluation(point=None, needs_fallback=True)
        canonical_unit = residual_profile[3]
        response_scale = residual_profile[5]
        residual = _fallback_validated_residual(
            value_quantity,
            canonical_unit,
            response_scale,
            context,
        )
        if residual is None:
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

    residual_profile = None
    requires_numeric_validation = False
    for candidate in discovery.candidates:
        symbolic_value = sp.simplify(expression.subs(variable, sp.sympify(candidate)))
        if not (symbolic_value == 0 or symbolic_value.is_zero is True):
            requires_numeric_validation = True
            break
    if requires_numeric_validation:
        fixed_overrides = context.unit_literal_overrides(expression, overrides)
        try:
            residual_profile = _fallback_response_profile(
                expression,
                variable,
                domain,
                context,
                overrides=fixed_overrides,
            )
        except EngEvaluationError:
            residual_profile = None

    for candidate in discovery.candidates:
        outcome = _evaluate_root_candidate(
            expression,
            variable,
            sp.sympify(candidate),
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
            residual_profile=residual_profile,
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
