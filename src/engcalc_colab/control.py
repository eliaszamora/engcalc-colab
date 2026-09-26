"""`% if` and `% for`: lines of a cell that decide which other lines run, and how often.

A line that starts with `%` is control, written as Python: `% if`, `% elif`, `% else`,
`% for`, and `% end` closes the block; `% n = 0` and `% n += 1` keep a helper of the `%`
layer. Every other line is the sheet's own. A condition reads the values the sheet has
computed by then, with their units, and only the branch that holds runs; it opens with a
sentence that states the condition in numbers - `Como Vu = 7920.00 kgf > φ_v V_c = 7603.63
kgf:` - because that is what a reviewer checks. A `% for` runs its lines once per value,
and `{...}` in a sheet line puts a value of the `%` layer into it: `M_U{i} := M({a}, {b})`
is written `M_U1 := M(1.4, 0)`, then `M_U2 := ...`. The memoria shows the rows each time,
as if they had been written by hand, and nothing of the `%` layer. Approved on
2026-09-25; see `tests/test_a_sheet_decides_with_if.py` and
`tests/test_a_sheet_repeats_with_for.py`.

The cell's structure is read before anything runs, so a block written wrong refuses the
whole cell, as a line written wrong always has. The lines themselves are parsed a stretch
at a time and evaluated as they come, because a condition may read a value computed two
lines above it.
"""

from __future__ import annotations

import ast
import itertools
import re
from dataclasses import dataclass, field
from typing import Iterator

import sympy as sp
from pint.errors import DimensionalityError

from .errors import EngCalcError, EngEvaluationError, EngSyntaxError
from .parser import normalize_expression, parse_cell

_KEYWORD = re.compile(r"^(\w+)\b(.*)$", re.S)
_BLOCKS = ("if", "elif", "else", "end", "for", "while")
_INSERTED = re.compile(r"\{([^{}]+)\}")
# A `% for` that would write more rows than a memoria can hold is a mistake, and one that
# never ends would hang the notebook. The same limit `% while` will have.
_MOST_ITERATIONS = 1000
# What the `%` layer can call. It is Python for arranging a sheet, not for reaching out of it.
_BUILTINS = {
    name: __builtins__[name] if isinstance(__builtins__, dict) else getattr(__builtins__, name)
    for name in (
        "abs", "enumerate", "float", "int", "len", "list", "max", "min", "range",
        "reversed", "round", "sorted", "str", "sum", "tuple", "zip",
    )
}
_WHAT_A_PERCENT_LINE_IS = (
    "a line that starts with % is % if, % elif, % else, % for, % while, % end, or a "
    "helper such as % n = 0"
)


@dataclass(frozen=True)
class ConditionNote:
    """The sentence a branch opens with, as LaTeX, typeset in the letter and size of the rows.

    It was first Markdown - Colab's text around `$...$` - and he could not find it on the
    page: smaller than the rows and in another letter. He chose (2026-09-25, option 1b) the
    whole sentence typeset as the rows are, "Como" in bold. Its room above and below is the
    room every block has (`renderer.page_block`), no longer a strut of its own.
    """

    latex: str


@dataclass
class _Stretch:
    first_line: int
    lines: list[str] = field(default_factory=list)
    # Indices of the lines inside a `\"\"\"` block: text, where a brace is LaTeX's.
    text: set[int] = field(default_factory=set)


@dataclass
class _Branch:
    line_no: int
    condition: str | None  # None for `% else`
    body: list = field(default_factory=list)


@dataclass
class _IfBlock:
    line_no: int
    branches: list[_Branch] = field(default_factory=list)


@dataclass
class _ForBlock:
    line_no: int
    header: ast.For
    body: list = field(default_factory=list)


@dataclass
class _WhileBlock:
    line_no: int
    condition: str
    body: list = field(default_factory=list)


@dataclass(frozen=True)
class Evaluated:
    """A line a `% while` has already worked out: its last iteration, shown as it stands."""

    result: object
    notices: tuple = ()


