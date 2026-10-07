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
        try:
            inverse = inverse_numbers(metric)
        except EngEvaluationError as exc:
            if "singular" not in str(exc):
                raise
            # A frame's geometric stiffness always is: nothing along the bars, whose
            # eigenvalue is infinite (his book, chapter 10). The finite ones are found as
            # the inverses of those of K⁻¹ G that are not zero.
            return _finite_eigenvalues(matrix, metric)
        # G⁻¹K tells the unit and refuses units that do not fit; its numbers do not serve:
        # a G singular only to round-off inverts, and G⁻¹K's eigenvalues were noise - 1e16
        # and -0.33 for 0.165 (the second audit). The values come from the shifted pencil.
        product = multiply_numbers(inverse, matrix)
        _inverse_units(product, operation)
        return _finite_eigenvalues(matrix, metric, unit=_eigenvalue_unit(product))
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


def _finite_eigenvalues(matrix: NumberMatrix, metric: NumberMatrix, unit=None) -> NumberMatrix:
    """`eigenvals(K, G)`: the finite λ of K x = λ G x, smallest first.

    Worked out in 60 figures on the entries exactly as the floats hold them
    (`_exact_pencil_values`). Seven audits of a method in floats each found a silently wrong
    λ - supports and links written as springs of 1e16-1e20, a G singular to round-off - and
    every one was the solver's round-off, not the matrices': in 60 figures a 1e20 spring
    beside a soft mode leaves forty to spare.

    What the floats of the entries themselves do not settle is told by asking again with
    every entry moved by 1e-14 of itself - zeros stay zeros, a symmetric matrix stays so:
    a λ that holds is printed; one that only a G singular to round-off makes finite runs off
    to ±1e16 and is infinite; a mechanism's λ that scatters around 0 is 0; anything else is
    refused. A wrong λ is not printed."""
    import numpy

    size = matrix.rows
    if unit is None:
        # With G singular nothing inverted K: its units are checked as its inverse checks
        # them (the third audit: an entry in kN/m among kN·m read in kN).
        _inverse_units(matrix, "eigenvals")
    stiffness = numpy.array(matrix.magnitudes, dtype=float).reshape(size, size)
    geometric = numpy.array(metric.magnitudes, dtype=float).reshape(size, size)
    if not numpy.abs(geometric).max():
        raise EngEvaluationError("eigenvals(K, G): the second matrix is zero; there is no finite eigenvalue")
    symmetric = bool((stiffness == stiffness.T).all() and (geometric == geometric.T).all())
    first = _exact_pencil_values(stiffness, geometric, symmetric)
    trials = numpy.random.default_rng(20261006)
    runs = [
        _exact_pencil_values(
            _moved(stiffness, trials, symmetric), _moved(geometric, trials, symmetric), symmetric, refuse=False
        )
        for _ in range(2)
    ]
    finite = _settled(first, runs)
    if unit is None:
        unit = _pencil_unit(matrix, metric)
    units = tuple(unit for _ in finite)
    return NumberMatrix(len(finite), 1, tuple(finite), units, _unitless_zeros(1, units))


_UNSETTLED = (
    "eigenvals(K, G): these eigenvalues cannot be told with the figures a float holds - a "
    "change of 1e-14 in the entries moves them; G is singular or nearly in a way the numbers "
    "do not settle. Take out the degrees of freedom where G has (almost) nothing, or write it "
    "exactly"
)


def _moved(numbers, trials, symmetric: bool):
    """Every entry moved by about 1e-14 of itself: a zero stays 0, a symmetric matrix stays so."""
    noise = trials.standard_normal(numbers.shape)
    if symmetric:
        noise = (noise + noise.T) / 2
    return numbers * (1 + 1e-14 * noise)


