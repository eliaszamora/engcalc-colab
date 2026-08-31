from __future__ import annotations

import sympy as sp

import engcalc_colab.characteristics.candidates as candidates
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell


def evaluate_cell(engine: EngineeringEngine, source: str):
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


def inspect(label: str, expression: sp.Expr, x: sp.Symbol) -> None:
    expression = sp.sympify(expression)
    floats = sorted(
        (
            (str(value), repr(value), value._prec)
            for value in expression.atoms(sp.Float)
        ),
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
    print("FREE_SYMBOLS=", [(repr(s), s.assumptions0) for s in expression.free_symbols])
    print("SOLVESET=", repr(solveset_result))
    print("SOLVE=", repr(solve_result))
    print("DISCOVERY_CANDIDATES=", repr(discovery.candidates))
    print("DISCOVERY_COMPLETE=", discovery.complete)


def main() -> None:
    engine = EngineeringEngine()
    evaluate_cell(engine, "f(x) = 2.87*x^2 + -12.50459*x + 6.4876637")
    engine_expression = engine.functions["f"].expression
    x = engine.resolve_symbol("x")

    decimal_string_expression = (
        sp.Float("2.87") * x**2
        - sp.Float("12.50459") * x
        + sp.Float("6.4876637")
    )
    python_float_expression = (
        sp.Float(float("2.87")) * x**2
        - sp.Float(float("12.50459")) * x
        + sp.Float(float("6.4876637"))
    )

    inspect("ENGINE", engine_expression, x)
    inspect("DECIMAL_STRING_FLOAT", decimal_string_expression, x)
    inspect("PYTHON_FLOAT", python_float_expression, x)

    print("ENGINE_EQ_DECIMAL_STRING=", engine_expression == decimal_string_expression)
    print("ENGINE_EQ_PYTHON_FLOAT=", engine_expression == python_float_expression)
    print("ENGINE_MINUS_DECIMAL=", repr(sp.expand(engine_expression - decimal_string_expression)))
    print("ENGINE_MINUS_PYTHON=", repr(sp.expand(engine_expression - python_float_expression)))

    assert engine_expression == python_float_expression
    assert engine_expression != decimal_string_expression

    engine_discovery = candidates._coerce_exact_discovery(
        candidates._exact_real_solution_set(engine_expression, x)
    )
    decimal_discovery = candidates._coerce_exact_discovery(
        candidates._exact_real_solution_set(decimal_string_expression, x)
    )
    assert engine_discovery.candidates == ()
    assert engine_discovery.complete is True
    assert len(decimal_discovery.candidates) == 2
    assert decimal_discovery.complete is True
    print("N1_ROOT_CAUSE_DIAGNOSTIC=PASS")


if __name__ == "__main__":
    main()
