from __future__ import annotations

import ast
import keyword
import re

from .errors import EngSyntaxError
from .matrix_syntax import consume_matrix_statement, rewrite_matrix_literals
from .models import ParsedHeading, ParsedNarrative, ParsedNumericAssignment, ParsedStatement

_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name,
    ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
    ast.UAdd, ast.USub, ast.Load,
)
_SWEEP_VALUE_NODES = (
    ast.BinOp, ast.UnaryOp, ast.Name, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
    ast.UAdd, ast.USub, ast.Load,
)
_DISPLAY_SWEEP_CALLS = {"plot", "envelope"}
_DISPLAY_TEXT_OPTIONS = {"title", "xlabel", "ylabel"}
_CHARACTERISTIC_CALLS = {"roots", "extrema", "intersections"}
_SCALAR_CALLS = {
    "sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "exp", "log"
}
_ALLOWED_CALLS = {
    # ``integrate`` is canonical - the name every mathematical Python user knows -
    # and ``integral`` is a permanent alias, kept because existing memorias and the
    # documented worked examples use it.
    "integrate", "integral", "diff", "solve", "simplify", "expand", "factor",
    "subs", "eq", "sum", "numeric", "result", "plot", "envelope", "table", "abs",
    "piecewise", "identity", "zeros", "diag", "transpose", "det", "inv", "trace", "size",
    "rank", "rref", "norm", "eigenvals", "eigenvects",
} | _SCALAR_CALLS | _CHARACTERISTIC_CALLS
_RESERVED = _ALLOWED_CALLS | {"pi", "True", "False", "None"}
_IDENTIFIER = re.compile(r"^[A-Za-z_]\w*$")
_FUNCTION_TARGET_HEAD = re.compile(r"^([A-Za-z_]\w*)\s*\((.*)\)$")
_HEADING = re.compile(r"^(#{2,3})\s+(.+)$")
_RESULT_CALL = re.compile(r"\bresult\s*(?=\()")
_TABLE_COLLECTION_NODES = (
    ast.ListComp,
    ast.Set,
    ast.SetComp,
    ast.Dict,
    ast.DictComp,
    ast.GeneratorExp,
    ast.Tuple,
)
_PIECEWISE_COMPARATORS = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)


def normalize_expression(text: str) -> str:
    text = text.replace("^", "**")
    text = _RESULT_CALL.sub("numeric", text)
    return _rewrite_solve_equality(text)


def _normalize_narrative_paragraphs(content_lines: list[str]) -> tuple[str, ...]:
    paragraphs: list[str] = []
    current: list[str] = []

    for raw_line in content_lines:
        text = raw_line.strip()
        if not text:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(text)

    if current:
        paragraphs.append(" ".join(current))
    return tuple(paragraphs)


def _parse_narrative_block(
    lines: list[str],
    start_index: int,
    blank_before: bool,
) -> tuple[ParsedNarrative, int]:
    start_line = start_index + 1
    opening = lines[start_index].strip()
    remainder = opening[3:]
    content_lines: list[str] = []

    if '"""' in remainder:
        content, trailing = remainder.split('"""', 1)
        if trailing.strip():
            raise EngSyntaxError(
                f"line {start_line}: unexpected content after narrative block"
            )
        content_lines.append(content)
        paragraphs = _normalize_narrative_paragraphs(content_lines)
        if not paragraphs:
            raise EngSyntaxError(
                f"line {start_line}: narrative block cannot be empty"
            )
        return (
            ParsedNarrative(
                line_no=start_line,
                paragraphs=paragraphs,
                blank_before=blank_before,
            ),
            start_index + 1,
        )

    content_lines.append(remainder)
    index = start_index + 1
    while index < len(lines):
        raw_line = lines[index]
        if '"""' in raw_line:
            content, trailing = raw_line.split('"""', 1)
            if trailing.strip():
                raise EngSyntaxError(
                    f"line {index + 1}: unexpected content after narrative block"
                )
            content_lines.append(content)
            paragraphs = _normalize_narrative_paragraphs(content_lines)
            if not paragraphs:
                raise EngSyntaxError(
                    f"line {start_line}: narrative block cannot be empty"
                )
            return (
                ParsedNarrative(
                    line_no=start_line,
                    paragraphs=paragraphs,
                    blank_before=blank_before,
                ),
                index + 1,
            )
        content_lines.append(raw_line)
        index += 1

    raise EngSyntaxError(f"line {start_line}: unterminated narrative block")


