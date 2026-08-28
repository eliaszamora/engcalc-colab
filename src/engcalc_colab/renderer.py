from __future__ import annotations

from html import escape

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


def _partial_polynomial_latex(
    evaluated_terms: tuple[tuple[int, object], ...] | None,
    variable: str,
) -> str | None:
    if evaluated_terms is None:
        return None

    variable_latex = _latex(sp.Symbol(variable))
    rendered: list[str] = []

    for power, coefficient in evaluated_terms:
        magnitude = float(coefficient.magnitude)
        if magnitude == 0:
            continue

        coefficient_latex = _quantity_latex(abs(coefficient))
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

    return "".join(rendered) if rendered else "0.00"


def _display_lhs(result: NumericEvaluationResult | PartialNumericEvaluationResult) -> str | None:
    if result.display_name is None:
        return None
    if result.display_argument is None:
        return _render_lhs(result.display_name, None)
    return _render_function_call_lhs(
        result.display_name,
        result.display_argument,
    )


def _additive_substitution_rows(
    expression: sp.Expr,
    substitutions: dict[str, object],
) -> list[str]:
    """Render a substituted sum one top-level term per visual row."""
    expression = sp.sympify(expression)
    terms = expression.as_ordered_terms() if expression.is_Add else [expression]
    rows: list[str] = []

    for index, term in enumerate(terms):
        negative = term.could_extract_minus_sign()
        unsigned_term = -term if negative else term
        term_latex = _substitution_latex(unsigned_term, substitutions)

        if index == 0:
            prefix = "- " if negative else ""
        else:
            prefix = r"\quad - " if negative else r"\quad + "
        rows.append(prefix + term_latex)

    return rows


def _numeric_evaluation_rows(result: NumericEvaluationResult) -> list[str]:
    formula_latex = _latex(result.symbolic_expression)
    substituted_rows = _additive_substitution_rows(
        result.symbolic_expression,
        result.substitutions,
    )
    final_latex = _quantity_latex(result.quantity)
    lhs = _display_lhs(result)

    rows: list[str] = []
    if lhs is not None:
        rows.append(rf"\displaystyle {lhs} & = & \displaystyle {formula_latex}")
        rows.append(rf" & = & \displaystyle {substituted_rows[0]}")
    else:
        rows.append(
            rf"\displaystyle {formula_latex} & = & \displaystyle {substituted_rows[0]}"
        )

    for continuation in substituted_rows[1:]:
        rows.append(rf" & & \displaystyle {continuation}")

    rows.append(rf" & = & \displaystyle {final_latex}")
    return rows


def _partial_numeric_evaluation_rows(result: PartialNumericEvaluationResult) -> list[str]:
    formula_latex = _latex(result.symbolic_expression)
    substituted_rows = _additive_substitution_rows(
        result.symbolic_expression,
        result.substitutions,
    )
    evaluated_latex = None
    if len(result.unresolved_symbols) == 1:
        evaluated_latex = _partial_polynomial_latex(
            result.evaluated_terms,
            result.unresolved_symbols[0],
        )
    lhs = _display_lhs(result)

    rows: list[str] = []
    if lhs is not None:
        rows.append(rf"\displaystyle {lhs} & = & \displaystyle {formula_latex}")
        rows.append(rf" & = & \displaystyle {substituted_rows[0]}")
    else:
        rows.append(
            rf"\displaystyle {formula_latex} & = & \displaystyle {substituted_rows[0]}"
        )

    for continuation in substituted_rows[1:]:
        rows.append(rf" & & \displaystyle {continuation}")

    if evaluated_latex is not None:
        rows.append(rf" & = & \displaystyle {evaluated_latex}")
    return rows


def _standard_result_row(result: CalculationResult) -> str:
    rendered = render_result(result)
    if " = " in rendered:
        left, right = rendered.split(" = ", 1)
        return rf"\displaystyle {left} & = & \displaystyle {right}"
    return rf"\displaystyle {rendered} & &"


