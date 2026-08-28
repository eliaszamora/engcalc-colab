from __future__ import annotations

import re
from dataclasses import dataclass

import sympy as sp
from sympy.printing.latex import LatexPrinter

from .models import (
    EvaluationResult,
    NumericAssignmentResult,
    NumericEvaluationResult,
    PartialNumericEvaluationResult,
)

CalculationResult = (
    EvaluationResult
    | NumericAssignmentResult
    | NumericEvaluationResult
    | PartialNumericEvaluationResult
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


def _quantity_latex(quantity, precision: int | None = None, *, settings: RenderSettings | None = None) -> str:
    active_settings = settings or _DEFAULT_RENDER_SETTINGS
    active_precision = active_settings.precision if precision is None else precision
    magnitude = float(quantity.magnitude)
    if abs(magnitude) < active_settings.zero_tolerance:
        magnitude = 0.0
    magnitude_latex = f"{magnitude:.{active_precision}f}"
    if getattr(quantity, "dimensionless", False):
        return magnitude_latex

    unit_latex = format(quantity.units, "~L")
    return rf"{magnitude_latex}\,{unit_latex}"


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


def _display_lhs(result: NumericEvaluationResult | PartialNumericEvaluationResult) -> str | None:
    if result.display_name is None:
        return None
    if result.display_argument is None:
        return _render_lhs(result.display_name, None)
    return _render_function_call_lhs(result.display_name, result.display_argument)


def _shows_substitution(result: NumericEvaluationResult | PartialNumericEvaluationResult) -> bool:
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


def _bounded_expression_rows(expression: sp.Expr, substitutions: dict[str, object] | None = None, *, settings: RenderSettings = _DEFAULT_RENDER_SETTINGS) -> list[str]:
    """Return additive rows, expanding only for presentation when a group remains too wide."""
    expression = sp.sympify(expression)
    rows = _adaptive_additive_rows(expression, substitutions, settings=settings)
    if all(_latex_visual_width(row) <= _NUMERIC_ROW_VISUAL_BUDGET for row in rows):
        return rows

    expanded = sp.expand(expression)
    if sp.sstr(expanded) != sp.sstr(expression):
        expanded_rows = _adaptive_additive_rows(expanded, substitutions, settings=settings)
        if max(_latex_visual_width(row) for row in expanded_rows) < max(_latex_visual_width(row) for row in rows):
            rows = expanded_rows
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
    final_latex = _quantity_latex(result.quantity, settings=settings)
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
    if len(result.unresolved_symbols) == 1:
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
    lhs = _render_lhs(statement.target, statement.parameter)
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
    if isinstance(result, NumericEvaluationResult):
        return _numeric_evaluation_rows(result, settings)
    if isinstance(result, PartialNumericEvaluationResult):
        return _partial_numeric_evaluation_rows(result, settings)
    if isinstance(result, EvaluationResult):
        return _symbolic_evaluation_rows(result, settings)
    return [_standard_result_row(result, settings)]


def render_aligned_results(results: list[CalculationResult], *, settings: RenderSettings | None = None) -> str:
    """Render all calculation groups with one consistent MathJax array layout."""
    if not results:
        return ""

    active_settings = settings or _DEFAULT_RENDER_SETTINGS
    rows: list[str] = []
    for result_index, result in enumerate(results):
        result_rows = _display_rows(result, active_settings)

        if result_index:
            spacing = "8pt" if result.statement.blank_before else "4pt"
            rows.append(rf"\\[{spacing}]")
        rows.append(result_rows[0])

        for continuation_row in result_rows[1:]:
            rows.append(r"\\[2pt]")
            rows.append(continuation_row)

    body = " ".join(rows)
    return rf"\hspace{{0.2em}}\begin{{array}}{{lcl}} {body} \end{{array}}"


def render_result(result: CalculationResult, *, settings: RenderSettings | None = None) -> str:
    active_settings = settings or _DEFAULT_RENDER_SETTINGS

    if isinstance(result, NumericAssignmentResult):
        lhs = _render_lhs(result.statement.target, None)
        return rf"{lhs} = {_quantity_latex(result.quantity, settings=active_settings)}"

    if isinstance(result, PartialNumericEvaluationResult):
        formula_latex = _latex(result.symbolic_expression)
        evaluated_latex = None
        if len(result.unresolved_symbols) == 1:
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
            if result.display_argument is None:
                lhs = _render_lhs(result.display_name, None)
            else:
                lhs = _render_function_call_lhs(result.display_name, result.display_argument)
            return rf"{lhs} = {right}"
        return right

    if isinstance(result, NumericEvaluationResult):
        formula_latex = _latex(result.symbolic_expression)
        final_latex = _quantity_latex(result.quantity, settings=active_settings)
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
            if result.display_argument is None:
                lhs = _render_lhs(result.display_name, None)
            else:
                lhs = _render_function_call_lhs(result.display_name, result.display_argument)
            return rf"{lhs} = {right}"
        return right

    statement = result.statement
    lhs = _render_lhs(statement.target, statement.parameter)
    value_latex = _latex(result.value)

    if lhs is None:
        if result.display_input is not None:
            return rf"{_latex(result.display_input)} = {value_latex}"
        return value_latex

    if result.display_input is not None:
        input_latex = _latex(result.display_input)
        if sp.sstr(result.display_input) != sp.sstr(result.value):
            return rf"{lhs} = {input_latex} = {value_latex}"
    return rf"{lhs} = {value_latex}"


def _render_function_call_lhs(name: str, argument) -> str:
    name_latex = _latex(sp.Symbol(name))
    return rf"{name_latex}\left({_latex(argument)}\right)"


def _render_lhs(target: str | None, parameter: str | None) -> str | None:
    if target is None:
        return None
    if target.startswith("Sigma_") and len(target) > len("Sigma_"):
        quantity = target[len("Sigma_"):]
        target_latex = rf"\Sigma {_latex(sp.Symbol(quantity))}"
    else:
        target_latex = _latex(sp.Symbol(target))
    if parameter is None:
        return target_latex
    parameter_latex = _latex(sp.Symbol(parameter))
    return rf"{target_latex}\left({parameter_latex}\right)"