def _settled(first: list[float], runs: list) -> list[float]:
    """The λ the entries settle, from the exact answers to them as written and moved by 1e-14.

    Held to a tenth of itself in every run, a λ is printed as the exact answer to the entries
    as written: a move of 1e-14 is a hundred times a float's round-off, so a λ that moves by a
    tenth under it moves by a thousandth under the round-off that made the entries - two
    stiff DOFs tied by a 1e12 spring, whose soft λ = 1 is (1 + P) - P, as main printed it
    (the audits' A_tie). Running off - more than 1e8 times
    the largest that holds - it is a direction G has only to round-off, whose λ is infinite
    (the second audit: an inclined bar whose G is c² and s² products). Scattered around 0,
    below 1e-8 of the smallest that holds, it is a mechanism's 0. Anything else - a soft
    mode beside a 1e17 N/m link that reads 0.99, 1.11 and 1.21 - is refused."""
    if any(run is None for run in runs):
        raise EngEvaluationError(_UNSETTLED)
    # Each λ beside the nearest of each run, not the one in the same place: one that runs
    # off changes sign, and sorted by value it took another's place. A G singular exactly
    # in the floats as written is not once moved, and that run has one more, running off
    # (a pinned column on 1e16 springs: 3e30); it is left over, or this one has none.
    columns = [[value] for value in first]
    left_over = []
    left_by_run = []
    # Near 0 by how far apart, not by how much of themselves: -9e-15 and 1.3e-11 are both a
    # mechanism's 0, and each is as far from the other as from 5 (found writing this).
    floor = 1e-10 * max((abs(value) for value in first), default=0.0)
    for run in runs:
        free = list(run)
        for index in sorted(range(len(first)), key=lambda i: abs(first[i])):
            value = first[index]
            if not free:
                columns[index].append(None)
                continue
            nearest = min(free, key=lambda v: abs(v - value) / (max(abs(v), abs(value)) + floor or 1.0))
            free.remove(nearest)
            columns[index].append(nearest)
        left_over.extend(free)
        left_by_run.append(free)

    def holds(values):
        return None not in values and max(values) - min(values) <= 0.1 * max(abs(v) for v in values)

    held = [abs(values[0]) for values in columns if holds(values) and values[0]]
    largest = max(held, default=0.0)
    smallest = min(held, default=float("inf"))
    if any(not held or abs(value) < 1e8 * largest for value in left_over):
        raise EngEvaluationError(_UNSETTLED)
    # Left over in both moved runs and agreeing, it is a λ that holds and this run lost:
    # refused, never dropped as one running off (the battery of 0.47.0: a 1e14 spring's λ).
    first_left, second_left = left_by_run
    if any(abs(a - b) <= 0.1 * max(abs(a), abs(b)) for a in first_left for b in second_left):
        raise EngEvaluationError(_UNSETTLED)
    finite = []
    for values in columns:
        if holds(values):
            finite.append(values[0])
        elif held and min(abs(v) for v in values if v is not None) >= 1e8 * largest:
            continue
        elif None in values:
            raise EngEvaluationError(_UNSETTLED)
        elif (min(values) <= 0.0 <= max(values) or abs(sum(values)) / 3 <= max(values) - min(values)) and (
            max(abs(v) for v in values) <= 1e-8 * smallest
        ):
            finite.append(0.0)
        else:
            raise EngEvaluationError(_UNSETTLED)
    return finite


_PENCIL_FIGURES = 60


