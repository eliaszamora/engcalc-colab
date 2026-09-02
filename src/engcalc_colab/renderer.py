from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from html import escape

import sympy as sp
from sympy.printing.latex import LatexPrinter

from pint.errors import DimensionalityError

from .matrix_numeric import QuantityMatrix
from .models import (
    CharacteristicInterval,
    CharacteristicPoint,
    EigenvalueSet,
    EigenvectorSet,
    EvaluationResult,
    ExtremaResult,
    IntersectionsResult,
    MatrixShape,
    NumericAssignmentResult,
    NumericEvaluationResult,
    NumericMatrixEvaluationResult,
    PartialMatrixNumericEvaluationResult,
    PartialNumericEvaluationResult,
    RootsResult,
    SystemSolveResult,
    TableResult,
)

CalculationResult = (
    EvaluationResult
    | NumericAssignmentResult
    | NumericEvaluationResult
    | NumericMatrixEvaluationResult
    | PartialNumericEvaluationResult
    | PartialMatrixNumericEvaluationResult
)


@dataclass(frozen=True)
class RenderSettings:
    """Global numerical presentation settings for EngCalc output."""

    precision: int = 2
    zero_tolerance: float = 1e-10

    def __post_init__(self) -> None:
        if isinstance(self.precision, bool) or not isinstance(self.precision, int):
            raise ValueError("precision must be an integer from 0 to 10")
        if not 0 <= self.precision <= 10:
            raise ValueError("precision must be an integer from 0 to 10")
        if self.zero_tolerance < 0:
            raise ValueError("zero_tolerance must be non-negative")


_DEFAULT_RENDER_SETTINGS = RenderSettings()


class _EngineeringLatexPrinter(LatexPrinter):
    def _print_Mul(self, expr):
        if not expr.is_commutative:
            return super()._print_Mul(expr)

        if expr.could_extract_minus_sign():
            expr = -expr
            prefix = "- "
        else:
            prefix = ""

        numer, denom = sp.fraction(expr, exact=True)
        snumer = self._print_engineering_product(numer)
        if denom is sp.S.One:
            return prefix + snumer

        sdenom = self._print_engineering_product(denom)
        return rf"{prefix}\frac{{{snumer}}}{{{sdenom}}}"

    def _print_engineering_product(self, expr):
        if not expr.is_Mul:
            return self._print(expr)

        args = sorted(expr.args, key=_engineering_factor_key)
        separator = self._settings["mul_symbol_latex"]
        rendered: list[str] = []

        for index, term in enumerate(args):
            term_latex = self._print(term)
            if self._needs_mul_brackets(term, first=(index == 0), last=(index == len(args) - 1)):
                term_latex = rf"\left({term_latex}\right)"
            rendered.append(term_latex)

        return separator.join(rendered)


class _NumericSubstitutionLatexPrinter(_EngineeringLatexPrinter):
    def __init__(self, substitutions: dict[str, object], settings: RenderSettings):
        super().__init__()
        self.substitutions = substitutions
        self.render_settings = settings

    def _print_Symbol(self, expr):
        quantity = self.substitutions.get(expr.name)
        if quantity is None:
            return super()._print_Symbol(expr)
        return rf"\left({_quantity_latex(quantity, settings=self.render_settings)}\right)"


def _engineering_factor_key(term):
    if term.is_Number:
        return (0, sp.default_sort_key(term))

    base = term.base if term.is_Pow else term
    if isinstance(base, sp.Symbol):
        first_alpha = next((char for char in base.name if char.isalpha()), "")
        if first_alpha.islower():
            group = 1
        elif first_alpha.isupper():
            group = 2
        else:
            group = 3
        return (group, sp.default_sort_key(term))

    return (3, sp.default_sort_key(term))


def _latex(expr) -> str:
    return _EngineeringLatexPrinter().doprint(expr)


def _substitution_latex(expr, substitutions: dict[str, object], settings: RenderSettings = _DEFAULT_RENDER_SETTINGS) -> str:
    return _NumericSubstitutionLatexPrinter(substitutions, settings).doprint(expr)


# Ordered families of units an engineer actually writes for each dimension. Keyed by
# Pint's dimensionality, which reduces to base dimensions: a table keyed on "[force]"
# silently matches nothing.
_UNIT_FAMILIES: dict[str, tuple[str, ...]] = {
    "[length]": ("mm", "m"),
    "[mass] * [length] / [time] ** 2": ("N", "kN", "MN"),
    "[mass] * [length] ** 2 / [time] ** 2": ("kN * m",),
    "[mass] / [length] / [time] ** 2": ("MPa", "GPa"),
    "[mass] / [time] ** 2": ("kN / m",),
    "[length] ** 2": ("cm ** 2", "m ** 2"),
    "[length] ** 4": ("cm ** 4",),
}


def _significant_figures(magnitude, precision: int) -> int:
    """Digits that survive a fixed-decimal render and still carry information."""
    rendered = f"{abs(float(magnitude)):.{precision}f}".replace(".", "")
    return len(rendered.strip("0"))


def _unit_family(quantity) -> tuple[str, ...]:
    try:
        return _UNIT_FAMILIES.get(str(quantity.dimensionality), ())
    except Exception:
        return ()


def _unit_terms(quantity) -> int:
    """How many unit symbols the reader has to hold at once.

    ``m`` and ``tonf`` are one, ``tonf/m`` and ``kN*m`` are two, and the deflection's
    ``kN/(GPa*m)`` is three. The count is what separates a unit the engineer's own
    inputs produced from one only the algebra invented.
    """
    try:
        return len(quantity.units._units)
    except Exception:
        return 1


def _unit_is_the_engineers(quantity) -> bool:
    """True when the unit came from the engineer's own inputs rather than the algebra.

    A family member is *not* the engineer's in this sense: metres are the family's
    own unit, so a value in metres is subject to the family's choice. A unit outside
    the family that is no more complex than the family's canonical member came from
    what was typed - ``tonf``, ``kN/mm`` - and is kept.
    """
    family = _unit_family(quantity)
    if not family:
        return True
    own = str(quantity.units)
    for name in family:
        try:
            if str(quantity.to(name).units) == own:
                return False
        except DimensionalityError:
            continue
    canonical = min(
        (_unit_terms(quantity.to(name)) for name in family),
        default=_unit_terms(quantity),
    )
    return _unit_terms(quantity) <= canonical


def _is_genuine_zero(quantity, settings: RenderSettings) -> bool:
    """Decided in the stored unit, always, and never after a conversion.

    ``zero_tolerance`` is compared against a magnitude, so it means something
    different in every unit: 1e-7 kN/mm is below a 1e-6 tolerance and 1e-4 kN/m,
    the same value, is above it. Rescaling for display must not be able to turn an
    approved zero into a number.
    """
    try:
        return abs(float(quantity.magnitude)) < settings.zero_tolerance
    except (TypeError, ValueError):
        return False