def _display_rows(result: CalculationResult) -> list[str]:
    if isinstance(result, NumericEvaluationResult):
        return _numeric_evaluation_rows(result)
    if isinstance(result, PartialNumericEvaluationResult):
        return _partial_numeric_evaluation_rows(result)
    return [_standard_result_row(result)]


def render_aligned_results(results: list[CalculationResult]) -> str:
    """Render results in the legacy three-column MathJax array layout."""
    if not results:
        return ""

    rows: list[str] = []
    for result_index, result in enumerate(results):
        result_rows = _display_rows(result)

        if result_index:
            spacing = "8pt" if result.statement.blank_before else "4pt"
            rows.append(rf"\\[{spacing}]")
        rows.append(result_rows[0])

        for continuation_row in result_rows[1:]:
            rows.append(r"\\[2pt]")
            rows.append(continuation_row)

    body = " ".join(rows)
    return rf"\hspace{{0.2em}}\begin{{array}}{{lcl}} {body} \end{{array}}"


_RESPONSIVE_STYLE = """
<style>
.engcalc-responsive{width:100%;max-width:100%;box-sizing:border-box;}
.engcalc-responsive .engcalc-calculation{width:100%;min-width:0;}
.engcalc-responsive .engcalc-stage{display:grid;grid-template-columns:max-content 1.15em minmax(0,1fr);column-gap:.35em;align-items:baseline;min-width:0;}
.engcalc-responsive .engcalc-stage+.engcalc-stage{margin-top:2pt;}
.engcalc-responsive .engcalc-lhs,.engcalc-responsive .engcalc-eq{white-space:nowrap;}
.engcalc-responsive .engcalc-rhs{min-width:0;}
.engcalc-responsive .engcalc-terms{display:flex;flex-wrap:wrap;align-items:baseline;column-gap:.45em;row-gap:2pt;min-width:0;}
.engcalc-responsive .engcalc-term{display:inline-block;white-space:nowrap;}
.engcalc-responsive .engcalc-single{display:inline-block;white-space:nowrap;}
</style>
""".strip()


def _math_html(latex: str, css_class: str) -> str:
    return f'<span class="{css_class}">${escape(latex)}$</span>'


def _responsive_additive_terms(
    expression: sp.Expr,
    substitutions: dict[str, object] | None = None,
) -> str:
    expression = sp.sympify(expression)
    terms = expression.as_ordered_terms() if expression.is_Add else [expression]
    rendered: list[str] = []

    for index, term in enumerate(terms):
        negative = term.could_extract_minus_sign()
        unsigned_term = -term if negative else term
        if substitutions is None:
            body = _latex(unsigned_term)
        else:
            body = _substitution_latex(unsigned_term, substitutions)

        if index == 0:
            prefix = "- " if negative else ""
        else:
            prefix = "- " if negative else "+ "
        rendered.append(_math_html(prefix + body, "engcalc-term"))

    return '<span class="engcalc-terms">' + "".join(rendered) + "</span>"


def _responsive_single(latex: str) -> str:
    return _math_html(latex, "engcalc-single")


def _responsive_stage(
    lhs_latex: str | None,
    equals: bool,
    rhs_html: str,
    stage: str,
) -> str:
    lhs = _responsive_single(lhs_latex) if lhs_latex else ""
    eq = _responsive_single("=") if equals else ""
    return (
        f'<div class="engcalc-stage" data-stage="{stage}">'
        f'<span class="engcalc-lhs">{lhs}</span>'
        f'<span class="engcalc-eq">{eq}</span>'
        f'<span class="engcalc-rhs">{rhs_html}</span>'
        "</div>"
    )


def _responsive_numeric_stages(result: NumericEvaluationResult) -> list[str]:
    lhs = _display_lhs(result)
    formula = _responsive_additive_terms(result.symbolic_expression)
    substitution = _responsive_additive_terms(
        result.symbolic_expression,
        result.substitutions,
    )
    final = _responsive_single(_quantity_latex(result.quantity))

    if lhs is not None:
        return [
            _responsive_stage(lhs, True, formula, "formula"),
            _responsive_stage(None, True, substitution, "substitution"),
            _responsive_stage(None, True, final, "result"),
        ]

    return [
        _responsive_stage(_latex(result.symbolic_expression), True, substitution, "substitution"),
        _responsive_stage(None, True, final, "result"),
    ]


