r"""A formula that writes a value of `=` in beside a name that stands says `:=` keeps it.

`L = 3*m` then `M = q*L^2/2`, `q` with no value, reads `9 m^2 q/2`: `L` goes in as its
value while `q` stays a name. Making `=` values stand was built and audited (2026-09-27)
and reached far past this row, so it was held; his decision (2026-09-28) is a notice,
once per name, that `:=` keeps it a name - `L := 3*m` reads `q L^2/2`. The page does not
change.
"""

import contextlib
import io

from IPython.display import Math

import engcalc_colab.magic as magic


def _run(source: str, monkeypatch) -> tuple[str, str]:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", source)
    latex = " ".join(item.data for item in captured if isinstance(item, Math))
    return latex.replace(r"\displaystyle ", ""), console.getvalue()


def test_a_value_of_equals_beside_a_name_is_told(monkeypatch):
    page, console = _run("L = 3*m\nM = q*L^2/2\n", monkeypatch)
    assert "engcalc: line 2:" in console, console
    assert "'L' was defined with '='" in console, console
    assert "L := 3*m" in console, console
    assert r"\frac{9\,\mathrm{m}^{2}\,q}{2}" in page, page


def test_two_values_are_told_in_one_notice(monkeypatch):
    _page, console = _run("L = 6*m\nq = 10*kN/m\nM(x) = q*L*x/2 - q*x^2/2\n", monkeypatch)
    assert console.count("engcalc:") == 1, console
    # In the order the line reads them: `q*L*x/2`.
    assert "'q' and 'L' were defined with '='" in console, console
    assert "L := 6*m" in console and "q := 10*kN/m" in console, console


def test_it_is_told_once_per_name(monkeypatch):
    _page, console = _run("L = 3*m\nM = q*L^2/2\nV = q*L\n", monkeypatch)
    assert console.count("engcalc:") == 1, console


def test_a_line_of_values_alone_says_nothing(monkeypatch):
    page, console = _run("L = 6*m\nq = 10*kN/m\nM = q*L^2/8\n", monkeypatch)
    assert not console, console
    assert r"45\,\mathrm{kN} \cdot \mathrm{m}" in page, page


def test_a_colon_equals_value_or_a_kept_name_says_nothing(monkeypatch):
    _page, console = _run("L := 3[m]\nM = q*L^2/2\nkeep h = 60*cm\nN = b*h\n", monkeypatch)
    assert not console, console


def test_a_parameter_named_like_a_value_is_not_told_about(monkeypatch):
    # In `f(a) = ...` the body's `a` is the parameter, not the sheet's `a = 3`.
    _page, console = _run("a = 3\nf(a) = 2*a + q\n", monkeypatch)
    assert not console, console


def test_the_names_are_told_in_the_order_the_line_reads_them(monkeypatch):
    _page, console = _run("L = 6*m\nq = 10*kN/m\nM(x) = L*q*x - x^2*q\n", monkeypatch)
    assert "'L' and 'q' were defined with '='" in console, console


def test_a_name_defined_again_with_colon_equals_says_nothing(monkeypatch):
    _page, console = _run("L = 3*m\nL := 4[m]\nM = q*L^2/2\n", monkeypatch)
    assert not console, console


def test_a_matrix_written_on_the_line_is_told_about(monkeypatch):
    _page, console = _run("L = 3*m\nK = [q*L, 0; 0, q]\n", monkeypatch)
    assert "'L' was defined with '='" in console, console


def test_a_formula_that_is_not_a_number_is_not_told_about(monkeypatch):
    # `a` is a formula (`b L`), not a value: only `L`, written into `a`, is told about.
    _page, console = _run("L = 3*m\na = b*L\nM = q*a\n", monkeypatch)
    assert console.count("engcalc:") == 1, console
    assert "engcalc: line 2:" in console and "'L'" in console, console
    assert "'a'" not in console, console
