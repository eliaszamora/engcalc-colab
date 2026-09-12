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
    r"\left": "",
    r"\right": "",
    "{": "",
    "}": "",
    "$": "",
}


def block_text(html: str) -> str:
    """One rendered block as the reader sees it: tags gone, LaTeX read back as text."""
    text = _re.sub(r"<[^>]+>", " ", html)
    text = _re.sub(r"\\mathrm\{([^}]*)\}", r"\1", text)
    text = _re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", r"\1/\2", text)
    text = _re.sub(r"\^\{?(-?\d+)\}?", lambda m: _superscript(m.group(1)), text)
    for latex, plain in _LATEX_TEXT.items():
        text = text.replace(latex, plain)
    return _re.sub(r"\s+", " ", text).strip()


def _superscript(digits: str) -> str:
    return digits.translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))
