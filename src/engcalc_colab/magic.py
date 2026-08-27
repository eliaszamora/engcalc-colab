from __future__ import annotations

from IPython.core.magic import Magics, cell_magic, line_magic, magics_class
from IPython.display import Math, display

from .engine import EngineeringEngine
from .errors import EngCalcError
from .parser import parse_cell
from .renderer import render_result


@magics_class
class EngMagics(Magics):
    def __init__(self, shell=None):
        super().__init__(shell)
        self.engine = EngineeringEngine()

    @cell_magic
    def eng(self, line: str, cell: str):
        results = []
        try:
            for statement in parse_cell(cell):
                result = self.engine.evaluate(statement)
                results.append(result)
                display(Math(render_result(result)))
        except EngCalcError as exc:
            print(f"engcalc: {exc}")
        return None

    @line_magic
    def eng_reset(self, line: str):
        self.engine.reset()
        print("engcalc symbolic state cleared")
