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

from .unit_text import normalise
from sympy.polys.polyerrors import PolynomialError

from .errors import EngEvaluationError, NoRealValueError, diagnostic_hint
from .matrix_modes import (
    ModeEigenvalue,
    ModeShapeEntry,
    mode_atoms,
    mode_key,
    modes_of,
    numbered,
)
from .interpolation import Interpolation
from .matrix_numeric import QuantityMatrix


_UNIT_ALIASES = {
    "mm": "millimeter",
    "cm": "centimeter",
    "m": "meter",
    "N": "newton",
    "kN": "kilonewton",
    # `MN` is here and deliberately not in `_UNIT_FAMILIES`, and the two tables answer
    # different questions. The families are what the system *chooses*, and #99 took mega
    # out of them because the engineer wanted a sheet that stays in kilonewtons rather
    # than mixing the two prefixes. This table is what the engineer may *write*, and a
    # bridge reaction is written in meganewtons. Without it, `P := 12*MN` was read as an
    # undefined variable and answered with "Define the numeric value first".
    "MN": "meganewton",
    "kgf": "kilogram_force",
    "tonf": "tonf",
    "Pa": "pascal",
    "kPa": "kilopascal",
    "MPa": "megapascal",
    "GPa": "gigapascal",
    "kg": "kilogram",
    # `metric_ton`, never Pint's `ton`, which is the US short ton of 907.18 kg. Pointing
    # at that would have taken ten per cent off every mass on a Spanish-language sheet -
    # a wrong number rather than a wrong unit, and one that survives review by looking
    # plausible. `kip` two entries down carries the same warning about `kilopound`.
    #
    # Defining our own the way `tonf` is defined does not work, and fails silently:
    # `registry.define("ton = 1000 * kilogram")` is accepted without complaint and Pint
    # keeps its own, so `5*ton` stays 4536 kg. The page therefore shows `t`, which is
    # the symbol every code uses for a tonne, rather than the `ton` that was typed.
    "ton": "metric_ton",
    "s": "second",
    # Written and asked for, never chosen: no family has hertz, because a frequency and a
    # circular frequency share `[time]⁻¹` and nothing in a value tells `f` from `ω`. A page
    # that picked it would print `ω_n = 374.98 Hz`. Without it here, `f := 5*Hz` asked the
    # engineer to define the hertz - the answer `MN` got before it joined the table.
    "Hz": "hertz",
    "rad": "radian",
    "deg": "degree",
    # US customary. Pint knows every one of these already, so this is a table of the
    # spellings an engineer writes, not a set of definitions. Two traps it steps around:
    # `inch` rather than `in`, because `in` is a Python keyword and can never be a name
    # here - the parser says what to write instead when somebody tries it; and `kip`,
    # which is Pint's force, where its `kilopound` is a mass of 453 kg, one letter away
    # and never what a structural engineer means by the word.
    "kip": "kip",
    "ksi": "ksi",
    "psi": "psi",
    "inch": "inch",
    "ft": "foot",
}


_ENGINEERING_REGISTRY: UnitRegistry | None = None


def _keep_written_unit_order(items, _registry):
    """Pint's sort hook, made to leave the order alone.

    Its contract is `Iterable[tuple[str, Number, str]] -> Iterable[...]`, and the
    default returns `sorted(items, key=lambda el: el[2])`. Returning the items as given
    is what preserves the order `_units` recorded when the quantity was built.
    """
    return list(items)


def _value_text(value) -> str:
    """A value as a message quotes it: four figures, and its unit when it has one."""
    text = f"{float(getattr(value, 'magnitude', value)):.4g}"
    units = getattr(value, "units", None)
    if units is not None and not value.dimensionless:
        text += f" {units:~P}"
    return text


def _real_power(base, exponent):
    """`base ** exponent`, refused when it has no real value.

    Python answers `(-16) ** 0.5` with a complex number and Pint carries it on, so
    `sqrt(b^2 - 4*a*c)` over a negative discriminant was stored without a word. The
    renderer prints real numbers and raised a TypeError on it: the notebook showed a
    traceback, and not one row of the cell, the ones before it included. Every root and
    fractional power on every path - `:=`, `numeric`, a function at a point, a matrix, a
    table, a plot - is made here, so this is where EngCalc says it works in real numbers.
    """
    result = base ** exponent
    magnitude = getattr(result, "magnitude", result)
    if isinstance(magnitude, numbers.Complex) and not isinstance(magnitude, numbers.Real):
        if getattr(exponent, "magnitude", exponent) == 0.5:
            raise NoRealValueError(
                f"the square root of {_value_text(base)} has no real value; "
                "EngCalc works in real numbers"
            )
        # Not "no real value": -8 has a real cube root, -2. What it has not is a real
        # *principal* power, which is what EngCalc takes, as SymPy and Mathcad do - an
        # exponent arrives as 0.333..., and guessing which decimals mean an odd root would
        # answer some and not others. He chose to keep that and to be told how to write
        # the real root. The independent review of 2026-09-24 caught the old wording.
        # The example is exact only for a cube root of a plain number: `(-27)^(2/3)` is +9,
        # and the minus sign outside `27^(2/3)` would give -9. Any other case gets the
        # rule, with the cube root of -8 to show it.
        cube_root = abs(float(getattr(exponent, "magnitude", exponent)) - 1 / 3) < 1e-12
        if cube_root and getattr(base, "dimensionless", True):
            how = f"For its real cube root, write -({_value_text(-base)}^(1/3))"
        else:
            how = (
                "An odd root of a negative number is real: take the root of its magnitude "
                "and put the sign outside, as -(8^(1/3)) = -2"
            )
        raise NoRealValueError(
            f"{_value_text(base)} raised to a fractional power has no real principal "
            f"value; EngCalc works in real numbers. {how}"
        )
    return result


