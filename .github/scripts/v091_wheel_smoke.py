import os
import sympy as sp

import engcalc_colab
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import ExtremaResult, IntersectionsResult, PlotResult, RootsResult
from engcalc_colab.parser import parse_cell


assert engcalc_colab.__version__ == "0.9.1"
module_path = os.path.realpath(engcalc_colab.__file__).replace("\\", "/")
assert "site-packages" in module_path, module_path
assert "/src/engcalc_colab/" not in module_path, module_path
print(f"INSTALLED_MODULE_PATH={module_path}")


def run(engine, source):
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


engine = EngineeringEngine()
run(engine, "L := 6*m")
run(engine, "q := 12*kN/m")
run(engine, "M(x) = q*x*(L-x)/2")
run(engine, "V(x) = q*(L/2-x)")
run(engine, "M2(x) = q*x*(L-x)/3")
run(engine, "K(x) = [x + L, 0; 0, 2*x + L]")

extrema = run(engine, "extrema(M(x), x, 0, L)")
assert isinstance(extrema, ExtremaResult)
peak = next(point for point in extrema.points if "global_max" in point.roles)
assert peak.provenance == "exact"
assert abs(peak.x_quantity.to("m").magnitude - 3.0) < 1e-12
assert abs(peak.value_quantity.to("kN*m").magnitude - 54.0) < 1e-10

roots = run(engine, "roots(V(x), x, 0, L)")
assert isinstance(roots, RootsResult)
assert len(roots.points) == 1
assert roots.points[0].provenance == "exact"
assert abs(roots.points[0].x_quantity.to("m").magnitude - 3.0) < 1e-12

intersections = run(engine, "intersections(M(x), M2(x), x, 0, L)")
assert isinstance(intersections, IntersectionsResult)
assert [round(point.x_quantity.to("m").magnitude, 12) for point in intersections.points] == [0.0, 6.0]
assert all(point.provenance == "exact" for point in intersections.points)

matrix_root = run(engine, "roots(K(x)[1,1] - 7*m, x, 0, L)")
assert isinstance(matrix_root, RootsResult)
assert len(matrix_root.points) == 1
assert matrix_root.points[0].provenance == "exact"
assert abs(matrix_root.points[0].x_quantity.to("m").magnitude - 1.0) < 1e-12

jump = run(engine, "J(x) = piecewise(-1, x < 2, 1)\nroots(J(x), x, 0, 4)")
assert isinstance(jump, RootsResult)
assert jump.points == ()
assert jump.intervals == ()

fallback = run(engine, "roots(cos(x) - x, x, 0, 1)")
assert isinstance(fallback, RootsResult)
assert len(fallback.points) == 1
assert fallback.points[0].provenance == "numeric"
assert abs(float(fallback.points[0].x_quantity.magnitude) - 0.7390851332151607) < 1e-9

plot_engine = EngineeringEngine()
plot_result = run(
    plot_engine,
    "f(x) = -(x - 1/3)^2 + 2\nplot(f(x), x, 0, 1)",
)
assert isinstance(plot_result, PlotResult)
plot_peak = next(
    point
    for point in plot_result.series[0].characteristics
    if "global_max" in point.roles
)
assert plot_peak.x_symbolic == sp.Rational(1, 3)
assert len(plot_result.x_values) == 201
assert all(
    abs(float(quantity.magnitude) - 1 / 3) > 1e-12
    for quantity in plot_result.x_values
)

print("WHEEL_SMOKE=PASS")
