from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator

from pint.errors import DimensionalityError

from .errors import EngEvaluationError


@dataclass(frozen=True)
class QuantityMatrix:
    """Immutable Pint-valued matrix result; symbolic algebra remains owned by SymPy."""

    rows: int
    cols: int
    entries: tuple[Any, ...]
    adaptable_zeros: frozenset[tuple[int, int]] = frozenset()

    def __post_init__(self) -> None:
        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("QuantityMatrix dimensions must be positive")
        normalized_entries = tuple(self.entries)
        if len(normalized_entries) != self.rows * self.cols:
            raise ValueError("QuantityMatrix entry count does not match shape")
        normalized_zeros = frozenset(self.adaptable_zeros)
        for row, col in normalized_zeros:
            if not (0 <= row < self.rows and 0 <= col < self.cols):
                raise ValueError("QuantityMatrix adaptable zero is outside matrix shape")
        object.__setattr__(self, "entries", normalized_entries)
        object.__setattr__(self, "adaptable_zeros", normalized_zeros)

    def entry(self, row: int, col: int):
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise IndexError("QuantityMatrix entry index out of range")
        return self.entries[row * self.cols + col]

    def __iter__(self) -> Iterator[Any]:
        return iter(self.entries)


def ensure_common_scale(quantity_matrix: QuantityMatrix, operation: str):
    """Return the common Pint unit, or None for dimensionless matrices.

    Numerical zero is neutral. Nonzero physical entries must all be convertible
    to one unit, and nonzero dimensionless entries may not mix with them.
    """
    common_unit = None
    saw_dimensionless_nonzero = False

    for quantity in quantity_matrix:
        if float(quantity.magnitude) == 0.0:
            continue
        if quantity.dimensionless:
            if common_unit is not None:
                raise EngEvaluationError(
                    f"matrix operation '{operation}' requires a dimensionless or common-scale matrix"
                )
            saw_dimensionless_nonzero = True
            continue

        if saw_dimensionless_nonzero:
            raise EngEvaluationError(
                f"matrix operation '{operation}' requires a dimensionless or common-scale matrix"
            )
        if common_unit is None:
            common_unit = quantity.units
            continue
        try:
            quantity.to(common_unit)
        except DimensionalityError as exc:
            raise EngEvaluationError(
                f"matrix operation '{operation}' requires a dimensionless or common-scale matrix"
            ) from exc

    return common_unit


# --- `d := solve(K, F)`: matrices worked out in numbers --------------------------------
#
# A `:=` line over matrices is arithmetic on numbers, and each entry of a structural
# matrix has a unit of its own: a stiffness mixes kN/m, kN and kN*m, and the solution
# mixes metres with rotations that have none. The entries are held in base units, so the
# magnitudes can be added and multiplied as plain floats, with one unit per entry kept
# beside them and checked wherever two terms meet.
#
# `None` is the zero written as `0`: an exact zero with no unit of its own, which takes
# the unit of whatever it meets. It is the adaptable zero of `QuantityMatrix`, and it is
# what lets `[K_jj, Z; Z, K_jj]` and `[0; 0; 0; d[1,1]; ...]` be written at all.
#
# mpmath and not numpy for the reason `matrix_modes` gives: SymPy depends on it.


# The calls a `:=` line works out on matrices. One list: the engine evaluates them and
# the renderer sets them apart as matrices, and a call added to one must be in both.
MATRIX_CALLS = ("solve", "inv", "transpose")


@dataclass(frozen=True)
class NumberMatrix:
    rows: int
    cols: int
    magnitudes: tuple[float, ...]
    units: tuple[Any, ...]

    def at(self, row: int, col: int) -> tuple[float, Any]:
        index = row * self.cols + col
        return self.magnitudes[index], self.units[index]

    @property
    def shape(self) -> str:
        return f"{self.rows}x{self.cols}"


def _same_dimension(left, right) -> bool:
    return (1 * left).dimensionality == (1 * right).dimensionality


def _unit_text(unit) -> str:
    return f"{unit:~P}" or "no unit"


def numbers_of(quantity_matrix: QuantityMatrix) -> NumberMatrix:
    magnitudes = []
    units = []
    for index, quantity in enumerate(quantity_matrix):
        position = divmod(index, quantity_matrix.cols)
        if float(quantity.magnitude) == 0.0 and (
            position in quantity_matrix.adaptable_zeros or quantity.dimensionless
        ):
            magnitudes.append(0.0)
            units.append(None)
            continue
        base = quantity.to_base_units()
        magnitudes.append(float(base.magnitude))
        units.append(base.units)
    return NumberMatrix(
        quantity_matrix.rows, quantity_matrix.cols, tuple(magnitudes), tuple(units)
    )


def scalar_numbers(quantity) -> NumberMatrix:
    """A number as a one-by-one matrix: a cell of `[a; b]`, or a factor to scale by."""
    if float(quantity.magnitude) == 0.0 and quantity.dimensionless:
        return NumberMatrix(1, 1, (0.0,), (None,))
    base = quantity.to_base_units()
    return NumberMatrix(1, 1, (float(base.magnitude),), (base.units,))