def _band_distance(magnitude):
    """How far a magnitude sits from the readable band [1, 1000). Design 4.5.

    Significant figures cannot make this choice. `0.02 m` and `20.00 mm` retain one
    figure each, so the comparison ties and the value stays in metres at a display
    resolution of 25% - EP-1. Measured over the cases that reach this function, the
    band rule is right 10 times out of 10 where counting figures is right 8.
    """
    magnitude = abs(float(magnitude))
    if magnitude == 0.0:
        return (2, 0.0)
    if 1.0 <= magnitude < 1000.0:
        return (0, 0.0)
    if magnitude < 1.0:
        return (1, abs(math.log10(magnitude)))
    return (1, math.log10(magnitude / 1000.0))


def _best_in_family(quantity, family, settings: RenderSettings, *, start=None):
    candidates = [] if start is None else [start]
    for name in family:
        try:
            candidates.append(quantity.to(name))
        except DimensionalityError:
            continue
    if not candidates:
        return quantity

    figures = [
        _significant_figures(candidate.magnitude, settings.precision)
        for candidate in candidates
    ]
    if max(figures) <= 0:
        # Below the family floor nothing gains a figure, so moving the value only
        # obscures it: 1e-6 m reads as 1.00e-6 m, not as 1.00e-3 mm. Scientific
        # notation happens where the engineer left the value. Design 4.6.
        return quantity
    # ``min`` is stable and ``start`` - the unit the value already carries - is first,
    # so a band tie keeps it. Every present family steps by 1000 or more, which makes a
    # tie impossible, so this is currently inert: verified by mutation, removing ``start``
    # changes no test. It is kept as the correct behaviour for any future family whose
    # members sit closer together, and documented as inert rather than credited with
    # results the band rule produces on its own.
    return min(candidates, key=lambda candidate: _band_distance(candidate.magnitude))


def _display_quantity(quantity, settings: RenderSettings, *, declared: bool):
    """Choose the unit the reader sees.

    Three cases, and the middle one is why significant figures alone are not
    enough. The P-3 deflection carries ``kN/(GPa*m)`` and renders ``5625.00``,
    which retains *more* figures than ``5.63 mm`` — so a rule that only maximised
    figures would keep the compound and leave P-3 unfixed.

    - the unit is a **family member**: choose within the family by significant
      figures, ties keeping what the value already carries, so a 5 m span stays in
      metres and an admissible deflection of ``L/300`` moves to millimetres;
    - the unit is **not** a family member but is no more complex than one: it came
      from the engineer's own inputs, as ``tonf`` does, and is kept;
    - the unit is a compound the algebra invented: replaced, whatever it shows.

    A declared unit is kept in every case, unless rendering it would leave no
    significant figure at all.
    """
    try:
        magnitude = float(quantity.magnitude)
    except (TypeError, ValueError):
        return quantity
    if abs(magnitude) < settings.zero_tolerance:
        return quantity

    family = _unit_family(quantity)
    if not family:
        return quantity

    own_figures = _significant_figures(magnitude, settings.precision)
    if declared and own_figures > 0:
        return quantity

    if _unit_is_the_engineers(quantity):
        # ``tonf``, ``kN/mm``: kept unless it says nothing at all.
        return quantity if own_figures > 0 else _best_in_family(quantity, family, settings)

    own_is_family_member = any(
        str(quantity.to(name).units) == str(quantity.units) for name in family
    )
    start = quantity if own_is_family_member and own_figures > 0 else None
    return _best_in_family(quantity, family, settings, start=start)


def _scientific_latex(magnitude: float, precision: int) -> str:
    exponent = int(math.floor(math.log10(abs(magnitude))))
    mantissa = magnitude / (10.0**exponent)
    return rf"{mantissa:.{precision}f} \cdot 10^{{{exponent}}}"


def _magnitude_text(magnitude, settings: RenderSettings) -> str:
    """Format one magnitude, falling back to scientific notation below the floor.

    Only values above ``zero_tolerance`` are owed a readable form; below it a value
    is a genuine zero by an existing approved contract and still renders as zero.
    """
    magnitude = float(magnitude)
    if magnitude == 0.0 or abs(magnitude) < settings.zero_tolerance:
        return f"{0.0:.{settings.precision}f}"
    if _significant_figures(magnitude, settings.precision) == 0:
        return _scientific_latex(magnitude, settings.precision)
    return f"{magnitude:.{settings.precision}f}"


def _quantity_latex(
    quantity,
    precision: int | None = None,
    *,
    settings: RenderSettings | None = None,
    declared: bool = True,
) -> str:
    active_settings = settings or _DEFAULT_RENDER_SETTINGS
    if precision is not None:
        active_settings = replace(active_settings, precision=precision)

    quantity = _display_quantity(quantity, active_settings, declared=declared)
    magnitude_latex = _magnitude_text(quantity.magnitude, active_settings)

    unit_name = str(quantity.units)
    if getattr(quantity, "dimensionless", False) and unit_name == "dimensionless":
        return magnitude_latex

    unit_latex = format(quantity.units, "~L")
    return rf"{magnitude_latex}\,{unit_latex}"


def _magnitude_latex(quantity, settings: RenderSettings) -> str:
    """Format a cell whose unit was already chosen for the whole aggregate.

    Deliberately does not rescale. A matrix prints one unit outside its brackets
    and a table prints one unit in its header, so a per-cell choice here would
    leave the cells reading against a unit that is not theirs.
    """
    return _magnitude_text(quantity.magnitude, settings)


def _matrix_from_cells_latex(rows: list[list[str]]) -> str:
    body = r"\\".join(" & ".join(row) for row in rows)
    return rf"\left[\begin{{matrix}}{body}\end{{matrix}}\right]"


def _matrix_latex(matrix) -> str:
    return _latex(sp.ImmutableMatrix(matrix))


def _matrix_substitution_latex(
    matrix,
    substitutions: dict[str, object],
    settings: RenderSettings,
) -> str:
    return _NumericSubstitutionLatexPrinter(substitutions, settings).doprint(
        sp.ImmutableMatrix(matrix)
    )


def _quantity_matrix_common_unit(quantity_matrix: QuantityMatrix):
    """Return one display unit when every physical cell is mutually convertible.

    Exact dimensionless zero cells are neutral, which preserves Task 5 adaptable-zero
    semantics. A nonzero dimensionless value mixed with physical entries makes the
    matrix heterogeneous for display.
    """
    physical = [
        quantity
        for quantity in quantity_matrix
        if not getattr(quantity, "dimensionless", False)
    ]
    if not physical:
        return None, True

    common_unit = physical[0].units
    for quantity in physical[1:]:
        try:
            quantity.to(common_unit)
        except DimensionalityError:
            return None, False

    for quantity in quantity_matrix:
        if getattr(quantity, "dimensionless", False):
            if abs(float(quantity.magnitude)) >= 1e-15:
                return None, False
    return common_unit, True


