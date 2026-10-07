"""Run eigenvals cases on a given tree: python h4.py <root> <cases.py> <out.json>"""
import json
import sys
import time

root, cases_file, out_file = sys.argv[1:4]
sys.path.insert(0, root + "/src")
from engcalc_colab.engine import EngineeringEngine  # noqa: E402
from engcalc_colab.parser import parse_cell  # noqa: E402
import engcalc_colab  # noqa: E402

assert root.replace("\\", "/").rstrip("/").split("/")[-1] in engcalc_colab.__file__.replace("\\", "/"), engcalc_colab.__file__

ns = {}
exec(open(cases_file, encoding="utf-8").read(), ns)
cases = ns["CASES"]


def lit(m, unit):
    rows = []
    for i, row in enumerate(m):
        cells = []
        for j, v in enumerate(row):
            u = unit[i][j] if isinstance(unit, list) else unit
            cells.append(f"{float(v)!r}[{u}]" if u else f"{float(v)!r}")
        rows.append(", ".join(cells))
    return "[" + "; ".join(rows) + "]"


results = {}
for name, case in cases.items():
    K = case["K"]
    G = case.get("G")
    src = f"K := {lit(K, case.get('ku', 'kN/m'))}\n"
    if G is not None:
        src += f"G := {lit(G, case.get('gu', 'kN/m'))}\nl := eigenvals(K, G)\n"
    else:
        src += "l := eigenvals(K)\n"
    engine = EngineeringEngine()
    t0 = time.perf_counter()
    try:
        for item in parse_cell(src):
            engine.evaluate(item)
        ents = engine.numeric_context.matrices["l"].entries
        vals = []
        units = set()
        for e in ents:
            if hasattr(e, "to_base_units"):
                b = e.to_base_units()
                vals.append(float(b.magnitude))
                units.add(str(b.units))
            else:
                vals.append(float(e))
        results[name] = {"vals": vals, "units": sorted(units), "t": time.perf_counter() - t0}
    except Exception as exc:  # noqa: BLE001
        results[name] = {"err": f"{type(exc).__name__}: {exc}"[:300], "t": time.perf_counter() - t0}
json.dump(results, open(out_file, "w", encoding="utf-8"), indent=1)
