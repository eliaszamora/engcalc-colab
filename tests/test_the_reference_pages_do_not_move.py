r"""The reference pages, compared whole against a stored copy of themselves.

**Why this exists.** 0.30.10 fixed a value and broke the coordinate beside it:

    0.30.9     x = L/2   · value = L² (0.15 qD + 0.2 qL)
    0.30.10    x = 0.5 L · value = 0.15 qD L² + 0.2 qL L²

The page had been rendered and looked at before the release, which is the rule this
repository keeps. What was read was the value being changed; the coordinate two
centimetres to its left was not compared against the previous run, and the engineer
found it in his own memoria. The rule depended on someone remembering to look, and on
looking at the right part. This compares every block, every time, whoever made the change.

Every other contract here asks whether a string contains a substring. This one asks
whether anything at all moved.

**What is stored, and what is deliberately not.**

* Every output the magic hands to `display()`, in order, as the source it was handed -
  raw LaTeX and HTML, not read back through `block_text`. Reading it back would erase the
  difference between `qD` and `\mathrm{qD}`, which was a real defect (#160).
* What was printed to the console: the palette announcement, the config line.
* For a figure, what EngCalc *writes* on it: title, axis labels, legend, annotations and
  the dense summary panel. Not pixels - they move between machines and font builds while
  the figure is right. The axis offset is the one string matplotlib writes itself, so it
  is stored read back (`×10⁶`), which still catches the `1e6` it used to be.

A LaTeX array is split at its row breaks and an HTML block at its closing tags, so a
change shows up in a pull request as the row that changed, not as one line of four
hundred characters.

**When a change is intended**, regenerate and read the diff before committing it:

    ENGCALC_UPDATE_SNAPSHOTS=1 python -m pytest tests/test_the_reference_pages_do_not_move.py

The diff is the review. A snapshot regenerated without reading it protects nothing.

**When nothing was changed and it fails anyway**, a dependency moved. CI installs the
newest SymPy, Pint and matplotlib on every run, and so does the engineer's first cell,
because it carries `--upgrade`. Pint 0.26 changed the dot between two unit factors in
exactly that way (#138). Read the diff: it is the page he will get.
"""

from __future__ import annotations

import difflib
import os
import pathlib
import re

import matplotlib
import pytest

matplotlib.use("Agg")

import matplotlib.figure  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

import engcalc_colab.magic as magic  # noqa: E402

from conftest import figure_text  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAPSHOTS = pathlib.Path(__file__).resolve().parent / "snapshots"
UPDATE = os.environ.get("ENGCALC_UPDATE_SNAPSHOTS") == "1"

# (snapshot name, sheet, palette). His beam memoria the way he runs it, with the `kgf`
# palette, and the repository's own reference memoria with none - the two routes most
# of the defects this project has fixed only showed on one of.
#
# And `formas.eng`, which is not a memoria. With only the first two, this test caught 19
# of the 40 mutants written for the corrections in 0.30.8 to 0.30.11 - including the
# `0.5 L` that reached the engineer - and missed the rest almost entirely because the
# shape was on neither page: no section modulus or curvature, no swept legend, no dense
# summary panel, no cantilever, no absolute value. A page comparison sees what its pages
# contain, so that sheet contains those.
REFERENCE_PAGES = [
    ("viga-kgf", ROOT / "tools" / "viga.eng", "kgf"),
    ("memoria", ROOT / "tools" / "memoria.eng", ""),
    ("formas-kgf", ROOT / "tools" / "formas.eng", "kgf"),
]

_SUMMARY_GID = "engcalc-characteristic-summary"


# A LaTeX row break and the spacing that belongs to it: `\\` or `\\[8pt]`.
_ROW_BREAK = re.compile(r"(\\\\(?:\[[^\]]*\])?)")

# Where an HTML block is cut: after each closing tag that ends a line a reader would scan.
_HTML_BREAK = re.compile(r"(?<=</div>)|(?<=</tr>)|(?<=</thead>)")


def _latex_rows(text: str) -> list[str]:
    r"""A LaTeX array one row per line, each row keeping the break that ends it.

    `re.split` with a capturing group, consumed left to right, and not a lookbehind: the
    first draft split after every `\\` it could see, and in `\\\frac` - a row break
    followed by a fraction - it saw two, so the stored page printed a lone `\` and then
    `frac{...}` on the next line. It compared fine and it read wrong, which for a file
    whose whole job is to be read in a pull request is the same as broken.
    """
    rows: list[str] = []
    current = ""
    for part in _ROW_BREAK.split(text):
        current += part
        if _ROW_BREAK.fullmatch(part):
            rows.append(current.strip())
            current = ""
    if current.strip():
        rows.append(current.strip())
    return rows


