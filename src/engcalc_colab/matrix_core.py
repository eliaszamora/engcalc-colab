from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from .errors import EngEvaluationError


def is_matrix(value: object) -> bool:
    return isinstance(value, sp.MatrixBase)


def _immutable(value):
    if isinstance(value, sp.MatrixBase):
        return sp.ImmutableMatrix(value)
    return value


def _shape(value: sp.MatrixBase) -> str:
    return f"{value.rows}x{value.cols}"


def build_matrix(rows) -> sp.ImmutableMatrix:
    if any(is_matrix(cell) for row in rows for cell in row):
        return _build_from_blocks(rows)
    normalized = []
    for row in rows:
        normalized_row = []
        for cell in row:
            normalized_row.append(sp.sympify(cell))
        normalized.append(normalized_row)
    return sp.ImmutableMatrix(normalized)


def _build_from_blocks(rows) -> sp.ImmutableMatrix:
    """`[r, zeros(3, 3); zeros(3, 3), r]`: a row places its blocks side by side, and the
    rows are stacked. A scalar among blocks is a 1x1 block. A frame element's rotation is
    its nodal block twice down a diagonal, and an element stiffness is four quadrants;
    until this a literal with a matrix in it was refused, so both had to be typed out."""
    stacked = []
    for number, row in enumerate(rows, start=1):
        blocks = [
            sp.ImmutableMatrix(cell) if is_matrix(cell) else sp.ImmutableMatrix([[sp.sympify(cell)]])
            for cell in row
        ]
        heights = [block.rows for block in blocks]
        if len(set(heights)) != 1:
            raise EngEvaluationError(
                f"row {number} of the matrix has blocks "
                + " and ".join(str(height) for height in heights)
                + " rows tall; the blocks of a row must be as tall as each other"
            )
        joined = blocks[0]
        for block in blocks[1:]:
            joined = joined.row_join(block)
        stacked.append(joined)
    widths = [row.cols for row in stacked]
    if len(set(widths)) != 1:
        raise EngEvaluationError(
            "the rows of the matrix are "
            + " and ".join(str(width) for width in widths)
            + " columns wide; each row of blocks must be as wide as the others"
        )
    result = stacked[0]
    for row in stacked[1:]:
        result = result.col_join(row)
    return sp.ImmutableMatrix(result)


def matrix_add(left, right):
    left_matrix = is_matrix(left)
    right_matrix = is_matrix(right)
    if not left_matrix and not right_matrix:
        return left + right
    if not (left_matrix and right_matrix):
        raise EngEvaluationError(
            "matrix addition requires two matrices with the same shape"
        )
    if left.shape != right.shape:
        raise EngEvaluationError(
            "matrix addition dimension mismatch: "
            f"left is {_shape(left)}, right is {_shape(right)}"
        )
    return _immutable(left + right)


def matrix_subtract(left, right):
    left_matrix = is_matrix(left)
    right_matrix = is_matrix(right)
    if not left_matrix and not right_matrix:
        return left - right
    if not (left_matrix and right_matrix):
        raise EngEvaluationError(
            "matrix subtraction requires two matrices with the same shape"
        )
    if left.shape != right.shape:
        raise EngEvaluationError(
            "matrix subtraction dimension mismatch: "
            f"left is {_shape(left)}, right is {_shape(right)}"
        )
    return _immutable(left - right)


def matrix_multiply(left, right):
    left_matrix = is_matrix(left)
    right_matrix = is_matrix(right)
    if not left_matrix and not right_matrix:
        return left * right
    if left_matrix and right_matrix:
        if left.cols != right.rows:
            raise EngEvaluationError(
                "matrix multiplication dimension mismatch: "
                f"left is {_shape(left)}, right is {_shape(right)}"
            )
        return _immutable(left * right)
    return _immutable(left * right)


def matrix_scalar_divide(left, right):
    left_matrix = is_matrix(left)
    right_matrix = is_matrix(right)
    if not left_matrix and not right_matrix:
        return left / right
    if left_matrix and right_matrix:
        raise EngEvaluationError("matrix division requires a scalar denominator")
    if right_matrix:
        raise EngEvaluationError("division by a matrix is unsupported")
    return _immutable(left / right)


