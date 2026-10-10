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
import copy
import itertools
import re
from dataclasses import dataclass, field, replace
from typing import Iterator

import sympy as sp
from pint.errors import DimensionalityError

from .errors import EngCalcError, EngEvaluationError, EngSyntaxError, diagnostic_hint
from .matrix_syntax import continued_lines, without_comment
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

    `notices` are what the lines it stands for said, for the console: a loop's table is
    one note for many `:=` lines, and what they say is said once.
    """

    latex: str
    notices: tuple = ()


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
        # Whether a `% for` around this point gathers its passes; one inside it streams
        # its own into the gathering one, which shows its assembly once for both.
        self.gathering = False
        # How many `% for` this point is inside: only the outermost one gathers.
        self.depth = 0

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
            _parse_stretch(node, _PROBE)
        elif isinstance(node, _ForBlock):
            _check_lines(node.body)
        elif isinstance(node, _WhileBlock):
            _condition_tree(_probed(node.condition, node.line_no), node.line_no, node.condition)
            _check_lines(node.body)
        elif isinstance(node, _IfBlock):
            for branch in node.branches:
                if branch.condition is not None:
                    _condition_tree(_probed(branch.condition, branch.line_no), branch.line_no, branch.condition)
                _check_lines(branch.body)


def _PROBE(_text, _line_no):
    """What a line's structure is read with before any pass runs: a stand-in value."""
    return _PROBE


def _probed(condition: str, line_no: int) -> str:
    """A condition read before any pass, its placeholders stand-ins as a line's are:
    `% if h_{e} < 0.5` read `h_` beside a set and was refused before the loop ran (his
    book, chapter 10, found by all four solvers)."""
    return _INSERTED.sub(lambda match: _put(_PROBE, match, line_no, condition), condition)


_IN_A_NUMBER_S_BRACKETS = re.compile(
    r"(?:(?<![\w.])(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?|(?<![\w}])\{[^{}]+\})\s*\[[^\[\]]*$"
)


def _put(insert, match, line_no, line):
    written = insert(match.group(1), line_no)
    if written is not _PROBE:
        return written
    # `{r}_a`, `k{p}`: a stand-in glued to a name is a name, or the line read `1_a` and was
    # refused before any pass ran (his book, problem 5.9); anywhere else it is a number.
    before = line[match.start() - 1] if match.start() else " "
    after = line[match.end()] if match.end() < len(line) else " "
    # `3[{u}]`, `{i}[{u}]`: inside a number's brackets it holds a unit, and the number `1`
    # there was refused, "3[1] holds no unit", before any pass ran (the audits of 0.46.1 and
    # of its fixes). An index, `x2[{i}]`, follows a name and is not this.
    # A comma makes it an entry, `{M}[{i}, 1]`: a unit has none.
    inside = _IN_A_NUMBER_S_BRACKETS.search(line[: match.start()])
    rest = re.match(r"[^\[\]]*\]", line[match.end():])
    if inside and rest and "," not in inside.group(0) + rest.group(0):
        return "m"
    if after.isalnum() or after == "_" or before.isalnum() or before == "_":
        return "n1"
    # `{M}[{i}, 1]`: brackets with a comma hold an entry, so what opens them is a matrix.
    if after == "[" and re.match(r"\[[^\[\]]*,[^\[\]]*\]", line[match.end():]):
        return "n1"
    # `{n} := 1`: the whole target is a name, or the line read `1 := 1` (his book, chapter 10).
    rest = line[match.end():].lstrip()
    if not line[: match.start()].strip() and (rest.startswith(":=") or (rest.startswith("=") and not rest.startswith("=="))):
        return "n1"
    # After an operand - `(2*a){q}`, `a {q}` - the placeholder holds an operation, ` + b`:
    # a bare number there read `(2*a)1` and the loop was refused before it ran (his book,
    # chapter 9).
    previous = line[: match.start()].rstrip()[-1:]
    if previous in (")", "]") or (previous and (previous.isalnum() or previous == "_") and before == " "):
        return " + 1"
    return "1"


def _parse_stretch(stretch: _Stretch, insert=None):
    lines = list(stretch.lines)
    written = {}
    if insert is not None:
        # A statement over several lines is made one line first, the rest left as comments
        # so the lines keep their numbers: its placeholders are read on the whole line, and
        # a gathering loop writes its rule whole - it wrote the first line, cut off (the
        # audit of 0.46.0).
        index = 0
        while index < len(lines):
            count = 1 if index in stretch.text else continued_lines(lines, index)
            if count > 1:
                parts = [without_comment(line).strip() for line in lines[index:index + count]]
                lines[index:index + count] = [" ".join(parts)] + ["#"] * (count - 1)
            index += count
        for index, line in enumerate(lines):
            if index not in stretch.text and "{" in line:
                line_no = stretch.first_line + index
                lines[index] = _INSERTED.sub(lambda m, n=line_no, s=line: _put(insert, m, n, s), line)
                if lines[index] != line:
                    written[line_no] = line.strip()
    # Empty lines in front number the stretch as the cell does; a leading blank line
    # changes nothing on the page.
    parsed = parse_cell("\n" * (stretch.first_line - 1) + "\n".join(lines))
    # A line that is told how to be written is told as the sheet writes it, `M_{i} = ...`,
    # not as one pass reads it.
    return [
        replace(item, written_as=written[item.line_no])
        if item.line_no in written and hasattr(item, "written_as") and "\n" not in item.source
        else item
        for item in parsed
    ]


