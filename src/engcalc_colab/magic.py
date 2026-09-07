from __future__ import annotations

import math
from dataclasses import replace
import re
from html import escape

from IPython.core.magic import Magics, cell_magic, line_magic, magics_class
from IPython.display import HTML, Markdown, Math, display

from .engine import EngineeringEngine
from .errors import EngCalcError
from .reference import CATALOGUE
from .models import (
    EvaluationResult,
    ExtremaResult,
    IntersectionsResult,
    NumericAssignmentResult,
    NumericEvaluationResult,
    ParsedHeading,
    ParsedNarrative,
    PartialNumericEvaluationResult,
    PlotResult,
    RootsResult,
    TableResult,
)
from .parser import parse_cell
from .presentation import render_presented_plot
from .renderer import (
    RenderSettings,
    render_aligned_results,
    CharacteristicResult,
    HtmlBlockResult,
    render_characteristic_result,
    render_call_help,
    render_call_index,
    render_result,
    render_table,
)

_HEADING_STYLE = {
    2: (
        "font-size:1.06rem;font-weight:600;"
        "margin:0.60rem 0 0.34rem 0;padding-bottom:0.14rem;"
        "border-bottom:1px solid rgba(127,127,127,0.18);"
    ),
    3: "font-size:0.95rem;font-weight:600;margin:0.46rem 0 0.24rem 0;",
}
# A narrative used to carry its own font size and margins, in a styled `<div>`. It does
# not any more: a markdown output takes the notebook's paragraph styling, and the
# alternative - raw HTML inside the markdown - is the thing that stopped the mathematics
# typesetting in the first place. The spacing was a nicety; the relations are the page.


def _render_heading(heading: ParsedHeading) -> HTML:
    style = _HEADING_STYLE[heading.level]
    return HTML(f'<div style="{style}">{escape(heading.text)}</div>')


# `$...$` inside a narrative paragraph is mathematics, the way a Colab markdown cell
# already reads it. A span qualifies only when its content neither begins nor ends with a
# space, which is the whole of what keeps prose safe: `cuesta $5 y $10` has a candidate
# span of `5 y `, and it ends with one.
#
# The relations a memoria explains have nowhere else to live. Written as statements the
# free symbols commute - `A_e = R_e*L_e*T` renders `L_e R_e T`, with the factors
# reordered - and for matrices the order is the mathematics, so the page would be stating
# something false. `transpose` on a symbol does not render at all.
_NARRATIVE_MATH = re.compile(r"\$(\S|\S[^$]*?\S)\$")


# Prose is markdown now, so what markdown would eat has to be escaped. Measured on this
# repository's own benchmark rather than guessed: its narrative carries seven underscores
# outside the formulas, in `L_e`, `R_e`, `A_e`, `theta_1` and `theta_4`, and markdown
# reads the span between two of them as emphasis - "la cadena T, L_e, R_e" would print
# with "e, R" in italics and the underscores gone.
#
# `<`, `>` and `&` go as entities rather than as backslash escapes, because markdown
# passes raw HTML straight through and the old HTML path escaped them. Losing that while
# fixing a rendering defect would have traded a formula that does not typeset for a
# paragraph that can inject markup, which is a worse page and a worse bargain. Entities
# survive markdown and render as the characters they name.
#
# `[` is an entity too, and for a different reason: `\[` is MathJax's *default* display
# delimiter. Escaping a bracket the markdown way would turn `el vector U [doce
# componentes]` into `\[doce componentes\]`, and the notebook lifts its mathematics out
# before the markdown converter runs, so that pair reaches MathJax intact and the prose
# becomes a centred formula. `&#91;` never looks like a delimiter. `]` needs no escape at
# all once `[` cannot open a link - it was in this set until a mutant removed it and
# every contract still passed, which was the right answer to a question about `]` and
# the wrong answer about `[`.
_MARKDOWN_ESCAPES = str.maketrans(
    {"&": "&amp;", "<": "&lt;", ">": "&gt;", "[": "&#91;"}
    | {character: "\\" + character for character in "\\`*_#$"}
)


