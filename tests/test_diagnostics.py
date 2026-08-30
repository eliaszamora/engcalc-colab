import pytest

import engcalc_colab.errors as errors
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_diagnostic_hint_exposes_stable_numeric_bridge_codes():
    assert hasattr(errors, "diagnostic_hint")

    direct = errors.diagnostic_hint("direct_numeric_argument", example="M(2.5*m)")
    unknown = errors.diagnostic_hint("unknown_numeric_name", name="q_missing")
    incompatible = errors.diagnostic_hint("incompatible_function_units", function="f")
    unresolved = errors.diagnostic_hint("unresolved_numeric_symbols", names=("L",))

    assert "numeric(M(2.5*m))" in direct
    assert "q_missing :=" in unknown
    assert "f" in incompatible
    assert "L" in unresolved


def test_unknown_numeric_name_error_names_value_and_gives_assignment_hint():
    engine = EngineeringEngine()

    with pytest.raises(
        EngEvaluationError,
        match=r"unknown numeric name 'q_missing'.*q_missing :=",
    ):
        run(engine, "q := q_missing*kN/m")


def test_numeric_function_dimension_error_names_function_and_expected_fix():
    engine = EngineeringEngine()
    run(engine, "f(x) = L + x")
    run(engine, "L := 1*m")

    with pytest.raises(
        EngEvaluationError,
        match=r"incompatible units while evaluating numeric function 'f'.*compatible units",
    ):
        run(engine, "numeric(f(2*kN))")


def test_unresolved_numeric_symbols_error_names_values_and_gives_hint():
    engine = EngineeringEngine()
    run(engine, "A = q*L")
    run(engine, "q := 2*kN/m")

    with pytest.raises(
        EngEvaluationError,
        match=r"numeric evaluation requires values for: L.*L :=",
    ):
        run(engine, "numeric(A)")

def test_piecewise_missing_default_diagnostic():
    import pytest
    from engcalc_colab.errors import EngSyntaxError
    from engcalc_colab.parser import parse_cell
    with pytest.raises(EngSyntaxError, match=r"piecewise.*default"):
        parse_cell("q(x) = piecewise(q1, x < a)")

def test_piecewise_boolean_and_chained_conditions_are_rejected():
    import pytest
    from engcalc_colab.errors import EngSyntaxError
    from engcalc_colab.parser import parse_cell
    with pytest.raises(EngSyntaxError, match=r"piecewise condition.*direct comparison"):
        parse_cell("q(x) = piecewise(q1, x < a and x < L, 0)")
    with pytest.raises(EngSyntaxError, match=r"chained piecewise comparisons"):
        parse_cell("q(x) = piecewise(q1, 0 < x < a, 0)")

def test_piecewise_condition_must_compare_interval_variable_directly():
    import pytest
    from engcalc_colab.errors import EngSyntaxError
    from engcalc_colab.parser import parse_cell
    with pytest.raises(EngSyntaxError, match=r"interval variable directly"):
        parse_cell("q(x) = piecewise(q1, x + 1 < a, 0)")

def test_piecewise_unresolved_plot_breakpoint_is_corrective():
    import pytest
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.errors import EngEvaluationError
    from engcalc_colab.parser import parse_cell
    engine = EngineeringEngine()
    for item in parse_cell("q(x) = piecewise(q1, x < a, 0)\nq1 := 8*kN/m\nL := 6*m"):
        engine.evaluate(item)
    with pytest.raises(EngEvaluationError, match=r"Piecewise breakpoint.*a"):
        engine.evaluate(parse_cell("plot(q(x), x, 0, L)")[0])

def test_piecewise_incompatible_condition_units_are_identified():
    import pytest
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.errors import EngEvaluationError
    from engcalc_colab.parser import parse_cell
    engine = EngineeringEngine()
    for item in parse_cell("q(x) = piecewise(q1, x < a, 0)\nq1 := 8*kN/m\na := 3*m"):
        engine.evaluate(item)
    with pytest.raises(EngEvaluationError, match=r"piecewise comparison.*incompatible units"):
        engine.evaluate(parse_cell("numeric(q(2*s))")[0])

def test_piecewise_incompatible_branch_units_are_identified():
    import pytest
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.errors import EngEvaluationError
    from engcalc_colab.parser import parse_cell
    engine = EngineeringEngine()
    source = (
        "q(x) = piecewise(q1, x < a, d, x <= L, 0)\n"
        "q1 := 8*kN/m\nd := 2*m\na := 3*m\nL := 6*m"
    )
    for item in parse_cell(source):
        engine.evaluate(item)
    with pytest.raises(EngEvaluationError, match=r"piecewise branches.*incompatible"):
        engine.evaluate(parse_cell("numeric(q(x))")[0])

def test_piecewise_derivative_breakpoint_diagnostic_is_explicit():
    import pytest
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.errors import EngEvaluationError
    from engcalc_colab.parser import parse_cell
    engine = EngineeringEngine()
    source = (
        "q(x) = piecewise(c1*x^2, x < a, c2*x, x <= L, 0)\n"
        "dq(x) = diff(q(x), x)\n"
        "c1 := 2*kN/m^3\nc2 := 5*kN/m^2\na := 3*m\nL := 6*m"
    )
    for item in parse_cell(source):
        engine.evaluate(item)
    with pytest.raises(EngEvaluationError, match=r"derivative.*undefined.*Piecewise breakpoint"):
        engine.evaluate(parse_cell("numeric(dq(3*m))")[0])
