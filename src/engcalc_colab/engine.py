from __future__ import annotations

import ast
import math
import re
from dataclasses import dataclass, replace

import sympy as sp
from pint.errors import DimensionalityError

from .characteristics.candidates import closed_form_factors
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
    FrameMember,
    FramePlotResult,
    ImageResult,
    MemberResult,
    CharacteristicInterval,
    CharacteristicPoint,
    DiscardedSolutions,
    LoadCaseResult,
    LoadCombinationResult,
    InequalityResult,
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
    NumericMatrixAssignmentResult,
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
    SummaryResult,
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
    IndexRange,
    matrix_assign,
    matrix_det,
    matrix_cross,
    matrix_diag,
    matrix_dot,
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
from .matrix_modes import modes_of, take_mode
from .matrix_numeric import (
    MATRIX_CALLS,
    NumberMatrix,
    QuantityMatrix,
    add_numbers,
    blocks_of_numbers,
    ensure_common_scale,
    entry_quantity,
    inverse_numbers,
    multiply_numbers,
    numbers_of,
    quantity_matrix_of,
    scalar_numbers,
    scale_numbers,
    solve_numbers,
    take_numbers,
    transpose_numbers,
)
from .matrix_solve import solve_linear_system
from .interpolation import Interpolation
from .min_max import WrittenMax, WrittenMin
from .numeric import _UNIT_ALIASES, NumericContext, _NumericAstEvaluator
from .piecewise import (
    build_piecewise,
    build_relation,
    extract_symbolic_breakpoints,
    substitute_keeping_condition_sides,
)
from .tables import normalize_explicit_points, normalize_uniform_points
from .unit_text import quantity_text


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
    # A piecewise is reassembled branch by branch, so SymPy's reassembly does not
    # canonicalise its conditions and move the interval variable across the comparison.
    # See ``substitute_keeping_condition_sides``.
    piecewise = substitute_keeping_condition_sides(expression, bindings)
    if piecewise is not None:
        return piecewise
    return expression.xreplace(bindings)

_MOMENT_LABEL = re.compile(r"^M(?:_[A-Za-z0-9]+|[0-9]+)?\(")
# `Md(x)`, `Mu(x)`, `Mn(x)`, `Mmax(x)`: the names a design sheet gives a moment. A letter
# after the `M` could as well begin `Mass(x)`, so these count as a moment only when what
# they draw is a force times a length. See `test_a_design_moment_is_plotted_downward`.
_MOMENT_FAMILY_LABEL = re.compile(r"^M[A-Za-z0-9_]*\(")


@dataclass(frozen=True)
class _ResolvedExpression:
    source_label: str
    display_label: str
    signed_expression: object
    comparison_expression: object
    is_absolute: bool
    # What a characteristic heading typesets, or None where the label is already how a
    # person writes it - `M(x)`. See `_heading_expression`.
    label_expression: object = None


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
    discarded: DiscardedSolutions | None = None


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
    label_expression: object = None
    left_expression: object = None
    right_expression: object = None


class _QuantityOfTheFormula(_NumericAstEvaluator):
    """A right side evaluated over quantities as it is written, calls and `subs` included.

    What `_unit_of_a_zero` asks. #184 asked `numeric(<right side>)`, which substitutes
    quantities into a function only when the right side is a single call: `M(L)` kept its
    kN·m and `2*M(L)`, `M(L) + M(0*m)`, `V(L/2)*L` and `subs(q*(L - x), x, L)` did not,
    because around the call the formula is simplified symbolically first. Here nothing is
    simplified before Pint: a name is its quantity, a function of the sheet is its
    expression with the arguments' quantities substituted, and `subs` sets its variable to
    the value's quantity.
    """

    def __init__(self, engine: "EngineeringEngine", overrides=None) -> None:
        super().__init__(engine.numeric_context)
        self.engine = engine
        self.overrides = dict(overrides or {})

    def visit_Name(self, node: ast.Name):
        if node.id in self.overrides:
            return self.overrides[node.id]
        if node.id in self.engine.namespace and node.id not in self.context.values:
            _, quantity = self.context.evaluate_symbolic(self.engine.resolve_symbol(node.id))
            return self.engine.zero_in_its_unit(node.id, quantity)
        return super().visit_Name(node)

    def visit_Call(self, node: ast.Call):
        name = node.func.id if isinstance(node.func, ast.Name) else None
        if name in self.engine.functions:
            function = self.engine.functions[name]
            arguments = {
                parameter: self.visit(argument)
                for parameter, argument in zip(function.parameters, node.args, strict=True)
            }
            _, quantity = self.context.evaluate_symbolic(function.expression, overrides=arguments)
            return quantity
        if name == "subs" and len(node.args) == 3 and isinstance(node.args[1], ast.Name):
            expression, variable, value = node.args
            inner = _QuantityOfTheFormula(self.engine, {variable.id: self.visit(value)})
            return inner.visit(expression)
        return super().visit_Call(node)


class _MatrixNumbers:
    """The right side of a `:=` line that reads a matrix, worked out in numbers.

    `d := solve(K, F)`: `K` and `F` are the matrices the sheet built with `=`, evaluated
    entry by entry as `numeric(K)` evaluates them, and `solve` is then arithmetic on
    numbers. The symbolic `solve` of six degrees of freedom is the closed form this
    exists to avoid. Whatever part of the line reads no matrix - `w*L/2`, `H` - is a
    scalar, and goes to the evaluator every other `:=` line uses, so it means exactly what
    it would mean there.
    """

    _MATRIX_CALLS = MATRIX_CALLS

    def __init__(self, engine: "EngineeringEngine", statement) -> None:
        self.engine = engine
        self.context = engine.numeric_context
        self.literals = {
            binding.name: binding.literal
            for binding in getattr(statement, "matrix_literals", ())
        }

    def names_a_matrix(self, name: str) -> bool:
        if name in self.literals:
            return True
        # The precedence a scalar `:=` already has: a value settled with `:=` outranks
        # what `=` said, and a matrix of numbers outranks a matrix of formulas.
        if name in self.context.values:
            return False
        if name in self.context.matrices:
            return True
        return is_matrix(self.engine.namespace.get(name))

    def reads_a_matrix(self, node: ast.AST) -> bool:
        return any(
            isinstance(each, ast.Name) and self.names_a_matrix(each.id)
            for each in ast.walk(node)
        )

    def value(self, node: ast.AST):
        """A `NumberMatrix`, or a scalar quantity when the line takes one entry."""
        if not self.reads_a_matrix(node):
            return self._scalar(node)
        if isinstance(node, ast.List):
            return self._row(node)
        if isinstance(node, ast.Name):
            return self._named(node.id)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            operand = self.value(node.operand)
            if isinstance(node.op, ast.UAdd):
                return operand
            if isinstance(operand, NumberMatrix):
                return scale_numbers(operand, self.context.ureg.Quantity(-1))
            return -operand
        if isinstance(node, ast.BinOp):
            return self._binary(node)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return self._call(node)
        if isinstance(node, ast.Subscript):
            return self._part(node)
        raise EngEvaluationError(
            f"'{ast.unparse(node)}' cannot be worked out in numbers on a := line"
        )

    def _scalar(self, node: ast.AST):
        """A part of the line that reads no matrix, as a `:=` line reads it elsewhere.

        A function of the sheet goes through `_QuantityOfTheFormula`, the way
        `_assign_through_the_sheet` answers `M_max := M(L/2)`; `NumericContext` knows only
        the functions mathematics has, and `y := M(3*m)*d[1,1]/m` stopped at `M`.
        """
        if self.engine._calls_a_function_of_the_sheet(node):
            return _QuantityOfTheFormula(self.engine).visit(node)
        return self.context.evaluate_expression(ast.Expression(body=node))

    def _row(self, node: ast.List) -> NumberMatrix:
        """`[d[1,1], d[2,1]]`: a row written with commas, as a `=` line reads it."""
        cells = []
        for element in node.elts:
            value = self.value(element)
            if not isinstance(value, NumberMatrix):
                value = scalar_numbers(self.context._as_quantity(value))
            cells.append(value)
        return blocks_of_numbers([cells])

    def _named(self, name: str) -> NumberMatrix:
        if name in self.literals:
            return self._literal(self.literals[name])
        if name in self.context.matrices:
            return numbers_of(self.context.matrices[name])
        _substitutions, unresolved, quantity_matrix = self.context.evaluate_matrix(
            self.engine.namespace[name]
        )
        if unresolved:
            hint = diagnostic_hint("unresolved_numeric_symbols", names=tuple(unresolved))
            raise EngEvaluationError(
                f"{name} needs values for: " + ", ".join(unresolved) + f". {hint}"
            )
        return numbers_of(quantity_matrix)

    def _literal(self, literal) -> NumberMatrix:
        block_rows = []
        for row in literal.rows:
            blocks = []
            for cell in row:
                value = self.value(cell.body)
                if not isinstance(value, NumberMatrix):
                    value = scalar_numbers(self.context._as_quantity(value))
                blocks.append(value)
            block_rows.append(blocks)
        return blocks_of_numbers(block_rows)

    def _binary(self, node: ast.BinOp):
        left = self.value(node.left)
        right = self.value(node.right)
        left_matrix = isinstance(left, NumberMatrix)
        right_matrix = isinstance(right, NumberMatrix)
        if not (left_matrix or right_matrix):
            return self._scalar_binary(node.op, left, right)
        if isinstance(node.op, (ast.Add, ast.Sub)):
            if not (left_matrix and right_matrix):
                raise EngEvaluationError(
                    f"'{ast.unparse(node)}' adds a number to a matrix; a matrix is "
                    "added only to a matrix of the same size"
                )
            return add_numbers(left, right, 1 if isinstance(node.op, ast.Add) else -1)
        if isinstance(node.op, ast.Mult):
            if left_matrix and right_matrix:
                return multiply_numbers(left, right)
            if left_matrix:
                return scale_numbers(left, self.context._as_quantity(right))
            return scale_numbers(right, self.context._as_quantity(left))
        if isinstance(node.op, ast.Div) and left_matrix and not right_matrix:
            return scale_numbers(left, 1 / self.context._as_quantity(right))
        raise EngEvaluationError(
            f"'{ast.unparse(node)}' is not an operation between matrices; they are "
            "added, subtracted, multiplied and divided by a number"
        )

    def _scalar_binary(self, op: ast.operator, left, right):
        if isinstance(op, ast.Add):
            return left + right
        if isinstance(op, ast.Sub):
            return left - right
        if isinstance(op, ast.Mult):
            return left * right
        if isinstance(op, ast.Div):
            return left / right
        if isinstance(op, ast.Pow):
            exponent = self.context._as_quantity(right)
            if not exponent.dimensionless:
                raise EngEvaluationError("an exponent must be a number without a unit")
            return left ** float(exponent.to("").magnitude)
        raise EngEvaluationError("unsupported operator on a := line")

    def _call(self, node: ast.Call):
        name = node.func.id
        if name not in self._MATRIX_CALLS:
            return self._number_call(node)
        arguments = [self.value(argument) for argument in node.args]
        if name in self._MATRIX_CALLS:
            if node.keywords or not all(isinstance(each, NumberMatrix) for each in arguments):
                raise EngEvaluationError(f"{name} on a := line takes matrices")
            if name == "solve" and len(arguments) == 2:
                return solve_numbers(*arguments)
            if name == "inv" and len(arguments) == 1:
                return inverse_numbers(arguments[0])
            if name == "transpose" and len(arguments) == 1:
                return transpose_numbers(arguments[0])
            raise EngEvaluationError(
                f"{name} on a := line takes "
                + ("a matrix and a right-hand side" if name == "solve" else "one matrix")
            )
        raise EngEvaluationError(f"{name} cannot be worked out in numbers on a := line")

    def _number_call(self, node: ast.Call):
        """`min(3*h, d[1,1])`, `M(d[1,1])`, `sqrt(u^2 + v^2)`: a call that takes numbers.

        The arguments that read a matrix are worked out here - each must come to one
        number - and the call itself is left to the evaluator a `:=` line uses for
        everything else, so `min`, `max`, `interp`, the functions of mathematics and those
        of the sheet mean exactly what they mean there. Only `solve`, `inv` and `transpose`
        take matrices.
        """
        name = node.func.id
        bound: dict[str, object] = {}
        arguments = []
        for index, argument in enumerate(node.args):
            if not self.reads_a_matrix(argument):
                arguments.append(argument)
                continue
            value = self.value(argument)
            if isinstance(value, NumberMatrix):
                raise EngEvaluationError(
                    f"{name} on a := line takes numbers, and '{ast.unparse(argument)}' "
                    "is a matrix; take one of its entries, such as d[1,1]"
                )
            key = f"__eng_number_{index}"
            bound[key] = value
            arguments.append(ast.Name(id=key, ctx=ast.Load()))
        call = ast.Call(func=node.func, args=arguments, keywords=node.keywords)
        return _QuantityOfTheFormula(self.engine, bound).visit(call)

    def _part(self, node: ast.Subscript):
        numbers = self.value(node.value)
        if not isinstance(numbers, NumberMatrix):
            raise EngEvaluationError(f"'{ast.unparse(node.value)}' is not a matrix")
        index = node.slice
        parts = list(index.elts) if isinstance(index, ast.Tuple) else [index]
        selections = [self._positions(part) for part in parts]
        written = f"{ast.unparse(node.value)}[{','.join(ast.unparse(p) for p in parts)}]"
        if len(selections) == 1 and 1 in (numbers.rows, numbers.cols):
            # `d[4]` of a column or a row: its fourth entry.
            if numbers.cols == 1:
                selections.append(([1], False))
            else:
                selections.insert(0, ([1], False))
        if len(selections) != 2:
            raise EngEvaluationError(
                f"{written}: a matrix is indexed [row, column]"
            )
        (rows, rows_listed), (cols, cols_listed) = selections
        for position, size in ((rows, numbers.rows), (cols, numbers.cols)):
            if any(not 1 <= each <= size for each in position):
                raise EngEvaluationError(
                    f"{written} is outside a {numbers.shape} matrix; rows and columns "
                    "are counted from 1"
                )
        rows = [each - 1 for each in rows]
        cols = [each - 1 for each in cols]
        if not rows_listed and not cols_listed:
            return entry_quantity(numbers, rows[0], cols[0], self.context.ureg)
        return take_numbers(numbers, rows, cols)

    @staticmethod
    def _positions(part: ast.AST) -> tuple[list[int], bool]:
        if isinstance(part, ast.Constant) and isinstance(part.value, int):
            return [part.value], False
        if isinstance(part, ast.List) and all(
            isinstance(each, ast.Constant) and isinstance(each.value, int)
            for each in part.elts
        ):
            return [each.value for each in part.elts], True
        raise EngEvaluationError(
            f"'{ast.unparse(part)}': an index on a := line is a whole number or a list "
            "of them, such as d[4,1] or K[[1, 2], [1, 2]]"
        )