# A paragraph that opens with a list marker becomes a list item, and an ordered one is
# *renumbered*: two paragraphs opening "3." and "5." print as 3 and 4. A number in a
# memoria changing on its way to the page is the worst thing markdown can do here, and it
# is worse than the underscore because nothing looks wrong - it looks like a tidy list.
#
# Found by rendering the verification cell written to check the underscores, which opened
# its own points "1.", "2.", "3." and came back as an ordered list.
#
# The marker has to be followed by a space to be one, which is what keeps `3.7 m es la
# altura libre` a sentence. `*` needs nothing here; it is escaped everywhere already.
_LIST_MARKER = re.compile(r"^([-+]|\d{1,9}[.)])(?=\s|$)")


def _escape_list_marker(paragraph: str) -> str:
    match = _LIST_MARKER.match(paragraph)
    if match is None:
        return paragraph
    marker = match.group(1)
    if marker[0].isdigit():
        # `1\.` keeps the digit and disarms the marker; `\1.` would print a backslash.
        return marker[:-1] + "\\" + marker[-1] + paragraph[len(marker):]
    return "\\" + paragraph


def _narrative_paragraph_markdown(paragraph: str) -> str:
    """Escape the prose and leave the marked spans as `$...$` for MathJax.

    The mathematics is *not* escaped: it is LaTeX and MathJax has to read it whole, and
    `$a < b$` needs its `<`. Everything around it is, the `$` of a price included -
    `cuesta $5 el kilo y $10 el metro` typesets as one formula otherwise, which is what
    Colab does with it.
    """
    parts: list[str] = []
    index = 0
    for match in _NARRATIVE_MATH.finditer(paragraph):
        parts.append(paragraph[index:match.start()].translate(_MARKDOWN_ESCAPES))
        parts.append("$" + match.group(1) + "$")
        index = match.end()
    parts.append(paragraph[index:].translate(_MARKDOWN_ESCAPES))
    return _escape_list_marker("".join(parts))


def _render_narrative(narrative: ParsedNarrative) -> Markdown:
    """Markdown, not HTML, because Colab does not typeset a `display(HTML(...))` at all.

    #96 made a narrative's marked spans reach the page as MathJax's parenthesis
    delimiters, and it was verified against a rendering harness this repository writes -
    which configures MathJax with exactly those delimiters, so it could not have failed.
    In Colab the relations came out as raw text, across a memoria that explains a matrix
    formulation and has nowhere else to put them.

    Measured in Colab rather than reasoned about, and the answer was not a delimiter. Of
    the parenthesis form, the dollar form, the bracket form and an explicit
    `MathJax.typeset()` call, *none* renders inside an HTML output; Colab isolates it.
    `Markdown`, `Latex` and `Math` outputs all typeset. Markdown is the one that keeps
    prose as prose rather than wrapping every sentence in `\\text{}`.

    The cost is the paragraph styling this used to set, which a markdown output does not
    take. Correctness over cosmetics: a relation that does not render is a memoria that
    does not say what it means.
    """
    return Markdown(
        "\n\n".join(
            _narrative_paragraph_markdown(paragraph)
            for paragraph in narrative.paragraphs
        )
    )


CalculationResult = (
    EvaluationResult
    | NumericAssignmentResult
    | NumericEvaluationResult
    | PartialNumericEvaluationResult
)


def _display_equation_group(
    results: list[CalculationResult],
    settings: RenderSettings | None = None,
) -> None:
    if not results:
        return
    display(Math(render_aligned_results(results, settings=settings)))


def _config_summary(settings: RenderSettings) -> str:
    return (
        "engcalc config: "
        f"precision={settings.precision} "
        f"figures={settings.figures} "
        f"zero_tolerance={settings.zero_tolerance:g}"
    )


