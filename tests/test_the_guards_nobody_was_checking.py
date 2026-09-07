r"""What EngCalc says back when an engineer types something it cannot do.

A coverage hunt over `engine.py` and `parser.py` asked which `raise` statements the suite
never executes, and found sixty-three. Each one has a message somebody wrote and nobody
had ever seen: an edit could soften any of them, or delete the guard entirely, and the
suite would stay green.

These are the ones reached by typing the mistake each was written for. Every one of them
already behaves - nothing crashes out of the magic, and every message is a sentence that
helps - so this module changes no behaviour. It stops the behaviour from changing by
accident.

Two things it is deliberately *not*:

* Not a claim to cover all sixty-three. Several messages are raised from more than one
  branch - "narrative block cannot be empty" from two, "unbalanced parentheses" from
  five - so reaching the sentence is not the same as reaching the line. What remains is
  recorded in `NEXT.md`.
* Not an assertion on exact wording. Each test pins the part of the sentence that tells
  the engineer what to do differently, which is the part worth defending. A message that
  gets clearer should not fail here; one that stops naming the problem should.
"""

import io
import contextlib

import pytest

import engcalc_colab.magic as magic


@pytest.fixture
def says(monkeypatch):
    """Run a cell and return what the notebook prints, not what it renders."""
    monkeypatch.setattr(magic, "display", lambda *_: None)

    def run(source: str) -> str:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            magic.EngMagics().eng("", source)
        return out.getvalue().strip()

    return run


# --- narrative blocks ---------------------------------------------------------------

def test_an_empty_narrative_block_says_so(says):
    assert "narrative block cannot be empty" in says('"""\n"""\n')


def test_text_after_a_narrative_block_says_so(says):
    assert "unexpected content after narrative block" in says('"""\nhola\n""" y esto\n')


def test_a_narrative_opened_and_closed_on_one_line_with_nothing_in_it(says):
    """The same sentence from the other branch. Two places raise it - the one that
    reads a block across several lines and the one that reads it on a single line - and
    reaching the message is not the same as reaching the guard."""
    assert "narrative block cannot be empty" in says('"""' + '"""' + "\n")
    assert "narrative block cannot be empty" in says('"""   """' + "\n")


# --- assignment shapes --------------------------------------------------------------

@pytest.mark.parametrize(
    "source, fragment",
    [
        ("f(x) + 1 = 2\n", "invalid assignment target"),
        ("(f)(x) = 2\n", "invalid assignment target"),
        ("a := (2*(3\n", "unbalanced parentheses"),
        ("a = (2*(3\n", "unbalanced parentheses"),
        ("a := b := 2*m\n", "multiple top-level ':=' operators"),
        ("a = b = 2\n", "multiple top-level '=' operators"),
        (":= 2*m\n", "malformed numeric assignment"),
        ("= 2\n", "malformed assignment"),
    ],
)
def test_a_malformed_assignment_names_its_problem(says, source, fragment):
    assert fragment in says(source), source


# --- calls the language does not take -----------------------------------------------

@pytest.mark.parametrize(
    "source, fragment",
    [
        ("numeric(x, unit=kN)\n", "keyword arguments are unsupported"),
        ("a = [i for i in range(3)]\n", "unsupported syntax 'ListComp'"),
        ("f = lambda x: x\n", "unsupported syntax 'Lambda'"),
        ("a = b.c\n", "unsupported syntax 'Attribute'"),
        ("a = ~x\n", "unsupported syntax 'Invert'"),
        ("a = x @ x\n", "unsupported syntax 'MatMult'"),
        ("a = 'hola'\n", "only numeric constants are supported"),
        ("a = b'x'\n", "only numeric constants are supported"),
        ("a = frobnicate(2)\n", "unsupported function 'frobnicate'"),
        ("a = (f)(2)\n", "unsupported function"),
        ("a = (f())(2)\n", "unsupported syntax 'Call'"),
        ("A = [1,2;3,4]\na = A[0](2)\n", "unsupported syntax 'Subscript'"),
    ],
)
def test_an_unsupported_shape_names_what_it_is(says, source, fragment):
    assert fragment in says(source), source


# --- assume -------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source, fragment",
    [
        ("assume()\n", "assume expects at least one comparison"),
        ("assume(L)\n", "assume takes comparisons"),
        ("assume(0 < L < 10)\n", "assume takes one comparison at a time"),
        ("y = assume(L > 0)\n", "assume must be a standalone statement"),
    ],
)
def test_assume_says_what_it_takes(says, source, fragment):
    assert fragment in says(source), source


def test_assume_does_take_several_comparisons(says):
    """The half the messages above could be read as denying. `assume takes one
    comparison at a time` guards a *chained* comparison, not several arguments, and this
    is what stops the sentence from being turned into the limit it sounds like."""
    assert says("assume(L > 0, b > 0)\n") == ""


# --- solve ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source, fragment",
    [
        ("M(x) = x\nsolve(0 < M(x) < 20, x, 0, 6)\n", "chained comparisons are unsupported"),
        ("M(x) = x\nsolve(M(x) > 2, 3, 0, 6)\n", "solve variable must be a symbolic identifier"),
        ("solve(eq(x, 2), 3)\n", "solve unknown must be a symbolic identifier"),
        ("solve(eq(x + y, 2), x, y)\n", "solve expects n equations followed by n unknowns"),
        ("solve(= 2, x)\n", "malformed equality in solve"),
        ("solve(x = 2 = 3, x)\n", "multiple '=' operators in solve equation"),
        ("solve(eq(x, x + 1), x)\n", "solve found no solution for x"),
        ("solve(eq(x, (2), x)\n", "unbalanced parentheses"),
    ],
)
def test_solve_says_what_it_takes(says, source, fragment):
    assert fragment in says(source), source


