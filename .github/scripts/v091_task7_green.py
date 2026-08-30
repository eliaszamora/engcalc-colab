from pathlib import Path

PATH = Path("src/engcalc_colab/characteristics.py")
text = PATH.read_text(encoding="utf-8")

if "_FALLBACK_SCAN_COUNT = 1025" in text:
    raise SystemExit("Task 7 fallback already present; guarded patch will not reapply")

# 1. Runtime import + fixed fallback contract constants.
old = "import math\nfrom dataclasses import dataclass\n"
new = "import math\n\nimport mpmath as mp\nfrom dataclasses import dataclass\n"
if old not in text:
    raise SystemExit("Task 7 patch guard failed: import anchor not found")
text = text.replace(old, new, 1)

old = "from .piecewise import extract_symbolic_breakpoints\n\n\n@dataclass(frozen=True)\nclass AnalysisDomain:"
new = """from .piecewise import extract_symbolic_breakpoints


_FALLBACK_SCAN_COUNT = 1025
_FALLBACK_REL_RESIDUAL_TOL = 1e-9
_FALLBACK_X_DEDUP_REL_TOL = 1e-10


@dataclass(frozen=True)
class AnalysisDomain:"""
if old not in text:
    raise SystemExit("Task 7 patch guard failed: constants anchor not found")
text = text.replace(old, new, 1)

# 2. Common numerical root fallback. It samples AnalysisDomain directly and never
#    calls NumericContext.build_plot_sample_points/sample_symbolic.
marker = "\ndef solve_roots_exact(\n"
if text.count(marker) != 1:
    raise SystemExit("Task 7 patch guard failed: solve_roots_exact anchor mismatch")

