"""The shipped notebook runs.

`examples/memoria-viga.ipynb` is what someone opens in Colab first. An example that
fails on its second cell is worse than no example: the reader concludes the tool is
broken, and they are not wrong to.

The install cell is skipped - it reaches the network and its correctness is GitHub's -
but every `%%eng` and `%eng_help` cell is executed here in the order the notebook has
them, against the same magic a notebook uses.
"""

import json
import pathlib

import matplotlib
import pytest

matplotlib.use("Agg")

NOTEBOOK = pathlib.Path(__file__).resolve().parents[1] / "examples" / "memoria-viga.ipynb"


def _code_cells():
    document = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return [
        "".join(cell["source"])
        for cell in document["cells"]
        if cell["cell_type"] == "code"
    ]


def test_the_notebook_exists_and_has_cells():
    cells = _code_cells()
    assert len(cells) >= 6, cells


def test_every_cell_runs_in_order(monkeypatch):
    """One magic across all of them, because the cells depend on each other.

    Running each in a fresh engine would pass while the notebook failed: cell 5 uses the
    reactions cell 4 solved for.
    """
    import engcalc_colab.magic as magic_module

    displayed = []
    monkeypatch.setattr(magic_module, "display", displayed.append)
    magics = magic_module.EngMagics(shell=None)

    for source in _code_cells():
        if source.startswith("%pip"):
            continue
        if source.startswith("%eng_help"):
            _, _, argument = source.partition(" ")
            magics.eng_help(argument.strip())
            continue
        assert source.startswith("%%eng"), source
        magics.eng("", source.split("\n", 1)[1])

    assert displayed, "the notebook displayed nothing"


def test_the_notebook_shows_the_features_it_claims_to(monkeypatch):
    """A notebook that runs but exercises nothing would pass the test above.

    These are the calls it exists to demonstrate; losing one to an edit should fail.
    """
    joined = "\n".join(_code_cells())
    for call in (
        "%eng_help",
        "solve(",
        "numeric(",
        "subs(",
        "plot(",
        "report(",
        "summary()",
        "extrema(",
    ):
        assert call in joined, f"the notebook no longer demonstrates {call}"


def test_no_cell_carries_a_control_character():
    """A backslash escape mangled by a shell has reached committed files twice."""
    text = NOTEBOOK.read_text(encoding="utf-8")
    assert not [char for char in text if ord(char) < 32 and char not in "\n\t"]


def test_the_install_cell_points_at_this_repository():
    cells = _code_cells()
    install = next(cell for cell in cells if cell.startswith("%pip"))
    assert "github.com/eliaszamora/engcalc-colab" in install
    assert "%load_ext engcalc_colab" in install
