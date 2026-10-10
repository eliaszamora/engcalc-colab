"""Probe: genuine small lambda whose mode has large |K| components (stiff link), zero snapping."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a6"))
from lib6 import sheet, ref, report2
import numpy as np

cases = {}
for kb in (1e8, 1e10, 1e11, 1e12, 1e13):
    for k in (1.0, 0.1):
        K = [[kb + k, -kb], [-kb, kb]]
        cases[f"link kb={kb:g} k={k:g}"] = (K, [[1.0, 0], [0, 1.0]])
# chain of 5 masses linked by stiff springs, soft ground spring at one end
for kb in (1e9, 1e11, 1e12):
    n = 5
    K = np.zeros((n, n))
    for i in range(n - 1):
        K[i:i+2, i:i+2] += kb * np.array([[1, -1], [-1, 1]])
    K[0, 0] += 10.0
    K[n-1, n-1] += 30.0
    cases[f"chain5 kb={kb:g}"] = (K.tolist(), np.eye(n).tolist())
# buckling: stiff column (axial) + soft sway spring (realistic-ish units kN, m)
for EA in (1e7, 1e9, 1e11):
    # 2 dof: top horizontal u (sway spring ks) coupled via rigid bar to 2nd node
    ks = 50.0
    K = np.array([[EA + ks, -EA], [-EA, EA + 1.0]])
    G = np.array([[1.0, 0], [0, 0.0]])
    cases[f"sway EA={EA:g}"] = (K.tolist(), G.tolist())
for name, (K, G) in cases.items():
    r = ref(K, G)
    got, t = sheet(K, G)
    report2(name, r, got, t, show=True)
