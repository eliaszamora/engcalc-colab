"""Stiff link / penalty constraint beside soft modes, realistic frames. Prints per-value relative error."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a6"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a5"))
from lib6 import sheet, ref
from frames import build
import numpy as np

CASES = {}
# two masses, rigid link as penalty spring kb, ground spring k (kN/m, t)
for kb, k in ((1e20, 1e3), (1e16, 100.0), (1e15, 1.0), (1e14, 5.0)):
    K = [[kb + k, -kb], [-kb, kb]]
    CASES[f"link kb={kb:g} k={k:g}"] = (K, [[2.0, 0], [0, 3.0]])

# portal frame, beam made axially rigid (EA huge), lumped masses at top: free vibration
def portal(EA_beam, consistent=False, P=None):
    nodes = [(0, 0), (0, 4), (6, 4), (6, 0)]
    E = 2e8  # kN/m2
    elems = [(0, 1, E, 0.01, 1e-4, 0.0 if P is None else P), (1, 2, E, EA_beam / E, 2e-4, 0.0),
             (3, 2, E, 0.01, 1e-4, 0.0 if P is None else P)]
    fixed = [0, 1, 2, 9, 10, 11]
    return build(nodes, elems, fixed, lumped={1: 10.0, 2: 10.0}, rot_inertia=0.0)

for EA in (2e6, 1e12, 1e15, 1e18):
    out = portal(EA)
    K, G, M, free = out if len(out) == 4 else (out[0], out[1], out[2], None)
    CASES[f"portal rigid-beam EA={EA:g} M"] = (K, M)
    CASES[f"portal rigid-beam EA={EA:g} G"] = (K, G) if False else (K, portal(EA, P=100.0)[1])

if __name__ == "__main__":
    for name, (K, G) in CASES.items():
        K = np.asarray(K, float); G = np.asarray(G, float)
        r = ref(K.tolist(), G.tolist())
        got, t = sheet(K.tolist(), G.tolist())
        if isinstance(got, str) or isinstance(r, str):
            print(f"{name:36} ref={r if isinstance(r,str) else ['%.6g'%x for x in r][:4]} got={got[:90] if isinstance(got,str) else got}")
            continue
        rr = [x for x in r if abs(x) < 1e14]
        if len(got) != len(rr):
            print(f"{name:36} COUNT got {len(got)} ref {len(r)}/{len(rr)}", ['%.6g'%x for x in r][:6], ['%.6g'%x for x in got][:6])
            continue
        errs = [abs(a - b) / max(abs(b), 1e-300) for a, b in zip(got, rr)]
        w = max(errs)
        print(f"{name:36} worst-rel {w:.2e} {'<<<' if w > 1e-5 else ''}")
        if w > 1e-5:
            print("   ref", ['%.8g' % x for x in rr][:8]); print("   got", ['%.8g' % x for x in got][:8])
