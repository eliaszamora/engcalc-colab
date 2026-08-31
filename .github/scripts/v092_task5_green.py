from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Task 5 anchor not found: {label}")
    return text.replace(old, new, 1)


# Engine: canonical user engineering symbols are explicitly real.
path = Path("src/engcalc_colab/engine.py")
text = path.read_text()
text = replace_once(
    text,
    "            self.symbols[name] = sp.Symbol(name)\n",
    "            self.symbols[name] = sp.Symbol(name, real=True)\n",
    "engine.resolve_symbol",
)
path.write_text(text)


# Numeric helpers: reuse the symbol already embedded in the expression.
path = Path("src/engcalc_colab/numeric.py")
text = path.read_text()
old = "        symbol = sp.Symbol(variable)\n"
new = (
    "        symbol = next(\n"
    "            (item for item in expr.free_symbols if item.name == variable),\n"
    "            sp.Symbol(variable, real=True),\n"
    "        )\n"
)
text = replace_once(text, old, new, "numeric.evaluate_partial_polynomial")
old2 = "        symbol = sp.Symbol(variable)\n"
new2 = (
    "        symbol = next(\n"
    "            (item for item in expression.free_symbols if item.name == variable),\n"
    "            sp.Symbol(variable, real=True),\n"
    "        )\n"
)
text = replace_once(text, old2, new2, "numeric.build_partial_piecewise_evaluation")
path.write_text(text)


# Piecewise breakpoint extraction: preserve symbol assumptions/identity.
path = Path("src/engcalc_colab/piecewise.py")
text = path.read_text()
old = '''    symbol = sp.Symbol(variable)\n    breakpoints: list[sp.Expr] = []\n\n    for piecewise in sp.preorder_traversal(sp.sympify(expression)):\n'''
new = '''    expression = sp.sympify(expression)\n    symbol = next(\n        (item for item in expression.free_symbols if item.name == variable),\n        sp.Symbol(variable, real=True),\n    )\n    breakpoints: list[sp.Expr] = []\n\n    for piecewise in sp.preorder_traversal(expression):\n'''
text = replace_once(text, old, new, "piecewise.extract_symbolic_breakpoints")
path.write_text(text)


# Characteristic direct API string adapters: reuse an existing expression symbol
# before falling back to the new real-engine contract.
path = Path("src/engcalc_colab/characteristics.py")
text = path.read_text()
helper_anchor = '''def _coerce_exact_discovery(result) -> _ExactDiscovery:\n    if isinstance(result, _ExactDiscovery):\n        return result\n    candidates, unresolved = result\n    return _ExactDiscovery(tuple(candidates), complete=not bool(unresolved))\n'''
helper = helper_anchor + '''\n\ndef _analysis_variable(variable, *expressions):\n    if isinstance(variable, sp.Symbol):\n        return variable\n    if not isinstance(variable, str):\n        return variable\n    for expression in expressions:\n        symbols = sorted(\n            (\n                item\n                for item in sp.sympify(expression).free_symbols\n                if item.name == variable\n            ),\n            key=sp.default_sort_key,\n        )\n        if symbols:\n            return symbols[0]\n    return sp.Symbol(variable, real=True)\n'''
if "def _analysis_variable(variable, *expressions):" not in text:
    if helper_anchor not in text:
        raise SystemExit("Task 5 anchor not found: characteristics helper")
    text = text.replace(helper_anchor, helper, 1)

root_old = '''    expression = sp.sympify(expression)\n    if isinstance(variable, str):\n        variable = sp.Symbol(variable)\n    if not isinstance(variable, sp.Symbol):\n        raise EngEvaluationError("roots variable must be a symbolic identifier")\n'''
root_new = '''    expression = sp.sympify(expression)\n    variable = _analysis_variable(variable, expression)\n    if not isinstance(variable, sp.Symbol):\n        raise EngEvaluationError("roots variable must be a symbolic identifier")\n'''
text = replace_once(text, root_old, root_new, "characteristics.roots variable")

intersection_old = '''    left_expression = sp.sympify(left_expression)\n    right_expression = sp.sympify(right_expression)\n    if isinstance(variable, str):\n        variable = sp.Symbol(variable)\n    if not isinstance(variable, sp.Symbol):\n        raise EngEvaluationError("intersections variable must be a symbolic identifier")\n'''
intersection_new = '''    left_expression = sp.sympify(left_expression)\n    right_expression = sp.sympify(right_expression)\n    variable = _analysis_variable(variable, left_expression, right_expression)\n    if not isinstance(variable, sp.Symbol):\n        raise EngEvaluationError("intersections variable must be a symbolic identifier")\n'''
text = replace_once(
    text,
    intersection_old,
    intersection_new,
    "characteristics.intersections variable",
)

