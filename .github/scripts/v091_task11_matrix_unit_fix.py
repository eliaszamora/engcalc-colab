from pathlib import Path

PATH = Path("src/engcalc_colab/characteristics.py")
text = PATH.read_text(encoding="utf-8")

anchor = '''def _candidate_in_domain(quantity, domain: AnalysisDomain) -> bool:
    magnitude = float(quantity.to(domain.unit).magnitude)
    lower = float(domain.lower_quantity.magnitude)
    upper = float(domain.upper_quantity.magnitude)
    tolerance = 1e-12 * max(1.0, abs(lower), abs(upper), abs(upper - lower))
    return lower - tolerance <= magnitude <= upper + tolerance


def _evaluate_root_candidate(
'''
replacement = '''def _candidate_in_domain(quantity, domain: AnalysisDomain) -> bool:
    magnitude = float(quantity.to(domain.unit).magnitude)
    lower = float(domain.lower_quantity.magnitude)
    upper = float(domain.upper_quantity.magnitude)
    tolerance = 1e-12 * max(1.0, abs(lower), abs(upper), abs(upper - lower))
    return lower - tolerance <= magnitude <= upper + tolerance


def _characteristic_literal_unit_overrides(
    context,
    expression: sp.Expr,
    overrides: dict[str, Any] | None,
) -> dict[str, Any]:
    """Resolve unit aliases that remain symbolic inside characteristic expressions.

    Symbolic formulas intentionally keep names such as ``m`` as SymPy symbols.
    During physical validation of a characteristic point, however, a unit literal
    such as ``7*m`` must be interpreted through the same Pint unit registry as
    numeric input. Explicit overrides and stored numeric values always win.
    """
    fixed = dict(overrides or {})
    for symbol in sp.sympify(expression).free_symbols:
        name = symbol.name
        if name in fixed or name in context.values:
            continue
        try:
            fixed[name] = context.resolve_target_unit_name(name)
        except EngEvaluationError:
            continue
    return fixed


def _evaluate_root_candidate(
'''
if anchor not in text:
    raise SystemExit("Task 11 literal-unit helper insertion anchor not found")
text = text.replace(anchor, replacement, 1)

old = '''    fixed_overrides = dict(overrides or {})
    try:
        _, x_quantity = context.evaluate_symbolic(candidate, overrides=fixed_overrides)
'''
new = '''    fixed_overrides = _characteristic_literal_unit_overrides(
        context,
        expression,
        overrides,
    )
    try:
        _, x_quantity = context.evaluate_symbolic(candidate, overrides=fixed_overrides)
'''
if old not in text:
    raise SystemExit("Task 11 root-candidate override anchor not found")
text = text.replace(old, new, 1)

PATH.write_text(text, encoding="utf-8")
