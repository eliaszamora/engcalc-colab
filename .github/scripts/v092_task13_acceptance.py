from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE = ROOT / "tests" / "test_characteristics_acceptance.py"
PLOT_ACCEPTANCE = ROOT / "tests" / "test_characteristics_plot_integration.py"
README = ROOT / "README.md"


def update_acceptance() -> None:
    text = ACCEPTANCE.read_text(encoding="utf-8")
    marker = "def test_v092_audit_remediations_end_to_end_without_monkeypatching():"
    if marker in text:
        return

    block = r'''


def test_v092_audit_remediations_end_to_end_without_monkeypatching():
    engine = EngineeringEngine()

    root_cases = [
        ("roots(log(x)-1, x, 1, 10)", (math.e,)),
        (
            "roots(exp(x)-3*x, x, 0, 3)",
            (0.619061286735945, 1.512134551657842),
        ),
        ("roots(x^5-x-1, x, 0, 2)", (1.167303978261419,)),
    ]
    for source, expected in root_cases:
        result = evaluate_cell(engine, source)
        assert isinstance(result, RootsResult)
        actual = tuple(float(point.x_quantity.magnitude) for point in result.points)
        assert actual == pytest.approx(expected, rel=1e-9, abs=1e-10)

    intersection = evaluate_cell(
        engine,
        "intersections(log(x), 1+0*x, x, 1, 10)",
    )
    assert isinstance(intersection, IntersectionsResult)
    assert len(intersection.points) == 1
    assert float(intersection.points[0].x_quantity.magnitude) == pytest.approx(
        math.e,
        rel=1e-9,
        abs=1e-10,
    )

    extrema = evaluate_cell(engine, "extrema(abs(x-2), x, 0, 4)")
    assert isinstance(extrema, ExtremaResult)
    minimum = next(point for point in extrema.points if "global_min" in point.roles)
    assert float(minimum.x_quantity.magnitude) == pytest.approx(2.0)
    assert float(minimum.value_quantity.magnitude) == pytest.approx(0.0)


def test_v092_direct_unit_literal_root_bounds_are_natural_end_to_end():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "L := 6*m\n"
        "V(x) = x-L/2\n"
        "roots(V(x), x, 0*m, 6000*mm)",
    )

    assert isinstance(result, RootsResult)
    assert len(result.points) == 1
    point = result.points[0]
    assert point.x_quantity.to("m").magnitude == pytest.approx(3.0)
    assert point.provenance == "exact"


def test_v092_continuous_piecewise_extrema_preserve_selected_boundary_value():
    engine = EngineeringEngine()
    result = evaluate_cell(
        engine,
        "a := 3*m\n"
        "L := 6*m\n"
        "f(x) = piecewise(x-a, x < a, 2*(x-a))\n"
        "extrema(f(x), x, 0*m, L)",
    )

    assert isinstance(result, ExtremaResult)
    at_break = [
        point
        for point in result.points
        if point.x_quantity.to("m").magnitude == pytest.approx(3.0)
    ]
    assert [point.side for point in at_break] == ["at"]
    assert at_break[0].value_quantity.to("m").magnitude == pytest.approx(0.0)

    lower = next(
        point
        for point in result.points
        if point.x_quantity.to("m").magnitude == pytest.approx(0.0)
    )
    upper = next(
        point
        for point in result.points
        if point.x_quantity.to("m").magnitude == pytest.approx(6.0)
    )
    assert lower.value_quantity.to("m").magnitude == pytest.approx(-3.0)
    assert upper.value_quantity.to("m").magnitude == pytest.approx(6.0)
'''
    ACCEPTANCE.write_text(
        text.rstrip() + block.rstrip() + "\n",
        encoding="utf-8",
    )


def update_plot_acceptance() -> None:
    text = PLOT_ACCEPTANCE.read_text(encoding="utf-8")
    old = "test_envelope_deliberately_keeps_sampled_characteristic_path_until_v092"
    new = "test_envelope_deliberately_keeps_sampled_characteristic_path_until_v093"
    if old in text:
        text = text.replace(old, new, 1)
        PLOT_ACCEPTANCE.write_text(text, encoding="utf-8")
        return
    if new not in text:
        raise RuntimeError("Task 13 envelope deferral acceptance test was not found")


def update_readme() -> None:
    text = README.read_text(encoding="utf-8")
    section = r'''## v0.9.2 reliability work

The 0.9.2 reliability work hardens exact characteristic analysis without changing the released-version label yet. Characteristic solving remains exact-first; when exact discovery is incomplete, EngCalc supplements it with a deterministic numerical fallback instead of silently returning an empty result. Engine-created engineering symbols are explicitly real, and accepted exact candidates keep exact provenance when exact and numerical candidates coincide.

Previously fragile transcendental and non-elementary cases are covered end to end with normal EngCalc syntax:

```text
roots(log(x)-1, x, 1, 10)
roots(exp(x)-3*x, x, 0, 3)
roots(x^5-x-1, x, 0, 2)
intersections(log(x), 1+0*x, x, 1, 10)
extrema(abs(x-2), x, 0, 4)
```

Natural unit-literal bounds use the same engineering grammar as plots and tables; no Python-qualified unit syntax is required:

```text
L := 6*m
V(x) = x-L/2
roots(V(x), x, 0*m, 6000*mm)
```

Continuous Piecewise boundaries preserve the selected governing branch and collapse equivalent left/at/right records to the physical `at` value, while real discontinuities retain meaningful one-sided values:

```text
a := 3*m
L := 6*m
f(x) = piecewise(x-a, x < a, 2*(x-a))
extrema(f(x), x, 0*m, L)
```

Ordinary plots keep exact characteristic coordinates and annotation identity independently of their 201-point drawing grid. The characteristic solver is now split internally by responsibility under `engcalc_colab.characteristics` while its public imports remain stable. IPython is a declared runtime dependency, and permanent CI validates the advertised Python 3.10–3.14 range.

`envelope(...)` deliberately remains sampled in 0.9.2. Exact envelope crossovers and governing intervals are planned for **0.9.3**.

'''
    marker = "## v0.9.2 reliability work"
    if marker not in text:
        anchor = "Current version: **0.9.1**.\n\n\n"
        if anchor not in text:
            raise RuntimeError("README current-version anchor not found")
        text = text.replace(anchor, anchor + section, 1)

    text = text.replace(
        "Exact envelope crossovers and governing intervals remain intentionally deferred to **0.9.2**; `envelope(...)` keeps its existing sampled governing mathematics in 0.9.1.",
        "Exact envelope crossovers and governing intervals remain intentionally deferred to **0.9.3**; `envelope(...)` keeps its existing sampled governing mathematics through the 0.9.2 reliability work.",
    )
    README.write_text(text, encoding="utf-8")


def main() -> None:
    update_acceptance()
    update_plot_acceptance()
    update_readme()
    print("Applied Task 13 acceptance and README candidate.")


if __name__ == "__main__":
    main()
