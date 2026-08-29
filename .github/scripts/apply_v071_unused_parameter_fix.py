from pathlib import Path


path = Path("src/engcalc_colab/engine.py")
text = path.read_text()

old = '''                    if target_unit is not None:
                        suffix = (
                            ": " + ", ".join(unresolved_symbols)
                            if unresolved_symbols
                            else ""
                        )
                        raise EngEvaluationError(
                            "target-unit conversion requires a fully numeric result"
                            + suffix
                        )

                    evaluated_terms = None
                    if len(unresolved_symbols) == 1:
                        evaluated_terms = (
                            self.engine.numeric_context.evaluate_partial_polynomial(
                                symbolic_expression,
                                unresolved_symbols[0],
                                overrides=overrides,
                            )
                        )

                    self.partial_numeric_evaluation = (
                        symbolic_expression,
                        substitutions,
                        unresolved_symbols,
                        evaluated_terms,
                        display_name,
                        display_arguments,
                    )
                    return symbolic_expression

                overrides = dict(zip(function.parameters, argument_values))
'''

new = '''                    if unresolved_symbols:
                        if target_unit is not None:
                            suffix = ": " + ", ".join(unresolved_symbols)
                            raise EngEvaluationError(
                                "target-unit conversion requires a fully numeric result"
                                + suffix
                            )

                        evaluated_terms = None
                        if len(unresolved_symbols) == 1:
                            evaluated_terms = (
                                self.engine.numeric_context.evaluate_partial_polynomial(
                                    symbolic_expression,
                                    unresolved_symbols[0],
                                    overrides=overrides,
                                )
                            )

                        self.partial_numeric_evaluation = (
                            symbolic_expression,
                            substitutions,
                            unresolved_symbols,
                            evaluated_terms,
                            display_name,
                            display_arguments,
                        )
                        return symbolic_expression
                else:
                    overrides = dict(zip(function.parameters, argument_values))
'''

if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("unused-parameter numeric corrective anchor not found")

path.write_text(text)
