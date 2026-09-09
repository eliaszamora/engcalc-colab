r"""A matrix inverse keeps the names its formula was written with.

The frame memoria ends in a static condensation, and its last two matrices were the only
ones still printed in nodal coordinates:

    K_ii  =  [ 4 E I_c / L_c        0          ]        legible
    K_id  =  [ 6 s_c E I_c / L_c^2  ...        ]        legible
    C     =  [ -3(-y_1+y_2) sqrt(x_1^2 - 2 x_1 x_2 + ...) / ... ]     not
    k_eq  =  [ ... the same again ... ]                              not

Two causes stacked, and the first hid the second.

**`inv` was not on `_WRITTEN_FORM_SAFE_CALLS`**, so `C = -inv(K_ii)*K_id` got no written
form at all - the same shape as the `transpose` finding one release earlier. #123 left it
off, on a measurement that said adding it changed nothing on any sheet, and *that
measurement was right about the frame sheet and wrong as a general claim*: on a small
sheet, `P = inv(K)*N` keeps its `L` the moment `inv` is allowed. The comment recording it
said more than had been measured, which is section 3 of HOW-THIS-WORK-GOES-WRONG.md.

**And behind it, a false negative in the verification.** With `inv` allowed, the written
form for `C` is built and then rejected: `_agrees_with` asks `difference.is_zero_matrix`
and SymPy answers `None` - not "no", but "I will not prove this without work". The form
is correct; the check cannot see it.

The work turns out to be cheap. Measured on that exact difference:

    is_zero_matrix as it stands   None
    cancel, cell by cell          True    0.04 s
    simplify, cell by cell        True    0.53 s
    radsimp, cell by cell         None    0.60 s

`cancel` normalises a rational function and answers in forty milliseconds, where
`simplify` - the push `_agrees_with` already refuses for scalars, at ~33 ms each and
failing three of seven real formulas - takes thirteen times as long. It is tried only
when the plain question came back `None`, so it can add time only where the answer was
going to be "no" anyway.

The cost of allowing `inv` is real and is the second walk: the frame sheet goes from
0.32 s to about 0.7 s, because a symbolic inverse is computed twice. Before this it
bought nothing on that sheet; now it buys the conclusion of the memoria.
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


GEOMETRY = "a := 3*m\nb := 4*m\nkeep L = sqrt(a^2 + b^2)\n"


def test_an_inverse_keeps_a_kept_name(cell):
    """The small case, which the #123 measurement missed by looking at one sheet."""
    final = _last(cell(GEOMETRY + "K = [L, 0; 0, L]\nN = [1, 0; 0, 1]\nP = inv(K)*N\n"))
    assert "L" in final, final
    assert "sqrt" not in final, final


def test_the_condensation_of_a_frame_reads_in_its_own_names(cell):
    """The benchmark's own shape, cut to its bones: a 2x2 inverse of a stiffness written
    in `E`, `I_c` and `L_c`, times a coupling written the same way. This is the statement
    whose written form was built and then rejected."""
    sheet = (
        "E := 210*GPa\nb_c := 300*mm\nd_c := 450*mm\n"
        "x_1 := 0*m\nx_2 := 0*m\ny_1 := 0*m\ny_2 := 3.70*m\n"
        "keep I_c = b_c*d_c^3/12\n"
        "keep L_c = sqrt((x_2 - x_1)^2 + (y_2 - y_1)^2)\n"
        "K_ii = [4*E*I_c/L_c, 0; 0, 4*E*I_c/L_c]\n"
        "K_id = [6*E*I_c/L_c^2; 6*E*I_c/L_c^2]\n"
        "C = -inv(K_ii)*K_id\n"
    )
    final = _last(cell(sheet))
    assert "L_{c}" in final, final
    assert "x_{2}" not in final, final
    assert "sqrt" not in final, final


def test_the_value_is_untouched(cell):
    """`C = -K_ii^-1 K_id` with 4EI/L on the diagonal and 6EI/L^2 coupling is
    -6EI/L^2 / (4EI/L) = -3/(2 L), and L is 3.70 m, so -0.405 1/m."""
    sheet = (
        "E := 210*GPa\nb_c := 300*mm\nd_c := 450*mm\n"
        "x_1 := 0*m\nx_2 := 0*m\ny_1 := 0*m\ny_2 := 3.70*m\n"
        "keep I_c = b_c*d_c^3/12\n"
        "keep L_c = sqrt((x_2 - x_1)^2 + (y_2 - y_1)^2)\n"
        "K_ii = [4*E*I_c/L_c, 0; 0, 4*E*I_c/L_c]\n"
        "K_id = [6*E*I_c/L_c^2; 6*E*I_c/L_c^2]\n"
        "C = -inv(K_ii)*K_id\n"
        "numeric(C)\n"
    )
    final = _last(cell(sheet))
    assert "-0.41" in final or "−0.41" in final, final


