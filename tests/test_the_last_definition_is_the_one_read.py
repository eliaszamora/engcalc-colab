r"""A name is what its last line made it: a `=` line drops the number a `:=` line gave it.

Found closing 0.41.0 (2026-09-26), on every release before it: `p := 500*kg`, `a := 2`,
`p = 3*a`, `x := 4*p` gave `x = 2000.00 kg` in silence, while `numeric(p)` on the same
page said `6.00` - one sheet, two answers for one name. The `=` line stored its formula
and left the `:=` value where it was, and a `:=` line reads a value before a formula. The
other way round was already right: a `:=` line drops the formula (`Vu = max(a, b)` then
`Vu := 5000*kgf`). He approved the rule the same day: *"Sí a los dos"*.

The same number outlived a plain `=` after `keep`: `keep d = h - 4*cm` stores `d`'s
number so a later formula can substitute it, and `d = 3*h` left the old one, so
`x := 2*d` read 112 cm where `numeric(2*d)` read 360 cm. A plain `=` line after `keep` is
a definition without the mark, as a plain `:=` line after `keep` already was.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


def run(magics, source: str, monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magics.eng("", source)
    return " ".join(item.data for item in captured if isinstance(item, Math)), console.getvalue()


@pytest.fixture
def magics():
    return magic.EngMagics()


def _row(name: str, value: str) -> str:
    return rf"{name} & = & \displaystyle {value}"


@pytest.mark.parametrize("name", ["p", "m"])
def test_a_formula_after_a_value_is_what_a_colon_equals_line_reads(magics, monkeypatch, name):
    """`m` too: a letter that is also a unit, where the closure printed a notice besides."""
    page, console = run(
        magics, f"{name} := 500*kg\na := 2\n{name} = 3*a\nx := 4*{name}\n", monkeypatch
    )
    assert _row("x", "24.00") in page, page
    assert "2000.00" not in page, page
    assert not console, console


def test_the_page_gives_one_answer_for_the_name(magics, monkeypatch):
    """`numeric(4*p)` and `x := 4*p`, one line apart, said 24 and 2000."""
    page, _console = run(
        magics, "p := 500*kg\na := 2\np = 3*a\nx := 4*p\nnumeric(4*p)\n", monkeypatch
    )
    assert _row("x", "24.00") in page, page
    assert page.rstrip().endswith(r"24.00 \end{array}"), page[-200:]


def test_a_formula_with_a_unit_after_a_value(magics, monkeypatch):
    page, _console = run(magics, "p := 500*kg\nq := 2*kg\np = 3*q\nx := 4*p\n", monkeypatch)
    assert _row("x", r"24.00\,\mathrm{kg}") in page, page


def test_a_named_numeric_line_drops_the_value_too(magics, monkeypatch):
    """`p = numeric(3*a)` is a `=` line that defines `p` by its formula (#332)."""
    page, _console = run(magics, "p := 500*kg\na := 2\np = numeric(3*a)\nx := 4*p\n", monkeypatch)
    assert _row("x", "24.00") in page, page


def test_a_kept_numeric_line_gives_its_name_the_new_number(magics, monkeypatch):
    """`keep p = numeric(3*a)` over `p := 500*kg`: the kept number is the new one, and
    `p` stays a name in a later formula."""
    page, _console = run(
        magics,
        "a := 2\np := 500*kg\nkeep p = numeric(3*a)\nx := 4*p\ny = 2*p\n",
        monkeypatch,
    )
    assert _row("x", "24.00") in page, page
    assert _row("y", "2 p") in page, page


def test_a_value_after_a_formula_is_still_the_value(magics, monkeypatch):
    """The other order, which was right, stays right."""
    page, _console = run(magics, "a := 2\np = 3*a\np := 500*kg\nx := 4*p\n", monkeypatch)
    assert _row("x", r"2000.00\,\mathrm{kg}") in page, page


def test_a_cell_run_again_gives_the_same_answer(magics, monkeypatch):
    sheet = "m := 500*kg\na := 2\nm = 3*a\nx := 4*m\n"
    run(magics, sheet, monkeypatch)
    page, console = run(magics, sheet, monkeypatch)
    assert _row("x", "24.00") in page, page
    assert not console, console


def test_a_plain_formula_after_keep_drops_the_kept_number(magics, monkeypatch):
    page, _console = run(
        magics, "h := 60*cm\nkeep d = h - 4*cm\nd = 3*h\nx := 2*d\n", monkeypatch
    )
    assert _row("x", r"360.00\,\mathrm{cm}") in page, page
    assert "112.00" not in page, page


def test_a_plain_formula_after_keep_is_no_longer_kept(magics, monkeypatch):
    """Left marked, `y = 2*d` stayed `2 d` with no number for `d`, and `numeric(y)`
    stopped asking for one."""
    page, console = run(
        magics, "h := 60*cm\nkeep d = h - 4*cm\nd = 3*h\ny = 2*d\nnumeric(y)\n", monkeypatch
    )
    assert not console, console
    assert _row("y", "6 h") in page, page
    assert page.rstrip().endswith(r"360.00\,\mathrm{cm} \end{array}"), page[-200:]


def test_keep_still_gives_its_name_a_number(magics, monkeypatch):
    """What must not move: a kept name substitutes its own number, including one kept
    over an earlier `:=` value."""
    page, _console = run(
        magics, "h := 60*cm\nkeep d = h - 4*cm\nx := 2*d\n", monkeypatch
    )
    assert _row("x", r"112.00\,\mathrm{cm}") in page, page
    page, _console = run(magics, "a := 2\np := 500*kg\nkeep p = 3*a\nx := 4*p\n", monkeypatch)
    assert _row("x", "24.00") in page, page


def test_a_kept_name_is_substituted_as_a_name_after_a_colon_equals_value(magics, monkeypatch):
    """`keep` over a `:=` value keeps the mark: the substitution shows `p`'s number."""
    page, _console = run(
        magics, "a := 2\np := 500*kg\nkeep p = 3*a\ny = 2*p\nnumeric(y)\n", monkeypatch
    )
    assert "12.00" in page, page