def parse_cell(
    cell: str,
) -> list[ParsedStatement | ParsedNumericAssignment | ParsedHeading | ParsedNarrative]:
    statements: list[
        ParsedStatement | ParsedNumericAssignment | ParsedHeading | ParsedNarrative
    ] = []
    pending_blank = False
    lines = cell.splitlines()
    index = 0

    while index < len(lines):
        line_no = index + 1
        raw_line = lines[index]
        source = raw_line.strip()
        if not source:
            if statements and not isinstance(statements[-1], ParsedHeading):
                pending_blank = True
            index += 1
            continue
        if source.startswith('"""'):
            narrative, index = _parse_narrative_block(
                lines,
                index,
                pending_blank,
            )
            statements.append(narrative)
            pending_blank = False
            continue
        heading_match = _HEADING.fullmatch(source)
        if heading_match:
            marks, text = heading_match.groups()
            statements.append(ParsedHeading(
                line_no=line_no,
                text=text.strip(),
                level=len(marks),
                blank_before=pending_blank,
            ))
            pending_blank = False
            index += 1
            continue
        if source.startswith("#"):
            index += 1
            continue
        try:
            statement_source, next_index = consume_matrix_statement(lines, index)
            source = statement_source.strip()
            numeric_assignment = _split_top_level_numeric_assignment(source)
            if numeric_assignment is not None:
                numeric_lhs, numeric_rhs = numeric_assignment
                target = numeric_lhs.strip()
                if not _IDENTIFIER.fullmatch(target):
                    raise EngSyntaxError(
                        f"line {line_no}: invalid numeric assignment target '{target}'"
                    )
                _validate_target(target, line_no)
                normalized = normalize_expression(numeric_rhs.strip())
                try:
                    expression = ast.parse(normalized, mode="eval")
                except SyntaxError as exc:
                    raise EngSyntaxError(f"line {line_no}: invalid syntax") from exc
                _validate_ast(expression, line_no)
                _validate_characteristic_statement_context(
                    expression,
                    target,
                    line_no,
                )
                statements.append(ParsedNumericAssignment(
                    line_no=line_no,
                    source=source,
                    target=target,
                    expression=expression,
                    blank_before=pending_blank,
                ))
                pending_blank = False
                index = next_index
                continue

            lhs, rhs = _split_top_level_assignment(source)
            target: str | None = None
            parameters: tuple[str, ...] | None = None
            if lhs is not None:
                function_target = _parse_function_target(lhs.strip(), line_no)
                if function_target is not None:
                    target, parameters = function_target
                else:
                    target = lhs.strip()
                    if not _IDENTIFIER.fullmatch(target):
                        raise EngSyntaxError(
                            f"line {line_no}: invalid assignment target '{target}'"
                        )
                    _validate_target(target, line_no)
            else:
                rhs = source

            normalized = normalize_expression(rhs.strip())
            rewritten, matrix_literals = rewrite_matrix_literals(normalized, line_no)
            try:
                expression = ast.parse(rewritten, mode="eval")
            except SyntaxError as exc:
                raise EngSyntaxError(f"line {line_no}: invalid syntax") from exc
            _validate_ast(expression, line_no, piecewise_parameters=parameters)
            _validate_matrix_literal_bindings(
                matrix_literals,
                line_no,
                piecewise_parameters=parameters,
            )
            _validate_characteristic_statement_context(
                expression,
                target,
                line_no,
                matrix_literals=matrix_literals,
            )
            display_options = _extract_display_options(expression)
            statements.append(ParsedStatement(
                line_no=line_no,
                source=source,
                target=target,
                parameters=parameters,
                expression=expression,
                blank_before=pending_blank,
                display_options=display_options,
                matrix_literals=matrix_literals,
            ))
            pending_blank = False
            index = next_index
        except EngSyntaxError as exc:
            message = str(exc)
            if message.startswith("line "):
                raise
            raise EngSyntaxError(f"line {line_no}: {message}") from None
        except Exception as exc:
            raise EngSyntaxError(f"line {line_no}: invalid syntax") from exc
    return statements


