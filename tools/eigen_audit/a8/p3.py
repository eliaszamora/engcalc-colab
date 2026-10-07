"""Portal frames with a penalty-rigid beam (EA huge) - sweep, M and G pencils."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a6"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a5"))
from lib6 import sheet, ref
from frames import build
import numpy as np


def portal(EA_beam, I_col=1e-4, P=0.0, mass=10.0, link=False, E=2e8):
    nodes = [(0, 0), (0, 4), (6, 4), (6, 0)]
    elems = [(0, 1, E, 0.01, I_col, P), (1, 2, E, EA_beam / E, 2e-4, 0.0), (3, 2, E, 0.01, I_col, P)]
    return build(nodes, elems, [0, 1, 2, 9, 10, 11], lumped={1: mass, 2: mass}, rot_inertia=0.0)


CASES = {}
for EA in (3e15, 1e16, 3e16, 1e17):
    for I in (1e-4, 1e-5, 1e-6):
        K, G, M, free = portal(EA, I_col=I, P=100.0 * I / 1e-4)
        CASES[f"portal EA={EA:g} I={I:g} M"] = (K, M)
        CASES[f"portal EA={EA:g} I={I:g} G"] = (K, G)

if __name__ == "__main__":
    for name, (K, G) in CASES.items():
        r = ref(K.tolist(), G.tolist())
        got, t = sheet(K.tolist(), G.tolist())
        if isinstance(got, str) or isinstance(r, str):
            print(f"{name:34} REF {['%.6g'%x for x in r][:3] if not isinstance(r,str) else r} GOT {got[:70] if isinstance(got,str) else got}")
            continue
        n = len(got)
        rr = r[:n]
        errs = [abs(a - b) / max(abs(b), 1e-300) for a, b in zip(got, rr)]
        w = max(errs) if errs else 0
        print(f"{name:34} n={n}/{len(r)} worst-rel {w:.2e} {'<<<' if w > 1e-4 else ''}  ref {['%.6g'%x for x in rr][:3]} got {['%.6g'%x for x in got][:3]}")
