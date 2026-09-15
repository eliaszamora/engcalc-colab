"""Eigenvalues and mode shapes computed from numbers.

The symbolic layer seeks no closed form for a matrix of three rows or more with names in
it (see `matrix_analysis._seeks_no_closed_form`), and this is where `numeric(...)` gets the
answer instead: from the matrix the sheet built, evaluated, in the one unit its entries
share.

`mpmath`, because SymPy depends on it and so it is always there; numpy is only there
because matplotlib happens to need it.
"""

from __future__ import annotations

from dataclasses import dataclass

import mpmath

from .errors import EngEvaluationError

# Two eigenvalues this close, relative to their size, are one eigenvalue counted twice.
# Floating point splits a repeated root by about the machine epsilon times the condition
# of the problem; a real pair of distinct modes is never within a part in a billion.
_SAME_EIGENVALUE = 1e-9

# The imaginary part a real eigenvalue picks up from rounding, relative to the real one.
_REAL_EIGENVALUE = 1e-9


@dataclass(frozen=True)
class NumericMode:
    value: float
    multiplicity: int
    vectors: tuple[tuple[float, ...], ...]


def _normalised(vector: list[float]) -> tuple[float, ...]:
    """Scaled so the last entry is one - the way SymPy's own nullspace writes the
    two-storey mode `[0.56; 1.00]` - or, when the last entry is zero, the largest."""
    largest = max(abs(entry) for entry in vector)
    if largest == 0.0:
        return tuple(vector)
    pivot = vector[-1] if abs(vector[-1]) > _SAME_EIGENVALUE * largest else max(
        vector, key=abs
    )
    return tuple(entry / pivot for entry in vector)


def numeric_modes(magnitudes: list[list[float]], *, operation: str) -> tuple[NumericMode, ...]:
    """The eigenvalues of a square matrix of plain numbers, ascending, with multiplicity
    and one normalised eigenvector per multiplicity."""
    size = len(magnitudes)
    values, right = mpmath.eig(mpmath.matrix(magnitudes))

    pairs = []
    for index, value in enumerate(values):
        real = float(mpmath.re(value))
        imaginary = float(mpmath.im(value))
        if abs(imaginary) > _REAL_EIGENVALUE * max(abs(real), 1.0):
            raise EngEvaluationError(
                f"{operation} has complex eigenvalues, which numeric evaluation does not "
                "support; a stiffness and a mass matrix give real ones"
            )
        vector = [float(mpmath.re(right[row, index])) for row in range(size)]
        pairs.append((real, vector))
    pairs.sort(key=lambda pair: pair[0])

    modes: list[NumericMode] = []
    group: list[tuple[float, list[float]]] = []
    for pair in pairs:
        if group and abs(pair[0] - group[0][0]) > _SAME_EIGENVALUE * max(
            abs(pair[0]), abs(group[0][0]), 1e-300
        ):
            modes.append(_mode(group))
            group = []
        group.append(pair)
    if group:
        modes.append(_mode(group))
    return tuple(modes)


def _mode(group: list[tuple[float, list[float]]]) -> NumericMode:
    return NumericMode(
        value=sum(value for value, _ in group) / len(group),
        multiplicity=len(group),
        vectors=tuple(_normalised(vector) for _, vector in group),
    )