def _quantity_matrix_latex(
    quantity_matrix: QuantityMatrix,
    settings: RenderSettings = _DEFAULT_RENDER_SETTINGS,
) -> str:
    common_unit, homogeneous = _quantity_matrix_common_unit(quantity_matrix)
    if homogeneous:
        common_unit = _aggregate_unit(list(quantity_matrix), settings, common_unit)
    rows: list[list[str]] = []

    for row in range(quantity_matrix.rows):
        rendered_row: list[str] = []
        for col in range(quantity_matrix.cols):
            quantity = quantity_matrix.entry(row, col)
            if homogeneous:
                if common_unit is not None and not getattr(quantity, "dimensionless", False):
                    quantity = quantity.to(common_unit)
                rendered_row.append(_magnitude_latex(quantity, settings))
            else:
                rendered_row.append(_quantity_latex(quantity, settings=settings))
        rows.append(rendered_row)

    matrix_latex = _matrix_from_cells_latex(rows)
    if homogeneous and common_unit is not None:
        return rf"{matrix_latex}\,{format(common_unit, '~L')}"
    return matrix_latex


def _analysis_scalar_latex(value, settings: RenderSettings) -> str:
    if hasattr(value, "magnitude") and hasattr(value, "units"):
        return _quantity_latex(value, settings=settings)
    return _latex(value)


def _matrix_shape_latex(value: MatrixShape) -> str:
    return rf"\left({value.rows}, {value.cols}\right)"


def _eigenvalue_set_latex(value: EigenvalueSet, settings: RenderSettings) -> str:
    entries = [
        rf"\lambda={_analysis_scalar_latex(entry.value, settings)},\;m={entry.multiplicity}"
        for entry in value.entries
    ]
    return r"\left\{" + r"\; ; \;".join(entries) + r"\right\}"


def _eigenvector_set_latex(value: EigenvectorSet, settings: RenderSettings) -> str:
    entries: list[str] = []
    for entry in value.entries:
        vectors: list[str] = []
        for index, vector in enumerate(entry.vectors, start=1):
            if isinstance(vector, QuantityMatrix):
                vector_latex = _quantity_matrix_latex(vector, settings)
            else:
                vector_latex = _matrix_latex(vector)
            vectors.append(rf"\mathbf{{v}}_{{{index}}}={vector_latex}")
        vector_block = r",\;".join(vectors)
        entries.append(
            rf"\lambda={_analysis_scalar_latex(entry.value, settings)},"
            rf"\;m={entry.multiplicity},\;{vector_block}"
        )
    return r"\left\{" + r"\; ; \;".join(entries) + r"\right\}"


def _value_latex(value, settings: RenderSettings) -> str:
    if isinstance(value, MatrixShape):
        return _matrix_shape_latex(value)
    if isinstance(value, EigenvalueSet):
        return _eigenvalue_set_latex(value, settings)
    if isinstance(value, EigenvectorSet):
        return _eigenvector_set_latex(value, settings)
    if isinstance(value, QuantityMatrix):
        return _quantity_matrix_latex(value, settings)
    if isinstance(value, sp.MatrixBase):
        return _matrix_latex(value)
    return _latex(value)


def _partial_polynomial_latex(evaluated_terms: tuple[tuple[int, object], ...] | None, variable: str, settings: RenderSettings = _DEFAULT_RENDER_SETTINGS) -> str | None:
    if evaluated_terms is None:
        return None

    variable_latex = _latex(sp.Symbol(variable))
    rendered: list[str] = []

    for power, coefficient in evaluated_terms:
        magnitude = float(coefficient.magnitude)
        if abs(magnitude) < settings.zero_tolerance:
            continue

        coefficient_latex = _quantity_latex(abs(coefficient), settings=settings)
        if power == 0:
            term_latex = coefficient_latex
        elif power == 1:
            term_latex = rf"{coefficient_latex}\,{variable_latex}"
        else:
            term_latex = rf"{coefficient_latex}\,{variable_latex}^{{{power}}}"

        if not rendered:
            prefix = "- " if magnitude < 0 else ""
        else:
            prefix = " - " if magnitude < 0 else " + "
        rendered.append(prefix + term_latex)

    zero_latex = f"{0.0:.{settings.precision}f}"
    return "".join(rendered) if rendered else zero_latex


def _piecewise_partial_latex(piecewise, substitutions: dict[str, object], settings: RenderSettings) -> str:
    variable_latex = _latex(sp.Symbol(piecewise.interval_variable))
    operator_latex = {
        "<": "<",
        "<=": r"\leq",
        ">": ">",
        ">=": r"\geq",
    }
    rendered = []
    for branch in piecewise.branches:
        value = branch.value
        if hasattr(value, "magnitude") and hasattr(value, "units"):
            value_latex = _quantity_latex(value, settings=settings)
        elif branch.evaluated_terms is not None:
            value_latex = _partial_polynomial_latex(
                branch.evaluated_terms,
                piecewise.interval_variable,
                settings,
            )
        else:
            value_latex = _substitution_latex(
                sp.sympify(value),
                substitutions,
                settings,
            )

        if branch.operator is None:
            rendered.append(rf"{value_latex} & \text{{otherwise}}")
            continue

        breakpoint = branch.breakpoint
        if hasattr(breakpoint, "magnitude") and hasattr(breakpoint, "units"):
            breakpoint_latex = _quantity_latex(breakpoint, settings=settings)
        else:
            breakpoint_latex = _substitution_latex(
                sp.sympify(breakpoint),
                substitutions,
                settings,
            )
        rendered.append(
            rf"{value_latex} & \text{{for}}\: "
            rf"{variable_latex} {operator_latex[branch.operator]} {breakpoint_latex}"
        )

    return r"\begin{cases} " + r" \\ ".join(rendered) + r" \end{cases}"


def _display_lhs(
    result: (
        NumericEvaluationResult
        | PartialNumericEvaluationResult
        | NumericMatrixEvaluationResult
        | PartialMatrixNumericEvaluationResult
    ),
) -> str | None:
    if result.display_name is None:
        return None
    if result.display_arguments is None:
        return _render_lhs(result.display_name, None)
    return _render_function_call_lhs(result.display_name, result.display_arguments)


def _shows_substitution(
    result: (
        NumericEvaluationResult
        | PartialNumericEvaluationResult
        | NumericMatrixEvaluationResult
        | PartialMatrixNumericEvaluationResult
    ),
) -> bool:
    """Return False for the compact result(...) presentation alias."""
    return re.match(r"^result\s*\(", result.statement.source.strip()) is None


_NUMERIC_ROW_VISUAL_BUDGET = 64.0
_COMPLETE_ROW_VISUAL_BUDGET = 104.0


def _latex_visual_width(latex: str) -> float:
    """Estimate rendered MathJax width from visual LaTeX complexity."""
    normalized = latex
    normalized = normalized.replace(r"\left", "").replace(r"\right", "")
    normalized = normalized.replace(r"\,", "").replace(r"\!", "")
    normalized = normalized.replace(r"\quad", "  ")
    normalized = normalized.replace(r"\cdot", "·")
    normalized = re.sub(r"\\mathrm\{([^{}]+)\}", r"\1", normalized)

    fraction_count = normalized.count(r"\frac")
    normalized = normalized.replace(r"\frac", "")
    normalized = re.sub(r"\\(?:displaystyle|textstyle|scriptstyle)", "", normalized)
    normalized = re.sub(r"\\[A-Za-z]+", "X", normalized)
    normalized = normalized.replace("{", "").replace("}", "")

    return float(len(normalized) + 6 * fraction_count)


