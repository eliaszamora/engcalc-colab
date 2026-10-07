"""Clusters beside stiff springs: soft spectrum with a near pair, springs on a few DOFs, coupling."""
import numpy as np

CASES = {}
rng = np.random.default_rng(77)
for trial in range(80):
    n = int(rng.integers(5, 11))
    m = int(rng.integers(1, max(2, (n - 1) // 2)))
    s = 10.0 ** rng.choice([16, 18, 20])
    gap = 10.0 ** rng.choice([-1.5, -2, -3, -4])
    ns = n - m
    lam = np.sort(rng.uniform(1, 100, ns))
    lam[1] = lam[0] * (1 + gap)
    Q, _ = np.linalg.qr(rng.standard_normal((ns, ns)))
    Gs = Q @ np.diag(rng.uniform(0.5, 2, ns)) @ Q.T
    Gs = (Gs + Gs.T) / 2
    L = np.linalg.cholesky(Gs)
    P, _ = np.linalg.qr(rng.standard_normal((ns, ns)))
    Ks = L @ P @ np.diag(lam) @ P.T @ L.T
    K = np.zeros((n, n))
    G = np.zeros((n, n))
    K[:ns, :ns] = (Ks + Ks.T) / 2
    G[:ns, :ns] = Gs
    C = rng.standard_normal((ns, m)) * 10
    K[:ns, ns:] = C
    K[ns:, :ns] = C.T
    K[ns:, ns:] = np.diag(s * rng.uniform(1, 3, m)) + 50 * np.eye(m)
    G[ns:, ns:] = np.diag(rng.uniform(0.5, 2, m))
    D = rng.uniform(0.5, 2, (n, 1))
    G[:ns, ns:] = 0.1 * rng.standard_normal((ns, m))
    G[ns:, :ns] = G[:ns, ns:].T
    CASES[f"t{trial}_n{n}_m{m}_s{s:g}_gap{gap:g}"] = {"K": K.tolist(), "G": G.tolist(), "ku": "", "gu": ""}
