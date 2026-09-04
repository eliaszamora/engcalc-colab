from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParsedMatrixLiteral:
    rows: tuple[tuple[ast.Expression, ...], ...]


@dataclass(frozen=True)
class MatrixLiteralBinding:
    name: str
    literal: ParsedMatrixLiteral


@dataclass(frozen=True)
class MatrixShape:
    rows: int
    cols: int


@dataclass(frozen=True)
class MatrixNumericGuard:
    operation: str
    source_matrix: Any


@dataclass(frozen=True)
class EigenvalueEntry:
    value: Any
    multiplicity: int


@dataclass(frozen=True)
class EigenvalueSet:
    entries: tuple[EigenvalueEntry, ...]
    source_matrix: Any


@dataclass(frozen=True)
class EigenvectorEntry:
    value: Any
    multiplicity: int
    vectors: tuple[Any, ...]


@dataclass(frozen=True)
class EigenvectorSet:
    entries: tuple[EigenvectorEntry, ...]
    source_matrix: Any


@dataclass(frozen=True)
class ParsedStatement:
    line_no: int
    source: str
    target: str | None
    parameters: tuple[str, ...] | None
    expression: ast.Expression
    blank_before: bool = False
    display_options: tuple[tuple[str, str], ...] = ()
    matrix_literals: tuple[MatrixLiteralBinding, ...] = ()
    declaration: str | None = None
    """`"case"` or `"combo"` when the line declared one; `None` for every other line."""

    @property
    def parameter(self) -> str | None:
        if self.parameters is not None and len(self.parameters) == 1:
            return self.parameters[0]
        return None

    def display_option(self, name: str) -> str | None:
        for option_name, value in self.display_options:
            if option_name == name:
                return value
        return None


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
class ParsedNarrative:
    line_no: int
    paragraphs: tuple[str, ...]
    blank_before: bool = False


@dataclass(frozen=True, init=False)
class UserFunction:
    parameters: tuple[str, ...]
    expression: Any
    derivative_variable: str | None = None
    derivative_breakpoints: tuple[Any, ...] = ()
    numeric_guards: tuple[MatrixNumericGuard, ...] = ()

    def __init__(
        self,
        parameters: tuple[str, ...] | str | None = None,
        expression: Any = None,
        derivative_variable: str | None = None,
        derivative_breakpoints: tuple[Any, ...] = (),
        numeric_guards: tuple[MatrixNumericGuard, ...] = (),
        *,
        parameter: str | None = None,
    ) -> None:
        if parameter is not None:
            if parameters is not None:
                raise TypeError("provide either parameters or parameter, not both")
            normalized = (parameter,)
        elif isinstance(parameters, str):
            normalized = (parameters,)
        elif parameters is not None:
            normalized = tuple(parameters)
        else:
            raise TypeError("UserFunction requires parameters")

        object.__setattr__(self, "parameters", normalized)
        object.__setattr__(self, "expression", expression)
        object.__setattr__(self, "derivative_variable", derivative_variable)
        object.__setattr__(self, "derivative_breakpoints", tuple(derivative_breakpoints))
        object.__setattr__(self, "numeric_guards", tuple(numeric_guards))

    @property
    def parameter(self) -> str | None:
        if len(self.parameters) == 1:
            return self.parameters[0]
        return None


@dataclass(frozen=True)
class DiscardedSolutions:
    """Answers `solve` found that `assume` ruled out.

    Carried so the sheet can show them. An engineer who is shown one answer has no
    way to know two were found, and a discard the reader cannot see is
    indistinguishable from a solver that only ever found one.
    """

    variable: str
    condition: str
    values: tuple[Any, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(self.values))
        if not self.values:
            raise ValueError("a discard record must carry the answers it ruled out")


@dataclass(frozen=True)
class EvaluationResult:
    statement: ParsedStatement
    display_input: Any | None
    value: Any
    discarded: DiscardedSolutions | None = None


@dataclass(frozen=True)
class NumericAssignmentResult:
    statement: ParsedNumericAssignment
    quantity: Any