def engineering_registry() -> UnitRegistry:
    """The one Pint registry this process uses, built on first ask.

    Pint asks for a single registry per application, and not as a style preference:
    quantities built by two registries refuse to meet, with `Cannot operate with Quantity
    and Quantity of different registries`. A notebook holds one context so nothing ever
    reached that, but every `NumericContext` carried its own registry and the hazard with
    it.

    It is also most of the test suite's running time. Pint re-parses its unit definition
    file on every `UnitRegistry()` - about 155 ms - and the suite builds an engine 724
    times across 120 files. Measured on the whole suite: 453 s with a registry per engine,
    179 s with this, 1624 passing either way.

    `tonf` is defined here rather than in `NumericContext.__init__` because a shared
    registry would see that definition once per context, and the second would raise.

    The sort function is replaced so a compound unit keeps the order it was built in.
    Pint's default sorts the factors alphabetically, which is right often enough to hide
    that it is not a rule anybody writes by: a moment is `kN*m` and survives because k
    precedes m, while the same moment in newtons prints `m*N` and an imperial one prints
    `ft*kip` where every US code writes kip-ft. `_units` already carries the order the
    quantity was made with - `N*m` gives newton then meter, `m*N` the reverse - so the
    information was there and only the formatter was discarding it.

    Measured rather than assumed: of every compound unit this suite renders, only `m*N`
    and `ft*kip` move. `kN*m`, `GPa*mm^2/m`, `N/mm^2`, `kg*m/s^2` and `kN/m` are
    identical either way, because for those the written order and the alphabet agree.
    """
    global _ENGINEERING_REGISTRY
    if _ENGINEERING_REGISTRY is None:
        registry = UnitRegistry()
        registry.define("tonf = 9.80665 * kilonewton")
        registry.formatter.default_sort_func = _keep_written_unit_order
        _ENGINEERING_REGISTRY = registry
    return _ENGINEERING_REGISTRY


