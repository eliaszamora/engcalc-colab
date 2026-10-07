"""ENGROOT=<tree> python run8.py casesX.py out.json  - each value judged against its own size.

ref: mpmath on the float entries; refp: mpmath on entries x(1+1e-15 N(0,1)) - how much the
floats themselves determine each value. Verdicts:
 ok / REFUSED / WRONG (value off by > max(1e-5, 100*sensitivity) relative) / COUNT (a finite
 ref value below 1e10 x smallest is missing or an extra value appears).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a5"))
from lib import sheet, ref as _ref  # noqa


def ref(K, G, dps=50, scale=1.0):
    for d in (dps, 90, 140):
        try:
            return _ref(K, G, dps=d, scale=scale)
        except Exception:
            pass
    return "mpfail"
import numpy as np

ns = {"__file__": os.path.abspath(sys.argv[1])}
exec(open(sys.argv[1], encoding="utf-8").read(), ns)
rf = sys.argv[1] + ".refs8.json"
refs = json.load(open(rf)) if os.path.exists(rf) else {}
only = os.environ.get("ONLY")
out = {}
tally = {}
for name, c in ns["CASES"].items():
    if only and only not in name:
        continue
    if name not in refs:
        K = np.asarray(c.get("Kref", c["K"]), float); G = np.asarray(c.get("Gref", c["G"]), float)
        rng = np.random.default_rng(1)
        Kp = K * (1 + 1e-15 * rng.standard_normal(K.shape)); Gp = G * (1 + 1e-15 * rng.standard_normal(G.shape))
        if c.get("sym", True):
            Kp = (Kp + Kp.T) / 2; Gp = (Gp + Gp.T) / 2
        dps = 40 if len(K) > 30 else 50
        refs[name] = [ref(K.tolist(), G.tolist(), dps=dps, scale=c.get("scale", 1.0)),
                      ref(Kp.tolist(), Gp.tolist(), dps=dps, scale=c.get("scale", 1.0))]
        json.dump(refs, open(rf, "w"))
    r, rp = refs[name]
    got, t = sheet(c["K"], c["G"], c.get("ku", ""), c.get("gu", ""))
    out[name] = {"got": got, "t": t}
    if isinstance(got, str):
        v = "REFUSED"
    elif isinstance(r, str):
        v = "ref:" + r
    else:
        fin = [x for x in r if abs(x) < 1e14 * c.get("scale", 1.0)] if False else r
        small = min((abs(x) for x in r if x), default=1.0)
        must = [x for x in r if abs(x) <= 1e10 * max(small, 1e-300)]
        # match got to r greedily by sorted order among r values
        rs = sorted(r)
        v = "ok"
        if len(got) > len(r) or len(got) < len(must):
            v = f"COUNT {len(got)} vs ref {len(r)} (must {len(must)})"
        else:
            # choose the subset of r closest to got (drop the largest |r| first)
            cand = sorted(sorted(r, key=abs)[: len(got)])
            rps = sorted(sorted(rp, key=abs)[: len(got)]) if not isinstance(rp, str) and len(rp) >= len(got) else cand
            worst = 0.0
            for a, b, bp in zip(sorted(got), cand, rps):
                sens = abs(b - bp) / max(abs(b), 1e-300)
                tol = max(1e-5, 100 * sens) * abs(b)
                if b == 0 or abs(b) < 1e-30:
                    tol = 1e-12 * max(abs(x) for x in r)
                e = abs(a - b) / tol if tol else (0 if a == b else np.inf)
                worst = max(worst, e)
            if worst > 1:
                v = f"WRONG x{worst:.3g}"
    tally[v.split()[0]] = tally.get(v.split()[0], 0) + 1
    if v not in ("ok", "REFUSED"):
        print(f"{name:44} {v}  t={t:.2f}", flush=True)
        print("    ref", r if isinstance(r, str) else ["%.9g" % x for x in r][:10])
        print("    got", got[:150] if isinstance(got, str) else ["%.9g" % x for x in got][:10])
    elif os.environ.get("V"):
        print(f"{name:44} {v}  t={t:.2f}", flush=True)
json.dump(out, open(sys.argv[2], "w"))
print(tally)
