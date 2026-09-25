"""`% if`: lines of a cell that decide which other lines run.

A line that starts with `%` is control, written as Python: `% if`, `% elif`, `% else`, and
`% end` closes the block. Every other line is the sheet's own. The condition reads the
values the sheet has computed by then, with their units, and only the branch that holds
runs; it opens with a sentence that states the condition in numbers - `Como Vu = 7920.00
kgf > φ_v V_c = 7603.63 kgf:` - because that is what a reviewer checks. Approved on
2026-09-25; see `tests/test_a_sheet_decides_with_if.py`.

The cell's structure is read before anything runs, so a block written wrong refuses the
whole cell, as a line written wrong always has. The lines themselves are parsed a stretch
at a time and evaluated as they come, because a condition may read a value computed two
lines above it.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Iterator

import sympy as sp
from pint.errors import DimensionalityError

from .errors import EngCalcError, EngEvaluationError, EngSyntaxError
from .parser import normalize_expression, parse_cell

_CONTROL = re.compile(r"^%\s*(\w+)\b(.*)$")
_KEYWORDS = ("if", "elif", "else", "end")


@dataclass(frozen=True)
class ConditionNote:
    """The sentence a branch opens with: Markdown, its mathematics between `$`."""

    markdown: str


@dataclass
class _Stretch:
    first_line: int
    lines: list[str] = field(default_factory=list)


@dataclass
class _Branch:
    line_no: int
    condition: str | None  # None for `% else`
    body: list = field(default_factory=list)


@dataclass
class _IfBlock:
    line_no: int
    branches: list[_Branch] = field(default_factory=list)


def _lines(cell: str) -> Iterator[tuple[int, str, bool]]:
    """Each line, numbered, and whether it is control: `%` first, outside `\"\"\"` text."""
    in_text = False
    for index, raw in enumerate(cell.splitlines()):
        text = raw.strip()
        if in_text:
            in_text = '"""' not in text
            yield index + 1, raw, False
            continue
        if text.startswith('"""'):
            # `"""` alone opens a block; `"""One line."""` opens and closes it.
            in_text = '"""' not in text[3:]
            yield index + 1, raw, False
            continue
        yield index + 1, raw, text.startswith("%")


def has_control(cell: str) -> bool:
    return any(control for _line_no, _raw, control in _lines(cell))


def _structure(cell: str) -> list:
    """The cell as stretches of sheet lines and `% if` blocks, nested."""
    root: list = []
    stack: list[tuple[_IfBlock, list]] = []
    body = root

    def stretch(line_no: int) -> _Stretch:
        if body and isinstance(body[-1], _Stretch):
            return body[-1]
        new = _Stretch(first_line=line_no)
        body.append(new)
        return new

    for line_no, raw, control in _lines(cell):
        text = raw.strip()
        if not control:
            current = stretch(line_no)
            # Keep the stretch's lines aligned with the cell's, so a line inside it is
            # numbered as the cell numbers it.
            while current.first_line + len(current.lines) < line_no:
                current.lines.append("")
            current.lines.append(raw)
            continue
        match = _CONTROL.match(text)
        keyword = match.group(1) if match else ""
        rest = match.group(2).strip() if match else ""
        if keyword not in _KEYWORDS:
            raise EngSyntaxError(
                f"line {line_no}: a line that starts with % is % if, % elif, % else "
                "or % end"
            )
        condition = rest[:-1].strip() if rest.endswith(":") else rest
        if keyword == "if":
            if not condition:
                raise EngSyntaxError(f"line {line_no}: % if needs a condition, as in % if Vu > phi*V_c:")
            block = _IfBlock(line_no=line_no, branches=[_Branch(line_no, condition)])
            body.append(block)
            stack.append((block, body))
            body = block.branches[-1].body
        elif keyword in ("elif", "else"):
            if not stack:
                raise EngSyntaxError(f"line {line_no}: % {keyword} with no % if open above it")
            block, _outer = stack[-1]
            if block.branches[-1].condition is None:
                raise EngSyntaxError(f"line {line_no}: % {keyword} after the % else of line {block.branches[-1].line_no}")
            if keyword == "elif" and not condition:
                raise EngSyntaxError(f"line {line_no}: % elif needs a condition")
            block.branches.append(_Branch(line_no, condition if keyword == "elif" else None))
            body = block.branches[-1].body
        else:  # end
            if not stack:
                raise EngSyntaxError(f"line {line_no}: % end with no % if open above it")
            _block, body = stack.pop()
    if stack:
        block, _outer = stack[-1]
        raise EngSyntaxError(f"line {block.line_no}: this % if has no % end")
    return root


