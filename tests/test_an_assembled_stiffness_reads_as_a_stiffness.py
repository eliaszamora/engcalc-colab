r"""`K_e = transpose(A_e) k_e A_e` prints as a stiffness matrix, not as coordinates.

The frame benchmark assembles its stiffness the way every textbook does, and the page
showed the first entry as

    b_c d_c^3 E / (3 sqrt((-x_1 + x_2)^2 + (-y_1 + y_2)^2))

where what an engineer checks against the book is

    4 E I_c / L_c

Every name in that line had been marked with `keep` - `I_c`, `L_c`, `A_c` - and the
barrier held for `A_1` and `R_1` one section above. It failed here for a second and
separate reason: `_written_form` refuses any statement containing a call that is not on
`_WRITTEN_FORM_SAFE_CALLS`, and `transpose` was not on it. No written form at all, so
the evaluated expression is what the reader gets, and the kept names are expanded inside
it.

That list exists because the written pass runs the evaluator a second time, so a call
that plots or solves would do its work twice. A transpose has no consequences to repeat.

Measured before it was added, on the benchmark:

    page     30856 chars  ->  24518
    time     0.65 s       ->  0.52 s
    `x_1`    50 occurrences  ->  16
    `L_c`    24              ->  54

Faster, because the written form is smaller than the expansion it replaces.

`inv` was measured at the same time - `C = -inv(K_ii)*K_id` is on the same page - and
changed nothing at all, so it is not on the list. An entry that cannot be shown to
matter is furniture, and section 6 of HOW-THIS-WORK-GOES-WRONG.md is about furniture.
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


def _last(latex: str) -> str:
    return latex.split(r"\\[8pt]")[-1].replace(r"\end{array}", "").strip()


COLUMN = (
    "x_1 := 0*m\nx_2 := 0*m\ny_1 := 0*m\ny_2 := 3.70*m\n"
    "E := 210*GPa\nb_c := 300*mm\nd_c := 450*mm\n"
    "keep I_c = b_c*d_c^3/12\n"
    "keep L_c = sqrt((x_2 - x_1)^2 + (y_2 - y_1)^2)\n"
    "k = [4*E*I_c/L_c, 2*E*I_c/L_c;\n"
    "     2*E*I_c/L_c, 4*E*I_c/L_c]\n"
    "A = [1, 0;\n"
    "     0, 1]\n"
)


def test_a_transposed_triple_product_keeps_its_names(cell):
    """The benchmark's own assembly, cut to a 2x2."""
    final = _last(cell(COLUMN + "K = transpose(A)*k*A\n"))
    assert "I_{c}" in final, final
    assert "L_{c}" in final, final
    assert "x_{2}" not in final, final


def test_the_same_product_without_the_transpose_was_never_broken(cell):
    """The half that already worked, kept so the fix is attributed to the right cause.
    Nothing about the barrier needed changing; only the call did."""
    final = _last(cell(COLUMN + "K = A*k*A\n"))
    assert "I_{c}" in final, final
    assert "x_{2}" not in final, final


def test_the_value_is_untouched(cell):
    """4 E I_c / L_c with I_c = 300x450^3/12 mm^4 and L_c = 3.70 m.

    `keep` and the safe-call list are both presentation. A page that reads better and
    computes differently would be a worse defect than the one being fixed.
    """
    final = _last(cell(COLUMN + "K = transpose(A)*k*A\nnumeric(K[1, 1])\n"))
    assert "517195.95" in final or "517195.94" in final, final


def test_a_call_that_is_not_on_the_list_still_stops_the_written_form(cell):
    """The rule the list is, which must not turn into "every call is fine". `inv` was
    measured and left off deliberately; this pins that leaving a call off still means
    what it meant."""
    final = _last(cell(COLUMN + "K = inv(k)\n"))
    assert "I_{c}" not in final, final