def measured_units_in(tree) -> frozenset[str]:
    """The unit aliases a statement writes as a measurement.

    A measurement is a product of numbers and units and nothing else: `1*m`, `2*kN/m`,
    `-1*kN/m`, `0.25*m^2`. A name written that way is a unit of this sheet. The same
    letters also name quantities - `s` a sine, `N` an axial force, `m` a mass - and in
    `c^2 + s^2` or `N + P` the name is never written so. Only whole products count:
    `4*kN*x/m` has an `x` in it and measures nothing, and `2*m*a` does not make a mass a
    metre. An exponent is not a factor, so `s^2` alone measures nothing either.
    """
    measured: set[str] = set()

    def factors(node, found: list) -> bool:
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Div)):
            return factors(node.left, found) and factors(node.right, found)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return factors(node.operand, found)
        if (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Pow)
            and isinstance(node.right, ast.Constant)
        ):
            return isinstance(node.left, ast.Name) and factors(node.left, found)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                return False
            found.append(None)
            return True
        if isinstance(node, ast.Name) and node.id in _UNIT_ALIASES:
            found.append(node.id)
            return True
        return False

    def visit(node, inside: bool) -> None:
        product = isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Div))
        if product and not inside:
            found: list = []
            if factors(node, found) and None in found:
                measured.update(name for name in found if name is not None)
        for child in ast.iter_child_nodes(node):
            visit(child, product or (inside and isinstance(node, ast.UnaryOp)))

    visit(tree, False)
    return frozenset(measured)


def letters_written_as_units_in(tree) -> frozenset[str]:
    """The one-letter unit aliases a statement writes where a unit is written.

    `N`, `m` and `s` are units and ordinary names at once. Next to a number or another unit
    they are plainly the unit - `30*N`, `2*m`, `4*kN*x/m`, `1/s` - and a sheet that writes
    them so has said what it means. Alone in a formula, `N/A` or `x/m`, nothing has.
    """
    written: set[str] = set()

    def factors(node, found: list) -> None:
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Div)):
            factors(node.left, found)
            factors(node.right, found)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            factors(node.operand, found)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            factors(node.left, found)
        else:
            found.append(node)

    def visit(node, inside: bool) -> None:
        product = isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Div))
        if product and not inside:
            found: list = []
            factors(node, found)
            names = [f.id for f in found if isinstance(f, ast.Name) and f.id in _UNIT_ALIASES]
            beside = any(
                isinstance(f, ast.Constant) and isinstance(f.value, (int, float))
                and not isinstance(f.value, bool)
                for f in found
            ) or any(len(name) > 1 for name in names)
            if beside:
                written.update(name for name in names if len(name) == 1)
        for child in ast.iter_child_nodes(node):
            visit(child, product or (inside and isinstance(node, ast.UnaryOp)))

    visit(tree, False)
    return frozenset(written)


def record_written_order(tree, order: dict) -> None:
    """Note in `order` which name each product of a statement writes before which.

    SymPy keeps no order for a product - `E*A` is stored `A*E` as it is read - so the
    order the engineer wrote is taken here, from the tree, before it is lost: for every
    product, each pair of names it holds, keyed by the pair and valued by which came
    first. The first writing is kept (`setdefault`): a page that writes `E*A` and then
    `A*E` reads one way throughout rather than a row changing with what came after it.

    A power counts by its base, `L^2` is `L`; a call or a sum is not a name and its own
    products are read on their own. Units are noted like any name and the printer leaves
    them to the page's unit order.
    """

    def names(node, found: list) -> None:
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Div)):
            names(node.left, found)
            names(node.right, found)
            return
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            names(node.operand, found)
            return
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            node = node.left
        if isinstance(node, ast.Name):
            found.append(node.id)

    def visit(node, inside: bool) -> None:
        product = isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Div))
        if product and not inside:
            found: list = []
            names(node, found)
            for index, first in enumerate(found):
                for second in found[index + 1:]:
                    if first != second:
                        order.setdefault(frozenset((first, second)), (first, second))
        for child in ast.iter_child_nodes(node):
            visit(child, product or (inside and isinstance(node, ast.UnaryOp)))

    visit(tree, False)


# The calls that leave a form of their own for the row to show. A statement that is one
# of them shows that form; a statement holding one inside something larger is read again.
_CALLS_THAT_SHOW = frozenset({"diff", "integrate", "sum", "solve"})


