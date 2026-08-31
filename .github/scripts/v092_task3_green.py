from pathlib import Path


path = Path("src/engcalc_colab/characteristics.py")
text = path.read_text()


def replace_between(source: str, start: str, end: str, replacement: str) -> str:
    start_index = source.index(start)
    end_index = source.index(end, start_index)
    return source[:start_index] + replacement.rstrip() + "\n\n\n" + source[end_index:]


models_anchor = '''@dataclass(frozen=True)
class ContinuousRegion:
    expression: sp.Expr
    lower_symbolic: sp.Expr
    upper_symbolic: sp.Expr
    lower_quantity: Any
    upper_quantity: Any
    lower_closed: bool
    upper_closed: bool
'''
models_replacement = models_anchor + '''


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
'''
if "class _ExactDiscovery:" not in text:
    if models_anchor not in text:
        raise SystemExit("Task 3 model anchor not found")
    text = text.replace(models_anchor, models_replacement, 1)

exact_replacement = '''def _exact_real_solution_set(expression: sp.Expr, variable: sp.Symbol):
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
'''
if "return _ExactDiscovery(tuple(candidates), complete=False)" not in text:
    text = replace_between(
        text,
        "def _exact_real_solution_set(expression: sp.Expr, variable: sp.Symbol):",
        "def _normalize_candidate_quantity",
        exact_replacement,
    )

candidate_replacement = '''def _evaluate_root_candidate(
    expression: sp.Expr,
    variable: sp.Symbol,
    candidate: sp.Expr,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
    source_label: str | None,
) -> _CandidateEvaluation:
    fixed_overrides = _characteristic_literal_unit_overrides(
        context,
        expression,
        overrides,
    )
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
'''
if ") -> _CandidateEvaluation:" not in text:
    text = replace_between(
        text,
        "def _evaluate_root_candidate(",
        "def _ordered_unique_points",
        candidate_replacement,
    )

nonpiecewise_replacement = '''    if not expression.has(sp.Piecewise):
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
        return _deduplicate_root_points(points, domain), (), False
'''
start = "    if not expression.has(sp.Piecewise):"
end = "    regions = _partition_piecewise_regions("
current_segment = text[text.index(start):text.index(end, text.index(start))]
if "discovery = _coerce_exact_discovery" not in current_segment:
    text = replace_between(text, start, end, nonpiecewise_replacement)

piecewise_start = "        candidates, unresolved = _exact_real_solution_set(branch_expression, variable)"
piecewise_end = "    for candidate in _piecewise_boundary_candidates("
if piecewise_start in text:
    piecewise_replacement = '''        discovery = _coerce_exact_discovery(
            _exact_real_solution_set(branch_expression, variable)
        )
        needs_fallback = not discovery.complete
        for candidate in discovery.candidates:
            outcome = _evaluate_root_candidate(
                branch_expression,
                variable,
                sp.sympify(candidate),
                domain,
                context,
                overrides=overrides,
                source_label=source_label,
            )
            needs_fallback = needs_fallback or outcome.needs_fallback
            if outcome.point is not None and _candidate_in_region(
                outcome.point.x_quantity,
                region,
                domain,
            ):
                points.append(outcome.point)

        if needs_fallback:
            region_domain = AnalysisDomain(
                lower_symbolic=region.lower_symbolic,
                upper_symbolic=region.upper_symbolic,
                lower_quantity=region.lower_quantity,
                upper_quantity=region.upper_quantity,
                unit=domain.unit,
            )
            fallback_points = _fallback_roots(
                branch_expression,
                variable,
                region_domain,
                context,
                overrides=overrides,
                source_label=source_label,
            )
            for point in fallback_points:
                if _candidate_in_region(point.x_quantity, region, domain):
                    points.append(point)
'''
    text = replace_between(text, piecewise_start, piecewise_end, piecewise_replacement)

boundary_old = '''        point = _evaluate_root_candidate(
            expression,
            variable,
            candidate,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
        )
        if point is not None:
            points.append(point)
'''
boundary_new = '''        outcome = _evaluate_root_candidate(
            expression,
            variable,
            candidate,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
        )
        # Boundary probes are topology checks, not exact solver candidates. An
        # undefined Piecewise boundary remains a normal non-root as in 0.9.1.
        if outcome.point is not None:
            points.append(outcome.point)
'''
if boundary_old in text:
    text = text.replace(boundary_old, boundary_new, 1)

path.write_text(text)
print("Applied Task 3 root discovery/candidate fallback patch.")
