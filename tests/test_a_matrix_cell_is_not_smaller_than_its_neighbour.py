r"""Every cell of a matrix is typeset at the same size as the cell beside it.

The engineer ran 0.30.1 in Colab and reported the one thing he did not like: *"en las
matrices hay mucha variación de tamaños en los textos y números"*. His screenshot shows
it inside a single matrix:

    K_ii  =  [ 4EI_c/L_c        0      ]        the fraction small, the zero full size
             [     0        4EI_c/L_c  ]

It is LaTeX's own rule and not a defect anybody wrote: a `matrix` environment typesets
its cells in *text* style, and `\frac` in text style is drawn smaller than in display
style. A cell with no fraction is unaffected, so the two sizes end up side by side in one
bracket, which is the ugliest form of it.

`\displaystyle` on each cell levels them. `\dfrac` would fix the fractions alone;
`\displaystyle` fixes every construct that shrinks in text style - sums, integrals,
limits - and does not require intercepting what SymPy emits.

**The cost is width, and it was measured before this was written**, because the wide
matrices on this page were a finding the engineer looked at and chose to live with. Per
block, on the frame benchmark:

    T, L_1, R_1, A_1, q            422 px  ->   422    unchanged
    k_c, the local stiffness       457     ->   522
    K_1 ... K, the assembly       1224     ->  1696
    the condensation              1009     ->  1009    unchanged
    the dynamics                   422     ->   422    unchanged

The blocks he was looking at do not get wider at all: their width is already set by a
substitution row, and the taller fractions fit inside it. The one that grows was already
1224 px against about 900 px of Colab output, so it was a horizontal scroll either way.

Both places a matrix is built carry the rule, for the same reason the 1x1 rule is in both:
a page that levels its symbolic matrices and not its numeric ones would trade one
inconsistency for another.
"""

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def cell(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()

    def run(source: str) -> str:
        captured.clear()
        magics.eng("", source)
        return "".join(getattr(obj, "data", "") for obj in captured)

    return run


def _cells(latex: str) -> list[str]:
    """Every cell of every matrix on the page."""
    out = []
    for chunk in latex.split(r"\begin{matrix}")[1:]:
        body = chunk.split(r"\end{matrix}")[0]
        for row in body.split(r"\\"):
            out.extend(cell.strip() for cell in row.split("&") if cell.strip())
    return out


def test_every_cell_of_a_symbolic_matrix_is_display_style(cell):
    """The definition stage: `K_ii = [4EI/L, 0; 0, 4EI/L]` is where he saw it."""
    latex = cell("E := 210*GPa\nI := 2*cm**4\nL := 3*m\nK = [4*E*I/L, 0; 0, 4*E*I/L]\n")
    cells = _cells(latex)
    assert cells, latex
    assert all(c.startswith(r"\displaystyle") for c in cells), cells


def test_a_cell_with_no_fraction_is_levelled_too(cell):
    """The zero is the other half of the pair. Levelling only the fractions would leave
    the same mismatch, measured from the other side."""
    latex = cell("M = [1, 0; 0, 1]\n")
    cells = _cells(latex)
    assert cells == [r"\displaystyle 1", r"\displaystyle 0",
                     r"\displaystyle 0", r"\displaystyle 1"], cells


def test_the_numeric_stage_is_levelled_as_well(cell):
    """Both builders or neither: a page that levels its symbolic matrices and not its
    values trades one inconsistency for another."""
    latex = cell("a := 3*kN\nb := 4*kN\nM = [a, b; b, a]\nnumeric(M)\n")
    assert all(c.startswith(r"\displaystyle") for c in _cells(latex)), latex


def test_the_substitution_stage_is_levelled_as_well(cell):
    """The stage between the two, which shares the printer with the first."""
    latex = cell("E := 210*GPa\nI := 2*cm**4\nL := 3*m\nK = [4*E*I/L, 0]\nnumeric(K)\n")
    assert all(c.startswith(r"\displaystyle") for c in _cells(latex)), latex


# --- what must not move ---------------------------------------------------------------

def test_a_one_by_one_is_still_the_number_it_holds(cell):
    """0.30.1's rule, which this must not undo: a 1x1 has no cell to level because it
    has no brackets."""
    latex = cell("a := 3*kN\nM = [a]\nnumeric(M)\n")
    assert r"\begin{matrix}" not in latex, latex
    assert "3.00" in latex, latex


def test_the_value_is_untouched(cell):
    latex = cell("a := 3*kN\nb := 4*kN\nM = [a, b]\nnumeric(M)\n")
    assert "3.00" in latex and "4.00" in latex, latex
    assert r"\mathrm{kN}" in latex, latex


def test_a_matrix_still_has_its_brackets(cell):
    latex = cell("M = [1, 2; 3, 4]\n")
    assert r"\left[\begin{matrix}" in latex, latex
    assert r"\end{matrix}\right]" in latex, latex
