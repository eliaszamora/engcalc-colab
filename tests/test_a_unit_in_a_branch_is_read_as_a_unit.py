r"""A unit written into a branch is a unit, not a name the sheet forgot to define.

Found while checking 0.31.7's own new reference block. A piecewise whose branch holds a
literal quantity kills the cell the moment the variable is left free:

    q_v(x) = piecewise(q1, x < a_q, 5*kN/m)
    numeric(q_v(x))
    -> engcalc: numeric evaluation requires values for: kN, m.
       Define the missing numeric values first, for example: kN := <value>*<unit>

which is advice nobody should follow - it asks the engineer to define the kilonewton.

**Only that path.** The definition draws `5 kN/m`, `numeric(q_v(1*m))` at a point answers
`8.00 kN/m`, and `extrema(q_v(x), x, 0, L)` answers `5.00 kN/m`. Every route through
`evaluate_symbolic` already reads an undefined unit alias as the unit, and that function
says so in its own words: "The numeric layer has always read an undefined unit alias as
the unit on the `:=` path - `L := 6*m` is metres - so this is not a new rule, it is the
same rule reaching the other path."

`partial_substitutions` is a third path it had not reached. It collected the free symbols,
found `kN` and `m` in neither the stored values nor the caller's overrides, and reported
them as missing. The two evaluators it hands off to - `build_partial_piecewise_evaluation`
and `evaluate_partial_polynomial` - both go through `evaluate_symbolic`, so they were
never the problem; the gate in front of them was.

A unit resolves for the arithmetic and stays out of the substitution stage, for the reason
`evaluate_symbolic` records: nobody writes `kN = 1 kN` under their working.

Older than 0.31.7 - measured on 0.31.6 with the tree asserted, not assumed.
"""

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import PartialNumericEvaluationResult
from engcalc_colab.parser import parse_cell

matplotlib.use("Agg")


SHEET = """q1 := 8*kN/m
a_q := 3*m
L := 6*m
q_v(x) = piecewise(q1, x < a_q, 5*kN/m)
"""


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def defined(engine: EngineeringEngine) -> None:
    for line in SHEET.strip().splitlines():
        run(engine, line)


@pytest.fixture
def page(monkeypatch):
    def render(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return render


def test_a_literal_quantity_in_a_branch_does_not_ask_for_its_units():
    """The message the engineer saw, and the reason this exists."""
    engine = EngineeringEngine()
    defined(engine)

    result = run(engine, "numeric(q_v(x))")

    assert isinstance(result, PartialNumericEvaluationResult), result


def test_the_variable_is_the_only_thing_left_free():
    """`kN` and `m` are resolved, so the piecewise payload is still built."""
    engine = EngineeringEngine()
    defined(engine)

    result = run(engine, "numeric(q_v(x))")

    assert result.unresolved_symbols == ("x",), result.unresolved_symbols
    assert result.piecewise_evaluation is not None


def test_the_branch_answers_in_the_unit_it_was_written_in(page):
    """The row the engineer reads off."""
    written = page(SHEET + "numeric(q_v(x))\n").replace(r"\dfrac", r"\frac")

    assert r"5.00\,\frac{\mathrm{kN}}{\mathrm{m}} & \text{otherwise}" in written, written
    assert r"8.00\,\frac{\mathrm{kN}}{\mathrm{m}} & \text{for}\: x < 3.00" in written, written


def test_a_unit_stays_a_unit_and_is_not_substituted(page):
    r"""Nobody writes `kN = 1 kN` under their working.

    `evaluate_symbolic` keeps a resolved unit out of the substitution stage; the path
    this file opens has to keep the same rule, or the middle row of the block would
    read `\left(1\,\mathrm{kN}\right)` where the engineer wrote a unit.
    """
    written = page(SHEET + "numeric(q_v(x))\n")

    assert r"\left(1\,\mathrm{kN}\right)" not in written, written
    assert r"\left(1\,\mathrm{m}\right)" not in written, written


# --- what must not move ---------------------------------------------------------------


def test_a_name_that_is_really_missing_still_says_so():
    """A unit is resolved; a name the sheet never defined is still reported."""
    engine = EngineeringEngine()
    defined(engine)
    run(engine, "w_v(x) = piecewise(q1, x < a_q, alpha*kN/m)")

    with pytest.raises(EngEvaluationError) as raised:
        run(engine, "numeric(w_v(x))")

    message = str(raised.value)
    assert "requires values for: alpha." in message, message
    assert "kN" not in message.split("for example")[0], message


def test_a_stored_value_beats_the_alias():
    """`m := 500*kg` makes `m` a mass, and the branch has to follow the engineer."""
    engine = EngineeringEngine()
    run(engine, "q1 := 8*kg")
    run(engine, "a_q := 3*s")
    run(engine, "m := 500*kg")
    run(engine, "r_v(t) = piecewise(q1, t < a_q, 5*m)")

    result = run(engine, "numeric(r_v(t))")

    branch = result.piecewise_evaluation.branches[-1]
    assert f"{branch.value.units:~P}" == "kg", branch.value
    assert float(branch.value.magnitude) == pytest.approx(2500.0)


def test_the_paths_that_already_worked_still_work(page):
    """A point, and an extrema block: neither went through the gate that was shut."""
    written = page(SHEET + "numeric(q_v(1*m))\nextrema(q_v(x), x, 0, L)\n")
    plain = written.replace(r"\dfrac", r"\frac")

    assert r"8.00\,\frac{\mathrm{kN}}{\mathrm{m}}" in plain, written
    assert r"5.00\,\frac{\mathrm{kN}}{\mathrm{m}}" in plain, written
