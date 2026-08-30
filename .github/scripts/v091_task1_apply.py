from pathlib import Path


path = Path("src/engcalc_colab/parser.py")
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"expected exactly one parser fragment, found {count}: {old[:80]!r}"
        )
    text = text.replace(old, new, 1)


replace_once(
    '_DISPLAY_SWEEP_CALLS = {"plot", "envelope"}\n'
    '_DISPLAY_TEXT_OPTIONS = {"title", "xlabel", "ylabel"}\n',
    '_DISPLAY_SWEEP_CALLS = {"plot", "envelope"}\n'
    '_DISPLAY_TEXT_OPTIONS = {"title", "xlabel", "ylabel"}\n'
    '_CHARACTERISTIC_CALLS = {"roots", "extrema", "intersections"}\n',
)

replace_once(
    '} | _SCALAR_CALLS\n_RESERVED = _ALLOWED_CALLS | {"pi", "True", "False", "None"}\n',
    '} | _SCALAR_CALLS | _CHARACTERISTIC_CALLS\n'
    '_RESERVED = _ALLOWED_CALLS | {"pi", "True", "False", "None"}\n',
)

replace_once(
    '                _validate_ast(expression, line_no)\n'
    '                statements.append(ParsedNumericAssignment(\n',
    '                _validate_ast(expression, line_no)\n'
    '                _validate_characteristic_statement_context(\n'
    '                    expression,\n'
    '                    target,\n'
    '                    line_no,\n'
    '                )\n'
    '                statements.append(ParsedNumericAssignment(\n',
)

replace_once(
    '            _validate_matrix_literal_bindings(\n'
    '                matrix_literals,\n'
    '                line_no,\n'
    '                piecewise_parameters=parameters,\n'
    '            )\n'
    '            display_options = _extract_display_options(expression)\n',
    '            _validate_matrix_literal_bindings(\n'
    '                matrix_literals,\n'
    '                line_no,\n'
    '                piecewise_parameters=parameters,\n'
    '            )\n'
    '            _validate_characteristic_statement_context(\n'
    '                expression,\n'
    '                target,\n'
    '                line_no,\n'
    '                matrix_literals=matrix_literals,\n'
    '            )\n'
    '            display_options = _extract_display_options(expression)\n',
)

replace_once(
    '        if node.func.id == "piecewise":\n',
    '        if node.func.id in _CHARACTERISTIC_CALLS:\n'
    '            _validate_characteristic_call(\n'
    '                node,\n'
    '                line_no,\n'
    '                piecewise_parameters=piecewise_parameters,\n'
    '            )\n'
    '            return\n\n'
    '        if node.func.id == "piecewise":\n',
)

marker = "\n\ndef _validate_piecewise_call(\n"
if text.count(marker) != 1:
    raise SystemExit("could not locate unique _validate_piecewise_call insertion point")

helpers = '''


def _validate_characteristic_call(
    node: ast.Call,
    line_no: int,
    *,
    piecewise_parameters: tuple[str, ...] | None,
) -> None:
    name = node.func.id
    expected = 5 if name == "intersections" else 4
    if node.keywords:
        raise EngSyntaxError(
            f"line {line_no}: {name} keyword arguments are unsupported"
        )
    if len(node.args) != expected:
        raise EngSyntaxError(
            f"line {line_no}: {name} expects {expected} positional arguments"
        )

    variable_index = 2 if name == "intersections" else 1
    variable_node = node.args[variable_index]
    if (
        not isinstance(variable_node, ast.Name)
        or keyword.iskeyword(variable_node.id)
        or variable_node.id in _RESERVED
    ):
        raise EngSyntaxError(
            f"line {line_no}: {name} variable must be a symbolic identifier"
        )

    for index, argument in enumerate(node.args):
        if index == variable_index:
            continue
        _validate_normal_node(
            argument,
            line_no,
            piecewise_parameters=piecewise_parameters,
        )


def _characteristic_calls(node: ast.AST) -> list[ast.Call]:
    return [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id in _CHARACTERISTIC_CALLS
    ]


def _validate_characteristic_statement_context(
    expression: ast.Expression,
    target: str | None,
    line_no: int,
    *,
    matrix_literals=(),
) -> None:
    expression_calls = _characteristic_calls(expression)
    matrix_calls = [
        call
        for binding in matrix_literals
        for row in binding.literal.rows
        for cell in row
        for call in _characteristic_calls(cell)
    ]
    calls = [*expression_calls, *matrix_calls]
    if not calls:
        return

    root = expression.body
    root_is_characteristic = (
        isinstance(root, ast.Call)
        and isinstance(root.func, ast.Name)
        and root.func.id in _CHARACTERISTIC_CALLS
    )
    if (
        target is not None
        or not root_is_characteristic
        or len(calls) != 1
        or matrix_calls
    ):
        raise EngSyntaxError(
            f"line {line_no}: characteristic analysis must be a standalone statement"
        )
'''

text = text.replace(marker, helpers + marker, 1)
path.write_text(text, encoding="utf-8")
