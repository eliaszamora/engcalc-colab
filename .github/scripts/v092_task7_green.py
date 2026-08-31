from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Task 7 anchor not found: {label}")
    return text.replace(old, new, 1)


path = Path("src/engcalc_colab/characteristics.py")
text = path.read_text()

# 1) Preserve the selected governing branch symbolically at physical boundaries.
anchor = '''def _piecewise_local_role_at_breakpoint(
'''
helper = '''def _piecewise_selected_boundary_point(
    expression: sp.Expr,
    variable: sp.Symbol,
    boundary_symbolic: sp.Expr,
    boundary_quantity,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None,
    source_label: str | None,
) -> CharacteristicPoint | None:
    folded = sp.piecewise_fold(sp.sympify(expression))
    branch_expression = folded
    if isinstance(folded, sp.Piecewise):
        try:
            _, branch_expression = _select_piecewise_branch(
                folded,
                variable,
                boundary_quantity,
                context,
                overrides=overrides,
            )
        except EngEvaluationError:
            return None
    return _evaluate_extrema_candidate(
        sp.sympify(branch_expression),
        variable,
        sp.sympify(boundary_symbolic),
        domain,
        context,
        overrides=overrides,
        source_label=source_label,
        roles=("boundary",),
        candidate_quantity=boundary_quantity,
    )


def _piecewise_local_role_at_breakpoint(
'''
text = replace_once(text, anchor, helper, "selected Piecewise boundary helper")

# 2) Normalize exact dimensional-zero topology records before comparison.
anchor = '''def _ordered_unique_extrema_points(
'''
helper = '''def _extrema_point_with_value_quantity(
    point: CharacteristicPoint,
    value_quantity,
) -> CharacteristicPoint:
    return CharacteristicPoint(
        x_symbolic=point.x_symbolic,
        x_quantity=point.x_quantity,
        value_symbolic=point.value_symbolic,
        value_quantity=value_quantity,
        provenance=point.provenance,
        side=point.side,
        roles=point.roles,
        source_label=point.source_label,
    )


def _normalize_piecewise_zero_units(
    records: tuple[CharacteristicPoint | None, ...],
    context,
) -> tuple[CharacteristicPoint | None, ...]:
    canonical_unit = next(
        (
            point.value_quantity.units
            for point in records
            if point is not None
            and point.value_quantity is not None
            and not point.value_quantity.dimensionless
        ),
        None,
    )
    if canonical_unit is None:
        return records

    normalized: list[CharacteristicPoint | None] = []
    for point in records:
        if point is None or point.value_quantity is None:
            normalized.append(point)
            continue
        quantity = point.value_quantity
        if (
            quantity.dimensionless
            and _quantity_is_zero(quantity)
            and sp.simplify(point.value_symbolic) == 0
        ):
            point = _extrema_point_with_value_quantity(
                point,
                context.ureg.Quantity(0, canonical_unit),
            )
        normalized.append(point)
    return tuple(normalized)


def _piecewise_breakpoint_records(
    left_point: CharacteristicPoint | None,
    at_point: CharacteristicPoint | None,
    right_point: CharacteristicPoint | None,
    context,
) -> tuple[CharacteristicPoint, ...]:
    left_point, at_point, right_point = _normalize_piecewise_zero_units(
        (left_point, at_point, right_point),
        context,
    )
    if (
        left_point is not None
        and at_point is not None
        and right_point is not None
        and _same_extrema_value(
            left_point.value_quantity,
            at_point.value_quantity,
            context,
        )
        and _same_extrema_value(
            at_point.value_quantity,
            right_point.value_quantity,
            context,
        )
    ):
        return (at_point,)
    return tuple(
        point
        for point in (left_point, at_point, right_point)
        if point is not None
    )


def _ordered_unique_extrema_points(
'''
text = replace_once(text, anchor, helper, "Piecewise zero-unit topology helpers")

# 3) Domain endpoints: evaluate selected branch, not the whole Piecewise object.
old = '''    for endpoint in (domain.lower_symbolic, domain.upper_symbolic):
        point = _evaluate_extrema_candidate(
            expression,
            variable,
            endpoint,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
            roles=("boundary",),
        )
        if point is not None:
            points.append(point)
'''
new = '''    for endpoint_symbolic, endpoint_quantity in (
        (domain.lower_symbolic, domain.lower_quantity),
        (domain.upper_symbolic, domain.upper_quantity),
    ):
        point = _piecewise_selected_boundary_point(
            expression,
            variable,
            endpoint_symbolic,
            endpoint_quantity,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
        )
        if point is not None:
            points.append(point)
'''
text = replace_once(text, old, new, "Piecewise physical domain endpoint selection")