def _render_signed_term(term: sp.Expr, *, substitutions: dict[str, object] | None, settings: RenderSettings) -> tuple[bool, str]:
    negative = term.could_extract_minus_sign()
    unsigned_term = -term if negative else term
    if substitutions is None:
        body = _latex(unsigned_term)
    else:
        body = _substitution_latex(unsigned_term, substitutions, settings)
    return negative, body


def _adaptive_additive_rows(expression: sp.Expr, substitutions: dict[str, object] | None = None, *, visual_budget: float = _NUMERIC_ROW_VISUAL_BUDGET, settings: RenderSettings = _DEFAULT_RENDER_SETTINGS) -> list[str]:
    """Pack complete top-level additive terms into MathJax rows adaptively."""
    expression = sp.sympify(expression)
    terms = expression.as_ordered_terms() if expression.is_Add else [expression]
    rendered_terms = [_render_signed_term(term, substitutions=substitutions, settings=settings) for term in terms]

    packed: list[list[tuple[int, bool, str]]] = []
    current: list[tuple[int, bool, str]] = []
    current_width = 0.0

    for index, (negative, body) in enumerate(rendered_terms):
        sign_width = 0.0 if index == 0 and not negative else 2.0
        term_width = _latex_visual_width(body) + sign_width

        if current and current_width + term_width > visual_budget:
            packed.append(current)
            current = []
            current_width = 0.0

        current.append((index, negative, body))
        current_width += term_width

    if current:
        packed.append(current)

    rows: list[str] = []
    for row_terms in packed:
        pieces: list[str] = []
        for term_index_in_row, (global_index, negative, body) in enumerate(row_terms):
            if term_index_in_row == 0:
                if global_index == 0:
                    prefix = "- " if negative else ""
                else:
                    prefix = r"\quad - " if negative else r"\quad + "
            else:
                prefix = " - " if negative else " + "
            pieces.append(prefix + body)
        rows.append("".join(pieces))

    return rows


def _multiplicative_factor_key(term):
    denominator_factor = bool(term.is_Pow and term.exp.is_number and term.exp.is_negative)
    return (1 if denominator_factor else 0, _engineering_factor_key(term))


def _render_multiplicative_factor(
    factor: sp.Expr,
    substitutions: dict[str, object] | None,
    settings: RenderSettings,
) -> str:
    if substitutions is None:
        rendered = _latex(factor)
    else:
        rendered = _substitution_latex(factor, substitutions, settings)
    if factor.is_Add:
        rendered = rf"\left({rendered}\right)"
    return rendered


def _bounded_product_rows(
    expression: sp.Expr,
    substitutions: dict[str, object] | None = None,
    *,
    settings: RenderSettings = _DEFAULT_RENDER_SETTINGS,
) -> list[str]:
    """Split one commutative product/fraction at factor boundaries for display."""
    expression = sp.sympify(expression)
    if expression.could_extract_minus_sign():
        expression = -expression
    if not expression.is_Mul:
        return []

    factors = sorted(expression.args, key=_multiplicative_factor_key)
    rendered_factors = [
        _render_multiplicative_factor(factor, substitutions, settings)
        for factor in factors
    ]

    rows: list[str] = []
    current = ""
    for factor_latex in rendered_factors:
        separator = "" if not current else " "
        candidate = f"{current}{separator}{factor_latex}"
        if current and _latex_visual_width(candidate) > _NUMERIC_ROW_VISUAL_BUDGET:
            rows.append(current)
            current = rf"\quad \cdot {factor_latex}"
        else:
            current = candidate

    if current:
        rows.append(current)
    return rows


def _split_overwide_terms(
    expression: sp.Expr,
    substitutions: dict[str, object] | None = None,
    *,
    settings: RenderSettings = _DEFAULT_RENDER_SETTINGS,
) -> list[str]:
    """Split only over-budget multiplicative terms while preserving additive signs."""
    expression = sp.sympify(expression)
    terms = expression.as_ordered_terms() if expression.is_Add else [expression]
    rows: list[str] = []

    for index, term in enumerate(terms):
        negative, body = _render_signed_term(
            term,
            substitutions=substitutions,
            settings=settings,
        )
        if index == 0:
            prefix = "- " if negative else ""
        else:
            prefix = r"\quad - " if negative else r"\quad + "

        if _latex_visual_width(prefix + body) <= _NUMERIC_ROW_VISUAL_BUDGET:
            rows.append(prefix + body)
            continue

        unsigned_term = -term if negative else term
        product_rows = _bounded_product_rows(
            unsigned_term,
            substitutions,
            settings=settings,
        )
        if not product_rows:
            rows.append(prefix + body)
            continue

        rows.append(prefix + product_rows[0])
        rows.extend(product_rows[1:])

    return rows


def _bounded_expression_rows(expression: sp.Expr, substitutions: dict[str, object] | None = None, *, settings: RenderSettings = _DEFAULT_RENDER_SETTINGS) -> list[str]:
    """Return additive rows and split overwide products/fractions at safe factor boundaries."""
    expression = sp.sympify(expression)
    rows = _adaptive_additive_rows(expression, substitutions, settings=settings)
    if all(_latex_visual_width(row) <= _NUMERIC_ROW_VISUAL_BUDGET for row in rows):
        return rows

    expanded = sp.expand(expression)
    if sp.sstr(expanded) != sp.sstr(expression):
        expanded_rows = _adaptive_additive_rows(expanded, substitutions, settings=settings)
        if max(_latex_visual_width(row) for row in expanded_rows) < max(_latex_visual_width(row) for row in rows):
            expression = expanded
            rows = expanded_rows
    if all(_latex_visual_width(row) <= _NUMERIC_ROW_VISUAL_BUDGET for row in rows):
        return rows

    split_rows = _split_overwide_terms(
        expression,
        substitutions,
        settings=settings,
    )
    if split_rows:
        return split_rows
    return rows


def _append_assignment_stage(rows: list[str], lhs: str | None, body_rows: list[str]) -> None:
    """Append one aligned stage without allowing a long body to enlarge the identity column."""
    if not body_rows:
        return

    if lhs is None:
        rows.append(rf" & & \displaystyle {body_rows[0]}")
        for continuation in body_rows[1:]:
            rows.append(rf" & & \displaystyle {continuation}")
        return

    candidate = rf"\displaystyle {lhs} & = & \displaystyle {body_rows[0]}"
    if _latex_visual_width(candidate) <= _COMPLETE_ROW_VISUAL_BUDGET:
        rows.append(candidate)
        for continuation in body_rows[1:]:
            rows.append(rf" & & \displaystyle {continuation}")
        return

    rows.append(rf"\displaystyle {lhs} & = &")
    for body in body_rows:
        rows.append(rf" & & \displaystyle {body}")


