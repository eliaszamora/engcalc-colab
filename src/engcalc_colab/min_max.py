"""`min` and `max` in the order they were written.

SymPy's `Min` and `Max` sort their arguments, so `min(L/4, b_w + 16*h_f, s)` - the flange
a T-beam may count on, as the code gives it - printed `min(L/4, s, b_w + 16 h_f)`. The
value is right and the formula is no longer the code's.

These are SymPy's own, with the arguments put back in the order they were typed and
nothing else changed: a derivative, a substitution, a Piecewise rewrite or an integral
treats them as SymPy does, because they are its `Min` and `Max`.
"""

from __future__ import annotations

import sympy as sp
from sympy.core.expr import Expr


def _in_written_order(cls, lattice, args):
    """`lattice(*args)`, then its surviving arguments in the order they were written.

    The real `Min` or `Max` is built first and only its argument order is changed.
    Building through the subclass instead gets `max(3, 5) = 3`: SymPy's lattice logic
    asks `cls is Max`, and a subclass answers no.
    """
    written = [sp.sympify(arg) for arg in args]
    result = lattice(*written)
    if not isinstance(result, lattice):
        # A single survivor - `max(3, 5)`, `max(x, x)` - is that value, not a call.
        return result
    place: dict = {}
    for index, arg in enumerate(written):
        place.setdefault(arg, index)
    ordered = sorted(result.args, key=lambda arg: place.get(arg, len(written)))
    obj = Expr.__new__(cls, *ordered)
    obj._argset = frozenset(ordered)
    return obj


def _latex(expr, printer, name: str) -> str:
    return rf"\{name}\left({', '.join(printer._print(arg) for arg in expr.args)}\right)"


class WrittenMax(sp.Max):
    """`max(...)`: SymPy's `Max`, its arguments where they were typed."""

    def __new__(cls, *args, **assumptions):
        return _in_written_order(cls, sp.Max, args)

    def _latex(self, printer):
        return _latex(self, printer, "max")


class WrittenMin(sp.Min):
    """`min(...)`: SymPy's `Min`, its arguments where they were typed."""

    def __new__(cls, *args, **assumptions):
        return _in_written_order(cls, sp.Min, args)

    def _latex(self, printer):
        return _latex(self, printer, "min")
