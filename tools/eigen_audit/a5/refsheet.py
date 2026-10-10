"""mpmath reference of a K/G sheet (values converted to base by the engine itself)."""
import sys
import numpy as np
from lib import ref, EngineeringEngine, parse_cell

src = open(sys.argv[1], encoding="utf-8").read()
engine = EngineeringEngine()
for item in parse_cell("\n".join(src.splitlines()[:2]) + "\n"):
    engine.evaluate(item)


def base(name):
    m = engine.numeric_context.matrices[name]
    vals = [float(e.to_base_units().magnitude) if hasattr(e, "to_base_units") else float(e) for e in m.entries]
    return np.array(vals).reshape(m.rows, m.cols)


K, G = base("K"), base("G")
print(["%.8g" % x for x in ref(K, G, dps=int(sys.argv[2]) if len(sys.argv) > 2 else 60)])
