import sympy as sp

import engcalc_colab.renderer as renderer
from engcalc_colab.models import (
    CharacteristicInterval,
    CharacteristicPoint,
    ExtremaResult,
    IntersectionsResult,
    RootsResult,
)
from engcalc_colab.numeric import NumericContext
from engcalc_colab.parser import parse_cell


_CONTEXT = NumericContext()
_UREG = _CONTEXT.ureg


def _render(result):
    assert hasattr(
        renderer,
        "render_characteristic_result",
    ), "renderer must expose render_characteristic_result"
    return renderer.render_characteristic_result(result)


def _roots_result(*, provenance: str = "exact") -> RootsResult:
    x_symbolic = sp.Symbol("L") / 2 if provenance == "exact" else sp.Float("3.0")
    return RootsResult(
        statement=parse_cell("roots(V(x), x, 0, L)")[0],
        display_label="V(x)",
        variable="x",
        lower_quantity=_UREG.Quantity(0, "m"),
        upper_quantity=_UREG.Quantity(6, "m"),
        points=(
            CharacteristicPoint(
                x_symbolic=x_symbolic,
                x_quantity=_UREG.Quantity(3, "m"),
                value_symbolic=sp.Integer(0),
                value_quantity=_UREG.Quantity(0, "kN"),
                provenance=provenance,
                source_label="V(x)",
            ),
        ),
    )


def test_root_renderer_uses_exact_and_approximate_symbols_with_units():
    exact_html = _render(_roots_result(provenance="exact"))
    numeric_html = _render(_roots_result(provenance="numeric"))

    assert "=" in exact_html
    assert "≈" not in exact_html
    assert "≈" in numeric_html
    assert "m" in exact_html
    assert "CharacteristicPoint(" not in exact_html
    assert "CharacteristicPoint(" not in numeric_html


def test_extrema_renderer_includes_global_role_and_piecewise_side():
    result = ExtremaResult(
        statement=parse_cell("extrema(M(x), x, 0, L)")[0],
        display_label="M(x)",
        variable="x",
        lower_quantity=_UREG.Quantity(0, "m"),
        upper_quantity=_UREG.Quantity(4, "m"),
        points=(
            CharacteristicPoint(
                x_symbolic=sp.Integer(2),
                x_quantity=_UREG.Quantity(2, "m"),
                value_symbolic=sp.Integer(10),
                value_quantity=_UREG.Quantity(10, "kN*m"),
                provenance="exact",
                side="left",
                roles=("local_max", "global_max"),
                source_label="M(x)",
            ),
        ),
    )

    html = _render(result)

    assert "global max" in html.lower()
    assert "left" in html.lower()
    assert "kN" in html
    assert "CharacteristicPoint(" not in html


def test_root_interval_locus_is_rendered_explicitly():
    result = RootsResult(
        statement=parse_cell("roots(f(x), x, 0, L)")[0],
        display_label="f(x)",
        variable="x",
        lower_quantity=_UREG.Quantity(0, "m"),
        upper_quantity=_UREG.Quantity(4, "m"),
        points=(),
        intervals=(
            CharacteristicInterval(
                lower_symbolic=sp.Integer(1),
                upper_symbolic=sp.Integer(3),
                lower_quantity=_UREG.Quantity(1, "m"),
                upper_quantity=_UREG.Quantity(3, "m"),
                role="roots",
                lower_closed=True,
                upper_closed=False,
            ),
        ),
    )

    html = _render(result)

    assert "all x in" in html.lower()
    assert "1.00" in html
    assert "3.00" in html
    assert "CharacteristicInterval(" not in html


def test_intersection_coincident_interval_is_rendered_explicitly():
    result = IntersectionsResult(
        statement=parse_cell("intersections(f(x), g(x), x, 0, L)")[0],
        left_label="f(x)",
        right_label="g(x)",
        variable="x",
        lower_quantity=_UREG.Quantity(0, "m"),
        upper_quantity=_UREG.Quantity(4, "m"),
        points=(),
        intervals=(
            CharacteristicInterval(
                lower_symbolic=sp.Integer(1),
                upper_symbolic=sp.Integer(3),
                lower_quantity=_UREG.Quantity(1, "m"),
                upper_quantity=_UREG.Quantity(3, "m"),
                role="coincident",
            ),
        ),
    )

    html = _render(result)

    assert "coincident on" in html.lower()
    assert "f(x)" in html
    assert "g(x)" in html
    assert "CharacteristicInterval(" not in html


def test_unbounded_extrema_state_is_rendered_without_python_repr():
    result = ExtremaResult(
        statement=parse_cell("extrema(f(x), x, 0, 1)")[0],
        display_label="f(x)",
        variable="x",
        lower_quantity=_UREG.Quantity(0, "dimensionless"),
        upper_quantity=_UREG.Quantity(1, "dimensionless"),
        points=(),
        unbounded_above=True,
        unbounded_below=False,
    )

    html = _render(result)

    assert "unbounded above" in html.lower()
    assert "ExtremaResult(" not in html
    assert "CharacteristicPoint(" not in html


def test_characteristic_rendering_normalizes_negative_zero_with_tolerance():
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.renderer import RenderSettings

    engine = EngineeringEngine()
    result = [
        engine.evaluate(statement)
        for statement in parse_cell(
            "roots((x-1)*(x-1.0000001), x, 0, 2)"
        )
    ][-1]
    html = renderer.render_characteristic_result(
        result,
        settings=RenderSettings(zero_tolerance=1e-10),
    )
    assert "-0.00" not in html
    assert "-0.0" not in html
    assert "-0\\," not in html
