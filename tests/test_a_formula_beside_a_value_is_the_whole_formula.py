r"""The formula a row shows beside its value is the whole formula, not its last call.

    y = 2*diff(x^2, x)                 y = d/dx x^2 = 4x          (d/dx x^2 is 2x)
    w = integrate(x, x, 0, 1) + 1      w = ∫_0^1 x dx = 3/2       (the integral is 1/2)
    M = [diff(x^2, x), diff(x^3, x)]   M = d/dx x^3 = [2x, 3x^2]

The value was always right; the equation beside it was false. A derivative or an integral
leaves its unevaluated form for the row to show, in one slot, and a statement with that
call inside something larger - a product, a sum, a matrix - showed only the form of the last
call as if it were the statement. Found on 2026-09-23 auditing, on the rendered page, the
matrix derivation he asked for, where `k_b = [diff(f_1, u_1), ...]` read as one derivative.

When the call is the whole statement the row is as it was. When it is inside something
larger the statement is read a second time with every derivative and integral left
standing, the way the written form is read a second time already: `2 d/dx x^2 = 4x`.
"""

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def magics(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    engine = magic.EngMagics()
    engine.captured = captured
    return engine


def run(magics, source: str) -> str:
    magics.captured.clear()
    magics.eng("", source)
    return "".join(getattr(obj, "data", "") for obj in magics.captured)


@pytest.mark.parametrize(
    ("source", "formula", "false"),
    [
        ("y = 2*diff(x^2, x)\n", r"2 \frac{d}{d x} x^{2} = 4 x", r"\displaystyle \frac{d}{d x} x^{2} = 4 x"),
        (
            "z = diff(x^2, x) + diff(x^3, x)\n",
            r"\frac{d}{d x} x^{2} + \frac{d}{d x} x^{3}",
            r"\displaystyle \frac{d}{d x} x^{3} = 3 x^{2} + 2 x",
        ),
        (
            "w = integrate(x, x, 0, 1) + 1\n",
            r"\int\limits_{0}^{1} x\, dx + 1",
            r"\displaystyle \int\limits_{0}^{1} x\, dx = \frac{3}{2}",
        ),
        (
            "M = [diff(x^2, x), diff(x^3, x)]\n",
            r"\frac{d}{d x} x^{2} & \displaystyle \frac{d}{d x} x^{3}",
            r"\displaystyle \frac{d}{d x} x^{3} = \left[",
        ),
    ],
)
def test_a_call_inside_a_statement_shows_the_whole_statement(magics, capsys, source, formula, false):
    page = run(magics, source)
    assert "engcalc:" not in capsys.readouterr().out
    assert formula in page, page
    assert false not in page, page


def test_a_matrix_of_derivatives_is_the_bar_s_stiffness(magics, capsys):
    """The case it was found in: every entry its own derivative."""
    page = run(
        magics,
        "N_b = E*A*(u_2 - u_1)/L\nf_1 = -N_b\nf_2 = N_b\n"
        "k_b = [diff(f_1, u_1), diff(f_1, u_2); diff(f_2, u_1), diff(f_2, u_2)]\n",
    )
    assert "engcalc:" not in capsys.readouterr().out
    assert page.count(r"\frac{\partial}{\partial u_{1}}") == 2, page
    assert page.count(r"\frac{\partial}{\partial u_{2}}") == 2, page


def test_an_integral_of_a_matrix_inside_a_product(magics, capsys):
    page = run(magics, "k = 2*integrate([x, x^2], x, 0, 1)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\int\limits_{0}^{1} x^{2}\, dx" in page, page
    assert page.count(r"\int\limits") == 2, page


def test_a_derivative_of_a_matrix_inside_a_product(magics, capsys):
    page = run(magics, "D = 2*diff([x^2, x^3], x)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\frac{d}{d x} x^{3}" in page and r"\frac{d}{d x} x^{2}" in page, page


def test_a_parameter_that_shares_a_defined_name_stays_the_parameter(magics, capsys):
    """`a = 3` then `f(a) = 2*integrate(t, t, 0, a)`: in the body `a` is the parameter,
    and the second reading must bind it as the first did, or the row reads `∫_0^3`."""
    page = run(magics, "a = 3\nf(a) = 2*integrate(t, t, 0, a)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"2 \int\limits_{0}^{a} t\, dt" in page, page


def test_the_constant_of_an_elastic_curve_is_on_its_row(magics, capsys):
    """The case the gap-map exercise E4 moved on: the constant written after the integral,
    the way the README tells an engineer to write it, was missing from the row."""
    page = run(magics, "M(x) = q*x*(L - x)/2\ntheta(x) = integrate(M(x)/(E*I), x) + C1\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"C_{1} + \int" in page, page


def test_a_function_whose_body_holds_a_call(magics, capsys):
    page = run(magics, "f(x) = 3*integrate(t, t, 0, x)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"3 \int\limits_{0}^{x} t\, dt" in page, page


@pytest.mark.parametrize(
    ("source", "row"),
    [
        # The call is the whole statement: the row is as it was.
        ("v = diff(x^3, x)\n", r"v & = & \displaystyle \frac{d}{d x} x^{3} = 3 x^{2}"),
        ("I_1 = integrate(x, x, 0, 1)\n", r"\int\limits_{0}^{1} x\, dx = \frac{1}{2}"),
    ],
)
def test_a_statement_that_is_its_call_is_unchanged(magics, capsys, source, row):
    page = run(magics, source)
    assert "engcalc:" not in capsys.readouterr().out
    assert row in page, page
