"""Frames: spring supports, eigenvals(-Kg, K), lumped masses w/o rotary inertia + springs, rigid
diaphragms by penalty EA, sizes to 60, N/mm and kip/in."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a5"))
import numpy as np
from frames import build, units_for, convert

CASES = {}
E = 2.0e8


def add(name, K, G, free, kind_k="kN", kind_g="kN", scale=1.0):
    CASES[name] = {"K": convert(K, free, kind_k).tolist(), "G": convert(G, free, kind_g).tolist(),
                   "ku": units_for(free, kind_k), "gu": units_for(free, kind_g),
                   "Kref": K.tolist(), "Gref": G.tolist(), "scale": scale}


def multi(bays, storeys, h=3.5, bay=6.0, load=200.0, EA_beam=E * 0.008, springs_base=None, Icol=2.2e-4,
          rhoA=0.0):
    nodes = [(c * bay, l * h) for l in range(storeys + 1) for c in range(bays + 1)]
    nc = bays + 1
    elems = []
    for l in range(storeys):
        for c in range(nc):
            P = load * (storeys - l) * (2.0 if 0 < c < bays else 1.0)
            elems.append((l * nc + c, (l + 1) * nc + c, E, 0.011, Icol, P, rhoA))
    for l in range(1, storeys + 1):
        for c in range(bays):
            elems.append((l * nc + c, l * nc + c + 1, E, EA_beam / E, 4e-4, 0.0, rhoA))
    if springs_base is None:
        fixed = list(range(3 * nc)); springs = ()
    else:  # base as springs: all three dofs of every base node, value springs_base; nothing fixed
        fixed = []; springs = [(d, springs_base) for d in range(3 * nc)]
    lumped = {nd: 20.0 for nd in range(nc, len(nodes))}
    return build(nodes, elems, fixed, springs=springs, lumped=lumped, rot_inertia=0.0)


for bays, storeys in ((1, 2), (2, 3), (3, 4), (4, 4)):
    for EAb in (1e13, 1e14, 1e15):
        K, G, M, free = multi(bays, storeys, EA_beam=EAb)
        tag = f"{bays}x{storeys}_n{len(free)}_EAb{EAb:g}"
        add(f"diaG_{tag}", K, G, free)
        add(f"diaM_{tag}", K, M, free, "kN", "kg", scale=1000.0)
        add(f"diaNegKg_{tag}", -G, K, free)
    for ks in (1e10, 1e15, 1e20):
        K, G, M, free = multi(bays, storeys, springs_base=ks)
        tag = f"{bays}x{storeys}_n{len(free)}_ks{ks:g}"
        add(f"sprG_{tag}", K, G, free)
        add(f"sprM_{tag}", K, M, free, "kN", "kg", scale=1000.0)
        add(f"sprNegKg_{tag}", -G, K, free)
        if bays * storeys == 6:
            add(f"sprG_{tag}_Nmm", K, G, free, "N_mm", "N_mm")
            add(f"sprG_{tag}_kipin", K, G, free, "kip_in", "kip_in")
            add(f"sprM_{tag}_tmm", K, M, free, "N_mm", "t_mm", scale=1000.0)

# up to 60: 4x5 frame = 60 dofs
for EAb in (E * 0.008, 1e14):
    K, G, M, free = multi(4, 5, EA_beam=EAb)
    add(f"big_G_n{len(free)}_EAb{EAb:g}", K, G, free)
    add(f"big_M_n{len(free)}_EAb{EAb:g}", K, M, free, "kN", "kg", scale=1000.0)
    add(f"big_NegKg_n{len(free)}_EAb{EAb:g}", -G, K, free)
    add(f"big_G_n{len(free)}_EAb{EAb:g}_kipin", K, G, free, "kip_in", "kip_in")