def _with_placeholders(text: str, line_no: int, scope: _Scope) -> str:
    """A condition with the values of the % lines written in, as a line of the body writes
    them: `% while abs(r^2 - {a}) > 1e-9` read `{2}` as a set (his book, chapter 9). Done
    each time the condition is decided, as its bare names are read: written in once, a
    counter the body moves never reached it (the audit of 0.45.6)."""
    return re.sub(
        r"\{([^{}]+)\}", lambda match: _inserted(match.group(1), line_no, scope), text
    )


def _condition_tree(text: str, line_no: int, written: str | None = None) -> ast.AST:
    try:
        tree = ast.parse(normalize_expression(text, line_no), mode="eval").body
    except SyntaxError as exc:
        # Quoted as typed, `x {op} 3`, and not as the stand-ins it was read with.
        message = f"line {line_no}: the condition of this % line is not one: {written or text}"
        # The hint a `:=` line gives: `% if y > 1*kip*in` is the inch (his book, chapter 10).
        if re.search(r"\bin\b", text):
            message += ". " + diagnostic_hint("keyword_unit_name", name="in", replacement="inch")
        raise EngSyntaxError(message) from exc
    return _read_in_numbers(tree, text, line_no)


def _read_in_numbers(tree: ast.AST, text: str, line_no: int) -> ast.AST:
    """A condition is worked out in numbers, and has no place to record one.

    A `report` records a value of the sheet for its summary; written in a condition it
    was a record taken while deciding. What `numeric` reads in a condition is `_value`'s.
    """
    if any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "report"
        for node in ast.walk(tree)
    ):
        from .engine import _written_without_numeric  # noqa: PLC0415 - engine imports this module's users

        raise EngEvaluationError(
            f"line {line_no}: report must be a standalone statement; a condition reads the "
            f"value itself: {_written_without_numeric(text, False)[0]}"
        )
    return tree


