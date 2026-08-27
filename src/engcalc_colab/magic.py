from __future__ import annotations

from html import escape

from IPython.core.magic import Magics, cell_magic, line_magic, magics_class
from IPython.display import HTML, Math, display

from .engine import EngineeringEngine
from .errors import EngCalcError
from .models import EvaluationResult, ParsedHeading
from .parser import parse_cell
from .renderer import render_aligned_results

_HEADING_STYLE = {
    2: (
        "font-size:1.06rem;font-weight:600;"
        "margin:0.65rem 0 0.32rem 0;padding-bottom:0.18rem;"
        "border-bottom:1px solid rgba(127,127,127,0.28);"
    ),
    3: "font-size:0.95rem;font-weight:600;margin:0.45rem 0 0.18rem 0;",
}


def _render_heading(heading: ParsedHeading) -> HTML:
    style = _HEADING_STYLE[heading.level]
    return HTML(f'<div style="{style}">{escape(heading.text)}</div>')


def _display_equation_group(results: list[EvaluationResult]) -> None:
    if results:
        display(Math(render_aligned_results(results)))


@magics_class
class EngMagics(Magics):
    def __init__(self, shell=None):
        super().__init__(shell)
        self.engine = EngineeringEngine()

    @cell_magic
    def eng(self, line: str, cell: str):
        pending_results: list[EvaluationResult] = []
        try:
            for item in parse_cell(cell):
                if isinstance(item, ParsedHeading):
                    _display_equation_group(pending_results)
                    pending_results.clear()
                    display(_render_heading(item))
                    continue

                pending_results.append(self.engine.evaluate(item))

            _display_equation_group(pending_results)
        except EngCalcError as exc:
            _display_equation_group(pending_results)
            print(f"engcalc: {exc}")
        return None

    @line_magic
    def eng_reset(self, line: str):
        self.engine.reset()
        print("engcalc symbolic state cleared")