@dataclass(frozen=True, init=False)
class NumericEvaluationResult:
    statement: ParsedStatement
    symbolic_expression: Any
    substitutions: dict[str, Any]
    quantity: Any
    display_name: str | None = None
    display_arguments: tuple[Any, ...] | None = None
    unit_literals: frozenset[str] = frozenset()

    def __init__(
        self,
        statement: ParsedStatement,
        symbolic_expression: Any,
        substitutions: dict[str, Any],
        quantity: Any,
        display_name: str | None = None,
        display_arguments: tuple[Any, ...] | None = None,
        *,
        display_argument: Any | None = None,
        unit_literals: frozenset[str] = frozenset(),
    ) -> None:
        if display_arguments is not None and display_argument is not None:
            raise TypeError("provide either display_arguments or display_argument, not both")
        normalized = (
            (display_argument,)
            if display_argument is not None
            else tuple(display_arguments) if display_arguments is not None else None
        )
        object.__setattr__(self, "statement", statement)
        object.__setattr__(self, "symbolic_expression", symbolic_expression)
        object.__setattr__(self, "substitutions", substitutions)
        object.__setattr__(self, "quantity", quantity)
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "display_arguments", normalized)
        object.__setattr__(self, "unit_literals", frozenset(unit_literals))

    @property
    def display_argument(self) -> Any | None:
        if self.display_arguments is not None and len(self.display_arguments) == 1:
            return self.display_arguments[0]
        return None


@dataclass(frozen=True)
class NumericMatrixEvaluationResult:
    statement: ParsedStatement
    symbolic_matrix: Any
    substitutions: dict[str, Any]
    quantity_matrix: Any
    display_name: str | None = None
    display_arguments: tuple[Any, ...] | None = None


@dataclass(frozen=True)
class PartialMatrixNumericEvaluationResult:
    statement: ParsedStatement
    symbolic_matrix: Any
    substitutions: dict[str, Any]
    unresolved_symbols: tuple[str, ...]
    display_name: str | None = None
    display_arguments: tuple[Any, ...] | None = None


@dataclass(frozen=True)
class PiecewisePartialBranch:
    value: Any
    operator: str | None
    breakpoint: Any | None
    evaluated_terms: tuple[tuple[int, Any], ...] | None = None


@dataclass(frozen=True)
class PiecewisePartialEvaluation:
    interval_variable: str
    branches: tuple[PiecewisePartialBranch, ...]


@dataclass(frozen=True, init=False)
class PartialNumericEvaluationResult:
    statement: ParsedStatement
    symbolic_expression: Any
    substitutions: dict[str, Any]
    unresolved_symbols: tuple[str, ...]
    evaluated_terms: tuple[tuple[int, Any], ...] | None = None
    display_name: str | None = None
    display_arguments: tuple[Any, ...] | None = None
    piecewise_evaluation: PiecewisePartialEvaluation | None = None
    unit_literals: frozenset[str] = frozenset()

    def __init__(
        self,
        statement: ParsedStatement,
        symbolic_expression: Any,
        substitutions: dict[str, Any],
        unresolved_symbols: tuple[str, ...],
        evaluated_terms: tuple[tuple[int, Any], ...] | None = None,
        display_name: str | None = None,
        display_arguments: tuple[Any, ...] | None = None,
        piecewise_evaluation: PiecewisePartialEvaluation | None = None,
        *,
        display_argument: Any | None = None,
        unit_literals: frozenset[str] = frozenset(),
    ) -> None:
        if display_arguments is not None and display_argument is not None:
            raise TypeError("provide either display_arguments or display_argument, not both")
        normalized = (
            (display_argument,)
            if display_argument is not None
            else tuple(display_arguments) if display_arguments is not None else None
        )
        object.__setattr__(self, "statement", statement)
        object.__setattr__(self, "symbolic_expression", symbolic_expression)
        object.__setattr__(self, "substitutions", substitutions)
        object.__setattr__(self, "unresolved_symbols", tuple(unresolved_symbols))
        object.__setattr__(self, "evaluated_terms", evaluated_terms)
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "display_arguments", normalized)
        object.__setattr__(self, "piecewise_evaluation", piecewise_evaluation)
        object.__setattr__(self, "unit_literals", frozenset(unit_literals))

    @property
    def display_argument(self) -> Any | None:
        if self.display_arguments is not None and len(self.display_arguments) == 1:
            return self.display_arguments[0]
        return None


