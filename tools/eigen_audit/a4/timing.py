import sys
import time

root = sys.argv[1]
sys.path.insert(0, root + "/src")
from engcalc_colab.engine import EngineeringEngine  # noqa: E402
from engcalc_colab.parser import parse_cell  # noqa: E402

ns = {}
exec(open("cases2.py", encoding="utf-8").read(), ns)
lit = {}
exec(open("h4.py", encoding="utf-8").read().split("results = {}")[0].split("ns = {}")[0].replace("root, cases_file, out_file = sys.argv[1:4]", "").replace("sys.path.insert(0, root + \"/src\")", "").split("assert")[0], lit)
src_h4 = open("h4.py", encoding="utf-8").read()
start = src_h4.index("def lit")
end = src_h4.index("results = {}")
exec(src_h4[start:end], lit)
for name in sys.argv[2:]:
    case = ns["CASES"][name]
    src = f"K := {lit['lit'](case['K'], case['ku'])}\nG := {lit['lit'](case['G'], case['gu'])}\n"
    engine = EngineeringEngine()
    for item in parse_cell(src):
        engine.evaluate(item)
    best = 1e9
    for _ in range(3):
        t = time.perf_counter()
        try:
            for item in parse_cell("l := eigenvals(K, G)\n"):
                engine.evaluate(item)
        except Exception as exc:  # noqa: BLE001
            pass
        best = min(best, time.perf_counter() - t)
    print(root[-6:], name, f"{best:.3f}s")
