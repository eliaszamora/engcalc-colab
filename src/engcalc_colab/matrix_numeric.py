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
    # Zeros a `:=` line worked out - a rotation a solve found to be 0 - and not written.
    # They print and convert as any zero does; taken out one at a time they stay plain
    # numbers, where a written zero takes the unit of the entries beside it (see
    # `entry_quantity`).
    fixed_zeros: frozenset[tuple[int, int]] = frozenset()

    def __post_init__(self) -> None:
        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("QuantityMatrix dimensions must be positive")
        normalized_entries = tuple(self.entries)
        if len(normalized_entries) != self.rows * self.cols:
            raise ValueError("QuantityMatrix entry count does not match shape")
        normalized_zeros = frozenset(self.adaptable_zeros)
        normalized_fixed = frozenset(self.fixed_zeros)
        for row, col in normalized_zeros | normalized_fixed:
            if not (0 <= row < self.rows and 0 <= col < self.cols):
                raise ValueError("QuantityMatrix adaptable zero is outside matrix shape")
        object.__setattr__(self, "entries", normalized_entries)
        object.__setattr__(self, "adaptable_zeros", normalized_zeros)
        object.__setattr__(self, "fixed_zeros", normalized_fixed)

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
    # The unitless zeros an operation worked out - a solve, a product, an inverse - apart
    # from the ones written as `0`, which take the unit of the entries beside them when
    # one is taken out (see `entry_quantity`). Kept through the operations that only move
    # entries: a transpose, a part, blocks, a factor.
    worked_zeros: frozenset = frozenset()

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


def _unitless_zeros(cols: int, units) -> frozenset:
    """Every entry an operation left as a zero with no unit."""
    return frozenset(
        divmod(index, cols) for index, unit in enumerate(units) if unit is None
    )


def _of_one_kind(*matrices: NumberMatrix) -> bool:
    """Each matrix's entries of one dimension, and no zero of a kind already unknown."""
    for numbers in matrices:
        if numbers.worked_zeros:
            return False
        units = list({unit for unit in numbers.units if unit is not None})
        if any(not _same_dimension(units[0], unit) for unit in units[1:]):
            return False
    return True


def _worked_zeros(cols: int, units, *sources: NumberMatrix) -> frozenset:
    """The unitless zeros of an operation's result that stay plain numbers.

    Which kind a zero worked out to be is the operation's to know, not the vector's: the
    displacements of two springs, `solve([k, 0; 0, k], [10 kN; 0])`, and of a frame,
    `solve([k, 0; 0, 2k m²], [10 kN; 0])`, are both `[10 mm; 0]`. When the operands are of
    one kind - springs, a truss - so is the zero, and taken out it borrows the unit beside
    it, as on main (the second audit of 0.45.6: a spring's force read `0.00 kN/m`). When
    they mix stiffnesses, the zero may be a rotation, and a number is all that is known
    (the first audit: `θ = 0.00 m`, its moment `kN·m²`)."""
    if _of_one_kind(*sources):
        return frozenset()
    return _unitless_zeros(cols, units)


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
        quantity_matrix.rows,
        quantity_matrix.cols,
        tuple(magnitudes),
        tuple(units),
        frozenset(
            position
            for position in quantity_matrix.fixed_zeros
            if units[position[0] * quantity_matrix.cols + position[1]] is None
        ),
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
    fixed = set()
    for index, (magnitude, unit) in enumerate(zip(numbers.magnitudes, numbers.units)):
        position = divmod(index, numbers.cols)
        if unit is None:
            zeros.add(position)
            if position in numbers.worked_zeros:
                fixed.add(position)
            entries.append(ureg.Quantity(0, ureg.dimensionless))
        else:
            quantity = ureg.Quantity(magnitude, unit)
            # The magnitude first: asking Pint for a dimension is slow, and a stiffness has
            # hundreds of entries (the second audit of 0.45.6 measured 8 s on p9_5).
            if magnitude == 0.0 and quantity.dimensionless:
                # A rotation worked out to be exactly 0: read back, a dimensionless zero
                # is taken for a written one (`numbers_of`), and this says it is not.
                fixed.add(position)
            entries.append(quantity)
    return QuantityMatrix(
        numbers.rows, numbers.cols, tuple(entries), frozenset(zeros), frozenset(fixed)
    )


def entry_quantity(numbers: NumberMatrix, row: int, col: int, ureg):
    """One entry, as the scalar a `:=` line goes on with. The unitless zero is a plain
    `0`, which Pint adds to any quantity, as the written `0` it stands for would be."""
    magnitude, unit = numbers.at(row, col)
    if unit is None:
        # The unit of every other entry, when they share one: in `D := [0; 2[1/m]]` the
        # written 0 is a curvature, and `GJ*D[1]/T` read `0.00 m` (his book, Example 7.4).
        # A matrix of several dimensions - a stiffness - leaves its zero a plain 0.
        others = [other for other in numbers.units if other is not None]
        # Not a zero an operation worked out: a rotation a solve found to be exactly 0 is
        # a number, and lent the vector's metre it read `0.00 m` and the moment it made
        # `kN·m²` (his book, chapter 9).
        if (
            (row, col) not in numbers.worked_zeros
            and others
            and all(_same_dimension(others[0], other) for other in others)
        ):
            return ureg.Quantity(0.0, others[0])
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
    worked = (left.worked_zeros | right.worked_zeros) & _unitless_zeros(left.cols, units)
    return NumberMatrix(left.rows, left.cols, tuple(magnitudes), tuple(units), worked)