@dataclass
class _Helper:
    line_no: int
    code: str


class _SheetName:
    """A name of the sheet inside the `%` layer: it compares by its value, and `{F}` writes
    `F_1` - the name, as a hand-written sheet would - not its number."""

    def __init__(self, name: str, quantity) -> None:
        self.name = name
        self.quantity = quantity

    def __repr__(self) -> str:
        return self.name

    # Arithmetic gives a plain value: it has no name to be written with.
    def _other(self, other):
        return other.quantity if isinstance(other, _SheetName) else other

    def __add__(self, other): return self.quantity + self._other(other)
    def __radd__(self, other): return self._other(other) + self.quantity
    def __sub__(self, other): return self.quantity - self._other(other)
    def __rsub__(self, other): return self._other(other) - self.quantity
    def __mul__(self, other): return self.quantity * self._other(other)
    def __rmul__(self, other): return self._other(other) * self.quantity
    def __truediv__(self, other): return self.quantity / self._other(other)
    def __rtruediv__(self, other): return self._other(other) / self.quantity
    def __neg__(self): return -self.quantity
    def __lt__(self, other): return self.quantity < self._other(other)
    def __le__(self, other): return self.quantity <= self._other(other)
    def __gt__(self, other): return self.quantity > self._other(other)
    def __ge__(self, other): return self.quantity >= self._other(other)


class _Scope(dict):
    """The `%` layer's variables; a name it does not hold is looked up on the sheet."""

    def __init__(self, engine) -> None:
        super().__init__()
        self.engine = engine

    def __missing__(self, name):
        value = self.engine.numeric_context.values.get(name)
        if value is None:
            raise KeyError(name)
        return _SheetName(name, value)


def _lines(cell: str) -> list[tuple[int, str, str]]:
    """Each line, numbered, as `text` (inside `\"\"\"`), `sheet` or `control`.

    A `%` line whose brackets are still open goes on in the `%` lines after it, as Python
    does: `% for i, c in enumerate([(1.4, 0),` then `%   (1.2, 1.6)]):` is one header.
    """
    raw_lines = cell.splitlines()
    out: list[tuple[int, str, str]] = []
    in_text = False
    index = 0
    while index < len(raw_lines):
        raw = raw_lines[index]
        text = raw.strip()
        index += 1
        if in_text:
            in_text = '"""' not in text
            out.append((index, raw, "text"))
            continue
        if text.startswith('"""'):
            # `"""` alone opens a block; `"""One line."""` opens and closes it.
            in_text = '"""' not in text[3:]
            out.append((index, raw, "text"))
            continue
        if not text.startswith("%"):
            out.append((index, raw, "sheet"))
            continue
        line_no = index
        code = text[1:].strip()
        while _open_brackets(code) > 0 and index < len(raw_lines) and raw_lines[index].strip().startswith("%"):
            code += " " + raw_lines[index].strip()[1:].strip()
            index += 1
        out.append((line_no, code, "control"))
    return out


def _open_brackets(code: str) -> int:
    return sum(code.count(c) for c in "([{") - sum(code.count(c) for c in ")]}")


def has_control(cell: str) -> bool:
    return any(kind == "control" for _line_no, _raw, kind in _lines(cell))


