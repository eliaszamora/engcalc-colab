"""Seventh audit: supports written as springs on half or more of the DOFs (the median rule)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a5"))
from frames import build, units_for, convert  # noqa: E402

CASES = {}
E = 2.0e8


def add(name, K, G, free, kind_k="kN", kind_g="kN", scale=1.0):
    CASES[name] = {"K": convert(K, free, kind_k), "G": convert(G, free, kind_g),
                   "ku": units_for(free, kind_k), "gu": units_for(free, kind_g),
                   "Kref": K, "Gref": G, "scale": scale}


# A: plain 4-node portal (h 4, span 6), fixed bases written as springs on all 6 base DOFs (half of 12)
nodes = [(0, 0), (0, 4), (6, 4), (6, 0)]
for sp in (1e10, 1e14, 1e16, 1e20):
    springs = [(d, sp) for d in (0, 1, 2, 9, 10, 11)]
    eb = [(0, 1, E, 0.01, 2e-4, 500.0), (1, 2, E, 0.008, 3e-4, 0.0), (2, 3, E, 0.01, 2e-4, 500.0)]
    K, G, M, free = build(nodes, eb, [], springs=springs)
    for kind in ("kN", "N_mm", "kip_in"):
        add(f"portal4_buck_sp{sp:g}_{kind}", K, G, free, kind, kind)
    add(f"portal4_buck_inv_sp{sp:g}", -G, K, free)          # his eigenvals(-K_g, K)
    add(f"portal4_buck_negG_sp{sp:g}", K, -G, free)          # eigenvals(K, -K_g)
    ev = [(0, 1, E, 0.01, 2e-4, 0.0, 0.08), (1, 2, E, 0.008, 3e-4, 0.0, 0.06), (2, 3, E, 0.01, 2e-4, 0.0, 0.08)]
    K, G, M, free = build(nodes, ev, [], springs=springs, consistent=True)
    add(f"portal4_vibcons_sp{sp:g}", K, M * 1000.0, free, "kN", "kg", scale=1000.0)
    K, G, M, free = build(nodes, [e[:6] for e in ev], [], springs=springs, lumped={1: 5.0, 2: 5.0})
    add(f"portal4_viblump_sp{sp:g}", K, M * 1000.0, free, "kN", "kg", scale=1000.0)

# B: two-bar truss (as frame with tiny I) -> use a pin-jointed frame: three nodes, supports springs
nodes = [(0, 0), (3, 4), (6, 0)]
for sp in (1e12, 1e16, 1e20):
    springs = [(d, sp) for d in (0, 1, 6, 7)]
    eb = [(0, 1, E, 0.002, 1e-5, 0.0, 0.016), (1, 2, E, 0.002, 1e-5, 0.0, 0.016)]
    K, G, M, free = build(nodes, eb, [2, 8], springs=springs, consistent=True)
    add(f"truss_vib_sp{sp:g}", K, M * 1000.0, free, "kN", "kg", scale=1000.0)

# C: continuous column over 4 storeys, braced at each floor by a spring (lateral brace)
nseg = 4
nodes = [(0, 3.0 * i) for i in range(nseg + 1)]
for sp in (1e12, 1e16, 1e20):
    eb = [(i, i + 1, E, 0.01, 2e-4, 400.0) for i in range(nseg)]
    springs = [(3 * i, sp) for i in range(1, nseg + 1)] + [(3 * i + 1, sp) for i in range(1, nseg + 1)]
    K, G, M, free = build(nodes, eb, [0, 1], springs=springs)
    add(f"braced_col_sp{sp:g}", K, G, free)
    add(f"braced_col_inv_sp{sp:g}", -G, K, free)

# D: 54x54 frame (3 bays x 3 storeys + ...): 4 cols x 4 levels -> 16 nodes = 48; 3x4 cols x5 lev? use 3 bays x 4 storeys, base fixed
def frame(bays, storeys, sp=None, P=600.0):
    nc = bays + 1
    nodes = [(c * 6.0, l * 3.5) for l in range(storeys + 1) for c in range(nc)]
    elems = []
    for l in range(storeys):
        for c in range(nc):
            elems.append((l * nc + c, (l + 1) * nc + c, E, 0.011, 2.2e-4, P * (storeys - l) / storeys))
    for l in range(1, storeys + 1):
        for c in range(bays):
            elems.append((l * nc + c, l * nc + c + 1, E, 0.008, 4e-4, 0.0))
    if sp is None:
        return build(nodes, elems, list(range(3 * nc)))
    return build(nodes, elems, [], springs=[(d, sp) for d in range(3 * nc)])


K, G, M, free = frame(2, 6)  # 3 cols x 6 levels = 18 nodes x3 = 54
add("frame54_buck", K, G, free)
add("frame54_buck_inv", -G, K, free)
add("frame54_buck_negG", K, -G, free)
add("frame54_buck_kipin", K, G, free, "kip_in", "kip_in")
