r"""A characteristic block writes its mathematics at the size of the page around it.

The engineer's modal memoria on 0.31.1, in Colab: the two frequencies of a two-storey frame

    w = √2 √(k₁/m₁ + k₂/m₂ + k₂/m₁ − √(…)/(m₁m₂)) / 2      (36.51 1/s) · root

set so small the letters could not be read, the two rows touching, the whole block
"apretado". Measured in the browser at Colab's 900 px, against `k₁` in the equation block
above it (11.9 px tall):

    letters inside w       3.8 - 5.9 px
    gap between the rows   1 px

**Why.** The block is a markdown output, and its mathematics is written inline - `$...$`
inside a line of text. Inline mathematics is set in text style, where each fraction inside
another fraction or a root steps down a size, and the frequency of a frame is three levels
deep. The equation blocks write every cell `\displaystyle`. The rows themselves were
spaced 0.08 rem apart, for lines of text, not for fractions.

**So a characteristic block's formulas are set in display style, every fraction at full
size, and its rows have room between them**: 7.5 - 11.7 px letters and a 7 px gap on the
same frame, 649 px wide in a 900 px cell; `x = L/2` on a beam reads at the size `L/2` has
in the working above it. A quantity - `(3.00 m)`, `0.00 1/s` - stays inline, as a value
in a line of text.

Since `test_a_computed_block_is_written_like_the_working` the block is a `Math` output, whose
rows are each `displaystyle` and `8pt` apart - the frame the working has - so display style
and room come from the row now; the `dfrac` is still this file's.
"""

import re

import engcalc_colab.magic as magic


def raw(monkeypatch, source: str) -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", source)
    return "".join(str(getattr(obj, "data", "")) for obj in captured)


FRAME = (
    "k_1 := 2000*kN/m\nk_2 := 1500*kN/m\nm_1 := 600*kg\nm_2 := 500*kg\n"
    "K = [k_1 + k_2, -k_2; -k_2, k_2]\nM = [m_1, 0; 0, m_2]\n"
)
BEAM = "L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L - x)/2\n"


def test_the_frequencies_of_a_frame_are_set_at_full_size(monkeypatch, capsys):
    page = raw(monkeypatch, FRAME + "roots(det(K - w^2*M), w, 0, 200/s)\n")
    capsys.readouterr()

    roots = re.findall(r"\\displaystyle w = (.*?)\\,\\left\(", page)
    assert len(roots) == 2, page
    for root in roots:
        assert root.startswith(r"\dfrac{\sqrt{2}"), root
        assert r"\frac" not in root.replace(r"\dfrac", ""), root


def test_a_beam_s_midspan_reads_as_its_working_does(monkeypatch, capsys):
    page = raw(monkeypatch, BEAM + "extrema(M(x), x, 0, L)\n")
    capsys.readouterr()

    assert r"\displaystyle x = \dfrac{L}{2}\,\left(" in page, page
    assert r"\text{value} = \dfrac{q L^{2}}{8}\,\left(" in page, page


def test_the_rows_have_room_between_them(monkeypatch, capsys):
    page = raw(monkeypatch, BEAM + "extrema(M(x), x, 0, L)\n")
    capsys.readouterr()

    assert r"\\[8pt] \displaystyle x = \dfrac{L}{2}" in page, page
    assert "margin:" not in page, page


# --- what must not move ---------------------------------------------------------------


def test_a_quantity_stays_inline(monkeypatch, capsys):
    page = raw(monkeypatch, BEAM + "extrema(M(x), x, 0, L)\n")
    capsys.readouterr()

    assert r"\left(3.00\,\mathrm{m}\right)" in page, page
    assert r"\text{Domain: } 0.00\,\mathrm{m} \text{ to } 6.00\,\mathrm{m}" in page, page
