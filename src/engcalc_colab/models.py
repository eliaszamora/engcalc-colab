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
    display_argument: Any | None = None


@dataclass(frozen=True)
class PartialNumericEvaluationResult:
    statement: ParsedStatement
    symbolic_expression: Any
    substitutions: dict[str, Any]
    unresolved_symbols: tuple[str, ...]
    evaluated_terms: tuple[tuple[int, Any], ...] | None = None
    display_name: str | None = None
    display_argument: Any | None = None


@dataclass(frozen=True)
class PlotSeries:
    display_label: str
    y_values: tuple[Any, ...]
    is_moment: bool


@dataclass(frozen=True)
class PlotResult:
    statement: ParsedStatement
    display_label: str
    variable: str
    x_values: tuple[Any, ...]
    series: tuple[PlotSeries, ...]
    kind: str = "plot"
    source_series: tuple[PlotSeries, ...] = ()
    source_labels: tuple[str, ...] = ()
    governing_max: tuple[int, ...] | None = None
    governing_min: tuple[int, ...] | None = None

    @property
    def y_values(self) -> tuple[Any, ...]:
        if len(self.series) != 1:
            raise AttributeError("y_values is unavailable for multi-series plots")
        return self.series[0].y_values
