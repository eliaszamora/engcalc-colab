import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a5"))
from lib import sheet, ref  # noqa: E402,F401


def judge2(r, got, rel=1e-5):
    """Every got value must match a distinct ref value (multiset). Ref values >=1e14 may be absent."""
    if isinstance(got, str):
        return "REFUSED"
    if isinstance(r, str):
        return "ref:" + r
    small = [x for x in r if abs(x) < 1e14]
    top = max((abs(x) for x in small), default=1.0)
    if len(got) == len(r):
        cand = r
    else:
        cand = small if len(got) == len(small) else None
    if cand is None:
        return f"COUNT {len(got)}/{len(small)}..{len(r)}"
    worst = 0
    for a, b in zip(sorted(got), sorted(cand)):
        tol = rel * abs(b) + 1e-11 * top
        if abs(b) >= 1e14:
            tol = 1e-3 * abs(b)
        worst = max(worst, abs(a - b) / tol)
    return "ok" if worst <= 1 else f"WRONG x{worst:.3g}"


def report2(name, r, got, t=0.0, show=False):
    j = judge2(r, got)
    flag = "" if j in ("ok", "REFUSED") else "  <<<"
    print(f"{name:40} {j:16} t={t:.3f}{flag}", flush=True)
    if (j not in ("ok", "REFUSED")) or show:
        print("   ref", r if isinstance(r, str) else ["%.9g" % x for x in r], flush=True)
        print("   got", got if isinstance(got, str) else ["%.9g" % x for x in got], flush=True)
    return j