def quantity_matrix_of(numbers: NumberMatrix, ureg) -> QuantityMatrix:
    entries = []
    zeros = set()
    for index, (magnitude, unit) in enumerate(zip(numbers.magnitudes, numbers.units)):
        if unit is None:
            zeros.add(divmod(index, numbers.cols))
            entries.append(ureg.Quantity(0, ureg.dimensionless))
        else:
            entries.append(ureg.Quantity(magnitude, unit))
    return QuantityMatrix(numbers.rows, numbers.cols, tuple(entries), frozenset(zeros))


def entry_quantity(numbers: NumberMatrix, row: int, col: int, ureg):
    """One entry, as the scalar a `:=` line goes on with. The unitless zero is a plain
    `0`, which Pint adds to any quantity, as the written `0` it stands for would be."""
    magnitude, unit = numbers.at(row, col)
    if unit is None:
        return 0
    return ureg.Quantity(magnitude, unit)


def _sum_unit(first, second, where: str):
    if first is None:
        return second
    if second is None:
        return first
    if not _same_dimension(first, second):
        raise EngEvaluationError(
            f"incompatible units at {where}: {_unit_text(first)} and {_unit_text(second)}"
        )
    return first


def add_numbers(left: NumberMatrix, right: NumberMatrix, sign: int = 1) -> NumberMatrix:
    if (left.rows, left.cols) != (right.rows, right.cols):
        verb = "added to" if sign > 0 else "subtracted from"
        raise EngEvaluationError(
            f"a {right.shape} matrix cannot be {verb} a {left.shape} matrix"
        )
    magnitudes = []
    units = []
    for index in range(left.rows * left.cols):
        row, col = divmod(index, left.cols)
        units.append(
            _sum_unit(left.units[index], right.units[index], f"[{row + 1},{col + 1}]")
        )
        magnitudes.append(left.magnitudes[index] + sign * right.magnitudes[index])
    return NumberMatrix(left.rows, left.cols, tuple(magnitudes), tuple(units))


def scale_numbers(numbers: NumberMatrix, factor) -> NumberMatrix:
    """Every entry times a scalar quantity; the unitless zero stays one."""
    base = factor.to_base_units()
    magnitude, unit = float(base.magnitude), base.units
    return NumberMatrix(
        numbers.rows,
        numbers.cols,
        tuple(value * magnitude for value in numbers.magnitudes),
        tuple(None if each is None else each * unit for each in numbers.units),
    )


def _product_units(left_units, right_units, rows: int, inner: int, cols: int):
    """The unit of each entry of a product, checked term by term."""
    units = []
    for row in range(rows):
        for col in range(cols):
            unit = None
            for k in range(inner):
                a = left_units[row * inner + k]
                b = right_units[k * cols + col]
                if a is None or b is None:
                    continue
                unit = _sum_unit(unit, a * b, f"[{row + 1},{col + 1}]")
            units.append(unit)
    return units


def multiply_numbers(left: NumberMatrix, right: NumberMatrix) -> NumberMatrix:
    if left.cols != right.rows:
        raise EngEvaluationError(
            f"a {left.shape} matrix times a {right.shape} matrix: the columns of the "
            "first must be as many as the rows of the second"
        )
    magnitudes = tuple(
        sum(
            left.magnitudes[row * left.cols + k] * right.magnitudes[k * right.cols + col]
            for k in range(left.cols)
        )
        for row in range(left.rows)
        for col in range(right.cols)
    )
    units = _product_units(left.units, right.units, left.rows, left.cols, right.cols)
    return NumberMatrix(left.rows, right.cols, magnitudes, tuple(units))


def transpose_numbers(numbers: NumberMatrix) -> NumberMatrix:
    order = [
        row * numbers.cols + col
        for col in range(numbers.cols)
        for row in range(numbers.rows)
    ]
    return NumberMatrix(
        numbers.cols,
        numbers.rows,
        tuple(numbers.magnitudes[i] for i in order),
        tuple(numbers.units[i] for i in order),
    )


def _misfit(operation: str, row: int, col: int) -> EngEvaluationError:
    return EngEvaluationError(
        f"matrix operation '{operation}': the unit of entry [{row + 1},{col + 1}] does "
        "not fit the rest of the matrix, so it has no inverse with units"
    )


