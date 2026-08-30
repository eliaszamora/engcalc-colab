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
