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
    """`eigenvals(K, G)`: the finite λ of K x = λ G x, smallest first (`_pencil_values`).

    Four audits of these fixes found a silently wrong λ in each way tried first - a shift
    of K, a cut on the size of μ, a Rayleigh quotient - and the fourth one a pencil no
    float can answer, whose G is singular to 1e-12 in exact arithmetic (5e-7 read 2.7e-6;
    main read 1.8e-7). So the answer is asked again with the entries moved by 1e-13 - zeros
    stay zeros - and refused when it moves by more than 1e-6 of itself, or changes how many
    there are: those figures are not in the numbers. A wrong λ is not printed."""
    import numpy

    size = matrix.rows
    if unit is None:
        # With G singular nothing inverted K: its units are checked as its inverse checks
        # them (the third audit: an entry in kN/m among kN·m read in kN).
        _inverse_units(matrix, "eigenvals")
    stiffness = numpy.array(matrix.magnitudes, dtype=float).reshape(size, size)
    geometric = numpy.array(metric.magnitudes, dtype=float).reshape(size, size)
    finite = _pencil_values(stiffness, geometric)
    # A move of 1e-14 is a hundred times a float's own round-off: a λ it moves by 1e-3 of
    # itself is 1e-5 off as written - inside the figures the page shows.
    largest = max(
        max(abs(value) for value in finite),
        numpy.linalg.norm(stiffness, 2) / numpy.linalg.norm(geometric, 2),
    )
    trials = numpy.random.default_rng(20261006)
    for _ in range(2):
        moved = _pencil_values(
            stiffness * (1 + 1e-14 * trials.standard_normal(stiffness.shape)),
            geometric * (1 + 1e-14 * trials.standard_normal(geometric.shape)),
            refuse=False,
        )
        if moved is None or len(moved) != len(finite) or any(
            abs(a - b) > 1e-3 * abs(a) + 1e-10 * largest for a, b in zip(finite, moved)
        ):
            raise EngEvaluationError(
                "eigenvals(K, G): these eigenvalues cannot be told with the figures a float "
                "holds - a change of 1e-14 in the entries moves them; G is singular or nearly "
                "in a way the numbers do not settle. Take out the degrees of freedom where G "
                "has (almost) nothing, or write it exactly"
            )
    if unit is None:
        unit = _pencil_unit(matrix, metric)
    units = tuple(unit for _ in finite)
    return NumberMatrix(len(finite), 1, tuple(finite), units, _unitless_zeros(1, units))


def _pencil_values(stiffness, geometric, refuse: bool = True):
    """The finite λ of K x = λ G x in floats, smallest first; None for a pencil refused when
    `refuse` is False.

    Scaled by G's own diagonal, every entry that is not 0 (a G spanning 24 decades lost its
    1e12 when only the large ones were - the fourth audit), which leaves λ as they are. A G
    that inverts well is read as main read every pencil, the eigenvalues of G⁻¹K. A singular
    G - a frame's geometric stiffness, a lumped mass (his book, chapter 10) - is taken apart
    exactly: with G = U S Vᵀ, Uᵀ(K - λG)V = K' - λS, and the directions where S is 0 are
    condensed out, K* = K'aa - K'ab K'bb⁻¹ K'ba, as a static condensation takes out a
    massless degree of freedom; what is left has a G that inverts. Refused when K'bb is
    singular: where G has nothing K has nothing either, and any λ satisfies K x = λ G x."""
    import numpy

    def refused(message: str):
        if refuse:
            raise EngEvaluationError(message)
        return None

    if not numpy.abs(geometric).max():
        return refused("eigenvals(K, G): the second matrix is zero; there is no finite eigenvalue")
    own = numpy.abs(numpy.diag(geometric))
    floor = own.max() if own.max() else numpy.abs(geometric).max()
    factor = 1.0 / numpy.sqrt(numpy.where(own > 0, own, floor))
    stiffness = factor[:, None] * stiffness * factor[None, :]
    geometric = factor[:, None] * geometric * factor[None, :]

    if numpy.linalg.cond(geometric) <= 1e10:
        values = numpy.linalg.eigvals(numpy.linalg.solve(geometric, stiffness))
    else:
        left, singular, right = numpy.linalg.svd(geometric)
        # A λ that hangs on what G holds below 1e-12 of its largest direction is round-off
        # (the fourth audit: 2.9967 for 3.0006), and that direction is one G does not have.
        null = singular <= 1e-12 * singular[0]
        if not null.any():
            values = numpy.linalg.eigvals(numpy.linalg.solve(geometric, stiffness))
        else:
            reduced = left.T @ stiffness @ right.T
            a, b = ~null, null
            kept = reduced[numpy.ix_(b, b)]
            # Against all of K, not K'bb's own condition: one direction is a 1 x 1 block,
            # whose condition is 1 however near 0 it is.
            if numpy.linalg.svd(kept, compute_uv=False).min() <= 1e-12 * numpy.linalg.norm(stiffness, 2):
                return refused(
                    "eigenvals(K, G): K - λG is singular for every λ - in a direction where "
                    "G has nothing, K has nothing either, and any λ satisfies K x = λ G x; "
                    "take those degrees of freedom out of both"
                )
            condensed = reduced[numpy.ix_(a, a)] - reduced[numpy.ix_(a, b)] @ numpy.linalg.solve(
                kept, reduced[numpy.ix_(b, a)]
            )
            values = numpy.linalg.eigvals(condensed / singular[a][:, None])
    if refuse:
        _refuse_complex(values, values)
    finite = sorted(float(value.real) for value in values)
    # Every pencil: one a little out of symmetry went unpolished and G⁻¹K's bias beside a
    # stiff spring through (the fifth audit: 1570.18 for 1515.90).
    symmetric = numpy.allclose(stiffness, stiffness.T, rtol=1e-10, atol=0) and numpy.allclose(
        geometric, geometric.T, rtol=1e-10, atol=0
    )
    # The λ that are 0 - a mechanism, or a singular first matrix as in his `eigenvals(-K_g, K)`
    # (his book, problem 10.9: ten of seventeen) - have no K - λG to iterate on. They are as
    # many as the directions K has nothing in; when the estimates that are 0 beside the
    # largest count exactly those, each is 0, verified by K's own rank.
    # K's null directions are its singular values at round-off of a typical column of K -
    # the median of those that are not 0. Against the largest, a 1e20 kN/m spring made
    # ω₁² = 1515.90 a zero; component by component, the null directions of his -K_g, whose
    # entries there are round-off themselves, did not count (both found writing this).
    top = max(abs(value) for value in finite) if finite else 0.0
    zero = [abs(value) <= 1e-12 * top for value in finite]
    columns = numpy.linalg.norm(stiffness, axis=0)
    typical = float(numpy.median(columns[columns > 0])) if numpy.any(columns > 0) else 0.0
    nullity = int(numpy.sum(numpy.linalg.svd(stiffness, compute_uv=False) <= 1e-12 * typical))
    if not any(zero) or sum(zero) != nullity:
        zero = [False for _ in finite]
    polished = [
        (0.0, True)
        if zero[index]
        else _polished(value, stiffness, geometric, finite[:index] + finite[index + 1:], symmetric)
        for index, value in enumerate(finite)
    ]
    if not all(verified for _value, verified in polished):
        return refused(
            "eigenvals(K, G): these eigenvalues cannot be told with the figures a float "
            "holds - one does not settle as an eigenvalue of K and G; a stiffness far "
            "beyond the rest (a support written as a spring) does this - take that degree "
            "of freedom out instead"
        )
    finite = sorted(value for value, _verified in polished)
    if not finite:
        return refused(
            "eigenvals(K, G): the second matrix has nothing in any direction; there is no "
            "finite eigenvalue"
        )
    return finite


