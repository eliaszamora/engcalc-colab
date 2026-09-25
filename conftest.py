"""Test-session configuration.

Pins matplotlib to a non-interactive backend before any test imports pyplot.

Without this, matplotlib picks a GUI backend, and on a Windows machine with a broken
Tcl installation the first test that draws anything fails:

    _tkinter.TclError: Can't find a usable init.tcl in the following directories: ...

Which test fails varies, because whichever plotting test runs first is the one that
decides the backend. Measured on `main` before this file existed, running
``pytest tests/test_engine.py tests/test_magic.py`` failed **4 runs out of 10**.

CI never sees it - Linux runners are headless and select Agg on their own - so the cost
is entirely local, and it is the worst kind: an intermittent failure in code that has
nothing to do with the change under test. It cost one real investigation before being
diagnosed.

An explicit ``MPLBACKEND`` is respected, so anyone who deliberately wants a GUI backend
still gets one.
"""

import os

import matplotlib

if not os.environ.get("MPLBACKEND"):
    matplotlib.use("Agg")


# --- reading a block that typesets -----------------------------------------------------
#
# The four block renderers - `table`, `governing`, the characteristic analyses and
# `summary` - are `Markdown` outputs now, and their mathematics is LaTeX inside `$...$`.
# #133 had made them plain text, on a measurement that was right about HTML (Colab
# typesets nothing inside one) and incomplete about the alternatives: a `Markdown` output
# *does* typeset, and it typesets the dollar form.
#
# So a contract that was checking *content* - "the summary says 20.00 mm" - is still
# asking the right question and can no longer find its answer by substring, because the
# answer now reads `$20.00\,\mathrm{mm}$`. `block_text` renders a block back down to what
# the reader sees, so those contracts say what they always said.
#
# It would be a bad helper if it were the only thing left, because it passes whether or
# not the page typesets - it strips the very delimiters that decide that. The contracts
# about *form* are separate and explicit, in
# `tests/test_an_html_block_typesets_after_all.py`: the block is a `Markdown` output, its
# mathematics is in `$...$`, and it carries no `<style>`. This helper answers "what does
# it say"; that file answers "does it typeset".

import re as _re

_LATEX_TEXT = {
    # `a \cdot b` with its spaces, so a unit reads `kN·m` the way the plain-text side
    # spells it - which is the whole point of #138 and of the contracts that pin it.
    r" \cdot ": "·",
    r"\cdot": "·",
    # And the same for the power of ten, whose plain-text spelling is `1.20×10⁶`.
    r" \times ": "×",
    r"\times": "×",
    r"\,": " ",
    # A relation an inequality's heading writes. `>` and `<` are already their own
    # characters; these two are not, and read as `\geq` without this.
    r"\geq": "≥",
    r"\leq": "≤",
    r"\left": "",
    r"\right": "",
    "{": "",
    "}": "",
    "$": "",
}


# The row the working puts between a row that holds a matrix and its neighbour, after the
# row break: `\\[8pt] \rule{0pt}{0.7em} \\`. See `renderer._row_break`. Not the computed
# block's own strut rows, which are followed by `\\[-4pt]` or close the array.
_SPACER_ROW = _re.compile(r"(\\\\\[[^\]]*\])\s*\\rule\{0pt\}\{0\.7em\}\s*\\\\(?!\[)")


# The line a sheet is told when it reads `N`, `m` or `s` as a unit it never wrote as one.
# See `test_a_letter_read_as_a_unit_says_so`.
_LETTER_NOTICE = _re.compile(
    r"engcalc: line \d+: '[Nms]' is read as a unit \([a-z]+\), and nothing on the sheet "
    r"writes it as one\. If it is a quantity, give it a value first \([Nms] := \.\.\.\) or "
    r"another name, such as [Nms]_1\.\n?"
)


def without_letter_notices(console: str) -> str:
    """The console with that line taken out, for a contract that uses `s` or `N` as a name
    on purpose - a sine, an axial force - and is about something else."""
    return _LETTER_NOTICE.sub("", console)


def without_spacer_rows(latex: str) -> str:
    """The working with the rows that only make room between matrices taken out.

    A reader sees no row there, and a contract that counts rows or reads the last one is
    about what the rows say, not about the room between them - which
    `test_a_matrix_row_has_room` pins on its own.
    """
    return _SPACER_ROW.sub(r"\1", latex)


