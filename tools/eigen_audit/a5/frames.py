"""Realistic frame pencils. build(nodes, elems, fixed, ...) -> K, G, M (kN, m, t-> kg)."""
import numpy as np


def member(L, E, A, I, P, rho_A=0.0, consistent=False):
    k = np.zeros((6, 6))
    EA = E * A / L
    k[0, 0] = k[3, 3] = EA
    k[0, 3] = k[3, 0] = -EA
    EI = E * I
    b = EI * np.array([[12 / L**3, 6 / L**2, -12 / L**3, 6 / L**2], [6 / L**2, 4 / L, -6 / L**2, 2 / L],
                       [-12 / L**3, -6 / L**2, 12 / L**3, -6 / L**2], [6 / L**2, 2 / L, -6 / L**2, 4 / L]])
    g4 = P / (30 * L) * np.array([[36, 3 * L, -36, 3 * L], [3 * L, 4 * L * L, -3 * L, -L * L],
                                  [-36, -3 * L, 36, -3 * L], [3 * L, -L * L, -3 * L, 4 * L * L]])
    g = np.zeros((6, 6))
    idx = [1, 2, 4, 5]
    for i in range(4):
        for j in range(4):
            k[idx[i], idx[j]] = b[i, j]
            g[idx[i], idx[j]] = g4[i, j]
    m = np.zeros((6, 6))
    mt = rho_A * L
    if consistent:
        m[0, 0] = m[3, 3] = mt / 3
        m[0, 3] = m[3, 0] = mt / 6
        c = mt / 420 * np.array([[156, 22 * L, 54, -13 * L], [22 * L, 4 * L * L, 13 * L, -3 * L * L],
                                 [54, 13 * L, 156, -22 * L], [-13 * L, -3 * L * L, -22 * L, 4 * L * L]])
        for i in range(4):
            for j in range(4):
                m[idx[i], idx[j]] = c[i, j]
    else:
        for d in (0, 1, 3, 4):
            m[d, d] = mt / 2
    return k, g, m


def build(nodes, elems, fixed, springs=(), consistent=False, lumped=None, rot_inertia=0.0):
    """elems: (a, b, E, A, I, P[, rhoA]); P > 0 compression. fixed: list of dof indices.
    springs: (dof, k) added (dof kept). lumped: {node: mass} added to translations."""
    n = len(nodes)
    K = np.zeros((3 * n, 3 * n)); G = np.zeros_like(K); M = np.zeros_like(K)
    for e in elems:
        a, b, E, A, I, P = e[:6]
        rho = e[6] if len(e) > 6 else 0.0
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        L = np.hypot(x2 - x1, y2 - y1)
        c, s = (x2 - x1) / L, (y2 - y1) / L
        k, g, m = member(L, E, A, I, P, rho, consistent)
        R = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
        T = np.zeros((6, 6)); T[:3, :3] = R; T[3:, 3:] = R
        d = [3 * a, 3 * a + 1, 3 * a + 2, 3 * b, 3 * b + 1, 3 * b + 2]
        K[np.ix_(d, d)] += T.T @ k @ T
        G[np.ix_(d, d)] += T.T @ g @ T
        M[np.ix_(d, d)] += T.T @ m @ T
    if lumped:
        for nd, mass in lumped.items():
            M[3 * nd, 3 * nd] += mass
            M[3 * nd + 1, 3 * nd + 1] += mass
            M[3 * nd + 2, 3 * nd + 2] += rot_inertia * mass
    for dof, kk in springs:
        K[dof, dof] += kk
    free = [i for i in range(3 * n) if i not in set(fixed)]
    sel = np.ix_(free, free)
    return K[sel], G[sel], M[sel], free


def units_for(free, kind):
    tab = {"kN": ("kN/m", "kN", "kN*m"), "N_mm": ("N/mm", "N", "N*mm"), "kip_in": ("kip/in", "kip", "kip*in"),
           "kg": ("kg", "kg*m", "kg*m^2"), "t_mm": ("kg", "kg*mm", "kg*mm^2")}[kind]
    t = ["u" if d % 3 != 2 else "r" for d in free]

    def u(a, b):
        if a == "u" and b == "u":
            return tab[0]
        if a == "r" and b == "r":
            return tab[2]
        return tab[1]
    return [[u(a, b) for b in t] for a in t]


def convert(A, free, kind):
    """kN,m values -> N,mm (factors), kip,in; kg,m -> t,mm."""
    t = ["u" if d % 3 != 2 else "r" for d in free]
    f = {"kN": (1, 1, 1), "N_mm": (1.0, 1e3, 1e6),  # kN/m = N/mm; kN = 1e3 N; kN m = 1e6 N mm
         "kip_in": (1 / 175.126835, 1 / 4.4482216152605, 1 / 0.1129848290276167),
         "kg": (1, 1, 1), "t_mm": (1.0, 1e3, 1e6)}[kind]
    out = A.copy()
    for i, a in enumerate(t):
        for j, b in enumerate(t):
            out[i, j] *= f[0] if a == b == "u" else (f[2] if a == b == "r" else f[1])
    return out
