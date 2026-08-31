from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_required(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")
        return
    if new not in text:
        raise RuntimeError(f"expected text not found in {path}: {old!r}")


def materialize() -> None:
    from v092_task14_version_red import main as materialize_version_tests

    materialize_version_tests()

    pyproject = ROOT / "pyproject.toml"
    replace_required(pyproject, 'version = "0.9.1"', 'version = "0.9.2"')

    init_file = ROOT / "src" / "engcalc_colab" / "__init__.py"
    replace_required(init_file, '__version__ = "0.9.1"', '__version__ = "0.9.2"')

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = text.replace("Current version: **0.9.1**.", "Current version: **0.9.2**.", 1)
    text = text.replace(
        "The 0.9.2 reliability work hardens exact characteristic analysis without changing the released-version label yet.",
        "EngCalc 0.9.2 hardens exact characteristic analysis and packages the completed audit-remediation reliability work as the current release.",
        1,
    )
    history_anchor = "## Version notes\n\n- **0.9.1** —"
    if "- **0.9.2** —" not in text:
        if history_anchor not in text:
            raise RuntimeError("README version-notes anchor not found")
        text = text.replace(
            history_anchor,
            "## Version notes\n\n- **0.9.2** — audit remediation and reliability: resilient exact-first characteristic discovery with deterministic fallback, explicit-real engineering symbols, consistent direct unit bounds, normalized Piecewise topology, exact characteristic presentation polish, declared IPython runtime support, and permanent Python 3.10–3.14 CI.\n- **0.9.1** —",
            1,
        )
    text = text.replace("Version: `0.9.1`.", "Version: `0.9.2`.")
    readme.write_text(text, encoding="utf-8")

    print("Materialized EngCalc 0.9.2 release candidate.")


def evaluate_cell(engine, source: str):
    from engcalc_colab.parser import parse_cell

    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


def smoke() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import IPython
    import engcalc_colab
    from engcalc_colab.engine import EngineeringEngine
    from engcalc_colab.models import ExtremaResult, IntersectionsResult, PlotResult, RootsResult
    from engcalc_colab.plotting import render_plot

    package_path = Path(engcalc_colab.__file__).resolve()
    assert "site-packages" in str(package_path), package_path
    assert engcalc_colab.__version__ == "0.9.2"
    assert IPython.__version__

    engine = EngineeringEngine()

    roots = evaluate_cell(engine, "roots(log(x)-1, x, 1, 10)")
    assert isinstance(roots, RootsResult)
    assert len(roots.points) == 1
    assert math.isclose(float(roots.points[0].x_quantity.magnitude), math.e, rel_tol=1e-9)

    roots = evaluate_cell(engine, "roots(exp(x)-3*x, x, 0, 3)")
    assert isinstance(roots, RootsResult)
    actual = tuple(float(point.x_quantity.magnitude) for point in roots.points)
    expected = (0.619061286735945, 1.512134551657842)
    assert len(actual) == 2
    assert all(math.isclose(a, e, rel_tol=1e-9, abs_tol=1e-10) for a, e in zip(actual, expected))

    roots = evaluate_cell(engine, "roots(x^5-x-1, x, 0, 2)")
    assert isinstance(roots, RootsResult)
    assert len(roots.points) == 1
    assert math.isclose(float(roots.points[0].x_quantity.magnitude), 1.167303978261419, rel_tol=1e-9)

    intersections = evaluate_cell(engine, "intersections(log(x), 1+0*x, x, 1, 10)")
    assert isinstance(intersections, IntersectionsResult)
    assert len(intersections.points) == 1
    assert math.isclose(float(intersections.points[0].x_quantity.magnitude), math.e, rel_tol=1e-9)

    extrema = evaluate_cell(engine, "extrema(abs(x-2), x, 0, 4)")
    assert isinstance(extrema, ExtremaResult)
    minimum = next(point for point in extrema.points if "global_min" in point.roles)
    assert math.isclose(float(minimum.x_quantity.magnitude), 2.0, abs_tol=1e-12)
    assert math.isclose(float(minimum.value_quantity.magnitude), 0.0, abs_tol=1e-12)

    roots = evaluate_cell(
        engine,
        "L := 6*m\nV(x) = x-L/2\nroots(V(x), x, 0*m, 6000*mm)",
    )
    assert isinstance(roots, RootsResult)
    assert len(roots.points) == 1
    assert math.isclose(float(roots.points[0].x_quantity.to("m").magnitude), 3.0, abs_tol=1e-12)

    continuous = evaluate_cell(
        engine,
        "a := 3*m\nL := 6*m\nf(x) = piecewise(x-a, x < a, 2*(x-a))\nextrema(f(x), x, 0*m, L)",
    )
    at_a = [
        point
        for point in continuous.points
        if math.isclose(float(point.x_quantity.to("m").magnitude), 3.0, abs_tol=1e-12)
    ]
    assert [point.side for point in at_a] == ["at"]

    discontinuous = evaluate_cell(
        EngineeringEngine(),
        "g(x) = piecewise(x, x < 2, 10, x <= 2, 4-x)\nextrema(g(x), x, 0, 4)",
    )
    at_two = [
        point
        for point in discontinuous.points
        if math.isclose(float(point.x_quantity.magnitude), 2.0, abs_tol=1e-12)
    ]
    sides = {point.side for point in at_two}
    assert sides == {"left", "at", "right"}, sides

    plot = evaluate_cell(EngineeringEngine(), "f(x)=-(x-1/3)^2+2\nplot(f(x), x, 0, 1)")
    assert isinstance(plot, PlotResult)
    figure = render_plot(plot)
    assert any("1/3" in item.get_text() for item in figure.axes[0].texts)

    moment = evaluate_cell(EngineeringEngine(), "M(x)=-(x-1)^2+2\nplot(M(x), x, 0, 2)")
    assert isinstance(moment, PlotResult)
    assert render_plot(moment).axes[0].yaxis_inverted()

    print(f"SITE_PACKAGES_IMPORT={package_path}")
    print("TASK14_EXTERNAL_SMOKE=PASS")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "materialize"
    if mode == "materialize":
        materialize()
    elif mode == "smoke":
        smoke()
    else:
        raise SystemExit(f"unknown mode: {mode}")


if __name__ == "__main__":
    main()
