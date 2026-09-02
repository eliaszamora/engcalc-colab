"""`subs(expr, v1, a1, v2, a2, ...)` substitutes several variables at once.

Step 3.2. The existing three-argument form is the one-pair case of the same rule, which
is why it needs no special case and keeps working unchanged - the same shape as the
scalar equation systems of 0.12.0, where `solve(eq, x)` became the n = 1 case of
`solve(eq_1, ..., eq_n, x_1, ..., x_n)`.

Pairs rather than keyword arguments: the restricted language has no keyword arguments,
and SymPy's own multi-substitution takes pairs too - `expr.subs([(x, a), (y, b)])`.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell


def run_cell(engine: EngineeringEngine, source: str):
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return results


def test_two_substitutions_in_one_call():
    result = run_cell(EngineeringEngine(), "a = subs(x^2 + y, x, 3, y, 4)")[-1]
    assert str(result.value) == "13"


def test_three_substitutions():
    result = run_cell(EngineeringEngine(), "a = subs(x + y + z, x, 1, y, 2, z, 3)")[-1]
    assert str(result.value) == "6"


def test_the_substitutions_are_simultaneous_not_sequential():
    """`subs(x + y, x, y, y, 2)` must not turn x into y and then that y into 2.

    SymPy substitutes sequentially by default and simultaneously when asked. Sequential
    would give 4 here; simultaneous gives y + 2, which is what writing both replacements
    on one line means.
    """
    result = run_cell(EngineeringEngine(), "a = subs(x + y, x, y, y, 2)")[-1]
    assert str(result.value) == "y + 2"


def test_the_single_pair_form_is_unchanged():
    result = run_cell(EngineeringEngine(), "a = subs(x^2, x, 3)")[-1]
    assert str(result.value) == "9"


def test_it_works_on_a_beam_expression_with_units():
    """Both replacements are names that carry numeric values.

    A literal like `20*kN/m` cannot be substituted here, and that is not this feature's
    doing: in the symbolic layer `kN` and `m` are ordinary free symbols, because units
    live in the numeric context. Substituting a declared name is how it is written.
    """
    engine = EngineeringEngine()
    result = run_cell(
        engine,
        "L := 6*m\nc := 2*m\nq := 10*kN/m\n"
        "M(x, b) = q*x*(L-b)/2\n"
        "numeric(subs(M(x, b), x, L/2, b, c))",
    )[-1]
    # 10 kN/m * 3 m * (6 - 2) m / 2
    assert float(result.quantity.to("kN*m").magnitude) == pytest.approx(60.0)


def test_it_works_entry_by_entry_on_a_matrix():
    result = run_cell(EngineeringEngine(), "A = subs([x, y; x*y, 1], x, 2, y, 5)")[-1]
    assert "10" in str(result.value)


def test_an_even_argument_count_is_refused():
    """One expression then variable/value pairs, so the count is odd."""
    with pytest.raises(EngEvaluationError) as excinfo:
        run_cell(EngineeringEngine(), "a = subs(x + y, x, 1, y)")
    assert "pairs" in str(excinfo.value).lower()


def test_a_bare_expression_with_no_pairs_is_refused():
    with pytest.raises(EngEvaluationError):
        run_cell(EngineeringEngine(), "a = subs(x)")
