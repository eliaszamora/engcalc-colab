r"""A characteristic block names what it analyses in mathematics, not in Python.

`roots` on a two-storey frame, the frequencies of `det(K - w²M)`:

    Roots — k_1*k_2 - k_1*m_2*w**2 - k_2*m_1*w**2 - k_2*m_2*w**2 + m_1*m_2*w**4
    w = √2 √(k₁/m₁ + k₂/m₂ + ...)

The roots under that heading were typeset; the heading was `str()` of the expression.
#133 moved a block's *values* to the page's printer - its docstring calls
`L**2*(0.15*qD + 0.2*qL)` "Python, in a memoria" - and the heading kept the spelling.

**Why.** A response given as a user function is labelled `M(x)`, which is how a person
writes it. Anything else was labelled `str(expression)`, and for a defined name that is
the whole expression it stands for: `roots(p, w, 0, 200/s)` printed the polynomial rather
than `p`.

**So the heading typesets its response**: a name as that name, any other expression with
the printer the block's values use. The label *text* is untouched - a figure's legend and a
governing block still read it - and a user function still reads `M(x)`.
"""

import re

import engcalc_colab.magic as magic


def headings(monkeypatch, source: str) -> list[str]:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", source)
    raw = "".join(str(getattr(obj, "data", "")) for obj in captured)
    found = re.findall(r'font-weight:600;margin-bottom:0\.15rem;">(.*?)</div>', raw)
    assert found, raw
    return found


FRAME = (
    "k_1 := 2000*kN/m\nk_2 := 1500*kN/m\nm_1 := 600*kg\nm_2 := 500*kg\n"
    "K = [k_1 + k_2, -k_2; -k_2, k_2]\nM = [m_1, 0; 0, m_2]\n"
)
BEAM = "L := 6*m\nq := 10*kN/m\n"


def test_the_frequencies_of_a_frame(monkeypatch, capsys):
    (heading,) = headings(monkeypatch, FRAME + "roots(det(K - w^2*M), w, 0, 200/s)\n")
    capsys.readouterr()

    assert "**" not in heading and "*" not in heading, heading
    assert heading.startswith("Roots — $\\displaystyle ") and heading.endswith("$"), heading
    assert r"m_{1} m_{2} w^{4}" in heading, heading


def test_a_defined_name_is_named(monkeypatch, capsys):
    (heading,) = headings(monkeypatch, FRAME + "p = det(K - w^2*M)\nroots(p, w, 0, 200/s)\n")
    capsys.readouterr()

    assert heading == r"Roots — $\displaystyle p$", heading


def test_an_expression_reads_as_it_is_typeset(monkeypatch, capsys):
    (heading,) = headings(monkeypatch, BEAM + "extrema(q*x*(L - x)/2, x, 0, L)\n")
    capsys.readouterr()

    # Display style and `\dfrac` since test_a_characteristic_block_reads_at_the_page_s_size.
    assert heading == r"Extrema — $\displaystyle \dfrac{q x \left(L - x\right)}{2}$", heading


def test_an_absolute_value_keeps_its_bars(monkeypatch, capsys):
    (heading,) = headings(monkeypatch, BEAM + "extrema(abs(q*x*(L - x)/2 - 20*kN*m), x, 0, L)\n")
    capsys.readouterr()

    assert heading.startswith(r"Extrema — $\displaystyle \left|"), heading
    assert heading.endswith(r"\right|$"), heading


def test_both_sides_of_an_intersection(monkeypatch, capsys):
    found = headings(
        monkeypatch,
        BEAM
        + "V(x) = q*(L/2 - x)\n"
        + "intersections(V(x), q*x/3, x, 0, L)\nintersections(q*x/3, V(x), x, 0, L)\n",
    )
    capsys.readouterr()

    assert found == [
        r"Intersections — V(x) / $\displaystyle \dfrac{q x}{3}$",
        r"Intersections — $\displaystyle \dfrac{q x}{3}$ / V(x)",
    ], found


# --- what must not move ---------------------------------------------------------------


def test_a_user_function_still_reads_as_written(monkeypatch, capsys):
    found = headings(
        monkeypatch,
        BEAM + "M(x) = q*x*(L - x)/2\nextrema(M(x), x, 0, L)\nextrema(abs(M(x)), x, 0, L)\n",
    )
    capsys.readouterr()

    assert found == ["Extrema — M(x)", "Extrema — |M(x)|"], found
