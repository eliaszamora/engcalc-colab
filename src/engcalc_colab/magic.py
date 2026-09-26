from __future__ import annotations

import math
from dataclasses import replace
import re
from html import escape

from IPython.core.magic import Magics, cell_magic, line_magic, magics_class
from IPython.display import HTML, Markdown, Math, display

from . import control
from .engine import EngineeringEngine
from .errors import EngCalcError
from .reference import CATALOGUE
from .models import (
    EvaluationResult,
    NumericAssignmentResult,
    NumericEvaluationResult,
    ParsedHeading,
    ParsedNarrative,
    PartialNumericEvaluationResult,
    FramePlotResult,
    ImageResult,
    MemberResult,
    PlotResult,
    TableResult,
)
from .parser import parse_cell
from .frame_diagrams import render_frame_plot
from .presentation import render_presented_plot
from .renderer import (
    MEASURED_UNITS,
    WRITTEN_ORDER,
    WRITTEN_SUMS,
    PALETTE_NAMES,
    RenderSettings,
    palette_unit_names,
    plot_in_palette,
    quantity_as_displayed,
    render_aligned_results,
    CharacteristicResult,
    ComputedBlockResult,
    render_characteristic_result,
    render_call_help,
    render_call_index,
    render_result,
    render_table,
)
from .renderer import narrative_latex

