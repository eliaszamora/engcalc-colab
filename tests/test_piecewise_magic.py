from IPython.display import HTML, Math
from matplotlib.figure import Figure
import engcalc_colab.magic as magic_module
from engcalc_colab.magic import EngMagics

def test_eng_magic_displays_equations_then_table_then_plot_in_source_order(monkeypatch):
    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magic = EngMagics(shell=None)
    cell = (
        "q1 := 8*kN/m\nq2 := 4*kN/m\na := 3*m\nL := 6*m\n"
        "q(x) = piecewise(q1, x < a, q2, x <= L, 0)\n"
        "numeric(q(x))\nnumeric(q(2*m))\n"
        "table(q(x), x, 0, L, 21)\nplot(q(x), x, 0, L)"
    )
    assert magic.eng("", cell) is None
    assert len(displayed) == 3
    assert isinstance(displayed[0], Math)
    assert isinstance(displayed[1], HTML)
    assert isinstance(displayed[2], Figure)
