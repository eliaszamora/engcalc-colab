"""`solve(M(x) > 20*kN*m, x, 0, L)` - the block says which inequality it answered.

Found by looking at the rendered memoria on 0.31.3. Every other characteristic block
names what it was asked about - `Roots — V(x)`, `Extrema — U_1(x)`,
`Intersections — A(x) / B(x)`, `Governing — x` - and this one read

    **Where x satisfies the inequality**
    Domain: 0.00 cm to 600.00 cm
    x in (76.39 cm, 523.61 cm)

under the heading "Zona donde se supera el momento admisible". A reader of the memoria
is told a region and never told what condition defines it: the `20*kN*m` the engineer
wrote is nowhere on the page. Two blocks of the same sheet name their response; this one
asks the reader to go back to the source.

Nothing had to be computed to fix it. `InequalityResult` already carried `relation`,
which no renderer had ever read, and both sides of the comparison were in the
evaluator's hands one line before it threw them away. The heading follows the family
now: `Where — M(x) > 20 kN·m`.
"""

import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ParsedHeading
from engcalc_colab.parser import parse_cell
from engcalc_colab.renderer import render_characteristic_result

from conftest import block_text


BEAM = """L := 6*m
q := 10*kN/m
M(x) = q*x*(L-x)/2
"""


def render(source: str) -> str:
    engine = EngineeringEngine()
    results = []
    for item in parse_cell(source):
        if isinstance(item, ParsedHeading):
            continue
        results.append(engine.evaluate(item))
    return render_characteristic_result(results[-1])


def rendered(source: str) -> str:
    return block_text(render(source))


def heading(source: str) -> str:
    return rendered(source).split("Domain:")[0].strip()


# `kN·m`, the way the page spells a compound unit everywhere else. It read `kN m` when
# this heading was written: two unit literals multiplied were separated by a LaTeX space
# wherever the symbolic printer met them. That was pinned here as `20 kN m` so the
# correction would have to come back and say so, and this is it saying so - see
# `test_two_units_multiplied_read_as_one_unit.py`.
LIMIT = "20 kN·m"


def test_the_heading_names_the_inequality_the_sheet_wrote():
    assert heading(BEAM + "solve(M(x) > 20*kN*m, x, 0, L)") == f"Where — M(x) > {LIMIT}"


def test_a_response_is_named_as_its_definition_names_it():
    """`M(x)`, not the expression it stands for.

    The same question `_heading_expression` answers for `roots` and `extrema`: a user
    function has a name the engineer wrote, and the block above this one in the memoria
    already uses it.
    """
    text = heading(BEAM + "solve(M(x) > 20*kN*m, x, 0, L)")
    assert "M(x)" in text
    assert "L - x" not in text and "L-x" not in text


def test_a_limit_that_is_itself_a_response_is_named_too():
    """`solve(M(x) > N(x), ...)` - a moment against another moment, not against a number.

    Added because mutation found the hole: with `20*kN*m` on the right the block reads
    the right *expression* and never the right *label*, so a change that gave both sides
    the same label - `Where — M(x) > M(x)` - passed every contract above.
    """
    sheet = BEAM + "N(x) = 2*q*x*(L-x)/2\n"
    assert heading(sheet + "solve(M(x) > N(x), x, 0, L)") == "Where — M(x) > N(x)"


def test_a_side_that_is_an_expression_is_typeset_rather_than_printed():
    """Written out instead of called, the heading still reads as mathematics.

    `str()` of the expression is Python - `q*x*(L - x)/2` - which is what the label this
    replaces has always been.
    """
    text = heading(BEAM + "solve(q*x*(L-x)/2 > 20*kN*m, x, 0, L)")
    assert "q x (L - x)/2" in text
    assert "*" not in text


@pytest.mark.parametrize(
    "comparison, relation",
    [
        ("M(x) > 20*kN*m", ">"),
        ("M(x) >= 20*kN*m", "≥"),
        ("M(x) < 20*kN*m", "<"),
        ("M(x) <= 20*kN*m", "≤"),
    ],
)
def test_each_comparison_is_headed_with_its_own_relation(comparison, relation):
    """All four, because one alone passes against a hard-coded `>`.

    `relation` has been on the result since `solve` learned inequalities and no renderer
    had ever read it, so a wrong sign here would have had nothing pinning it.
    """
    assert (
        heading(BEAM + f"solve({comparison}, x, 0, L)")
        == f"Where — M(x) {relation} {LIMIT}"
    )


def test_the_limit_keeps_the_unit_the_engineer_wrote_it_in():
    """`20*kN*m` is a moment, and a heading that said `20` would be no better than none.

    The units reach the heading as units - upright, through `unit_literals` - and not as
    a product of three italic names, which is how `kN` and `m` set in a symbolic
    expression that was never told they are units.
    """
    latex = render(BEAM + "solve(M(x) > 20*kN*m, x, 0, L)")
    assert r"20\," in latex
    assert r"\mathrm{kN}" in latex and r"\mathrm{m}" in latex


def test_the_block_still_answers_with_its_region():
    """The heading is what changed; the answer under it is what the block is for."""
    text = rendered(BEAM + "solve(M(x) > 20*kN*m, x, 0, L)")
    assert "Domain: 0.00 m to 6.00 m" in text
    assert "x in (0.76 m, 5.24 m)" in text
