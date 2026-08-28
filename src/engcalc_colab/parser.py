from __future__ import annotations

import ast
import keyword
import re

from .errors import EngSyntaxError
from .models import ParsedHeading, ParsedNumericAssignment, ParsedStatement

_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name,
    ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
    ast.UAdd, ast.USub, ast.Load, ast.keyword, ast.List,
)
_ALLOWED_CALLS = {
    "integral", "diff", "solve", "simplify", "expand", "factor", "subs", "eq", "sum", "numeric", "plot"
}
_RESERVED = _ALLOWED_CALLS | {"True", "False", "None"}
_IDENTIFIER = re.compile(r"^[A-Za-z_]\w*$")
_FUNCTION_TARGET = re.compile(r"^([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)\s*\)$")
_HEADING = re.compile(r"^(#{2,3})\s+(.+)$")


def normalize_expression(text: str) -> str:
    text = text.replace("^", "**")
    return _rewrite_solve_equality(text)


def parse_cell(cell: str) -> list[ParsedStatement | ParsedNumericAssignment | ParsedHeading]:
    statements: list[ParsedStatement | ParsedNumericAssignment | ParsedHeading] = []
    pending_blank = False

    for line_no, raw_line in enumerate(cell.splitlines(), start=1):
        source = raw_line.strip()
        if not source:
            if statements and not isinstance(statements[-1], ParsedHeading):
                pending_blank = True
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
            continue
        if source.startswith("#"):
            continue
        try:
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
                statements.append(ParsedNumericAssignment(
                    line_no=line_no,
                    source=source,
                    target=target,
                    expression=expression,
                    blank_before=pending_blank,
                ))
                pending_blank = False
                continue

            lhs, rhs = _split_top_level_assignment(source)
            target: str | None = None
            parameter: str | None = None
            if lhs is not None:
                function_match = _FUNCTION_TARGET.fullmatch(lhs.strip())
                if function_match:
                    target, parameter = function_match.groups()
                    _validate_target(target, line_no)
                    if keyword.iskeyword(parameter) or parameter in _RESERVED:
                        raise EngSyntaxError(
                            f"line {line_no}: reserved function parameter '{parameter}'"
                        )
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
            try:
                expression = ast.parse(normalized, mode="eval")
            except SyntaxError as exc:
                raise EngSyntaxError(f"line {line_no}: invalid syntax") from exc
            _validate_ast(expression, line_no)
            statements.append(ParsedStatement(
                line_no=line_no,
                source=source,
                target=target,
                parameter=parameter,
                expression=expression,
                blank_before=pending_blank,
            ))
            pending_blank = False
        except EngSyntaxError as exc:
            message = str(exc)
            if message.startswith("line "):
                raise
            raise EngSyntaxError(f"line {line_no}: {message}") from None
        except Exception as exc:
            raise EngSyntaxError(f"line {line_no}: invalid syntax") from exc
    return statements


def _validate_target(name: str, line_no: int) -> None:
    if keyword.iskeyword(name) or name in _RESERVED:
        raise EngSyntaxError(f"line {line_no}: reserved identifier '{name}'")


def _validate_ast(tree: ast.AST, line_no: int) -> None:
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }

    for node in ast.walk(tree):
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
            if node.func.id != "plot" and node.keywords:
                raise EngSyntaxError(f"line {line_no}: keyword arguments are unsupported")
            if node.func.id == "plot":
                _validate_plot_keywords(node, line_no)

        if isinstance(node, ast.List):
            keyword_node = parents.get(node)
            call = parents.get(keyword_node) if isinstance(keyword_node, ast.keyword) else None
            if not (
                isinstance(keyword_node, ast.keyword)
                and isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == "plot"
                and keyword_node.value is node
            ):
                raise EngSyntaxError(
                    f"line {line_no}: unsupported syntax 'List'"
                )


def _validate_plot_keywords(node: ast.Call, line_no: int) -> None:
    if len(node.keywords) > 1:
        raise EngSyntaxError(
            f"line {line_no}: plot accepts at most one sweep parameter"
        )
    if not node.keywords:
        return

    keyword_node = node.keywords[0]
    if keyword_node.arg is None:
        raise EngSyntaxError(f"line {line_no}: plot does not support **kwargs")
    if keyword_node.arg in _RESERVED or keyword.iskeyword(keyword_node.arg):
        raise EngSyntaxError(
            f"line {line_no}: invalid plot sweep parameter '{keyword_node.arg}'"
        )
    if not isinstance(keyword_node.value, ast.List):
        raise EngSyntaxError(
            f"line {line_no}: plot sweep values must be a list"
        )
    if not keyword_node.value.elts:
        raise EngSyntaxError(
            f"line {line_no}: plot sweep list cannot be empty"
        )


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
