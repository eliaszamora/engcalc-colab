from pathlib import Path

path = Path("src/engcalc_colab/renderer.py")
text = path.read_text()

if text.count("result.display_argument") != 6:
    raise RuntimeError(
        f"expected 6 singular display-argument references, found {text.count('result.display_argument')}"
    )
text = text.replace("result.display_argument", "result.display_arguments")

if text.count("statement.parameter") != 3:
    raise RuntimeError(
        f"expected 3 singular statement-parameter references, found {text.count('statement.parameter')}"
    )
text = text.replace("statement.parameter", "statement.parameters")

helper_start = text.index("def _render_function_call_lhs")
new_helpers = '''def _render_function_call_lhs(name: str, arguments: tuple) -> str:
    if not isinstance(arguments, tuple):
        arguments = (arguments,)
    name_latex = _latex(sp.Symbol(name))
    argument_latex = ", ".join(_latex(argument) for argument in arguments)
    return rf"{name_latex}\\left({argument_latex}\\right)"


def _render_lhs(
    target: str | None,
    parameters: tuple[str, ...] | str | None,
) -> str | None:
    if target is None:
        return None
    if target.startswith("Sigma_") and len(target) > len("Sigma_"):
        quantity = target[len("Sigma_"):]
        target_latex = rf"\\Sigma {_latex(sp.Symbol(quantity))}"
    else:
        target_latex = _latex(sp.Symbol(target))
    if parameters is None:
        return target_latex
    if isinstance(parameters, str):
        parameters = (parameters,)
    parameter_latex = ", ".join(
        _latex(sp.Symbol(parameter)) for parameter in parameters
    )
    return rf"{target_latex}\\left({parameter_latex}\\right)"
'''
text = text[:helper_start] + new_helpers

path.write_text(text)