def scale_numbers(numbers: NumberMatrix, factor) -> NumberMatrix:
    """Every entry times a scalar quantity; the unitless zero stays one."""
    base = factor.to_base_units()
    magnitude, unit = float(base.magnitude), base.units
    return NumberMatrix(
        numbers.rows,
        numbers.cols,
        tuple(value * magnitude for value in numbers.magnitudes),
        tuple(None if each is None else each * unit for each in numbers.units),
        numbers.worked_zeros,
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
    return NumberMatrix(
        left.rows, right.cols, magnitudes, tuple(units),
        _worked_zeros(right.cols, units, left, right),
    )


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
        frozenset((col, row) for row, col in numbers.worked_zeros),
    )


# What a matrix whose units do not fit has none of, by the operation that found it.
_MISFIT_CONSEQUENCE = {
    "det": "so its determinant has no one unit",
    "eigenvals": "so its eigenvalues have no one unit",
}


def _misfit(operation: str, row: int, col: int) -> EngEvaluationError:
    consequence = _MISFIT_CONSEQUENCE.get(operation, "so it has no inverse with units")
    return EngEvaluationError(
        f"matrix operation '{operation}': the unit of entry [{row + 1},{col + 1}] does "
        f"not fit the rest of the matrix, {consequence}"
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
    return NumberMatrix(
        size, size, magnitudes, tuple(units), _worked_zeros(size, units, numbers)
    )


def _a_full_permutation(numbers: NumberMatrix) -> list[int] | None:
    """Columns `p[i]` with every entry [i, p[i]] nonzero, or None when there is none - a
    term of the determinant that is not zero, whose units are the determinant's."""
    size = numbers.rows
    match_of_col = [-1] * size

    def assign(row: int, seen: list[bool]) -> bool:
        for col in range(size):
            if numbers.units[row * size + col] is None or seen[col]:
                continue
            seen[col] = True
            if match_of_col[col] == -1 or assign(match_of_col[col], seen):
                match_of_col[col] = row
                return True
        return False

    for row in range(size):
        if not assign(row, [False] * size):
            return None
    permutation = [0] * size
    for col, row in enumerate(match_of_col):
        permutation[row] = col
    return permutation


def det_numbers(numbers: NumberMatrix):
    """`det(K)` of a matrix of numbers: its magnitude in base units and its unit, the
    product of the units of a nonzero term (all terms share it when the units fit). A
    matrix with no nonzero term is 0 with no unit."""
    import mpmath

    _square(numbers, "det")
    _inverse_units(numbers, "det")
    permutation = _a_full_permutation(numbers)
    if permutation is None:
        return 0.0, None
    unit = None
    for row, col in enumerate(permutation):
        entry = numbers.units[row * numbers.cols + col]
        unit = entry if unit is None else unit * entry
    determinant = mpmath.det(_mp_matrix(numbers))
    if determinant and abs(determinant) > mpmath.mpf("1.7976931348623157e308"):
        # Exact here, infinity as a float, and the printer raised OverflowError (his book,
        # chapter 10: a 38 x 38 stiffness matrix in newtons). Its size is still worth saying.
        exponent = int(mpmath.floor(mpmath.log10(abs(determinant))))
        raise EngEvaluationError(
            f"det is about 10^{exponent} (in base units), too large for a number to hold: "
            "a float stops at 1.8 × 10^308"
        )
    return float(determinant), unit


def _a_cycle(numbers: NumberMatrix) -> list[tuple[int, int]] | None:
    """Entries [i1,i2], [i2,i3], ... [ik,i1], all nonzero - a closed walk through the
    matrix, whose product is λ^k in units - or None when there is none, and then every
    eigenvalue is 0."""
    size = numbers.rows
    state = [0] * size  # 0 unseen, 1 on the path, 2 done
    path: list[int] = []

    def walk(node: int) -> list[tuple[int, int]] | None:
        state[node] = 1
        path.append(node)
        for following in range(size):
            if numbers.units[node * size + following] is None:
                continue
            if state[following] == 1:
                loop = path[path.index(following):]
                return [(loop[i], loop[(i + 1) % len(loop)]) for i in range(len(loop))]
            if state[following] == 0:
                found = walk(following)
                if found is not None:
                    return found
        path.pop()
        state[node] = 2
        return None

    for start in range(size):
        if state[start] == 0:
            found = walk(start)
            if found is not None:
                return found
    return None


def _eigenvalue_unit(numbers: NumberMatrix):
    """The unit every eigenvalue has, or None when the matrix has no closed walk and its
    eigenvalues are all 0.

    A matrix with eigenvalues in a unit is that unit times `s_i / s_k` at [i,k] - a
    stiffness pencil's `G⁻¹ K` is, with `s` a displacement or a rotation. A diagonal entry
    says the unit; with none, a closed walk of k entries is its k-th power (`[0, 1; 1, 0]`
    has λ² = a₁₂ a₂₁: the audit of 0.45.6, where a diagonal of written zeros read as no
    unit answered [0; 0] for [-1; 1]). Every entry is then checked against it."""
    size = numbers.rows
    unit = next(
        (numbers.units[i * size + i] for i in range(size) if numbers.units[i * size + i] is not None),
        None,
    )
    if unit is None:
        cycle = _a_cycle(numbers)
        if cycle is None:
            return None
        power = None
        for row, col in cycle:
            entry = numbers.units[row * size + col]
            power = entry if power is None else power * entry
        unit = _unit_root(power, len(cycle))
        if unit is None:
            raise EngEvaluationError(
                f"matrix operation 'eigenvals': a walk through {len(cycle)} entries has the "
                f"unit {_unit_text(power)}, which is no power {len(cycle)} of one unit, so "
                "its eigenvalues have no one unit"
            )
    scale: list[Any] = [None] * size
    for start in range(size):
        if scale[start] is not None:
            continue
        scale[start] = unit / unit
        pending = [start]
        while pending:
            here = pending.pop()
            for other in range(size):
                implied_scales = []
                forward = numbers.units[here * size + other]
                if forward is not None:  # [here, other] is unit · s_here / s_other
                    implied_scales.append((unit * scale[here] / forward, (here, other)))
                backward = numbers.units[other * size + here]
                if backward is not None:  # [other, here] is unit · s_other / s_here
                    implied_scales.append((backward * scale[here] / unit, (other, here)))
                for implied, where in implied_scales:
                    if scale[other] is None:
                        scale[other] = implied
                        pending.append(other)
                    elif not _same_dimension(implied, scale[other]):
                        raise _misfit("eigenvals", *where)
    return unit


def eigenvalues_of_numbers(matrix: NumberMatrix, metric: NumberMatrix | None = None) -> NumberMatrix:
    """The eigenvalues of a matrix of numbers, or of the pencil `K x = λ G x` - the
    critical load factors of a frame, `eigenvals(K, G)` - as a column, smallest first, by
    value (a negative one before a positive one).

    Worked out on `G⁻¹ K` in base units: a stiffness's rows and columns carry forces and
    moments, displacements and rotations, and that product is the same matrix in another
    basis, in one unit times `s_i / s_k` (see `_eigenvalue_unit`). Refused when they are not
    all real: a stiffness pencil's are (his book, chapter 9, where every critical load had
    been found by an inverse iteration written by hand)."""
    import numpy

    operation = "eigenvals"
    _square(matrix, operation)
    if metric is not None:
        _square(metric, operation)
        if metric.rows != matrix.rows:
            raise EngEvaluationError(
                f"eigenvals of a {matrix.shape} matrix needs a second matrix of the same size, "
                f"not {metric.shape}"
            )
        symmetric = _nearly_symmetric(matrix) and _nearly_symmetric(metric)
        try:
            inverse = inverse_numbers(metric)
        except EngEvaluationError as exc:
            if "singular" not in str(exc):
                raise
            if symmetric:
                # A frame's geometric stiffness always is: nothing along the bars, whose
                # eigenvalue is infinite (his book, chapter 10). The finite ones are found
                # exactly, and judged one by one.
                try:
                    return _finite_eigenvalues(matrix, metric)
                except _OutOfSymmetry:
                    pass
            # A lumped geometric stiffness or mass often is (the audit of 0.45.6, where the
            # message sent the reader to K's supports).
            raise EngEvaluationError(
                "eigenvals(K, G): the second matrix is singular - it has nothing in some "
                "direction, whose eigenvalue is infinite; take those degrees of freedom out "
                "of both matrices"
            ) from exc
        product = multiply_numbers(inverse, matrix)
        if symmetric:
            # G⁻¹K tells the unit and refuses units that do not fit; its numbers do not serve:
            # a G singular only to round-off inverts, and G⁻¹K's eigenvalues were noise - 1e16
            # and -0.33 for 0.165 (the second audit). The values come from the exact pencil.
            _inverse_units(product, operation)
            try:
                return _finite_eigenvalues(matrix, metric, unit=_eigenvalue_unit(product))
            except _OutOfSymmetry:
                pass
        # Not symmetric - follower loads, not a frame's stiffness: the λ of G⁻¹K as main reads
        # them, worked out exactly instead of in floats - a column on 1e20 springs, out of
        # symmetry by 2.4 in 24000, read 1512.14 for 1515.90 in floats (the fifth audit of
        # 0.46.1). No λ is judged here: a nearly defective one has no first-order measure.
        _inverse_units(product, operation)
        return _exact_nonsymmetric(matrix, metric, _eigenvalue_unit(product))
    _inverse_units(matrix, operation)
    unit = _eigenvalue_unit(matrix)
    size = matrix.rows
    values = numpy.linalg.eigvals(
        numpy.array(matrix.magnitudes, dtype=float).reshape(size, size)
    )
    # Each eigenvalue by its own size, above the round-off of the whole spectrum: judged
    # by the largest, ±i beside 1e12 passed as two real zeros (the review of #395).
    scale = max((abs(value) for value in values), default=0.0) or 1.0
    floor = 1e-13 * scale
    if any(abs(value.imag) > 1e-9 * abs(value) + floor for value in values):
        raise EngEvaluationError(
            "eigenvals found eigenvalues that are not real; a stiffness and a geometric "
            "stiffness have real ones - check that both matrices are symmetric"
        )
    ordered = sorted(float(value.real) for value in values)
    units = tuple(unit for _ in ordered)
    return NumberMatrix(size, 1, tuple(ordered), units, _unitless_zeros(1, units))


class _OutOfSymmetry(Exception):
    """A pencil symmetric pair by pair whose dropped antisymmetric part moves a λ beyond its
    round-off: it is worked out as a pencil that is not symmetric."""


def _exact_nonsymmetric(matrix: NumberMatrix, metric: NumberMatrix, unit) -> NumberMatrix:
    """The eigenvalues of G⁻¹K for a G that inverts, in `_PENCIL_FIGURES` figures on the floats
    as they are; refused as main refuses when they are not all real."""
    import mpmath
    import numpy

    size = matrix.rows
    stiffness = numpy.array(matrix.magnitudes, dtype=float).reshape(size, size)
    geometric = numpy.array(metric.magnitudes, dtype=float).reshape(size, size)
    # mpmath's QR does not always converge in these figures - ten tied systems coupled
    # antisymmetrically, "qr: failed to converge after 321 steps" (the ninth audit of 0.47.0):
    # once more in half as many again, then refused in words.
    for figures in (_PENCIL_FIGURES, _PENCIL_FIGURES * 3 // 2):
        try:
            with mpmath.workdps(figures):
                values = mpmath.eig(
                    mpmath.inverse(mpmath.matrix(geometric.tolist())) * mpmath.matrix(stiffness.tolist()),
                    left=False, right=False,
                )
            break
        except RuntimeError:
            continue
    else:
        raise EngEvaluationError(
            "eigenvals(K, G): the eigenvalues of this pencil, which is not symmetric, could not be "
            "worked out - the iteration does not settle; check that both matrices are symmetric"
        )
    with mpmath.workdps(_PENCIL_FIGURES):
        values = [values[i] for i in range(size)]
        scale = max((abs(value) for value in values), default=0) or 1
        # Each against itself, in these figures: against the largest, as main judges floats,
        # 2 ± 0.3i beside a λ of 1e32 passed as 2 twice (the fourth audit of 0.47.0), and at
        # 1e-40 of it 2 ± 0.001i beside 3e37 (the seventh).
        # Below a millionth of itself an imaginary part is beyond the figures printed: main
        # printed 2 for 2 ± 1e-6i beside 1e8, and so does this (the eighth audit of 0.47.0).
        if any(abs(mpmath.im(value)) > 1e-6 * abs(value) + mpmath.mpf(10) ** -70 * scale for value in values):
            raise EngEvaluationError(
                "eigenvals found eigenvalues that are not real; a stiffness and a geometric "
                "stiffness have real ones - check that both matrices are symmetric"
            )
        ordered = sorted(float(mpmath.re(value)) for value in values)
    units = tuple(unit for _ in ordered)
    return NumberMatrix(size, 1, tuple(ordered), units, _unitless_zeros(1, units))


def _nearly_symmetric(numbers: NumberMatrix) -> bool:
    """Symmetric to its round-off: assembled as tᵀkt a stiffness or a mass differs from its
    transpose in the last bit (3e-17 of the entries), and is symmetric all the same. Each pair
    against its own scale, the larger of the two and of √(r_i r_j), r the largest of a row - not
    of the diagonal, which at a joint where K_g cancels is round-off itself, and his -K_g was
    sent out of symmetry and refused (the seventh audit of 0.47.0). Against the largest entry,
    a support written as a 1e18 spring hid a follower load of 1.5e5, the pencil was symmetrized
    and Beck's column read a negative ω² (the sixth audit of 0.47.0)."""
    import numpy

    size = numbers.rows
    values = numpy.array(numbers.magnitudes, dtype=float).reshape(size, size)
    rows = numpy.abs(values).max(axis=1)
    own = numpy.maximum(numpy.maximum(numpy.abs(values), numpy.abs(values.T)), numpy.sqrt(numpy.outer(rows, rows)))
    return bool(numpy.all(numpy.abs(values - values.T) <= 1e-12 * own))


def _finite_eigenvalues(matrix: NumberMatrix, metric: NumberMatrix, unit=None) -> NumberMatrix:
    """`eigenvals(K, G)` of a symmetric pencil: the finite λ of K x = λ G x, smallest first.

    Worked out in `_PENCIL_FIGURES` figures on the entries exactly as the floats hold them -
    symmetrized, a last-bit difference from tᵀkt being round-off - with each λ's vector
    (`_exact_pencil`). Seven audits of a method in floats each found a silently wrong λ -
    supports and links written as springs of 1e16-1e20, a G singular to round-off - and every
    one was the solver's round-off, not the matrices'.

    What the floats themselves do not settle is told by each λ's own sensitivity to a change
    of 1e-15 in every entry (`_judged`). A pencil that is not symmetric is worked out as main
    works it (`eigenvalues_of_numbers`): a nearly defective λ of one has no first-order
    sensitivity to tell it by, and lost a double of a ring in silence (the fifth audit)."""
    import numpy

    size = matrix.rows
    if unit is None:
        # With G singular nothing inverted K: its units are checked as its inverse checks
        # them (the third audit: an entry in kN/m among kN·m read in kN).
        _inverse_units(matrix, "eigenvals")
    stiffness = numpy.array(matrix.magnitudes, dtype=float).reshape(size, size)
    geometric = numpy.array(metric.magnitudes, dtype=float).reshape(size, size)
    # What symmetrizing drops, |K - Kᵀ| / 2, is weighed against each λ's round-off: symmetric
    # pair by pair to 1e-12, an antisymmetric 4.5 beside a tie of 1e13 split a double into
    # 1 ± 2.25i, and symmetrized it printed 1 twice (the seventh audit of 0.47.0).
    skews = (numpy.abs(stiffness - stiffness.T) / 2, numpy.abs(geometric - geometric.T) / 2)
    stiffness = (stiffness + stiffness.T) / 2
    geometric = (geometric + geometric.T) / 2
    if not numpy.abs(geometric).max():
        raise EngEvaluationError("eigenvals(K, G): the second matrix is zero; there is no finite eigenvalue")
    finite = _judged(stiffness, geometric, skews)
    if unit is None:
        unit = _pencil_unit(matrix, metric)
    units = tuple(unit for _ in finite)
    return NumberMatrix(len(finite), 1, tuple(finite), units, _unitless_zeros(1, units))


_UNSETTLED = (
    "eigenvals(K, G): these eigenvalues cannot be told with the figures a float holds - a "
    "change of 1e-15 in the entries moves one by more than 3% of itself; G is singular or "
    "nearly, or a stiffness far beyond the rest (a support written as a spring) does this. Take "
    "out the degrees of freedom where G has (almost) nothing, or write it exactly"
)

_PENCIL_FIGURES = 80


def _judged(stiffness, geometric, skews=None) -> list[float]:
    """The λ the floats settle, each by its sensitivity s to a change of 1e-15 in every entry,
    s = 1e-15 |x|ᵀ(|K| + |λ||G|)|x| / |xᵀGx|.

    - s ≤ 3% of |λ|: printed, the exact answer to the entries as written - two stiff DOFs tied
      by a 1e13 spring, whose soft λ = 1 is (1 + P) - P, s = 2% (the audits' A_tie), as main
      printed it. The round-off of entries as a sheet writes them - kN to N - moved a λ by about
      a thirtieth of its s: a portal's soft ω² of 3.736 read 3.723 with s at 9% (the battery of
      0.47.0), a third figure the page would print wrong; at 3% the third figure holds.
    - G cancelling to round-off on its vector, |xᵀGx| ≤ 1e-11 |x|ᵀ|G||x|, and not one figure
      holding at first order (s ≥ |λ|): a direction G has only to round-off, whose λ is
      round-off over round-off - infinite, not printed; no more of these than G has such
      directions (`_round_off_directions`). A group's own s decides only whether it prints
      (`_clusters_measured`).
    - negligible, below 1e-12 of the λ that are settled (their lower median): its own value
      while one figure of it holds (s < |λ|), else 0 - a mechanism, or his -K_g's λ of 1e-17
      beside 1e-3, as main printed them (the fourth audit of 0.47.0). The upper median of two -
      an axial mode and a link's - made a sway mode of 176 negligible, and it was printed 0
      (the fifth audit).
    - anything else is refused: a sway mode beside a link of 3e20, λ = 176 with s of 270, is a
      mechanism or not as the last bit of the link has it."""
    import numpy

    exact = _exact_pencil(stiffness, geometric, skews)
    # What symmetrizing dropped moves a λ by more than ten times what round-off could: the
    # pencil is not symmetric there, and is worked out as one that is not.
    if any(dropped > 10 * s for _value, s, _g, dropped in exact):
        raise _OutOfSymmetry
    pencil = _clusters_measured(stiffness, geometric, exact)
    # What 0 leaves in these figures - 1.6e-89 beside 1e9 - is 0, and judged as one: beside K's
    # scale over G's, not the largest λ, which a G of 1e-60 makes 1e60 (the fifth audit).
    scale = numpy.abs(stiffness).sum(axis=0).max() / numpy.abs(geometric).sum(axis=0).max()
    pencil = [(0.0 if abs(value) <= 1e-65 * scale else value, s, g, first) for value, s, g, first in pencil]
    sizes = sorted(abs(value) for value, s, _g, _f in pencil if value and s <= 0.03 * abs(value))
    typical = sizes[(len(sizes) - 1) // 2] if sizes else 0.0
    finite = []
    infinite = 0
    for value, sensitivity, g_part, first in pencil:
        if sensitivity <= 0.03 * abs(value):
            finite.append(value)
        elif g_part <= 1e-11 and first >= abs(value):
            infinite += 1
        elif abs(value) <= 1e-12 * typical:
            finite.append(0.0 if sensitivity >= abs(value) else value)
        else:
            raise EngEvaluationError(_UNSETTLED)
    if infinite and infinite > _round_off_directions(geometric):
        raise EngEvaluationError(_UNSETTLED)
    return sorted(finite)


def _clusters_measured(stiffness, geometric, pencil):
    """Each λ as (value, s to print by, g, first-order s). A group of λ within 1e-6 of each
    other, one of whose first-order s says it holds no figure, has its s to print by measured
    instead: the pencil again, exactly, on entries moved by 1e-15 of themselves, the group
    against as many values of each run nearest it, both in order. A defective double - K =
    [1, 3; 3, 0] against G = [0, 1; 1, 0], λ = 3 twice - has xᵀGx = 0 and no first-order s,
    and moves by the square root of the change, 3e-8: it was refused where main printed it
    (the fifth audit of 0.47.0). Member against its nearest, a twin's copy was its own nearest
    and the s came out low (the sixth audit). Whether a λ is infinite stays the first-order
    measure's: a pair of round-off λ of 7e28 measured at 93% was refused, where it is two
    directions G lacks (the battery, multi-storey frames on springs)."""
    import numpy

    out = [(value, s, g, s) for value, s, g, _skew in pencil]
    values = [value for value, _s, _g, _skew in pencil]
    order = sorted(range(len(values)), key=lambda i: values[i])
    groups, current = [], [order[0]] if order else []
    for previous, index in zip(order, order[1:]):
        if abs(values[index] - values[previous]) <= 1e-6 * max(abs(values[index]), abs(values[previous])):
            current.append(index)
        else:
            groups.append(current)
            current = [index]
    if current:
        groups.append(current)
    doubtful = [
        group for group in groups
        if len(group) > 1 and any(pencil[i][1] > 0.03 * abs(values[i]) for i in group)
    ]
    if not doubtful:
        return out
    trials = numpy.random.default_rng(20261009)
    moved_runs = []
    for _ in range(2):
        noise = trials.standard_normal(stiffness.shape)
        k = stiffness * (1 + 1e-15 * (noise + noise.T) / 2)
        noise = trials.standard_normal(geometric.shape)
        g = geometric * (1 + 1e-15 * (noise + noise.T) / 2)
        try:
            run = [value for value, _s, _g, _skew in _exact_pencil(k, g)]
        except EngEvaluationError:
            return out
        if len(run) < max(len(group) for group in doubtful):
            return out
        moved_runs.append(run)
    for group in doubtful:
        mine = sorted(group, key=lambda i: values[i])
        centre = sum(values[i] for i in mine) / len(mine)
        moved = [0.0] * len(mine)
        for run in moved_runs:
            theirs = sorted(sorted(run, key=lambda v: abs(v - centre))[: len(mine)])
            for place, (index, other) in enumerate(zip(mine, theirs)):
                moved[place] = max(moved[place], abs(other - values[index]))
        for place, index in enumerate(mine):
            value, first, g_part, _ = out[index]
            out[index] = (value, moved[place], g_part, first)
    return out


def _round_off_directions(geometric) -> int:
    """How many directions G has only to round-off: eigenvalues of G scaled by its own diagonal
    (a spring of 1e20 in G is no direction it lacks), in `_PENCIL_FIGURES` figures on the floats
    as they are, above what 0 leaves (1e-70 of the largest) and below 1e-11 of it."""
    import mpmath

    size = len(geometric)
    with mpmath.workdps(_PENCIL_FIGURES):
        # Scaled in these figures, not in floats: rounded, a 2x2 block of 100 [c², cs; cs, s²]
        # lost the round-off it is singular to, and its direction was not counted (the battery).
        g = mpmath.matrix(geometric.tolist())
        own = [mpmath.sqrt(abs(g[i, i])) or mpmath.mpf(1) for i in range(size)]
        scaled = mpmath.matrix([[g[i, j] / own[i] / own[j] for j in range(size)] for i in range(size)])
        values = mpmath.eigsy(scaled, eigvals_only=True)
        sizes = [abs(values[i]) for i in range(size)]
        top = max(sizes)
        return sum(1 for size in sizes if mpmath.mpf(10) ** -70 * top < size <= mpmath.mpf(10) ** -11 * top)


def _exact_pencil(stiffness, geometric, skews=None) -> list[tuple[float, float, float, float]]:
    """The finite λ of a symmetric pencil K x = λ G x on the floats as they are, in
    `_PENCIL_FIGURES` figures, each with its sensitivity to a change of 1e-15 in every entry and
    |xᵀGx| / |x|ᵀ|G||x|.

    Through a Cholesky factor: of G when it is positive definite (a mass, his `eigenvals(-K_g,
    K)`) - xᵀGx = 1 - else of K - σG for the σ nearest 0 that makes it so - xᵀGx = μ, and λ =
    σ + 1/μ, a μ of 0 being a direction G does not have, whose λ is infinite. A pencil with no
    definite combination - G and K both indefinite - through (K - σG)⁻¹ G, the σ nearest 0 that
    inverts with condition up to 1e40 (the best conditioned alone was -1.4e30 beside a 1e22
    spring, where 2 ± i came out real - the second audit); refused when a λ is not real, and
    when no σ inverts: K - λG is singular for every λ. The sums of s are of magnitudes and are
    taken in floats; what cancels is not."""
    import mpmath
    import numpy

    size = stiffness.shape[0]
    k_norm = numpy.abs(stiffness).sum(axis=0).max()
    g_norm = numpy.abs(geometric).sum(axis=0).max()
    scales = sorted({1.0, k_norm / g_norm if k_norm else 1.0})
    shifts = sorted(
        {0.0} | {sign * 1.37 * 10.0 ** power * scale for scale in scales for power in range(-8, 9) for sign in (-1, 1)},
        key=abs,
    )
    k_abs = numpy.abs(stiffness)
    g_abs = numpy.abs(geometric)

    def definite(matrix) -> bool:
        try:
            numpy.linalg.cholesky(matrix)
        except numpy.linalg.LinAlgError:
            return False
        return True

    def judged(value, vector, seen):
        # s = 1e-15 |x|ᵀ(|K| + |λ||G|)|x| / |xᵀGx|, and |xᵀGx| against |x|ᵀ|G||x|; what
        # symmetrizing dropped is added by `finished`, over each group of λ.
        x = numpy.abs(numpy.array([float(vector[i]) for i in range(size)]))
        weight = float(x @ ((k_abs + abs(float(value)) * g_abs) @ x))
        magnitude = float(x @ (g_abs @ x))
        seen = abs(float(seen))
        if not seen:
            return [float(value), float("inf"), 0.0, x, seen]
        return [float(value), 1e-15 * weight / seen, seen / magnitude if magnitude else 0.0, x, seen]

    def finished(rows, nulls=None):
        # What symmetrizing dropped, ΔK = |K - Kᵀ|/2 and ΔG, couples any two λ by
        # c = |x|ᵀ(|ΔK| + |λ||ΔG|)|x'| / √(|xᵀGx||x'ᵀGx'|), and moves λ by c when they are
        # within 2c - they may meet and leave the real line - else by c²/gap: an antisymmetric
        # 4.5 between two tied systems split their double into 1 ± 2.25i (the seventh audit of
        # 0.47.0), and one between two λ 1e-3 apart, each blind to it alone, moved them by 3e-4
        # (the eighth). Every pair, not a group's, and summed.
        if skews is None or not (skews[0].any() or skews[1].any()):
            return [(value, s, g, 0.0) for value, s, g, _x, _seen in rows]
        lams = numpy.array([abs(row[0]) for row in rows])
        vectors = numpy.array([row[3] for row in rows])
        seens = numpy.array([row[4] for row in rows])
        through_k = vectors @ skews[0] @ vectors.T
        through_g = vectors @ skews[1] @ vectors.T
        # Through ΔK - λ_i ΔG: its own λ, not the larger of the pair - a mechanism's 0 keeps 0
        # whatever ΔG is, and charged with its partner's λ it sent his condensed -K_g out of
        # symmetry (the ninth audit of 0.47.0).
        coupling = through_k + lams[:, None] * through_g
        scale = numpy.sqrt(numpy.outer(seens, seens))
        with numpy.errstate(divide="ignore", invalid="ignore"):
            c = numpy.where(scale > 0, coupling / scale, numpy.where(coupling > 0, numpy.inf, 0.0))
            values = numpy.array([row[0] for row in rows])
            gap = numpy.abs(values[:, None] - values[None, :])
            moved = numpy.where(gap <= 2 * c, c, numpy.where(gap > 0, c * c / gap, c))
        moved = numpy.nan_to_num(moved, nan=numpy.inf)
        # Summed over every partner, not the largest: six pairs each under the gate moved a λ of
        # 1 to 2.149 together (the ninth audit of 0.47.0).
        dropped = moved.sum(axis=1) if len(rows) else numpy.zeros(0)
        # And through each direction G does not have, z with Gz = 0, whose λ is infinite and
        # not a row here: (xᵀΔK z)² / (|xᵀGx| zᵀKz) - an antisymmetric 14 between a tied mode
        # and a soft direction G lacks moved λ = 1 to 6.06, blind to every pair above (the
        # tenth audit of 0.47.0).
        # nulls: the directions G lacks, as |Z| and |(ZᵀKZ)⁻¹| - their own K-Gram matrix, not
        # one stiffness each: two such directions tied by 1e13 have a soft combination of 20,
        # through which an antisymmetric 4.5 moved λ = 1 to 3.025 (the eleventh audit).
        if nulls:
            null_vectors, inverse_gram = nulls
            reach = vectors @ skews[0] @ null_vectors + lams[:, None] * (vectors @ skews[1] @ null_vectors)
            through = numpy.einsum("ij,jk,ik->i", reach, inverse_gram, reach)
            with numpy.errstate(divide="ignore", invalid="ignore"):
                dropped = dropped + numpy.where(seens > 0, through / seens, numpy.where(through > 0, numpy.inf, 0.0))
        return [(value, s, g, float(d)) for (value, s, g, _x, _seen), d in zip(rows, dropped)]

    with mpmath.workdps(_PENCIL_FIGURES):
        k = mpmath.matrix(stiffness.tolist())
        g = mpmath.matrix(geometric.tolist())
        floor = mpmath.mpf(10) ** -70
        g_size = mpmath.mnorm(g, 1)

        def cholesky(m):
            try:
                factor = mpmath.cholesky(m)
            except (ValueError, ZeroDivisionError):
                return None
            if any(factor[i, i] <= 0 for i in range(size)):
                return None
            return factor

        def column(m, j):
            return mpmath.matrix([m[i, j] for i in range(size)])

        factor = cholesky(g) if definite(geometric) else None
        if factor is not None:
            inverse = mpmath.inverse(factor)
            values, vectors = mpmath.eigsy(inverse * k * inverse.T)
            return finished([judged(values[i], inverse.T * column(vectors, i), 1) for i in range(size)])
        for shift in (shift for shift in shifts if definite(stiffness - shift * geometric)):
            factor = cholesky(k - mpmath.mpf(shift) * g)
            if factor is None:
                continue
            inverse = mpmath.inverse(factor)
            mus, vectors = mpmath.eigsy(inverse * g * inverse.T)
            zero = floor * mpmath.mnorm(inverse, 1) ** 2 * g_size
            # Orthonormal in K - σG and with Gz = 0, ZᵀKZ = I.
            null_columns = [
                numpy.abs(numpy.array([float(v) for v in inverse.T * column(vectors, i)]))
                for i in range(size)
                if abs(mus[i]) <= zero
            ]
            nulls = (numpy.array(null_columns).T, numpy.eye(len(null_columns))) if null_columns else None
            return finished([
                judged(shift + 1 / mus[i], inverse.T * column(vectors, i), mus[i])
                for i in range(size)
                if abs(mus[i]) > zero
            ], nulls)
        for shift in shifts:
            shifted = k - mpmath.mpf(shift) * g
            # mpmath's own failures on a matrix it cannot invert are that too: a free gable
            # whose K and K_g share a translation read "'>=' not supported between 'NoneType'
            # and 'int'" (the second audit of 0.47.0).
            try:
                inverse = mpmath.inverse(shifted)
                if mpmath.mnorm(inverse, 1) * mpmath.mnorm(shifted, 1) > mpmath.mpf(10) ** 40:
                    continue
                mus, vectors = mpmath.eig(inverse * g, left=False, right=True)
            except (ZeroDivisionError, TypeError, ValueError, RuntimeError):
                continue
            zero = floor * mpmath.mnorm(inverse, 1) * g_size
            out = []
            nulls = []
            for i in range(size):
                if abs(mus[i]) <= zero:
                    z = column(vectors, i)
                    phase = max((z[j] for j in range(size)), key=abs)
                    z = mpmath.matrix([mpmath.re(z[j] / phase) for j in range(size)])
                    nulls.append(z)
                    continue
                value = shift + 1 / mus[i]
                if abs(mpmath.im(value)) > mpmath.mpf(10) ** -30 * max(abs(value), abs(shift)):
                    raise EngEvaluationError(
                        "eigenvals found eigenvalues that are not real; a stiffness and a geometric "
                        "stiffness have real ones - check that both matrices are symmetric"
                    )
                # A real λ of a symmetric pencil has a real vector, up to a phase.
                x = column(vectors, i)
                phase = max((x[j] for j in range(size)), key=abs)
                x = mpmath.matrix([mpmath.re(x[j] / phase) for j in range(size)])
                out.append(judged(mpmath.re(value), x, (x.T * g * x)[0]))
            if nulls:
                basis = mpmath.matrix([[z[j] for z in nulls] for j in range(size)])
                try:
                    gram = mpmath.inverse(basis.T * k * basis)
                    inverse_gram = numpy.abs(numpy.array([[float(gram[a, b]) for b in range(len(nulls))] for a in range(len(nulls))]))
                except (ZeroDivisionError, ValueError):
                    inverse_gram = numpy.full((len(nulls), len(nulls)), numpy.inf)
                null_vectors = numpy.abs(numpy.array([[float(z[j]) for z in nulls] for j in range(size)]))
                return finished(out, (null_vectors, inverse_gram))
            return finished(out)
        raise EngEvaluationError(
            "eigenvals(K, G): K - λG is singular for every λ - in a direction where G has "
            "nothing, K has nothing either, and any λ satisfies K x = λ G x; take those "
            "degrees of freedom out of both"
        )


def _pencil_unit(matrix: NumberMatrix, metric: NumberMatrix):
    """The unit of λ in K x = λ G x: K over G where both have an entry, or, written with
    plain zeros between them, the one unit of K over the one unit of G (the second audit:
    `[1[kN/m], 0; 0, 0]` against `[0, 0; 0, 1[kN/m]]`). None for a number."""
    pair = next(
        (k / g for k, g in zip(matrix.units, metric.units) if k is not None and g is not None),
        None,
    )
    if pair is not None:
        return pair
    stiffness = [unit for unit in matrix.units if unit is not None]
    geometric = [unit for unit in metric.units if unit is not None]
    if not stiffness or not geometric:
        return stiffness[0] if stiffness else (1 / geometric[0] if geometric else None)
    if all(unit == stiffness[0] for unit in stiffness) and all(unit == geometric[0] for unit in geometric):
        return stiffness[0] / geometric[0]
    raise EngEvaluationError(
        "eigenvals(K, G): the unit of λ cannot be told - no entry of K stands where G has "
        "one; write the zeros with their units, such as 0[kN/m]"
    )


def _unit_root(unit, power: int):
    """`unit` to the 1/power, or None when that is no unit with whole exponents."""
    exponents = {name: value / power for name, value in unit._units.items()}
    if any(abs(value - round(value)) > 1e-9 for value in exponents.values()):
        return None
    from pint.util import UnitsContainer

    return unit._REGISTRY.Unit(
        UnitsContainer({name: int(round(value)) for name, value in exponents.items() if round(value)})
    )


def _units_by_work(matrix: NumberMatrix, right: NumberMatrix, units: list) -> list:
    """The unit of each entry of a solution its load leaves unknown - a group of degrees
    of freedom that only written zeros load, so all its entries are 0 - from its own
    stiffness by work: `K_ii c_i²` is the work `F_j x_j` of an entry that is loaded. A
    metre against kN/m, nothing against kN·m (the third audit of 0.45.6: an axial load on a
    frame left its shear `12EI/L³ v` in kN/m). An entry whose diagonal is 0, or whose root
    has no whole exponents, stays unknown; so does any against a zero of unknown kind."""
    if right.worked_zeros:
        return units
    size, cols = matrix.rows, right.cols
    for col in range(cols):
        work = next(
            (
                right.units[row * cols + col] * units[row * cols + col]
                for row in range(size)
                if right.units[row * cols + col] is not None
                and units[row * cols + col] is not None
            ),
            None,
        )
        if work is None:
            continue
        for row in range(size):
            stiffness = matrix.units[row * size + row]
            # A stiffness's diagonal has a dimension (kN/m, kN·m, kg). One without is a
            # system of another kind - equilibrium, a transformation - whose loads are not
            # work (the fourth audit of 0.45.6: V of `[M; H; V]` read N·m).
            if (
                units[row * cols + col] is not None
                or stiffness is None
                or (1 * stiffness).dimensionless
            ):
                continue
            units[row * cols + col] = _unit_root(work / stiffness, 2)
    return units


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
    # An entry with no unit was given none by the load: every load of its group is a
    # written zero, and so is the entry. Its unit, where its stiffness says it.
    unknown = [unit is None for unit in units]
    units = _units_by_work(matrix, right, units)
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
        0.0 if unknown[row * right.cols + col] else float(columns[col][row])
        for row in range(matrix.rows)
        for col in range(right.cols)
    )
    return NumberMatrix(
        matrix.rows, right.cols, magnitudes, tuple(units),
        _worked_zeros(right.cols, units, matrix, right),
    )


def take_numbers(numbers: NumberMatrix, rows: list[int], cols: list[int]) -> NumberMatrix:
    indices = [row * numbers.cols + col for row in rows for col in cols]
    return NumberMatrix(
        len(rows),
        len(cols),
        tuple(numbers.magnitudes[i] for i in indices),
        tuple(numbers.units[i] for i in indices),
        frozenset(
            (i, j)
            for i, row in enumerate(rows)
            for j, col in enumerate(cols)
            if (row, col) in numbers.worked_zeros
        ),
    )


def blocks_of_numbers(block_rows: list[list[NumberMatrix]]) -> NumberMatrix:
    """`[K_jj, Z; Z, K_jj]`: matrices and numbers put side by side and one under another."""
    magnitudes: list[float] = []
    units: list[Any] = []
    worked: set[tuple[int, int]] = set()
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
        offset = 0
        for block in blocks:
            worked.update((height + row, offset + col) for row, col in block.worked_zeros)
            offset += block.cols
        height += rows
    return NumberMatrix(height, width, tuple(magnitudes), tuple(units), frozenset(worked))