def _structure(cell: str) -> list:
    """The cell as stretches of sheet lines, helpers and `% if` / `% for` blocks, nested."""
    root: list = []
    stack: list[tuple[object, list]] = []
    body = root

    def stretch(line_no: int) -> _Stretch:
        if body and isinstance(body[-1], _Stretch):
            return body[-1]
        new = _Stretch(first_line=line_no)
        body.append(new)
        return new

    for line_no, raw, kind in _lines(cell):
        if kind != "control":
            current = stretch(line_no)
            # Keep the stretch's lines aligned with the cell's, so a line inside it is
            # numbered as the cell numbers it.
            while current.first_line + len(current.lines) < line_no:
                current.lines.append("")
            if kind == "text":
                current.text.add(len(current.lines))
            current.lines.append(raw)
            continue
        code = raw
        match = _KEYWORD.match(code)
        keyword = match.group(1) if match else ""
        rest = match.group(2).strip() if match else ""
        if keyword not in _BLOCKS:
            body.append(_helper(code, line_no))
            continue
        condition = rest[:-1].strip() if rest.endswith(":") else rest
        if keyword == "if":
            if not condition:
                raise EngSyntaxError(f"line {line_no}: % if needs a condition, as in % if Vu > phi*V_c:")
            block = _IfBlock(line_no=line_no, branches=[_Branch(line_no, condition)])
            body.append(block)
            stack.append((block, body))
            body = block.branches[-1].body
        elif keyword == "for":
            block = _ForBlock(line_no=line_no, header=_for_header(code, line_no))
            body.append(block)
            stack.append((block, body))
            body = block.body
        elif keyword == "while":
            if not condition:
                raise EngSyntaxError(
                    f"line {line_no}: % while needs a condition, as in % while abs(r) > 0.001:"
                )
            block = _WhileBlock(line_no=line_no, condition=condition)
            body.append(block)
            stack.append((block, body))
            body = block.body
        elif keyword in ("elif", "else"):
            if not stack:
                raise EngSyntaxError(f"line {line_no}: % {keyword} with no % if open above it")
            block, _outer = stack[-1]
            if not isinstance(block, _IfBlock):
                raise EngSyntaxError(
                    f"line {line_no}: % {keyword} belongs to a % if; the % {_kind(block)} of "
                    f"line {block.line_no} has none"
                )
            if block.branches[-1].condition is None:
                raise EngSyntaxError(f"line {line_no}: % {keyword} after the % else of line {block.branches[-1].line_no}")
            if keyword == "elif" and not condition:
                raise EngSyntaxError(f"line {line_no}: % elif needs a condition")
            block.branches.append(_Branch(line_no, condition if keyword == "elif" else None))
            body = block.branches[-1].body
        else:  # end
            if not stack:
                raise EngSyntaxError(f"line {line_no}: % end with no % if, % for or % while open above it")
            _block, body = stack.pop()
    if stack:
        block, _outer = stack[-1]
        raise EngSyntaxError(f"line {block.line_no}: this % {_kind(block)} has no % end")
    return root


def _kind(block) -> str:
    return {_ForBlock: "for", _WhileBlock: "while"}.get(type(block), "if")


def _for_header(code: str, line_no: int) -> ast.For:
    """`for i, (a, b) in enumerate(...):` read as Python, or refused with its line."""
    try:
        (header,) = ast.parse(code + "\n    pass").body if code.endswith(":") else (None,)
    except SyntaxError:
        header = None
    if not isinstance(header, ast.For):
        raise EngSyntaxError(
            f"line {line_no}: % for is written as Python, as in % for i in [1, 2]: - "
            f"this one reads {code}"
        )
    return header


