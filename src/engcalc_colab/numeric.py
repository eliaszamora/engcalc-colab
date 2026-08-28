from __future__ import annotations

import ast
import numbers
from functools import reduce
from operator import mul
from typing import Any

import sympy as sp
from pint import UnitRegistry
from pint.errors import DimensionalityError, PintError
from sympy.polys.polyerrors import PolynomialError

from .errors import EngEvaluationError


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

    def assign(self, name: str, expression: ast.Expression):
        try:
            value = _NumericAstEvaluator(self).visit(expression.body)
            quantity = self._as_quantity(value)
        except EngEvaluationError:
            raise
        except DimensionalityError as exc:
            raise EngEvaluationError("incompatible units") from exc
        except PintError as exc:
            raise EngEvaluationError(f"numeric unit evaluation failed: {exc}") from exc
        except Exception as exc:
            raise EngEvaluationError(f"numeric evaluation failed: {exc}") from exc

        self.values[name] = quantity
        return quantity

    def resolve_numeric_name(self, name: str):
        if name in self.values:
            return self.values[name]
        if name in _UNIT_ALIASES:
            return self.ureg.Unit(_UNIT_ALIASES[name])
        raise EngEvaluationError(f"unknown numeric name '{name}'")

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

    def partial_substitutions(
        self,
        expression: sp.Expr,
        allowed_unresolved: set[str],
    ) -> tuple[dict[str, Any], tuple[str, ...]]:
        expr = sp.sympify(expression)
        names = sorted(symbol.name for symbol in expr.free_symbols)
        missing = [
            name
            for name in names
            if name not in self.values and name not in allowed_unresolved
        ]
        if missing:
            raise EngEvaluationError(
                "numeric evaluation requires values for: " + ", ".join(missing)
            )

        substitutions = {
            name: self.values[name]
            for name in names
            if name in self.values
        }
        unresolved = tuple(
            name
            for name in names
            if name not in substitutions
        )
        return substitutions, unresolved

    def evaluate_partial_polynomial(
        self,
        expression: sp.Expr,
        variable: str,
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
            _, quantity = self.evaluate_symbolic(coefficient)
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
            raise EngEvaluationError(
                "numeric evaluation requires values for: " + ", ".join(missing)
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

    def _evaluate_sympy(self, expr, substitutions: dict[str, Any]):
        if isinstance(expr, sp.Symbol):
            return substitutions[expr.name]

        if expr.is_Number:
            if expr.is_Integer:
                return int(expr)
            if expr.is_Rational:
                return int(expr.p) / int(expr.q)
            return float(expr)

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
