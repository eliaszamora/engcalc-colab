from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import RenderSettings, _display_rows, _latex_visual_width


ROW_LIMIT = 104.0


def eval_cell(engine, text):
    return [engine.evaluate(stmt) for stmt in parse_cell(text)]


def assert_rows_bounded(rows):
    widths = [_latex_visual_width(row) for row in rows]
    assert widths
    assert max(widths) <= ROW_LIMIT, (max(widths), rows)


def propped_symbolic_results():
    engine = EngineeringEngine()
    source = """
delta_B = integral((-q*(L-s)^2/2 + R_B_aux*(L-s))*(L-s), s, 0, L)
R_B(q) = solve(eq(delta_B, 0), R_B_aux)
R_A(q) = solve(eq(R_A_aux + R_B(q) - q*L, 0), R_A_aux)
M_A(q) = solve(eq(M_A_aux + q*L^2/2 - R_B(q)*L, 0), M_A_aux)
"""
    return eval_cell(engine, source)


def test_long_integral_uses_bounded_operation_and_result_rows():
    result = propped_symbolic_results()[0]
    rows = _display_rows(result, RenderSettings())
    assert len(rows) >= 3
    assert any(r"\int" in row for row in rows)
    assert_rows_bounded(rows)


def test_long_solve_equations_do_not_create_ambiguous_assignment_chains():
    for result in propped_symbolic_results()[1:]:
        rows = _display_rows(result, RenderSettings())
        assert len(rows) >= 2
        assert all(row.count(" = ") <= 1 for row in rows)
        assert_rows_bounded(rows)


def test_long_solve_keeps_long_equation_out_of_left_identity_column():
    result = propped_symbolic_results()[1]
    rows = _display_rows(result, RenderSettings())
    equation_rows = rows[:-1]
    assert equation_rows
    assert all(row.lstrip().startswith("&") for row in equation_rows)
    assert "R_{B}" in rows[-1]


def test_short_symbolic_result_remains_compact_single_row():
    engine = EngineeringEngine()
    result = eval_cell(engine, "R = 3*q*L/8")[-1]
    rows = _display_rows(result, RenderSettings())
    assert len(rows) == 1
    assert_rows_bounded(rows)


def test_long_numeric_muu_substitution_is_bounded_stage_by_stage():
    engine = EngineeringEngine()
    source = """
L := 4*m
x0 := 0*m
qD := 4*tonf/m
qL := 3*tonf/m
gD := 1.2
gL := 1.6
M_D(x) = -qD*L^2/8 + 5*qD*L*x/8 - qD*x^2/2
M_L(x) = -qL*L^2/8 + 5*qL*L*x/8 - qL*x^2/2
M_UU(x) = gD*M_D(x) + gL*M_L(x)
numeric(M_UU(x0))
"""
    result = eval_cell(engine, source)[-1]
    rows = _display_rows(result, RenderSettings())
    assert len(rows) >= 5
    assert "-19.20" in rows[-1]
    assert_rows_bounded(rows)
