import os
import sys
import time

import mpmath as mp
import numpy as np

ROOT = os.environ.get("ENGROOT")
sys.path.insert(0, ROOT + "/src")
from engcalc_colab.engine import EngineeringEngine  # noqa: E402
from engcalc_colab.parser import parse_cell  # noqa: E402
import engcalc_colab  # noqa: E402

assert ROOT.replace("\\", "/").rstrip("/").split("/")[-1] in engcalc_colab.__file__.replace("\\", "/"), engcalc_colab.__file__


def lit(m, unit):
    rows = []
    for i, row in enumerate(m):
        cells = []
        for j, v in enumerate(row):
            u = unit[i][j] if isinstance(unit, list) else unit
            cells.append(f"{float(v)!r}[{u}]" if u else f"{float(v)!r}")
        rows.append(", ".join(cells))
    return "[" + "; ".join(rows) + "]"


def sheet(K, G, ku="kN/m", gu="kN/m"):
    src = f"K := {lit(K, ku)}\nG := {lit(G, gu)}\nl := eigenvals(K, G)\n"
    engine = EngineeringEngine()
    t0 = time.perf_counter()
    try:
        for item in parse_cell(src):
            engine.evaluate(item)
        vals = []
        for e in engine.numeric_context.matrices["l"].entries:
            vals.append(float(e.to_base_units().magnitude) if hasattr(e, "to_base_units") else float(e))
        return vals, time.perf_counter() - t0
    except Exception as exc:  # noqa: BLE001
        return "ERR " + f"{type(exc).__name__}: {exc}"[:200], time.perf_counter() - t0


def ref(K, G, dps=60, scale=1.0):
    mp.mp.dps = dps
    Km = mp.matrix([[mp.mpf(float(v)) for v in r] for r in K])
    Gm = mp.matrix([[mp.mpf(float(v)) for v in r] for r in G])
    s = mp.mpf("0.1234567")
    try:
        M = (Km - s * Gm) ** -1 * Gm
    except ZeroDivisionError:
        return "singular"
    ev = mp.eig(M, left=False, right=False)
    big = max(abs(e) for e in ev)
    lam = [s + 1 / e for e in ev if abs(e) > mp.mpf(10) ** (-(dps * 2 // 3)) * big]
    if any(abs(mp.im(x)) > 1e-20 * (1 + abs(x)) and abs(x) * scale < 1e14 for x in lam):
        return "complex"
    return sorted(float(mp.re(x)) * scale for x in lam if abs(mp.im(x)) <= 1e-20 * (1 + abs(x)) or abs(x) * scale >= 1e14)


def judge(r, got, rel=1e-5, absr=1e-12):
    if isinstance(got, str):
        return "REFUSED"
    if isinstance(r, str):
        return "ref:" + r
    r = [x for x in r if abs(x) < 1e14]  # round-off artifacts of a singular G: not reported by design
    if len(got) != len(r):
        return f"COUNT {len(got)}/{len(r)}"
    top = max(abs(x) for x in r) if r else 1
    worst = 0
    for a, b in zip(got, r):
        err = abs(a - b) / (rel * abs(b) + absr * top)
        worst = max(worst, err)
    return "ok" if worst <= 1 else f"WRONG x{worst:.3g}"


def report(name, r, got, t=0.0, show=False):
    j = judge(r, got)
    flag = "" if j == "ok" else "  <<<"
    print(f"{name:34} {j:14} t={t:.3f}{flag}", flush=True)
    if j != "ok" or show:
        print("   ref", r if isinstance(r, str) else ["%.9g" % x for x in r], flush=True)
        print("   got", got if isinstance(got, str) else ["%.9g" % x for x in got], flush=True)
    return j
