from __future__ import annotations

import ast
import re
from dataclasses import dataclass

import sympy as sp
from pint.errors import DimensionalityError

from .errors import (
    AmbiguousSolveError,
    EngCalcError,
    EngEvaluationError,
    EngSyntaxError,
    diagnostic_hint,
)
from .models import (
    EvaluationResult,
    NumericAssignmentResult,
    NumericEvaluationResult,
    ParsedNumericAssignment,
    ParsedStatement,
    PartialNumericEvaluationResult,
    PlotResult,
    PlotSeries,
    UserFunction,
)
from .numeric import NumericContext


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


class EngineeringEngine:
    def __init__(self) -> None:
        self.namespace: dict[str, sp.Expr] = {}
        self.functions: dict[str, UserFunction] = {}
        self.symbols: dict[str, sp.Symbol] = {}
        self.numeric_context = NumericContext()

    def reset(self) -> None:
        self.namespace.clear()
        self.functions.clear()
        self.symbols.clear()
        self.numeric_context.reset()

    def resolve_symbol(self, name: str) -> sp.Symbol:
        if name not in self.symbols:
            self.symbols[name] = sp.Symbol(name)
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
        | PartialNumericEvaluationResult
        | PlotResult
    ):
        evaluator = _Evaluator(self)
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
                if statement.parameter is None and statement.target in self.functions:
                    raise EngEvaluationError(
                        f"redefinition conflict: '{statement.target}' is already a function"
                    )
                if statement.parameter is not None and statement.target in self.namespace:
                    raise EngEvaluationError(
                        f"redefinition conflict: '{statement.target}' is already a scalar"
                    )

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

            if evaluator.partial_numeric_evaluation is not None:
                (
                    symbolic_expression,
                    substitutions,
                    unresolved_symbols,
                    evaluated_terms,
                    display_name,
                    display_argument,
                ) = evaluator.partial_numeric_evaluation
                return PartialNumericEvaluationResult(
                    statement=statement,
                    symbolic_expression=symbolic_expression,
                    substitutions=substitutions,
                    unresolved_symbols=unresolved_symbols,
                    evaluated_terms=evaluated_terms,
                    display_name=display_name,
                    display_argument=display_argument,
                )

            if evaluator.numeric_evaluation is not None:
                (
                    symbolic_expression,
                    substitutions,
                    quantity,
                    display_name,
                    display_argument,
                ) = evaluator.numeric_evaluation
                return NumericEvaluationResult(
                    statement=statement,
                    symbolic_expression=symbolic_expression,
                    substitutions=substitutions,
                    quantity=quantity,
                    display_name=display_name,
                    display_argument=display_argument,
                )

            if statement.target is not None:
                if statement.parameter is not None:
                    self.resolve_name(statement.parameter)
                    self.functions[statement.target] = UserFunction(
                        parameter=statement.parameter,
                        expression=value,
                    )
                else:
                    self.namespace[statement.target] = value
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
    def __init__(self, engine: EngineeringEngine) -> None:
        self.engine = engine
        self.display_input = None
        self.numeric_evaluation = None
        self.partial_numeric_evaluation = None
        self.plot_evaluation: _PlotEvaluation | None = None
        self.symbol_overrides: dict[str, sp.Symbol] = {}

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

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, bool) or node.value is None:
            raise EngEvaluationError("only numeric constants are supported")
        if isinstance(node.value, int):
            return sp.Integer(node.value)
        if isinstance(node.value, float):
            return sp.Float(str(node.value))
        raise EngEvaluationError("only numeric constants are supported")

    def visit_Name(self, node: ast.Name):
        if node.id in self.symbol_overrides:
            return self.symbol_overrides[node.id]
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
        if isinstance(node.op, ast.Add): return left + right
        if isinstance(node.op, ast.Sub): return left - right
        if isinstance(node.op, ast.Mult): return left * right
        if isinstance(node.op, ast.Div): return left / right
        if isinstance(node.op, ast.Pow): return left ** right
        raise EngEvaluationError("unsupported operator")

    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name):
            raise EngSyntaxError(f"unsupported syntax '{type(node.func).__name__}'")
        name = node.func.id

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

        if name == "plot":
            return self._evaluate_plot(node)

        if name == "envelope":
            return self._evaluate_envelope(node)

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
            display_argument = None

            if (
                isinstance(argument, ast.Call)
                and isinstance(argument.func, ast.Name)
                and argument.func.id in self.engine.functions
            ):
                function_name = argument.func.id
                if len(argument.args) != 1:
                    raise EngEvaluationError(
                        f"function '{function_name}' expects 1 argument"
                    )
                function = self.engine.functions[function_name]
                argument_node = argument.args[0]
                argument_expression = self.visit(argument_node)
                argument_value = self._resolve_numeric_function_argument(argument_node)
                symbolic_expression = sp.sympify(function.expression)
                display_name = function_name
                display_argument = argument_expression

                if (
                    isinstance(argument_node, ast.Name)
                    and isinstance(argument_value, sp.Symbol)
                    and self.engine.numeric_context.get(argument_node.id) is None
                ):
                    if target_unit is not None:
                        raise EngEvaluationError(
                            "target-unit conversion requires a fully numeric result"
                        )
                    parameter = self.engine.resolve_symbol(function.parameter)
                    symbolic_expression = symbolic_expression.subs(
                        parameter,
                        argument_value,
                    )
                    substitutions, unresolved_symbols = (
                        self.engine.numeric_context.partial_substitutions(
                            symbolic_expression,
                            allowed_unresolved={argument_node.id},
                        )
                    )
                    evaluated_terms = self.engine.numeric_context.evaluate_partial_polynomial(
                        symbolic_expression,
                        argument_node.id,
                    )
                    self.partial_numeric_evaluation = (
                        symbolic_expression,
                        substitutions,
                        unresolved_symbols,
                        evaluated_terms,
                        display_name,
                        display_argument,
                    )
                    return symbolic_expression

                try:
                    substitutions, quantity = self.engine.numeric_context.evaluate_symbolic(
                        symbolic_expression,
                        overrides={function.parameter: argument_value},
                    )
                except EngEvaluationError as exc:
                    if "incompatible units" not in str(exc):
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
                display_argument,
            )
            return symbolic_expression

        if name == "solve":
            self._require_arity(name, node.args, 2, "equation, unknown")
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
                raise AmbiguousSolveError(
                    f"solve returned {len(solutions)} solutions for {unknown}; v0.1 requires one"
                )
            return solutions[0]

        args = [self.visit(arg) for arg in node.args]

        if name in self.engine.functions:
            if len(args) != 1:
                raise EngEvaluationError(f"function '{name}' expects 1 argument")
            function = self.engine.functions[name]
            parameter = self.engine.resolve_name(function.parameter)
            return sp.sympify(function.expression).subs(parameter, args[0])

        if name == "abs":
            self._require_arity(name, args, 1, "expression")
            return sp.Abs(args[0])

        if name == "integral":
            self._require_arity(name, args, 4, "expression, variable, lower, upper")
            expr, var, lower, upper = args
            self.display_input = sp.Integral(expr, (var, lower, upper))
            return sp.integrate(expr, (var, lower, upper))

        if name == "diff":
            if len(args) not in (2, 3):
                raise EngEvaluationError(
                    "diff expects 2 or 3 arguments: expression, variable[, order]"
                )
            expr, var = args[:2]
            order = int(args[2]) if len(args) == 3 else 1
            self.display_input = sp.Derivative(expr, (var, order))
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
            return operation(args[0])

        if name == "subs":
            self._require_arity(name, args, 3, "expression, variable, value")
            return sp.sympify(args[0]).subs(args[1], args[2])

        raise EngSyntaxError(f"unsupported function '{name}'")

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
            ),
            PlotSeries(
                display_label=minimum_label,
                y_values=tuple(minimum_values),
                is_moment=is_moment,
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
        _, start_quantity = self.engine.numeric_context.evaluate_symbolic(start_expression)
        _, end_quantity = self.engine.numeric_context.evaluate_symbolic(end_expression)
        start_quantity, end_quantity = self.engine.numeric_context.normalize_plot_bounds(
            start_quantity,
            end_quantity,
        )

        resolved_expressions = [
            self._resolve_response_expression(item, variable)
            for item in expression_nodes
        ]
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
            x_values = None
            for expression in resolved_expressions:
                series_x, y_values = self.engine.numeric_context.sample_symbolic(
                    expression.comparison_expression,
                    variable,
                    start_quantity,
                    end_quantity,
                    count=201,
                )
                source_x, source_y_values = self.engine.numeric_context.sample_symbolic(
                    expression.signed_expression,
                    variable,
                    start_quantity,
                    end_quantity,
                    count=201,
                )
                if x_values is None:
                    x_values = series_x
                raw_series.append(
                    PlotSeries(
                        display_label=expression.display_label,
                        y_values=y_values,
                        is_moment=self._is_moment_label(expression.source_label),
                    )
                )
                raw_source_series.append(
                    PlotSeries(
                        display_label=expression.source_label,
                        y_values=source_y_values,
                        is_moment=self._is_moment_label(expression.source_label),
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
        x_values = None
        for sweep_value in sweep_values:
            overrides = {parameter_name: sweep_value}
            series_x, comparison_y_values = (
                self.engine.numeric_context.sample_symbolic(
                    comparison_expression,
                    variable,
                    start_quantity,
                    end_quantity,
                    count=201,
                    overrides=overrides,
                )
            )
            if preserve_signed_source:
                _, source_y_values = self.engine.numeric_context.sample_symbolic(
                    signed_expression,
                    variable,
                    start_quantity,
                    end_quantity,
                    count=201,
                    overrides=overrides,
                )
            else:
                source_y_values = comparison_y_values

            if x_values is None:
                x_values = series_x
            case_label = (
                f"{parameter_name} = {self._format_plot_quantity(sweep_value)}"
            )
            comparison_series.append(
                PlotSeries(
                    display_label=case_label,
                    y_values=comparison_y_values,
                    is_moment=is_moment,
                )
            )
            source_series.append(
                PlotSeries(
                    display_label=case_label,
                    y_values=source_y_values,
                    is_moment=is_moment,
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
            except DimensionalityError as exc:
                raise EngEvaluationError(
                    f"{call_name} series have incompatible y dimensions"
                ) from exc
            normalized.append(
                PlotSeries(
                    display_label=item.display_label,
                    y_values=y_values,
                    is_moment=item.is_moment,
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
    def _require_arity(name: str, args: list, count: int, signature: str) -> None:
        if len(args) != count:
            noun = "argument" if count == 1 else "arguments"
            raise EngEvaluationError(f"{name} expects {count} {noun}: {signature}")
