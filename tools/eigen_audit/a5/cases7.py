import numpy as np
from frames import build, units_for, convert

CASES = {}
E = 2.0e8


def add(name, K, G, free, kind_k="kN", kind_g="kN", scale=1.0):
    CASES[name] = {"K": convert(K, free, kind_k), "G": convert(G, free, kind_g),
                   "ku": units_for(free, kind_k), "gu": units_for(free, kind_g),
                   "Kref": K, "Gref": G, "scale": scale}


# shear buildings: stiff beams (EA, EI multiplied), floor mass on the left node's horizontal only
for storeys in (3, 6):
    for bays in (1, 2):
        nc = bays + 1
        nodes = [(c * 6.0, l * 3.5) for l in range(storeys + 1) for c in range(nc)]
        for mult in (1.0, 1e3, 1e6, 1e8):
            elems = []
            for l in range(storeys):
                for c in range(nc):
                    elems.append((l * nc + c, (l + 1) * nc + c, E, 0.011, 2.2e-4, 0.0))
            for l in range(1, storeys + 1):
                for c in range(bays):
                    elems.append((l * nc + c, l * nc + c + 1, E * mult, 0.008, 4e-4, 0.0))
            K, G, M, free = build(nodes, elems, list(range(3 * nc)))
            # mass: 20 t per floor at left node horizontal dof; nothing else
            Mm = np.zeros_like(K)
            for l in range(1, storeys + 1):
                d = free.index(3 * (l * nc))
                Mm[d, d] = 20000.0 * (1 + 0.37 * l)
            add(f"shear_{bays}x{storeys}_beam{mult:g}", K, Mm, free, "kN", "kg", scale=1000.0)
            # mass on every translation, equal (symmetric-ish -> clusters), no rotation
            Mm2 = np.zeros_like(K)
            for i, d in enumerate(free):
                if d % 3 != 2:
                    Mm2[i, i] = 5000.0
            add(f"shearall_{bays}x{storeys}_beam{mult:g}", K, Mm2, free, "kN", "kg", scale=1000.0)
            add(f"shearall_{bays}x{storeys}_beam{mult:g}_tmm", K, Mm2, free, "N_mm", "t_mm", scale=1000.0)

# buckling of frames with rigid beams
for mult in (1e3, 1e6, 1e8):
    nodes = [(0, 0), (0, 4), (6, 4), (6, 0), (0, 8), (6, 8)]
    elems = [(0, 1, E, 0.01, 2e-4, 900.0), (3, 2, E, 0.01, 2e-4, 900.0), (1, 2, E * mult, 0.008, 3e-4, 0.0),
             (1, 4, E, 0.01, 2e-4, 450.0), (2, 5, E, 0.01, 2e-4, 450.0), (4, 5, E * mult, 0.008, 3e-4, 0.0)]
    K, G, M, free = build(nodes, elems, [0, 1, 2, 9, 10, 11])
    add(f"buckle_rigidbeam_{mult:g}", K, G, free)

# non-symmetric pencils: frame K, G + follower-like asymmetric part on top rotation/translation
nodes = [(0, 0), (0, 3), (0, 6), (0, 9)]
elems = [(0, 1, E, 0.01, 2e-4, 300.0), (1, 2, E, 0.01, 2e-4, 300.0), (2, 3, E, 0.01, 2e-4, 300.0)]
K, G, M, free = build(nodes, elems, [0, 1, 2])
for eta in (0.05, 0.2, 0.5):
    Gn = G.copy()
    # follower tip load: tangential load adds -eta*P to (tip transverse, tip rotation) coupling only
    i, j = free.index(9), free.index(11)
    Gn[i, j] += eta * 300.0 * 0.3
    add(f"cantilever_follower_{eta:g}", K, Gn, free)

rng = np.random.default_rng(42)
for n in (5, 12, 30):
    for cv in (1.0, 1e3, 1e6):
        A = rng.standard_normal((n, n))
        U, _, Vt = np.linalg.svd(A)
        V = U @ np.diag(np.logspace(0, np.log10(cv), n)) @ Vt
        lam = np.sort(rng.uniform(1, 100, n))
        lam[1] = lam[0] * (1 + 1e-3)
        G = rng.standard_normal((n, n)) + n * np.eye(n)
        K = G @ V @ np.diag(lam) @ np.linalg.inv(V)
        CASES[f"nonsym_n{n}_cv{cv:g}"] = {"K": K, "G": G, "ku": "", "gu": ""}
        # singular G: zero last two rows/cols structure -> K nonsym with zero G rows
        G2 = G.copy(); G2[-2:, :] = 0; G2[:, -2:] = 0
        CASES[f"nonsym_singG_n{n}_cv{cv:g}"] = {"K": K, "G": G2, "ku": "", "gu": ""}

# clusters with wide spectra (polish twin threshold): diagonal-ish K over consistent G
for n in (8, 20):
    for top in (1e4, 1e8):
        for gap in (1e-5, 1e-4, 1e-3):
            Q, _ = np.linalg.qr(rng.standard_normal((n, n)))
            lam = np.concatenate([[1.0, 1 + gap, 1 + 2 * gap], np.logspace(0.5, np.log10(top), n - 3)])
            G = Q @ np.diag(rng.uniform(0.5, 2, n)) @ Q.T
            G = (G + G.T) / 2
            L = np.linalg.cholesky(G)
            K = L @ Q @ np.diag(lam) @ Q.T @ L.T
            K = (K + K.T) / 2
            CASES[f"cluster_n{n}_top{top:g}_gap{gap:g}"] = {"K": K, "G": G, "ku": "", "gu": ""}
            # singular G version: extra massless dofs coupled
            m = 3
            B = rng.standard_normal((n, m))
            Kb = np.block([[K + B @ B.T * 10, B * 10], [B.T * 10, np.eye(m) * 10 + rng.uniform(0, 1, (m, m)) * 0]])
            Kb = (Kb + Kb.T) / 2
            Gb = np.zeros((n + m, n + m)); Gb[:n, :n] = G
            CASES[f"cluster_sing_n{n}_top{top:g}_gap{gap:g}"] = {"K": Kb, "G": Gb, "ku": "", "gu": ""}
