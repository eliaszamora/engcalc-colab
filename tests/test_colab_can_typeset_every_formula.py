r"""Every formula the reference sheets put on the page, typeset by the KaTeX Colab uses.

Colab does not typeset a notebook with MathJax. Asked from inside an output on 2026-09-23:
`window.MathJax` is absent, `katex.version` is 0.16.28, loaded from gstatic - for the
`text/latex` a `%%eng` cell displays and for the `$...$` in its Markdown alike. The preview
this repository renders its pages with is MathJax 3, and the two differ: 0.33.1 calibrated
a matrix's row spacing on MathJax and it read tight in Colab; 0.33.2 still let two matrices
one above the other touch, because KaTeX reads `\\[len]` as LaTeX does, a minimum depth.
Both reached him before anything here could have seen them.

This test hands every formula of the reference sheets - the five pages the snapshot test
pins, the eighteen gap-map exercises, and the matrix derivation he asked for - to that same
KaTeX, pinned in `tools/katex/package.json`, and fails on any it cannot typeset: in Colab
that formula would be red source text in place of the mathematics. It does not measure
spacing; `test_a_matrix_row_has_room` pins that. It makes sure Colab can draw the page at
all.

KaTeX runs under Node. Install it with `npm ci --prefix tools/katex`. Without it the test
is skipped on a workstation and fails in CI, where the workflow installs it.
"""

import contextlib
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import matplotlib
import pytest

from IPython.display import Markdown, Math

import engcalc_colab.magic as magic

matplotlib.use("Agg")

ROOT = pathlib.Path(__file__).resolve().parents[1]
KATEX = ROOT / "tools" / "katex"
sys.path.insert(0, str(ROOT / "tools"))

from gap_map_exercises import EXERCISES  # noqa: E402

from test_the_reference_pages_do_not_move import REFERENCE_PAGES  # noqa: E402

# The mathematics inside a narrative block: `$...$`, not an escaped dollar.
_INLINE_MATH = re.compile(r"(?<!\\)\$(.+?)(?<!\\)\$", re.S)


def _sheets() -> list[tuple[str, str, str]]:
    sheets = [(name, path.read_text(encoding="utf-8"), palette) for name, path, palette in REFERENCE_PAGES]
    sheets.append(("matrix-derivation", (ROOT / "tools" / "matrix_derivation.eng").read_text(encoding="utf-8"), ""))
    # The gap map's exercises last. Some ask for what EngCalc does not do - that is what the
    # gap map measures - and the cell is refused whole, so they may put nothing on the page.
    sheets += [(title.split()[0], source, "") for title, _area, source in EXERCISES]
    return sheets


_MUST_DRAW = {name for name, _, _ in REFERENCE_PAGES} | {"matrix-derivation"}


def _formulas(source: str, palette: str, monkeypatch) -> list[dict]:
    """Every formula a sheet puts on the page, as Colab would hand it to KaTeX."""
    captured: list = []
    monkeypatch.setattr(magic, "display", captured.append)
    engine = magic.EngMagics()
    with contextlib.redirect_stdout(io.StringIO()):
        if palette:
            engine.eng_units(palette)
        engine.eng("", source)
    formulas = []
    for item in captured:
        if isinstance(item, Math):
            formulas.append({"tex": item.data, "display": True})
        elif isinstance(item, Markdown):
            formulas += [{"tex": tex, "display": False} for tex in _INLINE_MATH.findall(item.data)]
    return formulas


def _katex_available() -> bool:
    return shutil.which("node") is not None and (KATEX / "node_modules" / "katex").is_dir()


def _typeset(formulas: list[dict]) -> dict:
    run = subprocess.run(
        ["node", str(KATEX / "render.cjs")],
        input=json.dumps(formulas),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(run.stdout)


@pytest.fixture(scope="module")
def katex_ready():
    if not _katex_available():
        message = "KaTeX is not installed; run `npm ci --prefix tools/katex`"
        if os.environ.get("CI"):
            pytest.fail(message + " - the CI workflow is meant to have done it")
        pytest.skip(message)


def test_it_is_the_katex_colab_uses(katex_ready):
    assert _typeset([{"tex": "x", "display": True}])["version"] == "0.16.28"


@pytest.mark.parametrize(("name", "source", "palette"), _sheets(), ids=[name for name, _, _ in _sheets()])
def test_colab_can_typeset_every_formula_on_the_sheet(katex_ready, monkeypatch, name, source, palette):
    formulas = _formulas(source, palette, monkeypatch)
    if name in _MUST_DRAW:
        assert formulas, f"{name} put no formula on the page"
    if not formulas:
        return
    results = _typeset(formulas)["results"]
    failed = [
        f"{result['error']}\n    in: {formula['tex'][:300]}"
        for formula, result in zip(formulas, results)
        if result["error"]
    ]
    assert not failed, f"{name}: {len(failed)} of {len(formulas)} formulas KaTeX cannot typeset:\n" + "\n".join(failed)


def test_a_formula_katex_cannot_typeset_is_caught(katex_ready):
    """The check itself, on a command KaTeX does not have."""
    results = _typeset([{"tex": r"\notacommand{x}", "display": True}])["results"]
    assert results[0]["error"], results
