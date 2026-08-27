from __future__ import annotations

import sympy as sp

from .models import EvaluationResult


def render_result(result: EvaluationResult) -> str:
    statement = result.statement
    lhs = _render_lhs(statement.target, statement.parameter)
    value_latex = sp.latex(result.value)

    if lhs is None:
        if result.display_input is not None:
            return rf"{sp.latex(result.display_input)} = {value_latex}"
        return value_latex

    if result.display_input is not None:
        input_latex = sp.latex(result.display_input)
        if sp.sstr(result.display_input) != sp.sstr(result.value):
            return rf"{lhs} = {input_latex} = {value_latex}"
    return rf"{lhs} = {value_latex}"


def _render_lhs(target: str | None, parameter: str | None) -> str | None:
    if target is None:
        return None
    target_latex = sp.latex(sp.Symbol(target))
    if parameter is None:
        return target_latex
    parameter_latex = sp.latex(sp.Symbol(parameter))
    return rf"{target_latex}\left({parameter_latex}\right)"