def _numeric_evaluation_rows(result: NumericEvaluationResult, settings: RenderSettings) -> list[str]:
    formula_rows = _bounded_expression_rows(result.symbolic_expression, settings=settings)
    final_latex = _quantity_latex(result.quantity, settings=settings, declared=False)
    lhs = _display_lhs(result)

    rows: list[str] = []
    _append_assignment_stage(rows, lhs, formula_rows)
    if _shows_substitution(result):
        substituted_rows = _bounded_expression_rows(
            result.symbolic_expression,
            result.substitutions,
            settings=settings,
        )
        for index, body in enumerate(substituted_rows):
            if index == 0:
                rows.append(rf" & = & \displaystyle {body}")
            else:
                rows.append(rf" & & \displaystyle {body}")
    rows.append(rf" & = & \displaystyle {final_latex}")
    return rows


def _partial_numeric_evaluation_rows(result: PartialNumericEvaluationResult, settings: RenderSettings) -> list[str]:
    formula_rows = _bounded_expression_rows(result.symbolic_expression, settings=settings)
    evaluated_latex = None
    if result.piecewise_evaluation is not None:
        evaluated_latex = _piecewise_partial_latex(
            result.piecewise_evaluation,
            result.substitutions,
            settings,
        )
    elif len(result.unresolved_symbols) == 1:
        evaluated_latex = _partial_polynomial_latex(result.evaluated_terms, result.unresolved_symbols[0], settings)
    lhs = _display_lhs(result)

    rows: list[str] = []
    _append_assignment_stage(rows, lhs, formula_rows)
    if _shows_substitution(result):
        substituted_rows = _bounded_expression_rows(
            result.symbolic_expression,
            result.substitutions,
            settings=settings,
        )
        for index, body in enumerate(substituted_rows):
            if index == 0:
                rows.append(rf" & = & \displaystyle {body}")
            else:
                rows.append(rf" & & \displaystyle {body}")
    if evaluated_latex is not None:
        rows.append(rf" & = & \displaystyle {evaluated_latex}")
    return rows


def _matrix_stage_rows(lhs: str | None, stages: list[str]) -> list[str]:
    if not stages:
        return []
    if lhs is None:
        rows = [rf" & & \displaystyle {stages[0]}"]
    else:
        rows = [rf"\displaystyle {lhs} & = & \displaystyle {stages[0]}"]
    rows.extend(rf" & = & \displaystyle {stage}" for stage in stages[1:])
    return rows


def _numeric_matrix_evaluation_rows(
    result: NumericMatrixEvaluationResult,
    settings: RenderSettings,
) -> list[str]:
    stages = [_matrix_latex(result.symbolic_matrix)]
    if _shows_substitution(result):
        stages.append(
            _matrix_substitution_latex(
                result.symbolic_matrix,
                result.substitutions,
                settings,
            )
        )
    stages.append(_quantity_matrix_latex(result.quantity_matrix, settings))
    return _matrix_stage_rows(_display_lhs(result), stages)


def _partial_matrix_numeric_evaluation_rows(
    result: PartialMatrixNumericEvaluationResult,
    settings: RenderSettings,
) -> list[str]:
    stages = [_matrix_latex(result.symbolic_matrix)]
    if _shows_substitution(result):
        stages.append(
            _matrix_substitution_latex(
                result.symbolic_matrix,
                result.substitutions,
                settings,
            )
        )
    return _matrix_stage_rows(_display_lhs(result), stages)


def _standard_result_row(result: CalculationResult, settings: RenderSettings) -> str:
    rendered = render_result(result, settings=settings)
    if " = " in rendered:
        left, right = rendered.split(" = ", 1)
        return rf"\displaystyle {left} & = & \displaystyle {right}"
    return rf"\displaystyle {rendered} & &"


def _equality_stage_rows(display_input: sp.Equality, settings: RenderSettings) -> list[str]:
    """Render the equation being solved entirely in the right-hand block."""
    lhs_rows = _bounded_expression_rows(display_input.lhs, settings=settings)
    rhs_latex = _latex(display_input.rhs)
    rows: list[str] = []
    for index, equation_row in enumerate(lhs_rows):
        if index == len(lhs_rows) - 1:
            rows.append(rf" & & \displaystyle {equation_row} = {rhs_latex}")
        else:
            rows.append(rf" & & \displaystyle {equation_row}")
    return rows


def _symbolic_evaluation_rows(result: EvaluationResult, settings: RenderSettings) -> list[str]:
    statement = result.statement
    lhs = _render_lhs(statement.target, statement.parameters)
    if isinstance(
        result.value,
        (sp.MatrixBase, MatrixShape, EigenvalueSet, EigenvectorSet, QuantityMatrix),
    ):
        return [_standard_result_row(result, settings)]

    value = sp.sympify(result.value)
    display_input = result.display_input

    if display_input is None or sp.sstr(display_input) == sp.sstr(value):
        value_rows = _bounded_expression_rows(value, settings=settings)
        if len(value_rows) == 1:
            standard = _standard_result_row(result, settings)
            if _latex_visual_width(standard) <= _COMPLETE_ROW_VISUAL_BUDGET:
                return [standard]
        rows: list[str] = []
        _append_assignment_stage(rows, lhs, value_rows)
        return rows

    if isinstance(display_input, sp.Equality):
        rows = _equality_stage_rows(display_input, settings)
        value_rows = _bounded_expression_rows(value, settings=settings)
        _append_assignment_stage(rows, lhs, value_rows)
        return rows

    input_latex = _latex(display_input)
    value_rows = _bounded_expression_rows(value, settings=settings)
    lhs_width = _latex_visual_width(lhs) + 3.0 if lhs is not None else 0.0
    chain_width = lhs_width + _latex_visual_width(input_latex) + sum(_latex_visual_width(row) for row in value_rows) + 6.0
    if len(value_rows) == 1 and chain_width <= _NUMERIC_ROW_VISUAL_BUDGET:
        return [_standard_result_row(result, settings)]

    rows: list[str] = []
    input_candidate = rf"\displaystyle {lhs} & = & \displaystyle {input_latex}" if lhs is not None else rf" & & \displaystyle {input_latex}"
    if _latex_visual_width(input_candidate) <= _COMPLETE_ROW_VISUAL_BUDGET:
        rows.append(input_candidate)
    else:
        if lhs is not None:
            rows.append(rf"\displaystyle {lhs} & = &")
        rows.append(rf" & & \displaystyle {input_latex}")

    for index, body in enumerate(value_rows):
        if index == 0:
            rows.append(rf" & = & \displaystyle {body}")
        else:
            rows.append(rf" & & \displaystyle {body}")
    return rows


def _display_rows(result: CalculationResult, settings: RenderSettings) -> list[str]:
    if isinstance(result, NumericMatrixEvaluationResult):
        return _numeric_matrix_evaluation_rows(result, settings)
    if isinstance(result, PartialMatrixNumericEvaluationResult):
        return _partial_matrix_numeric_evaluation_rows(result, settings)
    if isinstance(result, NumericEvaluationResult):
        return _numeric_evaluation_rows(result, settings)
    if isinstance(result, PartialNumericEvaluationResult):
        return _partial_numeric_evaluation_rows(result, settings)
    if isinstance(result, EvaluationResult):
        return _symbolic_evaluation_rows(result, settings)
    return [_standard_result_row(result, settings)]