def _check_lines(nodes: list) -> None:
    """Every sheet line parsed before any runs, as a cell without `%` lines is."""
    for node in nodes:
        if isinstance(node, _Stretch):
            _parse_stretch(node)
        else:
            for branch in node.branches:
                if branch.condition is not None:
                    _condition_tree(branch.condition, branch.line_no)
                _check_lines(branch.body)


def _parse_stretch(stretch: _Stretch):
    # Empty lines in front number the stretch as the cell does; a leading blank line
    # changes nothing on the page.
    return parse_cell("\n" * (stretch.first_line - 1) + "\n".join(stretch.lines))


def _condition_tree(text: str, line_no: int) -> ast.AST:
    try:
        return ast.parse(normalize_expression(text), mode="eval").body
    except SyntaxError as exc:
        raise EngSyntaxError(f"line {line_no}: the condition of this % line is not one: {text}") from exc


def run(cell: str, engine, settings) -> Iterator:
    """The cell's items in order - parsed statements and ConditionNotes - deciding as it goes.

    `settings` is a function returning the page's settings, read at each use: a `:=` line
    adds the units it writes as the cell runs, and a condition must see them.
    """
    tree = _structure(cell)
    _check_lines(tree)
    yield from _walk(tree, engine, settings)


def _walk(nodes: list, engine, settings) -> Iterator:
    for node in nodes:
        if isinstance(node, _Stretch):
            yield from _parse_stretch(node)
            continue
        held = []
        chosen = None
        for branch in node.branches:
            if branch.condition is None:
                chosen = branch
                break
            tree = _condition_tree(branch.condition, branch.line_no)
            verdict, stated = _decide(tree, branch.line_no, engine, settings)
            if verdict:
                chosen = branch
                break
            held.append((tree, branch.line_no))
        if chosen is None:
            continue
        # Why this branch: the conditions above it that did not hold, then its own.
        said = [_negated(tree, line_no, engine, settings) for tree, line_no in held]
        if chosen.condition is not None:
            said.append(stated)
        yield ConditionNote(markdown=f"Como {' y '.join(said)}:")
        yield from _walk(chosen.body, engine, settings)


# -- deciding, and saying it -------------------------------------------------------------

_OPERATORS = {
    ast.Gt: (">", ">", lambda a, b: a > b),
    ast.GtE: (">=", r"\geq", lambda a, b: a >= b),
    ast.Lt: ("<", "<", lambda a, b: a < b),
    ast.LtE: ("<=", r"\leq", lambda a, b: a <= b),
    ast.Eq: ("==", "=", lambda a, b: a == b),
    ast.NotEq: ("!=", r"\neq", lambda a, b: a != b),
}
_NEGATED = {ast.Gt: ast.LtE, ast.GtE: ast.Lt, ast.Lt: ast.GtE, ast.LtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}


def _decide(tree: ast.AST, line_no: int, engine, settings) -> tuple[bool, str]:
    """Whether the condition holds, and the condition said in numbers."""
    if isinstance(tree, ast.BoolOp):
        parts = []
        joiner = " y " if isinstance(tree.op, ast.And) else " o "
        for value in tree.values:
            verdict, said = _decide(value, line_no, engine, settings)
            parts.append((verdict, said))
            # As Python does: stop at the first that settles it.
            if isinstance(tree.op, ast.And) and not verdict:
                return False, said
            if isinstance(tree.op, ast.Or) and verdict:
                return True, said
        return isinstance(tree.op, ast.And), joiner.join(said for _, said in parts)
    if isinstance(tree, ast.UnaryOp) and isinstance(tree.op, ast.Not):
        verdict, said = _decide(tree.operand, line_no, engine, settings)
        return (not verdict), f"no se cumple {said}"
    if isinstance(tree, ast.Compare):
        return _compare(tree, line_no, engine, settings, tree.ops)
    raise EngEvaluationError(
        f"line {line_no}: a condition compares, as in Vu > phi*V_c; "
        f"{ast.unparse(tree)} is not a comparison"
    )


