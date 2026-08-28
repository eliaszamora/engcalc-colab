from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import _display_rows, render_aligned_results


def _eval_cell(source: str):
    engine = EngineeringEngine()
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def test_solve_uses_eight_points_between_equation_and_solved_assignment():
    result = _eval_cell("R_Ac = solve(eq(R_Ac - qC*L, 0), R_Ac)")[-1]
    latex = render_aligned_results([result])

    assert r"\\[8pt]" in latex
    assert r"\\[2pt]" not in latex


def test_numeric_uses_eight_points_between_formula_substitution_and_result():
    result = _eval_cell(
        "M_A = q*L^2/2\n"
        "q := 2*tonf/m\n"
        "L := 4*m\n"
        "numeric(M_A)"
    )[-1]
    latex = render_aligned_results([result])

    assert latex.count(r"\\[8pt]") == 2
    assert r"\\[2pt]" not in latex


def test_wrapped_single_stage_uses_four_point_continuation_spacing():
    terms = " + ".join(f"a{i:02d}" for i in range(1, 41))
    result = _eval_cell(f"A = {terms}")[-1]
    rows = _display_rows(result, settings=None)
    assert len(rows) >= 2

    latex = render_aligned_results([result])
    assert r"\\[4pt]" in latex
    assert r"\\[2pt]" not in latex
    assert r"\\[8pt]" not in latex
