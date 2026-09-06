r"""A frequency reads as a frequency and a period as a period.

Found by working a matrix frame analysis, where the three answers of the exercise came
out like this:

    w_n = sqrt(k/m)        11.86 GPa^0.5*mm/(kg^0.5*m^0.5)
    f_n = w_n/(2 pi)        1.89 GPa^0.5*mm/(kg^0.5*m^0.5)
    T_n = 2 pi/w_n          0.53 kg^0.5*m^0.5/(GPa^0.5*mm)

Every number is right. `11.86` in those units is `374.98 1/s`, and the period is
`16.76 ms`. None of the three can be read, and no matrix is involved: a square root of a
stiffness over a mass produces fractional exponents, and there was no family for
`[time]` or for `[time]^-1` to replace them with.

`_unit_terms` is what makes this the family's job rather than a special case. The
artefact carries four unit terms with fractional exponents; `1 / s` carries one. The
machinery for replacing a unit the algebra invented already existed and simply had
nothing to replace these with.

`1 / s` rather than `Hz`, deliberately. A circular frequency is rad/s and a natural
frequency is Hz, and Pint cannot tell them apart because a radian is dimensionless.
Labelling `w_n` as Hz would state something false; `1 / s` is true of both and leaves
the reader to know which they asked for.
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


# k = 210 GPa x 625 mm^2 / 6 m = 21875 kN/m, over 500 kg:
#   w = sqrt(21875000/500) = 209.17 1/s      T = 2 pi/w = 30.04 ms
OSCILLATOR = (
    "E := 210*GPa\n"
    "A := 625*mm**2\n"
    "L := 6*m\n"
    "ms_ := 500*kg\n"
    "keep k = E*A/L\n"
)


def test_a_circular_frequency_reads_in_reciprocal_seconds(cell):
    final = _final(cell(OSCILLATOR + "w = sqrt(k/ms_)\nnumeric(w)\n"))
    assert "209.17" in final, final
    assert r"\frac{1}{\mathrm{s}}" in final, final
    assert "GPa" not in final, final


def test_a_period_reads_in_seconds(cell):
    """Seconds, not milliseconds, and this contract was written the other way first.

    `("s", "ms")` was the original family, on the reasoning that sends a 0.02 m
    deflection to millimetres. A period does not obey that convention: it made a
    building with T = 0.24 s read `240.00 ms`, which nobody writes. The 30 ms period
    here reads `0.03 s` at a precision of 2, and recovering its figures is what
    `%eng_config precision=4` is for - a precision question, not a unit one.
    """
    final = _final(cell(OSCILLATOR + "w = sqrt(k/ms_)\nkeep w_n = w\nT = 2*pi/w_n\nnumeric(T)\n"))
    assert "0.03" in final, final
    assert r"\mathrm{s}" in final, final
    assert "ms" not in final, final
    assert "GPa" not in final, final


def test_a_structural_period_is_not_sent_to_milliseconds(cell):
    """The case that decided it. Every period a building actually has is under a
    second or a few, and all of them read in seconds."""
    for source, expected in [
        ("T := 0.24*s\nx = 1*T\nnumeric(x)\n", "0.24"),
        ("T := 0.50*s\nx = 1*T\nnumeric(x)\n", "0.50"),
        ("T := 1.20*s\nx = 1*T\nnumeric(x)\n", "1.20"),
    ]:
        final = _final(cell(source))
        assert expected in final, final
        assert r"\mathrm{s}" in final, final
        assert "ms" not in final, final


def test_a_period_of_ordinary_size_stays_in_seconds(cell):
    """The band rule decides between the family's members as it does everywhere else.
    A one-second pendulum is not 1000 ms."""
    final = _final(cell("T := 1.25*s\nnumeric(T)\n"))
    assert "1.25" in final, final
    assert r"\mathrm{s}" in final, final
    assert "ms" not in final, final


def test_a_declared_second_is_left_alone(cell):
    final = _final(cell("dt := 0.02*s\n"))
    assert r"\mathrm{s}" in final or r"\mathrm{ms}" in final, final


def test_a_frequency_in_a_matrix_agrees_with_the_scalar(cell):
    """The two paths meet here: a frequency assembled in a matrix reads the same as one
    that never was, which is the other half of this pair of fixes."""
    scalar = _final(cell(OSCILLATOR + "w = sqrt(k/ms_)\nnumeric(w)\n"))
    matrix = _final(cell(OSCILLATOR + "W = [sqrt(k/ms_)]\nnumeric(W)\n"))
    assert r"\frac{1}{\mathrm{s}}" in scalar, scalar
    assert r"\frac{1}{\mathrm{s}}" in matrix, matrix
