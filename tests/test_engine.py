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
Delta_B = integral(M_0*m_B/(E*I), x, 0, L)
""")
    q, L, E, I = sp.symbols("q L E I")
    assert sp.simplify(results[-1].value + q*L**4/(8*E*I)) == 0


def test_function_assignment_and_call():
    engine = EngineeringEngine()
    eval_cell(engine, "V(x) = R_A - q*x")
    result = eval_cell(engine, "x_crit = solve(V(x) = 0, x)")[-1]
    R_A, q = sp.symbols("R_A q")
    assert sp.simplify(result.value - R_A/q) == 0


def test_supported_symbolic_operations():
    engine = EngineeringEngine()
    eval_cell(engine, "F(x) = (x+1)^2")
    assert str(eval_cell(engine, "dF = diff(F(x), x)")[-1].value) == "2*x + 2"
    assert str(eval_cell(engine, "expanded = expand(F(x))")[-1].value) == "x**2 + 2*x + 1"
    assert str(eval_cell(engine, "factored = factor(expanded)")[-1].value) == "(x + 1)**2"
    assert str(eval_cell(engine, "simple = simplify(expanded - x^2)")[-1].value) == "2*x + 1"
    assert eval_cell(engine, "at2 = subs(F(x), x, 2)")[-1].value == 9


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
Delta_B = integral(M_0*m_B/(E*I), x, 0, L)
f_BB = integral(m_B^2/(E*I), x, 0, L)
R_B = solve(Delta_B + R_B*f_BB = 0, R_B)
""")
    q, L, E, I = sp.symbols("q L E I")
    values = {r.statement.target: r.value for r in results}
    assert sp.simplify(values["Delta_B"] + q*L**4/(8*E*I)) == 0
    assert sp.simplify(values["f_BB"] - L**3/(3*E*I)) == 0
    assert sp.simplify(values["R_B"] - 3*q*L/8) == 0


def test_ambiguous_solve_is_concise_and_line_aware():
    engine = EngineeringEngine()
    with pytest_raises(AmbiguousSolveError) as captured:
        eval_cell(engine, "R = solve(x^2 = 1, x)")
    assert str(captured.value) == "line 1: solve returned 2 solutions for x; v0.1 requires one"


def test_integral_wrong_arity_is_concise_and_line_aware():
    engine = EngineeringEngine()
    with pytest_raises(EngEvaluationError) as captured:
        eval_cell(engine, "A = integral(x, x, 0)")
    assert str(captured.value) == "line 1: integral expects 4 arguments: expression, variable, lower, upper"


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