# --- what must not move ---------------------------------------------------------------

def test_a_written_form_that_is_genuinely_wrong_is_still_refused(cell):
    """The verification is what stands between a readable formula and a false one, and
    the new push must not turn it into a rubber stamp. A definition whose written form
    does not equal its value has no written form, and the page shows the evaluated
    expression rather than a formula that lies about it.
    """
    from engcalc_colab.engine import _agrees_with
    import sympy as sp

    a, b = sp.symbols("a b")
    assert _agrees_with(a + b, a + b)
    assert not _agrees_with(a + b, a - b)
    assert not _agrees_with(sp.Matrix([[a, 0], [0, a]]), sp.Matrix([[b, 0], [0, b]]))


def test_a_matrix_that_does_agree_still_verifies(cell):
    from engcalc_colab.engine import _agrees_with
    import sympy as sp

    a = sp.symbols("a")
    assert _agrees_with(sp.Matrix([[a, 0], [0, a]]), sp.Matrix([[a, 0], [0, a]]))


# --- the cost, pinned by counting rather than by a clock ---------------------------------

@pytest.fixture
def counted(monkeypatch):
    """How many times `_agrees_with` reaches for each normaliser.

    Two mutants survive every correctness contract here, because neither changes an
    answer: running the push unconditionally, and running `simplify` instead of `cancel`.
    Both are pure cost - `simplify` was measured at thirteen times `cancel` on the one
    difference that needs it - and cost is what a counter can see and a wall clock cannot
    see reliably.
    """
    import sympy as sp

    from engcalc_colab import engine

    counts = {"cancel": 0, "simplify": 0}

    def counting(name, original):
        def wrapper(*args, **kwargs):
            counts[name] += 1
            return original(*args, **kwargs)

        return wrapper

    monkeypatch.setattr(engine.sp, "cancel", counting("cancel", sp.cancel))
    monkeypatch.setattr(engine.sp, "simplify", counting("simplify", sp.simplify))
    return counts


def test_the_push_is_skipped_when_the_plain_question_answers(counted):
    """`is_zero_matrix` answers True here, so nothing more is owed. The mutant that
    drops the early return computes an answer it already had, on every matrix the
    renderer ever verifies."""
    import sympy as sp

    from engcalc_colab.engine import _agrees_with

    a = sp.symbols("a")
    matrix = sp.Matrix([[a, 0], [0, a]])
    assert _agrees_with(matrix, matrix)
    assert counted["cancel"] == 0, counted


def test_the_push_is_cancel_and_not_simplify(counted):
    """The inverse case: `is_zero_matrix` says None and the cheap normaliser settles it.
    `simplify` reaches the same verdict thirteen times slower, and is the push this
    function already refuses for scalars."""
    import sympy as sp

    from engcalc_colab.engine import _agrees_with

    x_1, x_2, y_1, y_2, e, inertia = sp.symbols("x_1 x_2 y_1 y_2 E I_c", positive=True)
    span = sp.Symbol("L_c", positive=True)
    expansion = sp.sqrt((x_2 - x_1) ** 2 + (y_2 - y_1) ** 2)

    stiffness = sp.Matrix([[4 * e * inertia / span, 0], [0, 4 * e * inertia / span]])
    coupling = sp.Matrix([[6 * e * inertia / span**2], [6 * e * inertia / span**2]])

    # The written form keeps `L_c`; the value never had it, because the evaluator worked
    # in coordinates from the start and SymPy simplified along a different road. That is
    # what makes the two equal and not structurally equal, and it is the whole reason
    # `is_zero_matrix` answers None here rather than True.
    written = -stiffness.inv() * coupling
    value = (
        -stiffness.subs({span: expansion}).inv() * coupling.subs({span: expansion})
    )

    assert _agrees_with(written, value, {span: expansion})
    assert counted["cancel"] > 0, counted
    assert counted["simplify"] == 0, counted
