"""Mechanisms where G loads the mechanism (lambda = 0), leaning columns, hinged frames."""
import numpy as np
from frames import build, units_for
from lib import sheet, ref, report

E = 2e8
# portal: pinned bases, columns pinned at top too (truss-like columns) -> sway mechanism.
# Model the hinge by a tiny EI? Instead: two-column frame where both columns are 'leaning' (truss bars, I=0)
for I_col in (0.0, 1e-12, 2e-4):
    nodes = [(0, 0), (0, 4), (6, 4), (6, 0)]
    elems = [(0, 1, E, 0.01, I_col, 500.0), (1, 2, E, 0.008, 3e-4, 0.0), (3, 2, E, 0.01, I_col, 500.0)]
    K, G, M, free = build(nodes, elems, [0, 1, 2, 9, 10, 11])
    # rotational dofs at column bases are fixed; with I_col=0 the sway is a mechanism (K zero on it)
    u = units_for(free, "kN")
    got, t = sheet(K, G, u, u)
    report(f"leaning_portal_Icol{I_col:g}", ref(K, G), got, t, show=True)
# mixed: one rigid column + one leaning column
for P_lean in (0.0, 300.0, 1500.0):
    nodes = [(0, 0), (0, 4), (6, 4), (6, 0)]
    elems = [(0, 1, E, 0.01, 2e-4, 500.0), (1, 2, E, 0.008, 3e-4, 0.0), (3, 2, E, 0.01, 0.0, P_lean)]
    K, G, M, free = build(nodes, elems, [0, 1, 2, 9, 10, 11])
    keep = [i for i, d in enumerate(free) if d != 11]  # leaning column base rotation would be free; drop
    K = K[np.ix_(keep, keep)]; G = G[np.ix_(keep, keep)]
    fr = [free[i] for i in keep]
    u = units_for(fr, "kN")
    got, t = sheet(K, G, u, u)
    report(f"rigid_plus_leaning_P{P_lean:g}", ref(K, G), got, t, show=True)
