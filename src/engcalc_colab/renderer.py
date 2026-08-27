from __future__ import annotations

import sympy as sp
from sympy.printing.latex import LatexPrinter

from .models import (
    EvaluationResult,
    NumericAssignmentResult,
    NumericEvaluationResult,
)

CalculationResult = EvaluationResult | NumericAssignmentResult | NumericEvaluationResult


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
            if self._needs_mul_brackets(
                term,
                first=(index == 0),
                last=(index == len(args) - 1),
            ):
                term_latex = rf"\left({term_latex}\right)"
            rendered.append(term_latex)

        return separator.join(rendered)


class _NumericSubstitutionLatexPrinter(_EngineeringLatexPrinter):
    def __init__(self, substitutions: dict[str, object]):
        super().__init__()
        self.substitutions = substitutions

    def _print_Symbol(self, expr):
        quantity = self.substitutions.get(expr.name)
        if quantity is None:
            return super()._print_Symbol(expr)
        return rf"\left({_quantity_latex(quantity)}\right)"


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


def _substitution_latex(expr, substitutions: dict[str, object]) -> str:
    return _NumericSubstitutionLatexPrinter(substitutions).doprint(expr)


def _quantity_latex(quantity, precision: int = 2) -> str:
    magnitude = float(quantity.magnitude)
    magnitude_latex = f"{magnitude:.{precision}f}"
    if getattr(quantity, "dimensionless", False):
        return magnitude_latex

    unit_latex = format(quantity.units, "~L")
    return rf"{magnitude_latex}\,{unit_latex}"


def render_aligned_results(results: list[CalculationResult]) -> str:
    """Render consecutive results as a three-column engineering calculation block."""
    if not results:
        return ""

    rows: list[str] = []
    for index, result in enumerate(results):
        rendered = render_result(result)
        if " = " in rendered:
            left, right = rendered.split(" = ", 1)
            row = rf"\displaystyle {left} & = & \displaystyle {right}"
        else:
            row = rf"\displaystyle {rendered} & &"

        if index:
            spacing = "8pt" if result.statement.blank_before else "4pt"
            rows.append(rf"\\[{spacing}]")
        rows.append(row)

    body = " ".join(rows)
    return rf"\hspace{{0.2em}}\begin{{array}}{{lcl}} {body} \end{{array}}"


def render_result(result: CalculationResult) -> str:
    if isinstance(result, NumericAssignmentResult):
        lhs = _render_lhs(result.statement.target, None)
        return rf"{lhs} = {_quantity_latex(result.quantity)}"

    if isinstance(result, NumericEvaluationResult):
        formula_latex = _latex(result.symbolic_expression)
        substituted_latex = _substitution_latex(
            result.symbolic_expression,
            result.substitutions,
        )
        final_latex = _quantity_latex(result.quantity)
        if result.display_name is not None:
            lhs = _render_lhs(result.display_name, None)
            return rf"{lhs} = {formula_latex} = {substituted_latex} = {final_latex}"
        return rf"{formula_latex} = {substituted_latex} = {final_latex}"

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