_CHARACTERISTIC_PROVENANCE = {"exact", "numeric"}
_CHARACTERISTIC_SIDES = {"at", "left", "right"}


@dataclass(frozen=True)
class CharacteristicPoint:
    x_symbolic: Any
    x_quantity: Any
    value_symbolic: Any | None
    value_quantity: Any | None
    provenance: str
    side: str = "at"
    roles: tuple[str, ...] = ()
    source_label: str | None = None

    def __post_init__(self) -> None:
        if self.provenance not in _CHARACTERISTIC_PROVENANCE:
            raise ValueError("characteristic provenance must be 'exact' or 'numeric'")
        if self.side not in _CHARACTERISTIC_SIDES:
            raise ValueError("characteristic side must be 'at', 'left' or 'right'")
        object.__setattr__(self, "roles", tuple(self.roles))


@dataclass(frozen=True)
class CharacteristicInterval:
    lower_symbolic: Any
    upper_symbolic: Any
    lower_quantity: Any
    upper_quantity: Any
    role: str
    provenance: str = "exact"
    value_symbolic: Any | None = None
    value_quantity: Any | None = None
    lower_closed: bool = True
    upper_closed: bool = True

    def __post_init__(self) -> None:
        if self.provenance not in _CHARACTERISTIC_PROVENANCE:
            raise ValueError("characteristic provenance must be 'exact' or 'numeric'")
        if not isinstance(self.lower_closed, bool) or not isinstance(self.upper_closed, bool):
            raise ValueError("characteristic interval closure flags must be boolean")


@dataclass(frozen=True)
class SummaryResult:
    statement: ParsedStatement
    entries: tuple[tuple[str, Any], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))
        if not self.entries:
            raise ValueError("a summary must carry at least one reported value")


@dataclass(frozen=True)
class GoverningInterval:
    lower_quantity: Any
    upper_quantity: Any
    label: str


@dataclass(frozen=True)
class GoverningResult:
    statement: ParsedStatement
    variable: str
    labels: tuple[str, ...]
    intervals: tuple[GoverningInterval, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "labels", tuple(self.labels))
        object.__setattr__(self, "intervals", tuple(self.intervals))
        if not self.intervals:
            raise ValueError("a governing result must cover the domain")


@dataclass(frozen=True)
class AssumptionResult:
    """``assume(L > 0, E > 0)``: what the engineer states before using the symbols."""

    statement: ParsedStatement
    assumptions: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "assumptions", tuple(self.assumptions))
        if not self.assumptions:
            raise ValueError("an assumption result must carry at least one assumption")


@dataclass(frozen=True)
class SystemSolveResult:
    """`solve(eq_1, ..., eq_n, x_1, ..., x_n)`.

    The unknowns come back labelled rather than positional, which is what every
    established system does and what makes a silent swap impossible.
    """

    statement: ParsedStatement
    equations: tuple[Any, ...]
    solutions: tuple[tuple[str, Any], ...]
    discarded: DiscardedSolutions | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "equations", tuple(self.equations))
        object.__setattr__(self, "solutions", tuple(self.solutions))
        if not self.solutions:
            raise ValueError("a system solve result must carry at least one unknown")


@dataclass(frozen=True)
class RootsResult:
    statement: ParsedStatement
    display_label: str
    variable: str
    lower_quantity: Any
    upper_quantity: Any
    points: tuple[CharacteristicPoint, ...]
    intervals: tuple[CharacteristicInterval, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "points", tuple(self.points))
        object.__setattr__(self, "intervals", tuple(self.intervals))


