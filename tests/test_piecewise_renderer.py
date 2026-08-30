from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import RenderSettings, render_result


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def define_piecewise(engine: EngineeringEngine) -> None:
    run(engine, "q(x) = piecewise(q1, x < a, q2, x <= L, 0)")
    run(engine, "q1 := 8*kN/m")
    run(engine, "q2 := 4*kN/m")
    run(engine, "a := 3*m")
    run(engine, "L := 6*m")


def test_numeric_piecewise_partial_renders_formula_substitution_and_evaluated_cases():
    engine = EngineeringEngine()
    define_piecewise(engine)

    rendered = render_result(run(engine, "numeric(q(x))"))

    assert rendered.count(r"\begin{cases}") == 3
    assert "8.00" in rendered
    assert "4.00" in rendered
    assert "3.00" in rendered
    assert "6.00" in rendered
    assert r"\mathrm{kN}" in rendered or "kilonewton" in rendered


def test_result_piecewise_partial_omits_substitution_stage_but_keeps_final_cases():
    engine = EngineeringEngine()
    define_piecewise(engine)

    rendered = render_result(run(engine, "result(q(x))"))

    assert rendered.count(r"\begin{cases}") == 2
    assert "8.00" in rendered
    assert "4.00" in rendered
    assert "3.00" in rendered
    assert "6.00" in rendered


def test_piecewise_partial_rendering_honors_precision_and_zero_tolerance():
    engine = EngineeringEngine()
    run(engine, "q(x) = piecewise(q1, x < a, q2, x <= L, 0)")
    run(engine, "q1 := 8.1234*kN/m")
    run(engine, "q2 := 1e-12*kN/m")
    run(engine, "a := 3.126*m")
    run(engine, "L := 6*m")

    rendered = render_result(
        run(engine, "numeric(q(x))"),
        settings=RenderSettings(precision=2, zero_tolerance=1e-10),
    )

    assert "8.12" in rendered
    assert "3.13" in rendered
    assert "0.00" in rendered
    assert "8.1234" not in rendered
    assert "3.126" not in rendered
