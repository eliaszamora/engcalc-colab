import sympy as sp

from engcalc_colab.characteristics import _exact_real_solution_set, normalize_analysis_domain
from engcalc_colab.engine import EngineeringEngine, _Evaluator
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell

engine = EngineeringEngine()
for statement in parse_cell(
    "L := 6*m\n"
    "K(x) = [x + L, 0; 0, 2*x + L]"
):
    engine.evaluate(statement)

statement = parse_cell("roots(K(x)[1,1] - 7*m, x, 0, L)")[0]
call = statement.expression.body
response_node = call.args[0]
variable = "x"
evaluator = _Evaluator(engine, statement.matrix_literals)
resolved = evaluator._resolve_response_expression(response_node, variable)
expression = sp.sympify(resolved.comparison_expression)
x = engine.resolve_symbol(variable)
domain = normalize_analysis_domain(engine.numeric_context, sp.Integer(0), engine.resolve_symbol("L"))
candidates, unresolved = _exact_real_solution_set(expression, x)

print("RESOLVED_EXPRESSION", repr(expression))
print("FREE_SYMBOLS", sorted(symbol.name for symbol in expression.free_symbols))
print("EXACT_CANDIDATES", tuple(map(repr, candidates)), "UNRESOLVED", unresolved)
for candidate in candidates:
    print("CANDIDATE", repr(candidate), "FREE", sorted(symbol.name for symbol in candidate.free_symbols))
    try:
        _, quantity = engine.numeric_context.evaluate_symbolic(candidate)
        print("CANDIDATE_QUANTITY", quantity)
    except EngEvaluationError as exc:
        print("CANDIDATE_EVAL_ERROR", str(exc))
    try:
        _, quantity = engine.numeric_context.evaluate_symbolic(
            expression,
            overrides={"x": engine.numeric_context.ureg.Quantity(1, "m")},
        )
        print("EXPRESSION_AT_1M", quantity)
    except EngEvaluationError as exc:
        print("EXPRESSION_AT_1M_ERROR", str(exc))
