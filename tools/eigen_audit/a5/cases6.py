import numpy as np
from frames import build, units_for, convert

CASES = {}
E = 2.0e8  # kN/m2


def add(name, K, G, free, kind_k="kN", kind_g="kN", scale=1.0):
    CASES[name] = {"K": convert(K, free, kind_k), "G": convert(G, free, kind_g),
                   "ku": units_for(free, kind_k), "gu": units_for(free, kind_g),
                   "Kref": K, "Gref": G, "scale": scale}


# --- A. gable portal frame: columns 6 m, rafters inclined to ridge 2 m higher, span 20 m
def gable(P_col=300.0, P_raf=60.0, nseg=2, span=20.0, h=6.0, rise=2.0, base_fixed=True):
    nodes = [(0, 0), (0, h)]
    for i in range(1, nseg + 1):
        nodes.append((span / 2 * i / nseg, h + rise * i / nseg))
    for i in range(nseg - 1, 0, -1):
        nodes.append((span - span / 2 * i / nseg, h + rise * i / nseg))
    nodes += [(span, h), (span, 0)]
    nn = len(nodes)
    elems = [(0, 1, E, 0.012, 2.5e-4, P_col)]
    for i in range(1, nn - 2):
        elems.append((i, i + 1, E, 0.009, 3.5e-4, P_raf))
    elems.append((nn - 2, nn - 1, E, 0.012, 2.5e-4, P_col))
    fixed = [0, 1, 2, 3 * (nn - 1), 3 * (nn - 1) + 1, 3 * (nn - 1) + 2] if base_fixed else [0, 1, 3 * (nn - 1), 3 * (nn - 1) + 1]
    return build(nodes, elems, fixed)


for raf in (60.0, 0.0, -80.0):  # compression, zero, tension in rafters
    for nseg in (1, 2, 4):
        for bf in (True, False):
            K, G, M, free = gable(P_raf=raf, nseg=nseg, base_fixed=bf)
            add(f"gable_r{raf:g}_s{nseg}_{'fix' if bf else 'pin'}", K, G, free)
K, G, M, free = gable(nseg=3)
add("gable_kipin", K, G, free, "kip_in", "kip_in")
add("gable_Nmm", K, G, free, "N_mm", "N_mm")


# --- B. multi-storey frames, bays x storeys, with sizes to 60 dof
def multi(bays=2, storeys=3, h=3.5, bay=6.0, load=200.0, lean=False, tension_brace=False):
    nodes = [(c * bay, l * h) for l in range(storeys + 1) for c in range(bays + 1)]
    nc = bays + 1
    elems = []
    for l in range(storeys):
        for c in range(nc):
            P = load * (storeys - l) * (2.0 if 0 < c < bays else 1.0)
            elems.append((l * nc + c, (l + 1) * nc + c, E, 0.011, 2.2e-4 * (1 + 0.1 * c), P))
    for l in range(1, storeys + 1):
        for c in range(bays):
            elems.append((l * nc + c, l * nc + c + 1, E, 0.008, 4e-4, 0.0))
    if tension_brace:
        for l in range(storeys):
            elems.append((l * nc, (l + 1) * nc + 1, E, 0.002, 1e-6, -150.0))
    fixed = list(range(3 * nc))
    return build(nodes, elems, fixed), nodes, elems, fixed


for bays, storeys in ((1, 1), (1, 3), (2, 3), (3, 4), (4, 4)):
    (K, G, M, free), *_ = multi(bays, storeys)
    add(f"multi_{bays}x{storeys}_n{len(free)}", K, G, free)
    if bays * storeys in (6, 16):
        add(f"multi_{bays}x{storeys}_Nmm", K, G, free, "N_mm", "N_mm")
        add(f"multi_{bays}x{storeys}_kipin", K, G, free, "kip_in", "kip_in")
        (K2, G2, M2, free2), *_ = multi(bays, storeys, tension_brace=True)
        add(f"multi_{bays}x{storeys}_brace", K2, G2, free2)
        add(f"multi_{bays}x{storeys}_neg", K, -G, free)


