import json
import pathlib

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell

A = pathlib.Path(__file__).parent / "a3"
cases = json.loads((A / "cases3.json").read_text())
refs = json.loads((A / "refs.json").read_text())
for name, source in cases.items():
    engine = EngineeringEngine()
    for item in parse_cell(source):
        engine.evaluate(item)
    matrix = engine.numeric_context.matrices["l"]
    got = [float(q.to("1/s**2").magnitude) for q in matrix.entries]
    want = refs[name]["lam"]
    worst = max(abs(g - w) / abs(w) for g, w in zip(got, want))
    print(name, len(got), len(want), f"worst relative {worst:.2e}")
