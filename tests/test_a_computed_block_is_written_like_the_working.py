r"""A computed block is written like the working around it: one font, one edge, one line a row.

The engineer's memoria on 0.31.2, in Colab - "sigo sintiendo que se ve como un poco
amontonado, hay fuentes distintas, no se ve ordenado" - and a reminder: "permitíamos
habilitar la barra de deslizamiento horizontal para casos con términos muy grandes".

    M  =  [m₁ 0; 0 m₂]                       MathJax, indented
    Roots — k₁k₂ − …                         the notebook's sans-serif, flush left
    Domain: 0.00 1/s to 200.00 1/s
    w =                                      one root on three lines:
    √2 √(k₁/m₁ + …)/2                        the formula wrapped under its name
    (36.51 1/s) · root                       and its value under that
    P  =  2 · 3 kN                           no space before the next block

**Why.** The equation blocks are `Math` outputs: MathJax's own font, the `\hspace` edge,
and a row too wide for the cell scrolls sideways. The computed blocks - roots, extrema,
intersections, `governing`, `table`, `summary` - were `Markdown` outputs carrying HTML,
because #146 needed them to typeset and a `Markdown` output does. It typesets the
mathematics and sets everything else in the notebook's text font, wraps a line that does
not fit the cell as prose wraps, and starts at the text's edge. Half of every block was in
one font and half in another, which is the complaint #146 itself quoted from him.

**So a computed block is a `Math` output too**: its words in `\text{}`, its heading in
`\textbf{}`, a response named as its definition names it (`U_{1}(x)`), each point on one
row that scrolls rather than wraps, the equation blocks' edge, room above and below it, and
a table drawn as an array with its rules. What each block says is unchanged.
"""

import re

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic

from conftest import blocks_into, block_text


SHEET = (
    "L := 6.00*m\n"
    "qD := 18*kN/m\n"
    "qL := 12*kN/m\n"
    "M_D(x) = qD*x*(L - x)/2\n"
    "M_L(x) = qL*x*(L - x)/2\n"
    "case D = M_D(x)\n"
    "case Lv = M_L(x)\n"
    "combo U1 = 1.2*D + 1.6*Lv\n"
    "governing(U1(x), M_D(x), x, 0, L)\n"
    "table(U1(x), x, 0, L, 4)\n"
    "extrema(U1(x), x, 0, L)\n"
    "V(x) = qD*(L/2 - x)\n"
    "roots(V(x), x, 0, L)\n"
    "M_u = U1(L/2)\n"
    "report(M_u)\n"
    "summary()\n"
)


@pytest.fixture
def outputs(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", SHEET)
    return captured


def blocks(outputs) -> dict[str, str]:
    """The computed blocks by what they are, read off their data."""
    found = {}
    for output in outputs:
        data = str(getattr(output, "data", ""))
        for kind, marker in (
            ("governing", "Governing"),
            ("extrema", "Extrema"),
            ("roots", "Roots"),
            ("summary", "Summary"),
            ("table", r"\hline"),
        ):
            if marker in data:
                found[kind] = output
    assert set(found) == {"governing", "extrema", "roots", "summary", "table"}, [
        str(getattr(o, "data", ""))[:60] for o in outputs
    ]
    return found


def test_every_computed_block_is_a_math_output(outputs):
    for kind, output in blocks(outputs).items():
        assert isinstance(output, Math), (kind, type(output).__name__)


def test_no_block_carries_markup(outputs):
    for kind, output in blocks(outputs).items():
        assert "<" not in output.data and "style=" not in output.data, (kind, output.data)


def test_every_block_starts_at_the_working_s_edge(outputs):
    for kind, output in blocks(outputs).items():
        assert output.data.startswith(r"\hspace{0.2em}\begin{array}"), (kind, output.data[:60])


def test_every_block_opens_and_closes_in_one_frame(outputs):
    """Its room from the blocks around it is no longer its own: one rule for every block,
    the magic's spacer, since 2026-09-25 - see test_one_spacing_rule."""
    for kind, output in blocks(outputs).items():
        assert output.data.startswith(r"\hspace{0.2em}\begin{array}{l} \displaystyle "), (kind, output.data[:120])
        assert output.data.endswith(r" \end{array}"), (kind, output.data[-60:])
        assert r"\rule{0pt}{0.7em}" not in output.data, (kind, output.data[:120])


def test_the_words_of_a_block_are_set_as_text(outputs):
    found = blocks(outputs)
    assert r"\textbf{Extrema} \text{ — }" in found["extrema"].data, found["extrema"].data
    assert r"\text{Domain: }" in found["extrema"].data, found["extrema"].data
    assert r"\text{local max, global max}" in found["extrema"].data, found["extrema"].data
    assert r"\textbf{Governing} \text{ along }" in found["governing"].data, found["governing"].data
    assert r"\textbf{Summary}" in found["summary"].data, found["summary"].data


def test_a_response_is_named_as_its_definition_names_it(outputs):
    found = blocks(outputs)
    assert r"\text{ — } U_{1}\left(x\right)" in found["extrema"].data, found["extrema"].data
    assert r"\text{ — } V\left(x\right)" in found["roots"].data, found["roots"].data
    assert r"\qquad \displaystyle U_{1}\left(x\right)" in found["governing"].data, found["governing"].data


def test_a_point_is_one_row(outputs):
    """Coordinate, value and role on one row, so a wide one scrolls instead of wrapping."""
    rows = blocks(outputs)["extrema"].data.split(r"\\")
    midspan = [row for row in rows if "local max" in row]
    assert len(midspan) == 1, rows
    assert r"x = \dfrac{L}{2}" in midspan[0] and r"\text{value} = " in midspan[0], midspan


def test_a_table_is_an_array_with_its_rules(outputs):
    table = blocks(outputs)["table"].data
    assert r"\begin{array}{l|r}" in table, table
    assert r"x\,[\mathrm{m}] & U_{1}\left(x\right)\,[\mathrm{kN} \cdot \mathrm{m}] \\ \hline" in table, table


def test_a_summary_row_reads_as_a_result(outputs):
    summary = blocks(outputs)["summary"].data
    assert re.search(r"M_\{u\} & = & \\displaystyle [\d.]+\\,\\mathrm\{kN\}", summary), summary


# --- what must not move ---------------------------------------------------------------


def test_what_each_block_says_is_unchanged(outputs):
    found = blocks(outputs)
    assert "Domain: 0.00 m to 6.00 m" in block_text(found["extrema"].data)
    assert "x = L/2 (3.00 m) · value = " in block_text(found["extrema"].data)
    assert "local max, global max" in block_text(found["extrema"].data)
    assert "x = L/2 (3.00 m) · root" in block_text(found["roots"].data)
    assert "0.00 m to 6.00 m" in block_text(found["governing"].data)


def test_a_heading_and_a_narrative_are_still_text(monkeypatch):
    """A heading is HTML, and a paragraph is set as the working is since 2026-09-25 (his
    choice): a Math output whose words are `\\text{}`."""
    captured = []
    monkeypatch.setattr(magic, "display", blocks_into(captured))
    magic.EngMagics().eng("", '### Viga\n"""\nUna viga simplemente apoyada.\n"""\nL := 6*m\n')
    kinds = [type(output).__name__ for output in captured]
    assert kinds == ["HTML", "Math", "Math"], kinds
    assert r"\text{Una viga simplemente apoyada.}" in captured[1].data, captured[1].data
