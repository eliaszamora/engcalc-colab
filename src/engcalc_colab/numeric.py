from __future__ import annotations

import ast
import math
import numbers
from functools import reduce
from operator import mul
from typing import Any

import sympy as sp
from pint import UnitRegistry
from pint.errors import DimensionalityError, PintError
from sympy.polys.polyerrors import PolynomialError

from .errors import EngEvaluationError, diagnostic_hint


_UNIT_ALIASES = {
    "mm": "millimeter",
    "cm": "centimeter",
    "m": "meter",
    "N": "newton",
    "kN": "kilonewton",
    "kgf": "kilogram_force",
    "tonf": "tonf",
    "Pa": "pascal",
    "kPa": "kilopascal",
    "MPa": "megapascal",
    "GPa": "gigapascal",
    "kg": "kilogram",
    "s": "second",
    "rad": "radian",
    "deg": "degree",
}


class NumericContext:
    """Pint-backed numeric values kept separate from EngCalc symbolic state."""

    def __init__(self) -> None:
        self.ureg = UnitRegistry()
        self.ureg.define("tonf = 9.80665 * kilonewton")
        self.values: dict[str, Any] = {}

    def reset(self) -> None:
        self.values.clear()

    def get(self, name: str):
        return self.values.get(name)

    def evaluate_expression(self, expression: ast.Expression):
        try:
            value = _NumericAstEvaluator(self).visit(expression.body)
            return self._as_quantity(value)
        except EngEvaluationError:
            raise
        except DimensionalityError as exc:
            raise EngEvaluationError("incompatible units") from exc
        except PintError as exc:
            raise EngEvaluationError(f"numeric unit evaluation failed: {exc}") from exc
        except Exception as exc:
            raise EngEvaluationError(f"numeric evaluation failed: {exc}") from exc

    def assign(self, name: str, expression: ast.Expression):
        quantity = self.evaluate_expression(expression)
        self.values[name] = quantity
        return quantity

    def resolve_numeric_name(self, name: str):
        if name in self.values:
            return self.values[name]
        if name == "pi":
            return math.pi
        if name in _UNIT_ALIASES:
            return self.ureg.Unit(_UNIT_ALIASES[name])
        hint = diagnostic_hint("unknown_numeric_name", name=name)
        raise EngEvaluationError(f"unknown numeric name '{name}'. {hint}")

    def _has_explicit_angle_unit(self, quantity) -> bool:
        return (
            quantity.units == self.ureg.degree
            or quantity.units == self.ureg.radian
        )

    def evaluate_scalar_function(self, name: str, value):
        quantity = self._as_quantity(value)

        if name == "sqrt":
            return quantity ** 0.5

        forward_trig = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
        }
        if name in forward_trig:
            try:
                angle = quantity.to(self.ureg.radian)
            except DimensionalityError as exc:
                raise EngEvaluationError(
                    f"{name} requires a dimensionless or angle argument"
                ) from exc
            return forward_trig[name](float(angle.magnitude))

        inverse_trig = {
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
        }
        if name in inverse_trig:
            if self._has_explicit_angle_unit(quantity) or not quantity.dimensionless:
                raise EngEvaluationError(f"{name} requires a dimensionless argument")
            magnitude = float(quantity.to_base_units().magnitude)
            return self.ureg.Quantity(inverse_trig[name](magnitude), self.ureg.radian)

        scalar_dimensionless = {
            "exp": math.exp,
            "log": math.log,
        }
        if name in scalar_dimensionless:
            if self._has_explicit_angle_unit(quantity) or not quantity.dimensionless:
                raise EngEvaluationError(f"{name} requires a dimensionless argument")
            magnitude = float(quantity.to_base_units().magnitude)
            return scalar_dimensionless[name](magnitude)

        raise EngEvaluationError(f"unsupported numeric function '{name}'")

    def resolve_target_unit_name(self, name: str):
        if name in _UNIT_ALIASES:
            return self.ureg.Unit(_UNIT_ALIASES[name])
        raise EngEvaluationError(f"unknown target unit '{name}'")

    def evaluate_unit_expression(self, expression: ast.Expression):
        """Evaluate a restricted target-unit expression without consulting numeric values."""
        try:
            unit = _UnitAstEvaluator(self).visit(expression.body)
        except EngEvaluationError:
            raise
        except PintError as exc:
            raise EngEvaluationError(f"target unit evaluation failed: {exc}") from exc
        except Exception as exc:
            raise EngEvaluationError(f"target unit evaluation failed: {exc}") from exc

        if isinstance(unit, numbers.Number) or hasattr(unit, "magnitude"):
            raise EngEvaluationError("target unit must be a unit expression")
        if not hasattr(unit, "dimensionality"):
            raise EngEvaluationError("target unit must be a unit expression")
        return unit

    def convert_quantity(self, quantity, target_unit):
        try:
            return quantity.to(target_unit)
        except DimensionalityError as exc:
            raise EngEvaluationError("target unit is incompatible with result") from exc
        except PintError as exc:
            raise EngEvaluationError(f"target unit conversion failed: {exc}") from exc

    def normalize_plot_bounds(self, start, end):
        start = self._as_quantity(start)
        end = self._as_quantity(end)

        if start.dimensionless and not end.dimensionless:
            if float(start.magnitude) != 0.0:
                raise EngEvaluationError("plot bounds have incompatible units")
            start = self.ureg.Quantity(0, end.units)
        elif end.dimensionless and not start.dimensionless:
            if float(end.magnitude) != 0.0:
                raise EngEvaluationError("plot bounds have incompatible units")
            end = self.ureg.Quantity(0, start.units)

        try:
            end = end.to(start.units)
        except DimensionalityError as exc:
            raise EngEvaluationError("plot bounds have incompatible units") from exc

        if float(end.magnitude) <= float(start.magnitude):
            raise EngEvaluationError("plot end must be greater than start")
        return start, end

    def sample_symbolic(
        self,
        expression,
        variable,
        start,
        end,
        count=201,
        overrides: dict[str, Any] | None = None,
    ):
        if count < 2:
            raise EngEvaluationError("plot sampling requires at least 2 points")

        start, end = self.normalize_plot_bounds(start, end)
        delta = end - start
        xs = tuple(start + delta * (index / (count - 1)) for index in range(count))
        fixed_overrides = dict(overrides or {})

        ys = []
        y_unit = None
        for x_value in xs:
            sample_overrides = dict(fixed_overrides)
            sample_overrides[variable] = x_value
            _, y_value = self.evaluate_symbolic(
                expression,
                overrides=sample_overrides,
            )
            if y_unit is None:
                y_unit = y_value.units
            try:
                y_value = y_value.to(y_unit)
            except DimensionalityError as exc:
                raise EngEvaluationError("plot samples have incompatible result units") from exc
            ys.append(y_value)

        return xs, tuple(ys)

    def build_plot_sample_points(
        self,
        expression_cases,
        variable,
        start,
        end,
        count=201,
    ):
        from .piecewise import extract_symbolic_breakpoints

        if count < 2:
            raise EngEvaluationError("plot sampling requires at least 2 points")
        start, end = self.normalize_plot_bounds(start, end)
        delta = end - start
        points = [
            start + delta * (index / (count - 1))
            for index in range(count)
        ]

        for expression, overrides in expression_cases:
            for breakpoint_expression in extract_symbolic_breakpoints(
                sp.sympify(expression),
                variable,
            ):
                try:
                    _, breakpoint = self.evaluate_symbolic(
                        breakpoint_expression,
                        overrides=dict(overrides or {}),
                    )
                except EngEvaluationError as exc:
                    raise EngEvaluationError(
                        "plot Piecewise breakpoint must be numerically resolvable: "
                        + str(exc)
                    ) from None

                breakpoint = self._as_quantity(breakpoint)
                if breakpoint.dimensionless and not start.dimensionless:
                    if float(breakpoint.magnitude) != 0.0:
                        raise EngEvaluationError(
                            "plot Piecewise breakpoint has incompatible units"
                        )
                    breakpoint = self.ureg.Quantity(0, start.units)
                try:
                    breakpoint = breakpoint.to(start.units)
                except DimensionalityError as exc:
                    raise EngEvaluationError(
                        "plot Piecewise breakpoint has incompatible units"
                    ) from exc

                magnitude = float(breakpoint.magnitude)
                if float(start.magnitude) <= magnitude <= float(end.magnitude):
                    points.append(breakpoint)

        ordered = sorted(
            points,
            key=lambda quantity: float(quantity.to(start.units).magnitude),
        )
        unique = []
        for point in ordered:
            point = point.to(start.units)
            if unique and math.isclose(
                float(point.magnitude),
                float(unique[-1].magnitude),
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                continue
            unique.append(point)
        return tuple(unique)

    def sample_symbolic_points(
        self,
        expression,
        variable,
        points,
        overrides: dict[str, Any] | None = None,
    ):
        fixed_overrides = dict(overrides or {})
        values = []
        for point in points:
            sample_overrides = dict(fixed_overrides)
            sample_overrides[variable] = point
            _, value = self.evaluate_symbolic(
                expression,
                overrides=sample_overrides,
            )
            values.append(value)
        try:
            return self._normalize_quantity_group(values, "plot samples")
        except EngEvaluationError as exc:
            raise EngEvaluationError("plot samples have incompatible result units") from exc

    def _piecewise_branch_signature(
        self,
        expression,
        substitutions: dict[str, Any],
    ) -> tuple[int, ...]:
        signature: list[int] = []

        def visit(node):
            node = sp.sympify(node)
            if isinstance(node, sp.Piecewise):
                for index, (branch_expression, condition) in enumerate(node.args):
                    if condition == sp.true or self._evaluate_relation(
                        condition, substitutions
                    ):
                        signature.append(index)
                        visit(branch_expression)
                        return
                raise EngEvaluationError("piecewise has no governing branch")
            for argument in node.args:
                visit(argument)

        visit(expression)
        return tuple(signature)

    def piecewise_segment_starts(
        self,
        expression,
        variable: str,
        points,
        overrides: dict[str, Any] | None = None,
    ) -> tuple[int, ...]:
        expression = sp.sympify(expression)
        fixed_overrides = dict(overrides or {})
        names = sorted(symbol.name for symbol in expression.free_symbols)
        previous = None
        starts: list[int] = []
        for index, point in enumerate(points):
            sample_overrides = {**fixed_overrides, variable: point}
            substitutions = {
                name: (
                    sample_overrides[name]
                    if name in sample_overrides
                    else self.values[name]
                )
                for name in names
            }
            signature = self._piecewise_branch_signature(
                expression, substitutions
            )
            if index and signature != previous:
                starts.append(index)
            previous = signature
        return tuple(starts)

    def ensure_not_derivative_breakpoint(
        self,
        variable: str,
        value,
        breakpoints,
        overrides: dict[str, Any] | None = None,
    ) -> None:
        overrides = dict(overrides or {})
        value = self._as_quantity(value)
        for breakpoint_expression in breakpoints:
            _, breakpoint = self.evaluate_symbolic(
                sp.sympify(breakpoint_expression),
                overrides=overrides,
            )
            left, right = self._normalize_relation_operands(value, breakpoint)
            if math.isclose(
                float(left.magnitude),
                float(right.magnitude),
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                unit = f" {right.units:~P}" if not right.dimensionless else ""
                raise EngEvaluationError(
                    "derivative is undefined at explicit Piecewise breakpoint "
                    f"{variable} = {float(right.magnitude):g}{unit}"
                )

    def partial_substitutions(
        self,
        expression: sp.Expr,
        allowed_unresolved: set[str] | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], tuple[str, ...]]:
        expr = sp.sympify(expression)
        overrides = dict(overrides or {})
        names = sorted(symbol.name for symbol in expr.free_symbols)
        substitutions = {
            name: overrides[name] if name in overrides else self.values[name]
            for name in names
            if name in overrides or name in self.values
        }
        unresolved = tuple(
            name
            for name in names
            if name not in substitutions
        )

        if allowed_unresolved is not None:
            unexpected = [
                name
                for name in unresolved
                if name not in allowed_unresolved
            ]
            if unexpected:
                hint = diagnostic_hint(
                    "unresolved_numeric_symbols",
                    names=tuple(unexpected),
                )
                raise EngEvaluationError(
                    "numeric evaluation requires values for: "
                    + ", ".join(unexpected)
                    + f". {hint}"
                )

        return substitutions, unresolved

    def evaluate_partial_polynomial(
        self,
        expression: sp.Expr,
        variable: str,
        overrides: dict[str, Any] | None = None,
    ) -> tuple[tuple[int, Any], ...] | None:
        """Evaluate known coefficients of a polynomial while leaving its variable free."""
        expr = sp.sympify(expression)
        symbol = sp.Symbol(variable)
        try:
            polynomial = sp.Poly(expr, symbol)
        except PolynomialError:
            return None

        evaluated_terms: list[tuple[int, Any]] = []
        for (power,), coefficient in reversed(polynomial.terms()):
            _, quantity = self.evaluate_symbolic(
                coefficient,
                overrides=overrides,
            )
            evaluated_terms.append((int(power), quantity))
        return tuple(evaluated_terms)

    def evaluate_symbolic(
        self,
        expression: sp.Expr,
        overrides: dict[str, Any] | None = None,
    ):
        expr = sp.sympify(expression)
        overrides = overrides or {}
        names = sorted(symbol.name for symbol in expr.free_symbols)
        missing = [
            name
            for name in names
            if name not in overrides and name not in self.values
        ]
        if missing:
            hint = diagnostic_hint("unresolved_numeric_symbols", names=tuple(missing))
            raise EngEvaluationError(
                "numeric evaluation requires values for: "
                + ", ".join(missing)
                + f". {hint}"
            )

        substitutions = {
            name: overrides[name] if name in overrides else self.values[name]
            for name in names
        }
        try:
            value = self._evaluate_sympy(expr, substitutions)
            quantity = self._as_quantity(value)
        except EngEvaluationError:
            raise
        except DimensionalityError as exc:
            raise EngEvaluationError("incompatible units") from exc
        except PintError as exc:
            raise EngEvaluationError(f"numeric unit evaluation failed: {exc}") from exc
        except Exception as exc:
            raise EngEvaluationError(f"numeric evaluation failed: {exc}") from exc
        return substitutions, quantity

    def _is_exact_zero_quantity(self, value) -> bool:
        quantity = self._as_quantity(value)
        return float(quantity.magnitude) == 0.0

    def _normalize_relation_operands(self, left, right):
        left_quantity = self._as_quantity(left)
        right_quantity = self._as_quantity(right)

        if left_quantity.dimensionless and not right_quantity.dimensionless:
            if not self._is_exact_zero_quantity(left_quantity):
                raise EngEvaluationError(
                    "piecewise comparison cannot mix a dimensional quantity with "
                    "a nonzero dimensionless value"
                )
            left_quantity = self.ureg.Quantity(0, right_quantity.units)
        elif right_quantity.dimensionless and not left_quantity.dimensionless:
            if not self._is_exact_zero_quantity(right_quantity):
                raise EngEvaluationError(
                    "piecewise comparison cannot mix a dimensional quantity with "
                    "a nonzero dimensionless value"
                )
            right_quantity = self.ureg.Quantity(0, left_quantity.units)

        try:
            right_quantity = right_quantity.to(left_quantity.units)
        except DimensionalityError as exc:
            raise EngEvaluationError(
                "piecewise comparison has incompatible units"
            ) from exc
        return left_quantity, right_quantity

    def _evaluate_relation(self, relation, substitutions: dict[str, Any]) -> bool:
        left = self._evaluate_sympy(relation.lhs, substitutions)
        right = self._evaluate_sympy(relation.rhs, substitutions)
        left, right = self._normalize_relation_operands(left, right)

        if relation.func == sp.StrictLessThan:
            return left.magnitude < right.magnitude
        if relation.func == sp.LessThan:
            return left.magnitude <= right.magnitude
        if relation.func == sp.StrictGreaterThan:
            return left.magnitude > right.magnitude
        if relation.func == sp.GreaterThan:
            return left.magnitude >= right.magnitude
        raise EngEvaluationError("unsupported piecewise relation")

    def _normalize_quantity_group(self, values, context: str):
        quantities = tuple(self._as_quantity(value) for value in values)
        dimensional = next(
            (quantity for quantity in quantities if not quantity.dimensionless),
            None,
        )
        if dimensional is None:
            return quantities

        unit = dimensional.units
        normalized = []
        for quantity in quantities:
            if quantity.dimensionless:
                if self._is_exact_zero_quantity(quantity):
                    normalized.append(self.ureg.Quantity(0, unit))
                    continue
                raise EngEvaluationError(
                    f"{context} cannot mix dimensional quantities with "
                    "a nonzero dimensionless value"
                )
            try:
                normalized.append(quantity.to(unit))
            except DimensionalityError as exc:
                raise EngEvaluationError(f"{context} has incompatible units") from exc
        return tuple(normalized)

    def _infer_piecewise_zero_unit(self, expression, substitutions: dict[str, Any]):
        canonical_unit = None
        saw_nonzero_dimensionless = False

        for branch_expression, _condition in expression.args:
            try:
                candidate = self._as_quantity(
                    self._evaluate_sympy(branch_expression, substitutions)
                )
            except (
                EngEvaluationError,
                DimensionalityError,
                PintError,
                ValueError,
                ZeroDivisionError,
                OverflowError,
            ):
                continue

            if candidate.dimensionless:
                if self._is_exact_zero_quantity(candidate):
                    continue
                if canonical_unit is not None:
                    raise EngEvaluationError(
                        "piecewise has nonzero dimensionless branch incompatible "
                        "with dimensional branch"
                    )
                saw_nonzero_dimensionless = True
                continue

            if saw_nonzero_dimensionless:
                raise EngEvaluationError(
                    "piecewise has nonzero dimensionless branch incompatible "
                    "with dimensional branch"
                )

            if canonical_unit is None:
                canonical_unit = candidate.units
                continue

            try:
                candidate.to(canonical_unit)
            except (DimensionalityError, PintError) as exc:
                raise EngEvaluationError(
                    "piecewise has incompatible branch units"
                ) from exc

        return canonical_unit

    def _evaluate_piecewise(self, expression, substitutions: dict[str, Any]):
        for branch_expression, condition in expression.args:
            if condition == sp.true or self._evaluate_relation(condition, substitutions):
                value = self._as_quantity(
                    self._evaluate_sympy(branch_expression, substitutions)
                )
                if value.dimensionless and self._is_exact_zero_quantity(value):
                    inferred_unit = self._infer_piecewise_zero_unit(
                        expression,
                        substitutions,
                    )
                    if inferred_unit is not None:
                        return self.ureg.Quantity(0, inferred_unit)
                return value
        raise EngEvaluationError("piecewise has no governing branch")

    def build_partial_piecewise_evaluation(
        self,
        expression,
        variable: str,
        overrides: dict[str, Any] | None = None,
    ):
        from .models import PiecewisePartialBranch, PiecewisePartialEvaluation

        expression = sp.sympify(expression)
        if not isinstance(expression, sp.Piecewise):
            return None

        symbol = sp.Symbol(variable)
        overrides = dict(overrides or {})
        operator_direct = {
            sp.StrictLessThan: "<",
            sp.LessThan: "<=",
            sp.StrictGreaterThan: ">",
            sp.GreaterThan: ">=",
        }
        operator_reverse = {
            sp.StrictLessThan: ">",
            sp.LessThan: ">=",
            sp.StrictGreaterThan: "<",
            sp.GreaterThan: "<=",
        }

        branches = []
        resolved_indices = []
        resolved_values = []
        for branch_expression, condition in expression.args:
            branch_expression = sp.sympify(branch_expression)
            evaluated_terms = None
            if symbol not in branch_expression.free_symbols:
                _, value = self.evaluate_symbolic(
                    branch_expression,
                    overrides=overrides,
                )
                resolved_indices.append(len(branches))
                resolved_values.append(value)
            else:
                value = branch_expression
                evaluated_terms = self.evaluate_partial_polynomial(
                    branch_expression,
                    variable,
                    overrides=overrides,
                )

            operator = None
            breakpoint = None
            if condition != sp.true:
                if not isinstance(condition, sp.Rel):
                    raise EngEvaluationError("piecewise condition must be relational")
                if condition.lhs == symbol and symbol not in condition.rhs.free_symbols:
                    operator = operator_direct.get(condition.func)
                    breakpoint_expression = condition.rhs
                elif condition.rhs == symbol and symbol not in condition.lhs.free_symbols:
                    operator = operator_reverse.get(condition.func)
                    breakpoint_expression = condition.lhs
                else:
                    raise EngEvaluationError(
                        "piecewise condition must compare the interval variable directly "
                        "with a breakpoint"
                    )
                if operator is None:
                    raise EngEvaluationError("unsupported piecewise relation")
                _, breakpoint = self.evaluate_symbolic(
                    breakpoint_expression,
                    overrides=overrides,
                )

            branches.append({
                "value": value,
                "operator": operator,
                "breakpoint": breakpoint,
                "evaluated_terms": evaluated_terms,
            })

        if resolved_values:
            normalized = self._normalize_quantity_group(
                resolved_values,
                "piecewise branches",
            )
            for index, value in zip(resolved_indices, normalized):
                branches[index]["value"] = value

        return PiecewisePartialEvaluation(
            interval_variable=variable,
            branches=tuple(PiecewisePartialBranch(**branch) for branch in branches),
        )

    def _evaluate_sympy(self, expr, substitutions: dict[str, Any]):
        if isinstance(expr, sp.Symbol):
            return substitutions[expr.name]

        if expr == sp.pi:
            return math.pi

        if expr.is_Number:
            if expr.is_Integer:
                return int(expr)
            if expr.is_Rational:
                return int(expr.p) / int(expr.q)
            return float(expr)

        if expr.func == sp.Piecewise:
            return self._evaluate_piecewise(expr, substitutions)

        if expr.func in {
            sp.StrictLessThan,
            sp.LessThan,
            sp.StrictGreaterThan,
            sp.GreaterThan,
        }:
            return self._evaluate_relation(expr, substitutions)

        if expr.func in {sp.Min, sp.Max}:
            values = self._normalize_quantity_group(
                (self._evaluate_sympy(arg, substitutions) for arg in expr.args),
                "numeric Min/Max",
            )
            selector = min if expr.func == sp.Min else max
            return selector(values, key=lambda quantity: quantity.magnitude)

        if expr.is_Add:
            values = [self._evaluate_sympy(arg, substitutions) for arg in expr.args]
            result = values[0]
            for value in values[1:]:
                result = result + value
            return result

        if expr.is_Mul:
            return reduce(
                mul,
                (self._evaluate_sympy(arg, substitutions) for arg in expr.args),
                1,
            )

        if expr.is_Pow:
            base = self._evaluate_sympy(expr.base, substitutions)
            exponent = self._evaluate_sympy(expr.exp, substitutions)
            if hasattr(exponent, "dimensionality"):
                if not exponent.dimensionless:
                    raise EngEvaluationError("numeric exponent must be dimensionless")
                exponent = exponent.to_base_units().magnitude
            return base ** exponent

        if expr.func == sp.Abs and len(expr.args) == 1:
            return abs(self._evaluate_sympy(expr.args[0], substitutions))

        scalar_sympy = {
            sp.sin: "sin",
            sp.cos: "cos",
            sp.tan: "tan",
            sp.asin: "asin",
            sp.acos: "acos",
            sp.atan: "atan",
            sp.exp: "exp",
            sp.log: "log",
        }
        if expr.func in scalar_sympy and len(expr.args) == 1:
            value = self._evaluate_sympy(expr.args[0], substitutions)
            return self.evaluate_scalar_function(scalar_sympy[expr.func], value)

        raise EngEvaluationError(
            f"numeric evaluation does not support symbolic type '{type(expr).__name__}'"
        )

    def _as_quantity(self, value):
        if isinstance(value, numbers.Number):
            return self.ureg.Quantity(value)
        if hasattr(value, "magnitude") and hasattr(value, "units"):
            return value
        if hasattr(value, "dimensionality"):
            return self.ureg.Quantity(1, value)
        raise EngEvaluationError("numeric expression did not produce a quantity")


class _NumericAstEvaluator(ast.NodeVisitor):
    def __init__(self, context: NumericContext) -> None:
        self.context = context

    def generic_visit(self, node):
        raise EngEvaluationError(f"unsupported numeric syntax '{type(node).__name__}'")

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, bool) or node.value is None:
            raise EngEvaluationError("numeric assignments require numeric constants")
        if isinstance(node.value, (int, float)):
            return node.value
        raise EngEvaluationError("numeric assignments require numeric constants")

    def visit_Name(self, node: ast.Name):
        return self.context.resolve_numeric_name(node.id)

    def visit_Call(self, node: ast.Call):
        if (
            not isinstance(node.func, ast.Name)
            or len(node.args) != 1
            or node.keywords
        ):
            raise EngEvaluationError("unsupported numeric function")
        name = node.func.id
        value = self.visit(node.args[0])
        if name == "abs":
            return abs(value)
        if name in {"sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "exp", "log"}:
            return self.context.evaluate_scalar_function(name, value)
        raise EngEvaluationError("unsupported numeric function")

    def visit_UnaryOp(self, node: ast.UnaryOp):
        value = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
        raise EngEvaluationError("unsupported numeric unary operator")

    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)
        try:
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                return left ** right
        except DimensionalityError as exc:
            raise EngEvaluationError("incompatible units") from exc
        except PintError as exc:
            raise EngEvaluationError(f"numeric unit evaluation failed: {exc}") from exc
        raise EngEvaluationError("unsupported numeric operator")


class _UnitAstEvaluator(ast.NodeVisitor):
    def __init__(self, context: NumericContext) -> None:
        self.context = context

    def generic_visit(self, node):
        raise EngEvaluationError(f"unsupported target unit syntax '{type(node).__name__}'")

    def visit_Name(self, node: ast.Name):
        return self.context.resolve_target_unit_name(node.id)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, bool) or node.value is None:
            raise EngEvaluationError("target unit exponents must be numeric")
        if isinstance(node.value, (int, float)):
            return node.value
        raise EngEvaluationError("target unit exponents must be numeric")

    def visit_UnaryOp(self, node: ast.UnaryOp):
        value = self.visit(node.operand)
        if not isinstance(value, numbers.Number):
            raise EngEvaluationError("target unit unary signs are only valid for exponents")
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
        raise EngEvaluationError("unsupported target unit unary operator")

    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)
        try:
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                if not isinstance(right, numbers.Number):
                    raise EngEvaluationError("target unit exponent must be numeric")
                return left ** right
        except PintError as exc:
            raise EngEvaluationError(f"target unit evaluation failed: {exc}") from exc
        raise EngEvaluationError("target units support only *, /, and powers")
