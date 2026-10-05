from __future__ import annotations

import ast

from .errors import EngSyntaxError
from .models import MatrixLiteralBinding, ParsedMatrixLiteral



def mark_typed_decimals(tree: ast.AST, text: str) -> ast.AST:
    """Note on each decimal the figures it was typed with, when a zero ends them.

    `0.90` parses to the float 0.9 and the zero is gone; ACI writes its factors with their
    figures and a memoria is checked against the code. The written form reads `typed` back.
    See `test_a_number_is_written_as_typed`.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            typed = ast.get_source_segment(text, node)
            if typed and "." in typed and "e" not in typed.lower() and typed.endswith("0"):
                node.typed = typed
    return tree

def consume_matrix_statement(
    lines: list[str],
    start_index: int,
) -> tuple[str, int]:
    """Collect one statement written over several lines.

    A matrix literal opened after a top-level symbolic ``=`` continues as it always has,
    its rows on lines of their own. Any other line that leaves a ``(`` or a ``[`` open
    goes on to the next lines until it is closed, and they are read as one line (his ask
    of 2026-10-04: a long `solve` or a formula of many terms was refused "unbalanced
    parentheses", though its parentheses were balanced). A blank line, a narrative or a
    comment ends it: a parenthesis left open by mistake does not swallow the sheet.
    """
    first = lines[start_index]
    balance = _square_balance(first)
    if balance <= 0 or not _has_symbolic_assignment_before_first_bracket(first):
        depth = _bracket_depth(first)
        if depth <= 0:
            return first, start_index + 1
        parts = [without_comment(first).strip()]
        index = start_index + 1
        while depth > 0:
            following = lines[index].strip() if index < len(lines) else ""
            if not following or following.startswith(('"""', "#")):
                raise EngSyntaxError(
                    f"line {start_index + 1}: unbalanced parentheses - one opened on this line is never "
                    "closed"
                )
            following = without_comment(following).strip()
            parts.append(following)
            depth += _bracket_depth(following)
            index += 1
        return " ".join(parts), index

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


def continued_lines(lines: list[str], index: int) -> int:
    """How many lines from `index` one statement takes, as `consume_matrix_statement`
    reads them: 1 for a line that closes what it opens, and 1 too for one never closed
    (the parser then says so). A matrix literal after a top-level `=` is the parser's
    own, its rows on their lines, and is left to it."""
    first = lines[index]
    if _square_balance(first) > 0 and _has_symbolic_assignment_before_first_bracket(first):
        return 1
    depth = _bracket_depth(first)
    count = 1
    while depth > 0:
        following = lines[index + count].strip() if index + count < len(lines) else ""
        if not following or following.startswith(('"""', "#")):
            return 1
        depth += _bracket_depth(without_comment(following))
        count += 1
    return count


def without_comment(text: str) -> str:
    """A line without a `#` comment after it, outside quotes: `y := (x +  # first term`
    joined to the next line swallowed its `1)` (the audit of 0.46.0)."""
    quote: str | None = None
    for index, char in enumerate(text):
        if quote is not None:
            if char == quote:
                quote = None
        elif char == '"' or (char == "'" and not is_transpose_prime(text, index)):
            quote = char
        elif char == "#":
            return text[:index].rstrip()
    return text


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
                expression = mark_typed_decimals(
                    ast.parse(raw_cell.strip(), mode="eval"), raw_cell.strip()
                )
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


def is_transpose_prime(text: str, index: int) -> bool:
    """Whether the `'` at `index` is a transpose, `T'`, `(K d)'`, `d[2]'`, and not the
    start of a quoted text: it follows a name, a closing parenthesis or bracket at once."""
    if text[index] != "'" or index == 0:
        return False
    previous = text[index - 1]
    return previous.isalnum() or previous in "_)]'"


def _bracket_depth(text: str) -> int:
    """Parentheses and brackets a line leaves open, outside quotes."""
    depth = 0
    quote: str | None = None
    for index, char in enumerate(text):
        if quote is not None:
            if char == quote:
                quote = None
            continue
        if char == '"' or (char == "'" and not is_transpose_prime(text, index)):
            quote = char
        elif char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
    return depth


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
        # `:` is not in this set: `D := [0;` runs on like `K = [a, b;`, since a `:=` line
        # holds a matrix too now. `<=`, `>=`, `!=` and `==` are comparisons, not assignments.
        if previous in {"<", ">", "!", "="} or following == "=":
            continue
        return True
    return False
