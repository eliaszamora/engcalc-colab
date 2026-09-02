from __future__ import annotations

import ast
import re
from dataclasses import dataclass, replace

import sympy as sp
from pint.errors import DimensionalityError

from .characteristics import (
    normalize_analysis_domain,
    solve_extrema_exact,
    solve_intersections_exact,
    solve_roots_exact,
)
from .errors import (
    AmbiguousSolveError,
    EngCalcError,
    EngEvaluationError,
    EngSyntaxError,
    diagnostic_hint,
)
from .models import (
    CharacteristicPoint,
    EigenvalueEntry,
    EigenvalueSet,
    EigenvectorEntry,
    EigenvectorSet,
    EvaluationResult,
    ExtremaResult,
    IntersectionsResult,
    MatrixNumericGuard,
    NumericAssignmentResult,
    NumericEvaluationResult,
    NumericMatrixEvaluationResult,
    PartialMatrixNumericEvaluationResult,
    MatrixShape,
    ParsedNumericAssignment,
    ParsedStatement,
    PartialNumericEvaluationResult,
    PlotResult,
    PlotSeries,
    AssumptionResult,
    GoverningInterval,
    GoverningResult,
    RootsResult,
    SystemSolveResult,
    TableColumn,
    TableResult,
    UserFunction,
)
from .matrix_core import (
    build_matrix,
    is_matrix,
    map_matrix_entries,
    matrix_add,
    matrix_det,
    matrix_diag,
    matrix_identity,
    matrix_index,
    matrix_inv,
    matrix_multiply,
    matrix_power,
    matrix_scalar_divide,
    matrix_size,
    matrix_subtract,
    matrix_trace,
    matrix_transpose,
    matrix_zeros,
)
from .matrix_analysis import (
    matrix_eigenvals,
    matrix_eigenvects,
    matrix_norm,
    matrix_rank,
    matrix_rref,
)
from .matrix_numeric import ensure_common_scale
from .matrix_solve import solve_linear_system
from .numeric import NumericContext
from .piecewise import build_piecewise, build_relation, extract_symbolic_breakpoints
from .tables import normalize_explicit_points, normalize_uniform_points


_SCALAR_SYMBOLIC_FUNCTIONS = {
    "sqrt": sp.sqrt,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "exp": sp.exp,
    "log": sp.log,
}

_INVERSE_TRIG_SYMBOLIC_FUNCTIONS = {sp.asin, sp.acos, sp.atan}


def _substitute_preserving_inverse_trig(expr, bindings):
    expr = sp.sympify(expr)
    if isinstance(expr, sp.Symbol) and expr in bindings:
        return bindings[expr]
    if not expr.free_symbols.intersection(bindings):
        return expr

    rebuilt_args = tuple(
        _substitute_preserving_inverse_trig(arg, bindings)
        for arg in expr.args
    )
    if expr.func in _INVERSE_TRIG_SYMBOLIC_FUNCTIONS:
        return expr.func(*rebuilt_args, evaluate=False)
    return expr.func(*rebuilt_args)


def substitute_symbolic_value(value, bindings):
    """Substitute one scalar or immutable matrix while preserving scalar CAS semantics."""
    if is_matrix(value):
        return map_matrix_entries(
            value,
            lambda entry: substitute_symbolic_value(entry, bindings),
        )

    expression = sp.sympify(value)
    if any(
        item.func in _INVERSE_TRIG_SYMBOLIC_FUNCTIONS
        for item in sp.preorder_traversal(expression)
    ):
        return _substitute_preserving_inverse_trig(expression, bindings)
    return expression.xreplace(bindings)

_MOMENT_LABEL = re.compile(r"^M(?:_[A-Za-z0-9]+|[0-9]+)?\(")


@dataclass(frozen=True)
class _ResolvedExpression:
    source_label: str
    display_label: str
    signed_expression: object
    comparison_expression: object
    is_absolute: bool


@dataclass(frozen=True)
class _ResolvedResponseSeries:
    display_label: str
    variable: str
    x_values: tuple
    series: tuple[PlotSeries, ...]
    source_series: tuple[PlotSeries, ...]
    source_labels: tuple[str, ...]
    first_symbolic_expression: object
    envelope_mode: str | None = None


@dataclass(frozen=True)
class _PlotEvaluation:
    display_label: str
    variable: str
    x_values: tuple
    series: tuple[PlotSeries, ...]
    kind: str = "plot"
    source_series: tuple[PlotSeries, ...] = ()
    source_labels: tuple[str, ...] = ()
    governing_max: tuple[int, ...] | None = None
    governing_min: tuple[int, ...] | None = None
    envelope_mode: str | None = None
    governing_signed: tuple | None = None


@dataclass(frozen=True)
class _TableEvaluation:
    variable: str
    point_unit: object
    point_values: tuple
    columns: tuple[TableColumn, ...]
    mode: str
    first_symbolic_expression: object


@dataclass(frozen=True)
class _SystemSolveEvaluation:
    """A solved scalar system, carried out of the evaluator like plots and tables.

    ``kind`` separates the two cases that share this carrier. A ``system`` has one
    answer per unknown and defines them. A ``multi`` has several answers for a single
    unknown, so there is nothing to define - the reader picks.
    """

    equations: tuple
    solutions: tuple
    kind: str = "system"


@dataclass(frozen=True)
class _CharacteristicEvaluation:
    kind: str
    variable: str
    lower_quantity: object
    upper_quantity: object
    points: tuple
    intervals: tuple
    first_symbolic_expression: object
    display_label: str | None = None
    left_label: str | None = None
    right_label: str | None = None
    unbounded_above: bool = False
    unbounded_below: bool = False