def _negated(tree: ast.AST, line_no: int, engine, settings) -> str:
    """The condition that did not hold, said as what does: `Vu = ... <= phi_v V_c = ...`."""
    if isinstance(tree, ast.Compare) and len(tree.ops) == 1:
        _verdict, said = _compare(tree, line_no, engine, settings, [_NEGATED[type(tree.ops[0])]()])
        return said
    _verdict, said = _decide(tree, line_no, engine, settings)
    return f"no se cumple {said}"


def _compare(tree: ast.Compare, line_no: int, engine, settings, operators) -> tuple[bool, str]:
    operands = [tree.left, *tree.comparators]
    values = [_value(operand, line_no, engine) for operand in operands]
    verdict = True
    for (left, right), operator in zip(zip(values, values[1:]), tree.ops):
        first, second = left[0].quantity, right[0].quantity
        try:
            holds = _OPERATORS[type(operator)][2](first, second)
        except DimensionalityError as exc:
            raise EngEvaluationError(
                f"line {line_no}: the condition cannot compare {ast.unparse(tree)}: "
                f"{first.units:~P} against {second.units:~P}"
            ) from exc
        verdict = verdict and bool(holds)
    shown = _in_one_unit(operands, values, settings, engine)
    pieces = [
        _said(operand, value, quantity, settings)
        for operand, value, quantity in zip(operands, values, shown)
    ]
    said = pieces[0]
    for operator, piece in zip(operators, pieces[1:]):
        said += f" {_OPERATORS[type(operator)][1]} {piece}"
    return verdict, f"${said}$"


def _value(operand: ast.AST, line_no: int, engine):
    """One side of a comparison, in numbers: the quantity and what the page writes it as."""
    from .models import NumericEvaluationResult  # noqa: PLC0415 - models import nothing back

    text = ast.unparse(operand)
    try:
        (statement,) = parse_cell(f"numeric({text})")
        result = engine.evaluate(statement)
    except EngCalcError as exc:
        raise EngEvaluationError(f"line {line_no}: the condition needs a value for {text}: {exc}") from exc
    if not isinstance(result, NumericEvaluationResult):
        raise EngEvaluationError(f"line {line_no}: the condition needs one value for {text}")
    quantity = result.quantity
    written = None
    try:
        from .engine import _WrittenFormEvaluator  # noqa: PLC0415 - engine imports this module's users

        written = _WrittenFormEvaluator(engine, ()).visit(operand)
    except Exception:  # noqa: BLE001 - the page then writes the number alone
        written = None
    return result, written, getattr(result, "unit_literals", frozenset())


def _in_one_unit(operands, values, settings, engine) -> list:
    """Each side of a comparison as it is written: all in the unit of the first.

    The first side reads as the page reads it - a name in the unit its definition was
    written in, `Vu = 7920.00 kgf` - and the others follow it, so the reviewer compares
    `7920.00 kgf > 7603.63 kgf` at a glance and not kgf against tonf.
    """
    from .renderer import _display_quantity  # noqa: PLC0415 - renderer imports models only

    current = settings() if callable(settings) else settings
    first_operand = operands[0]
    declared = isinstance(first_operand, ast.Name) and first_operand.id in engine.declared_unit_names
    first = _display_quantity(values[0][0].quantity, current, declared=declared)
    shown = [first]
    for result, _written, _units in values[1:]:
        quantity = result.quantity
        if quantity.dimensionality == first.dimensionality:
            shown.append(quantity.to(first.units))
        else:
            shown.append(_display_quantity(quantity, current, declared=False))
    return shown


def _said(operand: ast.AST, value, quantity, settings) -> str:
    """`\\phi_{v} V_{c} = 7603.63\\,kgf`, or the number alone for a number."""
    from .renderer import _latex, _quantity_latex  # noqa: PLC0415 - renderer imports models only

    _result, written, units = value
    current = settings() if callable(settings) else settings
    # The unit is chosen already, by `_in_one_unit`: keep it.
    number = _quantity_latex(quantity, settings=current, declared=True)
    names = [node for node in ast.walk(operand) if isinstance(node, ast.Name)]
    if written is None or not names or all(node.id in units for node in names):
        return number
    return f"{_latex(sp.sympify(written), units, current)} = {number}"