def matrix_power(base, exponent):
    if not is_matrix(base):
        if is_matrix(exponent):
            raise EngEvaluationError("matrix exponent must be an exact integer")
        return base ** exponent
    if base.rows != base.cols:
        raise EngEvaluationError("matrix power requires a square matrix")
    if not isinstance(exponent, sp.Integer):
        raise EngEvaluationError("matrix exponent must be an exact integer")
    try:
        return _immutable(base ** int(exponent))
    except Exception as exc:
        raise EngEvaluationError(f"matrix power failed: {exc}") from None


def _positive_index(value) -> int:
    if not isinstance(value, sp.Integer) or value <= 0:
        raise EngEvaluationError("matrix indices must be positive integers, counted from 1")
    return int(value)


@dataclass(frozen=True)
class IndexRange:
    """`1:2`, `2:` or `:` inside a matrix index. Both ends are included and counted from
    one, as `K[1, 1]` already counts: `K[1:2, 1:2]` is rows 1 and 2."""

    lower: object | None
    upper: object | None


def _positions(index, size: int) -> list[int] | None:
    """The zero-based rows or columns a range or a list of indices takes, or None for a
    single index, which keeps the scalar path it has always had."""
    if isinstance(index, IndexRange):
        lower = 1 if index.lower is None else _positive_index(index.lower)
        upper = size if index.upper is None else _positive_index(index.upper)
        if upper < lower:
            raise EngEvaluationError(f"the range {lower}:{upper} runs backwards")
        if upper > size:
            raise EngEvaluationError(f"the range {lower}:{upper} is out of range for {size}")
        return list(range(lower - 1, upper))
    if is_matrix(index):
        if index.rows != 1 and index.cols != 1:
            raise EngEvaluationError("a list of indices is one row, [1, 3]")
        positions = [_positive_index(entry) for entry in index]
        for position in positions:
            if position > size:
                raise EngEvaluationError(f"index {position} is out of range for {size}")
        return [position - 1 for position in positions]
    return None


def matrix_index(value, indices: tuple[object, ...]):
    if not is_matrix(value):
        raise EngEvaluationError("matrix indexing requires a matrix")
    if len(indices) not in (1, 2):
        raise EngEvaluationError(
            "matrix indexing expects one vector index or two matrix indices"
        )

    if len(indices) == 1 and (value.rows == 1 or value.cols == 1):
        # A part of a vector keeps the vector's orientation.
        positions = _positions(indices[0], max(value.rows, value.cols))
        if positions is not None:
            if value.rows == 1:
                return value.extract([0], positions)
            return value.extract(positions, [0])

    if len(indices) == 2:
        rows = _positions(indices[0], value.rows)
        cols = _positions(indices[1], value.cols)
        if rows is not None or cols is not None:
            return value.extract(
                rows if rows is not None else [_in_range(indices[0], value.rows) - 1],
                cols if cols is not None else [_in_range(indices[1], value.cols) - 1],
            )

    if len(indices) == 1:
        index = _positive_index(indices[0])
        if value.rows == 1:
            if index > value.cols:
                raise EngEvaluationError(
                    f"matrix index [{index}] is out of range for shape {_shape(value)}"
                )
            return value[0, index - 1]
        if value.cols == 1:
            if index > value.rows:
                raise EngEvaluationError(
                    f"matrix index [{index}] is out of range for shape {_shape(value)}"
                )
            return value[index - 1, 0]
        raise EngEvaluationError(
            "general matrix indexing requires two indices"
        )

    row = _positive_index(indices[0])
    col = _positive_index(indices[1])
    if row > value.rows or col > value.cols:
        raise EngEvaluationError(
            f"matrix index [{row},{col}] is out of range for shape {_shape(value)}"
        )
    return value[row - 1, col - 1]


