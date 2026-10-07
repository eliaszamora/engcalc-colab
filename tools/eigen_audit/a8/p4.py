"""Rigid end offsets modelled as short stiff elements (no penalty spring) - portal frame."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a6"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a5"))
from lib6 import sheet, ref
from frames import build
import numpy as np

E = 2e8
for Lo, Ar, Ir, Ic in ((0.3, 1.0, 1.0, 1e-4), (0.05, 1.0, 1.0, 1e-4), (0.05, 10.0, 10.0, 1e-5), (0.01, 10.0, 10.0, 1e-5), (0.3, 1e4, 1e4, 1e-5)):
    nodes = [(0, 0), (0, 4), (Lo, 4), (6 - Lo, 4), (6, 4), (6, 0)]
    elems = [(0, 1, E, 0.01, Ic, 100.0), (1, 2, E, Ar, Ir, 0.0), (2, 3, E, 0.008, 4e-4, 0.0), (3, 4, E, Ar, Ir, 0.0),
             (5, 4, E, 0.01, Ic, 100.0)]
    K, G, M, free = build(nodes, elems, [0, 1, 2, 15, 16, 17], lumped={1: 10.0, 4: 10.0, 2: 0.1, 3: 0.1}, rot_inertia=0.0)
    for nm, B in (("G", G), ("M", M)):
        r = ref(K.tolist(), B.tolist())
        got, t = sheet(K.tolist(), B.tolist())
        rr = sorted(sorted(r, key=abs)[:len(got)]) if not isinstance(got, str) and not isinstance(r, str) else r
        print(f"Lo={Lo} A={Ar} I={Ir} Ic={Ic} {nm}: ref {['%.6g'%x for x in rr][:3] if not isinstance(rr,str) else rr} got {got[:80] if isinstance(got,str) else ['%.6g'%x for x in got][:3]}")
