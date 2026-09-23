"""`interp(x, xs, ys)`: a value read from a table by linear interpolation.

The call stays on the page as it was written, the table with it, because the table is
what a reviewer holds the sheet against. The value is read by `numeric`, which finds the
two points around `x` (`NumericContext.interpolation_segment`) and draws the straight line
between them - and the page shows that segment worked out before the value.
"""

from __future__ import annotations

import sympy as sp


class Interpolation(sp.Function):
    """`interp(x, xs, ys)`: the point, then the table's points and its values as two
    one-row matrices. Never evaluated symbolically: a table read at a number is a
    number, and the page would lose the table."""

    nargs = 3

    @classmethod
    def eval(cls, point, points, values):
        return None

    def as_piecewise(self) -> sp.Piecewise:
        """The same function as one straight segment per pair of points.

        What `extrema` reads, because its piecewise analysis finds the extremes at the
        breakpoints, where the slope of a broken line jumps. Past the table it has no
        value, which is why `extrema` checks the domain against the table first.
        """
        point, points, values = self.args
        xs, ys = list(points), list(values)
        return sp.Piecewise(
            *(
                (
                    ys[i] + (ys[i + 1] - ys[i]) * (point - xs[i]) / (xs[i + 1] - xs[i]),
                    sp.Le(point, xs[i + 1]),
                )
                for i in range(len(xs) - 1)
            )
        )

    def _eval_derivative(self, symbol):
        # Unevaluated. SymPy's chain rule would differentiate the table's matrices too,
        # and that sends it into a recursion of its own (matrix `diff` through
        # `array_derivatives`), found by `plot`, which differentiates to mark extrema.
        # None leaves `Derivative(interp(...), x)` standing, and every analysis that
        # needs a slope falls back on the numbers, as it does for any function it
        # cannot differentiate.
        return None

    def _eval_is_commutative(self):
        # A scalar. SymPy infers commutativity from the arguments and a matrix is not
        # commutative - the same reason `ModeEigenvalue` says so itself.
        return True

    def _latex(self, printer):
        arguments = ", ".join(printer._print(argument) for argument in self.args)
        return rf"\operatorname{{interp}}\left({arguments}\right)"