def _stage_spacing_sequence(stage_lengths: list[int]) -> list[str]:
    """Return semantic gaps: 4 pt within one stage and 8 pt between stages."""
    spacings: list[str] = []
    row_seen = False
    for stage_length in stage_lengths:
        if stage_length <= 0:
            continue
        for row_index in range(stage_length):
            if not row_seen:
                row_seen = True
                continue
            spacings.append("8pt" if row_index == 0 else "4pt")
    return spacings


def _assignment_stage_row_count(lhs: str | None, body_rows: list[str]) -> int:
    stage_rows: list[str] = []
    _append_assignment_stage(stage_rows, lhs, body_rows)
    return len(stage_rows)


def _internal_row_spacings(
    result: CalculationResult,
    result_rows: list[str],
    settings: RenderSettings,
) -> list[str]:
    """Classify internal rows as wrapped continuations or new mathematical stages."""
    if len(result_rows) <= 1:
        return []

    if isinstance(result, NumericMatrixEvaluationResult):
        stage_lengths = [1, 1]
        if _shows_substitution(result):
            stage_lengths.insert(1, 1)

    elif isinstance(result, PartialMatrixNumericEvaluationResult):
        stage_lengths = [1]
        if _shows_substitution(result):
            stage_lengths.append(1)

    elif isinstance(result, NumericEvaluationResult):
        formula_rows = _bounded_expression_rows(
            result.symbolic_expression,
            settings=settings,
        )
        stage_lengths = [
            _assignment_stage_row_count(_display_lhs(result), formula_rows)
        ]
        if _shows_substitution(result):
            stage_lengths.append(
                len(
                    _bounded_expression_rows(
                        result.symbolic_expression,
                        result.substitutions,
                        settings=settings,
                    )
                )
            )
        stage_lengths.append(1)

    elif isinstance(result, PartialNumericEvaluationResult):
        formula_rows = _bounded_expression_rows(
            result.symbolic_expression,
            settings=settings,
        )
        stage_lengths = [
            _assignment_stage_row_count(_display_lhs(result), formula_rows)
        ]
        if _shows_substitution(result):
            stage_lengths.append(
                len(
                    _bounded_expression_rows(
                        result.symbolic_expression,
                        result.substitutions,
                        settings=settings,
                    )
                )
            )
        evaluated_latex = None
        if result.piecewise_evaluation is not None:
            evaluated_latex = _piecewise_partial_latex(
                result.piecewise_evaluation,
                result.substitutions,
                settings,
            )
        elif len(result.unresolved_symbols) == 1:
            evaluated_latex = _partial_polynomial_latex(
                result.evaluated_terms,
                result.unresolved_symbols[0],
                settings,
            )
        if evaluated_latex is not None:
            stage_lengths.append(1)

    elif isinstance(result, EvaluationResult):
        statement = result.statement
        lhs = _render_lhs(statement.target, statement.parameters)
        value = sp.sympify(result.value)
        display_input = result.display_input

        if display_input is None or sp.sstr(display_input) == sp.sstr(value):
            stage_lengths = [len(result_rows)]
        elif isinstance(display_input, sp.Equality):
            value_rows = _bounded_expression_rows(value, settings=settings)
            stage_lengths = [
                len(_equality_stage_rows(display_input, settings)),
                _assignment_stage_row_count(lhs, value_rows),
            ]
        else:
            input_latex = _latex(display_input)
            input_candidate = (
                rf"\displaystyle {lhs} & = & \displaystyle {input_latex}"
                if lhs is not None
                else rf" & & \displaystyle {input_latex}"
            )
            input_stage_length = 1
            if _latex_visual_width(input_candidate) > _COMPLETE_ROW_VISUAL_BUDGET:
                input_stage_length += 1 if lhs is not None else 0
            value_rows = _bounded_expression_rows(value, settings=settings)
            stage_lengths = [input_stage_length, len(value_rows)]

    else:
        stage_lengths = [len(result_rows)]

    spacings = _stage_spacing_sequence(stage_lengths)
    expected = len(result_rows) - 1
    if len(spacings) != expected:
        raise RuntimeError(
            "renderer semantic spacing metadata does not match rendered row count"
        )
    return spacings


def render_aligned_results(results: list[CalculationResult], *, settings: RenderSettings | None = None) -> str:
    """Render all calculation groups with one consistent MathJax array layout."""
    if not results:
        return ""

    active_settings = settings or _DEFAULT_RENDER_SETTINGS
    rows: list[str] = []
    for result_index, result in enumerate(results):
        result_rows = _display_rows(result, active_settings)

        if result_index:
            spacing = "16pt" if result.statement.blank_before else "8pt"
            rows.append(rf"\\[{spacing}]")
        rows.append(result_rows[0])

        internal_spacings = _internal_row_spacings(
            result,
            result_rows,
            active_settings,
        )
        for spacing, continuation_row in zip(
            internal_spacings,
            result_rows[1:],
        ):
            rows.append(rf"\\[{spacing}]")
            rows.append(continuation_row)

    body = " ".join(rows)
    return rf"\hspace{{0.2em}}\begin{{array}}{{lcl}} {body} \end{{array}}"


def _table_unit_text(unit) -> str:
    if str(unit) == "dimensionless":
        return ""
    return format(unit, "~P")


def _table_header(label: str, unit) -> str:
    safe_label = escape(label)
    unit_text = _table_unit_text(unit)
    if not unit_text:
        return safe_label
    return f"{safe_label} [{escape(unit_text)}]"


def _in_unit(quantity, unit, settings: RenderSettings):
    """Convert for display, leaving dimensionless zeros and mismatches alone.

    A value that is a genuine zero in its stored unit is zeroed before conversion,
    so it cannot cross ``zero_tolerance`` on the way. See ``_is_genuine_zero``.
    """
    if unit is None or getattr(quantity, "dimensionless", False):
        return quantity
    if _is_genuine_zero(quantity, settings):
        quantity = quantity * 0.0
    try:
        return quantity.to(unit)
    except DimensionalityError:
        return quantity


def _table_magnitude(quantity, settings: RenderSettings) -> str:
    """A table column carries its unit in the header, so the unit is chosen once
    for the column and this only formats. See ``_aggregate_unit``."""
    return _magnitude_text(quantity.magnitude, settings)


