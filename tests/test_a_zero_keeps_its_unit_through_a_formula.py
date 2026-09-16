r"""A zero reached through a formula keeps its unit, not only one reached by a single call.

#184 gave `M_B = M(L)` its `0.00 kN·m`. Every other way of writing the same zero still read
a bare `0.00`:

    subs(q*(L - x), x, L)       M(L) + M(0*m)       2*M(L)       V(L/2)*L
    R_A - q*L/2                 subs(M(x), x, L)    M(L)/L

**Why.** #184 asked `numeric(<right side>)` for the unit, and that evaluation substitutes
quantities into a function only when the right side *is* one call. Anything around the
call - a sum, a factor, `subs` - is simplified symbolically first, and SymPy's zero has no
dimension by the time a number reaches it.

**So the unit of an exact zero is asked of the formula as written, evaluated over
quantities**: each name is its value, a function of the sheet is its expression with the
arguments' quantities substituted, and `subs` evaluates its expression with the variable
set to the value's quantity. Pint keeps the unit through `(6 m) - (6 m)` wherever the
cancellation happens. A formula that cannot be evaluated that way leaves the zero as it
was, and a zero with no dimension stays a plain zero.
"""

import pytest

import engcalc_colab.magic as magic

from conftest import block_text


def last(monkeypatch, source: str) -> str:
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", source)
    text = block_text("".join(str(getattr(obj, "data", "")) for obj in captured))
    return text.rstrip().removesuffix(r"\endarray").rsplit(r"\displaystyle", 1)[-1].strip()


BEAM = (
    "L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L - x)/2\nV(x) = q*(L/2 - x)\nR_A = q*L/2\n"
)


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("subs(q*(L - x), x, L)", "0.00 kN"),
        ("M(L) + M(0*m)", "0.00 kN·m"),
        ("2*M(L)", "0.00 kN·m"),
        ("V(L/2)*L", "0.00 kN·m"),
        ("R_A - q*L/2", "0.00 kN"),
        ("subs(M(x), x, L)", "0.00 kN·m"),
        ("M(L)/L", "0.00 kN"),
    ],
)
def test_a_zero_reached_through_a_formula(monkeypatch, capsys, formula, expected):
    assert last(monkeypatch, BEAM + f"a = {formula}\nnumeric(a)\n") == expected
    capsys.readouterr()


def test_a_zero_carried_by_a_name_into_the_next_formula(monkeypatch, capsys):
    """`M_B` is a zero in kN·m from #184; the formula that uses it is a zero in kN·m too."""
    assert last(monkeypatch, BEAM + "M_B = M(L)\nM_2 = 2*M_B\nnumeric(M_2)\n") == "0.00 kN·m"
    capsys.readouterr()


# --- what must not move ---------------------------------------------------------------


def test_the_single_call_still_reads_in_its_unit(monkeypatch, capsys):
    assert last(monkeypatch, BEAM + "M_B = M(L)\nnumeric(M_B)\n") == "0.00 kN·m"
    capsys.readouterr()


def test_a_dimensionless_zero_stays_bare(monkeypatch, capsys):
    assert last(monkeypatch, "L := 6*m\nf(x) = x/L - 1\nz = 2*f(L)\nnumeric(z)\n") == "0.00"
    capsys.readouterr()


def test_a_formula_with_mixed_units_is_still_defined(monkeypatch, capsys):
    """`q*x - x` cannot be evaluated over quantities; the definition was a zero before."""
    captured = []
    monkeypatch.setattr(magic, "display", captured.append)
    magic.EngMagics().eng("", "q := 10*kN/m\nG(x) = q*x - x\ng_0 = 2*G(0*m)\n")
    capsys.readouterr()

    text = block_text("".join(str(getattr(obj, "data", "")) for obj in captured))
    assert text.rstrip().endswith(r"g_0 & = & \displaystyle 0 \endarray"), text
