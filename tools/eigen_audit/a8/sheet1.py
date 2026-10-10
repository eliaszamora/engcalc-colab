import os, sys
sys.path.insert(0, os.environ["ENGROOT"] + "/src")
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell

SRC = {
"link": """K := [100000000000005[kN/m], -100000000000000[kN/m]; -100000000000000[kN/m], 100000000000000[kN/m]]
M := [2000[kg], 0000[kg]; 0000[kg], 3000[kg]]
l := eigenvals(K, M)
""",
}
for name, src in SRC.items():
    e = EngineeringEngine()
    try:
        for it in parse_cell(src):
            e.evaluate(it)
        print(name, [str(q) for q in e.numeric_context.matrices["l"].entries])
    except Exception as exc:
        print(name, "ERR", str(exc)[:150])