def _parse_function_target(
    text: str,
    line_no: int,
) -> tuple[str, tuple[str, ...]] | None:
    match = _FUNCTION_TARGET_HEAD.fullmatch(text.strip())
    if match is None:
        return None

    target, raw_parameters = match.groups()
    _validate_target(target, line_no)
    if not raw_parameters.strip():
        raise EngSyntaxError(
            f"line {line_no}: user functions require at least one parameter"
        )

    parameters: list[str] = []
    for raw_parameter in raw_parameters.split(","):
        parameter = raw_parameter.strip()
        if not _IDENTIFIER.fullmatch(parameter):
            raise EngSyntaxError(
                f"line {line_no}: invalid function parameter '{parameter}'"
            )
        if keyword.iskeyword(parameter) or parameter in _RESERVED:
            raise EngSyntaxError(
                f"line {line_no}: reserved function parameter '{parameter}'"
            )
        if parameter in parameters:
            raise EngSyntaxError(
                f"line {line_no}: duplicate function parameter '{parameter}'"
            )
        parameters.append(parameter)

    return target, tuple(parameters)


def _validate_target(name: str, line_no: int) -> None:
    if keyword.iskeyword(name) or name in _RESERVED:
        raise EngSyntaxError(f"line {line_no}: reserved identifier '{name}'")


def _validate_ast(
    tree: ast.AST,
    line_no: int,
    *,
    piecewise_parameters: tuple[str, ...] | None = None,
) -> None:
    _validate_normal_node(
        tree,
        line_no,
        piecewise_parameters=piecewise_parameters,
    )


def _validate_matrix_literal_bindings(
    bindings,
    line_no: int,
    *,
    piecewise_parameters: tuple[str, ...] | None = None,
) -> None:
    for binding in bindings:
        for row in binding.literal.rows:
            for expression in row:
                _validate_normal_node(
                    expression,
                    line_no,
                    piecewise_parameters=piecewise_parameters,
                )


def _validate_normal_node(
    node: ast.AST,
    line_no: int,
    *,
    piecewise_parameters: tuple[str, ...] | None = None,
) -> None:
    if isinstance(node, ast.List):
        if not node.elts:
            raise EngSyntaxError(f"line {line_no}: matrix literal cannot be empty")
        for element in node.elts:
            if isinstance(element, ast.List):
                raise EngSyntaxError(
                    f"line {line_no}: nested matrix literals are unsupported"
                )
            _validate_normal_node(
                element,
                line_no,
                piecewise_parameters=piecewise_parameters,
            )
        return
    if isinstance(node, ast.Subscript):
        _validate_normal_node(
            node.value,
            line_no,
            piecewise_parameters=piecewise_parameters,
        )
        index_node = node.slice
        if isinstance(index_node, ast.Slice) or any(
            isinstance(child, ast.Slice) for child in ast.walk(index_node)
        ):
            raise EngSyntaxError(f"line {line_no}: matrix slicing is unsupported")
        if isinstance(index_node, ast.Tuple):
            for element in index_node.elts:
                _validate_normal_node(
                    element,
                    line_no,
                    piecewise_parameters=piecewise_parameters,
                )
        else:
            _validate_normal_node(
                index_node,
                line_no,
                piecewise_parameters=piecewise_parameters,
            )
        return
    if isinstance(node, ast.keyword):
        raise EngSyntaxError(f"line {line_no}: keyword arguments are unsupported")
    if not isinstance(node, _ALLOWED_NODES):
        raise EngSyntaxError(
            f"line {line_no}: unsupported syntax '{type(node).__name__}'"
        )

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise EngSyntaxError(
                f"line {line_no}: unsupported syntax '{type(node.func).__name__}'"
            )
        if node.func.id.startswith("__"):
            raise EngSyntaxError(
                f"line {line_no}: unsupported function '{node.func.id}'"
            )

        if node.func.id in _CHARACTERISTIC_CALLS:
            _validate_characteristic_call(
                node,
                line_no,
                piecewise_parameters=piecewise_parameters,
            )
            return

        if node.func.id == "piecewise":
            _validate_piecewise_call(
                node,
                line_no,
                piecewise_parameters=piecewise_parameters,
            )
            return

        if node.func.id == "table":
            _validate_table_call(node, line_no)
            return

        for arg in node.args:
            _validate_normal_node(
                arg,
                line_no,
                piecewise_parameters=piecewise_parameters,
            )

        if node.keywords:
            if node.func.id not in _DISPLAY_SWEEP_CALLS:
                raise EngSyntaxError(
                    f"line {line_no}: keyword arguments are unsupported"
                )
            _validate_display_sweep_keywords(node, line_no)
        return

    for child in ast.iter_child_nodes(node):
        _validate_normal_node(
            child,
            line_no,
            piecewise_parameters=piecewise_parameters,
        )



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


