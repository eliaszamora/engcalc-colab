r"""What the second audit of 0.43.2's refusal found (2026-09-28), and what it pins.

`numeric` written inside a formula stops the line, and the line is written back without it
(`test_numeric_is_a_line_of_its_own`). A written-back line is advice: pasted back, it must
run and give the value the line meant. Three lenses and a skeptic for each finding found:

- a condition dropped the unit of `numeric(X, unit)` unread - `% if numeric(r, percent) >
  50` ran, where it stopped before, and `numeric(d, mm)` was said in metres;
- advice that does not run: `report(2*M_2)` (report takes a name), `numeric(M_2)` for
  `numeric(report(M_2))` (the record gone), `then numeric(y)` of a formula still in `x`,
  `L^3**(1/3)` and `K^2[1,1]` (brackets lost), the first pass of a `% for` for its line;
- older, found on the way: `K[1, 1] = numeric(M(L_2))` passed as a named numeric and
  stored `M`'s body read at the sheet's own value of its parameter, and `keep w =
  result(M_2)` showed the substitution `result` leaves out.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic
from engcalc_colab.engine import _without_a_comment

BASE = "L_2 := 3[m]\nq_2 := 10[kN/m]\nM_2 = q_2*L_2^2/2\nM(x) = q_2*x^2/2\n"


def _run(source: str, monkeypatch) -> tuple[str, str]:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        magic.EngMagics().eng("", source)
    page = " ".join(str(getattr(item, "data", "")) for item in captured)
    return page.replace(r"\displaystyle ", ""), console.getvalue()


@pytest.mark.parametrize(
    ("condition", "told"),
    [
        ("% if numeric(M_2, m) > 40*kN*m:", "target unit is incompatible with result"),
        ("% if numeric(M_2, foo) > 40*kN*m:", "unknown target unit 'foo'"),
        ("% if 2*numeric(M_2, foo) > 40*kN*m:", "unknown target unit 'foo'"),
    ],
)
def test_a_condition_reads_the_unit_it_asks_for(condition, told, monkeypatch):
    _page, console = _run(BASE + condition + "\nnumeric(M_2)\n% end\n", monkeypatch)
    assert "engcalc: line 5: the condition needs a value for" in console, console
    assert told in console, console
    # The inner line is the condition's own, not a line of the sheet.
    assert "line 1" not in console, console


def test_a_condition_says_a_side_in_the_unit_asked_for(monkeypatch):
    source = "d_1 := 0.0123[m]\n% if numeric(d_1, mm) > 20*mm:\nnumeric(d_1)\n% else:\nnumeric(d_1, mm)\n% end\n"
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert r"d_{1} = 12.30\,\mathrm{mm} \leq 20.00\,\mathrm{mm}" in page, page


@pytest.mark.parametrize(
    ("line", "told"),
    [
        # `report` takes one name the sheet defines; the line cannot be written as one.
        ("2*report(M_2)", "report takes a name the sheet defines: write 2*M_2 under a name"),
        ("sqrt(report(M_2))", "report takes a name the sheet defines: write sqrt(M_2) under a name"),
        # The record is what the line asked for: report shows what numeric shows.
        ("numeric(report(M_2))", "Write report(M_2)."),
        ("result(report(M_2))", "Write report(M_2)."),
        # The call kept is told what is wrong with it, as it was before.
        ("z = report(numeric(M_2))", "report expects one defined name, as in report(M_max)"),
        ("report(2*numeric(M_2))", "report expects one defined name, as in report(M_max)"),
        ("numeric(2*numeric(L_2), cm, m)", "numeric expects 1 or 2 arguments"),
    ],
)
def test_a_report_is_written_back_as_report_takes_it(line, told, monkeypatch):
    _page, console = _run(BASE + line + "\n", monkeypatch)
    assert told in console, console
    assert "Write report(2" not in console and "Write numeric(M_2)." not in console, console


@pytest.mark.parametrize(
    ("line", "written"),
    [
        # A formula still in `x` has no number to ask for: only the line is written.
        ("y = numeric(M(x))*2", "Write y = M(x)*2."),
        ("diff(numeric(M(x)), x)", "Write diff(M(x), x)."),
        ("numeric(q_2)*x", "Write q_2*x."),
        # The variable of a sum with its limits is the sum's own: it has a number.
        ("S = sum(numeric(L_2)*i, i, 1, 3)", "Write S = sum(L_2*i, i, 1, 3), then numeric(S)."),
        ("A = integrate(numeric(q_2)*x, x, 0, L_2)", "Write A = integrate(q_2*x, x, 0, L_2), then numeric(A)."),
        # A power or an index binds tighter than the call it came out of.
        ("d = numeric(L_2^3)**(1/3)", "Write d = (L_2^3)**(1/3), then numeric(d)."),
        ("y = numeric(K^2)[1,1]", "Write y = (K^2)[1,1], then numeric(y)."),
        # A line of its own is written back as it is, even where every name has a value.
        ('image("beam.png", "Viga", width=numeric(L_2))', 'Write image("beam.png", "Viga", width=L_2).'),
        # A part of a matrix is no named numeric: it stored `M`'s body at the sheet's `x`.
        ("K[1, 1] = numeric(M(L_2))", "Write K[1, 1] = M(L_2), then numeric(K)."),
        ("K[1, 1] = report(M_2)", "Write K[1, 1] = M_2, then report(K)."),
    ],
)
def test_the_line_written_back_runs(line, written, monkeypatch):
    source = BASE + "K = [1*m^2, 2*m^2; 3*m^2, 4*m^2]\n" + line + "\n"
    _page, console = _run(source, monkeypatch)
    assert "must be a standalone statement" in console, console
    assert written in console, console


@pytest.mark.parametrize(
    ("written", "shown"),
    [
        ("y = M(x)*2", r"y & = & q_{2} x^{2}"),
        ("d = (L_2^3)**(1/3)\nnumeric(d)", r"3.00\,\mathrm{m} \end{array}"),
        ("y = (K^2)[1,1]\nnumeric(y)", r"7.00\,\mathrm{m}^{4} \end{array}"),
        ("K[1, 1] = M(L_2)\nnumeric(K)", r"45.00"),
    ],
)
def test_pasted_back_it_gives_the_value_meant(written, shown, monkeypatch):
    source = BASE + "K = [1*m^2, 2*m^2; 3*m^2, 4*m^2]\n" + written + "\n"
    page, console = _run(source, monkeypatch)
    assert not console, console
    assert shown in page, page


def test_a_line_of_a_for_is_written_back_as_the_for_writes_it(monkeypatch):
    source = BASE + "% for i in range(1, 3):\nM_{i} = q_2*numeric(L_2^2)/(8*{i})\n% end\n"
    _page, console = _run(source, monkeypatch)
    assert "engcalc: line 6: numeric must be a standalone statement" in console, console
    assert "Write M_{i} = q_2*L_2^2/(8*{i}), then numeric(M_{i})." in console, console


def test_a_comment_after_a_string_with_a_quote_in_it_is_not_written_back():
    assert _without_a_comment('plot(M(x), title="5\\" bar") # note') == 'plot(M(x), title="5\\" bar")'
    assert _without_a_comment("f('it''s') # note") == "f('it''s')"


def test_keep_of_a_result_leaves_the_substitution_out(monkeypatch):
    page, console = _run(BASE + "keep w = result(M_2)\n", monkeypatch)
    plain, _console = _run(BASE + "w = result(M_2)\n", monkeypatch)
    assert not console, console
    assert r"\left(10.00" not in page, page
    assert page.count(r"\\[") == plain.count(r"\\["), (page, plain)
