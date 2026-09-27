r"""`extrema` over a function whose value is an angle.

`L := 4*m`, `h(x) = atan(x/L)`, `extrema(h(x), x, 0*m, L)` stopped with "extrema response
values have incompatible dimensions" (found on 0.40.0 with the angles in degrees, still on
0.41.1). The values were `0 rad` and `0.785 rad`, and the guard that refuses a plain number
beside a unit asked whether the unit *was* `dimensionless`; a radian is not that unit, and
Pint counts it without dimension. It now asks whether the unit has a dimension, in the exact
path and in the numerical one.
"""

import contextlib
import io

import pytest

import engcalc_colab.magic as magic
from engcalc_colab.characteristics import extrema, fallback
from engcalc_colab.numeric import NumericContext


def run(source: str, monkeypatch) -> tuple[str, str]:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", source)
    return "".join(getattr(obj, "data", "") for obj in captured), console.getvalue()


@pytest.mark.parametrize(
    "source, rows",
    [
        (
            "L := 4*m\nh(x) = atan(x/L)\nextrema(h(x), x, 0*m, L)\n",
            [
                r"\text{boundary, global min}",
                r"\text{boundary, global max}",
                # A computed angle in degrees, the sign against the number as a row
                # writes it (0.41.0), not `45.00\,{}^{\circ}`.
                r"\dfrac{\pi}{4}\,\left(45.00^{\circ}\right)",
            ],
        ),
        (
            "g(x) = asin(x/2)\nextrema(g(x), x, -1, 1)\n",
            [
                r"\text{boundary, global min}",
                r"\text{boundary, global max}",
                r"\left(-30.00^{\circ}\right)",
            ],
        ),
    ],
)
def test_an_angle_has_its_extrema(monkeypatch, source, rows):
    page, console = run(source, monkeypatch)
    assert "engcalc:" not in console, console
    for row in rows:
        assert row in page, page


READERS = [extrema._extrema_magnitude_in_unit, fallback._fallback_magnitude_in_unit]


@pytest.mark.parametrize("reader", READERS)
@pytest.mark.parametrize("magnitude", [0.0, 0.785398163])
def test_a_radian_reads_in_radians(reader, magnitude):
    """The numerical path answered `None` for it - the sample dropped, in silence."""
    context = NumericContext()
    radian = context.ureg.radian
    assert reader(context.ureg.Quantity(magnitude, radian), radian, context) == pytest.approx(magnitude)


def test_a_plain_number_beside_a_length_is_still_refused():
    """What the guard is for: a response that is `2` at one point and `3 m` at another."""
    context = NumericContext()
    two = context.ureg.Quantity(2.0, "dimensionless")
    with pytest.raises(Exception, match="incompatible dimensions"):
        extrema._extrema_magnitude_in_unit(two, context.ureg.meter, context)
    assert fallback._fallback_magnitude_in_unit(two, context.ureg.meter, context) is None


def test_a_zero_takes_the_unit_of_the_others():
    """And the reason the guard lets a zero through: `0` beside `3 m` is `0 m`."""
    context = NumericContext()
    zero = context.ureg.Quantity(0.0, "dimensionless")
    for reader in READERS:
        assert reader(zero, context.ureg.meter, context) == 0.0