helpers = r'''


def _fallback_response_quantity(
    expression: sp.Expr,
    variable: sp.Symbol,
    x_quantity,
    context,
    *,
    overrides: dict[str, Any] | None,
):
    sample_overrides = dict(overrides or {})
    sample_overrides[variable.name] = x_quantity
    try:
        _, quantity = context.evaluate_symbolic(
            expression,
            overrides=sample_overrides,
        )
    except EngEvaluationError:
        return None
    try:
        magnitude = float(quantity.magnitude)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(magnitude):
        return None
    return quantity


def _fallback_magnitude_in_unit(quantity, canonical_unit, context):
    if quantity is None:
        return None
    if quantity.dimensionless and canonical_unit != context.ureg.dimensionless:
        try:
            magnitude = float(quantity.magnitude)
        except (TypeError, ValueError, OverflowError):
            return None
        if magnitude != 0.0:
            return None
        return 0.0
    try:
        converted = quantity.to(canonical_unit)
        magnitude = float(converted.magnitude)
    except (DimensionalityError, TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(magnitude):
        return None
    return magnitude


def _fallback_canonical_unit(quantities, context):
    for quantity in quantities:
        if quantity is not None and not quantity.dimensionless:
            return quantity.units
    for quantity in quantities:
        if quantity is not None:
            return quantity.units
    return context.ureg.dimensionless


def _fallback_root_point(
    expression: sp.Expr,
    variable: sp.Symbol,
    x_magnitude: float,
    domain: AnalysisDomain,
    context,
    canonical_unit,
    response_scale: float,
    *,
    overrides: dict[str, Any] | None,
    source_label: str | None,
) -> CharacteristicPoint | None:
    if not math.isfinite(x_magnitude):
        return None
    lower = float(domain.lower_quantity.to(domain.unit).magnitude)
    upper = float(domain.upper_quantity.to(domain.unit).magnitude)
    span = abs(upper - lower)
    x_tolerance = _FALLBACK_X_DEDUP_REL_TOL * max(1.0, span)
    if x_magnitude < lower - x_tolerance or x_magnitude > upper + x_tolerance:
        return None
    if x_magnitude < lower:
        x_magnitude = lower
    elif x_magnitude > upper:
        x_magnitude = upper

    x_quantity = context.ureg.Quantity(x_magnitude, domain.unit)
    value_quantity = _fallback_response_quantity(
        expression,
        variable,
        x_quantity,
        context,
        overrides=overrides,
    )
    residual = _fallback_magnitude_in_unit(value_quantity, canonical_unit, context)
    if residual is None:
        return None
    relative_residual = abs(residual) / max(1.0, response_scale)
    if relative_residual > _FALLBACK_REL_RESIDUAL_TOL:
        return None

    return CharacteristicPoint(
        x_symbolic=sp.Float(x_magnitude, 17),
        x_quantity=x_quantity,
        value_symbolic=sp.Float(residual, 17),
        value_quantity=value_quantity,
        provenance="numeric",
        side="at",
        roles=("root",),
        source_label=source_label,
    )


def _deduplicate_root_points(
    points: list[CharacteristicPoint],
    domain: AnalysisDomain,
) -> tuple[CharacteristicPoint, ...]:
    if not points:
        return ()
    points = sorted(
        points,
        key=lambda point: float(point.x_quantity.to(domain.unit).magnitude),
    )
    span = abs(
        float(domain.upper_quantity.to(domain.unit).magnitude)
        - float(domain.lower_quantity.to(domain.unit).magnitude)
    )
    tolerance = _FALLBACK_X_DEDUP_REL_TOL * max(1.0, span)
    unique: list[CharacteristicPoint] = []
    for point in points:
        if not unique:
            unique.append(point)
            continue
        current = float(point.x_quantity.to(domain.unit).magnitude)
        previous = float(unique[-1].x_quantity.to(domain.unit).magnitude)
        if math.isclose(current, previous, rel_tol=0.0, abs_tol=tolerance):
            if unique[-1].provenance == "numeric" and point.provenance == "exact":
                unique[-1] = point
            continue
        unique.append(point)
    return tuple(unique)


def _fallback_roots(
    expression: sp.Expr,
    variable: sp.Symbol,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None = None,
    source_label: str | None = None,
) -> tuple[CharacteristicPoint, ...]:
    expression = sp.sympify(expression)
    lower = float(domain.lower_quantity.to(domain.unit).magnitude)
    upper = float(domain.upper_quantity.to(domain.unit).magnitude)
    span = upper - lower
    if not math.isfinite(lower) or not math.isfinite(upper) or span <= 0:
        raise EngEvaluationError(
            "characteristic numerical fallback could not validate a solution set"
        )

    x_magnitudes = tuple(
        lower + span * (index / (_FALLBACK_SCAN_COUNT - 1))
        for index in range(_FALLBACK_SCAN_COUNT)
    )
    quantities = tuple(
        _fallback_response_quantity(
            expression,
            variable,
            context.ureg.Quantity(x_magnitude, domain.unit),
            context,
            overrides=overrides,
        )
        for x_magnitude in x_magnitudes
    )
    canonical_unit = _fallback_canonical_unit(quantities, context)
    values = tuple(
        _fallback_magnitude_in_unit(quantity, canonical_unit, context)
        for quantity in quantities
    )
    finite_values = [value for value in values if value is not None]
    if not finite_values:
        raise EngEvaluationError(
            "characteristic numerical fallback could not validate a solution set"
        )
    response_scale = max(abs(value) for value in finite_values)

    def residual_callback(value):
        x_magnitude = float(value)
        quantity = _fallback_response_quantity(
            expression,
            variable,
            context.ureg.Quantity(x_magnitude, domain.unit),
            context,
            overrides=overrides,
        )
        residual = _fallback_magnitude_in_unit(quantity, canonical_unit, context)
        if residual is None or not math.isfinite(residual):
            raise ValueError("non-finite characteristic residual")
        return residual

    candidate_magnitudes: list[float] = []
    denominator = max(1.0, response_scale)

    # Grid seeds already satisfying the residual contract.
    for x_magnitude, value in zip(x_magnitudes, values):
        if value is None:
            continue
        if abs(value) / denominator <= _FALLBACK_REL_RESIDUAL_TOL:
            candidate_magnitudes.append(x_magnitude)

    def refine(left: float, right: float):
        if not (math.isfinite(left) and math.isfinite(right)) or left == right:
            return
        try:
            root = mp.findroot(
                residual_callback,
                (mp.mpf(str(left)), mp.mpf(str(right))),
                tol=mp.mpf("1e-14"),
                maxsteps=100,
            )
            root_float = float(root)
        except (ValueError, TypeError, ZeroDivisionError, OverflowError, ArithmeticError):
            return
        if math.isfinite(root_float):
            candidate_magnitudes.append(root_float)

    # Sign-changing brackets are guaranteed to remain inside this one continuous
    # AnalysisDomain. Piecewise callers invoke this once per ContinuousRegion.
    for index in range(_FALLBACK_SCAN_COUNT - 1):
        left_value = values[index]
        right_value = values[index + 1]
        if left_value is None or right_value is None:
            continue
        if left_value * right_value < 0.0:
            refine(x_magnitudes[index], x_magnitudes[index + 1])

    # Even-multiplicity roots do not change sign. Strict local minima of |f|
    # supply deterministic neighboring starting values for the same refinement.
    for index in range(1, _FALLBACK_SCAN_COUNT - 1):
        left_value = values[index - 1]
        center_value = values[index]
        right_value = values[index + 1]
        if left_value is None or center_value is None or right_value is None:
            continue
        if abs(center_value) < abs(left_value) and abs(center_value) < abs(right_value):
            refine(x_magnitudes[index - 1], x_magnitudes[index + 1])

    validated: list[CharacteristicPoint] = []
    for x_magnitude in candidate_magnitudes:
        point = _fallback_root_point(
            expression,
            variable,
            x_magnitude,
            domain,
            context,
            canonical_unit,
            response_scale,
            overrides=overrides,
            source_label=source_label,
        )
        if point is not None:
            validated.append(point)

    ordered = _deduplicate_root_points(validated, domain)
    if not ordered:
        raise EngEvaluationError(
            "characteristic numerical fallback could not validate a solution set"
        )
    return ordered
'''
text = text.replace(marker, helpers + marker, 1)

