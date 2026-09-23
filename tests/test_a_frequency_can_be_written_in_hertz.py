r"""A frequency can be written in hertz, and a circular frequency never reads in them.

    f := 5*Hz   ->  engcalc: line 1: unknown numeric name 'Hz'. Define the numeric value
                    first, for example: Hz := <value>*<unit>.

The engineer was asked to define the hertz - the answer `MN` got before it joined the table
of spellings an engineer writes. `Hz` joins it now, as a unit that can be *written* and
*asked for*, and never as one the page *chooses*.

That last part is the one that matters. A frequency and a circular frequency share a
dimension, and nothing in a value tells `f` from `ω`: a page that picked hertz for
`[time]⁻¹` would print `ω_n = 374.98 Hz`, wrong by 2π in the reading an engineer gives it.
Measured before the change, with the alias patched in: `w = 2*pi*f` from `f := 5*Hz` already
reads `31.42 1/s`, because a derived value goes to its family and the family of `[time]⁻¹` is
`1/s`. The contract below pins that, so the day someone adds hertz to the family, this says
why not.
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


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


def test_a_frequency_can_be_written_in_hertz(cell, capsys):
    page = cell("f := 5*Hz\n")
    assert capsys.readouterr().out == ""
    assert _final(page) == r"\displaystyle 5.00\,\mathrm{Hz}", _final(page)


def test_a_period_from_hertz_reads_in_seconds(cell, capsys):
    page = cell("f := 5*Hz\nT = 1/f\nnumeric(T)\n")
    assert capsys.readouterr().out == ""
    assert _final(page) == r"\displaystyle 0.20\,\mathrm{s}", _final(page)


def test_a_frequency_can_be_asked_for_in_hertz(cell, capsys):
    page = cell("w := 374.98/s\nf_n = w/(2*pi)\nnumeric(f_n, Hz)\n")
    assert capsys.readouterr().out == ""
    assert _final(page) == r"\displaystyle 59.68\,\mathrm{Hz}", _final(page)


def test_a_circular_frequency_from_hertz_never_reads_in_hertz(cell, capsys):
    """The page cannot tell `ω` from `f`, so it never chooses hertz: `2πf` reads `1/s`."""
    page = cell("f := 5*Hz\nw = 2*pi*f\nnumeric(w)\n")
    assert capsys.readouterr().out == ""
    assert _final(page) == r"\displaystyle 31.42\,\frac{1}{\mathrm{s}}", _final(page)


def test_a_circular_frequency_still_reads_per_second(cell, capsys):
    page = cell("w := 374.98/s\nnumeric(w)\n")
    assert capsys.readouterr().out == ""
    assert _final(page) == r"\displaystyle 374.98\,\frac{1}{\mathrm{s}}", _final(page)