continuous_old = '''    expression = sp.simplify(sp.sympify(expression))\n    if isinstance(variable, str):\n        variable = sp.Symbol(variable)\n    if not isinstance(variable, sp.Symbol):\n        raise EngEvaluationError("extrema variable must be a symbolic identifier")\n'''
continuous_new = '''    expression = sp.simplify(sp.sympify(expression))\n    variable = _analysis_variable(variable, expression)\n    if not isinstance(variable, sp.Symbol):\n        raise EngEvaluationError("extrema variable must be a symbolic identifier")\n'''
text = replace_once(
    text,
    continuous_old,
    continuous_new,
    "characteristics.continuous extrema variable",
)

extrema_old = '''    expression = sp.sympify(expression)\n    if isinstance(variable, str):\n        variable = sp.Symbol(variable)\n    if not isinstance(variable, sp.Symbol):\n        raise EngEvaluationError("extrema variable must be a symbolic identifier")\n    if expression.has(sp.Piecewise):\n'''
extrema_new = '''    expression = sp.sympify(expression)\n    variable = _analysis_variable(variable, expression)\n    if not isinstance(variable, sp.Symbol):\n        raise EngEvaluationError("extrema variable must be a symbolic identifier")\n    if expression.has(sp.Piecewise):\n'''
text = replace_once(
    text,
    extrema_old,
    extrema_new,
    "characteristics.extrema variable",
)

# A scaled absolute response c*Abs(g(x)), with c independent of x, has all
# interior extrema among zeros of g (cusps) and stationary points of g. Solving
# those smooth equations avoids differentiating Abs directly into sign/Piecewise
# forms that are not physically evaluable by NumericContext.
stationary_old = '''    derivative = sp.simplify(sp.diff(expression, variable))\n    stationary_points, stationary_intervals, derivative_unresolved = solve_roots_exact(\n        derivative,\n        variable,\n        domain,\n        context,\n        overrides=overrides,\n        source_label=source_label,\n    )\n    if stationary_intervals:\n        derivative_unresolved = True\n\n    for stationary in stationary_points:\n'''
stationary_new = '''    independent_factor, dependent_factor = expression.as_independent(\n        variable,\n        as_Add=False,\n    )\n    if (\n        dependent_factor.func == sp.Abs\n        and variable not in independent_factor.free_symbols\n    ):\n        inner_expression = sp.sympify(dependent_factor.args[0])\n        cusp_points, cusp_intervals, cusp_unresolved = solve_roots_exact(\n            inner_expression,\n            variable,\n            domain,\n            context,\n            overrides=overrides,\n            source_label=source_label,\n        )\n        stationary_candidates = list(cusp_points)\n        derivative_unresolved = bool(cusp_unresolved or cusp_intervals)\n\n        inner_derivative = sp.simplify(sp.diff(inner_expression, variable))\n        if variable in inner_derivative.free_symbols:\n            smooth_points, smooth_intervals, smooth_unresolved = solve_roots_exact(\n                inner_derivative,\n                variable,\n                domain,\n                context,\n                overrides=overrides,\n                source_label=source_label,\n            )\n            stationary_candidates.extend(smooth_points)\n            derivative_unresolved = bool(\n                derivative_unresolved or smooth_unresolved or smooth_intervals\n            )\n        stationary_points = _deduplicate_root_points(stationary_candidates, domain)\n    else:\n        derivative = sp.simplify(sp.diff(expression, variable))\n        stationary_points, stationary_intervals, derivative_unresolved = solve_roots_exact(\n            derivative,\n            variable,\n            domain,\n            context,\n            overrides=overrides,\n            source_label=source_label,\n        )\n        if stationary_intervals:\n            derivative_unresolved = True\n\n    for stationary in stationary_points:\n'''
text = replace_once(
    text,
    stationary_old,
    stationary_new,
    "characteristics scaled Abs extrema candidates",
)
path.write_text(text)

print("Applied Task 5 real-symbol identity-safe migration with scaled-Abs extrema support.")
