r"""A matrix takes a common power of ten outside its brackets, and stays in kilonewtons.

The engineer read an assembled stiffness and said what he wanted instead:

    "Prefiero que nos quedemos con kN, s, m ... para no usar tantos números en las
     matrices no podrías colocar un multiplicador de 10^3 x [] ... así evitamos usar
     la unidad Mega."

Which is how a stiffness matrix is printed in every textbook:

    K = 10^3 [ 517.20 kN*m   209.67 kN     0           ]
             [ 209.67 kN     240.31 kN/m   209.67 kN   ]
             [ 0             209.67 kN     517.20 kN*m ]

Each cell keeps its own dimension - they are a moment per radian, a force and a force per
length, and no single unit can cover them - while the digits move outside once.

Two things, and the second only works because of the first. The families stop at kilo, so
nothing reaches mega and a large value stays a large number in kN; then the matrix takes
that largeness outside as a power of ten. MPa and GPa are left alone deliberately: a
concrete strength is 25 MPa and a modulus 210 GPa in every code on the shelf, and nobody
writes 25000 kPa.

The exponent is a multiple of three, so the reader is choosing between the prefixes they
already know, and it is only taken when every cell survives it - a matrix holding both a
large and a small entry keeps its digits rather than flattening the small one to zero.
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


COLUMN = "E := 210*GPa\nb := 300*mm\nd := 450*mm\nh := 3.70*m\nkeep I_c = b*d**3/12\n"


# --- kilo, not mega ---------------------------------------------------------------

def test_a_large_force_stays_in_kilonewtons(cell):
    final = _final(cell("F := 209670*kN\nG = 1*F\nnumeric(G)\n"))
    assert "209670.00" in final, final
    assert r"\mathrm{kN}" in final, final
    assert "MN" not in final, final


def test_a_large_moment_stays_in_kilonewton_metres(cell):
    final = _final(cell(COLUMN + "k = 4*E*I_c/h\nnumeric(k)\n"))
    assert "517195.95" in final, final
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final
    assert "MN" not in final, final


def test_a_stress_is_left_in_megapascals(cell):
    """The deliberate exception. A concrete strength is 25 MPa in every code on the
    shelf, and 25000 kPa is not a thing anyone writes."""
    final = _final(cell("fc := 25*MPa\ns = 1*fc\nnumeric(s)\n"))
    assert "25.00" in final, final
    assert r"\mathrm{MPa}" in final, final


# --- the multiplier ---------------------------------------------------------------

def test_a_large_matrix_takes_its_scale_outside(cell):
    final = _final(cell(
        COLUMN + "K = [4*E*I_c/h, 6*E*I_c/h**2; 6*E*I_c/h**2, 12*E*I_c/h**3]\nnumeric(K)\n"
    ))
    assert "10^{3}" in final, final
    assert "517.20" in final, final
    assert "209.67" in final, final
    assert "113.34" in final, final


def test_each_cell_keeps_its_own_unit_under_the_multiplier(cell):
    """The multiplier is a number, so it changes nothing about dimensions: a mixed
    matrix still carries a unit per cell."""
    final = _final(cell(
        COLUMN + "K = [4*E*I_c/h, 6*E*I_c/h**2; 6*E*I_c/h**2, 12*E*I_c/h**3]\nnumeric(K)\n"
    ))
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final
    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in final, final


def test_a_matrix_already_in_the_readable_band_is_left_alone(cell):
    final = _final(cell("a := 12*kN\nb := 340*kN\nM = [a, b]\nnumeric(M)\n"))
    assert "10^{" not in final, final
    assert "12.00" in final and "340.00" in final, final


def test_a_matrix_of_small_but_readable_numbers_is_left_alone(cell):
    """Large and small are different questions. The condensation matrix of a frame holds
    -0.405 1/m in both entries; `-0.41` reads perfectly and does not want to become
    `10^-3 [-405.41]`. Below the band what matters is whether the number still says
    anything, which is the test the family rule already uses for a single value."""
    final = _final(cell("a := 0.405*m\nb := 0.405*m\nM = [a/(1*m**2), b/(1*m**2)]\nnumeric(M)\n"))
    assert "10^{" not in final, final
    assert "0.41" in final or "0.40" in final, final


def test_a_matrix_too_small_to_read_does_take_its_scale_out(cell):
    """The other side of that test: `0.0008` shows `0.00` and has nothing left to say,
    so the scale comes out and the digits come back.

    Strains, because they are dimensionless and there is no family to reach for - a
    `0.0008 kN` force does not need this, it becomes `0.80 N`, and the family answering
    is the better answer where a family exists.

    The exponent lands on -6 rather than -3, and that is the convention rather than a
    coincidence: a strain of 0.0008 is written `800 x 10^-6`, which is what microstrain
    means. Sizing on the largest entry puts it in the band, and the band is where the
    conventional prefix already is.
    """
    final = _final(cell("ea := 0.0008\neb := 0.0005\nM = [ea, eb]\nnumeric(M)\n"))
    assert "10^{-6}" in final, final
    assert "800.00" in final and "500.00" in final, final


def test_the_exponent_is_a_multiple_of_three(cell):
    """So the reader is choosing among the prefixes they already know."""
    final = _final(cell("a := 45000000*kN\nb := 12000000*kN\nM = [a, b]\nnumeric(M)\n"))
    assert "10^{6}" in final, final
    assert "45.00" in final and "12.00" in final, final


def test_a_matrix_holding_a_large_and_a_small_entry_keeps_its_digits(cell):
    """Taking the large one's scale outside would flatten the small one to 0.00, so the
    multiplier is declined and the matrix reads as it did."""
    final = _final(cell("a := 500000*kN\nb := 2*kN\nM = [a, b]\nnumeric(M)\n"))
    assert "10^{" not in final, final
    assert "500000.00" in final and "2.00" in final, final


def test_a_homogeneous_matrix_still_prints_its_unit_once(cell):
    final = _final(cell("a := 517195*kN*m\nb := 209670*kN*m\nM = [a, b]\nnumeric(M)\n"))
    assert "10^{3}" in final, final
    assert final.count(r"\mathrm{kN} \cdot \mathrm{m}") == 1, final
    assert "517.20" in final or "517.19" in final, final


# --- the small end, carried over from the family module this replaced ---

def test_a_small_moment_keeps_the_units_it_was_built_from(cell):
    """`N * m` is in the family for the same reason `N` is in the force family - a small
    moment is written in newton-metres, not in thousandths of a kilonewton-metre - and
    this test does *not* show it, which is worth knowing rather than hiding.

    `10 N x 500 mm` is stored as `mm * N`, which costs two unit terms, exactly what
    `N * m` costs. `_unit_is_the_engineers` therefore judges it to be what was typed and
    keeps it, so the value reads `5000.00 mm*N`. That is a legitimate unit - Eurocode
    work is full of moments in N*mm - printed with its factors in Pint's alphabetical
    order rather than the conventional one.

    Both of those are open items in `docs/project-context/NEXT.md`: the tie that
    `_unit_terms` cannot break, and the factor ordering. The family's small step is
    reached whenever the stored unit is not itself a two-term tie.
    """
    final = _final(cell("F := 10*N\nr := 500*mm\nM = F*r\nnumeric(M)\n"))
    assert "5000.00" in final, final
    assert r"\mathrm{mm} \cdot \mathrm{N}" in final, final


def test_an_ordinary_beam_moment_still_reads_in_kilonewton_metres(cell):
    """The half that must not move. A 45 kN*m span moment is in the band already, and
    the extra steps must not drag it anywhere."""
    final = _final(cell("q := 10*kN/m\nL := 6*m\nM = q*L**2/8\nnumeric(M)\n"))
    assert "45.00" in final, final
    assert r"\mathrm{kN} \cdot \mathrm{m}" in final, final


def test_an_ordinary_line_load_still_reads_in_kilonewtons_per_metre(cell):
    final = _final(cell("q := 10*kN/m\nw = 2*q\nnumeric(w)\n"))
    assert "20.00" in final, final
    assert r"\frac{\mathrm{kN}}{\mathrm{m}}" in final, final
