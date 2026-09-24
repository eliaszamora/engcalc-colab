r"""A one-letter name read as a unit, where nothing wrote it as one, says so.

    A := 500*mm^2
    sigma = N/A
    numeric(sigma)          0.002 MPa         - N was one newton, and nothing said so

`N`, `m` and `s` are units and ordinary names at once. A name the sheet has given no
value is read as the unit, which is right for `q := 10*kN/m` and silently wrong for an
axial force `N` the engineer forgot to define: the stress came out in MPa, with a figure
nobody would take for a force of one newton over the area but nothing on the page to say
where it came from. He asked on 2026-09-24 for it to be said aloud.

The line says it once per name, and only where nothing on the sheet has written that
letter as a unit - next to a number or to another unit: `30*N`, `2*m`, `4*kN*x/m`,
`q := 10*kN/m`. There it is plainly the unit, and nothing is said.
"""

import contextlib
import io

import pytest

from IPython.display import Math

import engcalc_colab.magic as magic


@pytest.fixture
def sheet(monkeypatch):
    engine = magic.EngMagics()

    def run(source: str) -> tuple[str, str]:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            engine.eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), console.getvalue()

    run.engine = engine
    return run


@pytest.mark.parametrize(
    ("source", "name", "unit"),
    [
        ("A := 500*mm^2\nsigma = N/A\nnumeric(sigma)\n", "N", "newton"),
        ("e := 0.2*m\nM = N*e\n", "N", "newton"),
        ("t := 3*s\nv = x/m\n", "m", "meter"),
    ],
)
def test_a_letter_nothing_wrote_as_a_unit_is_said_to_be_one(sheet, source, name, unit):
    _, console = sheet(source)
    said = f"'{name}' is read as a unit ({unit})"
    assert said in console, console
    assert console.count(said) == 1, console
    assert f"{name} := " in console and f"{name}_1" in console, console


@pytest.mark.parametrize(
    "source",
    [
        "q := 10*kN/m\nL := 6*m\nM = q*L^2/8\n",
        "P := 30*N\nA := 2*mm^2\nsigma = P/A\n",
        "k(x) = 1*kN + 4*kN*x/m\n",
        "t := 2*s\nw = 1/s\n",
        "N := 30*kN\nA := 500*mm^2\nsigma = N/A\nnumeric(sigma)\n",
    ],
)
def test_a_letter_written_as_a_unit_or_given_a_value_says_nothing(sheet, source):
    _, console = sheet(source)
    assert "engcalc:" not in console, console


def test_it_is_said_once_per_name_on_a_sheet(sheet):
    _, console = sheet("A := 500*mm^2\nsigma = N/A\ntau = N/(2*A)\n")
    assert console.count("'N' is read as a unit") == 1, console


def test_the_value_is_what_it_was(sheet):
    """Said, not changed: the page computes as it did."""
    page, _ = sheet("A := 500*mm^2\nsigma = N/A\nnumeric(sigma)\n")
    assert page.rstrip().endswith(r"0.002\,\mathrm{MPa} \end{array}"), page


def test_the_next_cell_does_not_say_it_again_and_a_reset_does(sheet):
    _, first = sheet("sigma = N/A\n")
    _, second = sheet("tau = N/B\n")
    assert "'N' is read as a unit" in first, first
    assert "'N' is read as a unit" not in second, second
    sheet.engine.engine.reset()
    _, third = sheet("tau = N/B\n")
    assert "'N' is read as a unit" in third, third