def matrix_assign(value, indices: tuple[object, ...], replacement, name: str):
    """`value` with the part `indices` names replaced by `replacement`, which must be the
    part's shape - a scalar for one entry. Indices count as they do when reading a part."""
    if len(indices) == 1 and (value.rows == 1 or value.cols == 1):
        size = max(value.rows, value.cols)
        positions = _positions(indices[0], size)
        if positions is None:
            positions = [_in_range(indices[0], size) - 1]
        rows, cols = ([0], positions) if value.rows == 1 else (positions, [0])
    elif len(indices) == 2:
        rows = _positions(indices[0], value.rows)
        rows = rows if rows is not None else [_in_range(indices[0], value.rows) - 1]
        cols = _positions(indices[1], value.cols)
        cols = cols if cols is not None else [_in_range(indices[1], value.cols) - 1]
    else:
        raise EngEvaluationError(
            "a part of a matrix is assigned with two indices, or one for a vector"
        )

    if is_matrix(replacement):
        if replacement.shape != (len(rows), len(cols)):
            raise EngEvaluationError(
                f"{name}[...] is {len(rows)}x{len(cols)} and the value is "
                f"{replacement.rows}x{replacement.cols}"
            )
        entries = replacement
    else:
        if (len(rows), len(cols)) != (1, 1):
            raise EngEvaluationError(
                f"{name}[...] is {len(rows)}x{len(cols)} and the value is a scalar"
            )
        entries = sp.ImmutableMatrix([[sp.sympify(replacement)]])

    updated = value.as_mutable()
    for i, row in enumerate(rows):
        for j, col in enumerate(cols):
            updated[row, col] = entries[i, j]
    return sp.ImmutableMatrix(updated)


def _in_range(index, size: int) -> int:
    position = _positive_index(index)
    if position > size:
        raise EngEvaluationError(f"index {position} is out of range for {size}")
    return position


def _positive_dimension(value) -> int:
    if not isinstance(value, sp.Integer) or value <= 0:
        raise EngEvaluationError(
            "matrix dimensions must be positive exact integers"
        )
    return int(value)


def matrix_identity(dimension):
    size = _positive_dimension(dimension)
    return sp.ImmutableMatrix(sp.eye(size))


def matrix_zeros(rows, cols):
    row_count = _positive_dimension(rows)
    col_count = _positive_dimension(cols)
    return sp.ImmutableMatrix(sp.zeros(row_count, col_count))


def matrix_diag(entries):
    if not entries:
        raise EngEvaluationError("diag expects at least one scalar entry")
    if any(is_matrix(entry) for entry in entries):
        raise EngEvaluationError("diag entries must be scalar")
    return sp.ImmutableMatrix(sp.diag(*(sp.sympify(entry) for entry in entries)))


def _require_matrix(value, name: str):
    if not is_matrix(value):
        raise EngEvaluationError(f"{name} requires a matrix")
    return value


def _require_square(value, name: str):
    matrix = _require_matrix(value, name)
    if matrix.rows != matrix.cols:
        raise EngEvaluationError(f"{name} requires a square matrix")
    return matrix


def matrix_transpose(value):
    matrix = _require_matrix(value, "transpose")
    return _immutable(matrix.T)


def matrix_det(value):
    matrix = _require_square(value, "det")
    return matrix.det()


def matrix_inv(value):
    matrix = _require_square(value, "inv")
    try:
        return _immutable(matrix.inv())
    except Exception as exc:
        message = str(exc).lower()
        if "not invertible" in message or "det == 0" in message or "zero determinant" in message:
            raise EngEvaluationError("inv requires a nonsingular matrix") from None
        raise


def matrix_trace(value):
    matrix = _require_square(value, "trace")
    return matrix.trace()


def matrix_size(value):
    matrix = _require_matrix(value, "size")
    return matrix.rows, matrix.cols


def map_matrix_entries(matrix, operation) -> sp.ImmutableMatrix:
    """Apply one scalar operation entrywise and preserve immutable matrix truth."""
    if not is_matrix(matrix):
        raise EngEvaluationError("matrix entry mapping requires a matrix")
    return sp.ImmutableMatrix(
        matrix.rows,
        matrix.cols,
        lambda row, col: sp.sympify(operation(matrix[row, col])),
    )