def _polished(value: float, stiffness, geometric, others, symmetric: bool = True) -> tuple[float, bool]:
    """A λ of the pencil, polished, and whether it is verified.

    G⁻¹K reads a small λ beside a stiff spring with a bias no perturbation shows (the third
    audit's column: 1517.60 for 1517.59, and 1512.23 with a 1e20 spring). Inverse iteration
    on K - λG from where it was found, then the Rayleigh quotient xᵀKx / xᵀGx; taken when
    the pair's residual is round-off against |K||x| + |λ||G||x| - it is then a λ of the
    pencil - and it stayed nearer its own estimate than half the gap to the next one, so it
    is this λ and not a neighbour."""
    import numpy

    # A repeated λ - K = 2G, the three rigid-body zeros of a free frame - is no neighbour:
    # landing on its twin is landing on it.
    spread = max((abs(other) for other in others), default=0.0) + abs(value)
    gap = min(
        (abs(value - other) for other in others if abs(value - other) > 1e-6 * spread),
        default=numpy.inf,
    )
    # Not an evenly spaced start: 1, 1.5, 2 is orthogonal to a chain's [1, -2, 1], and the
    # iteration never found that mode.
    start = numpy.random.default_rng(7).uniform(0.5, 1.5, len(stiffness))
    vector, left = start, start
    polished = value
    for _ in range(10):
        previous = polished
        try:
            shifted = stiffness - polished * geometric
            vector = numpy.linalg.solve(shifted, geometric @ vector)
            # Out of symmetry the quotient is two-sided, yᵀKx / yᵀGx with y from (K - λG)ᵀ,
            # and keeps the second-order accuracy xᵀKx / xᵀGx has for a symmetric pencil.
            left = vector if symmetric else numpy.linalg.solve(shifted.T, geometric.T @ left)
        except numpy.linalg.LinAlgError:
            return polished, True  # K - λG singular to the last bit: λ is one
        if not (numpy.all(numpy.isfinite(vector)) and numpy.all(numpy.isfinite(left))):
            return value, False
        if not numpy.abs(vector).max() or not numpy.abs(left).max():
            return value, False
        vector = vector / numpy.abs(vector).max()
        left = left / numpy.abs(left).max()
        weight = left @ geometric @ vector
        if abs(weight) <= 1e-12 * (numpy.abs(left) @ numpy.abs(geometric) @ numpy.abs(vector)):
            return value, False
        polished = float((left @ stiffness @ vector) / weight)
        # Until it stops moving: an estimate 1% off, as G⁻¹K gives beside a 1e20 spring out of
        # symmetry, took more than the four steps first allowed.
        if abs(polished - previous) <= 1e-15 * max(abs(polished), 1e-300):
            break
    residual = numpy.linalg.norm(stiffness @ vector - polished * (geometric @ vector))
    size = numpy.linalg.norm(numpy.abs(stiffness) @ numpy.abs(vector)) + abs(polished) * numpy.linalg.norm(
        numpy.abs(geometric) @ numpy.abs(vector)
    )
    if residual <= 1e-10 * size and abs(polished - value) < 0.5 * gap:
        return polished, True
    return value, False


def _refuse_complex(values, judged) -> None:
    """Refused when an eigenvalue is not real: each by its own size, above the round-off of
    the whole spectrum (the review of #395)."""
    top = max((abs(value) for value in values), default=0.0) or 1.0
    if any(abs(value.imag) > 1e-9 * abs(value) + 1e-13 * top for value in judged):
        raise EngEvaluationError(
            "eigenvals found eigenvalues that are not real; a stiffness and a geometric "
            "stiffness have real ones - check that both matrices are symmetric"
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