# --- C. mass pencils
for bays, storeys in ((1, 3), (2, 3), (4, 4)):
    nc = bays + 1
    nodes = [(c * 6.0, l * 3.5) for l in range(storeys + 1) for c in range(nc)]
    base = []
    for l in range(storeys):
        for c in range(nc):
            base.append((l * nc + c, (l + 1) * nc + c, E, 0.011, 2.2e-4, 0.0, 0.086))
    for l in range(1, storeys + 1):
        for c in range(bays):
            base.append((l * nc + c, l * nc + c + 1, E, 0.008, 4e-4, 0.0, 0.063))
    fixed = list(range(3 * nc))
    tag = f"{bays}x{storeys}"
    # lumped member masses (t/m -> kg: rhoA in t/m, M in t; convert to kg by *1000 below)
    K, G, M, free = build(nodes, base, fixed)
    add(f"mass_lumped_norot_{tag}", K, M * 1000, free, "kN", "kg", scale=1000.0)
    add(f"mass_lumped_norot_{tag}_tmm", K, M * 1000, free, "N_mm", "t_mm", scale=1000.0)
    K, G, M, free = build(nodes, base, fixed, consistent=True)
    add(f"mass_consistent_{tag}", K, M * 1000, free, "kN", "kg", scale=1000.0)
    add(f"mass_consistent_{tag}_tmm", K, M * 1000, free, "N_mm", "t_mm", scale=1000.0)
    # floor masses only at storey nodes, no rotary inertia; members massless
    nb = [e[:6] for e in base]
    lump = {i: 12.0 for i in range(nc, len(nodes))}
    K, G, M, free = build(nodes, nb, fixed, lumped=lump)
    add(f"mass_floor_norot_{tag}", K, M * 1000, free, "kN", "kg", scale=1000.0)
    K, G, M, free = build(nodes, nb, fixed, lumped=lump, rot_inertia=1e-4)
    add(f"mass_floor_tinyrot_{tag}", K, M * 1000, free, "kN", "kg", scale=1000.0)

# --- D. springs (elastic supports / stiff springs instead of supports)
for sp in (1e3, 1e6, 1e9, 1e11):
    nodes = [(0, 0), (0, 4), (6, 4), (6, 0)]
    elems = [(0, 1, E, 0.01, 2e-4, 500.0), (1, 2, E, 0.008, 3e-4, 0.0), (2, 3, E, 0.01, 2e-4, 500.0)]
    K, G, M, free = build(nodes, elems, [], springs=[(d, sp) for d in (0, 1, 2, 9, 10, 11)])
    add(f"portal_springs_{sp:g}", K, G, free)
    K, G, M, free = build(nodes, elems, [0, 1, 9, 10], springs=[(2, sp), (11, sp)])
    add(f"portal_rotspring_{sp:g}", K, G, free)

# --- E. mechanisms: pinned portal with beam pinned... (free frame, K singular)
nodes = [(0, 0), (0, 4), (6, 4), (6, 0)]
elems = [(0, 1, E, 0.01, 2e-4, 500.0), (1, 2, E, 0.008, 3e-4, 0.0), (2, 3, E, 0.01, 2e-4, 500.0)]
K, G, M, free = build(nodes, elems, [0, 1, 9, 10])  # pinned bases: fine
add("portal_pinned", K, G, free)
K, G, M, free = build(nodes, elems, [1, 10])  # rollers only: horizontal mechanism
add("portal_mech_rollers", K, G, free)

# --- F. clusters: two identical frames side by side (exact repeats), and a detuned copy
(K1, G1, M1, f1), *_ = multi(1, 3)
n1 = K1.shape[0]
for detune in (0.0, 1e-9, 1e-6, 1e-4, 1e-2):
    K = np.zeros((2 * n1, 2 * n1)); G = np.zeros_like(K)
    K[:n1, :n1] = K1; G[:n1, :n1] = G1
    K[n1:, n1:] = K1 * (1 + detune); G[n1:, n1:] = G1
    # weak coupling spring between the two top nodes (horizontal dof)
    c = 1e-3
    K[n1 - 3, n1 - 3] += c; K[2 * n1 - 3, 2 * n1 - 3] += c; K[n1 - 3, 2 * n1 - 3] -= c; K[2 * n1 - 3, n1 - 3] -= c
    free = f1 + f1
    add(f"twins_detune{detune:g}", K, G, free)
# symmetric gable: near-repeated symmetric/antisymmetric pairs
K, G, M, free = gable(P_raf=0.0, nseg=4)
add("gable_sym_P0", K, G, free)
