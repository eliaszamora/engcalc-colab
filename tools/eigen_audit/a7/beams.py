"""Continuous beam on many supports written as springs; buckling K x = λ Kg x."""
import numpy as np


def beam(nspan, L=5.0, EI=2e4, P=1.0, spring=1e20, spring_nodes=None, free_rot_first=False):
    n = nspan + 1
    size = 2 * n  # v, theta per node
    K = np.zeros((size, size))
    G = np.zeros((size, size))
    for e in range(nspan):
        k = EI / L**3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                   [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
        g = P / (30 * L) * np.array([[36, 3 * L, -36, 3 * L], [3 * L, 4 * L * L, -3 * L, -L * L],
                                      [-36, -3 * L, 36, -3 * L], [3 * L, -L * L, -3 * L, 4 * L * L]])
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        K[np.ix_(idx, idx)] += k
        G[np.ix_(idx, idx)] += g
    nodes = range(n) if spring_nodes is None else spring_nodes
    for i in nodes:
        K[2 * i, 2 * i] += spring
    return K, G


CASES = {}
for ns in (2, 3, 5):
    K, G = beam(ns)
    CASES[f"beam{ns}_springs1e20"] = {"K": K.tolist(), "G": G.tolist(), "ku": "kN/m", "gu": "kN/m"}
    K, G = beam(ns, spring=1e12)
    CASES[f"beam{ns}_springs1e12"] = {"K": K.tolist(), "G": G.tolist(), "ku": "kN/m", "gu": "kN/m"}
    K, G = beam(ns, spring=1e8)
    CASES[f"beam{ns}_springs1e8"] = {"K": K.tolist(), "G": G.tolist(), "ku": "kN/m", "gu": "kN/m"}