# 3. Wire fallback into ordinary and Piecewise root solving.
old = """        candidates, unresolved = _exact_real_solution_set(expression, variable)
        if unresolved:
            return (), (), True

        points: list[CharacteristicPoint] = []
"""
new = """        candidates, unresolved = _exact_real_solution_set(expression, variable)
        if unresolved:
            return (
                _fallback_roots(
                    expression,
                    variable,
                    domain,
                    context,
                    overrides=overrides,
                    source_label=source_label,
                ),
                (),
                False,
            )

        points: list[CharacteristicPoint] = []
"""
if old not in text:
    raise SystemExit("Task 7 patch guard failed: continuous roots unresolved block not found")
text = text.replace(old, new, 1)

old = "return _ordered_unique_points(points, domain), (), False"
if old not in text:
    raise SystemExit("Task 7 patch guard failed: continuous root ordering anchor not found")
text = text.replace(old, "return _deduplicate_root_points(points, domain), (), False", 1)

old = """        candidates, unresolved = _exact_real_solution_set(branch_expression, variable)
        unresolved_any = unresolved_any or unresolved
        if unresolved:
            continue
        for candidate in candidates:
"""
new = """        candidates, unresolved = _exact_real_solution_set(branch_expression, variable)
        if unresolved:
            region_domain = AnalysisDomain(
                lower_symbolic=region.lower_symbolic,
                upper_symbolic=region.upper_symbolic,
                lower_quantity=region.lower_quantity,
                upper_quantity=region.upper_quantity,
                unit=domain.unit,
            )
            fallback_points = _fallback_roots(
                branch_expression,
                variable,
                region_domain,
                context,
                overrides=overrides,
                source_label=source_label,
            )
            for point in fallback_points:
                if _candidate_in_region(point.x_quantity, region, domain):
                    points.append(point)
            continue
        for candidate in candidates:
"""
if old not in text:
    raise SystemExit("Task 7 patch guard failed: Piecewise roots unresolved block not found")
text = text.replace(old, new, 1)

# First ordered_points occurrence belongs to solve_roots_exact.
old = "ordered_points = _ordered_unique_points(points, domain)"
if old not in text:
    raise SystemExit("Task 7 patch guard failed: root merged ordering anchor not found")
text = text.replace(old, "ordered_points = _deduplicate_root_points(points, domain)", 1)

# 4. Numeric intersection materialization with common-response validation.
marker = "\ndef _coincident_interval(\n"
if text.count(marker) != 1:
    raise SystemExit("Task 7 patch guard failed: intersection helper anchor mismatch")
intersection_helper = r'''


def _evaluate_numeric_intersection_candidate(
    left_expression: sp.Expr,
    right_expression: sp.Expr,
    variable: sp.Symbol,
    root_point: CharacteristicPoint,
    context,
    *,
    overrides: dict[str, Any] | None,
    left_label: str | None,
    right_label: str | None,
) -> CharacteristicPoint | None:
    pair = _evaluate_response_pair(
        left_expression,
        right_expression,
        variable,
        root_point.x_quantity,
        context,
        overrides=overrides,
    )
    if pair is None:
        return None
    left_quantity, right_quantity = pair
    try:
        left_magnitude = float(left_quantity.magnitude)
        right_magnitude = float(right_quantity.to(left_quantity.units).magnitude)
    except (DimensionalityError, TypeError, ValueError, OverflowError):
        return None
    scale = max(1.0, abs(left_magnitude), abs(right_magnitude))
    if not math.isclose(
        left_magnitude,
        right_magnitude,
        rel_tol=_FALLBACK_REL_RESIDUAL_TOL,
        abs_tol=_FALLBACK_REL_RESIDUAL_TOL * scale,
    ):
        return None
    symbolic_value = sp.simplify(
        sp.sympify(left_expression).subs(variable, root_point.x_symbolic)
    )
    return CharacteristicPoint(
        x_symbolic=root_point.x_symbolic,
        x_quantity=root_point.x_quantity,
        value_symbolic=symbolic_value,
        value_quantity=left_quantity,
        provenance="numeric",
        side="at",
        roles=("intersection",),
        source_label=_intersection_source_label(left_label, right_label),
    )
'''
text = text.replace(marker, intersection_helper + marker, 1)