def _a_numeric(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "numeric"


class _ItsValue(ast.NodeTransformer):
    """`2*numeric(M_2)` in a condition is `2*M_2`; the side that is a `numeric` stays one.

    Each side is evaluated as `numeric(<side>)`, and since 0.43.2 `numeric` inside a
    formula is refused - a `numeric` written in a condition, which read before, was refused
    with it (the audit, 2026-09-28). One inside a side reads as its value, a unit it asks
    for checked by `check` as the side it would be; a side that is a `numeric`, `result`
    too, is worked out as it was, in the unit it asks for (the second audit: dropped, `%
    if numeric(r, percent) > 50` ran, and `numeric(d, mm)` was said in metres).
    """

    def __init__(self, whole, check) -> None:
        self.whole = whole
        self.check = check

    def visit_Call(self, node):
        self.generic_visit(node)
        if node is self.whole or not _a_numeric(node) or len(node.args) not in (1, 2) or node.keywords:
            return node
        if len(node.args) == 2:
            self.check(node)
        return node.args[0]


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
        condition = _with_placeholders(branch.condition, branch.line_no, scope)
        tree = _in_scope(_condition_tree(condition, branch.line_no), scope)
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

    def take(value) -> None:
        try:
            exec(assign, {"__builtins__": _BUILTINS, "__value__": value}, scope)  # noqa: S102 - the sheet's own % layer
        except (TypeError, ValueError) as exc:
            raise EngEvaluationError(
                f"line {line_no}: % for cannot give {ast.unparse(node.header.target)} the value "
                f"{value!r}: {exc}"
            ) from exc

    # A loop inside another streams its lines into it: one that gathers shows its assembly
    # once for both, and one that does not shows its rows as they come - an inner table per
    # outer pass had no outer index to say which it was. A loop with nothing to gather shows
    # its rows as they come, as written by hand (approved 2026-09-25).
    if scope.gathering or scope.depth or not _gathers(node.body):
        scope.depth += 1
        try:
            for value in values:
                take(value)
                yield from _walk(node.body, engine, settings, scope)
        finally:
            scope.depth -= 1
        return
    scope.gathering = True
    scope.depth += 1
    try:
        yield from _gathered(node, values, take, engine, settings, scope)
    finally:
        scope.gathering = False
        scope.depth -= 1


@dataclass
class _Kept:
    """A line a gathering loop worked out, and what the page needs of it."""

    kind: str  # "shown", "cell", "formula" or "part"
    item: object = None  # what is shown as it came, for "shown"
    key: object = None
    index: int = 0  # the pass
    direct: bool = True  # a line of the loop's own, not of a loop or `% if` inside it
    result: object = None
    notices: tuple = ()
    said: dict = field(default_factory=dict)  # the `%` values of the names its rule stands on


def _gathered(node: _ForBlock, values: list, take, engine, settings, scope: _Scope) -> Iterator:
    """A `% for` whose `:=` values are a table, or that assembles a matrix: every pass is
    worked out here and kept, and the page gets them once the loop is over (his decision,
    2026-09-29) - the table, then what the passes showed in the order they showed it, then
    each assembly's rule and the matrix it built.

    A pass that fails puts every row kept so far on the page, in the order it ran, and then
    the error: what the page shows of a failing loop is what it showed by hand.
    """
    from .models import ParsedNumericAssignment  # noqa: PLC0415 - models import nothing back

    helpers = _helpers_of(node)
    stands_on: dict = {}
    defined: dict = {}  # the names each line of the loop has defined so far
    kept: list[_Kept] = []
    try:
        for index, value in enumerate(values):
            take(value)
            occurrences: dict = {}
            for child in node.body:
                direct = isinstance(child, _Stretch)
                items = (
                    _parse_stretch(child, lambda text, line_no: _inserted(text, line_no, scope))
                    if direct
                    else _walk([child], engine, settings, scope)
                )
                for item in items:
                    if _shown_as_it_comes(item):
                        kept.append(_Kept("shown", item=item, index=index))
                        continue
                    result = engine.evaluate(item)
                    notices = tuple(engine.notices)
                    template = getattr(item, "written_as", None) or item.source
                    if template not in stands_on:
                        stands_on[template] = _names_it_stands_on(template, helpers)
                    said = {name: dict.get(scope, name) for name in stands_on[template] if dict.__contains__(scope, name)}
                    entry = _Kept("shown", index=index, direct=direct, result=result, notices=notices, said=said)
                    if _adds_into_a_part(item):
                        entry.kind, entry.key = "part", (item.target, template)
                    elif direct and isinstance(item, ParsedNumericAssignment):
                        occurrence = occurrences.get(template, 0)
                        occurrences[template] = occurrence + 1
                        entry.kind, entry.key = "cell", (template, occurrence)
                    elif direct and _a_formula(item, result) and not _reads_its_earlier_passes(item, defined.get(template, ())):
                        entry.kind, entry.key = "formula", template
                    if getattr(item, "target", None):
                        defined.setdefault(template, set()).add(item.target)
                    kept.append(entry)
    except EngCalcError:
        for entry in kept:
            yield _as_it_ran(entry)
        raise

    columns = _table_columns(kept)
    if columns:
        from .renderer import formula_rules_latex, loop_table_latex  # noqa: PLC0415 - renderer imports models only

        cells = {key: [None] * len(values) for key in columns}
        said: list = []
        for entry in kept:
            if entry.kind == "cell" and entry.key in cells:
                cells[entry.key][entry.index] = entry.result.quantity
                said.extend(notice for notice in entry.notices if notice not in said)
        variable = [element.id for element in ast.walk(node.header.target) if isinstance(element, ast.Name)]
        table = loop_table_latex(
            variable, values, [(_written_target(key[0]), cells[key]) for key in columns], _current(settings)
        )
        formulas = [key[0] for key in columns if _worked_out(key[0], variable)]
        if formulas:
            # The table gives the numbers; what each column is worked out from is written
            # once, above it - a memoria that shows `0.87` and never `sin 60°` shows nothing
            # to check (chapter 4 of his book). The table's first column gives the loop's
            # values; the helpers and the `%` names the formulas stand on are said here.
            entries = [entry for entry in kept if entry.kind == "cell" and entry.key[0] in formulas]
            _names, _labels, made, constants = _what_it_stands_on(formulas, entries, helpers, variable)
            yield ConditionNote(latex=formula_rules_latex(len(values), formulas, (), None, made, constants))
        yield ConditionNote(latex=table, notices=tuple(said))
    yield from _in_the_order_they_ran(node, values, kept, columns, helpers)
    yield from _assemblies(kept, helpers, settings, _header_names(node))


def _header_names(node: _ForBlock) -> list[str]:
    return [element.id for element in ast.walk(node.header.target) if isinstance(element, ast.Name)]


def _reads_its_earlier_passes(item, earlier) -> bool:
    """`M_{i} = M_{i-1} + V_{i}`: a line that reads what it defined in an earlier pass is a
    recurrence, and each pass is a new value a reader needs - the rule alone never said
    what M_3 came to."""
    return bool(earlier) and any(
        isinstance(node, ast.Name) and node.id in earlier for node in ast.walk(item.expression.body)
    )


def _names_it_stands_on(template: str, helpers: list) -> list[str]:
    """The `%` names a loop's line reads: those in its `{...}`, and those the helpers it
    reads were made from, followed back through helpers made from helpers - `K[[{p}, {q}],
    ...]` with `% p, q = 2*m - 1, 2*m` stands on p, q and m. In the order they are written."""
    return _chain([template], helpers)[0]


def _chain(templates: list, helpers: list) -> tuple[list[str], list[str]]:
    """The `%` names the lines stand on, and the helpers that made any of them, in the order
    the loop writes those helpers."""
    names: list[str] = []
    for template in templates:
        for inside in re.findall(r"\{([^{}]+)\}", template):
            names.extend(name for name in re.findall(r"[A-Za-z_]\w*", inside) if name not in names)
    used: set = set()
    changed = True
    while changed:
        changed = False
        for position, (code, made) in enumerate(helpers):
            if position not in used and made & set(names):
                used.add(position)
                names.extend(name for name in _names_read(code) if name not in names)
                changed = True
    return names, [code for position, (code, _made) in enumerate(helpers) if position in used]


def _names_read(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    read: list[str] = []
    for statement in tree.body:
        value = getattr(statement, "value", None)
        for element in ast.walk(value) if value is not None else ():
            if isinstance(element, ast.Name) and element.id not in read and element.id not in _BUILTINS:
                read.append(element.id)
    return read


def _what_it_stands_on(templates: list, entries: list, helpers: list, variable=None, order=()):
    """For a note: the names whose values changed from pass to pass and those values, the
    helpers that made names the lines read, and the `%` names that were the same every pass.

    `variable`, given, leaves the loop's own names out of the values - its table says them.
    """
    made_by_helpers = set().union(*(made for _code, made in helpers)) if helpers else set()
    names: list[str] = []
    for entry in entries:
        names.extend(name for name in entry.said if name not in names)
    _reached, made = _chain(templates, helpers)
    names = [name for name in names if name not in made_by_helpers]
    # The loop's own names first, as its header writes them: `(m, p)`, not `(p, m)`.
    if order:
        names = [name for name in order if name in names] + [name for name in names if name not in order]
    if len(templates) == 1:
        # Each time the line ran - a loop inside this one runs it several times a pass.
        ordered = [entry.said for entry in entries]
    else:
        passes: dict = {}
        for entry in entries:
            passes.setdefault(entry.index, {}).update(entry.said)
        ordered = [passes[index] for index in sorted(passes)]
    varying, constants = [], []
    for name in names:
        seen = [said.get(name) for said in ordered]
        if variable is not None and name in variable:
            continue
        if len(ordered) > 1 and any(value != seen[0] for value in seen):
            varying.append(name)
        elif _said_in_a_word(seen[0]):
            constants.append((name, seen[0]))
    labels = [
        tuple(said.get(name) for name in varying) if len(varying) > 1 else said.get(varying[0])
        for said in ordered
    ] if varying else None
    return varying, labels, made, constants


def _said_in_a_word(value) -> bool:
    """A `%` value a note can say: a number, a word, a name, a short list of them. A table
    of the `%` layer (`num = {c: k + 1 ...}`) is bookkeeping, and ran a row to 1165 px."""
    if isinstance(value, (list, tuple)):
        return len(value) <= 6 and all(_said_in_a_word(item) for item in value)
    if isinstance(value, str):
        return len(value) <= 24
    return isinstance(value, (int, float, _SheetName))


def _in_the_order_they_ran(node: _ForBlock, values: list, kept: list, columns: list, helpers: list) -> Iterator:
    """What the passes showed, in order, but what the table holds, the assemblies, and each
    formula every pass wrote with only its subscripts changed - said once, as a rule, where
    its first pass stood."""
    from .renderer import formula_rules_latex  # noqa: PLC0415 - renderer imports models only

    runs: dict = {}
    for entry in kept:
        if entry.kind == "formula":
            runs.setdefault(entry.key, []).append(entry)
    once = {
        template for template, entries in runs.items()
        if [entry.index for entry in entries] == list(range(len(values)))
    }
    pending: list = []

    def rules():
        entries = [entry for template in pending for entry in runs[template]]
        names, labels, made, constants = _what_it_stands_on(pending, entries, helpers, order=_header_names(node))
        # What every pass of these lines said, once - not only the first pass's.
        said: list = []
        for entry in entries:
            said.extend(notice for notice in entry.notices if notice not in said)
        return ConditionNote(
            latex=formula_rules_latex(len(values), list(pending), names, labels, made, constants),
            notices=tuple(said),
        )

    for entry in kept:
        if entry.kind == "part" or (entry.kind == "cell" and entry.key in columns):
            continue
        if entry.kind == "formula" and entry.key in once:
            if entry.index == 0:
                pending.append(entry.key)
            continue
        if pending:
            yield rules()
            pending = []
        yield _as_it_ran(entry)
    if pending:
        yield rules()


def _worked_out(template: str, variable: list) -> bool:
    """Whether a `:=` line works its value out of the sheet's names - `t_{m} := 2*r_{m}*L_1` -
    rather than writes the loop's own value, `x_{n} := {x}[m]`, which the table already says."""
    right = template.split(":=", 1)[1] if ":=" in template else ""
    right = right.split("#", 1)[0]  # a comment is words, not names
    right = re.sub(r"\{([^{}]+)\}", lambda match: " " + match.group(1).strip() + " ", right)
    right = re.sub(r"\[[^\[\]]*\]", "", right)  # a unit in brackets
    names = set(re.findall(r"[A-Za-z_]\w*", right))
    return bool(names - set(variable))


def _helpers_of(node: _ForBlock) -> list:
    """The `%` helpers of a loop's own body and the names each makes: `% p, q = 2*m - 1, 2*m`."""
    made_by_helpers = []
    for child in node.body:
        if isinstance(child, _Helper):
            try:
                tree = ast.parse(child.code)
            except SyntaxError:
                continue
            made = {
                element.id
                for statement in tree.body
                if isinstance(statement, (ast.Assign, ast.AugAssign))
                for target in (statement.targets if isinstance(statement, ast.Assign) else [statement.target])
                for element in ast.walk(target)
                if isinstance(element, ast.Name)
            }
            made_by_helpers.append((child.code, made))
    return made_by_helpers


def _a_formula(item, result) -> bool:
    """`g_{ij} = [-c_{ij}; ...]`: a line of the loop's own that defines a name by a formula of
    names - what a pass shows is the rule with other subscripts. One that works out to a
    number keeps its rows: the number is what a reader would otherwise have to work out.
    So does one that reads its own name, `W = W + w_{i}`: each pass is a new value of it,
    and the rule alone never said what W came to."""
    from .models import EvaluationResult, ParsedStatement  # noqa: PLC0415 - models import nothing back

    if not (
        isinstance(item, ParsedStatement)
        and type(result) is EvaluationResult
        and item.target
        and item.parameters is None
        and item.target_index is None
        and item.declaration is None
    ):
        return False
    if any(isinstance(node, ast.Name) and node.id == item.target for node in ast.walk(item.expression.body)):
        return False
    # A rule is the same formula with other subscripts: its right side reads the loop's
    # values. One that reads none, or works something out - `t_{i} = subs(diff(y(x), x),
    # x, 0)` after a solve each pass - has a result of its own every pass (the audit of
    # 0.44.1: two different results were said by one rule, `subs` and all).
    template = getattr(item, "written_as", None) or item.source
    right = template.split("=", 1)[1] if "=" in template else ""
    if "{" not in right or re.search(r"\b(?:subs|diff|integrate|solve|numeric|simplify|expand|factor|limit)\s*\(", right):
        return False
    units = set(getattr(result, "unit_literals", ()) or ())
    symbols = getattr(result.value, "free_symbols", set())
    return any(
        symbol.name not in units and not symbol.name.startswith("__") for symbol in symbols
    )


def _assemblies(kept: list, helpers: list, settings, order=()) -> Iterator:
    """Each matrix a loop assembled: the rule of every line that added into it, once, and
    the matrix - or, wider than the page, what it is."""
    from .renderer import assembly_note_latex, fits_the_page, matrix_summary_latex  # noqa: PLC0415

    lines: dict = {}
    built: dict = {}
    for entry in kept:
        if entry.kind != "part":
            continue
        lines.setdefault(entry.key, []).append(entry)
        target = entry.key[0]
        _last, said = built.get(target, (None, []))
        said.extend(notice for notice in entry.notices if notice not in said)
        built[target] = (entry.result, said)
    for target, (result, said) in built.items():
        for (line_target, template), entries in lines.items():
            if line_target != target:
                continue
            # A line of a loop inside this one: its helpers are that loop's, not these.
            own = helpers if all(entry.direct for entry in entries) else []
            names, labels, made, constants = _what_it_stands_on([template], entries, own, order=order)
            yield ConditionNote(
                latex=assembly_note_latex(len(entries), template, names, labels, made, constants)
            )
        if getattr(getattr(result, "statement", None), "target_index", None) is not None:
            # A part assembled with `:=` is the matrix it landed in: its last pass's row,
            # `K_{[2,3],[2,3]} = ...`, read as if only that pass was added (the audit of
            # 0.45.3).
            statement = replace(
                result.statement,
                target_index=None,
                expression=ast.Expression(body=ast.Name(id=target, ctx=ast.Load())),
                matrix_literals=(),
            )
            result = replace(result, statement=statement)
        if fits_the_page(result, _current(settings)):
            yield Evaluated(result, tuple(said))
        else:
            # A matrix of numbers assembled with `:=` holds quantities, not a SymPy matrix:
            # its summary reads their numbers (a 12 x 12 assembly stopped the cell with an
            # AttributeError, his book, chapter 9).
            matrix = getattr(result, "value", None)
            if matrix is None:
                numbers = result.quantity_matrix
                matrix = sp.Matrix(
                    numbers.rows,
                    numbers.cols,
                    [
                        # An exact 0: SymPy's `Float(0.0) == 0` is False, and every zero
                        # counted as a term.
                        sp.Float(magnitude) if magnitude else sp.Integer(0)
                        for magnitude in (
                            float(entry.to_base_units().magnitude) for entry in numbers
                        )
                    ],
                )
            yield ConditionNote(latex=matrix_summary_latex(target, matrix), notices=tuple(said))


def _iterate(node: _WhileBlock, engine, settings, scope: _Scope) -> Iterator:
    """Run the body while the condition holds, and show only the last time it ran.

    Each iteration is worked out here, silently: an iteration nobody reads is not written.
    What the page gets is a sentence - how many iterations, and the condition as it stands
    now, which no longer holds - and then the rows of the last iteration.
    """
    count = 0
    last: list = []
    while True:
        condition = _with_placeholders(node.condition, node.line_no, scope)
        current = _in_scope(_condition_tree(condition, node.line_no), scope)
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
    # On a copy: a transformer rewrites the tree it is given, and a `% while` reads its
    # condition again after every pass - `k < 3` became `0 < 3` for good (2026-09-25).
    return _InScope(scope).visit(copy.deepcopy(tree))


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
        f"{_as_typed(tree)} is not a comparison"
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
    for (left, right), operator, (left_side, right_side) in zip(
        zip(values, values[1:]), tree.ops, zip(operands, operands[1:])
    ):
        first, second = left[0].quantity, right[0].quantity
        try:
            holds = _OPERATORS[type(operator)][2](first, second)
        except DimensionalityError as exc:
            # As the sheet writes it, each side in the unit the page would show: an entry of
            # kips said `0.5 * __u_m: m·kg/s² against m` (the audit of 0.46.1).
            raise EngEvaluationError(
                f"line {line_no}: the condition cannot compare {_as_typed(tree)}: "
                f"{_shown_units(first, left_side, settings, engine)} against "
                f"{_shown_units(second, right_side, settings, engine)}"
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

    side = copy.deepcopy(operand)
    whole = side if _a_numeric(side) else None
    side = _ItsValue(whole, lambda call: _value(call, line_no, engine)).visit(side)
    text = ast.unparse(side)
    try:
        result = _from_numbers(text, engine) if whole is None else None
        if result is None:
            (statement,) = parse_cell(text if whole is not None else f"numeric({text})")
            result = engine.evaluate(statement)
    except EngCalcError as exc:
        # The line is the condition's own, one line long, and not a line of the sheet.
        told = re.sub(r"^line \d+: ", "", str(exc))
        raise EngEvaluationError(f"line {line_no}: the condition needs a value for {_as_typed(side)}: {told}") from exc
    if not isinstance(result, NumericEvaluationResult):
        raise EngEvaluationError(f"line {line_no}: the condition needs one value for {text}")
    quantity = result.quantity
    written = None
    try:
        from .engine import _WrittenFormEvaluator  # noqa: PLC0415 - engine imports this module's users

        # A whole side `numeric(M(L_2))` is written as the call worked out, `q L_2^2/2`:
        # the call's own written form is the function's body, still in `x` (the third
        # audit, 2026-09-28). `numeric(M_2)` writes the formula of `M_2`, as it did.
        shown = side.args[0] if whole is not None and isinstance(side.args[0], ast.Call) else side
        written = _WrittenFormEvaluator(engine, ()).visit(shown)
    except Exception:  # noqa: BLE001 - the page then writes the number alone
        written = None
    if written is None and getattr(result, "statement", None) is not None and getattr(
        result.statement, "target", None
    ) == "eng_condition":
        written = _entries_written(side, engine)
    return result, written, getattr(result, "unit_literals", frozenset())


def _entries_written(side: ast.AST, engine):
    """`f[2]/f[1]` as the page writes it, `f_2/f_1`: each entry by its name, the rest names
    with values. `None` when anything else is in it, and the page writes the number alone."""
    from .engine import _entry_name  # noqa: PLC0415 - engine imports this module's users

    symbols: dict = {}

    class _Entries(ast.NodeTransformer):
        def visit_Subscript(self, node):
            name = _entry_name(node, engine)
            if name is None:
                return node
            key = f"eng_written_{len(symbols)}"
            symbols[key] = sp.Symbol(name)
            return ast.Name(id=key, ctx=ast.Load())

    tree = _Entries().visit(copy.deepcopy(side))
    if any(isinstance(each, ast.Subscript) for each in ast.walk(tree)) or not all(
        each.id in symbols or each.id in engine.numeric_context.values
        for each in ast.walk(tree)
        if isinstance(each, ast.Name)
    ):
        return None
    try:
        return sp.sympify(ast.unparse(tree), locals=symbols)
    except (sp.SympifyError, SyntaxError, TypeError):
        return None


def _from_numbers(text: str, engine):
    """A side that reads a matrix of numbers, `f[1]`, worked out as a `:=` line works it out.

    `numeric(f[1])` refuses a `:=` matrix, rightly for a formula, and the condition said
    "Use it on a := line" (his book, chapter 10: which hinge forms next). Nothing is
    assigned. `None` when the side reads no such matrix, and `numeric` answers as before.
    """
    from .engine import _MatrixNumbers, _a_matrix_in, one_number  # noqa: PLC0415 - engine imports this module's users
    from .matrix_numeric import NumberMatrix  # noqa: PLC0415
    from .models import NumericEvaluationResult  # noqa: PLC0415

    matrices = engine.numeric_context.matrices
    if not any(name in matrices for name in re.findall(r"[A-Za-z_]\w*", text)):
        return None
    (statement,) = parse_cell(f"eng_condition := {text}")
    numbers = _MatrixNumbers(engine, statement)
    body = statement.expression.body
    if not any(
        isinstance(each, ast.Name) and each.id in matrices and numbers.names_a_matrix(each.id)
        for each in ast.walk(body)
    ):
        return None
    value = one_number(numbers.value(body), engine.numeric_context.ureg)
    if isinstance(value, NumberMatrix):
        raise EngEvaluationError(
            f"{text} is a matrix; a condition compares one of its entries, such as "
            f"{_a_matrix_in(body, numbers)}[1]"
        )
    return NumericEvaluationResult(
        statement=statement,
        symbolic_expression=None,
        substitutions={},
        quantity=engine.numeric_context._as_quantity(value),
    )


# `0.5 * __u_m`, `10 * __u_kN / __u_m`, `6000 * __u_mm ** 2`: a number in brackets as
# the parser reads it.
_A_READ_BRACKET = re.compile(r"(\d[\w.]*) \* (__u_\w+(?: (?:\*|/) __u_\w+| \*\* \d+(?:\.\d+)?)*)")
# `2 * (3[m])`: the brackets ast.unparse keeps around a number in its unit.
_A_WRAPPED_BRACKET = re.compile(r"\((\d[\w.]*\[[^\[\]]*\])\)")


def _as_typed(tree: "ast.AST | str") -> str:
    """A comparison as the sheet writes it: `f[1] > 0.5[m]`, its units in brackets."""

    def bracket(match: re.Match) -> str:
        units = match.group(2).replace("__u_", "").replace(" ** ", "^").replace(" ", "")
        return f"{match.group(1)}[{units}]"

    # `3[m^0.5]` read `3[m^0].5` with a whole power only, and `2*3[m]` read `2 * (3[m])` (the
    # third audit of 0.46.2).
    text = ast.unparse(tree) if isinstance(tree, ast.AST) else tree
    return _A_WRAPPED_BRACKET.sub(r"\1", _A_READ_BRACKET.sub(bracket, text))


def said_as_typed(message: str) -> str:
    """A message as the sheet writes its units: the engine quotes a line from its tree,
    and `5[kN/m] - k` came out `'5 * __u_kN / __u_m - k' adds a number to a matrix`
    (0.47.1). A unit name standing alone keeps its name, without the prefix."""
    if "__u_" not in message:
        return message
    return _as_typed(message).replace("__u_", "")


_SI_BASE = frozenset({"meter", "kilogram", "second", "kelvin", "ampere", "mole", "candela", "radian"})


def _typed_number(side: ast.AST) -> bool:
    """A number in its unit as the sheet typed it, `0.5[kN/m]`: no name but the unit's."""
    return not any(
        isinstance(node, ast.Subscript) or (isinstance(node, ast.Name) and not node.id.startswith("__u_"))
        for node in ast.walk(side)
    )


def _shown_units(quantity, side: ast.AST, settings, engine=None) -> str:
    from .renderer import _display_quantity  # noqa: PLC0415 - renderer imports models only

    if quantity.dimensionless and not quantity.units._units:
        return "a number"  # it said nothing, `1 < P < 3[m]:  against kN`
    # A unit is said as it was typed, `0.5[kN/m]` in kN/m, `2400[kg/m^3]` in kg/m³, and a name
    # in the unit its definition wrote; what a matrix holds, or a name read from it
    # (`F := f[1]` of kips), in SI base units `m·kg/s²`, as the page would show it (the
    # third audit of 0.46.2).
    declared = isinstance(side, ast.Name) and engine is not None and side.id in engine.declared_unit_names
    if (
        not _typed_number(side) and not declared
        and len(quantity.units._units) > 1 and set(quantity.units._units) <= _SI_BASE
    ):
        current = settings() if callable(settings) else settings
        try:
            quantity = _display_quantity(quantity, current, declared=False)
        except Exception:  # noqa: BLE001 - a message is not refused for its units
            pass
    return f"{quantity.units:~P}"


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


def _current(settings):
    return settings() if callable(settings) else settings


def _gathers(body: list) -> bool:
    """Whether a `% for` has anything to show once: two `:=` lines of its own, or a line,
    its own or a loop's inside it, that adds into a part of a matrix.

    Not when it writes a heading or a paragraph of its own: those open each pass's rows,
    and gathered the rows would leave them standing over nothing ("Barra 2" with no bar
    under it). Not when a `% if` inside it assembles: its "Como ..." would be left without
    the row it decided.
    """
    if _writes_text(body) or _assembles_under_if(body):
        return False
    return len(_values_in(body)) >= 2 or _assembles(body)


def _writes_text(body: list) -> bool:
    for node in body:
        if isinstance(node, _Stretch):
            try:
                items = _parse_stretch(node, _PROBE)
            except EngCalcError:
                continue
            if any(type(item).__name__ in ("ParsedHeading", "ParsedNarrative") for item in items):
                return True
        elif isinstance(node, (_ForBlock, _WhileBlock)) and _writes_text(node.body):
            return True
        elif isinstance(node, _IfBlock) and any(_writes_text(branch.body) for branch in node.branches):
            return True
    return False


def _assembles_under_if(body: list) -> bool:
    for node in body:
        if isinstance(node, _IfBlock) and any(
            _assembles(branch.body) or _assembles_under_if(branch.body) for branch in node.branches
        ):
            return True
        if isinstance(node, _ForBlock) and _assembles_under_if(node.body):
            return True
    return False


def _assembles(body: list) -> bool:
    for node in body:
        if isinstance(node, _Stretch):
            try:
                items = _parse_stretch(node, _PROBE)
            except EngCalcError:
                continue  # said when the line runs
            if any(_adds_into_a_part(item) for item in items):
                return True
        elif isinstance(node, _ForBlock) and _assembles(node.body):
            return True
    return False


def _shown_as_it_comes(item) -> bool:
    """What a gathering loop passes on as it is: what `control` has already worked out, a
    heading, a paragraph."""
    return (
        isinstance(item, (ConditionNote, Evaluated))
        or not hasattr(item, "line_no")
        or type(item).__name__ in ("ParsedHeading", "ParsedNarrative")
    )


def _as_it_ran(entry: "_Kept"):
    if entry.item is not None:
        return entry.item
    return Evaluated(entry.result, entry.notices)


def _table_columns(kept: list) -> list:
    """The `:=` lines a loop's table holds: those whose every pass is a value of one kind
    of quantity. Two or more, or none - one line keeps its rows, as written by hand.

    A line whose passes are not all one quantity keeps its rows: a column has one unit,
    and 4 s under `a [m]` read as 4 m. A line written twice in the loop keeps its rows too:
    two columns of one name would say which is which by nothing but their order.
    """
    results: dict = {}
    for entry in kept:
        if entry.kind == "cell":
            results.setdefault(entry.key, []).append(entry.result)
    written_twice = {template for template, occurrence in results if occurrence}
    # A name the pass assigns again after its line - a `% while` inside the loop that
    # iterates it - is not that line's value at the end of the pass: tabulated, `r = 1.00`
    # stood beside the converged `s = 1.41` (his book, chapter 9). Its rows stay.
    def target(entry):
        # A line of the loop keeps its result; a line of a block inside it is kept as what
        # that block showed, `Evaluated(result)`, which has no pass of its own.
        result = entry.result if entry.result is not None else getattr(entry.item, "result", None)
        statement = getattr(result, "statement", None)
        return getattr(statement, "target", None)

    for position, entry in enumerate(kept):
        if entry.kind != "cell" or target(entry) is None:
            continue
        for later in kept[position + 1:]:
            if later.index != entry.index:
                break  # the next pass, whatever showed it first
            if later.key != entry.key and target(later) == target(entry):
                written_twice.add(entry.key[0])
                break
    columns = []
    for key, passes in results.items():
        if key[0] in written_twice or not all(_a_value(result) for result in passes):
            continue
        kinds = {str(getattr(result.quantity, "dimensionality", "")) for result in passes}
        if len(kinds) == 1:
            columns.append(key)
    return columns if len(columns) >= 2 else []


def _values_in(body: list) -> list[str]:
    """The `:=` lines of a loop's own stretches, as the sheet writes them."""
    from .models import ParsedNumericAssignment  # noqa: PLC0415 - models import nothing back

    lines = []
    for node in body:
        if isinstance(node, _Stretch):
            try:
                items = _parse_stretch(node, _PROBE)
            except EngCalcError:
                continue  # said when the line runs
            for item in items:
                if isinstance(item, ParsedNumericAssignment):
                    index = item.line_no - node.first_line
                    lines.append(node.lines[index].strip())
    return lines


def _a_value(result) -> bool:
    """A scalar `:=` value with nothing else to show: a cell of the loop's table."""
    from .models import NumericAssignmentResult  # noqa: PLC0415 - models import nothing back

    return (
        isinstance(result, NumericAssignmentResult)
        and getattr(result, "equation", None) is None
        and not getattr(result, "shown_as_written", False)
    )


def _adds_into_a_part(item) -> bool:
    """`K[[p, q], [p, q]] = K[[p, q], [p, q]] + ...`: a line that assembles into a matrix.

    It adds into the part it assigns - the same part, read as a term of the sum. A line
    that reads another part, `v[p] = 2*v[p - 1]`, is a recurrence, and each pass is a row.
    """
    target_index = getattr(item, "target_index", None)
    if target_index is None:
        return False
    wanted = ast.dump(target_index)

    def added(node):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return added(node.left) + added(node.right)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub):
            return added(node.left)
        return [node]

    body = item.expression.body
    if not (isinstance(body, ast.BinOp) and isinstance(body.op, (ast.Add, ast.Sub))):
        return False
    return any(
        isinstance(term, ast.Subscript)
        and isinstance(term.value, ast.Name)
        and term.value.id == item.target
        and ast.dump(term.slice) == wanted
        for term in added(body)
    )


def _written_target(template: str) -> str:
    """`L_{i}` of `L_{i} := ...`, the loop's name standing where a pass puts its value."""
    target = template.split(":=", 1)[0].strip()
    return re.sub(r"\{([^{}]+)\}", lambda match: "{" + match.group(1).strip() + "}", target)
