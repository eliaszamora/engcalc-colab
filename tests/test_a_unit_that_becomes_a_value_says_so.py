r"""A name that was read as a unit and is then given a value says so, at that line.

    k = 2000*kN/m        the metre
    m := 500*kg          m is now a mass
    numeric(k)           2000 kN/(500.00 kg) = 4.00 kN/kg

`N`, `m` and `s` are unit aliases and ordinary names at once, and a stored value outranks
the alias - `N := 500*kN` must make `N` the axial force. The price was paid in silence: a
formula written with the metre read the mass the moment it was evaluated again, in the same
run (`numeric(k)` above) or on the next. `k := 2000*kN/m` then `m := 500*kg` is the usual
way to write one degree of freedom, and running that cell a second time drew
`k = 4.00 kN/kg`. Found checking the pending items after 0.31.15; the README has said since
0.22.0 that the collision "has a contract of its own so that the day EngCalc warns about it,
the decision is visible rather than accidental". This is that day.

The rule is unchanged, because which meaning was wanted cannot be known: the metre in the
single degree of freedom, the axial force in `sigma := N/A` followed by `N := 500*kN`. What
is new is that the two moments a name changes meaning are said, each as one printed line:

- a name this session has read as a unit is given a value - said once, when it first
  gets one;
- a line that read a name as a unit reads it as a value now - said every time it happens,
  because every time it is a changed result.

A sheet that uses `m`, `N` or `s` one way throughout prints nothing, run once or twice, and
`%eng_reset` forgets what it has seen. An `N` never defined still reads as one newton in
silence - nothing distinguishes it from a sheet that means the newton - and stays pinned in
`test_numeric_unit_literals.py::test_an_undefined_axial_force_reads_as_newtons`.
"""

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def magics(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    engine = magic.EngMagics()
    engine.captured = captured
    return engine


def run(magics, source: str) -> str:
    magics.captured.clear()
    magics.eng("", source)
    return "".join(getattr(obj, "data", "") for obj in magics.captured)


NOTICE = "has been read as a unit"


def test_a_metre_that_becomes_a_mass_says_so_in_one_run(magics, capsys):
    run(magics, "k = 2000*kN/m\nm := 500*kg\nnumeric(k)\n")
    printed = capsys.readouterr().out
    assert "engcalc: line 2: 'm' has been read as a unit (meter)" in printed, printed
    assert printed.count(NOTICE) == 1, printed


def test_a_metre_read_in_one_cell_and_a_mass_given_in_the_next(magics, capsys):
    run(magics, "k := 2000*kN/m\n")
    assert capsys.readouterr().out == ""
    run(magics, "m := 500*kg\n")
    printed = capsys.readouterr().out
    assert "engcalc: line 1: 'm' has been read as a unit (meter)" in printed, printed


def test_a_second_that_becomes_a_spacing_says_so(magics, capsys):
    run(magics, "w := 374.98/s\ns := 150*mm\n")
    printed = capsys.readouterr().out
    assert "engcalc: line 2: 's' has been read as a unit (second)" in printed, printed


def test_giving_the_value_is_said_once(magics, capsys):
    sheet = "k := 2000*kN/m\nm := 500*kg\n"
    run(magics, sheet)
    assert capsys.readouterr().out.count(NOTICE) == 1
    run(magics, sheet)
    assert NOTICE not in capsys.readouterr().out


def test_running_the_line_again_says_its_result_changed(magics, capsys):
    """The usual single degree of freedom, run twice. On `main` before this, the second
    run drew `k = 4.00 kN/kg` and `w = 0.0894 kN^0.5/kg` and printed nothing."""
    sheet = "k := 2000*kN/m\nm := 500*kg\nsolve(k - w^2*m = 0, w)\n"
    run(magics, sheet)
    capsys.readouterr()
    page = run(magics, sheet)
    printed = capsys.readouterr().out
    assert (
        "engcalc: line 1: this line read 'm' as a unit (meter) when it ran before, "
        "and reads it as a value now" in printed
    ), printed
    assert r"4.00\,\frac{\mathrm{kN}}{\mathrm{kg}}" in page, page  # said, not changed


def test_every_run_after_the_first_says_it_again(magics, capsys):
    """Each of those runs draws the changed result, so each one says so: a third run that
    fell silent would be the silence this exists to end."""
    sheet = "k := 2000*kN/m\nm := 500*kg\n"
    run(magics, sheet)
    capsys.readouterr()
    for _ in range(2):
        run(magics, sheet)
        assert "this line read 'm' as a unit" in capsys.readouterr().out


def test_a_consistent_sheet_run_twice_says_nothing(magics, capsys):
    sheet = "k := 2000*kN/m\nm_s := 500*kg\nsolve(k - w^2*m_s = 0, w)\n"
    run(magics, sheet)
    run(magics, sheet)
    assert capsys.readouterr().out == ""


def test_an_axial_force_defined_after_a_newton_says_so_both_times(magics, capsys):
    """The other direction: `N` read as the newton, then defined as the axial force.
    Which one was meant cannot be known - so both moments are said, and nothing moves."""
    run(magics, "A := 100*cm^2\nsigma := N/A\n")
    assert capsys.readouterr().out == ""
    run(magics, "N := 500*kN\n")
    assert "'N' has been read as a unit (newton)" in capsys.readouterr().out
    run(magics, "sigma := N/A\n")
    assert "this line read 'N' as a unit (newton)" in capsys.readouterr().out


def test_a_name_used_as_a_variable_from_the_start_says_nothing(magics, capsys):
    run(magics, "N := 500*kN\nA := 100*cm^2\nsigma = N/A\nnumeric(sigma)\nm := 200*kg\n")
    assert capsys.readouterr().out == ""


def test_a_reset_forgets_what_was_read(magics, capsys):
    run(magics, "k := 2000*kN/m\n")
    magics.eng_reset("")
    capsys.readouterr()
    run(magics, "m := 500*kg\n")
    assert capsys.readouterr().out == ""


def test_a_reset_forgets_what_each_line_read(magics, capsys):
    """After a reset the same line is a new line: `m` holds a mass from the start."""
    run(magics, "k := 2000*kN/m\n")
    magics.eng_reset("")
    capsys.readouterr()
    run(magics, "m := 500*kg\nk := 2000*kN/m\n")
    assert capsys.readouterr().out == ""


def test_saying_so_changes_no_value(magics, capsys):
    """The precedence stays what it was: the page still shows what it computed."""
    page = run(magics, "k = 2000*kN/m\nm := 500*kg\nnumeric(k)\n")
    capsys.readouterr()
    assert r"4.00\,\frac{\mathrm{kN}}{\mathrm{kg}}" in page, page