@magics_class
class EngMagics(Magics):
    def __init__(self, shell=None):
        super().__init__(shell)
        self.engine = EngineeringEngine()
        self.render_settings = RenderSettings()

    def _settings(self) -> RenderSettings:
        """The page's settings, carrying the units this sheet has written so far.

        Read fresh at each use rather than once per cell: a `:=` line adds to the
        set as the cell runs, and a value rendered after it must see it.
        """
        return replace(
            self.render_settings,
            written_units=frozenset(self.engine.written_units),
        )

    @cell_magic
    def eng(self, line: str, cell: str):
        pending_results: list[CalculationResult] = []
        try:
            for item in parse_cell(cell):
                if isinstance(item, ParsedHeading):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                    )
                    pending_results.clear()
                    display(_render_heading(item))
                    continue

                if isinstance(item, ParsedNarrative):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                    )
                    pending_results.clear()
                    display(_render_narrative(item))
                    continue

                result = self.engine.evaluate(item)
                if isinstance(result, PlotResult):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                    )
                    pending_results.clear()
                    display(render_presented_plot(result))
                    continue

                if isinstance(result, TableResult):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                    )
                    pending_results.clear()
                    display(
                        HTML(
                            render_table(
                                result,
                                settings=self._settings(),
                            )
                        )
                    )
                    continue

                # The union from the renderer, not a tuple written out here. This
                # listed three types by hand and InequalityResult was added to the
                # renderer without reaching it, so a `solve(M(x) > ..., x, 0, L)` cell
                # raised AttributeError in the notebook while every contract passed:
                # they called render_characteristic_result directly and never asked
                # whether the magic would route anything to it.
                if isinstance(result, HtmlBlockResult):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                    )
                    pending_results.clear()
                    display(
                        HTML(render_result(result, settings=self._settings()))
                    )
                    continue

                if isinstance(result, CharacteristicResult):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                    )
                    pending_results.clear()
                    display(
                        HTML(
                            render_characteristic_result(
                                result,
                                settings=self._settings(),
                            )
                        )
                    )
                    continue

                pending_results.append(result)

            _display_equation_group(
                pending_results,
                self._settings(),
            )
        except EngCalcError as exc:
            _display_equation_group(
                pending_results,
                self._settings(),
            )
            print(f"engcalc: {exc}")
        return None

    @line_magic
    def eng_help(self, line: str):
        """`%eng_help` lists the calls; `%eng_help integrate` explains one.

        A notebook cannot help with this language on its own: `Shift+Tab` reads a Python
        object's signature, and `integrate` inside `%%eng` is a name in a restricted
        grammar rather than a function object. So the help is a line magic, beside
        `%eng_reset` and `%eng_config`.
        """
        name = line.strip()
        if not name:
            ordered = sorted(CATALOGUE.values(), key=lambda entry: entry.name)
            display(HTML(render_call_index(ordered)))
            return None

        entry = CATALOGUE.get(name)
        if entry is None:
            near = sorted(other for other in CATALOGUE if other.startswith(name[:2]))
            hint = f"; did you mean {', '.join(near)}?" if near else ""
            print(f"engcalc: no help for '{name}'{hint}")
            print("engcalc: %eng_help with no name lists every call")
            return None

        display(HTML(render_call_help(entry)))
        return None

    @line_magic
    def eng_reset(self, line: str):
        self.engine.reset()
        print("engcalc state cleared")

    @line_magic
    def eng_config(self, line: str):
        text = line.strip()
        if not text:
            print(_config_summary(self.render_settings))
            return None

        values = {
            "precision": self.render_settings.precision,
            "figures": self.render_settings.figures,
            "zero_tolerance": self.render_settings.zero_tolerance,
        }

        for token in text.split():
            if "=" not in token:
                print(f"engcalc: invalid config token '{token}'; expected name=value")
                return None

            name, raw_value = token.split("=", 1)
            if name not in values:
                print(f"engcalc: unknown option '{name}'")
                return None

            if name in ("precision", "figures"):
                try:
                    value = int(raw_value)
                except ValueError:
                    print(f"engcalc: {name} must be an integer from 0 to 10")
                    return None
                if str(value) != raw_value.strip() and raw_value.strip() not in {
                    f"+{value}",
                    f"-{abs(value)}" if value < 0 else "",
                }:
                    print(f"engcalc: {name} must be an integer from 0 to 10")
                    return None
                values[name] = value
                continue

            try:
                value = float(raw_value)
            except ValueError:
                print("engcalc: zero_tolerance must be a finite non-negative number")
                return None
            if not math.isfinite(value) or value < 0:
                print("engcalc: zero_tolerance must be a finite non-negative number")
                return None
            values[name] = value

        try:
            self.render_settings = RenderSettings(
                precision=values["precision"],
                figures=values["figures"],
                zero_tolerance=values["zero_tolerance"],
            )
        except ValueError as exc:
            print(f"engcalc: {exc}")
            return None

        print(_config_summary(self.render_settings))
        return None
