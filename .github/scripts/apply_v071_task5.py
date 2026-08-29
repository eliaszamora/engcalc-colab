from pathlib import Path

path = Path("src/engcalc_colab/renderer.py")
text = path.read_text()

old = '''def _display_lhs(result: NumericEvaluationResult | PartialNumericEvaluationResult) -> str | None:\n    if result.display_name is None:\n        return None\n    if result.display_argument is None:\n        return _render_lhs(result.display_name, None)\n    return _render_function_call_lhs(result.display_name, result.display_argument)\n'''
new = '''def _display_lhs(result: NumericEvaluationResult | PartialNumericEvaluationResult) -> str | None:\n    if result.display_name is None:\n        return None\n    if result.display_arguments is None:\n        return _render_lhs(result.display_name, None)\n    return _render_function_call_lhs(result.display_name, result.display_arguments)\n'''
if text.count(old) != 1:
    raise RuntimeError("unexpected _display_lhs shape")
text = text.replace(old, new, 1)

old_lhs = "lhs = _render_lhs(statement.target, statement.parameter)"
if text.count(old_lhs) != 3:
    raise RuntimeError(f"expected 3 singular statement LHS uses, found {text.count(old_lhs)}")
text = text.replace(old_lhs, "lhs = _render_lhs(statement.target, statement.parameters)")

old_display = '''        if result.display_name is not None:\n            if result.display_argument is None:\n                lhs = _render_lhs(result.display_name, None)\n            else:\n                lhs = _render_function_call_lhs(result.display_name, result.display_argument)\n            return rf"{lhs} = {right}"\n'''
new_display = '''        if result.display_name is not None:\n            lhs = _display_lhs(result)\n            return rf"{lhs} = {right}"\n'''
if text.count(old_display) != 2:
    raise RuntimeError(f"expected 2 numeric display blocks, found {text.count(old_display)}")
text = text.replace(old_display, new_display)

old_helpers = '''def _render_function_call_lhs(name: str, argument) -> str:\n    name_latex = _latex(sp.Symbol(name))\n    return rf"{name_latex}\\left({_latex(argument)}\\right)"\n\n\ndef _render_lhs(target: str | None, parameter: str | None) -> str | None:\n    if target is None:\n        return None\n    if target.startswith("Sigma_") and len(target) > len("Sigma_"):\n        quantity = target[len("Sigma_"):]\n        target_latex = rf"\\Sigma {_latex(sp.Symbol(quantity))}"\n    else:\n        target_latex = _latex(sp.Symbol(target))\n    if parameter is None:\n        return target_latex\n    parameter_latex = _latex(sp.Symbol(parameter))\n    return rf"{target_latex}\\left({parameter_latex}\\right)"\n'''
new_helpers = '''def _render_function_call_lhs(name: str, arguments: tuple) -> str:\n    if not isinstance(arguments, tuple):\n        arguments = (arguments,)\n    name_latex = _latex(sp.Symbol(name))\n    argument_latex = ", ".join(_latex(argument) for argument in arguments)\n    return rf"{name_latex}\\left({argument_latex}\\right)"\n\n\ndef _render_lhs(\n    target: str | None,\n    parameters: tuple[str, ...] | str | None,\n) -> str | None:\n    if target is None:\n        return None\n    if target.startswith("Sigma_") and len(target) > len("Sigma_"):\n        quantity = target[len("Sigma_"):]\n        target_latex = rf"\\Sigma {_latex(sp.Symbol(quantity))}"\n    else:\n        target_latex = _latex(sp.Symbol(target))\n    if parameters is None:\n        return target_latex\n    if isinstance(parameters, str):\n        parameters = (parameters,)\n    parameter_latex = ", ".join(\n        _latex(sp.Symbol(parameter)) for parameter in parameters\n    )\n    return rf"{target_latex}\\left({parameter_latex}\\right)"\n'''
if text.count(old_helpers) != 1:
    raise RuntimeError("unexpected renderer helper shape")
text = text.replace(old_helpers, new_helpers, 1)

path.write_text(text)