def _inverse_units(numbers: NumberMatrix, operation: str) -> list[Any]:
    """The unit of each entry of the inverse of a square matrix of numbers.

    A matrix with an inverse that has units has a unit `r_i` for each row and `c_k` for
    each column with entry [i,k] = r_i / c_k - a stiffness has a force or a moment per
    row and a displacement or a rotation per column - and the inverse's entry [k,j] is
    then c_k / r_j. They are found by walking the nonzero entries from one row; each
    connected group of rows and columns fixes its own scale, which cancels in c_k / r_j,
    and entries between two groups are zeros of the inverse.
    """
    size = numbers.rows
    row_units: list[Any] = [None] * size
    col_units: list[Any] = [None] * size
    row_group = [-1] * size
    col_group = [-1] * size
    seed = next((unit for unit in numbers.units if unit is not None), None)
    for start in range(size):
        if seed is None or row_group[start] != -1:
            continue
        row_units[start] = seed / seed
        row_group[start] = start
        pending = [("row", start)]
        while pending:
            kind, index = pending.pop()
            for other in range(size):
                if kind == "row":
                    unit = numbers.units[index * size + other]
                    if unit is None:
                        continue
                    implied = row_units[index] / unit
                    if col_group[other] == -1:
                        col_units[other], col_group[other] = implied, start
                        pending.append(("col", other))
                    elif not _same_dimension(implied, col_units[other]):
                        raise _misfit(operation, index, other)
                else:
                    unit = numbers.units[other * size + index]
                    if unit is None:
                        continue
                    implied = unit * col_units[index]
                    if row_group[other] == -1:
                        row_units[other], row_group[other] = implied, start
                        pending.append(("row", other))
                    elif not _same_dimension(implied, row_units[other]):
                        raise _misfit(operation, other, index)
    return [
        None
        if col_group[k] == -1 or col_group[k] != row_group[j]
        else col_units[k] / row_units[j]
        for k in range(size)
        for j in range(size)
    ]


def _square(numbers: NumberMatrix, operation: str) -> None:
    if numbers.rows != numbers.cols:
        raise EngEvaluationError(
            f"matrix operation '{operation}' requires a square matrix, not {numbers.shape}"
        )


def _mp_matrix(numbers: NumberMatrix):
    import mpmath

    return mpmath.matrix(
        [
            [numbers.magnitudes[row * numbers.cols + col] for col in range(numbers.cols)]
            for row in range(numbers.rows)
        ]
    )


def _singular(operation: str) -> EngEvaluationError:
    return EngEvaluationError(
        f"matrix operation '{operation}': the matrix is singular - check the supports "
        "and that every degree of freedom has a stiffness"
    )


def inverse_numbers(numbers: NumberMatrix) -> NumberMatrix:
    import mpmath

    _square(numbers, "inv")
    units = _inverse_units(numbers, "inv")
    try:
        inverse = mpmath.inverse(_mp_matrix(numbers))
    except ZeroDivisionError as exc:
        raise _singular("inv") from exc
    size = numbers.rows
    magnitudes = tuple(
        0.0 if units[k * size + j] is None else float(inverse[k, j])
        for k in range(size)
        for j in range(size)
    )
    return NumberMatrix(size, size, magnitudes, tuple(units))


def solve_numbers(matrix: NumberMatrix, right: NumberMatrix) -> NumberMatrix:
    import mpmath

    _square(matrix, "solve")
    if right.rows != matrix.rows:
        raise EngEvaluationError(
            f"solve of a {matrix.shape} matrix needs a right-hand side with "
            f"{matrix.rows} rows, not {right.shape}"
        )
    inverse_units = _inverse_units(matrix, "solve")
    units = _product_units(inverse_units, right.units, matrix.rows, matrix.rows, right.cols)
    system = _mp_matrix(matrix)
    columns = []
    for col in range(right.cols):
        rhs = mpmath.matrix(
            [right.magnitudes[row * right.cols + col] for row in range(right.rows)]
        )
        try:
            columns.append(mpmath.lu_solve(system, rhs))
        except ZeroDivisionError as exc:
            raise _singular("solve") from exc
    magnitudes = tuple(
        0.0 if units[row * right.cols + col] is None else float(columns[col][row])
        for row in range(matrix.rows)
        for col in range(right.cols)
    )
    return NumberMatrix(matrix.rows, right.cols, magnitudes, tuple(units))


def take_numbers(numbers: NumberMatrix, rows: list[int], cols: list[int]) -> NumberMatrix:
    indices = [row * numbers.cols + col for row in rows for col in cols]
    return NumberMatrix(
        len(rows),
        len(cols),
        tuple(numbers.magnitudes[i] for i in indices),
        tuple(numbers.units[i] for i in indices),
    )


def blocks_of_numbers(block_rows: list[list[NumberMatrix]]) -> NumberMatrix:
    """`[K_jj, Z; Z, K_jj]`: matrices and numbers put side by side and one under another."""
    magnitudes: list[float] = []
    units: list[Any] = []
    width = None
    height = 0
    for blocks in block_rows:
        rows = blocks[0].rows
        if any(block.rows != rows for block in blocks):
            raise EngEvaluationError(
                "the blocks of one row of a matrix must have as many rows as each other"
            )
        cols = sum(block.cols for block in blocks)
        if width is None:
            width = cols
        elif cols != width:
            raise EngEvaluationError(
                "the rows of a matrix must have as many columns as each other"
            )
        for row in range(rows):
            for block in blocks:
                start = row * block.cols
                magnitudes.extend(block.magnitudes[start:start + block.cols])
                units.extend(block.units[start:start + block.cols])
        height += rows
    return NumberMatrix(height, width, tuple(magnitudes), tuple(units))