def _lines_of(kind: str, source: str) -> list[str]:
    """One output's source, cut where a reviewer wants to read it: a LaTeX array by its
    rows, an HTML block by its divs and by its table rows - a table is where the values
    are, and one line of three thousand characters would show a single changed cell as
    the whole table."""
    text = source.replace("\r\n", "\n")
    if kind == "Math" or "\\begin{array}" in text:
        return _latex_rows(text)
    if kind == "HTML" or text.lstrip().startswith("<"):
        return [part.strip() for part in _HTML_BREAK.split(text) if part.strip()]
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def _figure_lines(figure: matplotlib.figure.Figure) -> list[str]:
    """What EngCalc wrote on a figure. Positions are not stored: the layout that picks
    them measures text with the installed fonts."""
    figure.canvas.draw()
    axes = figure.axes[0]
    lines = [
        f"title: {axes.get_title()}",
        f"xlabel: {axes.get_xlabel()}",
        f"ylabel: {axes.get_ylabel()}",
        f"offset: {figure_text(axes.yaxis.get_offset_text().get_text())}",
    ]
    legend = axes.get_legend()
    if legend is not None:
        lines.append("legend: " + " | ".join(text.get_text() for text in legend.get_texts()))
    for text in sorted(item.get_text() for item in axes.texts if item.get_text().strip()):
        lines.append(f"annotation: {text}")
    for panel in figure.axes[1:]:
        if panel.get_gid() != _SUMMARY_GID:
            continue
        for text in panel.texts:
            if text.get_text().strip():
                lines.append(f"summary: {text.get_text()}")
    return lines


def render_page(sheet: pathlib.Path, palette: str, monkeypatch, capsys) -> str:
    """The whole page, as one document a person can read and a diff can point into."""
    captured: list = []
    monkeypatch.setattr(magic, "display", captured.append)
    magics = magic.EngMagics()
    if palette:
        magics.eng_units(palette)
    magics.eng("", sheet.read_text(encoding="utf-8"))
    printed = capsys.readouterr().out

    sections = [f"# {sheet.name}, palette: {palette or 'none'}", "", "=== console ==="]
    sections.extend(line.rstrip() for line in printed.splitlines() if line.strip())

    for index, output in enumerate(captured):
        if isinstance(output, matplotlib.figure.Figure):
            sections += ["", f"=== {index} · Figure ==="]
            sections += _figure_lines(output)
            plt.close(output)
            continue
        kind = type(output).__name__
        sections += ["", f"=== {index} · {kind} ==="]
        sections += _lines_of(kind, str(getattr(output, "data", "")))

    return "\n".join(sections) + "\n"


@pytest.mark.parametrize(
    "name, sheet, palette",
    REFERENCE_PAGES,
    ids=[name for name, _, _ in REFERENCE_PAGES],
)
def test_the_reference_page_does_not_move(name, sheet, palette, monkeypatch, capsys):
    page = render_page(sheet, palette, monkeypatch, capsys)
    stored = SNAPSHOTS / f"{name}.txt"

    if UPDATE:
        SNAPSHOTS.mkdir(exist_ok=True)
        stored.write_text(page, encoding="utf-8", newline="\n")
        return

    assert stored.exists(), (
        f"no stored page for {name}. Create it with\n"
        "    ENGCALC_UPDATE_SNAPSHOTS=1 python -m pytest "
        "tests/test_the_reference_pages_do_not_move.py\n"
        "and read it before committing."
    )
    expected = stored.read_text(encoding="utf-8").replace("\r\n", "\n")
    if page == expected:
        return

    diff = "\n".join(
        difflib.unified_diff(
            expected.splitlines(),
            page.splitlines(),
            fromfile=f"stored {name}",
            tofile=f"rendered {name}",
            lineterm="",
            n=2,
        )
    )
    pytest.fail(
        f"the {name} page moved.\n\n{diff}\n\n"
        "If you changed the renderer on purpose, read that diff - all of it, not the line "
        "you meant to change - and regenerate:\n"
        "    ENGCALC_UPDATE_SNAPSHOTS=1 python -m pytest "
        "tests/test_the_reference_pages_do_not_move.py\n"
        "If you did not, a dependency did, and that diff is the page the engineer will get.",
        pytrace=False,
    )
