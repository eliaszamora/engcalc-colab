from __future__ import annotations

import math
from html import escape

from IPython.core.magic import Magics, cell_magic, line_magic, magics_class
from IPython.display import HTML, Math, display

from .engine import EngineeringEngine
from .errors import EngCalcError
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
_NARRATIVE_STYLE = (
    "font-size:0.95rem;line-height:1.55;"
    "margin:0.36rem 0 0.60rem 0;"
)
_NARRATIVE_PARAGRAPH_STYLE = "margin:0 0 0.42rem 0;"


def _render_heading(heading: ParsedHeading) -> HTML:
    style = _HEADING_STYLE[heading.level]
    return HTML(f'<div style="{style}">{escape(heading.text)}</div>')


def _render_narrative(narrative: ParsedNarrative) -> HTML:
    paragraphs = "".join(
        f'<p style="{_NARRATIVE_PARAGRAPH_STYLE}">{escape(paragraph)}</p>'
        for paragraph in narrative.paragraphs
    )
    return HTML(f'<div style="{_NARRATIVE_STYLE}">{paragraphs}</div>')


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
        f"zero_tolerance={settings.zero_tolerance:g}"
    )


@magics_class
class EngMagics(Magics):
    def __init__(self, shell=None):
        super().__init__(shell)
        self.engine = EngineeringEngine()
        self.render_settings = RenderSettings()

    @cell_magic
    def eng(self, line: str, cell: str):
        pending_results: list[CalculationResult] = []
        try:
            for item in parse_cell(cell):
                if isinstance(item, ParsedHeading):
                    _display_equation_group(
                        pending_results,
                        self.render_settings,
                    )
                    pending_results.clear()
                    display(_render_heading(item))
                    continue

                if isinstance(item, ParsedNarrative):
                    _display_equation_group(
                        pending_results,
                        self.render_settings,
                    )
                    pending_results.clear()
                    display(_render_narrative(item))
                    continue

                result = self.engine.evaluate(item)
                if isinstance(result, PlotResult):
                    _display_equation_group(
                        pending_results,
                        self.render_settings,
                    )
                    pending_results.clear()
                    display(render_presented_plot(result))
                    continue

                if isinstance(result, TableResult):
                    _display_equation_group(
                        pending_results,
                        self.render_settings,
                    )
                    pending_results.clear()
                    display(
                        HTML(
                            render_table(
                                result,
                                settings=self.render_settings,
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
                        self.render_settings,
                    )
                    pending_results.clear()
                    display(
                        HTML(render_result(result, settings=self.render_settings))
                    )
                    continue

                if isinstance(result, CharacteristicResult):
                    _display_equation_group(
                        pending_results,
                        self.render_settings,
                    )
                    pending_results.clear()
                    display(
                        HTML(
                            render_characteristic_result(
                                result,
                                settings=self.render_settings,
                            )
                        )
                    )
                    continue

                pending_results.append(result)

            _display_equation_group(
                pending_results,
                self.render_settings,
            )
        except EngCalcError as exc:
            _display_equation_group(
                pending_results,
                self.render_settings,
            )
            print(f"engcalc: {exc}")
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

            if name == "precision":
                try:
                    value = int(raw_value)
                except ValueError:
                    print("engcalc: precision must be an integer from 0 to 10")
                    return None
                if str(value) != raw_value.strip() and raw_value.strip() not in {
                    f"+{value}",
                    f"-{abs(value)}" if value < 0 else "",
                }:
                    print("engcalc: precision must be an integer from 0 to 10")
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
                zero_tolerance=values["zero_tolerance"],
            )
        except ValueError as exc:
            print(f"engcalc: {exc}")
            return None

        print(_config_summary(self.render_settings))
        return None