class EngineeringEngine:
    def __init__(self) -> None:
        self.namespace: dict[str, object] = {}
        self.functions: dict[str, UserFunction] = {}
        self.symbols: dict[str, sp.Symbol] = {}
        # What the engineer has stated about a symbol before using it, as SymPy keyword
        # assumptions. Applied in resolve_symbol.
        self.assumptions: dict[str, dict[str, bool]] = {}
        self.numeric_guards: dict[str, tuple[MatrixNumericGuard, ...]] = {}
        self.numeric_context = NumericContext()
        # Shared by reference, so a name defined symbolically later is visible when a
        # numeric evaluation needs it. See NumericContext._resolve_symbolic_names.
        self.numeric_context.symbolic_namespace = self.namespace

    def reset(self) -> None:
        self.namespace.clear()
        self.functions.clear()
        self.symbols.clear()
        self.numeric_guards.clear()
        self.numeric_context.reset()

    def resolve_symbol(self, name: str) -> sp.Symbol:
        if name not in self.symbols:
            # Assumptions are baked in at creation because a SymPy symbol carries them
            # in its identity: Symbol('L', real=True) and Symbol('L', positive=True) are
            # different symbols. That is also why `assume` refuses a name already here.
            self.symbols[name] = sp.Symbol(
                name, real=True, **self.assumptions.get(name, {})
            )
        return self.symbols[name]

    def resolve_name(self, name: str):
        if name in self.namespace:
            return self.namespace[name]
        return self.resolve_symbol(name)

    def evaluate(
        self,
        statement: ParsedStatement | ParsedNumericAssignment,
    ) -> (
        EvaluationResult
        | NumericAssignmentResult
        | NumericEvaluationResult
        | NumericMatrixEvaluationResult
        | PartialNumericEvaluationResult
        | PartialMatrixNumericEvaluationResult
        | PlotResult
        | TableResult
        | RootsResult
        | IntersectionsResult
        | ExtremaResult
    ):
        evaluator = _Evaluator(self, getattr(statement, "matrix_literals", ()))
        try:
            if isinstance(statement, ParsedNumericAssignment):
                quantity = self.numeric_context.assign(
                    statement.target,
                    statement.expression,
                )
                return NumericAssignmentResult(
                    statement=statement,
                    quantity=quantity,
                )

            if statement.target is not None:
                if statement.parameters is None and statement.target in self.functions:
                    raise EngEvaluationError(
                        f"redefinition conflict: '{statement.target}' is already a function"
                    )
                if statement.parameters is not None and statement.target in self.namespace:
                    raise EngEvaluationError(
                        f"redefinition conflict: '{statement.target}' is already a scalar"
                    )

            if statement.parameters is not None:
                value = evaluator.visit_function_body(
                    statement.expression.body,
                    statement.parameters,
                )
            else:
                value = evaluator.visit(statement.expression.body)

            if evaluator.plot_evaluation is not None:
                plot_evaluation = evaluator.plot_evaluation
                if statement.target is not None:
                    raise EngEvaluationError(
                        f"{plot_evaluation.kind} must be a standalone statement"
                    )
                return PlotResult(
                    statement=statement,
                    display_label=plot_evaluation.display_label,
                    variable=plot_evaluation.variable,
                    x_values=plot_evaluation.x_values,
                    series=plot_evaluation.series,
                    kind=plot_evaluation.kind,
                    source_series=plot_evaluation.source_series,
                    source_labels=plot_evaluation.source_labels,
                    governing_max=plot_evaluation.governing_max,
                    governing_min=plot_evaluation.governing_min,
                    envelope_mode=plot_evaluation.envelope_mode,
                    governing_signed=plot_evaluation.governing_signed,
                )

            if evaluator.governing_evaluation is not None:
                variable, labels, intervals = evaluator.governing_evaluation
                if statement.target is not None:
                    raise EngEvaluationError(
                        "governing must be a standalone statement"
                    )
                return GoverningResult(
                    statement=statement,
                    variable=variable,
                    labels=labels,
                    intervals=intervals,
                )

            if evaluator.assume_evaluation is not None:
                if statement.target is not None:
                    raise EngEvaluationError(
                        "assume must be a standalone statement; it states what is known "
                        "rather than producing a value"
                    )
                return AssumptionResult(
                    statement=statement,
                    assumptions=evaluator.assume_evaluation,
                )

            if evaluator.system_evaluation is not None:
                system = evaluator.system_evaluation
                if statement.target is not None:
                    if system.kind == "multi":
                        raise EngEvaluationError(
                            f"solve returned {len(system.solutions)} solutions, so there "
                            "is no single value to assign. Read them, or use "
                            "roots(expression, variable, lower, upper) to take the one "
                            "inside a physical domain"
                        )
                    raise EngEvaluationError(
                        "solve of a system must be a standalone statement; the unknowns "
                        "are the result and are defined by it"
                    )
                if system.kind == "system":
                    for name, value in system.solutions:
                        self.namespace[name] = value
                return SystemSolveResult(
                    statement=statement,
                    equations=system.equations,
                    solutions=system.solutions,
                )

            if evaluator.table_evaluation is not None:
                table_evaluation = evaluator.table_evaluation
                if statement.target is not None:
                    raise EngEvaluationError("table must be a standalone statement")
                return TableResult(
                    statement=statement,
                    variable=table_evaluation.variable,
                    point_unit=table_evaluation.point_unit,
                    point_values=table_evaluation.point_values,
                    columns=table_evaluation.columns,
                    mode=table_evaluation.mode,
                )

            if evaluator.characteristic_evaluation is not None:
                characteristic = evaluator.characteristic_evaluation
                if statement.target is not None:
                    raise EngEvaluationError(
                        f"{characteristic.kind} must be a standalone statement"
                    )
                if characteristic.kind == "roots":
                    return RootsResult(
                        statement=statement,
                        display_label=characteristic.display_label or "response",
                        variable=characteristic.variable,
                        lower_quantity=characteristic.lower_quantity,
                        upper_quantity=characteristic.upper_quantity,
                        points=characteristic.points,
                        intervals=characteristic.intervals,
                    )
                if characteristic.kind == "intersections":
                    return IntersectionsResult(
                        statement=statement,
                        left_label=characteristic.left_label or "left",
                        right_label=characteristic.right_label or "right",
                        variable=characteristic.variable,
                        lower_quantity=characteristic.lower_quantity,
                        upper_quantity=characteristic.upper_quantity,
                        points=characteristic.points,
                        intervals=characteristic.intervals,
                    )
                if characteristic.kind == "extrema":
                    return ExtremaResult(
                        statement=statement,
                        display_label=characteristic.display_label or "response",
                        variable=characteristic.variable,
                        lower_quantity=characteristic.lower_quantity,
                        upper_quantity=characteristic.upper_quantity,
                        points=characteristic.points,
                        intervals=characteristic.intervals,
                        unbounded_above=characteristic.unbounded_above,
                        unbounded_below=characteristic.unbounded_below,
                    )
                raise EngEvaluationError(
                    f"unsupported characteristic result '{characteristic.kind}'"
                )

            if evaluator.partial_matrix_numeric_evaluation is not None:
                (
                    symbolic_matrix,
                    substitutions,
                    unresolved_symbols,
                    display_name,
                    display_arguments,
                ) = evaluator.partial_matrix_numeric_evaluation
                return PartialMatrixNumericEvaluationResult(
                    statement=statement,
                    symbolic_matrix=symbolic_matrix,
                    substitutions=substitutions,
                    unresolved_symbols=unresolved_symbols,
                    display_name=display_name,
                    display_arguments=display_arguments,
                )

            if evaluator.numeric_matrix_evaluation is not None:
                (
                    symbolic_matrix,
                    substitutions,
                    quantity_matrix,
                    display_name,
                    display_arguments,
                ) = evaluator.numeric_matrix_evaluation
                return NumericMatrixEvaluationResult(
                    statement=statement,
                    symbolic_matrix=symbolic_matrix,
                    substitutions=substitutions,
                    quantity_matrix=quantity_matrix,
                    display_name=display_name,
                    display_arguments=display_arguments,
                )

            if evaluator.partial_numeric_evaluation is not None:
                (
                    symbolic_expression,
                    substitutions,
                    unresolved_symbols,
                    evaluated_terms,
                    display_name,
                    display_arguments,
                    piecewise_evaluation,
                ) = evaluator.partial_numeric_evaluation
                return PartialNumericEvaluationResult(
                    statement=statement,
                    symbolic_expression=symbolic_expression,
                    substitutions=substitutions,
                    unresolved_symbols=unresolved_symbols,
                    evaluated_terms=evaluated_terms,
                    display_name=display_name,
                    display_arguments=display_arguments,
                    piecewise_evaluation=piecewise_evaluation,
                )

            if evaluator.numeric_evaluation is not None:
                (
                    symbolic_expression,
                    substitutions,
                    quantity,
                    display_name,
                    display_arguments,
                ) = evaluator.numeric_evaluation
                return NumericEvaluationResult(
                    statement=statement,
                    symbolic_expression=symbolic_expression,
                    substitutions=substitutions,
                    quantity=quantity,
                    display_name=display_name,
                    display_arguments=display_arguments,
                )

            if statement.target is not None:
                if statement.parameters is not None:
                    for parameter in statement.parameters:
                        self.resolve_symbol(parameter)
                    self.functions[statement.target] = UserFunction(
                        parameters=statement.parameters,
                        expression=value,
                        derivative_variable=evaluator.derivative_variable,
                        derivative_breakpoints=evaluator.derivative_breakpoints,
                        numeric_guards=tuple(evaluator.numeric_guards),
                    )
                else:
                    self.namespace[statement.target] = value
                    if evaluator.numeric_guards:
                        self.numeric_guards[statement.target] = tuple(evaluator.numeric_guards)
                    else:
                        self.numeric_guards.pop(statement.target, None)
            return EvaluationResult(
                statement=statement,
                display_input=evaluator.display_input,
                value=value,
            )
        except EngCalcError as exc:
            message = str(exc)
            if message.startswith("line "):
                raise
            raise type(exc)(f"line {statement.line_no}: {message}") from None
        except Exception as exc:
            raise EngEvaluationError(
                f"line {statement.line_no}: symbolic evaluation failed: {exc}"
            ) from None


