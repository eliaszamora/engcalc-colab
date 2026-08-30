import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import _characteristic_requests


def _eval_cell(engine, source: str):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def _dense_six_series_moment_plot():
    engine = EngineeringEngine()
    _eval_cell(
        engine,
        """
        L := 4*m

        A1 := -6*tonf*m
        C1 := 1.50*tonf/m
        B1 := 7.50*tonf

        A2 := -22.4*tonf*m
        C2 := 5.00*tonf/m
        B2 := 25.00*tonf

        A3 := -8*tonf*m
        C3 := 2.00*tonf/m
        B3 := 10.00*tonf

        A4 := -19.2*tonf*m
        C4 := 4.80*tonf/m
        B4 := 24.00*tonf

        A5 := -14*tonf*m
        C5 := 3.50*tonf/m
        B5 := 17.50*tonf

        A6 := -16*tonf*m
        C6 := 4.20*tonf/m
        B6 := 21.00*tonf

        M_C1(x) = A1 + B1*x - C1*x^2
        M_C2(x) = A2 + B2*x - C2*x^2
        M_S1(x) = A3 + B3*x - C3*x^2
        M_S2(x) = A4 + B4*x - C4*x^2
        M_S3(x) = A5 + B5*x - C5*x^2
        M_S4(x) = A6 + B6*x - C6*x^2
        """,
    )
    return _eval_cell(
        engine,
        "plot(M_C1(x), M_C2(x), M_S1(x), M_S2(x), M_S3(x), M_S4(x), x, 0, L)",
    )[-1]


def test_characteristic_requests_are_single_authoritative_sequence():
    requests = _characteristic_requests(_dense_six_series_moment_plot())

    assert len(requests) == 12
    assert [(item.series_index, item.role) for item in requests] == [
        (0, "max"),
        (0, "min"),
        (1, "max"),
        (1, "min"),
        (2, "max"),
        (2, "min"),
        (3, "max"),
        (3, "min"),
        (4, "max"),
        (4, "min"),
        (5, "max"),
        (5, "min"),
    ]
    assert [float(item.x_quantity.magnitude) for item in requests[::2]] == pytest.approx(
        [2.5] * 6
    )
    assert [float(item.x_quantity.magnitude) for item in requests[1::2]] == pytest.approx(
        [0.0] * 6
    )
    assert [float(item.y_quantity.magnitude) for item in requests[::2]] == pytest.approx(
        [3.375, 8.85, 4.5, 10.8, 7.875, 10.25]
    )
    assert [float(item.y_quantity.magnitude) for item in requests[1::2]] == pytest.approx(
        [-6.0, -22.4, -8.0, -19.2, -14.0, -16.0]
    )
    assert [item.series.display_label for item in requests[::2]] == [
        "M_C1(x)",
        "M_C2(x)",
        "M_S1(x)",
        "M_S2(x)",
        "M_S3(x)",
        "M_S4(x)",
    ]
    assert all(item.inverted for item in requests)