def _aggregate_unit(quantities, settings: RenderSettings, fallback):
    """One unit for a whole table column or matrix, never one per cell.

    Scored by the significant figures the column keeps in total, so a single large
    value cannot drag the whole column into a unit that flattens the rest. Ties
    keep the unit the values already carry.
    """
    physical = [
        quantity
        for quantity in quantities
        if quantity is not None and not getattr(quantity, "dimensionless", False)
    ]
    if not physical or fallback is None:
        return fallback

    family = _unit_family(physical[0])
    if not family:
        return fallback
    if _unit_is_the_engineers(physical[0]) and all(
        _is_genuine_zero(quantity, settings)
        or _significant_figures(quantity.to(fallback).magnitude, settings.precision) > 0
        for quantity in physical
    ):
        # kN/mm is what the engineer typed and every cell still says something in it.
        return fallback

    def score(unit):
        total = 0.0
        for quantity in physical:
            try:
                converted = quantity.to(unit)
            except DimensionalityError:
                return None
            if abs(float(converted.magnitude)) < settings.zero_tolerance:
                continue
            band, distance = _band_distance(converted.magnitude)
            total += band + distance
        return total

    best_unit = fallback
    best_score = score(fallback)
    for name in family:
        candidate_score = score(name)
        if candidate_score is not None and (
            best_score is None or candidate_score < best_score
        ):
            best_unit, best_score = physical[0].to(name).units, candidate_score
    return best_unit


def render_table(
    result: TableResult,
    *,
    settings: RenderSettings | None = None,
) -> str:
    """Render a unit-aware engineering table as compact scoped HTML."""
    active_settings = settings or _DEFAULT_RENDER_SETTINGS
    point_unit = _aggregate_unit(result.point_values, active_settings, result.point_unit)
    column_units = [
        _aggregate_unit(column.values, active_settings, column.unit)
        for column in result.columns
    ]
    headers = [
        _table_header(result.variable, point_unit),
        *(
            _table_header(column.display_label, unit)
            for column, unit in zip(result.columns, column_units)
        ),
    ]
    header_html = "".join(f"<th>{header}</th>" for header in headers)

    rows: list[str] = []
    for row_index, point in enumerate(result.point_values):
        cells = [_table_magnitude(_in_unit(point, point_unit, active_settings), active_settings)]
        cells.extend(
            _table_magnitude(
                _in_unit(column.values[row_index], unit, active_settings), active_settings
            )
            for column, unit in zip(result.columns, column_units)
        )
        rows.append(
            "<tr>"
            + "".join(f"<td>{cell}</td>" for cell in cells)
            + "</tr>"
        )

    body_html = "".join(rows)
    return (
        '<style>'
        '.engcalc-table{margin:0.35rem 0 0.55rem 0;overflow-x:auto;}'
        '.engcalc-table table{border-collapse:collapse;font-size:0.92rem;line-height:1.35;}'
        '.engcalc-table th,.engcalc-table td{'
        'padding:0.28rem 0.62rem;border-bottom:1px solid rgba(127,127,127,0.20);'
        'text-align:right;white-space:nowrap;}'
        '.engcalc-table th{font-weight:600;border-bottom:1px solid rgba(127,127,127,0.42);}'
        '.engcalc-table th:first-child,.engcalc-table td:first-child{text-align:left;}'
        '</style>'
        '<div class="engcalc-table"><table>'
        f'<thead><tr>{header_html}</tr></thead>'
        f'<tbody>{body_html}</tbody>'
        '</table></div>'
    )



CharacteristicResult = RootsResult | IntersectionsResult | ExtremaResult


def _characteristic_role_text(role: str) -> str:
    return role.replace("_", " ")


def _characteristic_math(latex: str) -> str:
    return rf"\({latex}\)"


def _characteristic_quantity_math(quantity, settings: RenderSettings) -> str:
    return _characteristic_math(_quantity_latex(quantity, settings=settings))


def _characteristic_symbolic_math(value) -> str:
    return _characteristic_math(_latex(value))


def _characteristic_point_coordinate(
    point: CharacteristicPoint,
    variable: str,
    settings: RenderSettings,
) -> str:
    variable_html = _characteristic_symbolic_math(sp.Symbol(variable))
    if point.provenance == "numeric":
        return (
            f"{variable_html} ≈ "
            f"{_characteristic_quantity_math(point.x_quantity, settings)}"
        )

    symbolic = _characteristic_symbolic_math(point.x_symbolic)
    evaluated = _characteristic_quantity_math(point.x_quantity, settings)
    return f"{variable_html} = {symbolic} ({evaluated})"


def _characteristic_point_value(
    point: CharacteristicPoint,
    settings: RenderSettings,
) -> str | None:
    if point.value_symbolic is None and point.value_quantity is None:
        return None
    if point.provenance == "numeric" or point.value_symbolic is None:
        if point.value_quantity is None:
            return None
        return "value ≈ " + _characteristic_quantity_math(point.value_quantity, settings)

    symbolic = _characteristic_symbolic_math(point.value_symbolic)
    if point.value_quantity is None:
        return "value = " + symbolic
    evaluated = _characteristic_quantity_math(point.value_quantity, settings)
    return f"value = {symbolic} ({evaluated})"


def _characteristic_interval_text(
    interval: CharacteristicInterval,
    settings: RenderSettings,
) -> str:
    left = "[" if interval.lower_closed else "("
    right = "]" if interval.upper_closed else ")"
    lower = _quantity_latex(interval.lower_quantity, settings=settings)
    upper = _quantity_latex(interval.upper_quantity, settings=settings)
    return _characteristic_math(rf"{left}{lower},\;{upper}{right}")


def _characteristic_heading(result: CharacteristicResult) -> str:
    if isinstance(result, RootsResult):
        return f"Roots — {escape(result.display_label)}"
    if isinstance(result, IntersectionsResult):
        return (
            "Intersections — "
            f"{escape(result.left_label)} / {escape(result.right_label)}"
        )
    return f"Extrema — {escape(result.display_label)}"


def render_characteristic_result(
    result: CharacteristicResult,
    *,
    settings: RenderSettings | None = None,
) -> str:
    """Render one standalone exact-characteristic result as compact HTML/MathJax."""
    active_settings = settings or _DEFAULT_RENDER_SETTINGS
    domain = (
        _characteristic_quantity_math(result.lower_quantity, active_settings)
        + " to "
        + _characteristic_quantity_math(result.upper_quantity, active_settings)
    )

    rows: list[str] = []
    for point in result.points:
        parts = [
            _characteristic_point_coordinate(
                point,
                result.variable,
                active_settings,
            )
        ]
        value_text = _characteristic_point_value(point, active_settings)
        if value_text is not None and not isinstance(result, RootsResult):
            parts.append(value_text)
        if point.roles:
            parts.append(
                ", ".join(_characteristic_role_text(role) for role in point.roles)
            )
        if point.side != "at":
            parts.append(escape(point.side))
        rows.append("<div class=\"engcalc-characteristic-row\">" + " · ".join(parts) + "</div>")

    for interval in result.intervals:
        interval_text = _characteristic_interval_text(interval, active_settings)
        if isinstance(result, RootsResult) or interval.role == "roots":
            text = f"all x in {interval_text}"
        elif isinstance(result, IntersectionsResult) or interval.role == "coincident":
            text = f"coincident on {interval_text}"
        else:
            role = escape(_characteristic_role_text(interval.role))
            text = f"{role} on {interval_text}"
            if interval.value_quantity is not None:
                text += (
                    " · value = "
                    + _characteristic_quantity_math(
                        interval.value_quantity,
                        active_settings,
                    )
                )
        rows.append(f'<div class="engcalc-characteristic-row">{text}</div>')

    if isinstance(result, ExtremaResult):
        if result.unbounded_above:
            rows.append('<div class="engcalc-characteristic-row">unbounded above</div>')
        if result.unbounded_below:
            rows.append('<div class="engcalc-characteristic-row">unbounded below</div>')

    if not rows:
        rows.append('<div class="engcalc-characteristic-row">no finite characteristic points</div>')

    return (
        '<style>'
        '.engcalc-characteristics{margin:0.35rem 0 0.55rem 0;'
        'font-size:0.94rem;line-height:1.45;}'
        '.engcalc-characteristics-title{font-weight:600;margin-bottom:0.15rem;}'
        '.engcalc-characteristics-domain{opacity:0.78;margin-bottom:0.18rem;}'
        '.engcalc-characteristic-row{margin:0.08rem 0;}'
        '</style>'
        '<div class="engcalc-characteristics">'
        f'<div class="engcalc-characteristics-title">{_characteristic_heading(result)}</div>'
        f'<div class="engcalc-characteristics-domain">Domain: {domain}</div>'
        + "".join(rows)
        + '</div>'
    )