class NumericContext:
    """Pint-backed numeric values kept separate from EngCalc symbolic state.

    The registry is shared with every other context; the values are not. `reset` clears
    the sheet and leaves the units alone, which is the division a notebook expects from
    `%eng_reset`.
    """

    def __init__(self) -> None:
        self.ureg = engineering_registry()
        self.values: dict[str, Any] = {}
        # `d := solve(K, F)`: matrices of numbers, apart from the scalars. See
        # `engine._MatrixNumbers`.
        self.matrices: dict[str, Any] = {}

    def reset(self) -> None:
        self.values.clear()
        self.matrices.clear()

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
        self.matrices.pop(name, None)
        return quantity

    def written_unit_names(self, expression: ast.Expression) -> frozenset[str]:
        """Names in this assignment's source that the evaluation reads as units.

        What separates `q := 2.8*tonf/m`, where a unit was written down, from
        `phiMn := 0.9*As*fy*z`, where the units arrived from three stored values and
        nothing was declared at all. The renderer needs the difference: it keeps a
        declared unit outright, and on the second kind there is nothing to keep.

        The precedence is not a second rule. `resolve_numeric_name` consults stored
        values before the alias table, so `m := 500*kg` makes `m` a mass; asking the
        same two things in the same order is what stops the page relabelling the
        reader's own quantity as a metre. `unit_literal_names` does this for a symbolic
        expression and its free symbols; an assignment's right-hand side is an AST that
        has not been through SymPy, so the walk is over `ast.Name` instead.

        Its caller asks before ``assign`` stores the target, so the names are read
        against the values the arithmetic actually saw. Reading them afterwards differs
        only for a statement whose right-hand side mentions its own target, and
        `m := 2*m` renders the same either way - the metre is a family member, so the
        band rule returns it whichever answer `declared` gives. Measured, not assumed:
        moving the call after the assignment changes no test. Kept as the order that is
        correct rather than the order that happens to agree.
        """
        return frozenset(
            node.id
            for node in ast.walk(expression)
            if isinstance(node, ast.Name)
            and node.id not in self.values
            and node.id in _UNIT_ALIASES
        )

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
            return _real_power(quantity, 0.5)

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
            # Python's own message said this before, in words that change with its
            # version: `math domain error` on Colab's 3.12, another sentence on 3.14.
            if name != "atan" and not -1 <= magnitude <= 1:
                shown = f"{magnitude:.4g}"
                if -1 <= float(shown) <= 1:
                    # Four figures round the `1.0000000000000002` a division left behind
                    # back to `1`, and `acos of 1` is a value the reader can see is fine.
                    shown = repr(magnitude)
                raise NoRealValueError(
                    f"{name} of {shown} has no real value; "
                    "its argument must lie between -1 and 1"
                )
            return self.ureg.Quantity(inverse_trig[name](magnitude), self.ureg.radian)

        scalar_dimensionless = {
            "exp": math.exp,
            "log": math.log,
        }
        if name in scalar_dimensionless:
            if self._has_explicit_angle_unit(quantity) or not quantity.dimensionless:
                raise EngEvaluationError(f"{name} requires a dimensionless argument")
            magnitude = float(quantity.to_base_units().magnitude)
            if name == "log" and magnitude <= 0:
                raise NoRealValueError(
                    f"the logarithm of {magnitude:.4g} has no real value; "
                    "its argument must be positive"
                )
            return scalar_dimensionless[name](magnitude)

        raise EngEvaluationError(f"unsupported numeric function '{name}'")

    def resolve_target_unit_name(self, name: str):
        if name in _UNIT_ALIASES:
            return self.ureg.Unit(_UNIT_ALIASES[name])
        raise EngEvaluationError(f"unknown target unit '{name}'")

    def unit_literal_overrides(
        self,
        expression,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve free symbols that are direct supported unit literals.

        Explicit overrides take precedence over stored numeric values, and stored
        numeric values take precedence over interpreting a name as a unit alias.
        """
        fixed = dict(overrides or {})
        for symbol in sp.sympify(expression).free_symbols:
            name = symbol.name
            if name in fixed or name in self.values:
                continue
            if name in _UNIT_ALIASES:
                fixed[name] = self.resolve_target_unit_name(name)
        return fixed

    def unit_literal_names(self, expression) -> frozenset[str]:
        """Names in ``expression`` this evaluation reads as units rather than values.

        The printer needs this to set a unit upright. It cannot decide on the alias
        table alone: `m := 500*kg` makes `m` a mass, and the same precedence that
        governs the arithmetic has to govern the typesetting, or the page relabels the
        reader's own quantity.

        That precedence already lives in `unit_literal_overrides`, which yields to a
        stored value before ever consulting the alias table, so this is a rename rather
        than a second rule - one place decides what a name means. Two earlier drafts
        re-checked `self.values` and filtered explicit overrides here; both survived
        mutation, because the first is redundant and the second has no caller. Taking
        an `overrides` argument this cannot honour would be worse than not taking one:
        the filter would be dead until the day it silently was not.
        """
        return frozenset(self.unit_literal_overrides(expression))

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
        # A unit written in the function - `V(x) = 30*kN - q*x`, a breakpoint `x <= 1*m` -
        # is resolved as a unit, as every other evaluation resolves it. Looking every name
        # up among the sheet's values raised a KeyError on `kN`, and the figure was lost.
        fixed_overrides = self.unit_literal_overrides(expression, overrides)
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
                unit = (
                    normalise(f" {right.units:~P}") if not right.dimensionless else ""
                )
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
        # The rule `evaluate_symbolic` and `evaluate_matrix` both already keep, in the one
        # path that had not been given it: an undefined unit alias is the unit, not a name
        # the sheet forgot to define. `evaluate_matrix` puts it as "without this a column
        # of forces reports itself as partially evaluated, because `kN` looks like a name
        # nobody defined" - and a scalar left partially evaluated did worse than report
        # itself, because this path raises. `piecewise(q1, x < a, 5*kN/m)` asked the
        # engineer to define the kilonewton the moment the variable was left free, while
        # the same branch at a point, and its extrema, already answered.
        #
        # Resolved, not substituted: a unit stays a unit under the working, for the reason
        # recorded there - nobody writes `kN = 1 kN`. So it only leaves `unresolved`.
        resolved_units = self.unit_literal_overrides(expr, overrides)
        names = sorted(symbol.name for symbol in expr.free_symbols)
        substitutions = {
            name: overrides[name] if name in overrides else self.values[name]
            for name in names
            if name in overrides or name in self.values
        }
        unresolved = tuple(
            name
            for name in names
            if name not in substitutions and name not in resolved_units
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
        symbol = next(
            (item for item in expr.free_symbols if item.name == variable),
            sp.Symbol(variable, real=True),
        )
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

    def _resolve_symbolic_names(self, expr: sp.Expr) -> sp.Expr:
        """Replace free symbols that the symbolic namespace defines.

        A definition captures its free symbols, so `v(x) = integrate(...) + C1` keeps
        `C1` even after the boundary conditions determine it. Without this, an elastic
        curve could be derived symbolically and never reach a number.

        The loop stops when a pass changes nothing rather than after a fixed count. A
        self-referential definition - `a = b` then `b = a`, where the second captures the
        symbol `b` - substitutes to itself and falls through to the ordinary
        missing-value message, which is the right thing to say about it.
        """
        namespace = getattr(self, "symbolic_namespace", None)
        if not namespace:
            return expr
        while True:
            kept = getattr(self, "kept_names", None) or frozenset()
            replacements = {
                symbol: namespace[symbol.name]
                for symbol in expr.free_symbols
                if symbol.name in namespace and symbol.name not in kept
            }
            if not replacements:
                return expr
            substituted = sp.sympify(expr).subs(replacements)
            if substituted == expr:
                return expr
            expr = substituted

    def evaluate_symbolic(
        self,
        expression: sp.Expr,
        overrides: dict[str, Any] | None = None,
    ):
        expr = sp.sympify(expression)
        overrides = overrides or {}
        expr = self._resolve_symbolic_names(expr)
        # A unit is an ordinary free symbol in the symbolic layer, so `M = 5*kN` leaves
        # `kN` behind and asking for its number used to fail with "define kN := <value>",
        # which is advice nobody should follow. The numeric layer has always read an
        # undefined unit alias as the unit on the `:=` path - `L := 6*m` is metres - so
        # this is not a new rule, it is the same rule reaching the other path.
        resolved_units = self.unit_literal_overrides(expr, overrides)
        names = sorted(symbol.name for symbol in expr.free_symbols)
        missing = [
            name
            for name in names
            if name not in resolved_units and name not in self.values
        ]
        if missing:
            hint = diagnostic_hint("unresolved_numeric_symbols", names=tuple(missing))
            raise EngEvaluationError(
                "numeric evaluation requires values for: "
                + ", ".join(missing)
                + f". {hint}"
            )

        # A unit resolves for the arithmetic but never joins the substitution stage.
        # Nobody writes "kN = 1 kN" under their working: a unit stays a unit there, and
        # the printer renders any symbol it finds no substitution for as itself.
        substitutions = {
            name: overrides[name] if name in overrides else self.values[name]
            for name in names
            if name in overrides or name in self.values
        }
        try:
            substitutions.update(
                self._mode_substitutions(expr, {**resolved_units, **substitutions})
            )
            value = self._evaluate_sympy(expr, {**resolved_units, **substitutions})
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

    def evaluate_matrix(
        self,
        matrix,
        overrides: dict[str, Any] | None = None,
        target_unit=None,
        *,
        allowed_unresolved: set[str] | None = None,
    ):
        if not isinstance(matrix, sp.MatrixBase):
            raise EngEvaluationError("matrix numeric evaluation requires a symbolic matrix")

        overrides = dict(overrides or {})
        names = sorted({
            symbol.name
            for entry in matrix
            for symbol in sp.sympify(entry).free_symbols
        })

        # Same rule as the scalar path: a unit literal resolves for the arithmetic and
        # stays out of the substitution stage. Without this a column of forces reports
        # itself as partially evaluated, because `kN` looks like a name nobody defined.
        resolved_units = dict(overrides)
        for entry in matrix:
            resolved_units = self.unit_literal_overrides(entry, resolved_units)
        for name in overrides:
            resolved_units.pop(name, None)

        substitutions = {
            name: overrides[name] if name in overrides else self.values[name]
            for name in names
            if name in overrides or name in self.values
        }
        unresolved = tuple(
            name
            for name in names
            if name not in substitutions and name not in resolved_units
        )

        if allowed_unresolved is not None:
            unexpected = tuple(
                name for name in unresolved if name not in allowed_unresolved
            )
            if unexpected:
                hint = diagnostic_hint("unresolved_numeric_symbols", names=unexpected)
                raise EngEvaluationError(
                    "numeric evaluation requires values for: "
                    + ", ".join(unexpected)
                    + f". {hint}"
                )

        if unresolved:
            if target_unit is not None:
                raise EngEvaluationError(
                    "target-unit conversion requires a fully numeric result: "
                    + ", ".join(unresolved)
                )
            return substitutions, unresolved, None

        entries = []
        adaptable_zeros: set[tuple[int, int]] = set()
        for row in range(matrix.rows):
            for col in range(matrix.cols):
                expression = sp.sympify(matrix[row, col])
                if expression.is_zero is True:
                    adaptable_zeros.add((row, col))
                try:
                    value = self._evaluate_sympy(
                        expression, {**resolved_units, **substitutions}
                    )
                    quantity = self._as_quantity(value)
                except DimensionalityError as exc:
                    raise EngEvaluationError(
                        "matrix numeric evaluation has incompatible units at "
                        f"[{row + 1},{col + 1}]"
                    ) from exc
                except EngEvaluationError as exc:
                    if "incompatible" in str(exc).lower() and "unit" in str(exc).lower():
                        raise EngEvaluationError(
                            "matrix numeric evaluation has incompatible units at "
                            f"[{row + 1},{col + 1}]"
                        ) from exc
                    raise EngEvaluationError(
                        f"matrix numeric evaluation failed at [{row + 1},{col + 1}]: {exc}"
                    ) from exc
                except PintError as exc:
                    raise EngEvaluationError(
                        f"matrix numeric unit evaluation failed at [{row + 1},{col + 1}]: {exc}"
                    ) from exc
                except Exception as exc:
                    raise EngEvaluationError(
                        f"matrix numeric evaluation failed at [{row + 1},{col + 1}]: {exc}"
                    ) from exc
                entries.append(quantity)

        quantity_matrix = QuantityMatrix(
            rows=matrix.rows,
            cols=matrix.cols,
            entries=tuple(entries),
            adaptable_zeros=frozenset(adaptable_zeros),
        )
        substitutions.update(
            self._mode_substitutions(matrix, {**resolved_units, **substitutions})
        )

        if target_unit is not None:
            converted = []
            for row in range(matrix.rows):
                for col in range(matrix.cols):
                    quantity = quantity_matrix.entry(row, col)
                    coordinate = (row, col)
                    if (
                        coordinate in quantity_matrix.adaptable_zeros
                        and quantity.dimensionless
                        and self._is_exact_zero_quantity(quantity)
                    ):
                        converted.append(self.ureg.Quantity(0, target_unit))
                        continue
                    try:
                        converted.append(quantity.to(target_unit))
                    except DimensionalityError as exc:
                        raise EngEvaluationError(
                            "target unit is incompatible with matrix entry at "
                            f"[{row + 1},{col + 1}]"
                        ) from exc
            quantity_matrix = QuantityMatrix(
                rows=matrix.rows,
                cols=matrix.cols,
                entries=tuple(converted),
                adaptable_zeros=quantity_matrix.adaptable_zeros,
            )

        return substitutions, (), quantity_matrix

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

    def extremum(self, name: str, values):
        """`min` or `max` of values of one kind, compared in one unit.

        The first value written wins a tie, so the page shows the limit it would read
        first. Its message names the function the engineer typed; it used to say
        "numeric Min/Max", which is nothing anybody wrote.
        """
        try:
            quantities = self._normalize_quantity_group(values, name)
        except EngEvaluationError as exc:
            raise EngEvaluationError(
                f"{name} compares values of one kind; its arguments have incompatible units"
            ) from exc
        selector = min if name == "min" else max
        return selector(quantities, key=lambda quantity: quantity.magnitude)

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

        symbol = next(
            (item for item in expression.free_symbols if item.name == variable),
            sp.Symbol(variable, real=True),
        )
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

        self._give_a_lone_zero_the_branches_unit(
            expression,
            branches,
            variable,
            overrides,
        )

        return PiecewisePartialEvaluation(
            interval_variable=variable,
            branches=tuple(PiecewisePartialBranch(**branch) for branch in branches),
        )

    def _give_a_lone_zero_the_branches_unit(
        self,
        expression,
        branches: list[dict[str, Any]],
        variable: str,
        overrides: dict[str, Any],
    ) -> None:
        """A zero whose neighbours all hold the interval variable has no group to join.

        The group above is what turns a bare `Integer(0)` into `0.00 kN/m`, and it only
        contains branches that resolved to a quantity. When the neighbouring branches are
        formulas in the interval variable - which is how every real beam is written -
        none of them resolves, and the zero is left alone with nothing to take a unit
        from: the engineer's own `M_P(x)` answered a moment as a bare `0.00`.

        `_infer_piecewise_zero_unit` already answers this question, and is what makes the
        same piecewise asked at a point answer `0.00 kgf·cm`. It could not be reached here
        because a branch holding `x` does not evaluate while `x` is free. It does once `x`
        is given one unit of its own dimension, and the breakpoints say what that
        dimension is: `x <= L/2` with `L` in centimetres makes `P*x/2` a `kgf·cm`.

        Only when the group settled on no unit at all, and the empty `zero_indices` is
        the whole of that test - no second guard is needed, and one written here was
        removed as unreachable. A zero beside a branch that resolved dimensionally has
        already been given that branch's unit by the group above, so it is not
        dimensionless any more; and a branch that did not resolve holds a symbolic
        expression rather than a quantity, so it can never be mistaken for one.
        """
        zero_indices = [
            index
            for index, branch in enumerate(branches)
            if hasattr(branch["value"], "magnitude")
            and branch["value"].dimensionless
            and self._is_exact_zero_quantity(branch["value"])
        ]
        if not zero_indices:
            return

        variable_unit = next(
            (
                branch["breakpoint"].units
                for branch in branches
                if hasattr(branch["breakpoint"], "units")
            ),
            self.ureg.dimensionless,
        )
        try:
            substitutions, _unresolved = self.partial_substitutions(
                expression,
                allowed_unresolved={variable},
                overrides=overrides,
            )
            unit = self._infer_piecewise_zero_unit(
                expression,
                {**substitutions, variable: self.ureg.Quantity(1, variable_unit)},
            )
        except EngEvaluationError:
            # This row already evaluated; a question asked here must not be able to stop
            # it from being drawn. Left as found, which is what it read before.
            return

        # Intent rather than behaviour: with nothing to infer, writing a dimensionless
        # zero over a branch that already holds one changes nothing, and mutation
        # confirmed it by surviving. Kept so the rule reads as it is meant - a unit is
        # taken where there is one to take, and invented nowhere.
        if unit is None:
            return
        for index in zero_indices:
            branches[index]["value"] = self.ureg.Quantity(0, unit)

    def piecewise_branch_values(self, expression, overrides: dict[str, Any] | None = None):
        """Every branch of a piecewise evaluated at a point, in the unit they share.

        `build_partial_piecewise_evaluation` hands the renderer these values on the path
        that leaves the variable free. A piecewise evaluated at a point had nothing to
        hand it, so its substitution row printed a bare `0` for the very branch the answer
        two lines below writes as `0.00 kN/m`.

        A zero branch's unit is not on the branch: `0*kN/m` folds to `Integer(0)` on the
        way into the symbolic layer, and what gives it one is the group - the same
        `_normalize_quantity_group` call, under the same name, that the partial path uses.

        `None` when there is nothing to say: not a piecewise, or a branch this evaluation
        never needed and cannot resolve on its own. The renderer then leaves the row as it
        found it, so a sheet that reads today cannot stop reading because of this.
        """
        expression = sp.sympify(expression)
        if not isinstance(expression, sp.Piecewise):
            return None

        overrides = dict(overrides or {})
        values = []
        for branch_expression, _condition in expression.args:
            try:
                _, value = self.evaluate_symbolic(
                    sp.sympify(branch_expression),
                    overrides=overrides,
                )
            except EngEvaluationError:
                return None
            values.append(value)

        if not values:
            return None
        try:
            return self._normalize_quantity_group(values, "piecewise branches")
        except EngEvaluationError:
            return None

    def extremum_values(self, expression, overrides: dict[str, Any] | None = None):
        """Each argument of a `min` or `max` evaluated, in the unit they are compared in.

        The row a reviewer checks against the code: `min(2.00 m, 2.22 m, 3.00 m)` says
        which limit governs, where the substitution row only says what each one is made
        of. `None` when there is nothing to say - not a `min` or `max`, or an argument that
        cannot be resolved on its own - and the renderer then leaves the working as it was.
        """
        expression = sp.sympify(expression)
        if not isinstance(expression, (sp.Min, sp.Max)):
            return None
        values = []
        for argument in expression.args:
            try:
                _, value = self.evaluate_symbolic(argument, overrides=dict(overrides or {}))
            except EngEvaluationError:
                return None
            values.append(value)
        try:
            return self._normalize_quantity_group(values, "min/max")
        except EngEvaluationError:
            return None

    def interpolation_segment(self, point, points, values):
        """The point of an `interp` and the two table rows around it, `(x, x1, x2, y1, y2)`.

        The point is read in the unit of the table's points, and the values in the unit
        of its first value, so a point in millimetres finds its place in a table written
        in metres - and the segment is worked out in metres, the way the table reads. Refused outside
        the table: a code's table is not a law to extend, and extrapolating in silence is
        how a sheet ends up with a coefficient nobody tabulated. At a point of the table
        the segment starts there, so the tabulated value comes back exactly.
        """
        try:
            *xs, x = self._normalize_quantity_group([*points, point], "interp")
        except EngEvaluationError as exc:
            raise EngEvaluationError(
                "interp reads its point against the table in one kind of unit"
            ) from exc
        try:
            ys = list(self._normalize_quantity_group(values, "interp"))
        except EngEvaluationError as exc:
            raise EngEvaluationError(
                "interp needs the values of its table in one kind of unit"
            ) from exc
        at = [float(self._as_quantity(value).magnitude) for value in xs]
        if any(after <= before for before, after in zip(at, at[1:])):
            raise EngEvaluationError("interp needs its points in increasing order")
        here = float(self._as_quantity(x).magnitude)
        if not at[0] <= here <= at[-1]:
            raise EngEvaluationError(
                f"interp does not extrapolate: {_value_text(x)} lies outside its table, "
                f"{_value_text(xs[0])} to {_value_text(xs[-1])}"
            )
        index = min(max(i for i, value in enumerate(at) if value <= here), len(at) - 2)
        return x, xs[index], xs[index + 1], ys[index], ys[index + 1]

    def interpolation_values(self, expression, overrides: dict[str, Any] | None = None):
        """The segment an `interp` read, for the row that shows it worked out.

        `None` when there is nothing to say - not an `interp`, or a part of it that
        cannot be resolved on its own - and the renderer leaves the working as it was.
        """
        expression = sp.sympify(expression)
        if not isinstance(expression, Interpolation):
            return None
        point, points, values = expression.args

        def read(item):
            return self.evaluate_symbolic(item, overrides=dict(overrides or {}))[1]

        try:
            return self.interpolation_segment(
                read(point), [read(item) for item in points], [read(item) for item in values]
            )
        except EngEvaluationError:
            return None

    def _evaluate_sympy(self, expr, substitutions: dict[str, Any]):
        if isinstance(expr, sp.Symbol):
            return substitutions[expr.name]

        if expr == sp.pi:
            return math.pi

        if isinstance(expr, Interpolation):
            point, points, values = expr.args
            x, x1, x2, y1, y2 = self.interpolation_segment(
                self._as_quantity(self._evaluate_sympy(point, substitutions)),
                [self._as_quantity(self._evaluate_sympy(item, substitutions)) for item in points],
                [self._as_quantity(self._evaluate_sympy(item, substitutions)) for item in values],
            )
            return y1 + (y2 - y1) * ((x - x1) / (x2 - x1))

        if isinstance(expr, (ModeEigenvalue, ModeShapeEntry)):
            # Before the closed-number branch below, which a mode of a matrix of plain
            # numbers would otherwise reach and hand to `sp.N`, which cannot evaluate it.
            return self._evaluate_mode(expr, substitutions)

        if expr.is_Number:
            if expr.is_real is not True or expr.is_finite is not True:
                raise EngEvaluationError(
                    "symbolic numeric value must be real and finite"
                )
            if expr.is_Integer:
                return int(expr)
            if expr.is_Rational:
                return int(expr.p) / int(expr.q)
            return float(expr)

        if (
            not expr.free_symbols
            and expr.is_number is True
            and expr.func not in {sp.asin, sp.acos, sp.atan}
        ):
            evaluated = sp.N(expr, 50)
            if evaluated.is_real is not True or evaluated.is_finite is not True:
                raise EngEvaluationError(
                    "symbolic numeric value must be real and finite"
                )
            try:
                return float(evaluated)
            except (TypeError, ValueError, OverflowError) as exc:
                raise EngEvaluationError(
                    f"unsupported closed symbolic numeric value '{sp.sstr(expr)}'"
                ) from exc

        if expr.func == sp.Piecewise:
            return self._evaluate_piecewise(expr, substitutions)

        if expr.func in {
            sp.StrictLessThan,
            sp.LessThan,
            sp.StrictGreaterThan,
            sp.GreaterThan,
        }:
            return self._evaluate_relation(expr, substitutions)

        # `isinstance`, not `expr.func in {...}`: `min` and `max` are subclasses that keep
        # their arguments in the order written, and a set of the two bases missed them.
        if isinstance(expr, (sp.Min, sp.Max)):
            return self.extremum(
                "min" if isinstance(expr, sp.Min) else "max",
                [self._evaluate_sympy(arg, substitutions) for arg in expr.args],
            )

        if expr.is_Add:
            # A term that is a unit on its own - `1*kN` folds to `kN` - is one of it. Pint
            # multiplies a unit by a quantity and refuses to add one to it, so
            # `1*kN + 4*kN*x/m` failed in `numeric`, `table` and `plot` whenever the unit
            # came first, with Pint's own words.
            values = [
                self._as_quantity(value)
                if hasattr(value, "dimensionality") and not hasattr(value, "magnitude")
                else value
                for value in (self._evaluate_sympy(arg, substitutions) for arg in expr.args)
            ]
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
            return _real_power(base, exponent)

        if isinstance(expr, sp.Sum):
            # The symbolic layer keeps the sigma, which is what the memoria shows, and
            # this turns it into a value - the same division of labour as every other
            # operation in the language. No second `summation()` name is introduced.
            if len(expr.limits) != 1:
                raise EngEvaluationError(
                    "numeric evaluation supports one summation index at a time"
                )
            index, lower, upper = expr.limits[0]
            bounds = []
            for bound in (lower, upper):
                value = self._evaluate_sympy(bound, substitutions)
                if hasattr(value, "dimensionality") and not value.dimensionless:
                    raise EngEvaluationError(
                        "summation bounds must be dimensionless"
                    )
                bounds.append(int(getattr(value, "magnitude", value)))
            start, stop = bounds
            if stop < start:
                # SymPy's convention for reversed bounds, and the dimensionless path
                # below goes through SymPy directly: sum(i, i, 3, 1) is -2 there, so it
                # must be -2 here too. Two paths disagreeing about the same construct
                # would be a defect, and the units are the only thing that decides which
                # path a summation takes.
                reversed_sum = self._evaluate_sympy(
                    sp.Sum(expr.function, (index, stop + 1, start - 1)), substitutions
                )
                return -reversed_sum
            # A mistyped limit should not lock up a notebook while it adds ten million
            # terms; saying no is better than not responding.
            _SUMMATION_TERM_LIMIT = 100_000
            if stop - start + 1 > _SUMMATION_TERM_LIMIT:
                raise EngEvaluationError(
                    f"summation would evaluate {stop - start + 1} terms, above the "
                    f"limit of {_SUMMATION_TERM_LIMIT}; check the bounds"
                )
            total = None
            for step in range(start, stop + 1):
                term = self._evaluate_sympy(
                    expr.function.subs(index, sp.Integer(step)), substitutions
                )
                total = term if total is None else total + term
            return total

        if expr.func == sp.SingularityFunction and len(expr.args) == 3:
            # Macaulay bracket. Zero before the offset, the shifted power from there on.
            # Pint carries the units through the subtraction, so a bracket whose offset
            # is not a length compatible with the variable raises there rather than
            # silently producing a number.
            shifted = self._evaluate_sympy(expr.args[0], substitutions) - self._evaluate_sympy(
                expr.args[1], substitutions
            )
            order = int(expr.args[2])
            powered = shifted**order
            magnitude = getattr(shifted, "magnitude", shifted)
            # At the offset itself this reproduces SymPy exactly: 0**0 is 1, so the
            # zero-order bracket is closed on the left, and every higher order is zero.
            return powered if float(magnitude) >= 0 else powered * 0

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

    def _mode_substitutions(self, expr, substitutions: dict[str, Any]) -> dict[str, Any]:
        """Each mode the expression takes, by `mode_key`, as the quantity it evaluates to."""
        return {
            mode_key(atom): self._as_quantity(self._evaluate_mode(atom, substitutions))
            for atom in mode_atoms(expr)
        }

    def _evaluate_mode(self, expr, substitutions: dict[str, Any]):
        """`lam[i]` or a row of `phi[i]`, from the numbers of the matrix it was taken from."""
        matrix = expr.args[-1]
        quantity_matrix = QuantityMatrix(
            rows=matrix.rows,
            cols=matrix.cols,
            entries=tuple(
                self._as_quantity(self._evaluate_sympy(entry, substitutions))
                for entry in matrix
            ),
        )
        operation = "eigenvals" if isinstance(expr, ModeEigenvalue) else "eigenvects"
        modes, scale = modes_of(quantity_matrix, operation=operation)
        values, vectors = numbered(modes)
        if isinstance(expr, ModeEigenvalue):
            value = values[int(expr.args[0]) - 1]
            return self.ureg.Quantity(value, scale) if scale is not None else value
        mode, row = int(expr.args[0]), int(expr.args[1])
        return vectors[mode - 1][row - 1]

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
        if not isinstance(node.func, ast.Name) or node.keywords:
            raise EngEvaluationError("unsupported numeric function")
        name = node.func.id
        if name == "interp":
            raise EngEvaluationError(
                "interp reads a table, which := cannot hold; define it with = and ask "
                "numeric(...) for its value"
            )
        if name in {"min", "max"}:
            # `s_max := min(3*h, 450*mm)`: a limit is set as often as it is derived.
            if len(node.args) < 2:
                raise EngEvaluationError(
                    f"{name} expects at least 2 arguments: the values to compare"
                )
            return self.context.extremum(name, [self.visit(arg) for arg in node.args])
        if len(node.args) != 1:
            raise EngEvaluationError("unsupported numeric function")
        value = self.visit(node.args[0])
        if name == "abs":
            return abs(value)
        if name in {"sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "exp", "log"}:
            return self.context.evaluate_scalar_function(name, value)
        # Named: the message used to be the same for every function, and the engineer
        # could not tell which one it meant.
        raise EngEvaluationError(f"unsupported numeric function '{name}'")

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
                return _real_power(left, right)
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
                # `1/s` is how the page itself writes the inverse second. A number over a
                # unit is a quantity to Pint, and a quantity is rightly refused as a
                # target, so the `1` is read as what it means here: the reciprocal. Only
                # the `1` - `2/s` is still no unit, and reading it as `1/s` would drop
                # the 2 without a word. The number test comes first because Pint holds
                # that the radian equals 1, and `rad/s` must not lose its radian.
                if isinstance(left, numbers.Number) and left == 1:
                    return right**-1
                return left / right
            if isinstance(node.op, ast.Pow):
                if not isinstance(right, numbers.Number):
                    raise EngEvaluationError("target unit exponent must be numeric")
                return left ** right
        except PintError as exc:
            raise EngEvaluationError(f"target unit evaluation failed: {exc}") from exc
        raise EngEvaluationError("target units support only *, /, and powers")
