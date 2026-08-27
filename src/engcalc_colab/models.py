from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParsedStatement:
    line_no: int
    source: str
    target: str | None
    parameter: str | None
    expression: ast.Expression


@dataclass(frozen=True)
class UserFunction:
    parameter: str
    expression: Any


@dataclass(frozen=True)
class EvaluationResult:
    statement: ParsedStatement
    display_input: Any | None
    value: Any