old = """        candidates, unresolved = _exact_real_solution_set(difference, variable)
        unresolved_any = unresolved_any or unresolved
        if unresolved:
            continue
        for candidate in candidates:
"""
new = """        candidates, unresolved = _exact_real_solution_set(difference, variable)
        if unresolved:
            region_domain = AnalysisDomain(
                lower_symbolic=region.lower_symbolic,
                upper_symbolic=region.upper_symbolic,
                lower_quantity=region.lower_quantity,
                upper_quantity=region.upper_quantity,
                unit=domain.unit,
            )
            fallback_points = _fallback_roots(
                difference,
                variable,
                region_domain,
                context,
                overrides=overrides,
                source_label=_intersection_source_label(left_label, right_label),
            )
            for root_point in fallback_points:
                if not _candidate_strictly_inside_intersection_region(
                    root_point.x_quantity,
                    region,
                    domain,
                ):
                    continue
                point = _evaluate_numeric_intersection_candidate(
                    left_expression,
                    right_expression,
                    variable,
                    root_point,
                    context,
                    overrides=overrides,
                    left_label=left_label,
                    right_label=right_label,
                )
                if point is not None:
                    points.append(point)
            continue
        for candidate in candidates:
"""
if old not in text:
    raise SystemExit("Task 7 patch guard failed: intersection unresolved block not found")
text = text.replace(old, new, 1)

# The next ordered_points occurrence belongs to intersections.
old = "ordered_points = _ordered_unique_points(points, domain)"
if old not in text:
    raise SystemExit("Task 7 patch guard failed: intersection ordering anchor not found")
text = text.replace(old, "ordered_points = _deduplicate_root_points(points, domain)", 1)

# 5. Preserve numeric provenance/physical coordinate when derivative fallback
#    feeds extrema analysis.
old = """    roles: tuple[str, ...],
) -> CharacteristicPoint | None:
    fixed_overrides = dict(overrides or {})
    candidate = sp.sympify(candidate)
    try:
        _, x_quantity = context.evaluate_symbolic(candidate, overrides=fixed_overrides)
        x_quantity = _normalize_candidate_quantity(context, x_quantity, domain)
    except EngEvaluationError:
        return None
"""
new = """    roles: tuple[str, ...],
    candidate_quantity=None,
    provenance: str = "exact",
) -> CharacteristicPoint | None:
    fixed_overrides = dict(overrides or {})
    candidate = sp.sympify(candidate)
    if candidate_quantity is None:
        try:
            _, x_quantity = context.evaluate_symbolic(candidate, overrides=fixed_overrides)
            x_quantity = _normalize_candidate_quantity(context, x_quantity, domain)
        except EngEvaluationError:
            return None
    else:
        try:
            x_quantity = _normalize_candidate_quantity(context, candidate_quantity, domain)
        except EngEvaluationError:
            return None
"""
if old not in text:
    raise SystemExit("Task 7 patch guard failed: extrema candidate signature block not found")
text = text.replace(old, new, 1)

old = """        provenance="exact",
        side="at",
        roles=roles,
        source_label=source_label,
    )


def _quantity_strictly_inside_domain"""
new = """        provenance=provenance,
        side="at",
        roles=roles,
        source_label=source_label,
    )


def _quantity_strictly_inside_domain"""
if old not in text:
    raise SystemExit("Task 7 patch guard failed: extrema provenance return block not found")
text = text.replace(old, new, 1)

old = """            source_label=source_label,
            roles=(),
        )
        if point is None:
"""
new = """            source_label=source_label,
            roles=(),
            candidate_quantity=stationary.x_quantity,
            provenance=stationary.provenance,
        )
        if point is None:
"""
# This exact snippet should occur once in the stationary-point loop; endpoint
# calls use roles=("boundary",) and therefore are unaffected.
if old not in text:
    raise SystemExit("Task 7 patch guard failed: stationary extrema call not found")
text = text.replace(old, new, 1)

PATH.write_text(text, encoding="utf-8")