def block_text(html: str) -> str:
    """One rendered block as the reader sees it: tags gone, LaTeX read back as text."""
    text = without_spacer_rows(_re.sub(r"<[^>]+>", " ", html))
    if r"\rule{0pt}{0.7em} \\[-4pt]" in text:
        text = _computed_block_text(text)
    # A characteristic block sets its formulas `$\displaystyle ...$` with `\dfrac`, so they
    # read at the page's size; both are sizes, not words.
    text = text.replace(r"$\displaystyle ", "$")
    text = _re.sub(r"\\math(?:rm|it)\{([^}]*)\}", r"\1", text)
    text = _re.sub(r"\\d?frac\{([^}]*)\}\{([^}]*)\}", r"\1/\2", text)
    text = _re.sub(r"\^\{?(-?\d+)\}?", lambda m: _superscript(m.group(1)), text)
    for latex, plain in _LATEX_TEXT.items():
        text = text.replace(latex, plain)
    return _re.sub(r"\s+", " ", text).strip()


def table_cells(latex: str) -> tuple[list[str], list[list[str]]]:
    r"""A `table(...)` block's header cells and body rows, each cell read by `block_text`.

    The table is an array now - header `\\ \hline`, rows `\\[3pt]`, cells `&` - where it
    was `<th>` and `<td>`; the contracts that read one cell at a time read these instead.
    """
    start = latex.index(r"\begin{array}{l|")
    inner = latex[latex.index("}", start + len(r"\begin{array}{")) + 1 :]
    inner = inner[: inner.index(r"\end{array}")]
    header, body = inner.split(r"\\ \hline", 1)
    body = body.replace(r"\rule{0pt}{1.4em}", "")
    read = lambda cells: [  # noqa: E731
        block_text(_computed_block_text(cell)) for cell in cells.split("&")
    ]
    return read(header), [read(row) for row in body.split(r"\\[3pt]")]


def _computed_block_text(latex: str) -> str:
    r"""A computed block - roots, extrema, `governing`, `table`, `summary` - read as its lines.

    These are `Math` outputs, so their words are `\text{}` and their rows are an array's.
    The frame, the sizes and the column separators are how it is set, not what it says;
    the rows come back one after another, the way the HTML block's lines did.
    """
    text = _re.sub(r"\\rule\{[^}]*\}\{[^}]*\}", "", latex)
    text = _re.sub(r"\\hspace\{[^}]*\}", "", text)
    text = _re.sub(r"\\begin\{array\}\{[^}]*\}|\\end\{array\}", " ", text)
    text = _re.sub(r"\\text(?:bf)?\{([^}]*)\}", r"\1", text)
    text = _re.sub(r"\\\\(?:\[-?\d+pt\])?", " ", text)
    for latex_word, plain in (
        (r"\displaystyle", ""),
        (r"\hline", ""),
        (r"\qquad", " "),
        (r"\quad", " "),
        (r"\approx", "≈"),
        ("&", " "),
    ):
        text = text.replace(latex_word, plain)
    return text


def figure_text(label: str) -> str:
    r"""One figure's label, annotation or axis offset as the reader sees it.

    A figure typesets through matplotlib's mathtext, which is the same LaTeX subset the
    page uses, so the reading is `block_text`'s with one addition: matplotlib wraps the
    numbers it writes itself in `\mathdefault{...}`, so the axis offset arrives as
    `$\times\mathdefault{10^{6}}\mathdefault{}$` and nothing in the package emitted that.

    `\mathbf` is the second: a formula is set in mathtext's own font and ignores the
    weight of the text around it, so the one label on a figure that is bold asks for its
    unit in upright *bold* rather than upright. It is the same unit, and reads the same.

    It exists for the same reason `block_text` does. A contract that asks *what the
    figure says* - "the moment axis reads kgf·cm" - is still asking the right question
    once the label typesets, and can no longer find its answer by substring. The
    contracts about *form* - that the unit is inside `$...$`, that a quotient is not
    stacked, that a bold label's unit is bold - are separate and explicit, in
    `tests/test_a_figure_typesets_like_the_page.py`.
    """
    plain = label.replace(r"\mathdefault", "").replace(r"\mathbf", r"\mathrm")
    return block_text(plain)


def _superscript(digits: str) -> str:
    return digits.translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))