def _validate_piecewise_call(
    node: ast.Call,
    line_no: int,
    *,
    piecewise_parameters: tuple[str, ...] | None,
) -> None:
    if node.keywords:
        raise EngSyntaxError(f"line {line_no}: keyword arguments are unsupported")
    if len(node.args) < 3 or len(node.args) % 2 == 0:
        raise EngSyntaxError(
            f"line {line_no}: piecewise expects value/condition pairs and a default"
        )

    branch_values = node.args[:-1:2]
    conditions = node.args[1:-1:2]
    default_value = node.args[-1]

    for value in (*branch_values, default_value):
        _validate_normal_node(
            value,
            line_no,
            piecewise_parameters=piecewise_parameters,
        )

    candidate_sets = [
        _piecewise_condition_candidates(
            condition,
            line_no,
            piecewise_parameters=piecewise_parameters,
        )
        for condition in conditions
    ]
    common_candidates = set.intersection(*candidate_sets)
    if not common_candidates:
        raise EngSyntaxError(
            f"line {line_no}: piecewise conditions must use one interval variable"
        )
    if len(common_candidates) > 1:
        raise EngSyntaxError(
            f"line {line_no}: ambiguous piecewise interval variable"
        )


def _piecewise_condition_candidates(
    node: ast.AST,
    line_no: int,
    *,
    piecewise_parameters: tuple[str, ...] | None,
) -> set[str]:
    if not isinstance(node, ast.Compare):
        raise EngSyntaxError(
            f"line {line_no}: piecewise condition must be one direct comparison"
        )
    if len(node.ops) != 1 or len(node.comparators) != 1:
        raise EngSyntaxError(
            f"line {line_no}: chained piecewise comparisons are unsupported"
        )
    if not isinstance(node.ops[0], _PIECEWISE_COMPARATORS):
        raise EngSyntaxError(
            f"line {line_no}: unsupported piecewise comparator"
        )

    left = node.left
    right = node.comparators[0]
    candidates: set[str] = set()
    if isinstance(left, ast.Name) and not _node_contains_name(right, left.id):
        candidates.add(left.id)
    if isinstance(right, ast.Name) and not _node_contains_name(left, right.id):
        candidates.add(right.id)

    if piecewise_parameters is not None:
        candidates.intersection_update(piecewise_parameters)

    if not candidates:
        raise EngSyntaxError(
            f"line {line_no}: piecewise must compare an interval variable directly "
            "with a breakpoint expression"
        )

    for child in (left, right):
        if isinstance(child, ast.Name) and child.id in candidates:
            continue
        _validate_normal_node(
            child,
            line_no,
            piecewise_parameters=piecewise_parameters,
        )
    return candidates


def _node_contains_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(child, ast.Name) and child.id == name
        for child in ast.walk(node)
    )


