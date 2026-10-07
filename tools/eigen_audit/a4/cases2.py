import numpy as np

CASES = {}


def frame(cols=3, levels=7, h=3.0, bay=6.0, E=2e8, Ac=0.01, Ic=2e-4, Ab=0.008, Ib=3e-4, load=150.0,
          spring=None, mass=None):
    nodes = [(c * bay, l * h) for l in range(levels) for c in range(cols)]
    n = len(nodes)
    K = np.zeros((3 * n, 3 * n))
    G = np.zeros((3 * n, 3 * n))
    M = np.zeros((3 * n, 3 * n))
    elems = []
    for l in range(levels - 1):
        for c in range(cols):
            P = load * (levels - 1 - l) * (1.5 if c == 1 else 1.0)
            elems.append((l * cols + c, (l + 1) * cols + c, Ac, Ic, P))
    for l in range(1, levels):
        for c in range(cols - 1):
            elems.append((l * cols + c, l * cols + c + 1, Ab, Ib, 0.0))
    for a, b, A, I, P in elems:
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        L = np.hypot(x2 - x1, y2 - y1)
        c, s = (x2 - x1) / L, (y2 - y1) / L
        k = np.zeros((6, 6))
        EA, EI = E * A / L, E * I
        k[0, 0] = k[3, 3] = EA; k[0, 3] = k[3, 0] = -EA
        b2 = np.array([[12 / L**3, 6 / L**2, -12 / L**3, 6 / L**2], [6 / L**2, 4 / L, -6 / L**2, 2 / L],
                       [-12 / L**3, -6 / L**2, 12 / L**3, -6 / L**2], [6 / L**2, 2 / L, -6 / L**2, 4 / L]]) * EI
        idx = [1, 2, 4, 5]
        g = np.zeros((6, 6))
        g4 = P / (30 * L) * np.array([[36, 3 * L, -36, 3 * L], [3 * L, 4 * L * L, -3 * L, -L * L],
                                      [-36, -3 * L, 36, -3 * L], [3 * L, -L * L, -3 * L, 4 * L * L]])
        for i in range(4):
            for j in range(4):
                k[idx[i], idx[j]] = b2[i, j]
                g[idx[i], idx[j]] = g4[i, j]
        T = np.zeros((6, 6))
        R = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
        T[:3, :3] = R; T[3:, 3:] = R
        dofs = [3 * a, 3 * a + 1, 3 * a + 2, 3 * b, 3 * b + 1, 3 * b + 2]
        K[np.ix_(dofs, dofs)] += T.T @ k @ T
        G[np.ix_(dofs, dofs)] += T.T @ g @ T
    for i in range(n):
        M[3 * i, 3 * i] = M[3 * i + 1, 3 * i + 1] = 2000.0 if i >= cols else 0.0
    if spring is None:
        free = list(range(3 * cols, 3 * n))
    else:
        free = list(range(3 * n))
        for d in range(3 * cols):
            K[d, d] += spring
            M[d, d] += 0.0
    return K[np.ix_(free, free)], G[np.ix_(free, free)], M[np.ix_(free, free)]


def units(nd, kind):
    tab = {"stiff": {("u", "u"): "kN/m", ("u", "t"): "kN", ("t", "u"): "kN", ("t", "t"): "kN*m"},
           "Nmm": {("u", "u"): "N/mm", ("u", "t"): "N", ("t", "u"): "N", ("t", "t"): "N*mm"},
           "mass": {("u", "u"): "kg", ("u", "t"): "kg*m", ("t", "u"): "kg*m", ("t", "t"): "kg*m^2"}}[kind]
    t = ["u", "u", "t"] * (nd // 3)
    return [[tab[(t[i], t[j])] for j in range(nd)] for i in range(nd)]


def to_nmm(A):
    nd = A.shape[0]
    t = ["u", "u", "t"] * (nd // 3)
    f = {("u", "u"): 1.0, ("u", "t"): 1e3, ("t", "u"): 1e3, ("t", "t"): 1e6}
    return np.array([[A[i, j] * f[(t[i], t[j])] for j in range(nd)] for i in range(nd)])


K, G, M = frame()
nd = K.shape[0]
CASES["F54_buckle"] = {"K": K, "G": G, "ku": units(nd, "stiff"), "gu": units(nd, "stiff")}
CASES["F54_buckle_neg"] = {"K": K, "G": -G, "ku": units(nd, "stiff"), "gu": units(nd, "stiff")}
CASES["F54_buckle_Nmm"] = {"K": to_nmm(K), "G": to_nmm(G), "ku": units(nd, "Nmm"), "gu": units(nd, "Nmm")}
CASES["F54_mass"] = {"K": K, "G": M, "ku": units(nd, "stiff"), "gu": units(nd, "mass"), "scale": 1000.0}
for sp in (1e12, 1e16, 1e20):
    K2, G2, M2 = frame(spring=sp)
    nd2 = K2.shape[0]
    CASES[f"F63_spring_{sp:g}"] = {"K": K2, "G": G2, "ku": units(nd2, "stiff"), "gu": units(nd2, "stiff")}
    CASES[f"F63_spring_mass_{sp:g}"] = {"K": K2, "G": M2, "ku": units(nd2, "stiff"), "gu": units(nd2, "mass"), "scale": 1000.0}
# free-floating frame (mechanism) with mass
K3, G3, M3 = frame(cols=2, levels=3)
Kf, Gf, Mf = frame(cols=2, levels=3, spring=0.0)
for d in range(Mf.shape[0]):
    Mf[d, d] += 500.0 if d % 3 != 2 else 0.0
CASES["F18_free_mass"] = {"K": Kf, "G": Mf, "ku": units(Kf.shape[0], "stiff"), "gu": units(Kf.shape[0], "mass"), "scale": 1000.0}
Mr = M.copy()
for d in range(2, nd, 3):
    Mr[d, d] = 10.0
CASES["F54_fullmass"] = {"K": K, "G": Mr, "ku": units(nd, "stiff"), "gu": units(nd, "mass"), "scale": 1000.0}
