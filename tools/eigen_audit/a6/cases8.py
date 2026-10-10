"""Sixth audit: realistic frames with penalty supports (springs), wide spectra, units, non-symmetric,
negative lambda, mechanisms, size up to 60."""
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


# A: portal frame vibration, consistent mass, base supports as springs (penalty) instead of fixity
nodes = [(0, 0), (0, 4), (3, 4), (6, 4), (6, 0)]
elems = [(0, 1, E, 0.01, 2e-4, 0.0, 0.08), (1, 2, E, 0.008, 3e-4, 0.0, 0.06), (2, 3, E, 0.008, 3e-4, 0.0, 0.06),
         (3, 4, E, 0.01, 2e-4, 0.0, 0.08)]
for sp in (1e8, 1e10, 1e12, 1e14, 1e16, 1e18, 1e20):
    springs = [(0, sp), (1, sp), (2, sp), (12, sp), (13, sp), (14, sp)]
    K, G, M, free = build(nodes, elems, [], springs=springs, consistent=True)
    M = M * 1000.0  # t -> kg per m length? rhoA in t/m -> kg
    for kind in ("kN", "N_mm", "kip_in"):
        mk = {"kN": "kg", "N_mm": "t_mm", "kip_in": "kg"}[kind]
        add(f"portal_vib_sp{sp:g}_{kind}", K, M, free, kind, mk, scale=1000.0)
    # buckling with spring supports (G singular)
    elems_b = [(0, 1, E, 0.01, 2e-4, 500.0), (1, 2, E, 0.008, 3e-4, 0.0), (2, 3, E, 0.008, 3e-4, 0.0),
               (3, 4, E, 0.01, 2e-4, 500.0)]
    Kb, Gb, Mb, freeb = build(nodes, elems_b, [], springs=springs)
    add(f"portal_buckle_sp{sp:g}", Kb, Gb, freeb)
    # one roller support as a spring only (vertical), others fixed
    Kc, Gc, Mc, freec = build(nodes, elems_b, [0, 1, 2, 12, 14], springs=[(13, sp)])
    add(f"portal_buckle_onespring{sp:g}", Kc, Gc, freec)

# B: cantilever column 10 segments, consistent mass, tip spring (lateral brace) of growing stiffness
nseg = 10
nodes = [(0, 0.5 * i) for i in range(nseg + 1)]
elems = [(i, i + 1, E, 0.01, 2e-4, 400.0, 0.08) for i in range(nseg)]
for sp in (1e6, 1e10, 1e14, 1e16, 1e18):
    K, G, M, free = build(nodes, elems, [0, 1, 2], springs=[(3 * nseg, sp)], consistent=True)
    add(f"col_vib_brace{sp:g}", K, M * 1000.0, free, "kN", "kg", scale=1000.0)
    add(f"col_buck_brace{sp:g}", K, G, free)
    # follower-ish asymmetry
    Gn = G.copy()
    i, j = free.index(3 * nseg), free.index(3 * nseg + 2)
    Gn[i, j] += 0.1 * 400.0 * 0.5
    add(f"col_follow_brace{sp:g}", K, Gn, free)
    Ka = K.copy()
    Ka[0, 1] *= 1 + 1e-7
    add(f"col_asymK_brace{sp:g}", Ka, G, free)

# C: 54x54 frame, 3 bays x 3 storeys, lumped mass, rigid diaphragm beams x1e6 and penalty supports
def frame(bays, storeys, mult=1.0, sp=None, P=600.0):
    nc = bays + 1
    nodes = [(c * 6.0, l * 3.5) for l in range(storeys + 1) for c in range(nc)]
    elems = []
    for l in range(storeys):
        for c in range(nc):
            elems.append((l * nc + c, (l + 1) * nc + c, E, 0.011, 2.2e-4, P * (storeys - l) / storeys, 0.09))
    for l in range(1, storeys + 1):
        for c in range(bays):
            elems.append((l * nc + c, l * nc + c + 1, E * mult, 0.008, 4e-4, 0.0, 0.06))
    if sp is None:
        return build(nodes, elems, list(range(3 * nc)), consistent=True)
    return build(nodes, elems, [], springs=[(d, sp) for d in range(3 * nc)], consistent=True)


for bays, storeys in ((3, 6), (4, 4)):
    for mult in (1.0, 1e6):
        for sp in (None, 1e12, 1e16):
            K, G, M, free = frame(bays, storeys, mult, sp)
            tag = f"frame{bays}x{storeys}_m{mult:g}_sp{sp}"
            add(tag + "_buck", K, G, free)
            add(tag + "_vib", K, M * 1000.0, free, "kN", "kg", scale=1000.0)

# D: negative lambda (tension in G), indefinite G, symmetric clusters 1e-7 apart, mechanisms
rng = np.random.default_rng(99)
for n in (10, 30, 60):
    Q, _ = np.linalg.qr(rng.standard_normal((n, n)))
    lam = np.concatenate([[-5.0, -5.0 * (1 + 1e-7), 0.0, 0.0, 3.0, 3.0 * (1 + 1e-7), 3.0 * (1 + 2e-7)],
                          np.sort(rng.uniform(4, 1e4, n - 7))])
    Gd = Q @ np.diag(rng.uniform(0.5, 2, n)) @ Q.T
    Gd = (Gd + Gd.T) / 2
    L = np.linalg.cholesky(Gd)
    P, _ = np.linalg.qr(rng.standard_normal((n, n)))
    K = L @ P @ np.diag(lam) @ P.T @ L.T
    K = (K + K.T) / 2
    CASES[f"neg_cluster_mech_n{n}"] = {"K": K, "G": Gd, "ku": "", "gu": ""}
    # indefinite G: flip sign of some
    Gi = Q @ np.diag(rng.uniform(0.5, 2, n) * np.where(np.arange(n) % 3 == 0, -1, 1)) @ Q.T
    Gi = (Gi + Gi.T) / 2
    CASES[f"indefG_n{n}"] = {"K": K, "G": Gi, "ku": "", "gu": ""}
    # same with a penalty spring added on one dof
    Ks = K.copy()
    Ks[0, 0] += 1e14
    CASES[f"neg_cluster_spring_n{n}"] = {"K": Ks, "G": Gd, "ku": "", "gu": ""}
    # non-symmetric clustered: similarity by mildly non-orthogonal V
    V = np.eye(n) + 0.3 * rng.standard_normal((n, n)) / np.sqrt(n)
    Kn = Gd @ V @ np.diag(lam) @ np.linalg.inv(V)
    CASES[f"nonsym_cluster_n{n}"] = {"K": Kn, "G": Gd, "ku": "", "gu": ""}
    Kn2 = Kn.copy()
    Kn2[1, 1] += 1e14
    CASES[f"nonsym_cluster_spring_n{n}"] = {"K": Kn2, "G": Gd, "ku": "", "gu": ""}
