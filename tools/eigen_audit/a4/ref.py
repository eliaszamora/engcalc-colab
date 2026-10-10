"""python ref.py cases.py refs.json - mpmath reference finite eigenvalues."""
import json
import sys

import mpmath as mp

mp.mp.dps = int(sys.argv[3]) if len(sys.argv) > 3 else 60
ns = {}
exec(open(sys.argv[1], encoding="utf-8").read(), ns)
out = {}
for name, case in ns["CASES"].items():
    K = mp.matrix([[mp.mpf(float(v)) for v in row] for row in case["K"]])
    if case.get("G") is None:
        ev = mp.eig(K, left=False, right=False)
        out[name] = sorted(float(mp.re(e)) for e in ev)
        continue
    G = mp.matrix([[mp.mpf(float(v)) for v in row] for row in case["G"]])
    s = mp.mpf("0.1234567")
    try:
        M = mp.lu_solve(K - s * G, G) if False else (K - s * G) ** -1 * G
        ev = mp.eig(M, left=False, right=False)
    except ZeroDivisionError:
        out[name] = "singular"
        continue
    big = max(abs(e) for e in ev)
    lam = [s + 1 / e for e in ev if abs(e) > mp.mpf(10) ** (-(mp.mp.dps * 2 // 3)) * big]
    out[name] = sorted([float(mp.re(x)) * case.get("scale", 1.0) for x in lam]) + (["IMAG"] if any(abs(mp.im(x)) > 1e-20 * (1 + abs(x)) for x in lam) else [])
json.dump(out, open(sys.argv[2], "w"), indent=0)
