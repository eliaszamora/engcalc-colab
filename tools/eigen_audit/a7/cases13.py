"""Mechanism + springs: portal on rollers written as vertical springs (horizontal rigid-body mode)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a5"))
from frames import build, units_for, convert  # noqa: E402

CASES = {}
E = 2.0e8


def add(name, K, G, free, kind_k="kN", kind_g="kN", scale=1.0):
    CASES[name] = {"K": convert(K, free, kind_k), "G": convert(G, free, kind_g),
                   "ku": units_for(free, kind_k), "gu": units_for(free, kind_g),
                   "Kref": K, "Gref": G, "scale": scale}


nodes = [(0, 0), (0, 4), (3, 4), (6, 4), (6, 0)]
ev = [(0, 1, E, 0.01, 2e-4, 0.0, 0.08), (1, 2, E, 0.008, 3e-4, 0.0, 0.06), (2, 3, E, 0.008, 3e-4, 0.0, 0.06),
      (3, 4, E, 0.01, 2e-4, 0.0, 0.08)]
for sp in (1e8, 1e12, 1e16, 1e20):
    K, G, M, free = build(nodes, ev, [], springs=[(1, sp), (13, sp)], consistent=True)
    add(f"rollers_vib_sp{sp:g}", K, M * 1000.0, free, "kN", "kg", scale=1000.0)
    # plus a horizontal spring that is genuinely soft (a brace): 1 kN/m
    K2 = K.copy()
    K2[0, 0] += 1.0
    add(f"rollers_softbrace_vib_sp{sp:g}", K2, M * 1000.0, free, "kN", "kg", scale=1000.0)
# fixed supports removed exactly, mechanism by a hinge: free-free plus soft spring
K, G, M, free = build(nodes, ev, [1, 13], consistent=True)
add("rollers_exact_vib", K, M * 1000.0, free, "kN", "kg", scale=1000.0)
K2 = K.copy()
K2[0, 0] += 1e-3
add("rollers_exact_softbrace1e-3_vib", K2, M * 1000.0, free, "kN", "kg", scale=1000.0)
K3 = K.copy()
K3[0, 0] += 1e-6
add("rollers_exact_softbrace1e-6_vib", K3, M * 1000.0, free, "kN", "kg", scale=1000.0)
