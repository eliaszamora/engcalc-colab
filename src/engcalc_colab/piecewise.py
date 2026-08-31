from __future__ import annotations

import ast

import sympy as sp

from .errors import EngEvaluationError, EngSyntaxError


_RELATION_BUILDERS = {
    ast.Lt: sp.StrictLessThan,
    ast.LtE: sp.LessThan,
    ast.Gt: sp.StrictGreaterThan,
    ast.GtE: sp.GreaterThan,
}


def build_relation(left: object, operator: ast.cmpop, right: object) -> sp.Rel:
    """Build one non-evaluating SymPy relation from the restricted AST comparator."""
    builder = _RELATION_BUILDERS.get(type(operator))
    if builder is None:
        raise EngEvaluationError("unsupported piecewise comparator")
    return builder(sp.sympify(left), sp.sympify(right), evaluate=False)


def build_piecewise(
    branches: tuple[tuple[object, object], ...],
    default: object,
) -> sp.Piecewise:
    """Build a Piecewise expression while preserving source branch order."""
    args = tuple(
        (sp.sympify(value), sp.sympify(condition))
        for value, condition in branches
    ) + ((sp.sympify(default), sp.true),)
    return sp.Piecewise(*args, evaluate=False)


def inspect_piecewise_variable(conditions: tuple[ast.Compare, ...]) -> str:
    """Return the one direct interval variable shared by all conditions."""
    if not conditions:
        raise EngSyntaxError("piecewise requires at least one condition")

    candidate_sets: list[set[str]] = []
    for condition in conditions:
        if len(condition.ops) != 1 or len(condition.comparators) != 1:
            raise EngSyntaxError("piecewise conditions must be binary comparisons")
        if type(condition.ops[0]) not in _RELATION_BUILDERS:
            raise EngSyntaxError("unsupported piecewise comparator")

        left = condition.left
        right = condition.comparators[0]
        candidates: set[str] = set()
        if isinstance(left, ast.Name) and not _contains_name(right, left.id):
            candidates.add(left.id)
        if isinstance(right, ast.Name) and not _contains_name(left, right.id):
            candidates.add(right.id)
        if not candidates:
            raise EngSyntaxError(
                "piecewise must compare an interval variable directly with a breakpoint expression"
            )
        candidate_sets.append(candidates)

    common = set.intersection(*candidate_sets)
    if len(common) != 1:
        raise EngSyntaxError("piecewise conditions must use one interval variable")
    return next(iter(common))


def extract_symbolic_breakpoints(
    expression: sp.Expr,
    variable: str,
) -> tuple[sp.Expr, ...]:
    """Return explicit direct breakpoints for ``variable`` in source traversal order."""
    expression = sp.sympify(expression)
    symbol = next(
        (item for item in expression.free_symbols if item.name == variable),
        sp.Symbol(variable, real=True),
    )
    breakpoints: list[sp.Expr] = []

    for piecewise in sp.preorder_traversal(expression):
        if not isinstance(piecewise, sp.Piecewise):
            continue
        for _, condition in piecewise.args:
            if condition is sp.true:
                continue
            if not isinstance(condition, sp.Rel):
                continue
            left, right = condition.lhs, condition.rhs
            breakpoint = None
            if left == symbol and symbol not in right.free_symbols:
                breakpoint = right
            elif right == symbol and symbol not in left.free_symbols:
                breakpoint = left
            if breakpoint is not None and breakpoint not in breakpoints:
                breakpoints.append(sp.sympify(breakpoint))

    return tuple(breakpoints)


def _contains_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(child, ast.Name) and child.id == name
        for child in ast.walk(node)
    )
