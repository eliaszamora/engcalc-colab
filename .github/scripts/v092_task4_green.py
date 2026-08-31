from pathlib import Path


path = Path("src/engcalc_colab/characteristics.py")
text = path.read_text()


def replace_between(source: str, start: str, end: str, replacement: str) -> str:
    start_index = source.index(start)
    end_index = source.index(end, start_index)
    return source[:start_index] + replacement.rstrip() + "\n\n\n" + source[end_index:]


helper = '''def _solve_continuous_zero_set(
    expression: sp.Expr,
    variable: sp.Symbol,
    domain: AnalysisDomain,
    context,
    *,
    overrides: dict[str, Any] | None = None,
    source_label: str | None = None,
) -> tuple[CharacteristicPoint, ...]:
    """Solve one continuous zero-set with exact-first/fallback merge semantics."""
    discovery = _coerce_exact_discovery(
        _exact_real_solution_set(expression, variable)
    )
    points: list[CharacteristicPoint] = []
    needs_fallback = not discovery.complete

    for candidate in discovery.candidates:
        outcome = _evaluate_root_candidate(
            expression,
            variable,
            sp.sympify(candidate),
            domain,
            context,
            overrides=overrides,
            source_label=source_label,
        )
        needs_fallback = needs_fallback or outcome.needs_fallback
        if outcome.point is not None:
            points.append(outcome.point)

    if needs_fallback:
        points.extend(
            _fallback_roots(
                expression,
                variable,
                domain,
                context,
                overrides=overrides,
                source_label=source_label,
            )
        )
    return _deduplicate_root_points(points, domain)
'''
if "def _solve_continuous_zero_set(" not in text:
    marker = "def solve_roots_exact(\n"
    text = text.replace(marker, helper + "\n\n\n" + marker, 1)

root_start = "    if not expression.has(sp.Piecewise):"
root_end = "    regions = _partition_piecewise_regions("
root_segment = text[text.index(root_start):text.index(root_end, text.index(root_start))]
if "_solve_continuous_zero_set(" not in root_segment:
    root_replacement = '''    if not expression.has(sp.Piecewise):
        return (
            _solve_continuous_zero_set(
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
'''
    text = replace_between(text, root_start, root_end, root_replacement)

piece_start = '''        discovery = _coerce_exact_discovery(
            _exact_real_solution_set(branch_expression, variable)
        )
        needs_fallback = not discovery.complete
'''
piece_end = "    for candidate in _piecewise_boundary_candidates("
if piece_start in text:
    start_index = text.index(piece_start)
    end_index = text.index(piece_end, start_index)
    old_segment = text[start_index:end_index]
    region_domain_start = '''            region_domain = AnalysisDomain(
                lower_symbolic=region.lower_symbolic,
                upper_symbolic=region.upper_symbolic,
                lower_quantity=region.lower_quantity,
                upper_quantity=region.upper_quantity,
                unit=domain.unit,
            )
'''
    piece_replacement = '''        region_domain = AnalysisDomain(
            lower_symbolic=region.lower_symbolic,
            upper_symbolic=region.upper_symbolic,
            lower_quantity=region.lower_quantity,
            upper_quantity=region.upper_quantity,
            unit=domain.unit,
        )
        for point in _solve_continuous_zero_set(
            branch_expression,
            variable,
            region_domain,
            context,
            overrides=overrides,
            source_label=source_label,
        ):
            if _candidate_in_region(point.x_quantity, region, domain):
                points.append(point)

'''
    text = text[:start_index] + piece_replacement + text[end_index:]

intersection_old_start = "        candidates, unresolved = _exact_real_solution_set(difference, variable)"
intersection_old_end = "    boundaries = _intersection_boundaries("
if intersection_old_start in text:
    start_index = text.index(intersection_old_start)
    end_index = text.index(intersection_old_end, start_index)
    replacement = '''        region_domain = AnalysisDomain(
            lower_symbolic=region.lower_symbolic,
            upper_symbolic=region.upper_symbolic,
            lower_quantity=region.lower_quantity,
            upper_quantity=region.upper_quantity,
            unit=domain.unit,
        )
        zero_points = _solve_continuous_zero_set(
            difference,
            variable,
            region_domain,
            context,
            overrides=overrides,
            source_label=None,
        )
        for root_point in zero_points:
            if not _candidate_strictly_inside_intersection_region(
                root_point.x_quantity,
                region,
                domain,
            ):
                continue
            if root_point.provenance == "exact":
                point = _evaluate_intersection_candidate(
                    left_expression,
                    right_expression,
                    variable,
                    root_point.x_symbolic,
                    domain,
                    context,
                    overrides=overrides,
                    left_label=left_label,
                    right_label=right_label,
                )
            else:
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

'''
    text = text[:start_index] + replacement + text[end_index:]

path.write_text(text)
print("Applied Task 4 shared continuous zero-set patch.")
