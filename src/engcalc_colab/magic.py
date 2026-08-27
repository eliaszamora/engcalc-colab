from __future__ import annotations

from html import escape

from IPython.core.magic import Magics, cell_magic, line_magic, magics_class
from IPython.display import HTML, Math, display

from .engine import EngineeringEngine
from .errors import EngCalcError
from .models import ParsedHeading
from .parser import parse_cell
from .renderer import render_result

_OUTPUT_GROUP_GAP = '<div aria-hidden="true" style="height: 0.75rem;"></div>'
_HEADING_STYLE = {
    2: "font-size:1.05rem;font-weight:600;margin:0.15rem 0 0.25rem 0;",
    3: "font-size:0.95rem;font-weight:600;margin:0.1rem 0 0.2rem 0;",
}


def _render_heading(heading: ParsedHeading) -> HTML:
    style = _HEADING_STYLE[heading.level]
    return HTML(f'<div style="{style}">{escape(heading.text)}</div>')


@magics_class
class EngMagics(Magics):
    def __init__(self, shell=None):
        super().__init__(shell)
        self.engine = EngineeringEngine()

    @cell_magic
    def eng(self, line: str, cell: str):
        results = []
        try:
            for item in parse_cell(cell):
                if item.blank_before:
                    display(HTML(_OUTPUT_GROUP_GAP))
                if isinstance(item, ParsedHeading):
                    display(_render_heading(item))
                    continue
                result = self.engine.evaluate(item)
                results.append(result)
                display(Math(render_result(result)))
        except EngCalcError as exc:
            print(f"engcalc: {exc}")
        return None

    @line_magic
    def eng_reset(self, line: str):
        self.engine.reset()
        print("engcalc symbolic state cleared")