def _validate_table_call(node: ast.Call, line_no: int) -> None:
    if node.keywords:
        raise EngSyntaxError(f"line {line_no}: keyword arguments are unsupported")

    args = node.args
    for arg in args:
        if isinstance(arg, _TABLE_COLLECTION_NODES):
            raise EngSyntaxError(
                f"line {line_no}: unsupported table point syntax "
                f"'{type(arg).__name__}'"
            )

    point_list: ast.List | None = None
    unit_node: ast.AST | None = None

    if len(args) >= 3 and isinstance(args[-1], ast.List):
        response_nodes = args[:-2]
        variable_node = args[-2]
        point_list = args[-1]
        tail_nodes: tuple[ast.AST, ...] = ()
    elif len(args) >= 4 and isinstance(args[-2], ast.List):
        response_nodes = args[:-3]
        variable_node = args[-3]
        point_list = args[-2]
        unit_node = args[-1]
        tail_nodes = ()
    else:
        if len(args) == 4:
            raise EngSyntaxError(
                f"line {line_no}: table requires at least one response expression"
            )
        if len(args) < 5:
            raise EngSyntaxError(f"line {line_no}: unsupported table call shape")
        response_nodes = args[:-4]
        variable_node = args[-4]
        tail_nodes = tuple(args[-3:])

    if not response_nodes:
        raise EngSyntaxError(
            f"line {line_no}: table requires at least one response expression"
        )
    if not isinstance(variable_node, ast.Name):
        raise EngSyntaxError(
            f"line {line_no}: table variable must be a symbolic identifier"
        )
    if keyword.iskeyword(variable_node.id) or variable_node.id in _RESERVED:
        raise EngSyntaxError(
            f"line {line_no}: table variable must be a symbolic identifier"
        )

    for response_node in response_nodes:
        _validate_normal_node(response_node, line_no)

    if point_list is not None:
        _validate_table_point_list(point_list, line_no)
        if unit_node is not None:
            _validate_normal_node(unit_node, line_no)
        return

    for tail_node in tail_nodes:
        _validate_normal_node(tail_node, line_no)


def _validate_table_point_list(node: ast.List, line_no: int) -> None:
    if not node.elts:
        raise EngSyntaxError(f"line {line_no}: table point list cannot be empty")
    for element in node.elts:
        _validate_table_point_value(element, line_no)


def _validate_table_point_value(node: ast.AST, line_no: int) -> None:
    if not isinstance(node, _SWEEP_VALUE_NODES):
        raise EngSyntaxError(
            f"line {line_no}: unsupported table point syntax "
            f"'{type(node).__name__}'"
        )
    for child in ast.iter_child_nodes(node):
        _validate_table_point_value(child, line_no)


def _validate_display_sweep_keywords(node: ast.Call, line_no: int) -> None:
    call_name = node.func.id
    sweep_keywords: list[ast.keyword] = []

    for keyword_node in node.keywords:
        if keyword_node.arg is None:
            raise EngSyntaxError(
                f"line {line_no}: {call_name} does not support keyword unpacking"
            )

        if keyword_node.arg in _DISPLAY_TEXT_OPTIONS:
            value = keyword_node.value
            if (
                not isinstance(value, ast.Constant)
                or not isinstance(value.value, str)
                or not value.value.strip()
            ):
                raise EngSyntaxError(
                    f"line {line_no}: {call_name} {keyword_node.arg} must be a non-empty string"
                )
            continue

        sweep_keywords.append(keyword_node)

    if len(sweep_keywords) > 1:
        raise EngSyntaxError(
            f"line {line_no}: {call_name} accepts at most one sweep parameter"
        )
    if not sweep_keywords:
        return

    keyword_node = sweep_keywords[0]
    if (
        not _IDENTIFIER.fullmatch(keyword_node.arg)
        or keyword.iskeyword(keyword_node.arg)
        or keyword_node.arg in _RESERVED
    ):
        raise EngSyntaxError(
            f"line {line_no}: invalid {call_name} sweep parameter '{keyword_node.arg}'"
        )

    sweep_value = keyword_node.value
    if not isinstance(sweep_value, ast.List):
        if isinstance(
            sweep_value,
            (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp),
        ):
            raise EngSyntaxError(
                f"line {line_no}: unsupported {call_name} sweep syntax "
                f"'{type(sweep_value).__name__}'"
            )
        raise EngSyntaxError(
            f"line {line_no}: {call_name} sweep values must be a list"
        )
    if not sweep_value.elts:
        raise EngSyntaxError(
            f"line {line_no}: {call_name} sweep list cannot be empty"
        )

    for element in sweep_value.elts:
        _validate_sweep_value(element, line_no, call_name)