def _helper(code: str, line_no: int) -> _Helper:
    """`% n = 0`, `% n += 1`: a variable of the `%` layer, never on the page."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        tree = None
    if tree is None or len(tree.body) != 1 or not isinstance(tree.body[0], (ast.Assign, ast.AugAssign)):
        raise EngSyntaxError(f"line {line_no}: {_WHAT_A_PERCENT_LINE_IS}")
    return _Helper(line_no, code)


def _check_lines(nodes: list) -> None:
    """Every sheet line parsed before any runs, as a cell without `%` lines is.

    A `{...}` is read as a number here: what it will hold is known only when it runs, and
    a line written wrong around it is wrong whatever it holds.
    """
    for node in nodes:
        if isinstance(node, _Stretch):
            _parse_stretch(node, lambda _text, _line_no: "1")
        elif isinstance(node, _ForBlock):
            _check_lines(node.body)
        elif isinstance(node, _WhileBlock):
            _condition_tree(node.condition, node.line_no)
            _check_lines(node.body)
        elif isinstance(node, _IfBlock):
            for branch in node.branches:
                if branch.condition is not None:
                    _condition_tree(branch.condition, branch.line_no)
                _check_lines(branch.body)


def _parse_stretch(stretch: _Stretch, insert=None):
    lines = list(stretch.lines)
    if insert is not None:
        for index, line in enumerate(lines):
            if index not in stretch.text and "{" in line:
                line_no = stretch.first_line + index
                lines[index] = _INSERTED.sub(lambda m, n=line_no: insert(m.group(1), n), line)
    # Empty lines in front number the stretch as the cell does; a leading blank line
    # changes nothing on the page.
    return parse_cell("\n" * (stretch.first_line - 1) + "\n".join(lines))


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
    yield from _walk(tree, engine, settings, _Scope(engine))


def _walk(nodes: list, engine, settings, scope: _Scope) -> Iterator:
    for node in nodes:
        if isinstance(node, _Stretch):
            yield from _parse_stretch(node, lambda text, line_no: _inserted(text, line_no, scope))
        elif isinstance(node, _Helper):
            _run_helper(node, scope)
        elif isinstance(node, _ForBlock):
            yield from _repeat(node, engine, settings, scope)
        elif isinstance(node, _WhileBlock):
            yield from _iterate(node, engine, settings, scope)
        else:
            yield from _choose(node, engine, settings, scope)


def _choose(node: _IfBlock, engine, settings, scope: _Scope) -> Iterator:
    held = []
    chosen = None
    stated = ""
    for branch in node.branches:
        if branch.condition is None:
            chosen = branch
            break
        tree = _in_scope(_condition_tree(branch.condition, branch.line_no), scope)
        verdict, stated = _decide(tree, branch.line_no, engine, settings)
        if verdict:
            chosen = branch
            break
        held.append((tree, branch.line_no))
    if chosen is None:
        return
    # Why this branch: the conditions above it that did not hold, then its own.
    said = [_negated(tree, line_no, engine, settings) for tree, line_no in held]
    if chosen.condition is not None:
        said.append(stated)
    yield ConditionNote(latex=f"\\textbf{{Como}}\\;\\; {_AND.join(said)}\\,\\text{{:}}")
    yield from _walk(chosen.body, engine, settings, scope)


def _repeat(node: _ForBlock, engine, settings, scope: _Scope) -> Iterator:
    line_no = node.line_no
    source = ast.unparse(node.header.iter)
    try:
        values = iter(_evaluated(node.header.iter, scope, line_no))
    except TypeError as exc:
        raise EngEvaluationError(
            f"line {line_no}: % for goes through a list, a range or an enumerate; "
            f"{source} is not one"
        ) from exc
    values = list(itertools.islice(values, _MOST_ITERATIONS + 1))
    if len(values) > _MOST_ITERATIONS:
        raise EngEvaluationError(
            f"line {line_no}: this % for runs more than {_MOST_ITERATIONS} times, more rows "
            "than a memoria can hold"
        )
    assign = compile(
        ast.fix_missing_locations(ast.Module(
            body=[ast.Assign(targets=[node.header.target], value=ast.Name("__value__", ast.Load()))],
            type_ignores=[],
        )),
        "<% for>",
        "exec",
    )
    for value in values:
        try:
            exec(assign, {"__builtins__": _BUILTINS, "__value__": value}, scope)  # noqa: S102 - the sheet's own % layer
        except (TypeError, ValueError) as exc:
            raise EngEvaluationError(
                f"line {line_no}: % for cannot give {ast.unparse(node.header.target)} the value "
                f"{value!r}: {exc}"
            ) from exc
        yield from _walk(node.body, engine, settings, scope)


def _iterate(node: _WhileBlock, engine, settings, scope: _Scope) -> Iterator:
    """Run the body while the condition holds, and show only the last time it ran.

    Each iteration is worked out here, silently: an iteration nobody reads is not written.
    What the page gets is a sentence - how many iterations, and the condition as it stands
    now, which no longer holds - and then the rows of the last iteration.
    """
    tree = _condition_tree(node.condition, node.line_no)
    count = 0
    last: list = []
    while True:
        current = _in_scope(tree, scope)
        holds, _said = _decide(current, node.line_no, engine, settings)
        if not holds:
            break
        if count == _MOST_ITERATIONS:
            raise EngEvaluationError(
                f"line {node.line_no}: this % while ran {_MOST_ITERATIONS} times and its "
                f"condition still holds: it does not converge from this start"
            )
        count += 1
        last = []
        for item in _walk(node.body, engine, settings, scope):
            if isinstance(item, (ConditionNote, Evaluated)) or not hasattr(item, "line_no"):
                last.append(item)
            elif type(item).__name__ in ("ParsedHeading", "ParsedNarrative"):
                last.append(item)
            else:
                result = engine.evaluate(item)
                last.append(Evaluated(result, tuple(engine.notices)))
    word = "iteración" if count == 1 else "iteraciones"
    stated = _negated(current, node.line_no, engine, settings)
    yield ConditionNote(latex=f"\\textbf{{En {count} {word}:}}\\;\\; {stated}")
    yield from last


def _run_helper(node: _Helper, scope: _Scope) -> None:
    try:
        exec(compile(node.code, "<% line>", "exec"), {"__builtins__": _BUILTINS}, scope)  # noqa: S102
    except NameError as exc:
        raise EngEvaluationError(f"line {node.line_no}: {_unknown(exc)}") from exc
    except Exception as exc:  # noqa: BLE001 - said in the sheet's words, with its line
        raise EngEvaluationError(f"line {node.line_no}: % {node.code} failed: {exc}") from exc


def _evaluated(tree: ast.AST, scope: _Scope, line_no: int):
    try:
        return eval(  # noqa: S307 - the sheet's own % layer, with a short list of builtins
            compile(ast.Expression(body=tree), "<% line>", "eval"), {"__builtins__": _BUILTINS}, scope
        )
    except NameError as exc:
        raise EngEvaluationError(f"line {line_no}: {_unknown(exc)}") from exc
    except EngCalcError:
        raise
    except TypeError:
        raise
    except Exception as exc:  # noqa: BLE001 - said in the sheet's words, with its line
        raise EngEvaluationError(f"line {line_no}: {ast.unparse(tree)} failed: {exc}") from exc


def _unknown(exc: NameError) -> str:
    name = getattr(exc, "name", None) or str(exc)
    return f"{name} is neither a variable of the % lines nor a value of the sheet"


def _inserted(text: str, line_no: int, scope: _Scope) -> str:
    """What `{text}` writes into a sheet line: a number, a name of the sheet, or text."""
    try:
        tree = ast.parse(text.strip(), mode="eval").body
    except SyntaxError as exc:
        raise EngSyntaxError(f"line {line_no}: {{{text}}} is not something to put in a line") from exc
    try:
        value = _evaluated(tree, scope, line_no)
    except TypeError as exc:
        raise EngEvaluationError(f"line {line_no}: {{{text}}} failed: {exc}") from exc
    if isinstance(value, _SheetName):
        return value.name
    if isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    raise EngEvaluationError(
        f"line {line_no}: {{{text}}} holds {value!r}, and a line can take a number, a name "
        "of the sheet or text; put the arithmetic in the line itself, as 2*{F}"
    )


class _InScope(ast.NodeTransformer):
    """A condition inside a `% for` reads its variables: `x > 2` with `x` = 3 is `3 > 2`."""

    def __init__(self, scope: _Scope) -> None:
        self.scope = scope

    def visit_Name(self, node: ast.Name):
        if node.id not in dict.keys(self.scope):
            return node
        value = dict.__getitem__(self.scope, node.id)
        if isinstance(value, _SheetName):
            return ast.copy_location(ast.Name(value.name, ast.Load()), node)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return ast.copy_location(ast.Constant(value), node)
        return node


def _in_scope(tree: ast.AST, scope: _Scope) -> ast.AST:
    if not dict.__len__(scope):
        return tree
    return _InScope(scope).visit(tree)


# -- deciding, and saying it -------------------------------------------------------------

_OPERATORS = {
    ast.Gt: (">", ">", lambda a, b: a > b),
    ast.GtE: (">=", r"\geq", lambda a, b: a >= b),
    ast.Lt: ("<", "<", lambda a, b: a < b),
    ast.LtE: ("<=", r"\leq", lambda a, b: a <= b),
    ast.Eq: ("==", "=", lambda a, b: a == b),
    ast.NotEq: ("!=", r"\neq", lambda a, b: a != b),
}
# The words of the sentence, typeset as text inside it.
_AND = r"\;\text{y}\;"
_OR = r"\;\text{o}\;"
_NOT = r"\text{no se cumple }"
_NEGATED = {ast.Gt: ast.LtE, ast.GtE: ast.Lt, ast.Lt: ast.GtE, ast.LtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}


def _decide(tree: ast.AST, line_no: int, engine, settings) -> tuple[bool, str]:
    """Whether the condition holds, and the condition said in numbers."""
    if isinstance(tree, ast.BoolOp):
        parts = []
        joiner = _AND if isinstance(tree.op, ast.And) else _OR
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
        return (not verdict), f"{_NOT}{said}"
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
    return f"{_NOT}{said}"


def _compare(tree: ast.Compare, line_no: int, engine, settings, operators) -> tuple[bool, str]:
    operands = [tree.left, *tree.comparators]
    values = _zeros_in_their_neighbours_unit(
        [_value(operand, line_no, engine) for operand in operands]
    )
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
    return verdict, said


def _zeros_in_their_neighbours_unit(values: list) -> list:
    """`V > 0` and `x > 0*m`: a zero compares with anything, in its neighbour's unit.

    `0*kN` reaches here as a plain 0 - a zero keeps no unit - and a comparison of kN against
    a plain number is refused, rightly for `V > 3` and wrongly for zero. Found writing
    `% while x > 0*m` (2026-09-25).
    """
    from dataclasses import replace  # noqa: PLC0415

    units = next(
        (value[0].quantity.units for value in values if not value[0].quantity.dimensionless),
        None,
    )
    if units is None:
        return values
    out = []
    for result, written, literals in values:
        quantity = result.quantity
        if quantity.dimensionless and quantity.magnitude == 0:
            result = replace(result, quantity=quantity.magnitude * units)
        out.append((result, written, literals))
    return out


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
    quantities = [result.quantity for result, _written, _units in values]
    # The first side's unit, unless a side has no figure left in it - `1e-6 m²` reads
    # `0.00 m²` and the printer moves it to cm² on its own, one side in each unit. Then
    # the unit that side would be shown in, for every side.
    candidates = [first.units] + [
        _display_quantity(quantity, current, declared=False).units for quantity in quantities[1:]
    ]
    common = next(
        (
            unit
            for unit in candidates
            if all(_reads_in(quantity, unit, current) for quantity in quantities)
        ),
        first.units,
    )
    shown = []
    for index, quantity in enumerate(quantities):
        if quantity.dimensionality == first.dimensionality:
            shown.append(quantity.to(common))
        else:
            shown.append(first if index == 0 else _display_quantity(quantity, current, declared=False))
    return shown


def _reads_in(quantity, unit, settings) -> bool:
    """Whether `quantity` keeps a figure written in `unit` (a zero always does)."""
    from .renderer import _display_quantity  # noqa: PLC0415 - renderer imports models only

    try:
        converted = quantity.to(unit)
    except DimensionalityError:
        return True
    if abs(float(converted.to_base_units().magnitude)) <= settings.zero_tolerance:
        return True
    return _display_quantity(converted, settings, declared=True).units == converted.units


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
