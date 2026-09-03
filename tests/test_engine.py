import sympy as sp

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import AmbiguousSolveError, EngEvaluationError
from engcalc_colab.parser import parse_cell


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def test_auto_symbols_and_integral():
    engine = EngineeringEngine()
    results = eval_cell(engine, """
M_0 = -q/2*(L-x)^2
m_B = L-x
Delta_B = integrate(M_0*m_B/(E*I), x, 0, L)
""")
    q, L, E, I = tuple(engine.resolve_symbol(name) for name in "q L E I".split())
    assert sp.simplify(results[-1].value + q*L**4/(8*E*I)) == 0


def test_function_assignment_and_call():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = R_A - q*x")
    result = eval_cell(engine, "x_crit = solve(V(x) = 0, x)")[-1]
    R_A, q = tuple(engine.resolve_symbol(name) for name in "R_A q".split())
    assert sp.simplify(result.value - R_A/q) == 0


def test_supported_symbolic_operations():
    engine = EngineeringEngine()
    eval_cell(engine, "F(x) = (x+1)^2")
    assert str(eval_cell(engine, "dF = diff(F(x), x)")[-1].value) == "2*x + 2"
    assert str(eval_cell(engine, "expanded = expand(F(x))")[-1].value) == "x**2 + 2*x + 1"
    assert str(eval_cell(engine, "factored = factor(expanded)")[-1].value) == "(x + 1)**2"
    assert str(eval_cell(engine, "simple = simplify(expanded - x^2)")[-1].value) == "2*x + 1"
    assert eval_cell(engine, "at2 = subs(F(x), x, 2)")[-1].value == 9


def test_abs_builds_sympy_absolute_value():
    engine = EngineeringEngine()
    result = eval_cell(engine, "A = abs(x - 3)")[-1]
    x = engine.resolve_symbol("x")
    assert result.value == sp.Abs(x - 3)


def test_abs_rejects_zero_arguments():
    engine = EngineeringEngine()
    with pytest_raises(EngEvaluationError) as captured:
        eval_cell(engine, "A = abs()")
    assert str(captured.value) == "line 1: abs expects 1 argument: expression"


def test_abs_rejects_multiple_arguments():
    engine = EngineeringEngine()
    with pytest_raises(EngEvaluationError) as captured:
        eval_cell(engine, "A = abs(x, 2)")
    assert str(captured.value) == "line 1: abs expects 1 argument: expression"


def test_numeric_accepts_abs_and_preserves_units():
    engine = EngineeringEngine()
    eval_cell(engine, "P := -7*tonf")
    result = eval_cell(engine, "numeric(abs(P))")[-1]
    assert result.quantity.to("tonf").magnitude == 7.0


def test_state_reset_removes_assignments():
    engine = EngineeringEngine()
    eval_cell(engine, "A = q*L")
    engine.reset()
    assert "A" not in engine.namespace


def test_propped_cantilever_reference_solution():
    engine = EngineeringEngine()
    results = eval_cell(engine, """
M_0 = -q/2*(L-x)^2
m_B = L-x
Delta_B = integrate(M_0*m_B/(E*I), x, 0, L)
f_BB = integrate(m_B^2/(E*I), x, 0, L)
R_B = solve(Delta_B + R_B*f_BB = 0, R_B)
""")
    q, L, E, I = tuple(engine.resolve_symbol(name) for name in "q L E I".split())
    values = {r.statement.target: r.value for r in results}
    assert sp.simplify(values["Delta_B"] + q*L**4/(8*E*I)) == 0
    assert sp.simplify(values["f_BB"] - L**3/(3*E*I)) == 0
    assert sp.simplify(values["R_B"] - 3*q*L/8) == 0


def test_assigning_a_multi_solution_solve_is_concise_and_line_aware():
    """The subject of this test changed in 0.14.0; its intent did not.

    Two solutions used to be an error in itself - `AmbiguousSolveError`, "v0.1 requires
    one" - and they are now shown instead. What is still an error is *assigning* them,
    because there is no single value to bind, and that error must stay concise, carry
    its line, and say what to use instead.
    """
    engine = EngineeringEngine()
    with pytest_raises(EngEvaluationError) as captured:
        eval_cell(engine, "R = solve(x^2 = 1, x)")
    message = str(captured.value)
    assert message.startswith("line 1: solve returned 2 solutions")
    assert "roots(expression, variable, lower, upper)" in message
    assert len(message.splitlines()) == 1, "the message must stay one line"


def test_integrate_wrong_arity_is_concise_and_line_aware():
    engine = EngineeringEngine()
    with pytest_raises(EngEvaluationError) as captured:
        eval_cell(engine, "A = integrate(x, x, 0)")
    assert str(captured.value) == "line 1: integrate expects 2 arguments (expression, variable) for an indefinite integral, or 4 (expression, variable, lower, upper) for a definite one; got 3"


def test_rejects_function_scalar_kind_conflict():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = R_A - q*x")
    with pytest_raises(EngEvaluationError) as captured:
        eval_cell(engine, "V = 3")
    assert "redefinition conflict" in str(captured.value)


class pytest_raises:
    def __init__(self, exc_type):
        self.exc_type = exc_type
        self.value = None
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            raise AssertionError(f"expected {self.exc_type.__name__}")
        if not issubclass(exc_type, self.exc_type):
            return False
        self.value = exc
        return True


def test_solve_unknown_stays_symbolic_when_cell_is_reexecuted():
    engine = EngineeringEngine()
    cell = """
M_0 = -q/2*(L-x)^2
m_B = L-x
Delta_B = integrate(M_0*m_B/(E*I), x, 0, L)
f_BB = integrate(m_B^2/(E*I), x, 0, L)
R_B = solve(Delta_B + R_B*f_BB = 0, R_B)
"""
    first = eval_cell(engine, cell)[-1].value
    second = eval_cell(engine, cell)[-1].value
    q, L = tuple(engine.resolve_symbol(name) for name in "q L".split())
    assert sp.simplify(first - 3*q*L/8) == 0
    assert sp.simplify(second - first) == 0


def test_sum_builds_unevaluated_symbolic_sum():
    engine = EngineeringEngine()
    result = eval_cell(engine, "S = sum(F_i, i, 0, n)")[-1]
    F_i, i, n = tuple(engine.resolve_symbol(name) for name in "F_i i n".split())
    assert result.value == sp.Sum(F_i, (i, 0, n))


def test_sum_requires_symbolic_index_identifier():
    engine = EngineeringEngine()
    with pytest_raises(EngEvaluationError) as captured:
        eval_cell(engine, "S = sum(F_i, i + 1, 0, n)")
    assert str(captured.value) == "line 1: sum index must be a symbolic identifier"
