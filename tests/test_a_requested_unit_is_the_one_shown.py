r"""`numeric(expr, unit)` shows the unit that was asked for.

The second argument is the one place in the language where an engineer states the display
unit outright. It is documented - `numeric expects 1 or 2 arguments: expression[,
target_unit]` - and this repository's own example notebook uses it:

    numeric(subs(M(x), x, L/2), kN*m)

It was silently ignored. The engine does its half: `convert_quantity` stores the result
in exactly the unit asked for, so `numeric(M, N*m)` holds `45000.0 N*m`. Then
`_numeric_evaluation_rows` renders it with `declared=False`, the unit family judges
`N*m` to be the algebra's rather than the engineer's, and the page prints `45.00 kN*m`.

The notebook's call happens to name the unit the family would have chosen anyway, which
is why nobody saw it.

`declared` already means "keep the unit as stored". A unit the engineer wrote into the
call is the strongest case of a declared unit there is, so the fix is to say so. What
this does *not* touch is the choice made when no unit was asked for: `numeric(M)` still
goes to the family, because there is nothing to keep.

Found by auditing `examples/memoria-viga.ipynb` after 0.28.0. Depends on #104: honouring
`N*m` before compound units kept their written order would have printed `45000.00 m*N`.
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


def _final(latex: str) -> str:
    return latex.split(r"& = &")[-1].replace(r"\end{array}", "").strip()


BEAM = "L := 6*m\nq := 10*kN/m\n"


# --- the defect --------------------------------------------------------------------

def test_a_requested_unit_is_shown(cell):
    """45 kN*m asked for in newton-metres is 45000.00 N*m."""
    final = _final(cell(BEAM + "M = q*L**2/8\nnumeric(M, N*m)\n"))
    assert "45000.00" in final, final
    assert r"\mathrm{N} \cdot \mathrm{m}" in final, final


DEFLECTION = (
    "L := 6*m\nq := 10*kN/m\nE := 200*GPa\nI_z := 80e6*mm**4\n"
    "d = 5*q*L^4/(384*E*I_z)\n"
)


def test_a_requested_unit_that_the_family_also_knows(cell):
    """Where the defect actually bites, which is narrower than "always ignored".

    A requested unit outside every family survived by accident - `cm` and `inch` are
    each one unit term, so `_unit_is_the_engineers` judged them to be what was typed and
    kept them. A requested unit that *is* a family member was overruled by the family:
    `numeric(d, m)` printed `10.55 mm`.
    """
    final = _final(cell(DEFLECTION + "numeric(d, m)\n"))
    assert r"\mathrm{m}" in final, final
    assert "mm" not in final, final
    assert "0.0105" in final or "0.01" in final, final


def test_a_requested_unit_outside_every_family_keeps_working(cell):
    """`cm` and `inch` already survived, by a rule that was not this one. They must go
    on surviving, and for a reason that now holds either way."""
    assert r"\mathrm{cm}" in _final(cell(DEFLECTION + "numeric(d, cm)\n"))
    assert r"\mathrm{in}" in _final(cell(DEFLECTION + "numeric(d, inch)\n"))


def test_a_requested_unit_reaches_a_matrix(cell):
    """The matrix path took the same argument and ignored it the same way."""
    final = _final(cell(BEAM + "K = [q*L**2/8]\nnumeric(K, N*m)\n"))
    assert "45000.00" in final, final
    assert r"\mathrm{N} \cdot \mathrm{m}" in final, final


def test_the_notebook_call_still_reads_as_it_did(cell):
    """`numeric(subs(M(x), x, L/2), kN*m)` from `examples/memoria-viga.ipynb`. It names
    the unit the family would have chosen anyway, which is why the defect went unseen -
    and it must keep reading exactly as it does."""
    final = _final(cell(
        BEAM + "R_A = q*L/2\nM(x) = R_A*x - q*x^2/2\n"
        "numeric(subs(M(x), x, L/2), kN*m)\n"
    ))
    assert "45.00" in final, final
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final


# --- what must not move -------------------------------------------------------------

def test_without_a_requested_unit_the_family_still_answers(cell):
    """The half this must not disturb. Nothing was asked for, so there is nothing to
    keep and the family chooses, exactly as before."""
    final = _final(cell(BEAM + "M = q*L**2/8\nnumeric(M)\n"))
    assert "45.00" in final, final
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final


def test_a_deflection_without_a_request_still_reaches_millimetres(cell):
    final = _final(cell(DEFLECTION + "numeric(d)\n"))
    assert "10.55" in final, final
    assert r"\mathrm{mm}" in final, final


def test_a_declared_value_is_unaffected(cell):
    final = _final(cell("q := 2.8*tonf/m\nw = 1*q\nnumeric(w)\n"))
    assert r"\mathrm{tonf}" in final, final


def test_an_incompatible_request_is_still_refused(cell):
    """The engine's own check, which must keep working: asking for a length when the
    result is a moment is an error, not a silent conversion."""
    out = cell(BEAM + "M = q*L**2/8\nnumeric(M, mm)\n")
    assert "45000.00" not in out, out
