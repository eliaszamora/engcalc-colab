"""Judge every audit case (a5 cases6-7, a6 cases8, a7 cases9-13 + beams) on the working tree.

Prints WRONG/COUNT lines (silent errors) and a tally of refusals; a4 runs separately (all.sh).
"""
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
PY = r"C:\Users\elias\engcalc\.venv\Scripts\python.exe"
sys.path.insert(0, str(HERE / "a6"))
from lib6 import judge2  # noqa: E402

FILES = [HERE / "a5" / "cases6.py", HERE / "a5" / "cases7.py", HERE / "a6" / "cases8.py"] + [
    HERE / "a7" / f"cases{i}.py" for i in range(9, 14)
] + [HERE / "a7" / "beams.py"]
env = dict(os.environ, ENGROOT="C:/Users/elias/engcalc", PYTHONIOENCODING="utf-8")
tally = {"ok": 0, "REFUSED": 0, "bad": 0}
for cases in FILES:
    out = HERE / "master_out" / (cases.parent.name + "_" + cases.stem + ".json")
    out.parent.mkdir(exist_ok=True)
    subprocess.run([PY, str(HERE / "a6" / "run6.py"), str(cases), str(out)], env=env,
                   capture_output=True, cwd=str(HERE / "a6"))
    refs = json.load(open(str(cases) + ".refs.json"))
    got = json.load(open(out))
    for name, result in got.items():
        verdict = judge2(refs[name], result["got"])
        if verdict == "ok":
            tally["ok"] += 1
        elif verdict == "REFUSED":
            tally["REFUSED"] += 1
            if "-v" in sys.argv:
                print(f"{cases.stem}:{name} REFUSED")
        else:
            tally["bad"] += 1
            print(f"{cases.stem}:{name} {verdict}")
            print("    ref", [f"{x:.8g}" for x in refs[name]][:8] if not isinstance(refs[name], str) else refs[name])
            print("    got", [f"{x:.8g}" for x in result["got"]][:8] if not isinstance(result["got"], str) else result["got"][:120])
print(tally)
