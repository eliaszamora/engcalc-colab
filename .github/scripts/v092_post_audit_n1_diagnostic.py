from __future__ import annotations

import sympy as sp

import engcalc_colab.characteristics.candidates as candidates
import engcalc_colab.characteristics.fallback as fallback
import engcalc_colab.engine as engine_module
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import RootsResult
from engcalc_colab.parser import parse_cell


def evaluate_cell(engine: EngineeringEngine, source: str):
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


def inspect(label: str, expression: sp.Expr, x: sp.Symbol) -> None:
    expression = sp.sympify(expression)
    equation = sp.Eq(expression, 0)
    solveset_result = sp.solveset(equation, x, domain=sp.S.Reals)
    try:
        solve_result = sp.solve(equation, x)
    except Exception as exc:  # diagnostic only
        solve_result = f"ERROR:{type(exc).__name__}:{exc}"
    discovery = candidates._coerce_exact_discovery(
        candidates._exact_real_solution_set(expression, x)
    )

    print(f"=== {label} ===")
    print("SYMPY_VERSION=", sp.__version__)
    print("REPR=", repr(expression))
    print("SREPR=", sp.srepr(expression))
    print("SOLVESET=", repr(solveset_result))
    print("SOLVE=", repr(solve_result))
    print("DISCOVERY_CANDIDATES=", repr(discovery.candidates))
    print("DISCOVERY_COMPLETE=", discovery.complete)


def main() -> None:
    engine = EngineeringEngine()
    evaluate_cell(engine, "f(x) = 2.87*x^2 + -12.50459*x + 6.4876637")
    stored_expression = engine.functions["f"].expression
    global_x = engine.resolve_symbol("x")
    inspect("STORED_FUNCTION", stored_expression, global_x)

    captured: dict[str, object] = {}
    original = engine_module.solve_roots_exact

    def traced_solve_roots_exact(expression, variable, domain, context, **kwargs):
        captured["expression"] = sp.sympify(expression)
        captured["variable"] = variable
        captured["domain"] = domain
        captured["context"] = context
        print("ROOTS_SOURCE_LABEL=", repr(kwargs.get("source_label")))
        inspect("ROOTS_SOLVER_INPUT", sp.sympify(expression), variable)
        return original(expression, variable, domain, context, **kwargs)

    engine_module.solve_roots_exact = traced_solve_roots_exact
    try:
        result = evaluate_cell(engine, "roots(f(x), x, 0, 5)")
    finally:
        engine_module.solve_roots_exact = original

    assert isinstance(result, RootsResult)
    print("PUBLIC_ROOTS_COUNT=", len(result.points))
    print("PUBLIC_ROOTS=", [repr(point.x_symbolic) for point in result.points])

    expression = sp.sympify(captured["expression"])
    variable = captured["variable"]
    domain = captured["domain"]
    context = captured["context"]
    discovery = candidates._coerce_exact_discovery(
        candidates._exact_real_solution_set(expression, variable)
    )

    print("=== CANDIDATE_VALIDATION ===")
    for candidate in discovery.candidates:
        symbolic_residual = sp.simplify(expression.subs(variable, candidate))
        _, value_quantity = context.evaluate_symbolic(
            expression,
            overrides={variable.name: context.ureg.Quantity(float(candidate), domain.unit)},
        )
        outcome = candidates._evaluate_root_candidate(
            expression,
            variable,
            candidate,
            domain,
            context,
            overrides=None,
            source_label="f(x)",
        )
        print("CANDIDATE=", repr(candidate))
        print("SYMBOLIC_RESIDUAL=", repr(symbolic_residual))
        print("NUMERIC_RESIDUAL=", repr(value_quantity.magnitude))
        print("OUTCOME_POINT=", repr(outcome.point))
        print("OUTCOME_NEEDS_FALLBACK=", outcome.needs_fallback)

    print("=== FALLBACK_DIRECT ===")
    try:
        fallback_points = fallback._fallback_roots(
            expression,
            variable,
            domain,
            context,
            overrides=None,
            source_label="f(x)",
        )
        print("FALLBACK_POINTS=", [repr(point.x_symbolic) for point in fallback_points])
    except Exception as exc:
        print("FALLBACK_ERROR=", type(exc).__name__, str(exc))
        fallback_points = ()

    if discovery.candidates:
        assert len(result.points) == 0
        assert all(
            candidates._evaluate_root_candidate(
                expression,
                variable,
                candidate,
                domain,
                context,
                overrides=None,
                source_label="f(x)",
            ).point
            is None
            for candidate in discovery.candidates
        )
        print("N1_MECHANISM=CANDIDATE_RESIDUAL_REJECTION")
    elif discovery.complete:
        assert len(result.points) == 0
        print("N1_MECHANISM=AUTHORITATIVE_EMPTY_DISCOVERY")
    else:
        print("N1_MECHANISM=UNRESOLVED_DISCOVERY")

    print("N1_ROOT_CAUSE_DIAGNOSTIC_STAGE3=PASS")


if __name__ == "__main__":
    main()
