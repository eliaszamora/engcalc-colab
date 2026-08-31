from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Task 6 diagnostic corrective anchor not found: {label}")
    return text.replace(old, new, 1)


path = Path("src/engcalc_colab/engine.py")
text = path.read_text()

old = '''        lower_expression = self.visit(lower_node)
        upper_expression = self.visit(upper_node)
        lower_quantity = self._resolve_domain_numeric_value(lower_node)
        upper_quantity = self._resolve_domain_numeric_value(upper_node)
        try:
            domain = normalize_analysis_domain(
                self.engine.numeric_context,
                lower_expression,
                upper_expression,
                lower_quantity=lower_quantity,
                upper_quantity=upper_quantity,
            )
        except EngEvaluationError as exc:
            raise self._operation_specific_characteristic_error(name, exc) from None
'''
new = '''        lower_expression = self.visit(lower_node)
        upper_expression = self.visit(upper_node)
        try:
            try:
                lower_quantity = self._resolve_domain_numeric_value(lower_node)
                upper_quantity = self._resolve_domain_numeric_value(upper_node)
            except EngEvaluationError as exc:
                raise EngEvaluationError(
                    "characteristic domain bound must be numerically resolvable: "
                    + str(exc)
                ) from None
            domain = normalize_analysis_domain(
                self.engine.numeric_context,
                lower_expression,
                upper_expression,
                lower_quantity=lower_quantity,
                upper_quantity=upper_quantity,
            )
        except EngEvaluationError as exc:
            raise self._operation_specific_characteristic_error(name, exc) from None
'''
text = replace_once(text, old, new, "operation-specific characteristic bound diagnostics")
path.write_text(text)

print("Restored operation-specific characteristic bound diagnostics for Task 6.")
