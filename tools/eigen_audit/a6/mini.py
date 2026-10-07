import os
import sys

root = os.environ["ENGROOT"]
sys.path.insert(0, root + "/src")
from engcalc_colab.engine import EngineeringEngine  # noqa: E402
from engcalc_colab.parser import parse_cell  # noqa: E402


def run(src):
    e = EngineeringEngine()
    try:
        for it in parse_cell(src):
            e.evaluate(it)
        return [float(v.to_base_units().magnitude) if hasattr(v, "to_base_units") else float(v)
                for v in e.numeric_context.matrices["l"].entries]
    except Exception as exc:  # noqa: BLE001
        return f"ERR {exc}"[:120]


for s in ("1e10", "1e12", "1e13", "1e14", "1e15", "1e16", "1e20"):
    src = (f"K := [1, 0, 0; 0, 3, 0; 0, 0, {s}]\n"
           "G := [1.9, 0, -0.5; 0, 1.9, -0.2; -0.5, -0.2, 3]\n"
           "l := eigenvals(K, G)\n")
    print("plain spring", s, run(src))
for s in ("1e13", "1e16", "1e19"):
    src = (f"K := [1000[kN/m], 0[kN/m], 0[kN/m]; 0[kN/m], 3000[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m], {s}[kN/m]]\n"
           "G := [1900[kg], 0[kg], -500[kg]; 0[kg], 1900[kg], -200[kg]; -500[kg], -200[kg], 3000[kg]]\n"
           "l := eigenvals(K, G)\n")
    print("kN/m kg spring", s, run(src))
