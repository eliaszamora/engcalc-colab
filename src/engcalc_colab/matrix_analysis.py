from __future__ import annotations

import sympy as sp

from .errors import EngEvaluationError
from .models import (
    EigenvalueEntry,
    EigenvalueSet,
    EigenvectorEntry,
    EigenvectorSet,
)


def _require_matrix(value, operation: str) -> sp.MatrixBase:
    if not isinstance(value, sp.MatrixBase):
        raise EngEvaluationError(f"{operation} requires a matrix")
    return value


def _require_square(value, operation: str) -> sp.MatrixBase:
    matrix = _require_matrix(value, operation)
    if matrix.rows != matrix.cols:
        raise EngEvaluationError(f"{operation} requires a square matrix")
    return matrix


def matrix_rank(value):
    return _require_matrix(value, "rank").rank()


def matrix_rref(value) -> sp.ImmutableMatrix:
    reduced, _pivots = _require_matrix(value, "rref").rref()
    return sp.ImmutableMatrix(reduced)


def matrix_norm(value):
    matrix = _require_matrix(value, "norm")
    terms = tuple(sp.Abs(entry) ** 2 for entry in matrix)
    return sp.simplify(sp.sqrt(sp.Add(*terms)))


def _seeks_no_closed_form(matrix: sp.MatrixBase) -> bool:
    """Three rows or more, and names in the entries.

    The frequency equation of such a matrix is a polynomial of degree three or more in
    those names. A cubic with three real roots - a shear building's always has them - is
    written in radicals only through complex numbers, so the formula SymPy found could
    not be evaluated, and a quartic took 81 s and 760 KB of page to fail differently.
    Nobody reads those formulas; the modes are computed from the numbers, which is what
    `numeric(...)` now does. A two-by-two keeps its quadratic, and a matrix of plain
    numbers keeps SymPy's exact answer.
    """
    return matrix.rows >= 3 and bool(matrix.free_symbols)


def matrix_eigenvals(value) -> EigenvalueSet:
    matrix = sp.ImmutableMatrix(_require_square(value, "eigenvals"))
    if _seeks_no_closed_form(matrix):
        return EigenvalueSet(entries=(), source_matrix=matrix, closed_form=False)
    eigenvalues = matrix.eigenvals()
    entries = tuple(
        EigenvalueEntry(value=eigenvalue, multiplicity=int(multiplicity))
        for eigenvalue, multiplicity in sorted(
            eigenvalues.items(),
            key=lambda item: sp.default_sort_key(item[0]),
        )
    )
    return EigenvalueSet(entries=entries, source_matrix=matrix)


def matrix_eigenvects(value) -> EigenvectorSet:
    matrix = sp.ImmutableMatrix(_require_square(value, "eigenvects"))
    if _seeks_no_closed_form(matrix):
        return EigenvectorSet(entries=(), source_matrix=matrix, closed_form=False)
    raw_entries = sorted(
        matrix.eigenvects(),
        key=lambda item: sp.default_sort_key(item[0]),
    )
    entries = tuple(
        EigenvectorEntry(
            value=eigenvalue,
            multiplicity=int(multiplicity),
            vectors=tuple(sp.ImmutableMatrix(vector) for vector in vectors),
        )
        for eigenvalue, multiplicity, vectors in raw_entries
    )
    return EigenvectorSet(entries=entries, source_matrix=matrix)
