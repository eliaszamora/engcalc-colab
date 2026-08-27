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
    blank_before: bool = False


@dataclass(frozen=True)
class ParsedNumericAssignment:
    line_no: int
    source: str
    target: str
    expression: ast.Expression
    blank_before: bool = False


@dataclass(frozen=True)
class ParsedHeading:
    line_no: int
    text: str
    level: int
    blank_before: bool = False


@dataclass(frozen=True)
class UserFunction:
    parameter: str
    expression: Any


@dataclass(frozen=True)
class EvaluationResult:
    statement: ParsedStatement
    display_input: Any | None
    value: Any


@dataclass(frozen=True)
class NumericAssignmentResult:
    statement: ParsedNumericAssignment
    quantity: Any


@dataclass(frozen=True)
class NumericEvaluationResult:
    statement: ParsedStatement
    symbolic_expression: Any
    substitutions: dict[str, Any]
    quantity: Any
    display_name: str | None = None
