r"""`tools/viga.eng` has to be a beam that exists.

It is the sheet the language is demonstrated with, so whatever it models is what it
teaches. Two things in it were wrong, and the engineer's own Colab output is where they
showed:

**The point load's moment did not return to zero at the support.** The sheet wrote

    M_P(x) = P*x/2

which is the moment of a central point load for `0 <= x <= L/2` and nothing at all after
it. Past the centre it is `P*(L - x)/2`. Carried through the combination, his table read
`U2(600.00 cm) = 1.96×10⁶ kgf·cm` - a bending moment at a simple support, where a beam
has none. Checked: `1.6 * P*L/2` is exactly that number.

`piecewise` is in the language for this, and it is what the sheet should have been
showing all along: the one call whose whole purpose is a response that changes form along
the span, demonstrated on the case every engineer knows.

**And every value under "Flecha" was printed twice.** The sheet called `report(delta)`
and then `numeric(delta)`, and `report` already shows the value exactly as `numeric`
does - it says so in its own contract. Two identical derivations of a deflection, each
four rows of substitution, one under the other.
"""

import io
import pathlib
from contextlib import redirect_stdout

import pytest

import engcalc_colab.magic as magic

SHEET = pathlib.Path("tools/viga.eng").read_text(encoding="utf-8")


@pytest.fixture
def page():
    captured = []
    magic.display = captured.append
    magics = magic.EngMagics()
    with redirect_stdout(io.StringIO()):
        magics.eng("", SHEET)
    return "".join(getattr(obj, "data", "") for obj in captured)


def test_the_beam_has_no_moment_at_its_supports(page):
    """A simply supported span carries no bending moment where it is supported, and the
    table is where the sheet says otherwise."""
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.models import ParsedHeading, ParsedNarrative
    from engcalc_colab.parser import parse_cell

    engine = EngineeringEngine()
    table = None
    for item in parse_cell(SHEET):
        if isinstance(item, (ParsedHeading, ParsedNarrative)):
            continue
        result = engine.evaluate(item)
        if type(result).__name__ == "TableResult":
            table = result

    assert table is not None, "the sheet no longer has a table"
    for column in table.columns:
        first, last = column.values[0], column.values[-1]
        for end, value in (("x = 0", first), ("x = L", last)):
            magnitude = abs(float(value.to("kN*m").magnitude))
            assert magnitude < 1e-9, (column.display_label, end, magnitude)


def test_the_point_load_peaks_where_a_central_load_peaks(page):
    """`P*L/4` at mid-span, which is the number the correction has to preserve - a
    moment that is zero at both ends and zero everywhere would also pass the test
    above."""
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.models import ParsedHeading, ParsedNarrative
    from engcalc_colab.parser import parse_cell

    from engcalc_colab.numeric import engineering_registry

    units = engineering_registry()
    expected = (40 * units.kN) * (6 * units.m) / 4

    # Asked through the sheet itself, with one line appended, so the answer comes from
    # the definitions the reader sees rather than a private call path.
    engine = EngineeringEngine()
    results = []
    for item in parse_cell(SHEET + "numeric(M_P(L/2))\n"):
        if not isinstance(item, (ParsedHeading, ParsedNarrative)):
            results.append(engine.evaluate(item))

    value = results[-1].quantity
    assert float(value.to("kN*m").magnitude) == pytest.approx(
        float(expected.to("kN*m").magnitude)
    ), value


def test_no_value_is_derived_twice():
    """`report(...)` shows the value exactly as `numeric(...)` does - its own contract
    says so - so calling both prints the same four rows of substitution twice.

    Asked of the sheet rather than of the page, because that is where the mistake is and
    where it would come back: counting rows on the rendered output would also pass if the
    renderer started collapsing duplicates, which is not the thing being fixed.
    """
    marked, computed = set(), set()
    for line in SHEET.splitlines():
        line = line.strip()
        if line.startswith("report(") and line.endswith(")"):
            marked.add(line[len("report(") : -1])
        elif line.startswith("numeric(") and line.endswith(")"):
            computed.add(line[len("numeric(") : -1])

    assert marked, "the sheet no longer reports anything"
    assert not marked & computed, sorted(marked & computed)
