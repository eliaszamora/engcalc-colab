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


def matrix_eigenvals(value) -> EigenvalueSet:
    matrix = sp.ImmutableMatrix(_require_square(value, "eigenvals"))
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