class _Evaluator(ast.NodeVisitor):
    def __init__(self, engine: EngineeringEngine, matrix_literals=()) -> None:
        self.engine = engine
        self.matrix_literals = {binding.name: binding.literal for binding in matrix_literals}
        self.display_input = None
        self.numeric_evaluation = None
        self.partial_numeric_evaluation = None
        self.numeric_matrix_evaluation = None
        self.partial_matrix_numeric_evaluation = None
        self.plot_evaluation: _PlotEvaluation | None = None
        self.table_evaluation: _TableEvaluation | None = None
        self.characteristic_evaluation: _CharacteristicEvaluation | None = None
        self.system_evaluation: _SystemSolveEvaluation | None = None
        self.assume_evaluation: tuple[tuple[str, str], ...] | None = None
        self.governing_evaluation = None
        self.symbol_overrides: dict[str, sp.Symbol] = {}
        self.derivative_variable: str | None = None
        self.derivative_breakpoints: tuple[object, ...] = ()
        self.numeric_guards: list[MatrixNumericGuard] = []

    def _add_numeric_guard(self, guard: MatrixNumericGuard) -> None:
        if not any(existing == guard for existing in self.numeric_guards):
            self.numeric_guards.append(guard)

    def _add_numeric_guards(self, guards) -> None:
        for guard in guards:
            self._add_numeric_guard(guard)

    def _substitute_numeric_guard(self, guard: MatrixNumericGuard, bindings) -> MatrixNumericGuard:
        source = substitute_symbolic_value(guard.source_matrix, bindings) if bindings else guard.source_matrix
        return MatrixNumericGuard(
            operation=guard.operation,
            source_matrix=sp.ImmutableMatrix(source),
        )

    def _validate_numeric_guards(
        self,
        guards=None,
        *,
        overrides=None,
        allowed_unresolved=None,
    ):
        validations = []
        for guard in tuple(self.numeric_guards if guards is None else guards):
            _substitutions, unresolved, quantity_matrix = self.engine.numeric_context.evaluate_matrix(
                guard.source_matrix,
                overrides=overrides,
                allowed_unresolved=allowed_unresolved,
            )
            if unresolved:
                continue
            scale = ensure_common_scale(quantity_matrix, guard.operation)
            validations.append((guard, scale))
        return tuple(validations)

    @staticmethod
    def _guard_scale(validations, operation: str, source_matrix):
        for guard, scale in reversed(validations):
            if guard.operation == operation and guard.source_matrix == source_matrix:
                return scale
        return None

    def _numeric_eigenvalue_set(self, value: EigenvalueSet, validations, target_unit=None):
        scale = self._guard_scale(validations, "eigenvals", value.source_matrix)
        entries = []
        for entry in value.entries:
            _substitutions, quantity = self.engine.numeric_context.evaluate_symbolic(entry.value)
            if (
                scale is not None
                and quantity.dimensionless
                and float(quantity.magnitude) == 0.0
            ):
                quantity = self.engine.numeric_context.ureg.Quantity(0, scale)
            if target_unit is not None:
                quantity = self.engine.numeric_context.convert_quantity(quantity, target_unit)
            entries.append(EigenvalueEntry(value=quantity, multiplicity=entry.multiplicity))
        return EigenvalueSet(entries=tuple(entries), source_matrix=value.source_matrix)

    def _numeric_eigenvector_set(self, value: EigenvectorSet, validations, target_unit=None):
        scale = self._guard_scale(validations, "eigenvects", value.source_matrix)
        entries = []
        for entry in value.entries:
            _substitutions, quantity = self.engine.numeric_context.evaluate_symbolic(entry.value)
            if (
                scale is not None
                and quantity.dimensionless
                and float(quantity.magnitude) == 0.0
            ):
                quantity = self.engine.numeric_context.ureg.Quantity(0, scale)
            if target_unit is not None:
                quantity = self.engine.numeric_context.convert_quantity(quantity, target_unit)
            numeric_vectors = []
            for vector in entry.vectors:
                _subs, unresolved, quantity_matrix = self.engine.numeric_context.evaluate_matrix(vector)
                if unresolved:
                    raise EngEvaluationError(
                        "numeric eigenvectors require fully numeric vector entries"
                    )
                numeric_vectors.append(quantity_matrix)
            entries.append(
                EigenvectorEntry(
                    value=quantity,
                    multiplicity=entry.multiplicity,
                    vectors=tuple(numeric_vectors),
                )
            )
        return EigenvectorSet(entries=tuple(entries), source_matrix=value.source_matrix)

    def visit_function_body(self, node: ast.AST, parameters: tuple[str, ...]):
        previous = dict(self.symbol_overrides)
        try:
            for name in parameters:
                self.symbol_overrides[name] = self.engine.resolve_symbol(name)
            return self.visit(node)
        finally:
            self.symbol_overrides.clear()
            self.symbol_overrides.update(previous)

    def generic_visit(self, node):
        raise EngEvaluationError(f"unsupported syntax '{type(node).__name__}'")

    def _resolve_numeric_function_argument(self, node: ast.AST):
        if isinstance(node, ast.Name):
            symbolic = self.visit(node)
            if (
                isinstance(symbolic, sp.Symbol)
                and self.engine.numeric_context.get(node.id) is None
            ):
                return symbolic
        return self.engine.numeric_context.evaluate_expression(
            ast.Expression(body=node)
        )

    def _resolve_numeric_user_function_argument(self, node: ast.AST):
        try:
            return self._resolve_numeric_function_argument(node)
        except EngEvaluationError as exc:
            user_function_fallback = (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in self.engine.functions
                and "unsupported numeric function" in str(exc)
            )
            unresolved_name_fallback = "unknown numeric name" in str(exc)
            if not (user_function_fallback or unresolved_name_fallback):
                raise

            symbolic = self.visit(node)
            try:
                _, quantity = self.engine.numeric_context.evaluate_symbolic(symbolic)
            except EngEvaluationError as symbolic_exc:
                if "numeric evaluation requires values for:" in str(symbolic_exc):
                    return sp.sympify(symbolic)
                raise
            return quantity

    def _evaluate_matrix_literal(self, literal):
        rows = tuple(
            tuple(self.visit(expression.body) for expression in row)
            for row in literal.rows
        )
        return build_matrix(rows)

    def visit_List(self, node: ast.List):
        return build_matrix((tuple(self.visit(element) for element in node.elts),))

    def visit_Subscript(self, node: ast.Subscript):
        value = self.visit(node.value)
        if isinstance(node.slice, ast.Tuple):
            index_nodes = tuple(node.slice.elts)
        else:
            index_nodes = (node.slice,)
        indices = tuple(self.visit(item) for item in index_nodes)
        return matrix_index(value, indices)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, bool) or node.value is None:
            raise EngEvaluationError("only numeric constants are supported")
        if isinstance(node.value, int):
            return sp.Integer(node.value)
        if isinstance(node.value, float):
            return sp.Float(str(node.value))
        raise EngEvaluationError("only numeric constants are supported")

    def visit_Name(self, node: ast.Name):
        if node.id in self.matrix_literals:
            return self._evaluate_matrix_literal(self.matrix_literals[node.id])
        if node.id in self.symbol_overrides:
            return self.symbol_overrides[node.id]
        if node.id == "pi":
            return sp.pi
        if node.id in self.engine.namespace:
            self._add_numeric_guards(self.engine.numeric_guards.get(node.id, ()))
        return self.engine.resolve_name(node.id)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        value = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
        raise EngEvaluationError("unsupported unary operator")

    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return matrix_add(left, right)
        if isinstance(node.op, ast.Sub):
            return matrix_subtract(left, right)
        if isinstance(node.op, ast.Mult):
            return matrix_multiply(left, right)
        if isinstance(node.op, ast.Div):
            return matrix_scalar_divide(left, right)
        if isinstance(node.op, ast.Pow):
            return matrix_power(left, right)
        raise EngEvaluationError("unsupported operator")

    def _evaluate_piecewise_condition(self, node: ast.AST):
        if not isinstance(node, ast.Compare):
            raise EngEvaluationError("piecewise condition must be a comparison")
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise EngEvaluationError("piecewise condition must be a binary comparison")
        left = self.visit(node.left)
        right = self.visit(node.comparators[0])
        return build_relation(left, node.ops[0], right)

    def _evaluate_piecewise(self, node: ast.Call):
        if node.keywords or len(node.args) < 3 or len(node.args) % 2 == 0:
            raise EngEvaluationError(
                "piecewise expects value/condition pairs and a default"
            )
        branches = tuple(
            (
                self.visit(node.args[index]),
                self._evaluate_piecewise_condition(node.args[index + 1]),
            )
            for index in range(0, len(node.args) - 1, 2)
        )
        default = self.visit(node.args[-1])
        return build_piecewise(branches, default)

    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name):
            raise EngSyntaxError(f"unsupported syntax '{type(node.func).__name__}'")
        name = node.func.id

        if name in {"roots", "intersections", "extrema", "governing"}:
            return self._evaluate_characteristic(node, name)

        if name == "piecewise":
            return self._evaluate_piecewise(node)

        if name == "sum":
            self._require_arity(name, node.args, 4, "expression, index, lower, upper")
            index_node = node.args[1]
            if not isinstance(index_node, ast.Name):
                raise EngEvaluationError("sum index must be a symbolic identifier")
            index_name = index_node.id
            index = self.engine.resolve_symbol(index_name)
            previous = self.symbol_overrides.get(index_name)
            self.symbol_overrides[index_name] = index
            try:
                expr = self.visit(node.args[0])
            finally:
                if previous is None:
                    self.symbol_overrides.pop(index_name, None)
                else:
                    self.symbol_overrides[index_name] = previous
            lower = self.visit(node.args[2])
            upper = self.visit(node.args[3])
            symbolic_sum = sp.Sum(expr, (index, lower, upper))
            self.display_input = symbolic_sum
            return symbolic_sum

        if name == "assume":
            # The parser has already checked these are single comparisons; what each one
            # means is decided here, so the messages come from one place.
            keywords = {
                ast.Gt: "positive",
                ast.GtE: "nonnegative",
                ast.Lt: "negative",
                ast.LtE: "nonpositive",
            }
            declared: list[tuple[str, str]] = []
            for argument in node.args:
                subject = argument.left
                comparator = argument.comparators[0]
                if not isinstance(subject, ast.Name):
                    raise EngEvaluationError(
                        "assume applies to a plain symbol, as in assume(L > 0)"
                    )
                if not (
                    isinstance(comparator, ast.Constant) and comparator.value == 0
                ):
                    raise EngEvaluationError(
                        "assume compares a symbol against zero, as in assume(L > 0); "
                        "a bound like L > 5 is not something a symbol can carry"
                    )
                subject_name = subject.id
                if subject_name in self.engine.symbols:
                    raise EngEvaluationError(
                        f"'{subject_name}' has already been used, so an assumption about "
                        "it would apply to a different symbol and change nothing at all; "
                        "state assumptions before the symbol appears"
                    )
                keyword = keywords[type(argument.ops[0])]
                self.engine.assumptions.setdefault(subject_name, {})[keyword] = True
                declared.append((subject_name, keyword))
            self.assume_evaluation = tuple(declared)
            return None

        if name == "plot":
            return self._evaluate_plot(node)

        if name == "envelope":
            return self._evaluate_envelope(node)

        if name == "table":
            return self._evaluate_table(node)

        if name == "numeric":
            if len(node.args) not in (1, 2):
                raise EngEvaluationError(
                    "numeric expects 1 or 2 arguments: expression[, target_unit]"
                )

            argument = node.args[0]
            target_unit = None
            if len(node.args) == 2:
                target_unit = self.engine.numeric_context.evaluate_unit_expression(
                    ast.Expression(body=node.args[1])
                )

            display_name = argument.id if isinstance(argument, ast.Name) else None
            display_arguments = None

            if (
                isinstance(argument, ast.Call)
                and isinstance(argument.func, ast.Name)
                and argument.func.id in self.engine.functions
            ):
                function_name = argument.func.id
                function = self.engine.functions[function_name]
                self._require_user_function_arity(
                    function_name,
                    function,
                    argument.args,
                )
                argument_expressions = tuple(
                    self.visit(argument_node)
                    for argument_node in argument.args
                )
                argument_values = tuple(
                    self._resolve_numeric_user_function_argument(argument_node)
                    for argument_node in argument.args
                )
                symbolic_expression = function.expression
                display_name = function_name
                display_arguments = argument_expressions

                unresolved_arguments = [
                    (parameter, argument_expression, argument_value)
                    for parameter, argument_expression, argument_value in zip(
                        function.parameters,
                        argument_expressions,
                        argument_values,
                    )
                    if isinstance(argument_value, sp.Expr)
                ]
                overrides = {}
                bindings = {}
                allowed_unresolved: set[str] = set()
                for parameter, argument_expression, argument_value in zip(
                    function.parameters,
                    argument_expressions,
                    argument_values,
                ):
                    if isinstance(argument_value, sp.Expr):
                        symbolic_argument = sp.sympify(argument_expression)
                        bindings[self.engine.resolve_symbol(parameter)] = symbolic_argument
                        allowed_unresolved.update(
                            symbol.name for symbol in symbolic_argument.free_symbols
                        )
                    else:
                        overrides[parameter] = argument_value

                if bindings:
                    symbolic_expression = substitute_symbolic_value(
                        symbolic_expression,
                        bindings,
                    )

                effective_guards = tuple(
                    self._substitute_numeric_guard(guard, bindings)
                    for guard in function.numeric_guards
                )
                self._add_numeric_guards(effective_guards)
                self._validate_numeric_guards(
                    effective_guards,
                    overrides=overrides,
                    allowed_unresolved=allowed_unresolved,
                )

                if is_matrix(symbolic_expression):
                    if (
                        not unresolved_arguments
                        and function.derivative_variable is not None
                        and function.derivative_breakpoints
                        and function.derivative_variable in function.parameters
                    ):
                        derivative_index = function.parameters.index(
                            function.derivative_variable
                        )
                        self.engine.numeric_context.ensure_not_derivative_breakpoint(
                            function.derivative_variable,
                            argument_values[derivative_index],
                            function.derivative_breakpoints,
                            overrides=overrides,
                        )

                    substitutions, unresolved_symbols, quantity_matrix = (
                        self.engine.numeric_context.evaluate_matrix(
                            symbolic_expression,
                            overrides=overrides,
                            target_unit=target_unit,
                            allowed_unresolved=allowed_unresolved,
                        )
                    )
                    if unresolved_symbols:
                        self.partial_matrix_numeric_evaluation = (
                            symbolic_expression,
                            substitutions,
                            unresolved_symbols,
                            display_name,
                            display_arguments,
                        )
                    else:
                        self.numeric_matrix_evaluation = (
                            symbolic_expression,
                            substitutions,
                            quantity_matrix,
                            display_name,
                            display_arguments,
                        )
                    return symbolic_expression

                symbolic_expression = sp.sympify(symbolic_expression)
                if unresolved_arguments:
                    substitutions, unresolved_symbols = (
                        self.engine.numeric_context.partial_substitutions(
                            symbolic_expression,
                            allowed_unresolved=allowed_unresolved,
                            overrides=overrides,
                        )
                    )

                    if unresolved_symbols:
                        if target_unit is not None:
                            suffix = ": " + ", ".join(unresolved_symbols)
                            raise EngEvaluationError(
                                "target-unit conversion requires a fully numeric result"
                                + suffix
                            )

                        evaluated_terms = None
                        if len(unresolved_symbols) == 1:
                            evaluated_terms = (
                                self.engine.numeric_context.evaluate_partial_polynomial(
                                    symbolic_expression,
                                    unresolved_symbols[0],
                                    overrides=overrides,
                                )
                            )

                        piecewise_evaluation = None
                        if (
                            len(unresolved_symbols) == 1
                            and isinstance(symbolic_expression, sp.Piecewise)
                        ):
                            piecewise_evaluation = (
                                self.engine.numeric_context.build_partial_piecewise_evaluation(
                                    symbolic_expression,
                                    unresolved_symbols[0],
                                    overrides=overrides,
                                )
                            )

                        self.partial_numeric_evaluation = (
                            symbolic_expression,
                            substitutions,
                            unresolved_symbols,
                            evaluated_terms,
                            display_name,
                            display_arguments,
                            piecewise_evaluation,
                        )
                        return symbolic_expression

                if (
                    function.derivative_variable is not None
                    and function.derivative_breakpoints
                    and function.derivative_variable in function.parameters
                ):
                    derivative_index = function.parameters.index(function.derivative_variable)
                    self.engine.numeric_context.ensure_not_derivative_breakpoint(
                        function.derivative_variable,
                        argument_values[derivative_index],
                        function.derivative_breakpoints,
                        overrides=overrides,
                    )
                try:
                    substitutions, quantity = self.engine.numeric_context.evaluate_symbolic(
                        symbolic_expression,
                        overrides=overrides,
                    )
                except EngEvaluationError as exc:
                    message = str(exc)
                    if message.startswith("piecewise "):
                        raise
                    if "incompatible units" not in message:
                        raise
                    hint = diagnostic_hint(
                        "incompatible_function_units",
                        function=function_name,
                    )
                    raise EngEvaluationError(
                        f"incompatible units while evaluating numeric function '{function_name}'. {hint}"
                    ) from exc
            else:
                symbolic_expression = self.visit(argument)
                guard_validations = self._validate_numeric_guards()
                if isinstance(symbolic_expression, EigenvalueSet):
                    return self._numeric_eigenvalue_set(
                        symbolic_expression,
                        guard_validations,
                        target_unit=target_unit,
                    )
                if isinstance(symbolic_expression, EigenvectorSet):
                    return self._numeric_eigenvector_set(
                        symbolic_expression,
                        guard_validations,
                        target_unit=target_unit,
                    )
                if is_matrix(symbolic_expression):
                    substitutions, unresolved_symbols, quantity_matrix = (
                        self.engine.numeric_context.evaluate_matrix(
                            symbolic_expression,
                            target_unit=target_unit,
                        )
                    )
                    if unresolved_symbols:
                        self.partial_matrix_numeric_evaluation = (
                            symbolic_expression,
                            substitutions,
                            unresolved_symbols,
                            display_name,
                            display_arguments,
                        )
                    else:
                        self.numeric_matrix_evaluation = (
                            symbolic_expression,
                            substitutions,
                            quantity_matrix,
                            display_name,
                            display_arguments,
                        )
                    return symbolic_expression

                substitutions, quantity = self.engine.numeric_context.evaluate_symbolic(
                    symbolic_expression
                )

            if target_unit is not None:
                quantity = self.engine.numeric_context.convert_quantity(
                    quantity,
                    target_unit,
                )

            self.numeric_evaluation = (
                symbolic_expression,
                substitutions,
                quantity,
                display_name,
                display_arguments,
            )
            return symbolic_expression

        if name == "solve":
            if len(node.args) != 2:
                self._visit_equation_system(node)
                return None

            first_value = self.visit(node.args[0])
            if is_matrix(first_value):
                rhs_value = self.visit(node.args[1])
                return solve_linear_system(first_value, rhs_value)

            unknown_node = node.args[1]
            if not isinstance(unknown_node, ast.Name):
                raise EngEvaluationError("solve unknown must be a symbolic identifier")
            unknown_name = unknown_node.id
            unknown = self.engine.resolve_symbol(unknown_name)
            previous = self.symbol_overrides.get(unknown_name)
            self.symbol_overrides[unknown_name] = unknown
            try:
                equation = self.visit(node.args[0])
            finally:
                if previous is None:
                    self.symbol_overrides.pop(unknown_name, None)
                else:
                    self.symbol_overrides[unknown_name] = previous
            if not isinstance(equation, sp.Equality):
                equation = sp.Eq(equation, 0, evaluate=False)
            self.display_input = equation
            solutions = sp.solve(equation, unknown)
            if len(solutions) == 0:
                raise EngEvaluationError(f"solve found no solution for {unknown}")
            if len(solutions) > 1:
                # Several answers is not an error and never was; the previous guard
                # said "v0.1 requires one", which was a contract from the earliest
                # version rather than a mathematical limit. Complex solutions are kept:
                # an engineer shown one answer has no way to know two were discarded.
                self.system_evaluation = _SystemSolveEvaluation(
                    equations=(equation,),
                    solutions=tuple((unknown_name, value) for value in solutions),
                    kind="multi",
                )
                return None
            return solutions[0]

        args = [self.visit(arg) for arg in node.args]

        if name == "identity":
            self._require_arity(name, args, 1, "dimension")
            return matrix_identity(args[0])

        if name == "zeros":
            self._require_arity(name, args, 2, "rows, cols")
            return matrix_zeros(args[0], args[1])

        if name == "diag":
            return matrix_diag(args)

        if name == "transpose":
            self._require_arity(name, args, 1, "matrix")
            return matrix_transpose(args[0])

        if name == "det":
            self._require_arity(name, args, 1, "matrix")
            return matrix_det(args[0])

        if name == "inv":
            self._require_arity(name, args, 1, "matrix")
            return matrix_inv(args[0])

        if name == "trace":
            self._require_arity(name, args, 1, "matrix")
            return matrix_trace(args[0])

        if name == "size":
            self._require_arity(name, args, 1, "matrix")
            rows, cols = matrix_size(args[0])
            return MatrixShape(rows=rows, cols=cols)

        if name in {"rank", "rref", "norm", "eigenvals", "eigenvects"}:
            self._require_arity(name, args, 1, "matrix")
            operations = {
                "rank": matrix_rank,
                "rref": matrix_rref,
                "norm": matrix_norm,
                "eigenvals": matrix_eigenvals,
                "eigenvects": matrix_eigenvects,
            }
            result = operations[name](args[0])
            source_matrix = sp.ImmutableMatrix(args[0])
            self._add_numeric_guard(
                MatrixNumericGuard(operation=name, source_matrix=source_matrix)
            )
            return result

        if name in self.engine.functions:
            function = self.engine.functions[name]
            self._require_user_function_arity(name, function, args)
            parameters = tuple(
                self.engine.resolve_symbol(parameter)
                for parameter in function.parameters
            )
            bindings = dict(zip(parameters, args))
            self._add_numeric_guards(
                self._substitute_numeric_guard(guard, bindings)
                for guard in function.numeric_guards
            )
            return substitute_symbolic_value(function.expression, bindings)

        if name in _SCALAR_SYMBOLIC_FUNCTIONS:
            self._require_arity(name, args, 1, "expression")
            if is_matrix(args[0]):
                raise EngEvaluationError(
                    f"{name} requires a scalar expression, not a matrix"
                )
            if name in {"asin", "acos", "atan"}:
                return _SCALAR_SYMBOLIC_FUNCTIONS[name](args[0], evaluate=False)
            return _SCALAR_SYMBOLIC_FUNCTIONS[name](args[0])

        if name == "abs":
            self._require_arity(name, args, 1, "expression")
            return sp.Abs(args[0])

        if name in ("integrate", "integral"):
            # Two arguments is the indefinite integral, four the definite one. The
            # message below names the function the engineer actually typed, and names
            # both forms, because three arguments almost always means a bound was
            # forgotten rather than that the shape was misunderstood.
            if len(args) not in (2, 4):
                raise EngEvaluationError(
                    f"{name} expects 2 arguments (expression, variable) for an "
                    "indefinite integral, or 4 (expression, variable, lower, upper) "
                    f"for a definite one; got {len(args)}"
                )
            expr, var = args[0], args[1]
            # No constant of integration is invented. The engineer writes the one they
            # need - ``integrate(M(x)/(E*I), x) + C1`` - which is what happens on paper
            # and avoids EngCalc naming symbols nobody asked for.
            bounds = var if len(args) == 2 else (var, args[2], args[3])
            if is_matrix(expr):
                self.display_input = map_matrix_entries(
                    expr,
                    lambda entry: sp.Integral(entry, bounds),
                )
                return map_matrix_entries(
                    expr,
                    lambda entry: sp.integrate(entry, bounds),
                )
            self.display_input = sp.Integral(expr, bounds)
            return sp.integrate(expr, bounds)

        if name == "macaulay":
            # Written `<variable - offset>^n`; the parser rewrites the bracket notation
            # to this call. SymPy's SingularityFunction is the operation itself,
            # including the integration rule that makes V -> M -> theta -> v chain term
            # by term, so nothing mathematical is implemented here.
            self._require_arity(name, args, 2, "shifted expression, exponent")
            expression, order = args
            expanded = sp.expand(expression)
            # The variable is the symbol the bracket shifts, so it carries coefficient 1.
            # Anything else - a scaled variable, two symbols, a bare number - is not
            # Macaulay notation and is refused rather than guessed at.
            candidates = [
                symbol
                for symbol in getattr(expanded, "free_symbols", set())
                if expanded.coeff(symbol, 1) == 1
            ]
            if len(candidates) != 1:
                raise EngEvaluationError(
                    "a Macaulay bracket is written <variable - offset>, so exactly one "
                    f"symbol must appear with coefficient 1; got <{expression}>"
                )
            variable = candidates[0]
            offset = sp.simplify(variable - expanded)
            if variable in offset.free_symbols:
                raise EngEvaluationError(
                    "a Macaulay bracket shifts its variable, it does not scale it: "
                    f"<{expression}> is not of the form <variable - offset>"
                )
            return sp.SingularityFunction(variable, offset, order)

        if name == "diff":
            if len(args) not in (2, 3):
                raise EngEvaluationError(
                    "diff expects 2 or 3 arguments: expression, variable[, order]"
                )
            expr, var = args[:2]
            order = int(args[2]) if len(args) == 3 else 1
            if is_matrix(expr):
                self.display_input = map_matrix_entries(
                    expr,
                    lambda entry: sp.Derivative(entry, (var, order)),
                )
                if isinstance(var, sp.Symbol):
                    breakpoints = []
                    for entry in expr:
                        for breakpoint in extract_symbolic_breakpoints(entry, var.name):
                            if breakpoint not in breakpoints:
                                breakpoints.append(breakpoint)
                    if breakpoints:
                        self.derivative_variable = var.name
                        self.derivative_breakpoints = tuple(breakpoints)
                return map_matrix_entries(
                    expr,
                    lambda entry: sp.diff(entry, var, order),
                )

            self.display_input = sp.Derivative(expr, (var, order))
            if isinstance(var, sp.Symbol):
                breakpoints = extract_symbolic_breakpoints(expr, var.name)
                if breakpoints:
                    self.derivative_variable = var.name
                    self.derivative_breakpoints = breakpoints
            return sp.diff(expr, var, order)

        if name == "eq":
            self._require_arity(name, args, 2, "left, right")
            return sp.Eq(args[0], args[1], evaluate=False)

        if name in {"simplify", "expand", "factor"}:
            self._require_arity(name, args, 1, "expression")
            operation = {
                "simplify": sp.simplify,
                "expand": sp.expand,
                "factor": sp.factor,
            }[name]
            if is_matrix(args[0]):
                return map_matrix_entries(args[0], operation)
            return operation(args[0])

        if name == "subs":
            # One expression followed by variable/value pairs, so the count is odd. The
            # three-argument form is the one-pair case of the same rule and is untouched.
            if len(args) < 3 or len(args) % 2 == 0:
                raise EngEvaluationError(
                    "subs expects an expression followed by variable/value pairs, so an "
                    f"odd number of arguments; got {len(args)}"
                )
            replacements = list(zip(args[1::2], args[2::2]))
            # ``simultaneous`` because writing several replacements on one line means
            # they happen together: subs(x + y, x, y, y, 2) is y + 2, not 4.
            if is_matrix(args[0]):
                return map_matrix_entries(
                    args[0],
                    lambda entry: sp.sympify(entry).subs(replacements, simultaneous=True),
                )
            return sp.sympify(args[0]).subs(replacements, simultaneous=True)

        raise EngSyntaxError(f"unsupported function '{name}'")


    def _resolve_domain_numeric_value(self, node: ast.AST):
        value = self._resolve_numeric_user_function_argument(node)
        if isinstance(value, sp.Expr):
            _, value = self.engine.numeric_context.evaluate_symbolic(
                value,
                overrides=self.engine.numeric_context.unit_literal_overrides(value),
            )
        return value

    @staticmethod
    def _operation_specific_characteristic_error(name: str, exc: EngEvaluationError):
        message = str(exc)
        if message.startswith("characteristic domain"):
            message = name + message[len("characteristic"):]
        return EngEvaluationError(message)

    def _evaluate_characteristic(self, node: ast.Call, name: str):
        if node.keywords:
            raise EngEvaluationError(
                f"{name} accepts positional arguments only"
            )

        if name == "governing":
            # Any number of responses, then variable, lower, upper - the same shape as
            # envelope, because these are the same combinations one would plot.
            if len(node.args) < 5:
                raise EngEvaluationError(
                    "governing expects at least 5 positional arguments: "
                    "two responses, variable, lower, upper. Comparing fewer than two "
                    "is a mistake: one response governs its whole domain by itself"
                )
            response_nodes = node.args[:-3]
            variable_node, lower_node, upper_node = node.args[-3:]
        elif name == "intersections":
            self._require_arity(
                name,
                node.args,
                5,
                "left_response, right_response, variable, lower, upper",
            )
            response_nodes = node.args[:2]
            variable_node = node.args[2]
            lower_node, upper_node = node.args[3:]
        else:
            self._require_arity(
                name,
                node.args,
                4,
                "response, variable, lower, upper",
            )
            response_nodes = node.args[:1]
            variable_node = node.args[1]
            lower_node, upper_node = node.args[2:]

        if not isinstance(variable_node, ast.Name):
            raise EngEvaluationError(
                f"{name} variable must be a symbolic identifier"
            )
        variable_name = variable_node.id
        variable_symbol = self.engine.resolve_symbol(variable_name)

        lower_expression = self.visit(lower_node)
        upper_expression = self.visit(upper_node)
        try:
            try:
                lower_quantity = self._resolve_domain_numeric_value(lower_node)
                upper_quantity = self._resolve_domain_numeric_value(upper_node)
            except EngEvaluationError as exc:
                raise EngEvaluationError(
                    "characteristic domain bound must be numerically resolvable: "
                    + str(exc)
                ) from None
            domain = normalize_analysis_domain(
                self.engine.numeric_context,
                lower_expression,
                upper_expression,
                lower_quantity=lower_quantity,
                upper_quantity=upper_quantity,
            )
        except EngEvaluationError as exc:
            raise self._operation_specific_characteristic_error(name, exc) from None

        sentinel = object()
        previous = self.symbol_overrides.get(variable_name, sentinel)
        self.symbol_overrides[variable_name] = variable_symbol
        try:
            resolved = tuple(
                self._resolve_response_expression(response_node, variable_name)
                for response_node in response_nodes
            )
        finally:
            if previous is sentinel:
                self.symbol_overrides.pop(variable_name, None)
            else:
                self.symbol_overrides[variable_name] = previous

        if any(
            is_matrix(item.signed_expression)
            or is_matrix(item.comparison_expression)
            for item in resolved
        ):
            raise EngEvaluationError(
                f"{name} response must be scalar; index the matrix first, "
                "for example A[1,1]"
            )

        if name == "governing":
            # Built on the exact crossovers rather than on the envelope's 201-point
            # sampling. Reading the envelope's per-sample winner back would have been
            # the obvious implementation and would have put every boundary on a 30 mm
            # grid for a 6 m span; equating the responses pairwise gives the crossover
            # symbolically, so a boundary is exact wherever the mathematics is.
            lower_quantity = domain.lower_quantity
            upper_quantity = domain.upper_quantity
            unit = lower_quantity.units

            crossovers = []
            for index, left in enumerate(resolved):
                for right in resolved[index + 1 :]:
                    points, _intervals, unresolved = solve_intersections_exact(
                        left.comparison_expression,
                        right.comparison_expression,
                        variable_symbol,
                        domain,
                        self.engine.numeric_context,
                        left_label=left.display_label,
                        right_label=right.display_label,
                    )
                    if unresolved:
                        raise EngEvaluationError(
                            "governing could not resolve where "
                            f"{left.display_label} and {right.display_label} cross"
                        )
                    crossovers.extend(point.x_quantity for point in points)

            def magnitude_in_unit(quantity):
                return float(quantity.to(unit).magnitude)

            edges = [lower_quantity, upper_quantity]
            for crossover in crossovers:
                position = magnitude_in_unit(crossover)
                if (
                    magnitude_in_unit(lower_quantity)
                    < position
                    < magnitude_in_unit(upper_quantity)
                ):
                    edges.append(crossover)
            edges.sort(key=magnitude_in_unit)

            segments: list[GoverningInterval] = []
            for start, end in zip(edges, edges[1:]):
                midpoint = (start + end) / 2
                best_label = None
                best_magnitude = None
                for response in resolved:
                    _, value = self.engine.numeric_context.evaluate_symbolic(
                        response.comparison_expression,
                        {variable_name: midpoint},
                    )
                    magnitude = float(value.magnitude)
                    if best_magnitude is None or magnitude > best_magnitude:
                        best_label, best_magnitude = response.display_label, magnitude
                # A boundary where nothing changes hands is not a boundary.
                if segments and segments[-1].label == best_label:
                    segments[-1] = GoverningInterval(
                        lower_quantity=segments[-1].lower_quantity,
                        upper_quantity=end,
                        label=best_label,
                    )
                else:
                    segments.append(
                        GoverningInterval(
                            lower_quantity=start,
                            upper_quantity=end,
                            label=best_label,
                        )
                    )

            self.governing_evaluation = (
                variable_name,
                tuple(item.display_label for item in resolved),
                tuple(segments),
            )
            return None

        if name == "roots":
            response = resolved[0]
            points, intervals, unresolved = solve_roots_exact(
                response.comparison_expression,
                variable_symbol,
                domain,
                self.engine.numeric_context,
                source_label=response.display_label,
            )
            if unresolved:
                raise EngEvaluationError(
                    "roots characteristic analysis could not resolve a safe solution set"
                )
            self.characteristic_evaluation = _CharacteristicEvaluation(
                kind="roots",
                variable=variable_name,
                lower_quantity=domain.lower_quantity,
                upper_quantity=domain.upper_quantity,
                points=tuple(points),
                intervals=tuple(intervals),
                first_symbolic_expression=response.comparison_expression,
                display_label=response.display_label,
            )
            return response.comparison_expression

        if name == "intersections":
            left, right = resolved
            points, intervals, unresolved = solve_intersections_exact(
                left.comparison_expression,
                right.comparison_expression,
                variable_symbol,
                domain,
                self.engine.numeric_context,
                left_label=left.display_label,
                right_label=right.display_label,
            )
            if unresolved:
                raise EngEvaluationError(
                    "intersections characteristic analysis could not resolve "
                    "a safe solution set"
                )
            self.characteristic_evaluation = _CharacteristicEvaluation(
                kind="intersections",
                variable=variable_name,
                lower_quantity=domain.lower_quantity,
                upper_quantity=domain.upper_quantity,
                points=tuple(points),
                intervals=tuple(intervals),
                first_symbolic_expression=left.comparison_expression,
                left_label=left.display_label,
                right_label=right.display_label,
            )
            return left.comparison_expression

        response = resolved[0]
        points, intervals, unbounded_above, unbounded_below, unresolved = (
            solve_extrema_exact(
                response.comparison_expression,
                variable_symbol,
                domain,
                self.engine.numeric_context,
                source_label=response.display_label,
            )
        )
        if unresolved:
            raise EngEvaluationError(
                "extrema characteristic analysis could not resolve a safe solution set"
            )
        self.characteristic_evaluation = _CharacteristicEvaluation(
            kind="extrema",
            variable=variable_name,
            lower_quantity=domain.lower_quantity,
            upper_quantity=domain.upper_quantity,
            points=tuple(points),
            intervals=tuple(intervals),
            first_symbolic_expression=response.comparison_expression,
            display_label=response.display_label,
            unbounded_above=unbounded_above,
            unbounded_below=unbounded_below,
        )
        return response.comparison_expression

    def _resolve_table_numeric_value(self, node: ast.AST):
        return self._resolve_domain_numeric_value(node)

    def _evaluate_table(self, node: ast.Call):
        args = node.args
        point_list = None
        declared_unit_node = None

        if len(args) >= 3 and isinstance(args[-1], ast.List):
            response_nodes = args[:-2]
            variable_node = args[-2]
            point_list = args[-1]
        elif len(args) >= 4 and isinstance(args[-2], ast.List):
            response_nodes = args[:-3]
            variable_node = args[-3]
            point_list = args[-2]
            declared_unit_node = args[-1]
        else:
            response_nodes = args[:-4]
            variable_node = args[-4]
            lower_node, upper_node, count_node = args[-3:]

        if not response_nodes:
            raise EngEvaluationError("table requires at least one response expression")
        if not isinstance(variable_node, ast.Name):
            raise EngEvaluationError("table variable must be a symbolic identifier")
        variable = variable_node.id
        context = self.engine.numeric_context

        if point_list is None:
            lower = self._resolve_table_numeric_value(lower_node)
            upper = self._resolve_table_numeric_value(upper_node)
            count = self._resolve_table_numeric_value(count_node)
            point_values = normalize_uniform_points(context, lower, upper, count)
            mode = "uniform"
        else:
            raw_points = tuple(
                self._resolve_table_numeric_value(element)
                for element in point_list.elts
            )
            declared_unit = None
            if declared_unit_node is not None:
                declared_unit = context.evaluate_unit_expression(
                    ast.Expression(body=declared_unit_node)
                )
            point_values = normalize_explicit_points(
                context,
                raw_points,
                declared_unit,
            )
            mode = "explicit"

        resolved_responses = [
            self._resolve_response_expression(item, variable)
            for item in response_nodes
        ]
        if any(
            is_matrix(response.signed_expression)
            or is_matrix(response.comparison_expression)
            for response in resolved_responses
        ):
            raise EngEvaluationError("table response must be scalar")

        columns = []
        canonical_unit = None
        for response in resolved_responses:
            values = []
            for point in point_values:
                _, quantity = context.evaluate_symbolic(
                    response.comparison_expression,
                    overrides={variable: point},
                )
                values.append(quantity)

            if canonical_unit is None:
                canonical_unit = values[0].units
            try:
                normalized_values = tuple(
                    value.to(canonical_unit)
                    for value in values
                )
            except DimensionalityError as exc:
                raise EngEvaluationError(
                    "table response columns have incompatible units"
                ) from exc

            columns.append(
                TableColumn(
                    display_label=response.display_label,
                    unit=canonical_unit,
                    values=normalized_values,
                )
            )

        self.table_evaluation = _TableEvaluation(
            variable=variable,
            point_unit=point_values[0].units,
            point_values=tuple(point_values),
            columns=tuple(columns),
            mode=mode,
            first_symbolic_expression=resolved_responses[0].comparison_expression,
        )
        return resolved_responses[0].comparison_expression

    def _plot_characteristics(
        self,
        expression,
        variable: str,
        domain,
        *,
        source_label: str,
        overrides=None,
    ) -> tuple[CharacteristicPoint, ...]:
        try:
            points, _intervals, _up, _down, unresolved = solve_extrema_exact(
                expression,
                self.engine.resolve_symbol(variable),
                domain,
                self.engine.numeric_context,
                overrides=overrides,
                source_label=source_label,
            )
        except (EngEvaluationError, TypeError, ValueError):
            return ()
        if unresolved:
            return ()
        return tuple(
            point
            for point in points
            if point.value_quantity is not None
            and any(role in {"global_max", "global_min"} for role in point.roles)
        )

    def _evaluate_plot(self, node: ast.Call):
        resolved = self._resolve_response_series(node, call_name="plot")
        self.plot_evaluation = _PlotEvaluation(
            display_label=resolved.display_label,
            variable=resolved.variable,
            x_values=resolved.x_values,
            series=resolved.series,
            kind="plot",
        )
        return resolved.first_symbolic_expression

    def _evaluate_envelope(self, node: ast.Call):
        resolved = self._resolve_response_series(node, call_name="envelope")
        comparison_series = resolved.series
        if len(comparison_series) < 2:
            raise EngEvaluationError("envelope requires at least two response series")
        if resolved.envelope_mode is None:
            raise EngEvaluationError(
                "envelope cannot mix absolute and signed response series"
            )

        envelope_segment_starts = tuple(sorted({
            start
            for series in (*resolved.series, *resolved.source_series)
            for start in series.segment_starts
        }))

        if resolved.envelope_mode == "magnitude":
            maximum_values = []
            governing_maximum = []
            governing_signed = []

            for sample_index in range(len(resolved.x_values)):
                magnitudes = [
                    float(item.y_values[sample_index].magnitude)
                    for item in comparison_series
                ]
                maximum_index = max(
                    range(len(magnitudes)),
                    key=magnitudes.__getitem__,
                )
                governing_maximum.append(maximum_index)
                maximum_values.append(
                    comparison_series[maximum_index].y_values[sample_index]
                )
                governing_signed.append(
                    resolved.source_series[maximum_index].y_values[sample_index]
                )

            suffix = f"({resolved.variable})"
            if (
                resolved.display_label != "Comparison"
                and resolved.display_label.endswith(suffix)
            ):
                family = resolved.display_label[: -len(suffix)]
                magnitude_label = f"|{family}|_max({resolved.variable})"
            else:
                magnitude_label = "|max|"

            envelope_series = (
                PlotSeries(
                    display_label=magnitude_label,
                    y_values=tuple(maximum_values),
                    is_moment=comparison_series[0].is_moment,
                    segment_starts=envelope_segment_starts,
                ),
            )

            self.plot_evaluation = _PlotEvaluation(
                display_label=resolved.display_label,
                variable=resolved.variable,
                x_values=resolved.x_values,
                series=envelope_series,
                kind="envelope",
                source_series=resolved.source_series,
                source_labels=resolved.source_labels,
                governing_max=tuple(governing_maximum),
                governing_min=None,
                envelope_mode="magnitude",
                governing_signed=tuple(governing_signed),
            )
            return resolved.first_symbolic_expression

        maximum_values = []
        minimum_values = []
        governing_maximum = []
        governing_minimum = []

        for sample_index in range(len(resolved.x_values)):
            magnitudes = [
                float(item.y_values[sample_index].magnitude)
                for item in comparison_series
            ]
            maximum_index = max(range(len(magnitudes)), key=magnitudes.__getitem__)
            minimum_index = min(range(len(magnitudes)), key=magnitudes.__getitem__)
            governing_maximum.append(maximum_index)
            governing_minimum.append(minimum_index)
            maximum_values.append(
                comparison_series[maximum_index].y_values[sample_index]
            )
            minimum_values.append(
                comparison_series[minimum_index].y_values[sample_index]
            )

        maximum_label, minimum_label = self._envelope_series_labels(
            resolved.display_label,
            resolved.variable,
        )
        is_moment = comparison_series[0].is_moment
        envelope_series = (
            PlotSeries(
                display_label=maximum_label,
                y_values=tuple(maximum_values),
                is_moment=is_moment,
                segment_starts=envelope_segment_starts,
            ),
            PlotSeries(
                display_label=minimum_label,
                y_values=tuple(minimum_values),
                is_moment=is_moment,
                segment_starts=envelope_segment_starts,
            ),
        )

        self.plot_evaluation = _PlotEvaluation(
            display_label=resolved.display_label,
            variable=resolved.variable,
            x_values=resolved.x_values,
            series=envelope_series,
            kind="envelope",
            source_series=resolved.source_series,
            source_labels=resolved.source_labels,
            governing_max=tuple(governing_maximum),
            governing_min=tuple(governing_minimum),
            envelope_mode="signed",
        )
        return resolved.first_symbolic_expression

    def _resolve_response_expression(
        self,
        node: ast.AST,
        variable: str,
    ) -> _ResolvedExpression:
        is_absolute = (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "abs"
        )
        if is_absolute:
            self._require_arity("abs", node.args, 1, "expression")
            signed_node = node.args[0]
            signed_expression = self.visit(signed_node)
            comparison_expression = sp.Abs(signed_expression)
            source_label = self._plot_expression_label(
                signed_node,
                variable,
                signed_expression,
            )
            display_label = f"|{source_label}|"
        else:
            signed_expression = self.visit(node)
            comparison_expression = signed_expression
            source_label = self._plot_expression_label(
                node,
                variable,
                signed_expression,
            )
            display_label = source_label

        return _ResolvedExpression(
            source_label=source_label,
            display_label=display_label,
            signed_expression=signed_expression,
            comparison_expression=comparison_expression,
            is_absolute=is_absolute,
        )

    def _resolve_response_series(
        self,
        node: ast.Call,
        *,
        call_name: str,
    ) -> _ResolvedResponseSeries:
        if len(node.args) < 4:
            raise EngEvaluationError(
                f"{call_name} expects at least 4 positional arguments: "
                "expression[, ...], variable, start, end"
            )

        expression_nodes = node.args[:-3]
        variable_node, start_node, end_node = node.args[-3:]
        if not expression_nodes:
            raise EngEvaluationError(
                f"{call_name} requires at least one expression"
            )
        if not isinstance(variable_node, ast.Name):
            raise EngEvaluationError(
                f"{call_name} variable must be a symbolic identifier"
            )
        variable = variable_node.id

        if node.keywords and len(expression_nodes) != 1:
            raise EngEvaluationError(
                f"{call_name} parameter sweep requires exactly one expression"
            )

        start_expression = self.visit(start_node)
        end_expression = self.visit(end_node)
        start_quantity = self._resolve_domain_numeric_value(start_node)
        end_quantity = self._resolve_domain_numeric_value(end_node)
        start_quantity, end_quantity = self.engine.numeric_context.normalize_plot_bounds(
            start_quantity,
            end_quantity,
        )
        analysis_domain = None
        if call_name == "plot":
            analysis_domain = normalize_analysis_domain(
                self.engine.numeric_context,
                start_expression,
                end_expression,
                lower_quantity=start_quantity,
                upper_quantity=end_quantity,
            )

        resolved_expressions = [
            self._resolve_response_expression(item, variable)
            for item in expression_nodes
        ]
        if any(
            is_matrix(expression.signed_expression)
            or is_matrix(expression.comparison_expression)
            for expression in resolved_expressions
        ):
            raise EngEvaluationError(f"{call_name} response must be scalar")
        source_labels = [item.source_label for item in resolved_expressions]

        if node.keywords:
            expression = resolved_expressions[0]
            raw_series, raw_source_series, x_values = self._evaluate_response_sweep(
                expression.comparison_expression,
                expression.signed_expression,
                expression.source_label,
                variable,
                start_quantity,
                end_quantity,
                node.keywords[0],
                call_name=call_name,
                preserve_signed_source=(
                    call_name == "envelope" and expression.is_absolute
                ),
                analysis_domain=analysis_domain,
            )
            source_labels = [item.display_label for item in raw_source_series]
            display_label = (
                expression.display_label
                if call_name == "plot"
                else expression.source_label
            )
        else:
            raw_series = []
            raw_source_series = []
            expression_cases = tuple(
                (expression.comparison_expression, None)
                for expression in resolved_expressions
            )
            x_values = self.engine.numeric_context.build_plot_sample_points(
                expression_cases,
                variable,
                start_quantity,
                end_quantity,
                count=201,
            )
            for expression in resolved_expressions:
                y_values = self.engine.numeric_context.sample_symbolic_points(
                    expression.comparison_expression,
                    variable,
                    x_values,
                )
                source_y_values = self.engine.numeric_context.sample_symbolic_points(
                    expression.signed_expression,
                    variable,
                    x_values,
                )
                segment_starts = self.engine.numeric_context.piecewise_segment_starts(
                    expression.comparison_expression, variable, x_values
                )
                source_segment_starts = self.engine.numeric_context.piecewise_segment_starts(
                    expression.signed_expression, variable, x_values
                )
                characteristics = ()
                if call_name == "plot":
                    characteristics = self._plot_characteristics(
                        expression.comparison_expression,
                        variable,
                        analysis_domain,
                        source_label=expression.display_label,
                    )
                raw_series.append(
                    PlotSeries(
                        display_label=expression.display_label,
                        y_values=y_values,
                        is_moment=self._is_moment_label(expression.source_label),
                        segment_starts=segment_starts,
                        characteristics=characteristics,
                    )
                )
                raw_source_series.append(
                    PlotSeries(
                        display_label=expression.source_label,
                        y_values=source_y_values,
                        is_moment=self._is_moment_label(expression.source_label),
                        segment_starts=source_segment_starts,
                    )
                )
            if call_name == "plot" and len(resolved_expressions) == 1:
                display_label = resolved_expressions[0].display_label
            else:
                display_label = self._common_plot_label(source_labels, variable)

        series = self._normalize_response_series(
            tuple(raw_series),
            call_name=call_name,
        )
        source_series = self._normalize_response_series(
            tuple(raw_source_series),
            call_name=call_name,
        )
        if len(series) > 1:
            moment_flags = {item.is_moment for item in series}
            if len(moment_flags) > 1:
                raise EngEvaluationError(
                    f"{call_name} cannot mix moment and non-moment series on one axis"
                )

        envelope_mode = None
        if call_name == "envelope":
            absolute_flags = {item.is_absolute for item in resolved_expressions}
            if absolute_flags == {True}:
                envelope_mode = "magnitude"
            elif absolute_flags == {False}:
                envelope_mode = "signed"

        return _ResolvedResponseSeries(
            display_label=display_label,
            variable=variable,
            x_values=x_values,
            series=series,
            source_series=source_series,
            source_labels=tuple(source_labels),
            first_symbolic_expression=resolved_expressions[0].comparison_expression,
            envelope_mode=envelope_mode,
        )

    def _evaluate_response_sweep(
        self,
        comparison_expression,
        signed_expression,
        source_label: str,
        variable: str,
        start_quantity,
        end_quantity,
        keyword_node: ast.keyword,
        *,
        call_name: str,
        preserve_signed_source: bool,
        analysis_domain,
    ) -> tuple[list[PlotSeries], list[PlotSeries], tuple]:
        parameter_name = keyword_node.arg
        if parameter_name is None:
            raise EngEvaluationError(
                f"{call_name} sweep parameter must be named"
            )
        if parameter_name == variable:
            raise EngEvaluationError(
                f"{call_name} sweep parameter '{parameter_name}' "
                "cannot be the plotting variable"
            )

        free_names = {
            symbol.name
            for symbol in sp.sympify(comparison_expression).free_symbols
        }
        if parameter_name not in free_names:
            raise EngEvaluationError(
                f"{call_name} sweep parameter '{parameter_name}' "
                "is not used in the plotted expression"
            )

        sweep_values = [
            self.engine.numeric_context.evaluate_expression(
                ast.Expression(body=element)
            )
            for element in keyword_node.value.elts
        ]
        sweep_values = self._normalize_sweep_values(
            parameter_name,
            sweep_values,
            call_name=call_name,
        )

        is_moment = self._is_moment_label(source_label)
        comparison_series: list[PlotSeries] = []
        source_series: list[PlotSeries] = []
        case_overrides = tuple(
            {parameter_name: sweep_value}
            for sweep_value in sweep_values
        )
        x_values = self.engine.numeric_context.build_plot_sample_points(
            tuple(
                (comparison_expression, overrides)
                for overrides in case_overrides
            ),
            variable,
            start_quantity,
            end_quantity,
            count=201,
        )
        for sweep_value, overrides in zip(sweep_values, case_overrides):
            comparison_y_values = self.engine.numeric_context.sample_symbolic_points(
                comparison_expression,
                variable,
                x_values,
                overrides=overrides,
            )
            if preserve_signed_source:
                source_y_values = self.engine.numeric_context.sample_symbolic_points(
                    signed_expression,
                    variable,
                    x_values,
                    overrides=overrides,
                )
            else:
                source_y_values = comparison_y_values

            case_label = (
                f"{parameter_name} = {self._format_plot_quantity(sweep_value)}"
            )
            segment_starts = self.engine.numeric_context.piecewise_segment_starts(
                comparison_expression, variable, x_values, overrides=overrides
            )
            source_segment_starts = self.engine.numeric_context.piecewise_segment_starts(
                signed_expression, variable, x_values, overrides=overrides
            )
            characteristics = ()
            if call_name == "plot":
                characteristics = self._plot_characteristics(
                    comparison_expression,
                    variable,
                    analysis_domain,
                    source_label=case_label,
                    overrides=overrides,
                )
            comparison_series.append(
                PlotSeries(
                    display_label=case_label,
                    y_values=comparison_y_values,
                    is_moment=is_moment,
                    segment_starts=segment_starts,
                    characteristics=characteristics,
                )
            )
            source_series.append(
                PlotSeries(
                    display_label=case_label,
                    y_values=source_y_values,
                    is_moment=is_moment,
                    segment_starts=source_segment_starts,
                )
            )

        return comparison_series, source_series, x_values

    def _normalize_sweep_values(
        self,
        parameter_name: str,
        values: list,
        *,
        call_name: str,
    ):
        stored = self.engine.numeric_context.get(parameter_name)
        target_unit = stored.units if stored is not None else values[0].units
        normalized = []
        for value in values:
            try:
                normalized.append(value.to(target_unit))
            except DimensionalityError as exc:
                raise EngEvaluationError(
                    f"{call_name} sweep values have incompatible units"
                ) from exc
        return normalized

    @staticmethod
    def _normalize_response_series(
        series: tuple[PlotSeries, ...],
        *,
        call_name: str,
    ) -> tuple[PlotSeries, ...]:
        if not series:
            raise EngEvaluationError(
                f"{call_name} requires at least one series"
            )

        target_unit = series[0].y_values[0].units
        normalized: list[PlotSeries] = []
        for item in series:
            try:
                y_values = tuple(value.to(target_unit) for value in item.y_values)
                characteristics = tuple(
                    replace(
                        point,
                        value_quantity=(
                            None
                            if point.value_quantity is None
                            else point.value_quantity.to(target_unit)
                        ),
                    )
                    for point in item.characteristics
                )
            except DimensionalityError as exc:
                raise EngEvaluationError(
                    f"{call_name} series have incompatible y dimensions"
                ) from exc
            normalized.append(
                PlotSeries(
                    display_label=item.display_label,
                    y_values=y_values,
                    is_moment=item.is_moment,
                    segment_starts=item.segment_starts,
                    characteristics=characteristics,
                )
            )
        return tuple(normalized)

    def _plot_expression_label(
        self,
        expression_node: ast.AST,
        variable: str,
        symbolic_expression,
    ) -> str:
        if (
            isinstance(expression_node, ast.Call)
            and isinstance(expression_node.func, ast.Name)
            and expression_node.func.id in self.engine.functions
        ):
            return f"{expression_node.func.id}({variable})"
        return str(symbolic_expression)

    @staticmethod
    def _common_plot_label(labels: list[str], variable: str) -> str:
        if len(labels) == 1:
            return labels[0]

        function_names = []
        for label in labels:
            if not label.endswith(f"({variable})"):
                return "Comparison"
            function_names.append(label[: -(len(variable) + 2)])

        families = {name.split("_", 1)[0] for name in function_names}
        if len(families) == 1:
            family = next(iter(families))
            return f"{family}({variable})"
        return "Comparison"

    @staticmethod
    def _envelope_series_labels(display_label: str, variable: str) -> tuple[str, str]:
        suffix = f"({variable})"
        if display_label != "Comparison" and display_label.endswith(suffix):
            family = display_label[: -len(suffix)]
            return f"{family}_max({variable})", f"{family}_min({variable})"
        return "max", "min"

    @staticmethod
    def _is_moment_label(label: str) -> bool:
        return _MOMENT_LABEL.match(label.strip()) is not None

    @staticmethod
    def _format_plot_quantity(quantity) -> str:
        magnitude = float(quantity.magnitude)
        value = f"{magnitude:g}"
        if quantity.dimensionless:
            return value
        return f"{value} {quantity.units:~P}"

    @staticmethod
    def _require_user_function_arity(name: str, function: UserFunction, args: list) -> None:
        expected = len(function.parameters)
        received = len(args)
        if received == expected:
            return
        signature = ", ".join(function.parameters)
        raise EngEvaluationError(
            f"function '{name}' expects {expected} arguments ({signature}), "
            f"received {received}"
        )

    def _visit_equation_system(self, node) -> None:
        """`solve(eq_1, ..., eq_n, x_1, ..., x_n)`.

        The count is even: n equations then n unknowns. The two-argument form is the
        n = 1 case of the same rule, handled on the ordinary path so its behaviour is
        untouched. Splitting by position rather than by inspecting the arguments is
        deliberate - in `solve(eqFy, eqMA, R_A, R_B)` all four are plain identifiers,
        so nothing syntactic distinguishes an equation from an unknown.
        """
        count = len(node.args)
        if count < 4 or count % 2 != 0:
            raise EngEvaluationError(
                "solve expects n equations followed by n unknowns, so an even number "
                f"of arguments; got {count}"
            )

        half = count // 2
        unknown_nodes = node.args[half:]
        names: list[str] = []
        for unknown_node in unknown_nodes:
            if not isinstance(unknown_node, ast.Name):
                raise EngEvaluationError("solve unknown must be a symbolic identifier")
            names.append(unknown_node.id)
        if len(set(names)) != len(names):
            raise EngEvaluationError("solve unknowns must be distinct")

        # Every unknown is forced to resolve as a free symbol while the equations are
        # read, so a name that already carries a value is still solved for rather than
        # substituted away.
        symbols = [self.engine.resolve_symbol(name) for name in names]
        previous = {name: self.symbol_overrides.get(name) for name in names}
        self.symbol_overrides.update(dict(zip(names, symbols)))
        try:
            equations = []
            for equation_node in node.args[:half]:
                equation = self.visit(equation_node)
                if not isinstance(equation, sp.Equality):
                    equation = sp.Eq(equation, 0, evaluate=False)
                equations.append(equation)
        finally:
            for name, value in previous.items():
                if value is None:
                    self.symbol_overrides.pop(name, None)
                else:
                    self.symbol_overrides[name] = value

        solution = sp.solve(equations, symbols, dict=True)
        if not solution:
            raise EngEvaluationError(
                "solve found no solution for " + ", ".join(names)
            )
        if len(solution) > 1:
            raise AmbiguousSolveError(
                f"solve returned {len(solution)} solutions for "
                + ", ".join(names)
                + "; a system must have one"
            )

        mapping = solution[0]
        missing = [name for name, symbol in zip(names, symbols) if symbol not in mapping]
        if missing:
            raise EngEvaluationError(
                "solve did not determine " + ", ".join(missing)
            )

        self.system_evaluation = _SystemSolveEvaluation(
            equations=tuple(equations),
            solutions=tuple(
                (name, mapping[symbol]) for name, symbol in zip(names, symbols)
            ),
        )

    @staticmethod
    def _require_arity(name: str, args: list, count: int, signature: str) -> None:
        if len(args) != count:
            noun = "argument" if count == 1 else "arguments"
            raise EngEvaluationError(f"{name} expects {count} {noun}: {signature}")