def render_system_solve_result(
    result: SystemSolveResult,
    *,
    settings: RenderSettings | None = None,
) -> str:
    """The equations as written, then one labelled line per unknown.

    Never an anonymous vector: the whole reason the unknowns are named in the call is
    that the reader - and the engineer scanning the memoria - can see which value
    belongs to which reaction.
    """
    rows = [rf"\displaystyle {_latex(equation)}" for equation in result.equations]
    for name, value in result.solutions:
        lhs = _render_lhs(name, None)
        rows.append(rf"\displaystyle {lhs} = {_value_latex(value, settings or _DEFAULT_RENDER_SETTINGS)}")
    body = r"\\".join(rows)
    return rf"\hspace{{0.2em}}\begin{{array}}{{l}} {body} \end{{array}}"


def render_result(result: CalculationResult, *, settings: RenderSettings | None = None) -> str:
    if isinstance(result, SystemSolveResult):
        return render_system_solve_result(result, settings=settings)
    if isinstance(result, (RootsResult, IntersectionsResult, ExtremaResult)):
        raise TypeError(
            "render_result does not support characteristic results; "
            "use render_characteristic_result"
        )

    active_settings = settings or _DEFAULT_RENDER_SETTINGS

    if isinstance(result, NumericAssignmentResult):
        lhs = _render_lhs(result.statement.target, None)
        return rf"{lhs} = {_quantity_latex(result.quantity, settings=active_settings)}"

    if isinstance(result, PartialMatrixNumericEvaluationResult):
        stages = [_matrix_latex(result.symbolic_matrix)]
        if _shows_substitution(result):
            stages.append(
                _matrix_substitution_latex(
                    result.symbolic_matrix,
                    result.substitutions,
                    active_settings,
                )
            )
        right = " = ".join(stages)
        lhs = _display_lhs(result)
        return rf"{lhs} = {right}" if lhs is not None else right

    if isinstance(result, NumericMatrixEvaluationResult):
        stages = [_matrix_latex(result.symbolic_matrix)]
        if _shows_substitution(result):
            stages.append(
                _matrix_substitution_latex(
                    result.symbolic_matrix,
                    result.substitutions,
                    active_settings,
                )
            )
        stages.append(_quantity_matrix_latex(result.quantity_matrix, active_settings))
        right = " = ".join(stages)
        lhs = _display_lhs(result)
        return rf"{lhs} = {right}" if lhs is not None else right

    if isinstance(result, PartialNumericEvaluationResult):
        formula_latex = _latex(result.symbolic_expression)
        evaluated_latex = None
        if result.piecewise_evaluation is not None:
            evaluated_latex = _piecewise_partial_latex(
                result.piecewise_evaluation,
                result.substitutions,
                active_settings,
            )
        elif len(result.unresolved_symbols) == 1:
            evaluated_latex = _partial_polynomial_latex(result.evaluated_terms, result.unresolved_symbols[0], active_settings)

        chain = [formula_latex]
        if _shows_substitution(result):
            chain.append(
                _substitution_latex(
                    result.symbolic_expression,
                    result.substitutions,
                    active_settings,
                )
            )
        if evaluated_latex is not None:
            chain.append(evaluated_latex)
        right = " = ".join(chain)

        if result.display_name is not None:
            if result.display_arguments is None:
                lhs = _render_lhs(result.display_name, None)
            else:
                lhs = _render_function_call_lhs(result.display_name, result.display_arguments)
            return rf"{lhs} = {right}"
        return right

    if isinstance(result, NumericEvaluationResult):
        formula_latex = _latex(result.symbolic_expression)
        final_latex = _quantity_latex(result.quantity, settings=active_settings, declared=False)
        chain = [formula_latex]
        if _shows_substitution(result):
            chain.append(
                _substitution_latex(
                    result.symbolic_expression,
                    result.substitutions,
                    active_settings,
                )
            )
        chain.append(final_latex)
        right = " = ".join(chain)
        if result.display_name is not None:
            if result.display_arguments is None:
                lhs = _render_lhs(result.display_name, None)
            else:
                lhs = _render_function_call_lhs(result.display_name, result.display_arguments)
            return rf"{lhs} = {right}"
        return right

    statement = result.statement
    lhs = _render_lhs(statement.target, statement.parameters)
    value_latex = _value_latex(result.value, active_settings)

    if lhs is None:
        if result.display_input is not None:
            return rf"{_latex(result.display_input)} = {value_latex}"
        return value_latex

    if result.display_input is not None:
        input_latex = _latex(result.display_input)
        if sp.sstr(result.display_input) != sp.sstr(result.value):
            return rf"{lhs} = {input_latex} = {value_latex}"
    return rf"{lhs} = {value_latex}"


def _render_function_call_lhs(name: str, arguments: tuple) -> str:
    if not isinstance(arguments, tuple):
        arguments = (arguments,)
    name_latex = _latex(sp.Symbol(name))
    argument_latex = ", ".join(_latex(argument) for argument in arguments)
    return rf"{name_latex}\left({argument_latex}\right)"


def _render_lhs(
    target: str | None,
    parameters: tuple[str, ...] | str | None,
) -> str | None:
    if target is None:
        return None
    if target.startswith("Sigma_") and len(target) > len("Sigma_"):
        quantity = target[len("Sigma_"):]
        target_latex = rf"\Sigma {_latex(sp.Symbol(quantity))}"
    else:
        target_latex = _latex(sp.Symbol(target))
    if parameters is None:
        return target_latex
    if isinstance(parameters, str):
        parameters = (parameters,)
    parameter_latex = ", ".join(
        _latex(sp.Symbol(parameter)) for parameter in parameters
    )
    return rf"{target_latex}\left({parameter_latex}\right)"
