from __future__ import annotations

import ast

from .errors import EngSyntaxError
from .models import MatrixLiteralBinding, ParsedMatrixLiteral


def consume_matrix_statement(
    lines: list[str],
    start_index: int,
) -> tuple[str, int]:
    """Collect one restricted multiline matrix assignment.

    Ordinary multiline Python/EngCalc calls remain unsupported. Continuation is
    enabled only when an unmatched ``[`` occurs after a top-level symbolic ``=``.
    """
    first = lines[start_index]
    balance = _square_balance(first)
    if balance <= 0 or not _has_symbolic_assignment_before_first_bracket(first):
        return first, start_index + 1

    parts = [first]
    index = start_index + 1
    while balance > 0 and index < len(lines):
        part = lines[index]
        parts.append(part)
        balance += _square_balance(part)
        if balance < 0:
            break
        index += 1

    if balance != 0:
        raise EngSyntaxError(f"line {start_index + 1}: unclosed matrix literal")
    return "\n".join(parts), index


def rewrite_matrix_literals(
    source: str,
    line_no: int,
) -> tuple[str, tuple[MatrixLiteralBinding, ...]]:
    """Rewrite semicolon matrix literals to private placeholders.

    One-row literals use Python's existing ``ast.List`` representation and are
    therefore left in the source. General/column matrices require semicolons and
    are captured as explicit bindings.
    """
    output: list[str] = []
    bindings: list[MatrixLiteralBinding] = []
    index = 0
    quote: str | None = None
    escaped = False

    while index < len(source):
        char = source[index]

        if quote is not None:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue

        if char in {"'", '"'}:
            quote = char
            output.append(char)
            index += 1
            continue

        if char != "[":
            output.append(char)
            index += 1
            continue

        close = _matching_square(source, index)
        if close is None:
            raise EngSyntaxError(f"line {line_no}: unclosed matrix literal")

        body = source[index + 1 : close]
        if not _contains_top_level(body, ";"):
            output.append(source[index : close + 1])
            index = close + 1
            continue

        literal = _parse_semicolon_matrix(body, line_no)
        name = f"__eng_matrix_literal_{len(bindings)}"
        bindings.append(MatrixLiteralBinding(name=name, literal=literal))
        output.append(name)
        index = close + 1

    return "".join(output), tuple(bindings)


def _parse_semicolon_matrix(body: str, line_no: int) -> ParsedMatrixLiteral:
    raw_rows = _split_top_level(body, ";")
    if any(not row.strip() for row in raw_rows):
        raise EngSyntaxError(f"line {line_no}: matrix literal row cannot be empty")

    parsed_rows: list[tuple[ast.Expression, ...]] = []
    width: int | None = None

    for raw_row in raw_rows:
        raw_cells = _split_top_level(raw_row, ",")
        if any(not cell.strip() for cell in raw_cells):
            raise EngSyntaxError(f"line {line_no}: matrix literal cell cannot be empty")
        if width is None:
            width = len(raw_cells)
        elif len(raw_cells) != width:
            raise EngSyntaxError(
                f"line {line_no}: matrix literal rows must have the same number of columns"
            )

        parsed_cells: list[ast.Expression] = []
        for raw_cell in raw_cells:
            try:
                expression = ast.parse(raw_cell.strip(), mode="eval")
            except SyntaxError as exc:
                raise EngSyntaxError(
                    f"line {line_no}: invalid matrix cell syntax"
                ) from exc
            if any(isinstance(node, ast.List) for node in ast.walk(expression)):
                raise EngSyntaxError(
                    f"line {line_no}: nested matrix literals are unsupported"
                )
            parsed_cells.append(expression)
        parsed_rows.append(tuple(parsed_cells))

    return ParsedMatrixLiteral(rows=tuple(parsed_rows))


def _split_top_level(text: str, delimiter: str) -> list[str]:
    parts: list[str] = []
    start = 0
    paren = brace = square = 0
    quote: str | None = None
    escaped = False

    for index, char in enumerate(text):
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in {"'", '"'}:
            quote = char
            continue
        if char == "(":
            paren += 1
            continue
        if char == ")":
            paren -= 1
            continue
        if char == "{":
            brace += 1
            continue
        if char == "}":
            brace -= 1
            continue
        if char == "[":
            square += 1
            continue
        if char == "]":
            square -= 1
            continue
        if char == delimiter and paren == 0 and brace == 0 and square == 0:
            parts.append(text[start:index])
            start = index + 1

    parts.append(text[start:])
    return parts


def _contains_top_level(text: str, delimiter: str) -> bool:
    return len(_split_top_level(text, delimiter)) > 1


def _matching_square(text: str, open_index: int) -> int | None:
    depth = 0
    quote: str | None = None
    escaped = False

    for index in range(open_index, len(text)):
        char = text[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in {"'", '"'}:
            quote = char
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return index
    return None


def _square_balance(text: str) -> int:
    balance = 0
    quote: str | None = None
    escaped = False

    for char in text:
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
        elif char == "[":
            balance += 1
        elif char == "]":
            balance -= 1
    return balance


def _has_symbolic_assignment_before_first_bracket(text: str) -> bool:
    bracket = text.find("[")
    if bracket < 0:
        return False

    prefix = text[:bracket]
    depth = 0
    for index, char in enumerate(prefix):
        if char in "({":
            depth += 1
            continue
        if char in ")}":
            depth -= 1
            continue
        if char != "=" or depth != 0:
            continue

        previous = prefix[index - 1] if index > 0 else ""
        following = prefix[index + 1] if index + 1 < len(prefix) else ""
        if previous in {":", "<", ">", "!", "="} or following == "=":
            continue
        return True
    return False
