from pathlib import Path

path = Path('src/engcalc_colab/engine.py')
text = path.read_text()

text = text.replace(
    '                    overrides = {}\n                    bindings = {}\n                    for parameter, argument_expression, argument_value in zip(',
    '                    overrides = {}\n                    bindings = {}\n                    allowed_unresolved = set()\n                    for parameter, argument_expression, argument_value in zip(',
    1,
)

text = text.replace(
    '                        if isinstance(argument_value, sp.Expr):\n                            bindings[self.engine.resolve_symbol(parameter)] = (\n                                sp.sympify(argument_expression)\n                            )',
    '                        if isinstance(argument_value, sp.Expr):\n                            symbolic_argument = sp.sympify(argument_expression)\n                            bindings[self.engine.resolve_symbol(parameter)] = symbolic_argument\n                            allowed_unresolved.update(\n                                symbol.name for symbol in symbolic_argument.free_symbols\n                            )',
    1,
)

text = text.replace(
    '                            allowed_unresolved=None,\n                            overrides=overrides,',
    '                            allowed_unresolved=allowed_unresolved,\n                            overrides=overrides,',
    1,
)

path.write_text(text)