def _exact_pencil_values(stiffness, geometric, symmetric: bool, refuse: bool = True):
    """The finite λ of K x = λ G x, smallest first, worked out in `_PENCIL_FIGURES` figures
    on the floats as they are; None for a pencil refused when `refuse` is False.

    Symmetric, through a Cholesky factor: of G when it is positive definite (a mass, his
    `eigenvals(-K_g, K)`), else of K - σG, whose μ in L⁻¹ G L⁻ᵀ give λ = σ + 1/μ - a μ of 0
    is a direction G does not have, and its λ is infinite. Otherwise through (K - σG)⁻¹ G.
    σ is the best conditioned of a ladder, measured in floats: the first that inverted was
    σ = 0 beside a K singular to round-off, whose μ of 1e16 made the μ of a 1e14 spring look
    like a zero, and that λ was lost (the battery of 0.47.0). A μ is 0 against what 0 leaves
    in these figures, ‖(K - σG)⁻¹‖ ‖G‖ 10⁻⁴⁵, not against the largest μ. Refused when no σ
    inverts - K - λG is singular for every λ - and when a λ is not real."""
    import mpmath
    import numpy

    def refused(message: str):
        if refuse:
            raise EngEvaluationError(message)
        return None

    size = stiffness.shape[0]
    k_norm = numpy.abs(stiffness).sum(axis=0).max()
    g_norm = numpy.abs(geometric).sum(axis=0).max()
    scale = k_norm / g_norm if k_norm else 1.0
    shifts = [0.0] + [sign * 1.37 * 10.0 ** power * scale for power in range(-8, 9) for sign in (-1, 1)]

    def condition(matrix) -> float:
        with numpy.errstate(all="ignore"):
            try:
                value = float(numpy.linalg.cond(matrix))
            except numpy.linalg.LinAlgError:
                return float("inf")
        return value if numpy.isfinite(value) else float("inf")

    def definite(matrix) -> bool:
        try:
            numpy.linalg.cholesky(matrix)
        except numpy.linalg.LinAlgError:
            return False
        return True

    with mpmath.workdps(_PENCIL_FIGURES):
        k = mpmath.matrix(stiffness.tolist())
        g = mpmath.matrix(geometric.tolist())
        zero = mpmath.mpf(10) ** -45

        def cholesky(m):
            try:
                factor = mpmath.cholesky(m)
            except (ValueError, ZeroDivisionError):
                return None
            if any(factor[i, i] <= 0 for i in range(size)):
                return None
            return factor

        def cleaned(values, reference):
            top = max([abs(v) for v in values] + [abs(reference)])
            return sorted(float(v) if abs(v) > zero * zero * top else 0.0 for v in values)

        if symmetric:
            factor = cholesky(g) if definite(geometric) else None
            if factor is not None:
                inverse = mpmath.inverse(factor)
                values = mpmath.eigsy(inverse * k * inverse.T, eigvals_only=True)
                return cleaned([values[i] for i in range(size)], 0)
            candidates = sorted(
                (shift for shift in shifts if definite(stiffness - shift * geometric)),
                key=lambda shift: condition(stiffness - shift * geometric),
            )
            for shift in candidates:
                factor = cholesky(k - mpmath.mpf(shift) * g)
                if factor is None:
                    continue
                inverse = mpmath.inverse(factor)
                mus = mpmath.eigsy(inverse * g * inverse.T, eigvals_only=True)
                floor = zero * mpmath.mnorm(inverse, 1) ** 2 * mpmath.mnorm(g, 1)
                return cleaned([shift + 1 / mus[i] for i in range(size) if abs(mus[i]) > floor], shift)
        candidates = sorted(shifts, key=lambda shift: condition(stiffness - shift * geometric))
        for shift in candidates:
            shifted = k - mpmath.mpf(shift) * g
            try:
                inverse = mpmath.inverse(shifted)
            except ZeroDivisionError:
                continue
            if mpmath.mnorm(inverse, 1) * mpmath.mnorm(shifted, 1) > mpmath.mpf(10) ** (_PENCIL_FIGURES - 10):
                continue
            mus = mpmath.eig(inverse * g, left=False, right=False)
            floor = zero * mpmath.mnorm(inverse, 1) * mpmath.mnorm(g, 1)
            kept = [mus[i] for i in range(size) if abs(mus[i]) > floor]
            if any(abs(mpmath.im(mu)) > mpmath.mpf(10) ** -20 * abs(mu) for mu in kept):
                return refused(
                    "eigenvals found eigenvalues that are not real; a stiffness and a geometric "
                    "stiffness have real ones - check that both matrices are symmetric"
                )
            return cleaned([shift + 1 / mpmath.re(mu) for mu in kept], shift)
        return refused(
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
