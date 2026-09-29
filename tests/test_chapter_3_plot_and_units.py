r"""What chapter 3 of his book found: a plot that hung, and values in units nobody reads.

He chose these first (2026-09-29), from solving chapter 3 of *Matrix Structural Analysis*
(McGuire, Gallagher, Ziemian) - every number right, these read wrong or never finished:

- `plot` works out the curve's extremes exactly to mark them, with no bound on what that
  costs: `max(abs(...))` of a 2x2 solve took 25 s, the real sheet of problem 3.2 more than
  400 s. The marks are furniture; a curve too large to work out exactly is marked from
  the points it was drawn with;
- a plot's axis carried the algebra's unit, `m·kN/(mm²·MPa)`, and its end labels read
  `(150, 0)` in it; it reads in the unit the page would write the largest value in, mm;
- a `:=` value whose line writes a unit in brackets kept the algebra's unit:
  `S := F[1] + 1[kN]` read `301000.00 m·kg/s²` and `N := k*0.5[mm]` read
  `2.00 × 10^7 MPa·mm³/m`. The bracket's alias, `__u_kN`, was not read as the unit it
  names, and "cannot read the unit" kept whatever the value carried;
- `numeric(S)` of a matrix written with `5[m]` printed the alias `__u_m` on the page.
"""

import contextlib
import io
import time

import matplotlib
import pytest
from IPython.display import Math

import engcalc_colab.magic as magic

matplotlib.use("Agg")


def _run(source: str, monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", source)
    latex = " ".join(item.data for item in captured if isinstance(item, Math))
    figures = [item for item in captured if hasattr(item, "axes")]
    return latex.replace(r"\displaystyle ", ""), console.getvalue(), figures


HARD = (
    "E := 200000[MPa]\nA_1 := 10000[mm^2]\nL := 5[m]\ntheta := 60[deg]\n"
    "K(A) = E/L*[A_1 + A*cos(theta)^3, A*cos(theta)^2*sin(theta); "
    "A*cos(theta)^2*sin(theta), A_1 + A*cos(theta)*sin(theta)^2]\n"
    "d(A) = solve(K(A), [0[kN]; -100[kN]])\n"
    "f(A) = max(abs(d(A)[1,1]), abs(d(A)[2,1]))\n"
    "plot(f(A), A, 0, 40000[mm^2])\n"
)


def test_a_plot_too_large_to_work_out_exactly_is_marked_from_its_points(monkeypatch):
    start = time.perf_counter()
    _page, console, figures = _run(HARD, monkeypatch)
    elapsed = time.perf_counter() - start
    assert not console, console
    assert elapsed < 10, elapsed
    (figure,) = figures
    texts = [text.get_text() for axis in figure.axes for text in axis.texts]
    # The largest displacement is at A = 0, where only the vertical bar carries the load:
    # 100 kN * 5 m / (200000 MPa * 10000 mm^2) = 0.25 mm.
    assert any("0.25" in text for text in texts), texts


def test_a_plot_reads_in_the_unit_of_its_largest_value(monkeypatch):
    source = "E := 200000[MPa]\nA := 300[mm^2]\nL := 5[m]\nv(P) = P*L/(E*A)\nplot(v(P), P, -30[kN], 150[kN])\n"
    _page, console, figures = _run(source, monkeypatch)
    (figure,) = figures
    axis = figure.axes[0]
    assert "mm" in axis.get_ylabel() and "MPa" not in axis.get_ylabel(), axis.get_ylabel()
    texts = [text.get_text() for text in axis.texts]
    # 150 kN * 5 m / (200000 MPa * 300 mm^2) = 12.50 mm.
    assert any("12.5" in text for text in texts), texts
    assert "(150, 0)" not in texts, texts


def test_a_plot_in_the_engineer_s_unit_is_as_it_was(monkeypatch):
    source = "L := 6[m]\nq := 10[kN/m]\nM(x) = q*x*(L - x)/2\nplot(M(x), x, 0, L)\n"
    _page, _console, figures = _run(source, monkeypatch)
    (figure,) = figures
    assert "kN" in figure.axes[0].get_ylabel(), figure.axes[0].get_ylabel()


@pytest.mark.parametrize(
    ("line", "shown"),
    [
        ("S := F[1] + 1[kN]", r"S & = & F_{1} + 1\,\mathrm{kN} = 301.00\,\mathrm{kN}"),
        ("V := U + 1[kN]", r"V & = & 301.00\,\mathrm{kN}"),
        # A stiffness worked out from E, A and L carries `MPa·mm²/m`.
        ("E := 200000[MPa]\nA := 1000[mm^2]\nL := 5[m]\nk_2 := E*A/L\nN := k_2*0.5[mm]", r"N & = & 20.00\,\mathrm{kN}"),
    ],
)
def test_a_bracket_unit_is_read_as_the_unit_it_names(line, shown, monkeypatch):
    source = "k := 100[kN/mm]\nD := [3[mm]; 1[mm]]\nF := k*D\nU := F[1]\n" + line + "\n"
    page, console, _figures = _run(source, monkeypatch)
    assert not console, console
    assert shown in page, page
    assert "kg" not in page and r"\mathrm{mm}^{3}" not in page, page


def test_a_unit_typed_in_brackets_is_kept(monkeypatch):
    # What `unit_was_written` is for: `q := 2.8[tonf/m]` keeps its tonf.
    page, _console, _figures = _run("q := 2.8[tonf/m]\n", monkeypatch)
    assert r"2.80\,\frac{\mathrm{tonf}}{\mathrm{m}}" in page, page


def test_a_matrix_written_with_a_bracket_unit_prints_no_alias(monkeypatch):
    source = "E := 200000[MPa]\nA := 1000[mm^2]\nS = A*E/(5[m])*[1, -1; -1, 1]\nnumeric(S)\n"
    page, console, _figures = _run(source, monkeypatch)
    assert not console, console
    assert "__u" not in page, page
    assert r"40.00" in page, page

