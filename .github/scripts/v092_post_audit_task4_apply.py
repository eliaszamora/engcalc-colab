from __future__ import annotations

from pathlib import Path


PATH = Path("src/engcalc_colab/characteristics/extrema.py")

HELPER = '''\n\ndef _simplify_decidable_abs(\n    expression: sp.Expr,\n    context,\n    *,\n    overrides: dict[str, Any] | None,\n) -> sp.Expr:\n    simplified = sp.simplify(sp.sympify(expression))\n    replacements: dict[sp.Expr, sp.Expr] = {}\n    for absolute in simplified.atoms(sp.Abs):\n        argument = sp.sympify(absolute.args[0])\n        fixed_overrides = context.unit_literal_overrides(argument, overrides)\n        try:\n            _, quantity = context.evaluate_symbolic(\n                argument,\n                overrides=fixed_overrides,\n            )\n            magnitude = float(quantity.magnitude)\n        except (EngEvaluationError, TypeError, ValueError, OverflowError):\n            continue\n        if not math.isfinite(magnitude):\n            continue\n        if magnitude > 0.0:\n            replacements[absolute] = argument\n        elif magnitude < 0.0:\n            replacements[absolute] = -argument\n        else:\n            replacements[absolute] = sp.Integer(0)\n    if replacements:\n        simplified = simplified.xreplace(replacements)\n    return sp.simplify(simplified)\n'''


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    original = text

    if "def _simplify_decidable_abs(" not in text:
        anchor = "\ndef _extrema_quantity_is_finite(quantity) -> bool:\n"
        if anchor not in text:
            raise RuntimeError("Task 4 helper anchor not found")
        text = text.replace(anchor, HELPER + anchor, 1)

    candidate_old = "    symbolic_value = sp.simplify(expression.subs(variable, candidate))\n"
    candidate_new = (
        "    symbolic_value = _simplify_decidable_abs(\n"
        "        expression.subs(variable, candidate),\n"
        "        context,\n"
        "        overrides=fixed_overrides,\n"
        "    )\n"
    )
    if candidate_old in text:
        text = text.replace(candidate_old, candidate_new, 1)

    interval_old = "        value_symbolic=expression,\n"
    interval_new = (
        "        value_symbolic=_simplify_decidable_abs(\n"
        "            expression, context, overrides=overrides\n"
        "        ),\n"
    )
    if text.count(interval_old) >= 1:
        text = text.replace(interval_old, interval_new, 1)

    piecewise_interval_old = "        value_symbolic=expression,\n"
    piecewise_interval_new = interval_new
    if piecewise_interval_old in text:
        text = text.replace(piecewise_interval_old, piecewise_interval_new, 1)

    one_sided_old = "        value_symbolic=sp.simplify(value_symbolic),\n"
    one_sided_new = (
        "        value_symbolic=_simplify_decidable_abs(\n"
        "            value_symbolic, context, overrides=overrides\n"
        "        ),\n"
    )
    if one_sided_old in text:
        text = text.replace(one_sided_old, one_sided_new, 1)

    if text == original:
        print("TASK4_CHANGED=none")
        return

    PATH.write_text(text, encoding="utf-8")
    print("TASK4_CHANGED=extrema.py")


if __name__ == "__main__":
    main()
