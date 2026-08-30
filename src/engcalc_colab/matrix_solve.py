from __future__ import annotations

import sympy as sp
from sympy.matrices.exceptions import NonInvertibleMatrixError

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

    try:
        solution = coefficient_matrix.LUsolve(rhs_matrix)
    except (NonInvertibleMatrixError, ValueError, ZeroDivisionError) as exc:
        raise EngEvaluationError(
            "solve matrix system requires a unique solution"
        ) from exc

    return sp.ImmutableMatrix(solution)
