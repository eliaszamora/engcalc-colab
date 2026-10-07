"""Non-symmetric G (partly tangential / follower tip load) on a cantilever whose base is a penalty spring."""
import numpy as np
from frames import build, units_for
from lib import sheet, ref, report

E = 2e8
nodes = [(0, 0), (0, 3), (0, 6), (0, 9)]
elems = [(0, 1, E, 0.01, 2e-4, 300.0), (1, 2, E, 0.01, 2e-4, 300.0), (2, 3, E, 0.01, 2e-4, 300.0)]
for spring in (None, 1e8, 1e12, 1e16, 1e20):
    for eta in (0.0, 0.2):
        if spring is None:
            K, G, M, free = build(nodes, elems, [0, 1, 2])
        else:
            K, G, M, free = build(nodes, elems, [], springs=[(0, spring), (1, spring), (2, spring)])
        i, j = free.index(9), free.index(11)
        G[i, j] += eta * 300.0 * 0.3
        u = units_for(free, "kN")
        got, t = sheet(K, G, u, u)
        report(f"cantilever_spring{spring}_eta{eta:g}", ref(K, G), got, t, show=False)