# 4) Internal breakpoints: classify the actual branch value, normalize zero units,
# and retain side records unless all three values are physically identical.
old = '''        unbounded_above = unbounded_above or left_up or right_up
        unbounded_below = unbounded_below or left_down or right_down
        unresolved = unresolved or left_unresolved or right_unresolved
        if left_point is not None:
            points.append(left_point)

        at_point = _evaluate_extrema_candidate(
            expression,
            variable,
            breakpoint_symbolic,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
            roles=("boundary",),
        )
        if at_point is not None:
            local_role = _piecewise_local_role_at_breakpoint(
                expression,
                variable,
                at_point,
                left_region,
                right_region,
                domain,
                context,
                overrides=overrides,
            )
            if local_role is not None:
                at_point = _extrema_point_with_roles(
                    at_point,
                    tuple(dict.fromkeys((*at_point.roles, local_role))),
                )
            points.append(at_point)
        if right_point is not None:
            points.append(right_point)
'''
new = '''        unbounded_above = unbounded_above or left_up or right_up
        unbounded_below = unbounded_below or left_down or right_down
        unresolved = unresolved or left_unresolved or right_unresolved

        at_point = _piecewise_selected_boundary_point(
            expression,
            variable,
            breakpoint_symbolic,
            breakpoint_quantity,
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
        )
        if at_point is not None:
            local_role = _piecewise_local_role_at_breakpoint(
                expression,
                variable,
                at_point,
                left_region,
                right_region,
                domain,
                context,
                overrides=overrides,
            )
            if local_role is not None:
                at_point = _extrema_point_with_roles(
                    at_point,
                    tuple(dict.fromkeys((*at_point.roles, local_role))),
                )

        points.extend(
            _piecewise_breakpoint_records(
                left_point,
                at_point,
                right_point,
                context,
            )
        )
'''
text = replace_once(text, old, new, "Piecewise breakpoint topology normalization")
path.write_text(text)

# Persist the two approved Task 7 contracts after RED was observed.
path = Path("tests/test_characteristics_piecewise_extrema.py")
text = path.read_text()
marker = "def test_piecewise_boundary_value_symbolic_is_selected_governing_branch():"
if marker not in text:
    text += '''\n\ndef test_piecewise_boundary_value_symbolic_is_selected_governing_branch():
    context = NumericContext()
    _assign(context, "a", "3*m")
    _assign(context, "L", "6*m")
    x, a, L = sp.symbols("x a L", real=True)
    expr = sp.Piecewise((x-a, x < a), (2*(x-a), True), evaluate=False)
    domain = normalize_analysis_domain(context, sp.Integer(0), L)

    points, _, _, _, unresolved = solve_extrema_exact(expr, x, domain, context)
    lower = next(point for point in points if sp.simplify(point.x_symbolic) == 0)
    upper = next(point for point in points if sp.simplify(point.x_symbolic-L) == 0)
    assert sp.simplify(lower.value_symbolic + a) == 0
    assert sp.simplify(upper.value_symbolic - 2*(L-a)) == 0
    assert lower.value_quantity.to("m").magnitude == pytest.approx(-3.0)
    assert upper.value_quantity.to("m").magnitude == pytest.approx(6.0)
    assert unresolved is False


def test_continuous_piecewise_breakpoint_emits_only_at_with_dimensional_zero():
    context = NumericContext()
    _assign(context, "a", "3*m")
    _assign(context, "L", "6*m")
    x, a, L = sp.symbols("x a L", real=True)
    expr = sp.Piecewise((x-a, x < a), (2*(x-a), True), evaluate=False)
    domain = normalize_analysis_domain(context, sp.Integer(0), L)

    points, _, _, _, unresolved = solve_extrema_exact(expr, x, domain, context)
    at_a = [point for point in points if sp.simplify(point.x_symbolic-a) == 0]
    assert [point.side for point in at_a] == ["at"]
    assert at_a[0].value_quantity.to("m").magnitude == pytest.approx(0.0)
    assert unresolved is False
'''
path.write_text(text)

print("Applied Task 7 Piecewise boundary/topology normalization and persistent tests.")
