r"""A line whose right-hand side is all numbers is not written out twice.

Found by reading `formas.eng` on 0.31.4, where a block added for the unit spellings put
this on the page:

    M_lim  =  20 kN·m
           =  20 kN·m        <- the same row again
           =  20.00 kN·m

The middle stage is the substitution: the formula with every name replaced by its value.
When the right-hand side has no names in it there is nothing to replace, so it is the
formula again, character for character. A memoria that says a thing twice in a row asks
the reader to look for the difference, and there is none.

It is not new - 0.31.3 wrote the same three rows - and it is not only `numeric`. The same
stage repeats for a matrix of literals and for `report`, so the rule is the general one:
**a stage that says exactly what the stage above it says is not written.**

Nothing else is dropped. `A = b h` still shows `(30.00 cm) (60.00 cm)` between its
formula and its value, which is the step the substitution exists for.
"""

import matplotlib
import pytest

from IPython.display import Math

import engcalc_colab.magic as magic

from conftest import without_spacer_rows

matplotlib.use("Agg")


@pytest.fixture
def stages(monkeypatch):
    def read(source: str) -> list[str]:
        """The rows of the last statement: the one that names it, and its continuations."""
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        magic.EngMagics().eng("", source)
        maths = [item.data for item in captured if isinstance(item, Math)]
        assert maths, "the cell displayed no mathematics"
        # The room a matrix is given is not a stage; see test_a_matrix_row_has_room.
        body = without_spacer_rows(maths[-1])
        body = body[body.index(r"{lcl}") + len(r"{lcl}") :].replace(r"\end{array}", "")
        rows = [row.strip() for row in body.split(r"\\[8pt]")]
        named = [index for index, row in enumerate(rows) if row.startswith(r"\displaystyle")]
        return rows[named[-1] :]

    return read


def test_a_line_of_literals_is_not_written_out_twice(stages):
    """The row the engineer would have read twice."""
    written = stages("M_lim = 20*kN*m\nnumeric(M_lim)\n")
    assert len(written) == 2, written
    assert written[0].endswith(r"20\,\mathrm{kN} \cdot \mathrm{m}")
    assert written[1].endswith(r"20.00\,\mathrm{kN} \cdot \mathrm{m}")


def test_a_matrix_of_literals_is_not_written_out_twice(stages):
    """The same stage, drawn by the matrix renderer."""
    written = stages("K = [10*kN, 0; 0, 10*kN]\nnumeric(K)\n")
    assert len(written) == 2, written
    assert r"10.00" in written[-1]


def test_a_report_of_literals_is_not_written_out_twice(stages):
    """And by `report`, which is how a memoria asks for the same thing."""
    written = stages("q = 2*kN/m\nreport(q)\n")
    assert len(written) == 2, written
    assert written[-1].endswith(r"2.00\,\frac{\mathrm{kN}}{\mathrm{m}}")


# --- what must not move ---------------------------------------------------------------


@pytest.mark.parametrize(
    "source, middle",
    [
        (
            "b := 30*cm\nh := 60*cm\nA = b*h\nnumeric(A)\n",
            r"\left(30.00\,\mathrm{cm}\right)",
        ),
        (
            "L := 6*m\nd = L/300\nnumeric(d)\n",
            r"\frac{\left(6.00\,\mathrm{m}\right)}{300}",
        ),
    ],
)
def test_a_substitution_that_says_something_is_still_written(stages, source, middle):
    """The step the middle row exists for: the names replaced by what they stand for."""
    written = stages(source)
    assert len(written) == 3, written
    assert middle in written[1], written[1]


def test_a_matrix_whose_names_are_replaced_keeps_its_middle_stage(stages):
    written = stages("k := 10*kN\nK = [k, 0; 0, k]\nnumeric(K)\n")
    assert len(written) == 3, written
    assert r"\left(10.00\,\mathrm{kN}\right)" in written[1], written[1]
