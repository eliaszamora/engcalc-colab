import os
import sys

ROOT = os.environ["ENGROOT"]
sys.path.insert(0, ROOT + "/src")
from engcalc_colab.engine import EngineeringEngine  # noqa: E402
from engcalc_colab.parser import parse_cell  # noqa: E402

src = open(sys.argv[1], encoding="utf-8").read()
for k in sys.argv[2:]:
    src = src.replace("SPRING", k)
engine = EngineeringEngine()
try:
    for item in parse_cell(src):
        engine.evaluate(item)
    print([str(e) for e in engine.numeric_context.matrices["l"].entries])
except Exception as exc:  # noqa: BLE001
    print("ERR", str(exc)[:200])
