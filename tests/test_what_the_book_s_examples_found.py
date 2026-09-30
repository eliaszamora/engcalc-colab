r"""What the worked examples of his book found (chapters 2-4, 2026-09-30), and the loop
note seen in his Colab with 0.44.0.

- Example 4.5: a function written before a `solve` that fixed its constants kept reading
  them as unknowns - `t = subs(diff(y(x), x), x, 0)` stayed `C_1` although `C_1 = -p`
  stood two rows above it, and `diff(t, p)` gave 0 for -1. A wrong number.
- Example 2.6: `subs(F, y, 0)` of a name `y` with a definition read `y` as its definition
  and replaced nothing, silently.
- 0.44.0 in Colab: the rule rows of a loop's note set their fractions in text style,
  smaller than every other row of the page.
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


CONSTANTS = (
    "y(x) = C_1*x + C_2 + p*x^2\n"
    "solve(eq(subs(y(x), x, 0), 0), eq(subs(y(x), x, 1), 0), C_1, C_2)\n"
    "t = subs(diff(y(x), x), x, 0)\n"
    "g = diff(t, p)\n"
)


def test_a_function_reads_the_constants_a_later_solve_fixed(monkeypatch):
    page, console = _run(CONSTANTS, monkeypatch)
    assert not console, console
    assert r"g & = & \frac{d}{d p} \left(- p\right) = -1" in page or r"g & = & -1" in page, page
    assert r"= 0 \end{array}" not in page, page


def test_a_function_reads_a_name_defined_after_it(monkeypatch):
    page, console = _run("f(x) = a*x\na = 3\nz = f(2)\n", monkeypatch)
    assert r"z & = & f\left(2\right) \\[8pt]  & = & 6" in page, page


def test_a_kept_name_in_a_function_stays_a_name(monkeypatch):
    page, console = _run("keep k = E*A/L\nf(x) = k*x\nz = f(2)\n", monkeypatch)
    assert not console, console
    assert r"2 k" in page and r"\frac{2 A E}{L}" not in page, page


def test_subs_replaces_a_name_that_has_a_definition(monkeypatch):
    page, console = _run("F = k*(y - x)\ny = P/k\nG = subs(F, y, 0)\n", monkeypatch)
    assert r"G & = & - k x" in page, page


def test_subs_says_when_there_is_nothing_to_replace(monkeypatch):
    page, console = _run("y = P/k\nF = k*(y - x)\nG = subs(F, y, 0)\n", monkeypatch)
    assert "subs(F, y, ...) replaces nothing" in console, console
    assert console.count("replaces nothing") == 1, console


def test_the_rule_of_a_loop_s_note_is_set_at_the_page_s_size(monkeypatch):
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    with contextlib.redirect_stdout(io.StringIO()):
        magic.EngMagics().eng(
            "",
            "% for i in [1, 2]:\nL_{i} := {i}[m]\nc_{i} := 2[m]/L_{i}\n% end\n",
        )
    notes = [item.data for item in captured if isinstance(item, Math) and "En cada uno" in item.data]
    assert notes and r"\quad \displaystyle c_{i} = \frac{2\,\mathrm{m}}{L_{i}}" in notes[0], notes
