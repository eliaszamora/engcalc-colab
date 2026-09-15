from __future__ import annotations

import sympy as sp

from .errors import EngEvaluationError


def solve_linear_system(
    matrix: sp.MatrixBase,
    rhs: sp.MatrixBase,
) -> sp.ImmutableMatrix:
    """Solve an exact square linear system A*x=b and return an immutable column matrix."""
    if not isinstance(matrix, sp.MatrixBase):
        raise EngEvaluationError("solve matrix A must be a matrix")

    coefficient_matrix = sp.ImmutableMatrix(matrix)
    if coefficient_matrix.rows != coefficient_matrix.cols:
        raise EngEvaluationError("solve matrix A must be square")

    if not isinstance(rhs, sp.MatrixBase) or rhs.cols != 1:
        raise EngEvaluationError("solve matrix rhs must be a column vector")

    rhs_matrix = sp.ImmutableMatrix(rhs)
    if rhs_matrix.rows != coefficient_matrix.rows:
        raise EngEvaluationError("solve matrix rhs row count must match A")

    # `linsolve`, and each unknown factored. `LUsolve` returned the steps of Gaussian
    # elimination unsimplified: two springs printed their first displacement as a
    # fraction of fractions of fractions where `inv(K)*F` printed `15 kN/k₁`, and six
    # degrees of freedom ran to 6028 characters. `linsolve` eliminates without nesting
    # them - 488 characters in 0.05 s at six - where factoring the LU answer took 2.2 s,
    # Gauss-Jordan 36 s, and the adjugate 0.8 s to reach the same form.
    unknowns = sp.symbols(f"__solve_unknown_1:{coefficient_matrix.rows + 1}")
    # No `try`: the shape checks above are everything `linsolve` raises on, and a guard
    # around it survived mutation - a singular system comes back as an empty set or a
    # line of solutions, both refused below.
    solutions = sp.linsolve((coefficient_matrix, rhs_matrix), *unknowns)
    if not isinstance(solutions, sp.FiniteSet) or len(solutions) != 1:
        raise EngEvaluationError("solve matrix system requires a unique solution")
    (solution,) = solutions
    if any(symbol in unknowns for entry in solution for symbol in sp.sympify(entry).free_symbols):
        # A free unknown in the answer is a line of solutions, not one.
        raise EngEvaluationError("solve matrix system requires a unique solution")

    return sp.ImmutableMatrix([[sp.factor(entry)] for entry in solution])