def test_solve_reads_a_bare_expression_as_equal_to_zero(says):
    """Not a guard - a convention, found while looking for one. `solve(x + 2, x)` is an
    engineer who forgot `eq(...)`, and rather than refusing it the engine reads the
    expression as `x + 2 = 0` and answers `-2`. Worth pinning because it is the kind of
    helpfulness a later edit could remove without noticing."""
    assert says("solve(x + 2, x)\n") == ""


# --- table and plot -------------------------------------------------------------------

@pytest.mark.parametrize(
    "source, fragment",
    [
        ("table(x, 0, 6, 3)\n", "table requires at least one response expression"),
        ("M(x) = x\ntable(M(x), 3, 0*m, 6*m, 3)\n", "table variable must be a symbolic identifier"),
        ("L := 6*m\ntable()\n", "unsupported table call shape"),
        ("plot()\n", "plot expects at least 4 positional arguments"),
        ("L := 6*m\nplot(L, **{'x': 1})\n", "does not support keyword unpacking"),
        ("M(x) = x\nplot(M(x), x, 0, 6, colour='red')\n", "sweep values must be a list"),
        ("M(x) = x\nplot(M(x), x, 0, 6, wrong=[1,2])\n", "is not used in the plotted expression"),
        ("M(x) = x\ntable(M(x), 2, 0, 6, 3)\n", "table variable must be a symbolic identifier"),
        ("table(x)\n", "unsupported table call shape"),
    ],
)
def test_a_table_or_plot_call_says_what_it_takes(says, source, fragment):
    assert fragment in says(source), source


# --- piecewise -------------------------------------------------------------------------

@pytest.mark.parametrize(
    "source, fragment",
    [
        ("f(x) = piecewise(1, x, 0)\n", "piecewise condition must be one direct comparison"),
        ("f(x) = piecewise(1, x < 2)\n", "piecewise expects value/condition pairs and a default"),
        ("f(x) = piecewise(x, x < 1, y, y < 2, 0)\n", "piecewise must compare an interval variable"),
        ("f(x, y) = piecewise(1, x < 1, 2, y < 2, 0)\n", "must use one interval variable"),
    ],
)
def test_piecewise_says_what_it_takes(says, source, fragment):
    assert fragment in says(source), source


# --- statements that stand alone --------------------------------------------------------

@pytest.mark.parametrize(
    "source, fragment",
    [
        ("y = summary()\n", "summary has nothing to show"),
        ("M(x) = x\ny = governing(M(x), 2*x, x, 0, 6)\n", "must be a standalone statement"),
        ("M(x) = x\ny = extrema(M(x), x, 0, 6)\n", "must be a standalone statement"),
        ("report(2 + 2)\n", "report expects one defined name"),
    ],
)
def test_a_statement_that_must_stand_alone_says_so(says, source, fragment):
    assert fragment in says(source), source


# --- characteristics ----------------------------------------------------------------------

@pytest.mark.parametrize(
    "source, fragment",
    [
        ("M(x) = x\nextrema(M(x), x, 0, 6, foo=1)\n", "keyword arguments are unsupported"),
        ("M(x) = x\ngoverning(M(x), x)\n", "governing expects at least 5 positional arguments"),
        ("M(x) = x\nextrema(M(x), 3, 0, 6)\n", "extrema variable must be a symbolic identifier"),
        ("f(x) = x**2\na = diff(f(x))\n", "diff expects 2 or 3 arguments"),
        ("f(x) = macaulay(2*x - 1)\n", "macaulay expects 2 arguments"),
        ("M(x) = x\ny = roots(M(x), x, 0, 6)\n", "must be a standalone statement"),
        ("solve(eq(x,2), x, foo=1)\n", "keyword arguments are unsupported"),
    ],
)
def test_a_characteristic_call_says_what_it_takes(says, source, fragment):
    assert fragment in says(source), source


# --- matrices and inequalities -------------------------------------------------------------

@pytest.mark.parametrize(
    "source, fragment",
    [
        ("A = [1, 2; 3, 4]\nsolve(A > 2, x, 0, 6)\n", "inequality sides must be scalar"),
        ("M(x) = x\nsolve(M(x) > 2, x, y, 6)\n", "inequality domain bound must be numerically resolvable"),
        ("A = [a, 0; 0, b]\nnumeric(eigenvects(A))\n", "numeric evaluation requires values for"),
    ],
)
def test_a_matrix_or_inequality_says_what_it_needs(says, source, fragment):
    assert fragment in says(source), source


# --- nothing here may crash out of the magic --------------------------------------------

MISTAKES = [
    '"""\n"""\n',
    "f(x) + 1 = 2\n",
    "a := (2*(3\n",
    "assume(0 < L < 10)\n",
    "M(x) = x\nsolve(M(x) > 2, 3, 0, 6)\n",
    "table(x, 0, 6, 3)\n",
    "f(x) = piecewise(1, x, 0)\n",
    "y = summary()\n",
    "a = [i for i in range(3)]\n",
    "a = frobnicate(2)\n",
    "A = [1, 2; 3, 4]\nsolve(A > 2, x, 0, 6)\n",
    "M(x) = x\ngoverning(M(x), x)\n",
]


@pytest.mark.parametrize("source", MISTAKES)
def test_a_mistake_is_reported_rather_than_raised(says, source):
    """The property that matters more than any single sentence: a cell that cannot be
    run says so and the notebook survives. A traceback escaping the magic would end the
    session's engine state along with it."""
    message = says(source)
    assert message.startswith("engcalc:"), (source, message)
    assert len(message) > len("engcalc: "), source
