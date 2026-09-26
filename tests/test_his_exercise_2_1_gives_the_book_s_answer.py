r"""His exercise 2.1, `tools/ejercicio_2_1.eng`: the displacement of a two-bar joint.

He brought it on 2026-09-25 because his sheet did not give the book's answer: he had added
the two elongations as vectors, which holds only for bars at a right angle, and taken AC's
force as tension. Solved by compatibility - what A moves along each bar is what that bar
lengthens - with the angles alone, as he asked (*"No podrías haberlo resuelto solamente
apoyándote en los ángulos?"*). The book: u = 2.41 mm to the right, v = 0.72 mm up,
aa' = 2.52 mm. Run with the kN palette his notebook sets, and without it.
"""

import contextlib
import io
import pathlib

import pytest

import engcalc_colab.magic as magic

SHEET = (pathlib.Path(__file__).parent.parent / "tools" / "ejercicio_2_1.eng").read_text(encoding="utf-8")
BOOK = {"u": 2.41, "v": 0.72, "aa": 2.52, "delta_ab": 2.41, "delta_ac": -0.87}


@pytest.fixture(params=["kN", ""], ids=["kN palette", "no palette"])
def solved(request, monkeypatch):
    monkeypatch.setattr(magic, "display", lambda item: None)
    magics = magic.EngMagics()
    console = io.StringIO()
    with contextlib.redirect_stdout(console):
        if request.param:
            magics.eng_units(request.param)
        magics.eng("", SHEET)
    return magics.engine, console.getvalue()


def test_the_sheet_runs_without_a_notice(solved):
    _engine, console = solved
    assert not [line for line in console.splitlines() if not line.startswith("engcalc units")], console


@pytest.mark.parametrize("name, book", BOOK.items())
def test_each_answer_is_the_book_s(solved, name, book):
    engine, _console = solved
    _substitutions, value = engine.numeric_context.evaluate_symbolic(engine.resolve_name(name))
    assert round(float(value.to("mm").magnitude), 2) == book