# The letter of the mathematics, KaTeX's own - his choice, 2026-09-25: a heading in Colab's
# Google Sans stood above paragraphs and working set in KaTeX's. An HTML output keeps its
# style in Colab (a Markdown one does not); `serif` is what shows until KaTeX's letter loads.
_HEADING_LETTER = "font-family:KaTeX_Main,'Times New Roman',serif;"
_HEADING_STYLE = {
    2: (
        _HEADING_LETTER + "font-size:1.25rem;font-weight:700;"
        "margin:0.60rem 0 0.34rem 0;padding-bottom:0.14rem;"
        "border-bottom:1px solid rgba(127,127,127,0.18);"
    ),
    3: _HEADING_LETTER + "font-size:1.1rem;font-weight:700;margin:0.46rem 0 0.24rem 0;",
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


def _render_narrative(narrative: ParsedNarrative) -> Math:
    """A paragraph, typeset as the mathematics is: its words in `\\text{}`, its `$...$` as
    mathematics, in the letter and size of the working, with the room every block has.

    It was a Markdown output, because Colab typesets `$...$` there and not in an HTML one
    (#96, measured in Colab). That set it in Colab's own letter, Google Sans at 14 px beside
    KaTeX's 16.94 px, and Colab strips any style put on it - a margin, a font; measured in
    his Colab on 2026-09-25 - so it sat 5-7 px from the equations, closer than two rows of
    one block. His choice: the paragraph in the letter of the mathematics. See
    `renderer.narrative_latex` and `tests/test_one_spacing_rule.py`.
    """
    return Math(narrative_latex(narrative.paragraphs))


def _render_image(result: ImageResult) -> HTML:
    """The figure itself, embedded, so it stays in the notebook with the output."""
    import base64

    width = f"width:{result.width_cm:.2f}cm;" if result.width_cm is not None else ""
    data = base64.b64encode(result.data).decode("ascii")
    return HTML(
        f'<img src="data:{result.mime};base64,{data}" '
        f'style="{width}max-width:100%;height:auto;display:block;margin:6px 0 2px 0;">'
    )


def _figure_caption(number: int, caption: str | None) -> str:
    """`**Figura 1.** Geometría y cargas`: Markdown, so `$...$` in a caption is typeset.

    "Figura", in Spanish, is his choice (2026-09-24), over the English of the block names.
    """
    label = f"**Figura {number}.**"
    if not caption:
        return label
    return f"{label} {_narrative_paragraph_markdown(caption)}"


CalculationResult = (
    EvaluationResult
    | NumericAssignmentResult
    | NumericEvaluationResult
    | PartialNumericEvaluationResult
)


def _display_equation_group(
    results: list[CalculationResult],
    settings: RenderSettings | None = None,
    page: "_Page | None" = None,
) -> None:
    if not results:
        return
    (page.show if page is not None else display)(
        Math(render_aligned_results(results, settings=settings))
    )


# -- one rule for the room between blocks ------------------------------------------------
#
# Measured in his Colab on 2026-09-25: Colab stands every output 6-8 px from the next, the
# rows inside a block of equations are ~13 px apart, and a paragraph sat 5-7 px from the
# equations around it - closer than two rows of one block, so it read as part of its
# neighbour. Room had been given case by case: empty rows around a table and a `roots`
# block, a strut in the "Como" sentence. A Markdown output cannot carry room of its own -
# Colab strips its style - but an HTML one keeps it. So the room is one output, the same
# between any two blocks, and nothing else gives any. His choice, 2026-09-25.
#
# Its height, measured in his Colab: the gap two blocks show is the spacer's height, give or
# take a pixel (0 px left them touching). 18 px sets blocks ~1.4 times further apart than
# the rows inside one (~13 px), so each block reads as a group; before a heading the page
# opens wider on its own (34 px), with the heading's margin.
BLOCK_SPACER = '<div style="height:18px"></div>'


class _Page:
    """What a cell puts on the page, a block at a time, with the same room between any two."""

    def __init__(self) -> None:
        self.blocks = 0

    def show(self, *outputs) -> None:
        """One block - a figure and its caption are one - after the room every block has."""
        if self.blocks:
            display(HTML(BLOCK_SPACER))
        for output in outputs:
            display(output)
        self.blocks += 1


def _palette_help() -> str:
    return "available: " + ", ".join(PALETTE_NAMES) + " (or none to clear)"


def _palette_summary(name: str) -> str:
    """The units that palette fixes, read off the table rather than written twice.

    And spelled the way the page spells them. This printed Pint's *parseable* strings -
    `cm ** 2`, `kgf * cm`, `1 / s` - to a reader whose every other line says `cm²`.
    See ``palette_unit_names``.
    """
    return ", ".join(palette_unit_names(name))


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
        # The palette `%eng_units` declared, by name; "" until one is.
        self.units = ""

    def _settings(self) -> RenderSettings:
        """The page's settings, carrying the units this sheet has written so far.

        Read fresh at each use rather than once per cell: a `:=` line adds to the
        set as the cell runs, and a value rendered after it must see it.
        """
        return replace(
            self.render_settings,
            written_units=frozenset(self.engine.written_units),
            valued_names=frozenset(self.engine.numeric_context.values),
            # Which of those values carry mass, asked of Pint rather than of the name.
            # `getattr` because a stored value need not be a quantity: a sheet may settle
            # a plain number, and a direction cosine does.
            mass_carrying_names=frozenset(
                name
                for name, value in self.engine.numeric_context.values.items()
                if "[mass]" in getattr(value, "dimensionality", {})
            ),
            palette=self.units,
        )

    @cell_magic
    def eng(self, line: str, cell: str):
        # The units this sheet writes as measurements reach the printer while the cell
        # prints, so a unit alone is written with its one and a variable sharing its
        # name is not.
        token = MEASURED_UNITS.set(self.engine.measured_units)
        # And the order its products were written in, so `E*A` reads `E A`.
        order = WRITTEN_ORDER.set(self.engine.written_order)
        # And the order its sums were written in, so `theta + phi` reads `θ + φ`.
        sums = WRITTEN_SUMS.set(self.engine.written_sums)
        try:
            return self._eng_cell(cell)
        finally:
            WRITTEN_SUMS.reset(sums)
            WRITTEN_ORDER.reset(order)
            MEASURED_UNITS.reset(token)

    def _eng_cell(self, cell: str):
        pending_results: list[CalculationResult] = []
        page = _Page()
        try:
            # A cell with `%` lines decides as it goes which of its lines run; one without
            # is parsed whole and runs as it always has. See `control`.
            items = (
                control.run(cell, self.engine, self._settings)
                if control.has_control(cell)
                else parse_cell(cell)
            )
            for item in items:
                if isinstance(item, control.ConditionNote):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                        page,
                    )
                    pending_results.clear()
                    page.show(Math(item.latex))
                    continue

                if isinstance(item, ParsedHeading):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                        page,
                    )
                    pending_results.clear()
                    page.show(_render_heading(item))
                    continue

                if isinstance(item, ParsedNarrative):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                        page,
                    )
                    pending_results.clear()
                    page.show(_render_narrative(item))
                    continue

                # A `% while` hands over its last iteration already worked out.
                if isinstance(item, control.Evaluated):
                    result, notices = item.result, item.notices
                else:
                    result = self.engine.evaluate(item)
                    notices = self.engine.notices
                for notice in notices:
                    print(f"engcalc: {notice}")
                if isinstance(result, PlotResult):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                        page,
                    )
                    pending_results.clear()
                    page.show(
                        render_presented_plot(
                            plot_in_palette(result, self._settings())
                        )
                    )
                    continue

                if isinstance(result, MemberResult):
                    continue

                if isinstance(result, FramePlotResult):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                        page,
                    )
                    pending_results.clear()
                    settings = self._settings()
                    page.show(
                        render_frame_plot(
                            result,
                            lambda quantity, declared=False: quantity_as_displayed(
                                quantity, settings, declared=declared
                            ),
                        ),
                        Markdown(_figure_caption(result.number, result.caption)),
                    )
                    continue

                if isinstance(result, ImageResult):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                        page,
                    )
                    pending_results.clear()
                    page.show(
                        _render_image(result),
                        Markdown(_figure_caption(result.number, result.caption)),
                    )
                    continue

                if isinstance(result, TableResult):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                        page,
                    )
                    pending_results.clear()
                    page.show(
                        Math(
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
                if isinstance(result, ComputedBlockResult):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                        page,
                    )
                    pending_results.clear()
                    page.show(
                        Math(render_result(result, settings=self._settings()))
                    )
                    continue

                if isinstance(result, CharacteristicResult):
                    _display_equation_group(
                        pending_results,
                        self._settings(),
                        page,
                    )
                    pending_results.clear()
                    page.show(
                        Math(
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
                page,
            )
        except EngCalcError as exc:
            _display_equation_group(
                pending_results,
                self._settings(),
                page,
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
            hint = f"; ¿quisiste decir {', '.join(near)}?" if near else ""
            print(f"engcalc: no hay ayuda para '{name}'{hint}")
            print("engcalc: %eng_help sin nombre lista todo lo que se puede escribir")
            return None

        display(HTML(render_call_help(entry)))
        return None

    @line_magic
    def eng_units(self, line: str):
        """`%eng_units kN` fixes one unit per dimension for the whole sheet.

        The input stays free: `b := 500*mm` on a kN sheet is still five hundred
        millimetres and still computes as such, and reads `0.50 m`. `%eng_units` with no
        name clears it and the sheet reads as it always has.

        Where one unit per dimension is the wrong answer for a particular line - a
        deflection is a length and so is a span - `numeric(delta, mm)` shows the unit it
        is asked for, and the palette does not override it. That is the trade the
        engineer chose after seeing both pages, and the reason he gave for it is the one
        this feature rests on: the renderer cannot know which lengths are deflections.
        """
        name = line.strip()
        if not name:
            # `engcalc units:`, not `engcalc:`. The bare prefix is what this module says
            # when something went wrong - an unknown option, a token it cannot parse -
            # and `engcalc config:` and `engcalc units:` are what it says when reporting.
            # Both of these are reports and both wore the error prefix, which was found
            # by a filter looking for failures in a notebook run and finding "palette
            # cleared". A person skimming the page reads it the same way.
            if self.units:
                print(f"engcalc units: cleared (was {self.units})")
            else:
                print("engcalc units: none; " + _palette_help())
            self.units = ""
            return None

        if name not in PALETTE_NAMES:
            print(f"engcalc: unknown unit palette '{name}'; {_palette_help()}")
            return None

        self.units = name
        print(f"engcalc units: {name} — {_palette_summary(name)}")
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
