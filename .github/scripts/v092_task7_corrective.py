from pathlib import Path


def transform_function(text: str, function_name: str, transform) -> str:
    start = text.find(f"def {function_name}(")
    if start == -1:
        raise SystemExit(f"Task 7 function not found: {function_name}")
    end = text.find("\ndef ", start + 4)
    if end == -1:
        end = len(text)
    segment = text[start:end]
    updated = transform(segment)
    if updated == segment:
        raise SystemExit(f"Task 7 corrective made no change in {function_name}")
    return text[:start] + updated + text[end:]


path = Path("src/engcalc_colab/characteristics.py")
text = path.read_text()

selected_endpoint_block = '''    for endpoint_symbolic, endpoint_quantity in (
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

continuous_endpoint_block = '''    for endpoint in (domain.lower_symbolic, domain.upper_symbolic):
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


def restore_continuous(segment: str) -> str:
    if selected_endpoint_block not in segment:
        raise SystemExit("Task 7 selected endpoint block missing from continuous extrema")
    return segment.replace(selected_endpoint_block, continuous_endpoint_block, 1)


text = transform_function(text, "_solve_continuous_extrema_exact", restore_continuous)


def fix_piecewise(segment: str) -> str:
    if continuous_endpoint_block not in segment:
        raise SystemExit("Task 7 original endpoint block missing from Piecewise extrema")
    return segment.replace(continuous_endpoint_block, selected_endpoint_block, 1)


text = transform_function(text, "_solve_piecewise_extrema_exact", fix_piecewise)
path.write_text(text)

print("Scoped Task 7 endpoint handling to Piecewise extrema and restored continuous extrema.")
