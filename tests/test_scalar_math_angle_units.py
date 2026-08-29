import pytest
from IPython.display import Math

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import NumericEvaluationResult
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_exact_numeric_inverse_trig_retains_radian_unit():
    engine = EngineeringEngine()

    result = run(engine, "numeric(atan(1))")

    assert isinstance(result, NumericEvaluationResult)
    assert str(result.quantity.units) == "radian"
    assert result.quantity.to("rad").magnitude == pytest.approx(0.7853981633974483)


def test_eng_magic_renders_radian_unit_for_inverse_trig_assignment(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng("", "a := atan(1)")

    assert [type(item) for item in displayed] == [Math]
    assert "rad" in displayed[0].data


def test_eng_magic_renders_requested_degree_unit_for_inverse_trig_numeric(monkeypatch):
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)

    magics = magic_module.EngMagics(shell=None)
    magics.eng("", "numeric(atan(1), deg)")

    assert [type(item) for item in displayed] == [Math]
    assert "deg" in displayed[0].data


@pytest.mark.parametrize("function_name", ["asin", "acos", "atan", "exp", "log"])
@pytest.mark.parametrize("angle_unit", ["deg", "rad"])
def test_dimensionless_only_scalar_functions_reject_explicit_angle_units(
    function_name, angle_unit
):
    engine = EngineeringEngine()

    with pytest.raises(EngEvaluationError, match="requires a dimensionless argument"):
        run(engine, f"value := {function_name}(0.5*{angle_unit})")


def test_user_function_inverse_trig_retains_radian_unit_after_substitution():
    engine = EngineeringEngine()
    run(engine, "f(x) = atan(x)")
    run(engine, "a = f(1)")

    result = run(engine, "numeric(a)")

    assert isinstance(result, NumericEvaluationResult)
    assert str(result.quantity.units) == "radian"
    assert result.quantity.to("rad").magnitude == pytest.approx(0.7853981633974483)
