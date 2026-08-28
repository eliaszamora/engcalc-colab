from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import RenderSettings, _display_rows, render_aligned_results


def evaluate(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_short_symbolic_assignment_stays_on_one_row():
    engine = EngineeringEngine()
    result = evaluate(engine, "V(x) = R_A - q*x")

    rows = _display_rows(result, RenderSettings())

    assert len(rows) == 1


def test_long_symbolic_integral_breaks_input_and_evaluated_expression_across_rows():
    engine = EngineeringEngine()
    result = evaluate(
        engine,
        "delta_B = integral((-q*(L-s)^2/2 + R_B_aux*(L-s))*(L-s), s, 0, L)",
    )

    rows = _display_rows(result, RenderSettings())
    latex = render_aligned_results([result])

    assert len(rows) >= 2
    assert r"\int" in latex
    assert r"\\[4pt]" in latex
    assert r"\\[2pt]" not in latex


def test_long_solve_equation_is_wrapped_and_solution_gets_its_own_row():
    engine = EngineeringEngine()
    evaluate(
        engine,
        "delta_B = integral((-q*(L-s)^2/2 + R_B_aux*(L-s))*(L-s), s, 0, L)",
    )
    result = evaluate(engine, "R_B(q) = solve(delta_B, R_B_aux)")

    rows = _display_rows(result, RenderSettings())
    latex = render_aligned_results([result])

    assert len(rows) >= 3
    assert r"\\[4pt]" in latex
    assert r"\\[8pt]" in latex
    assert r"\\[2pt]" not in latex
    assert "R_{B}" in latex
    assert "3 q L" in latex
