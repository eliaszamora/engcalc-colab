from __future__ import annotations

from pathlib import Path


ROOT = Path("src/engcalc_colab/characteristics")


def patch_solver(
    filename: str,
    solver_name: str,
    anchor: str,
    resolution: str,
) -> bool:
    path = ROOT / filename
    text = path.read_text(encoding="utf-8")
    marker = f"def {solver_name}("
    start = text.index(marker)
    prefix = text[:start]
    solver = text[start:]

    if "resolved_overrides = context.unit_literal_overrides" not in solver:
        if anchor not in solver:
            raise RuntimeError(f"anchor not found for {solver_name}")
        solver = solver.replace(anchor, anchor + resolution, 1)

    solver = solver.replace(
        "overrides=overrides,",
        "overrides=resolved_overrides,",
    )
    updated = prefix + solver
    if updated == text:
        print(f"UNCHANGED {filename}:{solver_name}")
        return False
    path.write_text(updated, encoding="utf-8")
    print(f"PATCHED {filename}:{solver_name}")
    return True


def main() -> None:
    changed = []
    if patch_solver(
        "roots.py",
        "solve_roots_exact",
        '    if not isinstance(variable, sp.Symbol):\n        raise EngEvaluationError("roots variable must be a symbolic identifier")\n',
        "\n    resolved_overrides = context.unit_literal_overrides(expression, overrides)\n",
    ):
        changed.append("roots.py")

    if patch_solver(
        "intersections.py",
        "solve_intersections_exact",
        '    if not isinstance(variable, sp.Symbol):\n        raise EngEvaluationError("intersections variable must be a symbolic identifier")\n',
        "\n    resolved_overrides = context.unit_literal_overrides(left_expression, overrides)\n"
        "    resolved_overrides = context.unit_literal_overrides(\n"
        "        right_expression, resolved_overrides\n"
        "    )\n",
    ):
        changed.append("intersections.py")

    if patch_solver(
        "extrema.py",
        "solve_extrema_exact",
        '    if not isinstance(variable, sp.Symbol):\n        raise EngEvaluationError("extrema variable must be a symbolic identifier")\n',
        "\n    resolved_overrides = context.unit_literal_overrides(expression, overrides)\n",
    ):
        changed.append("extrema.py")

    print("TASK3_CHANGED=" + (",".join(changed) if changed else "none"))


if __name__ == "__main__":
    main()