def _responsive_partial_stages(result: PartialNumericEvaluationResult) -> list[str]:
    lhs = _display_lhs(result)
    formula = _responsive_additive_terms(result.symbolic_expression)
    substitution = _responsive_additive_terms(
        result.symbolic_expression,
        result.substitutions,
    )
    evaluated_latex = None
    if len(result.unresolved_symbols) == 1:
        evaluated_latex = _partial_polynomial_latex(
            result.evaluated_terms,
            result.unresolved_symbols[0],
        )

    if lhs is not None:
        stages = [
            _responsive_stage(lhs, True, formula, "formula"),
            _responsive_stage(None, True, substitution, "substitution"),
        ]
    else:
        stages = [
            _responsive_stage(_latex(result.symbolic_expression), True, substitution, "substitution")
        ]

    if evaluated_latex is not None:
        stages.append(
            _responsive_stage(None, True, _responsive_single(evaluated_latex), "result")
        )
    return stages


def _responsive_standard_stage(result: CalculationResult) -> str:
    rendered = render_result(result)
    if " = " in rendered:
        left, right = rendered.split(" = ", 1)
        return _responsive_stage(left, True, _responsive_single(right), "standard")
    return _responsive_stage(rendered, False, "", "standard")


def render_responsive_results(results: list[CalculationResult]) -> str:
    """Render numeric groups as responsive HTML whose terms wrap at real pane width."""
    if not results:
        return ""

    calculations: list[str] = []
    for index, result in enumerate(results):
        if isinstance(result, NumericEvaluationResult):
            stages = _responsive_numeric_stages(result)
        elif isinstance(result, PartialNumericEvaluationResult):
            stages = _responsive_partial_stages(result)
        else:
            stages = [_responsive_standard_stage(result)]

        margin = "0" if index == 0 else ("8pt" if result.statement.blank_before else "4pt")
        calculations.append(
            f'<div class="engcalc-calculation" style="margin-top:{margin}">'
            + "".join(stages)
            + "</div>"
        )

    return _RESPONSIVE_STYLE + '<div class="engcalc-responsive">' + "".join(calculations) + "</div>"


def render_result(result: CalculationResult) -> str:
    if isinstance(result, NumericAssignmentResult):
        lhs = _render_lhs(result.statement.target, None)
        return rf"{lhs} = {_quantity_latex(result.quantity)}"

    if isinstance(result, PartialNumericEvaluationResult):
        formula_latex = _latex(result.symbolic_expression)
        substituted_latex = _substitution_latex(
            result.symbolic_expression,
            result.substitutions,
        )
        evaluated_latex = None
        if len(result.unresolved_symbols) == 1:
            evaluated_latex = _partial_polynomial_latex(
                result.evaluated_terms,
                result.unresolved_symbols[0],
            )

        chain = [formula_latex, substituted_latex]
        if evaluated_latex is not None:
            chain.append(evaluated_latex)
        right = " = ".join(chain)

        if result.display_name is not None:
            if result.display_argument is None:
                lhs = _render_lhs(result.display_name, None)
            else:
                lhs = _render_function_call_lhs(
                    result.display_name,
                    result.display_argument,
                )
            return rf"{lhs} = {right}"
        return right

    if isinstance(result, NumericEvaluationResult):
        formula_latex = _latex(result.symbolic_expression)
        substituted_latex = _substitution_latex(
            result.symbolic_expression,
            result.substitutions,
        )
        final_latex = _quantity_latex(result.quantity)
        if result.display_name is not None:
            if result.display_argument is None:
                lhs = _render_lhs(result.display_name, None)
            else:
                lhs = _render_function_call_lhs(
                    result.display_name,
                    result.display_argument,
                )
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
