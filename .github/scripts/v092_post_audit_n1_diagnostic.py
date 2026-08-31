from __future__ import annotations

import sympy as sp

import engcalc_colab.characteristics.candidates as candidates
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
    floats = sorted(
        ((str(value), repr(value), value._prec) for value in expression.atoms(sp.Float)),
        key=lambda item: item[0],
    )
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
    print("REPR=", repr(expression))
    print("SREPR=", sp.srepr(expression))
    print("FLOATS=", floats)
    print("VARIABLE=", repr(x), x.assumptions0)
    print("FREE_SYMBOLS=", [(repr(s), s.assumptions0) for s in expression.free_symbols])
    print("VARIABLE_IN_FREE_SYMBOLS=", x in expression.free_symbols)
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

    solver_expression = sp.sympify(captured["expression"])
    solver_variable = captured["variable"]
    print("STORED_EQ_SOLVER=", stored_expression == solver_expression)
    print("GLOBAL_X_EQ_SOLVER_VARIABLE=", global_x == solver_variable)
    print("STORED_MINUS_SOLVER=", repr(sp.expand(stored_expression - solver_expression)))

    # The public failure must be reproduced while the stored expression remains solvable.
    stored_discovery = candidates._coerce_exact_discovery(
        candidates._exact_real_solution_set(stored_expression, global_x)
    )
    solver_discovery = candidates._coerce_exact_discovery(
        candidates._exact_real_solution_set(solver_expression, solver_variable)
    )
    print("STORED_DISCOVERY=", stored_discovery)
    print("SOLVER_DISCOVERY=", solver_discovery)
    assert len(stored_discovery.candidates) == 2
    assert len(result.points) == 0
    print("N1_ROOT_CAUSE_DIAGNOSTIC_STAGE2=PASS")


if __name__ == "__main__":
    main()