@dataclass(frozen=True)
class LoadCombinationResult:
    """`combo U1 = 1.2*D + 1.6*L`, shown with its factors rather than multiplied out.

    Written as an ordinary definition, `U1(x) = 1.2*D(x) + 1.6*Lv(x)` renders as
    `0.6*qD*x*(L - x) + 0.8*qL*x*(L - x)`: mathematically the same and no longer a load
    combination. The reader cannot check 1.2 and 1.6 against the code that requires
    them, because the page no longer contains them.

    So the combination keeps the terms as written, and the expanded expression lives
    beside them for everything else to use.
    """

    statement: ParsedStatement
    name: str
    variable: str
    terms: tuple[tuple[Any, str], ...]
    expression: Any

    def __post_init__(self) -> None:
        object.__setattr__(self, "terms", tuple(self.terms))
        if not self.terms:
            raise ValueError("a load combination must carry at least one case")


@dataclass(frozen=True)
class LoadCaseResult:
    """`case D = M_D(x)` - a named load case, ready to be combined."""

    statement: ParsedStatement
    name: str
    variable: str
    expression: Any


@dataclass(frozen=True)
class InequalityResult:
    """`solve(M(x) > 20*kN*m, x, 0, L)` - where on the beam the moment exceeds a value.

    The answer to an inequality is a region, not a point, so this carries intervals and
    no points. It keeps the shape of the other characteristics because it is one: the
    boundaries are the roots of `lhs - rhs`, found by the same machinery.

    The domain is not ceremony borrowed from `roots`. It is where the variable gets its
    unit, and an answer of "between 0.76 and 5.24" with no unit is not an engineering
    answer.
    """

    statement: ParsedStatement
    display_label: str
    variable: str
    relation: str
    lower_quantity: Any
    upper_quantity: Any
    intervals: tuple[CharacteristicInterval, ...] = ()
    points: tuple[CharacteristicPoint, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "intervals", tuple(self.intervals))
        object.__setattr__(self, "points", tuple(self.points))


@dataclass(frozen=True)
class IntersectionsResult:
    statement: ParsedStatement
    left_label: str
    right_label: str
    variable: str
    lower_quantity: Any
    upper_quantity: Any
    points: tuple[CharacteristicPoint, ...]
    intervals: tuple[CharacteristicInterval, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "points", tuple(self.points))
        object.__setattr__(self, "intervals", tuple(self.intervals))


@dataclass(frozen=True)
class ExtremaResult:
    statement: ParsedStatement
    display_label: str
    variable: str
    lower_quantity: Any
    upper_quantity: Any
    points: tuple[CharacteristicPoint, ...]
    intervals: tuple[CharacteristicInterval, ...] = ()
    unbounded_above: bool = False
    unbounded_below: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "points", tuple(self.points))
        object.__setattr__(self, "intervals", tuple(self.intervals))


@dataclass(frozen=True)
class PlotSeries:
    display_label: str
    y_values: tuple[Any, ...]
    is_moment: bool
    segment_starts: tuple[int, ...] = ()
    characteristics: tuple[CharacteristicPoint, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "y_values", tuple(self.y_values))
        object.__setattr__(self, "segment_starts", tuple(self.segment_starts))
        object.__setattr__(self, "characteristics", tuple(self.characteristics))


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
    envelope_mode: str | None = None
    governing_signed: tuple[Any, ...] | None = None

    @property
    def y_values(self) -> tuple[Any, ...]:
        if len(self.series) != 1:
            raise AttributeError("y_values is unavailable for multi-series plots")
        return self.series[0].y_values

    @property
    def title(self) -> str | None:
        return self.statement.display_option("title")

    @property
    def xlabel(self) -> str | None:
        return self.statement.display_option("xlabel")

    @property
    def ylabel(self) -> str | None:
        return self.statement.display_option("ylabel")


@dataclass(frozen=True)
class TableColumn:
    display_label: str
    unit: Any
    values: tuple[Any, ...]


@dataclass(frozen=True)
class TableResult:
    statement: ParsedStatement
    variable: str
    point_unit: Any
    point_values: tuple[Any, ...]
    columns: tuple[TableColumn, ...]
    mode: str

    def __post_init__(self) -> None:
        if self.mode not in {"uniform", "explicit"}:
            raise ValueError("table mode must be 'uniform' or 'explicit'")