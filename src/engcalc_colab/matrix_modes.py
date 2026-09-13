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
import sympy as sp

from .errors import EngEvaluationError
from .matrix_numeric import QuantityMatrix, ensure_common_scale
from .models import EigenvalueSet, EigenvectorSet

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


def modes_of(quantity_matrix: QuantityMatrix, *, operation: str):
    """The modes of a matrix of quantities, and the unit its eigenvalues carry - the one
    unit its entries share, or None for a matrix of plain numbers."""
    scale = ensure_common_scale(quantity_matrix, operation)
    magnitudes = [
        [
            float(
                quantity.to(scale).magnitude
                if scale is not None and not quantity.dimensionless
                else quantity.to_base_units().magnitude
            )
            for quantity in (
                quantity_matrix.entry(row, col) for col in range(quantity_matrix.cols)
            )
        ]
        for row in range(quantity_matrix.rows)
    ]
    return numeric_modes(magnitudes, operation=operation), scale


class ModeEigenvalue(sp.Function):
    r"""`lam[i]`: the i-th eigenvalue of a matrix, ascending, a repeated one counted as
    many times as it repeats. Written `\lambda_{i}` and computed from the numbers - the
    closed form of even a two-by-two is a quadratic formula, and a matrix of three rows
    has none. Arguments: the index, then the matrix."""

    nargs = 2

    @classmethod
    def eval(cls, index, matrix):
        return None

    def _eval_is_commutative(self):
        # A scalar. SymPy infers commutativity from the arguments and a matrix is not
        # commutative, so `2*pi/sqrt(lam[1])` printed `2 π · 1/√λ₁`: a non-commutative
        # factor is never moved below a fraction bar.
        return True


class ModeShapeEntry(sp.Function):
    r"""Row `j` of `phi[i]`, the i-th mode shape, scaled as the list of modes scales it.
    Written `\phi_{j,i}`. Arguments: the mode, the row, then the matrix."""

    nargs = 3

    @classmethod
    def eval(cls, mode, row, matrix):
        return None

    def _eval_is_commutative(self):
        return True


def take_mode(value: EigenvalueSet | EigenvectorSet, indices: tuple[object, ...]):
    """What `lam[i]` and `phi[i]` stand for, before any number is known."""
    if len(indices) != 1:
        raise EngEvaluationError(
            "a mode is taken with one index: lam[1] for the first eigenvalue, "
            "phi[2] for the second mode shape"
        )
    index = indices[0]
    if not isinstance(index, sp.Integer) or index <= 0:
        raise EngEvaluationError("a mode number must be a positive integer")
    matrix = value.source_matrix
    if int(index) > matrix.rows:
        raise EngEvaluationError(
            f"mode {int(index)} does not exist: a {matrix.rows}x{matrix.cols} matrix has "
            f"{matrix.rows} modes"
        )
    if isinstance(value, EigenvalueSet):
        return ModeEigenvalue(index, matrix)
    return sp.ImmutableMatrix(
        [[ModeShapeEntry(index, sp.Integer(row), matrix)] for row in range(1, matrix.rows + 1)]
    )


def mode_key(expr) -> str:
    """Where a mode's value is kept among a numeric result's substitutions, so the
    substitution stage writes `(897.61 1/s²)` for `λ₁` the way it writes `(3.70 m)` for a
    name. Not a name, so it cannot collide with one."""
    return "mode:" + sp.srepr(expr)


def mode_atoms(expr) -> set:
    """The modes an expression or matrix takes."""
    return set(sp.sympify(expr).atoms(ModeEigenvalue, ModeShapeEntry))


def numbered(modes: tuple[NumericMode, ...]) -> tuple[list[float], list[tuple[float, ...]]]:
    """The eigenvalues and mode shapes one per mode number, a repeated one repeated."""
    values = [mode.value for mode in modes for _ in mode.vectors]
    vectors = [vector for mode in modes for vector in mode.vectors]
    return values, vectors
