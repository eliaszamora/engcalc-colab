r"""What 0.52.0 adds and corrects, from the inventory of open findings."""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str) -> tuple[str, str]:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), out.getvalue()

    return run


def test_numeric_under_a_value_does_not_say_it_twice(sheet):
    page, printed = sheet("f(I) = 2*I\ny = f(1e8[mm^4])\nnumeric(y)\n")
    assert not printed, printed
    assert page.count(r"2.00 \times 10^{8}\,\mathrm{mm}^{4}") == 1, page


def test_numeric_under_a_formula_still_works_it_out(sheet):
    page, printed = sheet("a := 2[m]\ny = 3*a\nnumeric(y)\n")
    assert not printed, printed
    assert r"3\,\left(2.00\,\mathrm{m}\right)" in page and r"6.00\,\mathrm{m}" in page, page


# C10c: values set in a `% if` inside a loop were printed after its table, one by one.


def test_a_value_under_an_if_is_a_column_of_the_loop_table(sheet):
    page, printed = sheet(
        "% for i in range(1, 4):\na_{i} := {i}*1[m]\nc_{i} := 2*a_{i}\n% if {i} > 1:\nb_{i} := 3*a_{i}\n% end\n% end\n"
    )
    assert not printed, printed
    assert r"b_{i}\,[\mathrm{m}]" in page and r"\text{---}" in page, page
    assert r"\text{si}\ i > 1" in page and "Como" not in page and r"b_{2} & =" not in page, page


def test_one_value_and_one_under_an_if_make_a_table(sheet):
    page, printed = sheet("% for i in range(1, 3):\na_{i} := {i}*1[m]\n% if a_{i} > 1.5[m]:\nb_{i} := 2*a_{i}\n% end\n% end\n")
    assert not printed, printed
    assert r"\text{si}\ a_{i} > 1.5\,\mathrm{m}" in page and r"1 & 1.00 & \text{---}" in page, page


def test_an_if_with_an_else_keeps_its_rows(sheet):
    page, printed = sheet(
        "% for i in range(1, 3):\na_{i} := {i}*1[m]\nc_{i} := 2*a_{i}\n% if {i} > 1:\nb_{i} := 3*a_{i}\n% else:\nb_{i} := a_{i}\n% end\n% end\n"
    )
    assert not printed, printed
    assert "Como" in page, page


# C6a: an increment of an angle read as one italic word.


@pytest.mark.parametrize(
    ("source", "shown"),
    [("dtheta := 2\n", r"d\theta & ="), ("deltaphi := 3\n", r"\delta\phi & ="), ("dtheta_A := 4\n", r"d\theta_{A} & =")],
)
def test_an_increment_of_an_angle(sheet, source, shown):
    page, printed = sheet(source)
    assert not printed, printed
    assert shown in page and r"\mathit{d" not in page, page


@pytest.mark.parametrize(("source", "shown"), [("dx := 1[m]\n", r"\mathit{dx}"), ("dpi := 6\n", r"\mathit{dpi}")])
def test_other_names_beginning_with_d_stay_words(sheet, source, shown):
    page, printed = sheet(source)
    assert shown in page, page