def _extract_display_options(expression: ast.Expression) -> tuple[tuple[str, str], ...]:
    node = expression.body
    if (
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id not in _DISPLAY_SWEEP_CALLS
    ):
        return ()

    display_options: list[tuple[str, str]] = []
    evaluation_keywords: list[ast.keyword] = []
    for keyword_node in node.keywords:
        if keyword_node.arg in _DISPLAY_TEXT_OPTIONS:
            display_options.append((keyword_node.arg, keyword_node.value.value.strip()))
        else:
            evaluation_keywords.append(keyword_node)
    node.keywords = evaluation_keywords
    return tuple(display_options)


def _validate_sweep_value(node: ast.AST, line_no: int, call_name: str) -> None:
    if not isinstance(node, _SWEEP_VALUE_NODES):
        raise EngSyntaxError(
            f"line {line_no}: unsupported {call_name} sweep syntax "
            f"'{type(node).__name__}'"
        )
    for child in ast.iter_child_nodes(node):
        _validate_sweep_value(child, line_no, call_name)


def _split_top_level_numeric_assignment(text: str) -> tuple[str, str] | None:
    depth = 0
    positions: list[int] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
            if depth < 0:
                raise EngSyntaxError("unbalanced parentheses")
        elif char == ":" and index + 1 < len(text) and text[index + 1] == "=" and depth == 0:
            positions.append(index)
            index += 1
        index += 1

    if depth != 0:
        raise EngSyntaxError("unbalanced parentheses")
    if not positions:
        return None
    if len(positions) > 1:
        raise EngSyntaxError("multiple top-level ':=' operators are unsupported")

    pos = positions[0]
    lhs, rhs = text[:pos].strip(), text[pos + 2:].strip()
    if not lhs or not rhs:
        raise EngSyntaxError("malformed numeric assignment")
    return lhs, rhs


def _split_top_level_assignment(text: str) -> tuple[str | None, str]:
    depth = 0
    eq_positions: list[int] = []
    for index, char in enumerate(text):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
            if depth < 0:
                raise EngSyntaxError("unbalanced parentheses")
        elif char == "=" and depth == 0:
            eq_positions.append(index)
    if depth != 0:
        raise EngSyntaxError("unbalanced parentheses")
    if not eq_positions:
        return None, text
    if len(eq_positions) > 1:
        raise EngSyntaxError("multiple top-level '=' operators are unsupported")
    pos = eq_positions[0]
    lhs, rhs = text[:pos].strip(), text[pos + 1:].strip()
    if not lhs or not rhs:
        raise EngSyntaxError("malformed assignment")
    return lhs, rhs


def _rewrite_solve_equality(text: str) -> str:
    search_from = 0
    while True:
        start = text.find("solve(", search_from)
        if start < 0:
            return text
        open_pos = start + len("solve")
        close_pos = _matching_paren(text, open_pos)
        inner = text[open_pos + 1:close_pos]
        comma = _find_at_depth(inner, ",", 0)
        if comma is None:
            search_from = close_pos + 1
            continue
        first_arg = inner[:comma]
        equals = _positions_at_depth(first_arg, "=", 0)
        if len(equals) == 1:
            eq_pos = equals[0]
            left = first_arg[:eq_pos].strip()
            right = first_arg[eq_pos + 1:].strip()
            if not left or not right:
                raise EngSyntaxError("malformed equality in solve")
            replacement = f"eq({left}, {right})"
            inner = replacement + inner[comma:]
            text = text[:open_pos + 1] + inner + text[close_pos:]
            search_from = open_pos + 1 + len(inner) + 1
        elif len(equals) > 1:
            raise EngSyntaxError("multiple '=' operators in solve equation")
        else:
            search_from = close_pos + 1


def _matching_paren(text: str, open_pos: int) -> int:
    depth = 0
    for i in range(open_pos, len(text)):
        char = text[i]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return i
    raise EngSyntaxError("unbalanced parentheses")


def _find_at_depth(text: str, needle: str, depth_target: int) -> int | None:
    positions = _positions_at_depth(text, needle, depth_target)
    return positions[0] if positions else None


def _positions_at_depth(text: str, needle: str, depth_target: int) -> list[int]:
    depth = 0
    positions: list[int] = []
    for i, char in enumerate(text):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == needle and depth == depth_target:
            positions.append(i)
    return positions