class EngineeringEngine:
    def __init__(self) -> None:
        self.namespace: dict[str, object] = {}
        self.functions: dict[str, UserFunction] = {}
        self.symbols: dict[str, sp.Symbol] = {}
        # What the engineer has stated about a symbol before using it, as SymPy keyword
        # assumptions. Applied in resolve_symbol.
        self.assumptions: dict[str, dict[str, bool]] = {}
        # Values marked with report(...), in the order they were first marked.
        self.reported: dict[str, object] = {}
        self.load_cases: dict[str, str] = {}
        # Names declared with `keep`. A later formula shows the name instead of
        # what it stands for; `namespace` still holds the expanded expression and
        # everything computes with that, so the barrier is presentation only.
        self.kept_names: set[str] = set()
        # The kept names whose number in `numeric_context.values` was computed from their
        # expression, and so follows it. See `_refresh_kept_values`.
        self.kept_values: set[str] = set()
        # Names whose `:=` wrote a unit down. `written_unit_names` already drew this
        # line per assignment, for that assignment's own row, and then discarded it.
        # A substituted value two lines later needs the same answer, so it is kept:
        # `d := 0.0105*m` must substitute as metres, and a circular frequency the
        # algebra left in `GPa^0.5*mm/(kg^0.5*m^0.5)` must not.
        self.declared_unit_names: set[str] = set()
        # The composite units those lines actually spelled, as Pint writes them.
        # Consulted in exactly one place: a convention that would otherwise rewrite
        # a soil pressure the engineer wrote as `tonf/m^2` into `kgf/cm^2`.
        self.written_units: set[str] = set()
        # The expression each definition was written with, when one was kept and
        # verified. Only ever displayed - `namespace` is what everything computes
        # with - and it is what lets `numeric(phiMn)` open with the same formula
        # its definition showed instead of contradicting it a line later.
        self.written_namespace: dict[str, object] = {}
        self.numeric_guards: dict[str, tuple[MatrixNumericGuard, ...]] = {}
        # Every alias this session has read as a unit, and which aliases each line read
        # that way, so that a name changing meaning can say so. See `evaluate`.
        self.names_read_as_units: set[str] = set()
        # Unit aliases this sheet writes as a measurement - `1*m`, `2*kN/m` - and so
        # uses as units, not as variables that share their names. See
        # `measured_units_in`.
        self.measured_units: set[str] = set()
        # Which name this sheet wrote before which in a product, first writing kept. See
        # `record_written_order`.
        self.written_order: dict[frozenset[str], tuple[str, str]] = {}
        # The one-letter aliases the sheet has written where a unit is written, and those a
        # line has already been told are read as units. See `_notice_a_letter_read_as_a_unit`.
        self.letters_written_as_units: set[str] = set()
        self.letters_said_to_be_units: set[str] = set()
        self.units_read_by_line: dict[str, frozenset[str]] = {}
        # The number each figure of `image(...)` was given, by file and caption, so a
        # cell run again keeps its numbers. See `_image_asked_for`.
        self.figure_numbers: dict[tuple[str, str | None], int] = {}
        # The members of a frame, by name, in the order declared. See `_member_asked_for`.
        # A function's body as it was written, for a function that reads a kept name: a
        # call of it is written from this. See `test_a_kept_name_survives_a_sheet_function`.
        self.written_functions: dict[str, object] = {}
        self.frame_members: dict[str, FrameMember] = {}
        # What the last statement has to say that is not an error. The magic prints it.
        self.notices: list[str] = []
        # The unit of a definition whose value simplified to an exact zero, which a
        # SymPy zero cannot carry. See `_unit_of_a_zero`.
        self.zero_quantities: dict[str, object] = {}
        self.numeric_context = NumericContext()
        # Shared by reference, so a name defined symbolically later is visible when a
        # numeric evaluation needs it. See NumericContext._resolve_symbolic_names.
        self.numeric_context.symbolic_namespace = self.namespace
        # Shared the same way, and for the opposite reason: a kept name must not
        # be expanded when a numeric evaluation reaches it. It has a value of its
        # own, and that value is what the substitution stage should show.
        self.numeric_context.kept_names = self.kept_names

    def _case_variable(self, expression, where: str) -> str:
        """The one symbol a case is a function of.

        Everything else in a load case has a value: `qD`, `L`, the units. What is left
        is the coordinate along the member, so it is found rather than declared - which
        is what lets `case D = M_D(x)` read the way a combination is written down.
        """
        free = sorted(
            symbol.name
            for symbol in sp.sympify(expression).free_symbols
            if symbol.name not in self.numeric_context.values
            and symbol.name not in _UNIT_ALIASES
        )
        if len(free) != 1:
            raise EngEvaluationError(
                f"{where} must be a function of exactly one variable; "
                + (
                    "it has none, so there is nothing to plot it against"
                    if not free
                    else "found " + ", ".join(free)
                )
            )
        return free[0]

    def _solution_quantity(self, value):
        """The number of one of several answers, or None when it has none: a name with no
        value, or a complex root. Several answers cannot be named, so this is the only
        place the reader is shown them as numbers."""
        try:
            _substitutions, quantity = self.numeric_context.evaluate_symbolic(value)
        except EngEvaluationError:
            # A complex root among them: the numeric layer refuses a value with no
            # real result, where it used to hand back Python's `2j`.
            return None
        return quantity

    def _assign_part(self, statement: ParsedStatement, evaluator) -> EvaluationResult:
        """`K[[1, 2], [1, 2]] = K[[1, 2], [1, 2]] + k_1*k_e`: the direct stiffness method's
        assembly step. The right-hand side reads the matrix as it stands, the part is
        replaced, and the page shows the matrix after it.

        The matrix's written form is dropped, not kept: it was the formula of the matrix
        before this line, and a formula the matrix no longer equals must not be shown."""
        name = statement.target
        current = self.namespace.get(name)
        if not is_matrix(current):
            raise EngEvaluationError(
                f"{name} has no matrix to assign into; start it as one, for example "
                f"{name} = zeros(3, 3)"
            )
        replacement = evaluator.visit(statement.expression.body)
        value = matrix_assign(
            current, evaluator.index_values(statement.target_index), replacement, name
        )
        self.namespace[name] = value
        self.written_namespace.pop(name, None)
        self.numeric_guards.pop(name, None)
        return EvaluationResult(
            statement=statement,
            display_input=None,
            value=value,
            unit_literals=self._unit_literals_of(value),
        )

    def _unit_literals_of(self, *values) -> frozenset[str]:
        """The names a row reads as units, by the rule its numeric row uses.

        A row is its expression *and* its heading. `numeric(f(9*m))` writes the argument
        into the heading, and the renderer that draws it had nothing to tell `m` from an
        italic variable, so it fell back on the printer's own rule that a name of several
        letters is upright: `cm`, `mm`, `kN` and `kg` came out as units and `m`, `s`, `N`
        and `g` as variables, in the same column. Passing the arguments here is #96
        reaching the one place that was never handed the answer.

        The guard is what decides: only a symbolic value can carry a unit *name*. An
        argument that arrives as a quantity already carries a real unit and is drawn by
        the quantity printer, which never had this question to answer.
        """
        names: set[str] = set()
        for value in values:
            if isinstance(value, (sp.Basic, sp.MatrixBase)):
                names |= self.numeric_context.unit_literal_names(value)
            elif isinstance(value, (EigenvalueSet, EigenvectorSet)):
                # A set is not an expression, so it was never asked: `λ = 2 kN/m` set its
                # metre italic two lines under the matrix that wrote it upright. Every
                # name in its values and vectors comes from the matrix it was computed
                # from, and that matrix is also what a set with no closed form draws.
                names |= self._unit_literals_of(value.source_matrix)
        return frozenset(names)

    def _store_kept_value(self, name: str, value) -> None:
        """Give a kept name a number of its own, so an evaluation substitutes the name.

        Without this the substitution stage still reads in primitives. `d` and `a`
        resolve through the shared namespace to their expressions, and what the page
        shows is `cover`, `db_st`, `h`, `b` and `fc` again - the formula stage would say
        `phi As fy (d - a/2)` and the line under it would contradict it.

        Numeric values are consulted before symbolic names, so storing one here is what
        makes `d` substitute as `440.00 mm`. A definition that has no number yet - one
        with a free variable in it, `keep M = q*x**2/2` - simply does not get one, and
        its evaluation behaves as it did before.
        """
        try:
            _, quantity = self.numeric_context.evaluate_symbolic(sp.sympify(value))
        except Exception:
            # A number that can no longer be computed is dropped, not kept: a stale one
            # is a wrong answer given in silence. See `_refresh_kept_values`.
            if name in self.kept_values:
                self.numeric_context.values.pop(name, None)
                self.kept_values.discard(name)
            return
        self.numeric_context.values[name] = self.zero_in_its_unit(name, quantity)
        self.kept_values.add(name)

    def _refresh_kept_values(self) -> None:
        """Take every kept name's number again, from the values settled now.

        It was taken once, when the name was kept. `E := 100*GPa` after `keep a = E*A/L`
        left `a` at the number it had with 200 GPa, and `numeric(2*a)` answered with the
        old `a` while `numeric(a)` answered with the new one - one page, two answers, in
        silence. A name kept before its values were settled had no number at all, and
        `numeric` asked for a value the sheet had given. Called after a value is settled,
        which is the only thing that moves these numbers.
        """
        for name in list(self.kept_names):
            if name in self.namespace:
                self._store_kept_value(name, self.namespace[name])

    def _unit_of_a_zero(self, statement, value):
        """The quantity a definition that simplified to zero is, unit included.

        `M_B = M(L)` substitutes into `q*x*(L - x)/2`, and SymPy simplifies as it
        substitutes: the value is `0` before anything numeric sees it, and a SymPy zero
        has no dimension, so `numeric(M_B)` printed `0.00` beside moments in kN·m. The
        formula as written is evaluated over quantities instead - see
        `_QuantityOfTheFormula` - and Pint keeps the unit through `(6 m) - (6 m)`. Once,
        and only for an exact zero. A zero with no dimension - `f(L)` for
        `f(x) = x/L - 1` - comes back as the plain zero it was.
        """
        if not isinstance(value, sp.Expr) or value.is_zero is not True:
            return None
        # A sheet whose function mixes units - `G(x) = q*x - x` - defines `G(0*m)` as a
        # zero today and must go on doing so; asking for its unit is what would fail.
        try:
            quantity = _QuantityOfTheFormula(self).visit(statement.expression.body)
        except Exception:
            return None
        # `n = 0` evaluates to the Python integer it was written as, which is no quantity.
        return quantity if hasattr(quantity, "units") else None

    def _as_numeric(self, statement) -> "_Evaluator":
        """`numeric(<the statement's right side>)`, evaluated and handed back unread."""
        probe = _Evaluator(self, getattr(statement, "matrix_literals", ()))
        probe.visit(
            ast.Call(
                func=ast.Name(id="numeric", ctx=ast.Load()),
                args=[statement.expression.body],
                keywords=[],
            )
        )
        return probe

    def _calls_a_function_of_the_sheet(self, expression: ast.AST) -> bool:
        return any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in self.functions
            for node in ast.walk(expression)
        )

    def _assign_through_the_sheet(self, statement):
        """The value of `M_max := M(L/2)`, as `numeric(M(L/2))` computes it.

        `NumericContext` evaluates a `:=` over Pint quantities and knows the functions
        mathematics has - `sqrt`, `sin`, `log` - and none the sheet defined, so the cell
        stopped at `unsupported numeric function`. The engine owns those functions and
        the evaluation that substitutes quantities into one, guards and piecewise branches
        included, so it answers and the value is stored as any `:=` value is.
        """
        probe = self._as_numeric(statement)
        if probe.numeric_evaluation is None:
            unresolved = (
                probe.partial_numeric_evaluation[2]
                if probe.partial_numeric_evaluation is not None
                else ()
            )
            if not unresolved:
                raise EngEvaluationError(
                    f"'{statement.target} := ...' needs a single numeric value"
                )
            hint = diagnostic_hint("unresolved_numeric_symbols", names=tuple(unresolved))
            raise EngEvaluationError(
                "numeric evaluation requires values for: " + ", ".join(unresolved) + f". {hint}"
            )
        quantity = probe.numeric_evaluation[2]
        self.numeric_context.values[statement.target] = quantity
        self.numeric_context.matrices.pop(statement.target, None)
        return quantity

    def _image_asked_for(self, statement):
        """`image("portico.png", "Geometría y cargas", width=12*cm)`, read and numbered.

        A path is read from where the notebook runs - in Colab `/content`, or
        `/content/drive/MyDrive/...` with Drive mounted - and a URL is fetched. The number
        belongs to the figure, by file and caption, so running a cell again keeps it; a
        new figure takes the next one, and a reset starts again at 1.
        """
        body = _standalone_call(
            statement,
            "image",
            "image(...) places a figure and stands on its own line, "
            'as in image("portico.png", "Geometría y cargas")',
        )
        if body is None:
            return None
        source = body.args[0].value
        caption = body.args[1].value if len(body.args) > 1 else None
        width_cm = None
        for item in body.keywords:
            width = self.numeric_context.evaluate_expression(ast.Expression(body=item.value))
            try:
                width_cm = float(width.to("cm").magnitude)
            except (AttributeError, DimensionalityError) as exc:
                raise EngEvaluationError(
                    f"image width must be a length, such as 12*cm; {ast.unparse(item.value)} is not"
                ) from exc
        data, mime = _read_image(source)
        return ImageResult(
            statement=statement,
            number=self._figure_number((source, caption)),
            data=data,
            mime=mime,
            caption=caption,
            width_cm=width_cm,
        )

    def _figure_number(self, key: tuple[str, str | None]) -> int:
        """The number of a figure, `image` or `frame_plot` alike: kept across a rerun."""
        if key not in self.figure_numbers:
            self.figure_numbers[key] = len(self.figure_numbers) + 1
        return self.figure_numbers[key]

    def _member_asked_for(self, statement):
        """`member("V", start=[0*m, h], end=[L, h], forces=f_v, ...)`: a member declared.

        Nothing is solved here: the sheet worked the frame out, and this keeps what it
        found - geometry, local end forces, local end displacements, EI and a uniform load -
        for `frame_plot` to draw. Declaring a name again replaces that member in its place,
        so a cell run again draws the same frame.
        """
        body = _standalone_call(
            statement,
            "member",
            'member(...) declares a member of a frame and stands on its own line, '
            'as in member("V", start=[0*m, h], end=[L, h], forces=f_v)',
        )
        if body is None:
            return None
        name = body.args[0].value
        given = {item.arg: item.value for item in body.keywords}
        numbers = _MatrixNumbers(self, statement)
        ureg = self.numeric_context.ureg

        def scalar(node, what: str, dimension: str, meaning: str):
            try:
                value = numbers.value(node)
            except DimensionalityError as exc:
                raise EngEvaluationError(f"member {name}: {what} has incompatible units") from exc
            if isinstance(value, NumberMatrix):
                raise EngEvaluationError(
                    f"member {name}: {what} is one value, and {ast.unparse(node)} is a matrix"
                )
            quantity = self.numeric_context._as_quantity(value)
            # A bare `0` fits anything; `0*kgf` said what it is.
            if not (quantity.magnitude == 0 and quantity.dimensionless) and not quantity.check(dimension):
                raise EngEvaluationError(
                    f"member {name}: {what} is {meaning}; {ast.unparse(node)} is "
                    f"{quantity.units:~P}"
                )
            return quantity

        def point(which: str):
            return tuple(
                scalar(element, which, "[length]", "two lengths [x, y]")
                for element in given[which].elts
            )

        start, end = point("start"), point("end")
        if all(
            (b - a).to_base_units().magnitude == 0 for a, b in zip(start, end)
        ):
            raise EngEvaluationError(
                f"member {name} has no length: start and end are the same point"
            )

        def six(which: str, kinds: tuple[str, ...], order: str):
            node = given.get(which)
            if node is None:
                return None
            try:
                value = numbers.value(node)
            except DimensionalityError as exc:
                raise EngEvaluationError(f"member {name}: {which} has incompatible units") from exc
            shape = (value.rows, value.cols) if isinstance(value, NumberMatrix) else (1, 1)
            if shape not in ((6, 1), (1, 6)):
                raise EngEvaluationError(
                    f"member {name}: {which} has 6 entries, {order}; "
                    f"{ast.unparse(node)} is {shape[0]}×{shape[1]}"
                )
            matrix = quantity_matrix_of(value, ureg)
            for index, entry in enumerate(matrix):
                quantity = self.numeric_context._as_quantity(entry)
                kind = kinds[index % 3]
                fits = quantity.dimensionless if not kind else quantity.check(kind)
                if not (quantity.magnitude == 0 and quantity.dimensionless) and not fits:
                    raise EngEvaluationError(
                        f"member {name}: {which} entry {index + 1} is "
                        f"{quantity.units:~P}, which does not fit {order}"
                    )
            return matrix

        # `load=w`, or `load=[w_1, w_2]` running linearly from start to end.
        loads = (None, None)
        if "load" in given:
            written = given["load"]
            ends = written.elts if isinstance(written, ast.List) else [written]
            values = [
                scalar(end_value, "load", "[force] / [length]", "a force per length")
                for end_value in ends
            ]
            loads = (values[0], values[1] if len(values) == 2 else None)

        # `point=[P, a]`, one row per load: P towards -y' at a from start.
        points = []
        if "point" in given:
            node = given["point"]
            if isinstance(node, ast.List):
                # `[P, a]`, one load: its two values, read as any value on the line is.
                pairs = [tuple(numbers.value(element) for element in node.elts)]
            else:
                try:
                    value = numbers.value(node)
                except DimensionalityError as exc:
                    raise EngEvaluationError(f"member {name}: point has incompatible units") from exc
                if not isinstance(value, NumberMatrix) or value.cols != 2:
                    raise EngEvaluationError(
                        f"member {name}: point is [P, a], a load and its distance from start; "
                        "several are rows, [P_1, a_1; P_2, a_2]"
                    )
                rows = quantity_matrix_of(value, ureg)
                pairs = [(rows.entry(row, 0), rows.entry(row, 1)) for row in range(rows.rows)]
            span = math.hypot(*(float((b - a).to_base_units().magnitude) for a, b in zip(start, end)))
            for row, (force, where) in enumerate(pairs):
                force = self.numeric_context._as_quantity(force)
                where = self.numeric_context._as_quantity(where)
                if not force.check("[force]"):
                    raise EngEvaluationError(
                        f"member {name}: point load {row + 1} is {force.units:~P}, not a force"
                    )
                if not (where.magnitude == 0 and where.dimensionless) and not where.check("[length]"):
                    raise EngEvaluationError(
                        f"member {name}: point {row + 1} is at {where.units:~P}; its distance "
                        "from start is a length"
                    )
                distance = float(where.to_base_units().magnitude)
                if not 0 <= distance <= span * (1 + 1e-12):
                    unit = where.units if not where.dimensionless else ureg.meter
                    raise EngEvaluationError(
                        f"member {name}: point {row + 1} at {float(where.to(unit).magnitude):g} "
                        f"{unit:~P} is off the member, which is "
                        f"{ureg.Quantity(span, 'm').to(unit).magnitude:g} {unit:~P} long"
                    )
                points.append((force, where))
        points = tuple(points)

        member = FrameMember(
            name=name,
            start=start,
            end=end,
            forces=six(
                "forces",
                ("[force]", "[force]", "[force] * [length]"),
                "[N_i; V_i; M_i; N_j; V_j; M_j]",
            ),
            displacements=six(
                "displacements",
                ("[length]", "[length]", ""),
                "[u_i; v_i; θ_i; u_j; v_j; θ_j]",
            ),
            stiffness=(
                scalar(given["EI"], "EI", "[force] * [length] ** 2", "a force times a length squared")
                if "EI" in given
                else None
            ),
            load=loads[0],
            load_end=loads[1],
            points=points,
        )
        self.frame_members[name] = member
        return MemberResult(statement=statement, member=member)

    def _frame_plot_asked_for(self, statement):
        """`frame_plot(M, "Momento flector")`: a diagram of the members declared."""
        body = _standalone_call(
            statement,
            "frame_plot",
            "frame_plot(...) draws a figure and stands on its own line, "
            'as in frame_plot(M, "Momento flector")',
        )
        if body is None:
            return None
        diagram = body.args[0].id
        caption = body.args[1].value if len(body.args) > 1 else None
        written = ast.unparse(body)
        members = tuple(self.frame_members.values())
        if not members:
            raise EngEvaluationError(
                f"{written} draws the members declared with member(...), and none is "
                'declared yet: member("V", start=[0*m, h], end=[L, h], forces=f_v)'
            )
        needed = "displacements" if diagram == "deformed" else "forces"
        missing = [member.name for member in members if getattr(member, needed) is None]
        if missing:
            raise EngEvaluationError(
                f"{written} needs {needed}= on every member; "
                f"{', '.join(missing)} {'has' if len(missing) == 1 else 'have'} none"
            )
        if diagram == "deformed":
            unbending = [
                member.name
                for member in members
                if (member.load is not None or member.points) and member.stiffness is None
            ]
            if unbending:
                raise EngEvaluationError(
                    f"{written} needs EI= on {', '.join(unbending)}, to bend it under its load"
                )
        scale = next((float(item.value.value) for item in body.keywords), None)
        return FramePlotResult(
            statement=statement,
            diagram=diagram,
            number=self._figure_number((f"frame_plot({diagram})", caption)),
            members=members,
            caption=caption,
            scale=scale,
        )

    def _numbers_asked_for(self, statement):
        """`numeric(d)` or `numeric(d, cm)` of a matrix defined with `:=`: its numbers.

        There is no formula behind them to substitute into - that is what `:=` means -
        so the page writes the name and the value, as the `:=` line did.
        """
        body = statement.expression.body
        if not (
            statement.target is None
            and isinstance(body, ast.Call)
            and isinstance(body.func, ast.Name)
            and body.func.id == "numeric"
            and not body.keywords
            and len(body.args) in (1, 2)
            and isinstance(body.args[0], ast.Name)
        ):
            return None
        name = body.args[0].id
        context = self.numeric_context
        if (
            name not in context.matrices
            or name in self.namespace
            or context.get(name) is not None
        ):
            return None
        quantity_matrix = context.matrices[name]
        requested = len(body.args) == 2
        if requested:
            unit = context.evaluate_unit_expression(ast.Expression(body=body.args[1]))
            entries = []
            for index, entry in enumerate(quantity_matrix):
                position = divmod(index, quantity_matrix.cols)
                if position in quantity_matrix.adaptable_zeros:
                    entries.append(context.ureg.Quantity(0, unit))
                    continue
                try:
                    entries.append(entry.to(unit))
                except DimensionalityError as exc:
                    row, col = position
                    written = ast.unparse(body.args[1])
                    # Three figures, as a reader would quote it; a rotation says it has
                    # no unit rather than printing nothing after the number.
                    value = f"{float(entry.magnitude):.3g}"
                    value += (
                        ", a number without a unit"
                        if entry.dimensionless
                        else f" {entry.units:~P}"
                    )
                    raise EngEvaluationError(
                        f"numeric({name}, {written}): entry [{row + 1},{col + 1}] is "
                        f"{value}, which cannot be written in {written}"
                    ) from exc
            quantity_matrix = QuantityMatrix(
                quantity_matrix.rows, quantity_matrix.cols, tuple(entries)
            )
        shown = ParsedNumericAssignment(
            line_no=statement.line_no,
            source=statement.source,
            target=name,
            expression=ast.Expression(body=ast.Name(id=name, ctx=ast.Load())),
        )
        return NumericMatrixAssignmentResult(
            statement=shown,
            quantity_matrix=quantity_matrix,
            matrix_names=frozenset({name}),
            unit_was_requested=requested,
        )

    def _assign_numbers(self, statement, numbers: "_MatrixNumbers", written_units):
        """`d := solve(K, F)` and `u := d[2,1]`: a line that reads a matrix, in numbers.

        A matrix is kept in `numeric_context.matrices`, apart from the scalars, so that
        nothing that reads a scalar value can be handed a matrix; one entry taken out of
        it is a scalar like any other `:=` value, and a `numeric` line can use it.
        """
        context = self.numeric_context
        try:
            value = numbers.value(statement.expression.body)
        except DimensionalityError as exc:
            raise EngEvaluationError("incompatible units") from exc
        for binding in statement.matrix_literals:
            for row in binding.literal.rows:
                for cell in row:
                    written_units |= context.written_unit_names(cell)
        matrix_names = frozenset(
            node.id
            for node in ast.walk(statement.expression)
            if isinstance(node, ast.Name)
            and node.id not in numbers.literals
            and numbers.names_a_matrix(node.id)
        )
        if isinstance(value, NumberMatrix):
            quantity_matrix = quantity_matrix_of(value, context.ureg)
            context.values.pop(statement.target, None)
            context.matrices[statement.target] = quantity_matrix
            # `K = [...]` then `K := solve(K, F)`: the formula goes, or a `=` line after it
            # goes on reading the old K in silence.
            for store in (self.namespace, self.written_namespace, self.numeric_guards):
                store.pop(statement.target, None)
            self.zero_quantities.pop(statement.target, None)
            self.kept_names.discard(statement.target)
            self.kept_values.discard(statement.target)
            return NumericMatrixAssignmentResult(
                statement=statement,
                quantity_matrix=quantity_matrix,
                written_units=written_units,
                matrix_names=matrix_names,
            )
        quantity = context._as_quantity(value)
        context.matrices.pop(statement.target, None)
        context.values[statement.target] = quantity
        return NumericAssignmentResult(
            statement=statement,
            quantity=quantity,
            written_units=written_units,
            shown_as_written=True,
            matrix_names=matrix_names,
        )

    def zero_in_its_unit(self, name: str, quantity):
        """`quantity`, or the zero `name` was defined as when the arithmetic lost its unit."""
        zero = self.zero_quantities.get(name)
        if zero is None or not getattr(quantity, "dimensionless", False):
            return quantity
        return zero

    def _shows_its_written_form(self, name: str) -> bool:
        """True when this name should be shown as it was written rather than expanded.

        `written_namespace` has held each name's written form - the expression with its
        kept names still standing - since RC-3, and only `numeric(name)` was reading it.
        Reading it here is what lets the barrier survive more than one step: a name that
        is not itself kept can be replaced by its written form, and the kept names inside
        come through to the next formula, and the one after that.

        **Only on a sheet that uses `keep` at all.** That is the whole containment, and
        it is what keeps this opt-in: a sheet with no `keep` in it renders exactly as
        before, because the guard in `_written_form` still fires there.

        A first version asked the narrower question - whether *this* name's written form
        holds a kept name - and it did not survive being measured. Twenty-two sheets
        render identically either way, including all four in the repository that use
        `keep`; the one case that separates them was built on purpose from the README's
        own example, and the narrow answer is the worse one:

            narrow:  phiMn = fy phi As (-1.18 fy As / (2 b fc) + d)
            wide:    phiMn = fy phi As (-fy As / (2 0.85 b fc) + d)

        The 0.85 is ACI 318 §22.2.2.4.1, and "a coefficient written in a denominator
        stays there" is the change this repository made one release before RC-3. The
        narrow rule folded it back into a 1.18 one formula further down.
        """
        if not self.kept_names:
            return False
        return self.written_namespace.get(name) is not None

    def _reaches_a_kept_name(self, expression) -> bool:
        """True when this statement mentions a kept name, directly or through one."""
        for node in ast.walk(expression):
            if not isinstance(node, ast.Name):
                continue
            if node.id in self.kept_names or self._shows_its_written_form(node.id):
                return True
        return False

    def _shown_input(self, statement, evaluator):
        """The formula a row shows beside its value: the whole statement, never a part.

        A derivative or an integral leaves its unevaluated form in one slot for the row
        to show. When the call is the statement, that form is the formula. When it sits
        inside something larger the slot held only the last call, and the page printed
        equations that were false: `y = 2*diff(x^2, x)` read `y = d/dx x^2 = 4x`, and a
        matrix of derivatives read as the last one. The statement is then read a second
        time with every derivative and integral left standing - the second reading the
        written form already makes - and a statement that cannot be read so shows its
        value alone rather than a formula that is not its own.
        """
        body = statement.expression.body
        called = self._call_of_the_sheet_shown(statement)
        if called is not None:
            return called
        shown = evaluator.display_input
        if shown is None:
            return None
        if isinstance(body, ast.Call) and getattr(body.func, "id", None) in _CALLS_THAT_SHOW:
            return shown
        reader = _Evaluator(self, getattr(statement, "matrix_literals", ()))
        reader.showing = True
        reader.answered = evaluator.answered
        try:
            if statement.parameters is not None:
                return reader.visit_function_body(body, statement.parameters)
            return reader.visit(body)
        except Exception:
            return None

    def _call_of_the_sheet_shown(self, statement):
        """`M_u = U1(L/2)`: the call, as the row's first formula, before what it expands to.

        The row read `M_u = 0.15 qD L^2 + 0.2 qL L^2`, and which combination and where
        were gone from the page. Only a named line whose whole right side is one call to a
        function or combination of the sheet; see `test_a_call_of_the_sheet_is_written`.
        """
        body = statement.expression.body
        if not (
            statement.target is not None
            and statement.parameters is None
            and isinstance(body, ast.Call)
            and isinstance(body.func, ast.Name)
            and body.func.id in self.functions
            and not body.keywords
        ):
            return None
        # Read as written, or `G(0*m)` is shown as `G(0)`: SymPy folds `0*m` to a bare zero.
        reader = _WrittenFormEvaluator(self, getattr(statement, "matrix_literals", ()))
        reader.showing = True
        try:
            arguments = [reader.visit(argument) for argument in body.args]
        except Exception:
            return None
        if any(is_matrix(argument) for argument in arguments):
            return None
        return sp.Function(body.func.id)(*arguments)

    def _written_form(self, statement, evaluator, value):
        """The definition's expression as it was typed, or None to show the evaluated one.

        Returned only for a plain scalar definition whose calls are pure arithmetic. The
        written pass is the evaluator run a second time, so a statement that plots,
        summarises or solves would do that work twice and record its effects twice; the
        safe-call list is what keeps this to expressions where a second walk is free of
        consequence.

        None on anything unexpected, and None when the result does not verify. A formula
        the reader cannot check against the code is the defect being fixed here; a
        formula that is simply wrong would be worse than the defect.
        """
        # No guard here for a statement that plots or summarises. One was written, and
        # turning it into a raise fired it zero times across the whole suite: both of
        # those return their own result before this is reached, so the branch could not
        # be told apart from its absence.
        # `sp.Expr` already admits a matrix: `build_matrix` returns an
        # `ImmutableMatrix`, whose ancestry runs through `MatrixExpr` to `Expr`. This
        # line was widened to `(sp.Expr, sp.MatrixBase)` first, with a comment claiming
        # it was what had kept the written form out of matrices; mutation showed the
        # widening changed nothing, and it is not here.
        if not isinstance(value, sp.Expr):
            return None
        carries_kept = self._reaches_a_kept_name(statement.expression)
        for node in ast.walk(statement.expression):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None)
                if name not in _WRITTEN_FORM_SAFE_CALLS and name not in self.written_functions:
                    return None
            # A name already bound to a symbolic definition is substituted here, and
            # what arrives is an expression SymPy has already evaluated. The written
            # form that results is *wider* than the evaluated one - it keeps
            # `1.18 fy As / (2 b fc)` where evaluation folds the halving into
            # `0.59 fy As / (b fc)` - and width is not cosmetic here: it tips the row
            # past the wrapping budget, and the wrapping path splits a product into
            # additive terms. Measured on a real sheet, `phi*As*fy*(d - a/2)` stops
            # being a product of four factors and becomes two rows of expanded terms.
            #
            # An earlier draft of this comment blamed `(-1)` and separate `1/b`, `1/fc`
            # fractions. That was `sp.latex`; the renderer's own printer collects those
            # denominators correctly, and the reason above is what the page shows.
            #
            # So a written form is offered only where every name stands for itself -
            # *unless* this statement reaches a kept name, which is the case the guard
            # was silently costing. Abandoning the written form falls back on the fully
            # evaluated expression, and that expression has the kept names expanded
            # inside it, so the branch written to keep a page narrow was the one
            # throwing the barrier away. On the frame benchmark it printed `A_1` in
            # `x_1, x_2, y_1, y_2` where `R_1` one line above printed `c_c` and `s_c`,
            # and it is why the assembled stiffness matrix runs off the side of the page.
            #
            # The measurement behind the guard still stands, and a sheet with no `keep`
            # in it renders exactly as before: `carries_kept` is False there and this
            # returns None as it always did.
            if (
                not carries_kept
                and isinstance(node, ast.Name)
                and node.id in self.namespace
                and node.id not in self.kept_names
            ):
                return None
        try:
            writer = _WrittenFormEvaluator(
                self, getattr(statement, "matrix_literals", ())
            )
            if statement.parameters is not None:
                written = writer.visit_function_body(
                    statement.expression.body, statement.parameters
                )
            else:
                written = writer.visit(statement.expression.body)
        except Exception:
            return None
        if not isinstance(written, sp.Expr):
            return None
        expansions = {
            self.resolve_symbol(name): self.namespace[name]
            for name in self.kept_names
            if name in self.namespace
        }
        if not _agrees_with(written, value, expansions):
            return None
        return written

    def _declare_load(self, statement, evaluator):
        """`case D = ...` and `combo U1 = 1.2*D + 1.6*L`.

        A combination keeps its terms as written. Defined as an ordinary function,
        `U1(x) = 1.2*D(x) + 1.6*Lv(x)` renders as `0.6*qD*x*(L - x) + 0.8*qL*x*(L - x)`:
        the same number and no longer a load combination, so nobody can check 1.2 and
        1.6 against the code that requires them. The expanded form is kept beside the
        terms for everything else to use.
        """
        name = statement.target
        if name is None:
            raise EngEvaluationError(
                f"{statement.declaration} needs a name, as in "
                f"{statement.declaration} D = M_D(x)"
            )
        if name in self.functions or name in self.namespace:
            raise EngEvaluationError(
                f"redefinition conflict: '{name}' is already defined"
            )

        if statement.declaration == "case":
            expression = evaluator.visit(statement.expression.body)
            variable = self._case_variable(expression, f"a load case, '{name}',")
            self.functions[name] = UserFunction(
                parameters=(variable,),
                expression=sp.sympify(expression),
            )
            self.load_cases[name] = variable
            return LoadCaseResult(
                statement=statement,
                name=name,
                variable=variable,
                expression=sp.sympify(expression),
            )

        if not self.load_cases:
            raise EngEvaluationError(
                "a combination is built from load cases; declare one first, as in "
                "case D = M_D(x)"
            )

        # The case names stay free symbols here, so the written terms survive.
        previous = {
            case: evaluator.symbol_overrides.get(case) for case in self.load_cases
        }
        evaluator.symbol_overrides.update(
            {case: sp.Symbol(case) for case in self.load_cases}
        )
        try:
            written = sp.sympify(evaluator.visit(statement.expression.body))
        finally:
            for case, value in previous.items():
                if value is None:
                    evaluator.symbol_overrides.pop(case, None)
                else:
                    evaluator.symbol_overrides[case] = value

        used = [case for case in self.load_cases if written.has(sp.Symbol(case))]
        if not used:
            raise EngEvaluationError(
                f"'{name}' names no load case; the ones declared are "
                + ", ".join(sorted(self.load_cases))
            )

        variables = {self.load_cases[case] for case in used}
        if len(variables) > 1:
            raise EngEvaluationError(
                "the cases in a combination must share one variable; found "
                + ", ".join(sorted(variables))
            )
        variable = variables.pop()

        terms = tuple((written.coeff(sp.Symbol(case)), case) for case in used)
        rebuilt = sum(
            factor * sp.Symbol(case) for factor, case in terms
        )
        if sp.simplify(written - rebuilt) != 0:
            raise EngEvaluationError(
                "a combination is a sum of factored load cases, as in "
                "combo U1 = 1.2*D + 1.6*L"
            )

        # Kept for its side effect: it registers the variable's symbol, with its
        # assumptions, if the sheet has not used it yet. The symbol itself is not needed.
        self.resolve_symbol(variable)
        expanded = written.subs(
            {
                sp.Symbol(case): self.functions[case].expression
                for case in used
            }
        )
        self.functions[name] = UserFunction(
            parameters=(variable,),
            expression=sp.sympify(expanded),
        )
        self.load_cases[name] = variable
        return LoadCombinationResult(
            statement=statement,
            name=name,
            variable=variable,
            terms=terms,
            expression=sp.sympify(expanded),
        )

    def reset(self) -> None:
        self.namespace.clear()
        self.reported.clear()
        self.load_cases.clear()
        self.kept_names.clear()
        self.kept_values.clear()
        self.declared_unit_names.clear()
        self.written_units.clear()
        self.written_namespace.clear()
        self.functions.clear()
        self.symbols.clear()
        self.numeric_guards.clear()
        self.names_read_as_units.clear()
        self.measured_units.clear()
        self.written_order.clear()
        self.letters_written_as_units.clear()
        self.letters_said_to_be_units.clear()
        self.units_read_by_line.clear()
        self.figure_numbers.clear()
        self.frame_members.clear()
        self.written_functions.clear()
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

    def evaluate(self, statement: ParsedStatement | ParsedNumericAssignment):
        """One statement, a note of every alias it read as a unit, and what that means.

        `N`, `m` and `s` are aliases and ordinary names at once, and a stored value
        outranks the alias - `N := 500*kN` must make `N` the axial force. That stays. It
        had no voice: `k := 2000*kN/m` then `m := 500*kg` is the usual way to write one
        degree of freedom, and running that cell again made `k` 4.00 kN/kg in silence.
        Two moments are said aloud, and nothing else changes:

        - a name read as a unit is given a value (`_notice_a_unit_becoming_a_value`);
        - a line that read a name as a unit reads it as a value now, which is the
          re-run that changed its result.

        A statement that fails reads nothing the sheet goes on with, and says nothing.
        """
        self.notices = []
        result = self._evaluate_statement(statement)
        # What the line writes - the units it measures, the order of its products - is
        # taken only once it has evaluated. Taken before, a line that then failed left it
        # behind for the rest of the session: `q = 3*s + nofunc(1)` made the `s` of a
        # later rotation matrix a second. The printer reads both after this returns.
        expression = getattr(statement, "expression", None)
        if expression is not None:
            self.measured_units |= measured_units_in(expression)
            self.letters_written_as_units |= letters_written_as_units_in(expression)
            record_written_order(expression, self.written_order)
        # A matrix written `[a, b; c, d]` keeps its entries apart from the statement's own
        # tree, and a stiffness matrix is where `-1*kN/m` is most often written.
        for binding in getattr(statement, "matrix_literals", ()):
            for row in binding.literal.rows:
                for entry in row:
                    self.measured_units |= measured_units_in(entry)
                    self.letters_written_as_units |= letters_written_as_units_in(entry)
                    record_written_order(entry, self.written_order)
        # A settled value moves the numbers kept names stand for.
        if isinstance(statement, ParsedNumericAssignment) and self.kept_names:
            self._refresh_kept_values()
        read = frozenset(getattr(result, "unit_literals", ())) | frozenset(
            getattr(result, "written_units", ())
        )
        source = getattr(statement, "source", None)
        if source is not None:
            before = self.units_read_by_line.get(source, frozenset())
            # The same line stops reading an alias as a unit for one reason only: the
            # name holds a value now, which is the whole of the precedence rule.
            for name in sorted(before - read):
                self.notices.append(
                    f"line {statement.line_no}: this line read '{name}' as a unit "
                    f"({_UNIT_ALIASES[name]}) when it ran before, and reads it as a "
                    f"value now, so its result is not the one it had. Give the value "
                    f"another name, such as {name}_1, to keep both."
                )
            self.units_read_by_line[source] = before | read
        self.names_read_as_units |= read
        for name in sorted(read):
            said = self._notice_a_letter_read_as_a_unit(name, statement)
            if said is not None:
                self.notices.append(said)
        return result

    def _notice_a_letter_read_as_a_unit(self, name: str, statement) -> str | None:
        """What to say when a line reads `N`, `m` or `s` as a unit nobody wrote as one.

        `A := 500*mm^2` then `sigma = N/A` gave 0.002 MPa for an axial force the sheet
        forgot to define: `N` was one newton, and nothing said so. Said once per letter,
        and only where the sheet has not written the letter as a unit anywhere - next to a
        number or another unit, `30*N`, `2*m`, `4*kN*x/m` - which is where it plainly is one.
        """
        if (
            len(name) != 1
            or name not in _UNIT_ALIASES
            or name in self.letters_written_as_units
            or name in self.letters_said_to_be_units
        ):
            return None
        self.letters_said_to_be_units.add(name)
        return (
            f"line {statement.line_no}: '{name}' is read as a unit ({_UNIT_ALIASES[name]}), "
            f"and nothing on the sheet writes it as one. If it is a quantity, give it a "
            f"value first ({name} := ...) or another name, such as {name}_1."
        )

    def _notice_a_unit_becoming_a_value(self, statement) -> str | None:
        """What to say when a name that was read as a unit is given a value.

        Only when this session has already read the name as a unit, because only then
        does one name mean two things; and only when it first gets a value, because the
        re-run of the same assignment is the same news.
        """
        name = statement.target
        if (
            name not in _UNIT_ALIASES
            or name not in self.names_read_as_units
            or self.numeric_context.get(name) is not None
        ):
            return None
        return (
            f"line {statement.line_no}: '{name}' has been read as a unit "
            f"({_UNIT_ALIASES[name]}); from here on it is this value wherever it is "
            f"written, and a line that used the unit reads the value when it is "
            f"evaluated again. Give the value another name, such as {name}_1, to keep both."
        )

    def _evaluate_statement(
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
            declaration = getattr(statement, "declaration", None)
            if declaration is not None and declaration != "keep":
                return self._declare_load(statement, evaluator)
            # `keep` is an ordinary definition with a mark on it, so it falls through
            # to the path below rather than getting a branch of its own. What the mark
            # changes is presentation: the name stays a name in a later formula instead
            # of being replaced by what it stands for. Everything computes with the
            # expanded expression exactly as it did before, which is what makes an
            # opt-in barrier possible without dividing the language in two.
            if declaration == "keep":
                self.kept_names.add(statement.target)

            if isinstance(statement, ParsedNumericAssignment):
                # The same conflict a symbolic assignment has always refused, from the
                # other side. `a(x) = x` then `a := 2*m` left the sheet with `a` as a
                # length *and* a function of x, and said nothing.
                if statement.target in self.functions:
                    raise EngEvaluationError(
                        f"redefinition conflict: '{statement.target}' is already a function"
                    )
                # Before the assignment, not after: `assign` stores the target, and a
                # name this statement is defining must not read back as a value the
                # arithmetic never saw.
                written_units = self.numeric_context.written_unit_names(
                    statement.expression
                )
                # `discard` and not just `add`: redefining a name without a unit -
                # `d := 0.0105*m` then `d := As*fy/b` - must stop protecting it.
                if written_units:
                    self.declared_unit_names.add(statement.target)
                else:
                    self.declared_unit_names.discard(statement.target)
                self.zero_quantities.pop(statement.target, None)
                notice = self._notice_a_unit_becoming_a_value(statement)
                if notice:
                    self.notices.append(notice)
                numbers = _MatrixNumbers(self, statement)
                if numbers.reads_a_matrix(statement.expression.body) or isinstance(
                    statement.expression.body, ast.List
                ):
                    return self._assign_numbers(statement, numbers, written_units)
                if self._calls_a_function_of_the_sheet(statement.expression):
                    quantity = self._assign_through_the_sheet(statement)
                else:
                    quantity = self.numeric_context.assign(
                        statement.target,
                        statement.expression,
                    )
                if written_units:
                    try:
                        self.written_units.add(str(quantity.units))
                    except AttributeError:
                        pass
                return NumericAssignmentResult(
                    statement=statement,
                    quantity=quantity,
                    written_units=written_units,
                )

            if statement.target is not None:
                if statement.parameters is None and statement.target in self.functions:
                    raise EngEvaluationError(
                        f"redefinition conflict: '{statement.target}' is already a function"
                    )
                # `self.namespace` holds the symbolic scalars and `numeric_context` the
                # numeric ones, and this asked only the first. `a := 2*m` then
                # `a(x) = x` was accepted in silence, and the page then showed `a` as
                # `2.00 m`, as `a(x) = x^2`, and as `a = a`.
                if statement.parameters is not None and (
                    statement.target in self.namespace
                    or self.numeric_context.get(statement.target) is not None
                ):
                    raise EngEvaluationError(
                        f"redefinition conflict: '{statement.target}' is already a scalar"
                    )

            if getattr(statement, "target_index", None) is not None:
                return self._assign_part(statement, evaluator)

            shown = self._numbers_asked_for(statement)
            if shown is not None:
                return shown

            figure = self._image_asked_for(statement)
            if figure is not None:
                return figure

            declared = self._member_asked_for(statement)
            if declared is not None:
                return declared

            diagram = self._frame_plot_asked_for(statement)
            if diagram is not None:
                return diagram

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

            if evaluator.summary_evaluation is not None:
                if statement.target is not None:
                    raise EngEvaluationError(
                        "summary must be a standalone statement"
                    )
                return SummaryResult(
                    statement=statement,
                    entries=evaluator.summary_evaluation,
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

            if evaluator.inequality_evaluation is not None:
                variable, relation, domain, intervals, difference, sides = (
                    evaluator.inequality_evaluation
                )
                if statement.target is not None:
                    raise EngEvaluationError(
                        "an inequality answers with a region rather than a value, so "
                        "it cannot be assigned to a name; read the intervals"
                    )
                return InequalityResult(
                    statement=statement,
                    display_label=str(difference),
                    variable=variable,
                    relation=relation,
                    lower_quantity=domain.lower_quantity,
                    upper_quantity=domain.upper_quantity,
                    intervals=intervals,
                    left_label=sides[0],
                    right_label=sides[1],
                    left_expression=sides[2],
                    right_expression=sides[3],
                    unit_literals=sides[4],
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
                    discarded=system.discarded,
                    unit_literals=self._unit_literals_of(
                        *system.equations,
                        *(value for _, value in system.solutions),
                        *(system.discarded.values if system.discarded else ()),
                    ),
                    quantities=(
                        tuple(self._solution_quantity(value) for _, value in system.solutions)
                        if system.kind == "multi"
                        else ()
                    ),
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
                        label_expression=characteristic.label_expression,
                        unit_literals=self._unit_literals_of(
                            *(
                                expression
                                for point in characteristic.points
                                for expression in (point.x_symbolic, point.value_symbolic)
                                if expression is not None
                            )
                        ),
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
                        left_expression=characteristic.left_expression,
                        right_expression=characteristic.right_expression,
                        unit_literals=self._unit_literals_of(
                            *(
                                expression
                                for point in characteristic.points
                                for expression in (point.x_symbolic, point.value_symbolic)
                                if expression is not None
                            )
                        ),
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
                        label_expression=characteristic.label_expression,
                        unit_literals=self._unit_literals_of(
                            *(
                                expression
                                for point in characteristic.points
                                for expression in (point.x_symbolic, point.value_symbolic)
                                if expression is not None
                            )
                        ),
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
                    declared_names=frozenset(self.declared_unit_names),
                    unit_was_requested=evaluator.requested_unit is not None,
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
                    declared_names=frozenset(self.declared_unit_names),
                    unit_was_requested=evaluator.requested_unit is not None,
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
                    unit_literals=self._unit_literals_of(
                        symbolic_expression, *(display_arguments or ())
                    ),
                    declared_names=frozenset(self.declared_unit_names),
                    unit_was_requested=evaluator.requested_unit is not None,
                )

            if evaluator.numeric_evaluation is not None:
                (
                    symbolic_expression,
                    substitutions,
                    quantity,
                    display_name,
                    display_arguments,
                ) = evaluator.numeric_evaluation
                if evaluator.report_request is not None:
                    if statement.target is not None:
                        raise EngEvaluationError(
                            "report must be a standalone statement; its value is shown "
                            "where it is written"
                        )
                    # Assigning to the same key keeps the row where the reader first
                    # saw it. A recomputed result is the same result, not a second row,
                    # and a correction belongs in place rather than at the bottom.
                    self.reported[evaluator.report_request] = quantity
                return NumericEvaluationResult(
                    statement=statement,
                    symbolic_expression=symbolic_expression,
                    substitutions=substitutions,
                    quantity=quantity,
                    display_name=display_name,
                    display_arguments=display_arguments,
                    unit_literals=self._unit_literals_of(
                        symbolic_expression, *(display_arguments or ())
                    ),
                    declared_names=frozenset(self.declared_unit_names),
                    unit_was_requested=evaluator.requested_unit is not None,
                    # The substitutions are the overrides: they are exactly the values
                    # this row was evaluated with, the argument bound to the interval
                    # variable among them, so the branches resolve to the numbers the row
                    # already shows. A requested target unit is deliberately not applied -
                    # a zero follows the neighbours it is read against, and those are
                    # shown in the unit they were substituted in.
                    piecewise_branch_values=self.numeric_context.piecewise_branch_values(
                        symbolic_expression,
                        overrides=substitutions,
                    ),
                    extremum_values=self.numeric_context.extremum_values(
                        symbolic_expression,
                        overrides=substitutions,
                    ),
                    interpolation_values=self.numeric_context.interpolation_values(
                        symbolic_expression,
                        overrides=substitutions,
                    ),
                )

            # The formula is read before the name is stored: read after, `v = v + 2*diff(t^2, t)`
            # showed the new `v` inside the formula that defines it.
            shown = self._shown_input(statement, evaluator)
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
                    self.numeric_context.matrices.pop(statement.target, None)
                    zero = self._unit_of_a_zero(statement, value)
                    if zero is None:
                        self.zero_quantities.pop(statement.target, None)
                    else:
                        self.zero_quantities[statement.target] = zero
                    if declaration == "keep":
                        self._store_kept_value(statement.target, value)
                    written_form = self._written_form(statement, evaluator, value)
                    if written_form is None:
                        self.written_namespace.pop(statement.target, None)
                    else:
                        self.written_namespace[statement.target] = written_form
                    if evaluator.numeric_guards:
                        self.numeric_guards[statement.target] = tuple(evaluator.numeric_guards)
                    else:
                        self.numeric_guards.pop(statement.target, None)
            if statement.target is None:
                written = self._written_form(statement, evaluator, value)
            elif statement.parameters is None:
                written = self.written_namespace.get(statement.target)
            elif self._reaches_a_kept_name(statement.expression):
                # A function that reads a kept name is written as typed, or `f_cw` in
                # `As_req(Mu)` is expanded and 2/0.85 folded into 2.35. Any other function
                # prints as it always has. See `test_a_kept_name_survives_a_sheet_function`.
                written = self._written_form(statement, evaluator, value)
            else:
                written = None
            if statement.target is not None and statement.parameters is not None:
                if written is None:
                    self.written_functions.pop(statement.target, None)
                else:
                    self.written_functions[statement.target] = written
            return EvaluationResult(
                statement=statement,
                display_input=shown,
                value=value,
                discarded=evaluator.discarded_solutions,
                written=written,
                # Every form the row can print. `n = 6*m/(2*m)` is worth 3 and is shown
                # as written, so asked of the value alone its metres were set as variables.
                unit_literals=self._unit_literals_of(value, shown, written),
                solved_for=evaluator.solved_for,
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
        # Set for the second reading of `_shown_input`: a derivative or an integral
        # returns its unevaluated form, so the statement comes back as it is written.
        self.showing = False
        # Each `solve` call's answer, by the call's node, so the second reading reuses it
        # rather than solving the same equation again. See `visit_Call`.
        self.answered: dict[int, object] = {}
        self.solved_for = None
        self.numeric_evaluation = None
        # Set when `numeric(expr, unit)` named a unit. `convert_quantity` already
        # stores the result in it; the renderer needs to know it was *asked for*,
        # because a unit a family also knows was being overruled by the family.
        self.requested_unit = None
        self.partial_numeric_evaluation = None
        self.numeric_matrix_evaluation = None
        self.partial_matrix_numeric_evaluation = None
        self.plot_evaluation: _PlotEvaluation | None = None
        self.table_evaluation: _TableEvaluation | None = None
        self.characteristic_evaluation: _CharacteristicEvaluation | None = None
        self.system_evaluation: _SystemSolveEvaluation | None = None
        self.discarded_solutions: DiscardedSolutions | None = None
        self.inequality_evaluation = None
        self.assume_evaluation: tuple[tuple[str, str], ...] | None = None
        self.governing_evaluation = None
        self.summary_evaluation = None
        self.report_request: str | None = None
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

    def _numeric_modes(self, source_matrix, operation: str):
        """The eigenvalues and mode shapes of a matrix that has no closed form, from its
        numbers, in the one unit its entries share. See `matrix_modes`."""
        context = self.engine.numeric_context
        _substitutions, unresolved, quantity_matrix = context.evaluate_matrix(source_matrix)
        if unresolved:
            hint = diagnostic_hint("unresolved_numeric_symbols", names=tuple(unresolved))
            raise EngEvaluationError(
                "numeric evaluation requires values for: " + ", ".join(unresolved) + f". {hint}"
            )
        modes, scale = modes_of(quantity_matrix, operation=operation)
        unit = scale if scale is not None else context.ureg.dimensionless
        return modes, unit

    def _numeric_eigenvalue_set(self, value: EigenvalueSet, validations, target_unit=None):
        if not value.closed_form:
            modes, unit = self._numeric_modes(value.source_matrix, "eigenvals")
            entries = []
            for mode in modes:
                quantity = self.engine.numeric_context.ureg.Quantity(mode.value, unit)
                if target_unit is not None:
                    quantity = self.engine.numeric_context.convert_quantity(quantity, target_unit)
                entries.append(EigenvalueEntry(value=quantity, multiplicity=mode.multiplicity))
            return EigenvalueSet(
                entries=tuple(entries),
                source_matrix=value.source_matrix,
                unit_requested=target_unit is not None,
                closed_form=False,
            )
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
        return EigenvalueSet(
            entries=_in_mode_order(entries),
            source_matrix=value.source_matrix,
            unit_requested=target_unit is not None,
        )

    def _numeric_eigenvector_set(self, value: EigenvectorSet, validations, target_unit=None):
        if not value.closed_form:
            context = self.engine.numeric_context
            modes, unit = self._numeric_modes(value.source_matrix, "eigenvects")
            entries = []
            for mode in modes:
                quantity = context.ureg.Quantity(mode.value, unit)
                if target_unit is not None:
                    quantity = context.convert_quantity(quantity, target_unit)
                vectors = tuple(
                    QuantityMatrix(
                        rows=len(vector),
                        cols=1,
                        entries=tuple(context.ureg.Quantity(entry) for entry in vector),
                    )
                    for vector in mode.vectors
                )
                entries.append(
                    EigenvectorEntry(
                        value=quantity, multiplicity=mode.multiplicity, vectors=vectors
                    )
                )
            return EigenvectorSet(
                entries=tuple(entries),
                source_matrix=value.source_matrix,
                unit_requested=target_unit is not None,
                closed_form=False,
            )
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
        return EigenvectorSet(
            entries=_in_mode_order(entries),
            source_matrix=value.source_matrix,
            unit_requested=target_unit is not None,
        )

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
        indices = self.index_values(node.slice)
        if isinstance(value, (EigenvalueSet, EigenvectorSet)):
            return take_mode(value, indices)
        return matrix_index(value, indices)

    def index_values(self, index_node: ast.AST) -> tuple:
        """The indices a subscript names: numbers, lists, and `IndexRange` for `1:2`."""
        if isinstance(index_node, ast.Tuple):
            index_nodes = tuple(index_node.elts)
        else:
            index_nodes = (index_node,)
        return tuple(
            IndexRange(
                lower=None if item.lower is None else self.visit(item.lower),
                upper=None if item.upper is None else self.visit(item.upper),
            )
            if isinstance(item, ast.Slice)
            else self.visit(item)
            for item in index_nodes
        )

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
        elif (
            node.id in self.engine.numeric_context.matrices
            and self.engine.numeric_context.get(node.id) is None
        ):
            raise EngEvaluationError(
                f"'{node.id}' holds numbers, not formulas: it was defined with :=. "
                f"Use it on a := line, such as x := {node.id}[1,1] or f := k*{node.id}."
            )
        return self.engine.resolve_name(node.id)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        value = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
        raise EngEvaluationError("unsupported unary operator")

    def visit_BinOp(self, node: ast.BinOp):
        # Split from `_combine` so the written-form evaluator can change what an
        # operator does without changing how its operands are reached. Visiting is not
        # free of consequence - it records numeric guards - so a subclass must not walk
        # the children a second time.
        return self._combine(node.op, self.visit(node.left), self.visit(node.right))

    def _combine(self, op, left, right):
        if isinstance(op, ast.Add):
            return matrix_add(left, right)
        if isinstance(op, ast.Sub):
            return matrix_subtract(left, right)
        if isinstance(op, ast.Mult):
            return matrix_multiply(left, right)
        if isinstance(op, ast.Div):
            return matrix_scalar_divide(left, right)
        if isinstance(op, ast.Pow):
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

    def _called(self, name, function, bindings):
        """A call of a function of the sheet: its body, with the arguments put in."""
        return substitute_symbolic_value(function.expression, bindings)

    def visit_Call(self, node: ast.Call):
        """A call, with a `solve` answered once for both readings of its statement.

        `_shown_input` reads a statement a second time when a call sits inside something
        larger. A derivative or an integral returns its unevaluated form then, but a
        `solve` in `2*solve(x - 4 = 0, x)` shows its answer, and was solving the same
        equation a second time to get it.
        """
        solving = isinstance(node.func, ast.Name) and node.func.id == "solve"
        if solving and self.showing and id(node) in self.answered:
            return self.answered[id(node)]
        value = self._read_call(node)
        if solving:
            self.answered[id(node)] = value
        return value

    def _read_call(self, node: ast.Call):
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

        if name == "summary":
            if node.args or node.keywords:
                raise EngEvaluationError("summary takes no arguments")
            if not self.engine.reported:
                raise EngEvaluationError(
                    "summary has nothing to show; mark a value with report(...) first"
                )
            self.summary_evaluation = tuple(self.engine.reported.items())
            return None

        if name in ("numeric", "report"):
            if name == "report":
                # Evaluated and displayed exactly as numeric does; what report adds is
                # the record. `result(...)` already means "formula and final value
                # without the substitution stage" and keeps that meaning - which value
                # belongs in the summary is a different question from how it is shown.
                if len(node.args) != 1 or not isinstance(node.args[0], ast.Name):
                    raise EngEvaluationError(
                        "report expects one defined name, as in report(M_max)"
                    )
                self.report_request = node.args[0].id
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
                self.requested_unit = target_unit

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
                # `numeric(phiMn)` opens with the formula its definition showed, not a
                # second and different one. Both stages or neither: a definition reading
                # `phi As fy (d - a/2)` above an evaluation reading `cover` and `h`
                # contradicts itself, and #86's rule that a formula is not restated by
                # its own evaluation stops firing, so the reader is handed both.
                #
                # The quantity comes from this same expression, and it is the same
                # number: a kept name resolves to the value stored for it rather than
                # being expanded again.
                if isinstance(argument, ast.Name) and isinstance(symbolic_expression, sp.Expr):
                    written = self.engine.written_namespace.get(argument.id)
                    if isinstance(written, sp.Expr):
                        symbolic_expression = written
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
                if isinstance(argument, ast.Name):
                    quantity = self.engine.zero_in_its_unit(argument.id, quantity)

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
            if node.args and isinstance(node.args[0], ast.Compare):
                return self._evaluate_inequality(node)

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
            # Same rule as the system form.
            if not self._already_on_the_page(node.args[0]):
                self.display_input = equation
            # What the answer is an answer for. The system form carries it in
            # `solutions`; one answer had nowhere to put it and reached the page as a
            # bare value.
            self.solved_for = unknown_name
            solvable, degree = closed_form_factors(equation.lhs - equation.rhs, unknown)
            if degree and not solvable:
                # Only when nothing in it has a closed form: `(x - a)(x⁵ + b x + 1) = 0`
                # still answers `a`, as it did.
                raise EngEvaluationError(
                    f"this equation is a polynomial of degree {degree} in {unknown} with "
                    "other names in it, and has no closed form worth writing. For its "
                    f"values inside a range write roots(expression, {unknown}, lower, "
                    "upper); for the frequencies of a building, eigenvals(inv(M)*K)"
                )
            solutions = sp.solve(equation, unknown)
            if len(solutions) == 0:
                raise EngEvaluationError(f"solve found no solution for {unknown}")
            if len(solutions) > 1:
                solutions, self.discarded_solutions = self._rule_out_by_assumption(
                    solutions, unknown_name
                )
            if len(solutions) > 1:
                # Several answers is not an error and never was; the previous guard
                # said "v0.1 requires one", which was a contract from the earliest
                # version rather than a mathematical limit. Complex solutions are kept:
                # an engineer shown one answer has no way to know two were discarded.
                self.system_evaluation = _SystemSolveEvaluation(
                    equations=(equation,),
                    solutions=tuple((unknown_name, value) for value in solutions),
                    kind="multi",
                    discarded=self.discarded_solutions,
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

        if name in {"dot", "cross"}:
            self._require_arity(name, args, 2, "two vectors")
            return (matrix_dot if name == "dot" else matrix_cross)(args[0], args[1])

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
            return self._called(name, function, bindings)

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

        if name in {"min", "max"}:
            if len(args) < 2:
                raise EngEvaluationError(
                    f"{name} expects at least 2 arguments: the values to compare"
                )
            if any(is_matrix(arg) for arg in args):
                raise EngEvaluationError(f"{name} compares scalar values, not a matrix")
            return (WrittenMax if name == "max" else WrittenMin)(*args)

        if name == "interp":
            self._require_arity(name, args, 3, "point, [points], [values]")
            point, points, values = args
            if is_matrix(point):
                raise EngEvaluationError("interp reads one point, not a matrix")
            if not all(is_matrix(table) and 1 in table.shape for table in (points, values)):
                raise EngEvaluationError(
                    "interp reads its table as two rows, the points and the values"
                )
            if len(points) < 2:
                raise EngEvaluationError("interp needs a table of at least 2 points")
            if len(points) != len(values):
                raise EngEvaluationError(
                    f"interp needs one value for each point: {len(points)} points, "
                    f"{len(values)} values"
                )
            return Interpolation(
                point,
                sp.ImmutableMatrix(1, len(points), list(points)),
                sp.ImmutableMatrix(1, len(values), list(values)),
            )

        if name == "integrate":
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
                if self.showing:
                    return self.display_input
                return map_matrix_entries(
                    expr,
                    lambda entry: sp.integrate(entry, bounds),
                )
            self.display_input = sp.Integral(expr, bounds)
            if self.showing:
                return self.display_input
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
                if self.showing:
                    return self.display_input
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
            if self.showing:
                return self.display_input
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

            # Only where a crossing is, as a number, is kept. When both responses are
            # polynomials once the sheet's values are in, that is a real root of their
            # difference: six quadratic combinations took 54 s through fifteen symbolic
            # closed forms. See `test_governing_is_quick_over_polynomials`.
            polynomials = [
                _polynomial_in_base_units(
                    self.engine.numeric_context, item.comparison_expression, variable_symbol
                )
                for item in resolved
            ]
            crossovers = []
            for index, left in enumerate(resolved):
                for offset, right in enumerate(resolved[index + 1 :], start=index + 1):
                    if polynomials[index] is not None and polynomials[offset] is not None:
                        crossovers.extend(
                            _real_roots_between(
                                polynomials[index] - polynomials[offset],
                                lower_quantity,
                                upper_quantity,
                            )
                        )
                        continue
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
                label_expression=response.label_expression,
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
                left_expression=left.label_expression,
                right_expression=right.label_expression,
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
            label_expression=response.label_expression,
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

            reference = None
            if all(float(value.magnitude) == 0 for value in normalized_values):
                # Zero at every station - a simply supported moment at its supports - says
                # nothing about the unit the column reads in; the middle of the range does.
                try:
                    _, middle = context.evaluate_symbolic(
                        response.comparison_expression,
                        overrides={variable: (point_values[0] + point_values[-1]) / 2},
                    )
                    reference = middle.to(canonical_unit)
                except (EngEvaluationError, DimensionalityError, AttributeError):
                    reference = None
            columns.append(
                TableColumn(
                    display_label=response.display_label,
                    unit=canonical_unit,
                    values=normalized_values,
                    reference=reference,
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

    _ASSUMPTION_ADMITS = {
        "positive": lambda number: number > 0,
        "nonnegative": lambda number: number >= 0,
        "negative": lambda number: number < 0,
        "nonpositive": lambda number: number <= 0,
    }

    def _admits(self, value, condition: str):
        """Does `value` satisfy `condition`? True, False, or None when nothing says.

        Asking SymPy first would be the obvious design and it would be dead code. When
        the unknown carries the assumption, `sp.solve` has already dropped every root
        whose sign it could determine: solving `(x + 2)*(x - b)` for a positive x
        returns `[b]`, with the -2 gone before anything here runs. What reaches this
        method is exactly the set SymPy could not decide, so `value.is_positive` is
        None by construction and a symbolic branch could never change an outcome.

        That is also why a numeric route is needed at all. In `pi*sqrt(E*I/kN)/K` every
        symbol is unsigned, so neither root is decidable - but the sheet above says what
        E, I, K and kN are worth. Those `:=` lines are not extra information the reader
        must supply; they are what an engineer reads off their own page when they cross
        out the negative root.
        """
        context = self.engine.numeric_context
        try:
            overrides = context.unit_literal_overrides(value)
            _substitutions, quantity = context.evaluate_symbolic(value, overrides=overrides)
        except EngCalcError:
            # A complex answer ends here too: the numeric layer refuses a value with no
            # real result. It has no sign, so the assumption says nothing about it and
            # it survives. Discarding on ignorance is how a solver quietly loses roots.
            return None

        magnitude = getattr(quantity, "magnitude", quantity)
        try:
            number = float(magnitude)
        except (TypeError, ValueError):
            return None
        return self._ASSUMPTION_ADMITS[condition](number)

    def _rule_out_by_assumption(self, solutions: list, unknown_name: str):
        """Drop the answers the engineer has already said are impossible.

        `assume(L > 0)` reaches the unknown's symbol, but a length being positive says
        nothing about the sign of an expression built from unsigned symbols, so SymPy
        keeps both roots and is right to. This is where the statement is spent.

        Only decided contradictions are dropped. An answer that cannot be evaluated
        survives, and if every answer would go, none does: an assumption that rules out
        the entire solution set is a statement about the problem, not about the answer,
        and silently emptying the result would hide it.
        """
        declared = self.engine.assumptions.get(unknown_name)
        if not declared:
            return solutions, None

        for condition in declared:
            if condition not in self._ASSUMPTION_ADMITS:
                continue
            verdicts = [self._admits(value, condition) for value in solutions]
            kept = [v for v, ok in zip(solutions, verdicts) if ok is not False]
            if not kept or len(kept) == len(solutions):
                continue
            ruled_out = [v for v, ok in zip(solutions, verdicts) if ok is False]
            return kept, DiscardedSolutions(
                variable=unknown_name,
                condition=condition,
                values=tuple(ruled_out),
            )
        return solutions, None

    _INEQUALITY_RELATIONS = {
        ast.Gt: ">",
        ast.GtE: r"\geq",
        ast.Lt: "<",
        ast.LtE: r"\leq",
    }
    _INEQUALITY_HOLDS = {
        ast.Gt: lambda number: number > 0.0,
        ast.GtE: lambda number: number >= 0.0,
        ast.Lt: lambda number: number < 0.0,
        ast.LtE: lambda number: number <= 0.0,
    }

    def _evaluate_inequality(self, node: ast.Call):
        """`solve(M(x) > 20*kN*m, x, 0, L)` - the region where a response exceeds a value.

        The boundaries of that region are the roots of `lhs - rhs`, so this is the roots
        machinery with a sign test on top rather than a second solver. SymPy's own
        `solve_univariate_inequality` cannot take this problem: `q*x*(L - x)/2 > 20*kN*m`
        raises NotImplementedError, because q, L, kN and m are unsigned free symbols in
        the symbolic layer. The sheet's `:=` lines are what make it answerable.

        The domain is required. It is where the variable gets its unit, and "between 0.76
        and 5.24" with no unit is not an engineering answer. It is also the beam.
        """
        comparison = node.args[0]
        operator = type(comparison.ops[0])
        variable_name = node.args[1].id
        variable_symbol = self.engine.resolve_symbol(variable_name)

        lower_node, upper_node = node.args[2:]
        lower_expression = self.visit(lower_node)
        upper_expression = self.visit(upper_node)
        try:
            domain = normalize_analysis_domain(
                self.engine.numeric_context,
                lower_expression,
                upper_expression,
                lower_quantity=self._resolve_domain_numeric_value(lower_node),
                upper_quantity=self._resolve_domain_numeric_value(upper_node),
            )
        except EngEvaluationError as exc:
            raise EngEvaluationError(
                "inequality domain bound must be numerically resolvable: " + str(exc)
            ) from None

        sentinel = object()
        previous = self.symbol_overrides.get(variable_name, sentinel)
        self.symbol_overrides[variable_name] = variable_symbol
        try:
            left = self.visit(comparison.left)
            right = self.visit(comparison.comparators[0])
        finally:
            if previous is sentinel:
                self.symbol_overrides.pop(variable_name, None)
            else:
                self.symbol_overrides[variable_name] = previous

        if is_matrix(left) or is_matrix(right):
            raise EngEvaluationError(
                "inequality sides must be scalar; index the matrix first, "
                "for example A[1,1]"
            )
        difference = sp.sympify(left) - sp.sympify(right)

        # What the heading names. The same two questions `roots` and `extrema` ask of
        # their response - what does a person call this, and what does a heading typeset
        # - asked of each side, so `solve(M(x) > 20*kN*m, ...)` is headed with the line
        # the engineer wrote rather than with a region whose condition is nowhere.
        left_node, right_node = comparison.left, comparison.comparators[0]
        left_label = self._plot_expression_label(left_node, variable_name, left)
        right_label = self._plot_expression_label(right_node, variable_name, right)
        left_heading = self._heading_expression(left_node, left)
        right_heading = self._heading_expression(right_node, right)

        points, _intervals, unresolved = solve_roots_exact(
            difference,
            variable_symbol,
            domain,
            self.engine.numeric_context,
        )
        if unresolved:
            raise EngEvaluationError(
                "inequality analysis could not resolve a safe solution set"
            )

        unit = domain.lower_quantity.units
        edges = [domain.lower_quantity]
        for point in points:
            quantity = point.x_quantity.to(unit)
            if all(
                abs(float((quantity - edge).magnitude)) > 0.0 for edge in edges
            ):
                edges.append(quantity)
        edges.append(domain.upper_quantity.to(unit))
        edges.sort(key=lambda quantity: float(quantity.magnitude))

        # A boundary is a root, where the two sides are equal. A strict comparison
        # excludes it and a non-strict one includes it; the ends of the domain are
        # always closed, being bounds the engineer wrote rather than roots.
        boundary_closed = operator in (ast.GtE, ast.LtE)

        holds = self._INEQUALITY_HOLDS[operator]
        satisfied: list[tuple[int, int]] = []
        for index in range(len(edges) - 1):
            lower, upper = edges[index], edges[index + 1]
            midpoint = (lower + upper) / 2
            _substitutions, value = self.engine.numeric_context.evaluate_symbolic(
                difference,
                overrides={variable_name: midpoint},
            )
            if holds(float(value.to_base_units().magnitude)):
                # Two neighbouring regions join only if the root between them is in
                # the answer too. For `(x - 3)^2 > 0` on [0, 6] both sides hold and
                # x = 3 does not, so the answer is two intervals; merging them would
                # quietly hand back a point the inequality excludes.
                if satisfied and satisfied[-1][1] == index and boundary_closed:
                    satisfied[-1] = (satisfied[-1][0], index + 1)
                else:
                    satisfied.append((index, index + 1))

        intervals = tuple(
            CharacteristicInterval(
                lower_symbolic=None,
                upper_symbolic=None,
                lower_quantity=edges[start],
                upper_quantity=edges[stop],
                role="satisfies",
                provenance="exact",
                lower_closed=True if start == 0 else boundary_closed,
                upper_closed=True if stop == len(edges) - 1 else boundary_closed,
            )
            for start, stop in satisfied
        )

        self.inequality_evaluation = (
            variable_name,
            self._INEQUALITY_RELATIONS[operator],
            domain,
            intervals,
            difference,
            (
                left_label,
                right_label,
                left_heading,
                right_heading,
                self.engine._unit_literals_of(left, right),
            ),
        )
        return None

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
            label_expression = self._heading_expression(signed_node, signed_expression)
            if label_expression is not None:
                label_expression = sp.Abs(label_expression, evaluate=False)
        else:
            signed_expression = self.visit(node)
            comparison_expression = signed_expression
            source_label = self._plot_expression_label(
                node,
                variable,
                signed_expression,
            )
            display_label = source_label
            label_expression = self._heading_expression(node, signed_expression)

        return _ResolvedExpression(
            source_label=source_label,
            display_label=display_label,
            signed_expression=signed_expression,
            comparison_expression=comparison_expression,
            is_absolute=is_absolute,
            label_expression=label_expression,
        )

    def _heading_expression(self, node: ast.AST, expression):
        """The response a characteristic heading typesets.

        The label text beside it is `str()` of the expression - Python, `w**4` - and
        for a defined name it is the whole expression the name stands for. A figure's
        legend and a governing block still read that text, so this is carried beside
        it rather than replacing it. A user function has no expression here: its label
        is already `M(x)`.
        """
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in self.engine.functions
        ):
            return None
        if isinstance(node, ast.Name):
            return self.engine.resolve_symbol(node.id)
        return expression

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
                        is_moment=self._is_moment_series(expression.source_label, y_values),
                        segment_starts=segment_starts,
                        characteristics=characteristics,
                    )
                )
                raw_source_series.append(
                    PlotSeries(
                        display_label=expression.source_label,
                        y_values=source_y_values,
                        is_moment=self._is_moment_series(expression.source_label, y_values),
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

        is_moment = None
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
            if is_moment is None:
                is_moment = self._is_moment_series(source_label, comparison_y_values)

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
                    sweep_parameter=parameter_name,
                    sweep_value=sweep_value,
                    y_values=comparison_y_values,
                    is_moment=is_moment,
                    segment_starts=segment_starts,
                    characteristics=characteristics,
                )
            )
            source_series.append(
                PlotSeries(
                    display_label=case_label,
                    sweep_parameter=parameter_name,
                    sweep_value=sweep_value,
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
            # `replace`, not a fresh `PlotSeries`: this rebuilds a series to put its y
            # values in one unit, and listing the fields to carry over means every field
            # added later is silently dropped here. One was - a sweep's parameter and
            # value reached this and did not leave it, so the legend could not be
            # rewritten in the sheet's units.
            normalized.append(
                replace(
                    item,
                    y_values=y_values,
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

        # `M_1`, `M_2` are the family `M`, and so are `U1`, `U2`: a code's combinations
        # are written with their number and no underscore, and the frame's envelope was
        # titled `Comparison envelope`. See `test_combinations_are_named_as_a_family`.
        families = {
            re.sub(r"(?<=[A-Za-z])\d+$", "", name.split("_", 1)[0])
            for name in function_names
        }
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

    def _is_moment_series(self, label: str, values) -> bool:
        """A moment by its name, or by a moment's name and a moment's dimension.

        A load case or combination is named for the load, not the response - `D`, `Lv`,
        `U1` - so for those the dimension alone decides: `combo U1 = 1.2*D + 1.6*Lv` over
        `case D = M_D(x)` is a moment, and a combination of shears is not.
        """
        if self._is_moment_label(label):
            return True
        name = label.strip().split("(", 1)[0]
        if _MOMENT_FAMILY_LABEL.match(label.strip()) is None and name not in self.engine.load_cases:
            return False
        moment = self.engine.numeric_context.ureg.Quantity(1, "newton * meter").dimensionality
        for value in values:
            dimensionality = getattr(value, "dimensionality", None)
            if dimensionality is not None:
                return dimensionality == moment
        return False

    @staticmethod
    def _format_plot_quantity(quantity) -> str:
        """See ``quantity_text``, which the renderer needs too."""
        return quantity_text(quantity)

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

    def _already_on_the_page(self, node: ast.AST) -> bool:
        """Has the reader seen this exact equation under a name of its own?

        `solve(eqFy, eqMA, R_A, R_B)` re-showed both equations, so a statics sheet
        printed each of them twice - once as its definition and once as the solve's
        echo. Nobody writes the same equation twice by hand.

        The test is not merely "the argument is a name". `solve(delta_B, R_B_aux)` names
        an *expression*, and what the solve displays is `delta_B = 0` with the integral
        evaluated: the equality is new, and dropping it would hide the equation being
        solved. Only a name already bound to an `Eq` is a genuine repeat.
        """
        if not isinstance(node, ast.Name):
            return False
        return isinstance(self.engine.namespace.get(node.id), sp.Equality)

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
            unnamed = []
            for equation_node in node.args[:half]:
                equation = self.visit(equation_node)
                if not isinstance(equation, sp.Equality):
                    equation = sp.Eq(equation, 0, evaluate=False)
                equations.append(equation)
                if not self._already_on_the_page(equation_node):
                    unnamed.append(equation)
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
            equations=tuple(unnamed),
            solutions=tuple(
                (name, mapping[symbol]) for name, symbol in zip(names, symbols)
            ),
        )

    @staticmethod
    def _require_arity(name: str, args: list, count: int, signature: str) -> None:
        if len(args) != count:
            noun = "argument" if count == 1 else "arguments"
            raise EngEvaluationError(f"{name} expects {count} {noun}: {signature}")


# Functions a written form may walk through. Everything here is pure arithmetic; the
# written pass runs the evaluator a second time, and a call that solves, plots or
# summarises would do that work twice and record its effects twice.
_WRITTEN_FORM_SAFE_CALLS = frozenset(
    {"sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "exp", "log", "abs",
     # `transpose`, because `K_e = transpose(A_e)*k_e*A_e` is how a stiffness matrix is
     # assembled and the call was the only thing keeping a written form off it. Without
     # it the frame benchmark printed every entry in nodal coordinates,
     # `b_c d_c^3 E / (3 sqrt((-x_1 + x_2)^2 + (-y_1 + y_2)^2))`, where with it the same
     # entry reads `4 E I_c / L_c` - the form the textbooks print. The page loses a fifth
     # of its characters and renders *faster*, 0.65 s to 0.52 s, because the written form
     # is smaller than the expansion it replaces.
     #
     # The list is about a second walk being free of consequence, and neither a transpose
     # nor an inverse has one.
     #
     # `inv` was left off here at first, on a measurement that said adding it changed
     # nothing on any sheet. The measurement was right about the frame benchmark and the
     # sentence recorded was wrong: on a smaller sheet `P = inv(K)*N` keeps its kept names
     # the moment `inv` is allowed. What was actually happening on the benchmark is
     # underneath, in `_agrees_with` - the written form for `C = -inv(K_ii)*K_id` was
     # built and then refused, because `is_zero_matrix` answers None for a symbolic
     # inverse. Both halves had to move for the condensation to read in `E`, `I_c`, `L_c`.
     #
     # It is not free: a symbolic inverse is computed twice, and the frame sheet goes from
     # 0.32 s to about 0.7 s. Before the verification was fixed that bought nothing at
     # all; now it buys the last two matrices of the memoria.
     "transpose",
     "inv",
     # The algebra calls, on 2026-09-24. Without them a derivation that passed through one
     # lost every kept name at once: `K_b0 = subs(K_b, c_theta, 1, s_theta, 0)` and the
     # column `K_c` read in `E A / L` and `12 E I / L^3` between matrices that read in `a`
     # and `b_1 ... b_4`. None has an effect a second walk would repeat, and the
     # verification keeps the short form honest: `subs(..., L, L_1)` replaces the `L`
     # inside `a = E*A/L`, the written form no longer agrees, and the entry reads
     # `E A / L_1` as it should. A `simplify` is computed twice, on the smaller form.
     "subs",
     "expand",
     "simplify",
     "factor",
     # `min` and `max`, found designing the portal frame's beam: `As = max(f_cw*b*d/fy*(...),
     # As_min)` lost `f_cw`, `R_n` and `As_min` at once, and the 0.85 of Whitney's block
     # folded into 2/0.85 = 2.35. A limit is pure arithmetic, like `abs` above; the
     # evaluator records the limits it compares, but on the written pass's own instance.
     # See `test_a_kept_name_survives_min_and_max`.
     "min",
     "max"}
)


class TypedFloat(sp.Float):
    """A number with the figures it was typed with: `0.90`, which a Float prints `0.9`.

    Only ever in a written form, which is shown and not computed with: arithmetic that
    evaluates returns an ordinary Float. It equals and hashes as the Float it is, and it
    is turned back into one before a written form is verified.
    """

    __slots__ = ("typed",)

    def __new__(cls, typed: str):
        number = sp.Float.__new__(cls, typed)
        number.typed = typed
        return number


def _plain_floats(expression):
    """`expression` with every TypedFloat an ordinary Float, for `srepr` to read back."""
    if isinstance(expression, TypedFloat):
        # `sp.Float(x)` hands a Float subclass back unchanged; `_new` builds a Float.
        return sp.Float._new(expression._mpf_, expression._prec)
    if not getattr(expression, "args", ()):
        return expression
    arguments = [_plain_floats(argument) for argument in expression.args]
    if all(new is old for new, old in zip(arguments, expression.args)):
        return expression
    try:
        return expression.func(*arguments, evaluate=False)
    except TypeError:
        return expression.func(*arguments)


def _flat_products(expression):
    r"""`expression` with each product flat, as `_flattened` builds them.

    An argument put into a written body arrives as a product inside a product, and
    `2*(876940*kgf*cm)` printed `2 876940 kgf cm` - one number, to the eye. Flat, the page
    writes `2 \cdot 876940 kgf cm`, as it does for `2*3*c` typed by hand.
    """
    if not getattr(expression, "args", ()):
        return expression
    arguments = [_flat_products(argument) for argument in expression.args]
    if isinstance(expression, sp.Mul):
        return _flattened(sp.Mul, *arguments)
    if isinstance(expression, sp.Add):
        return _flattened(sp.Add, *arguments)
    try:
        return expression.func(*arguments, evaluate=False)
    except TypeError:
        return expression.func(*arguments)


def _flattened(kind, *args):
    r"""An unevaluated ``Add`` or ``Mul`` with no nesting of its own kind inside it.

    Not a detail. Built nested, `5*q*L**4/(384*E*I_z)` prints `L^4 \cdot 5 q` and
    `h - cover - db_st - db/2` prints `-(cover + db_st - h)`: grouping SymPy would never
    produce, and worse than the defect this exists to fix. Flat, every real formula
    measured prints exactly as it does today apart from the one whose coefficient was
    being destroyed.
    """
    flat: list = []
    for arg in args:
        if isinstance(arg, kind):
            flat.extend(arg.args)
        else:
            flat.append(arg)
    return kind(*flat, evaluate=False)


def _in_mode_order(entries) -> tuple:
    """A closed form's eigenvalues once they are numbers, ascending - the order `lam[i]`
    counts in. A two-by-two written in names lists its roots in SymPy's order, which the
    numbers need not follow."""
    return tuple(sorted(entries, key=lambda entry: float(entry.value.to_base_units().magnitude)))


def _polynomial_in_base_units(context, expression, variable):
    """`expression` as a polynomial in `variable` with every other name a number, or None.

    Each name and unit takes its value's magnitude in base units, and the variable stands
    for its own magnitude in base units, so the polynomial's roots are positions in base
    units. Base units are what make this sound: converting to them only multiplies, so a
    sum that agrees in units agrees in base magnitudes. None when a name has no value, or
    when what is left is not a polynomial - a `piecewise`, a Macaulay bracket - and the
    caller keeps its exact path.
    """
    expression = sp.sympify(expression)
    if expression.has(sp.Piecewise):
        return None
    try:
        units = context.unit_literal_overrides(expression, None)
    except EngEvaluationError:
        return None
    substitutions = {}
    for symbol in expression.free_symbols:
        if symbol == variable:
            continue
        value = units.get(symbol.name, context.values.get(symbol.name))
        if value is None:
            return None
        try:
            magnitude = context._as_quantity(value).to_base_units().magnitude
            substitutions[symbol] = sp.Float(float(magnitude))
        except (TypeError, ValueError, AttributeError):
            return None
    try:
        polynomial = sp.Poly(expression.xreplace(substitutions), variable)
    except sp.PolynomialError:
        return None
    if not all(coefficient.is_real for coefficient in polynomial.all_coeffs()):
        return None
    return polynomial


def _real_roots_between(polynomial, lower_quantity, upper_quantity):
    """The real roots of `polynomial` strictly inside the domain, as quantities."""
    unit = lower_quantity.units
    base = lower_quantity.to_base_units()
    low = float(base.magnitude)
    high = float(upper_quantity.to_base_units().magnitude)
    if polynomial.is_zero or polynomial.degree() < 1:
        return []
    roots = []
    for root in polynomial.nroots(n=15, maxsteps=200):
        value = complex(root)
        # A root this close to the axis is a real crossing computed in floating point.
        if abs(value.imag) > 1e-9 * max(1.0, abs(value.real)):
            continue
        if low < value.real < high:
            roots.append(base._REGISTRY.Quantity(value.real, base.units).to(unit))
    return roots


def _standalone_call(statement, name: str, message: str):
    """The call `name(...)` when it is the whole line; None when the line does not call it.

    Anywhere else - assigned, or inside an expression - it is refused with `message`.
    """
    body = statement.expression.body
    if not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name
        for node in ast.walk(body)
    ):
        return None
    if statement.target is not None or not (
        isinstance(body, ast.Call) and isinstance(body.func, ast.Name) and body.func.id == name
    ):
        raise EngEvaluationError(message)
    return body


_IMAGE_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}


def _read_image(source: str) -> tuple[bytes, str]:
    """The bytes of a figure and its type, from a file or a URL."""
    import pathlib
    import urllib.request

    suffix = pathlib.PurePosixPath(source.split("?", 1)[0]).suffix.lower()
    mime = _IMAGE_TYPES.get(suffix)
    if source.startswith(("http://", "https://")):
        try:
            with urllib.request.urlopen(source, timeout=30) as response:
                data = response.read()
                mime = mime or response.headers.get("Content-Type", "").split(";")[0].strip()
        except Exception as exc:  # noqa: BLE001 - any failure to fetch is said the same way
            raise EngEvaluationError(f"image could not be fetched from {source}: {exc}") from exc
    else:
        path = pathlib.Path(source).expanduser()
        if not path.is_file():
            raise EngEvaluationError(
                f"image file not found: {source} (looked in {path.resolve().parent}); in "
                "Colab, upload it to the Files panel or mount Drive and give its path"
            )
        data = path.read_bytes()
    if not mime or not mime.startswith("image/"):
        raise EngEvaluationError(
            f"image reads .png, .jpg, .gif, .svg or .webp files; {source} is not one"
        )
    return data, mime


def _canonical_limits(expression):
    """`WrittenMin`/`WrittenMax` as SymPy's `Min`/`Max`, which put their arguments in order."""
    if not hasattr(expression, "replace"):
        return expression
    return expression.replace(
        lambda node: isinstance(node, (WrittenMin, WrittenMax)),
        lambda node: (sp.Min if isinstance(node, WrittenMin) else sp.Max)(*node.args),
    )


def _agrees_with(written, value, expansions: dict | None = None) -> bool:
    """True when the written form is the same expression as the one computed beside it.

    Not `written - value == 0`: that is False even when they agree, because subtracting
    does not force an unevaluated expression to flatten and the difference keeps it
    whole. `simplify` does force it, at about 33 ms a definition, and still failed to
    verify three of seven real formulas. A `srepr` round-trip rebuilds the expression
    through SymPy's ordinary constructors - which is precisely the evaluation that was
    held off - and verified all seven at 1.9 ms.
    """
    try:
        # A `min` or `max` keeps its arguments where they were typed, and a round trip
        # through `srepr` would bring `WrittenMin` back as an unknown function of that
        # name: both sides are compared as SymPy's own `Min` and `Max`, whose order is
        # canonical. See `test_a_kept_name_survives_min_and_max`.
        rebuilt = sp.sympify(sp.srepr(_canonical_limits(_plain_floats(written))))
        if expansions:
            # A `keep` name stands for itself in the written form and for its expression
            # in the evaluated one, so the two only agree once the names are put back.
            # Checking without this would reject every formula built on a kept name,
            # which is the whole feature.
            rebuilt = rebuilt.subs(expansions)
        difference = _canonical_limits(rebuilt) - _canonical_limits(sp.sympify(value))
        if isinstance(difference, sp.MatrixBase):
            # The whole of what let a written form reach a matrix. A zero matrix is not
            # `== 0` - `Matrix([[0, 0], [0, 0]]) == 0` is False - so asking a matrix the
            # question a scalar is asked discarded every matrix, including the ones that
            # agreed, and no matrix ever had a written form to show. A local stiffness
            # matrix printed each entry expanded into `b_c d_c^3/12` and
            # `sqrt((-x_1 + x_2)^2 + ...)` for want of this line.
            #
            # A shape mismatch raises above and is caught, which is the answer it should
            # give. `is True` because the property is True, False or None for a symbolic
            # matrix; returning it raw is indistinguishable to the one caller, measured,
            # and this says what is meant.
            verdict = difference.is_zero_matrix
            if verdict is not None:
                return verdict is True

            # `None` is not "no", it is "I will not prove this without work", and for a
            # symbolic inverse it is a *false negative*: the written form for
            # `C = -inv(K_ii)*K_id` is correct and gets thrown away, so the last two
            # matrices of a condensation print in nodal coordinates while everything
            # above them reads in `E`, `I_c` and `L_c`.
            #
            # `cancel` rather than `simplify`, measured on that exact difference:
            # `cancel` answers True in 0.04 s, `simplify` in 0.53 s, `radsimp` not at
            # all. `simplify` is the push this function already refuses for scalars - ~33
            # ms each, and it failed three of seven real formulas - so thirteen times its
            # cost is not the trade. Normalising a rational function is.
            #
            # Only on the `None` branch, so it can add time only where the answer was
            # about to be "no". A difference that is genuinely non-zero still cancels to
            # something non-zero, which is what keeps this a verification rather than a
            # rubber stamp.
            try:
                return difference.applyfunc(sp.cancel).is_zero_matrix is True
            except Exception:
                return False
        if difference == 0:
            return True

        # The same argument the matrix branch above makes, on the branch it was never
        # extended to. `difference == 0` is a *structural* test, and a coefficient is
        # exactly what breaks the structure: SymPy distributes a Number over an Add as it
        # builds, so `5*q_s` evaluates to `5*qD + 5*qL` while the written form still says
        # `5*q_s`, and the two shapes of one value do not subtract to a literal zero.
        #
        #     60*(qD + qL)/(b*h³) - (60*qD + 60*qL)/(b*h³)  ==  0   ->  False
        #
        # `keep` exists to stop precisely that, and it was failing on the most ordinary
        # formula in the trade: a memoria wrote `5*q_s*L^4/(384*E*I)` and the page printed
        # `L⁴(5 qD + 5 qL)/(32 b h³ E)`. Every deflection leads with a coefficient.
        #
        # `cancel` rather than `simplify`, for the reason recorded above: it normalises a
        # rational function instead of searching, and this file measured `simplify` at
        # ~33 ms a definition while failing three of seven real formulas. Only on the
        # branch that was about to answer "no", so a formula that already verified pays
        # nothing - and a written form that is genuinely wrong still cancels to something
        # non-zero, which is what keeps this a verification rather than a rubber stamp.
        try:
            if sp.cancel(difference) == 0:
                return True
        except Exception:
            pass
        # A float under a root is where `cancel` stops: Colab's SymPy (1.13.3) builds
        # `As_req(876940*kgf*cm)` as `sqrt(219235)*sqrt(4.85e-7 - ...)`, which no
        # normalisation brings back to the written `sqrt(1 - 2*876940 kgf cm/...)`, and
        # the written form was thrown away. Asked at a few points instead, the two agree
        # or they do not; a written form that is wrong still gives another number.
        # See `test_a_written_form_agrees_when_a_float_sits_under_a_root`.
        return _agree_at_points(rebuilt, sp.sympify(value))
    except Exception:
        return False


def _agree_at_points(left, right) -> bool:
    """True when two scalar expressions take the same value at three points.

    Every name is given a value between 0.5 and 2 - the same three for both sides, from a
    fixed seed - and the values are compared to nine figures. A root of something negative
    is taken as SymPy takes it, the same on both sides.
    """
    import cmath
    import random

    symbols = sorted(left.free_symbols | right.free_symbols, key=lambda symbol: symbol.name)
    if not symbols:
        return False
    chooser = random.Random(20260924)
    for _ in range(3):
        point = {symbol: sp.Float(chooser.uniform(0.5, 2.0), 30) for symbol in symbols}
        try:
            first = complex(left.xreplace(point).evalf(30))
            second = complex(right.xreplace(point).evalf(30))
        except (TypeError, ValueError):
            return False
        if not cmath.isfinite(first) or not cmath.isfinite(second):
            return False
        if not cmath.isclose(first, second, rel_tol=1e-9, abs_tol=1e-12):
            return False
    return True


class _WrittenFormEvaluator(_Evaluator):
    """The expression as the engineer typed it, kept for the page.

    `a = As*fy/(0.85*fc*b)` rendered `1.18 fy As / (b fc)`, because SymPy inverts a Float
    in a denominator as it builds the expression. The number is right and the 0.85 that
    ACI 318 requires is not on the page, so a reviewer cannot check the sheet against the
    code - which is `## v0.25.0`'s finding about load combinations, in a second place.

    Only the arithmetic changes. Names, calls and everything else resolve exactly as they
    do for the evaluated form, so this is not a second language: it is the same walk with
    SymPy's automatic simplification held off, and its answer is verified against the
    evaluated expression before anything is shown.
    """

    # The unary minus is deliberately left alone, and `_Evaluator` has no seam for it.
    # An unevaluated negation was written here first and then measured away: SymPy's own
    # `-value` leaves an unevaluated `Mul` whole, so `-x/(0.85*b)` keeps its 0.85 either
    # way, and every unary-minus formula measured renders identically. What it did do
    # was break one case -
    # `Mul(-1, Add(a, b), evaluate=False)` is the right expression and prints `- a + b`,
    # dropping the parentheses so the page states something false. `_agrees_with` cannot
    # see that, because what is wrong is the typesetting and not the mathematics, which
    # is the trap #76 was.
    #
    # `a - (b + c)` is a `Sub` and goes through `_combine`, where the negation lands
    # inside an `Add` and keeps its brackets - so that one is written as typed rather
    # than flattened to `a - b - c`, and gains from this without needing a unary rule.

    def visit_Constant(self, node: ast.Constant):
        # `0.90` as typed, not the float 0.9. See `test_a_number_is_written_as_typed`.
        typed = getattr(node, "typed", None)
        if typed is not None:
            return TypedFloat(typed)
        return super().visit_Constant(node)

    def _called(self, name, function, bindings):
        # A function that reads a kept name is called on the body it was written with,
        # so `As_req(Mu)` keeps its `f_cw` in the row that says what the call expands to;
        # and the arguments go in as written, or `2*Mu` folds into one number.
        written = self.engine.written_functions.get(name)
        if written is None:
            return super()._called(name, function, bindings)
        with sp.evaluate(False):
            return _flat_products(written.xreplace(bindings))

    def visit_Name(self, node: ast.Name):
        # A kept name stands for itself. This is the whole of RC-3: without it the
        # symbolic layer replaces `d` with `h - cover - db_st - db/2` where it is used,
        # and the formula an engineer would check against the code is not on the page.
        if node.id in self.engine.kept_names:
            return self.engine.resolve_symbol(node.id)
        # And a name that is *not* kept but was written in terms of one stands for its
        # written form, so the kept names inside it reach this formula too. Without this
        # the barrier held for one step and was gone at the second: `x = 2*L` kept `L`
        # and `y = x` printed `2 sqrt(a^2 + b^2)`.
        #
        if self.engine._shows_its_written_form(node.id):
            return self.engine.written_namespace[node.id]
        return super().visit_Name(node)

    def _combine(self, op, left, right):
        if not (isinstance(left, sp.Expr) and isinstance(right, sp.Expr)):
            return super()._combine(op, left, right)
        if isinstance(op, ast.Add):
            return _flattened(sp.Add, left, right)
        if isinstance(op, ast.Sub):
            return _flattened(sp.Add, left, _flattened(sp.Mul, sp.Integer(-1), right))
        if isinstance(op, ast.Mult):
            return _flattened(sp.Mul, left, right)
        if isinstance(op, ast.Div):
            return _flattened(
                sp.Mul, left, sp.Pow(right, sp.Integer(-1), evaluate=False)
            )
        if isinstance(op, ast.Pow):
            return sp.Pow(left, right, evaluate=False)
        return super()._combine(op, left, right)
