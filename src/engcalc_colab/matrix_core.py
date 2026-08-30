from __future__ import annotations

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
    normalized = []
    for row in rows:
        normalized_row = []
        for cell in row:
            if is_matrix(cell):
                raise EngEvaluationError("matrix literal cells must be scalar")
            normalized_row.append(sp.sympify(cell))
        normalized.append(normalized_row)
    return sp.ImmutableMatrix(normalized)


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
        raise EngEvaluationError("matrix indices must be positive integers")
    return int(value)


def matrix_index(value, indices: tuple[object, ...]):
    if not is_matrix(value):
        raise EngEvaluationError("matrix indexing requires a matrix")
    if len(indices) not in (1, 2):
        raise EngEvaluationError(
            "matrix indexing expects one vector index or two matrix indices"
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
