r"""An eigenvalue's multiplicity is not written `m`.

An eigenvalue set printed every value with its multiplicity as `m`:

    λ = 1.65 kN/(kg·m), m = 1 ; λ = 9.10 kN/(kg·m), m = 1

on a dynamics sheet whose masses are `m_1`, `m_2` - and a building's modes printed
`m = 1` beside the storey masses they came from. On the one kind of sheet that asks for
eigenvalues, `m` is the mass. Found by the audit of 0.31.14; the engineer left the call to
me.

A simple eigenvalue - multiplicity 1, which is every mode of an ordinary structure - now
carries no label, because it says nothing the list does not already say. A repeated one
says so in words, `multiplicity 2`: that is the case where the count is information, two
modes sharing one frequency, and a symmetric structure is where an engineer meets it. The
word is English, like the rest of the block vocabulary.

These read the raw LaTeX. The old label was always `\;m=`, so its absence is a precise
test; `multiplicity` is checked absent too, so a rule that labelled every entry with the
new word would not pass for one that labels none.
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


TWO_STOREYS = (
    "k_1 := 2000*kN/m\nk_2 := 1500*kN/m\nm_1 := 500*kg\nm_2 := 400*kg\n"
    "K = [k_1 + k_2, -k_2; -k_2, k_2]\nM = diag(m_1, m_2)\n"
)


def test_a_mode_of_a_frame_carries_no_label(cell, capsys):
    raw = cell(TWO_STOREYS + "lam = eigenvals(inv(M)*K)\nnumeric(lam)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert raw.count(r"\lambda=") == 4, raw  # the closed form and its numbers, two each
    assert r"\;m=" not in raw, raw
    assert "multiplicity" not in raw, raw


def test_a_mode_shape_carries_no_label_either(cell, capsys):
    raw = cell(TWO_STOREYS + "phi = eigenvects(inv(M)*K)\nnumeric(phi)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert raw.count(r"\mathbf{v}_{1}=") == 4, raw
    assert r"\;m=" not in raw, raw
    assert "multiplicity" not in raw, raw


def test_a_repeated_eigenvalue_says_so_in_words(cell, capsys):
    raw = cell("A = diag(2, 2, 3)\nlam = eigenvals(A)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert (
        r"\left\{\lambda=2,\;\text{multiplicity } 2\; ; \;\lambda=3\right\}" in raw
    ), raw


def test_a_repeated_mode_says_so_before_its_vectors(cell, capsys):
    raw = cell("A = diag(2, 2, 3)\nphi = eigenvects(A)\n")
    assert "engcalc:" not in capsys.readouterr().out
    assert r"\lambda=2,\;\text{multiplicity } 2,\;\mathbf{v}_{1}=" in raw, raw
    assert r"\mathbf{v}_{2}=" in raw, raw
    assert r"\lambda=3,\;\mathbf{v}_{1}=" in raw, raw
