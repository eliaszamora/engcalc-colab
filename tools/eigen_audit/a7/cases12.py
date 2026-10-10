"""Clusters in wide spectra without springs; symmetric and non-symmetric; negative pairs."""
import numpy as np

CASES = {}
rng = np.random.default_rng(5)
for trial in range(60):
    n = int(rng.integers(6, 16))
    top = 10.0 ** rng.choice([4, 6, 8, 10, 12])
    gap = 10.0 ** rng.choice([-4, -5, -6, -7, -8])
    lam = np.sort(10 ** rng.uniform(0, np.log10(top), n))
    lam[0] = 1.0
    lam[1] = 1.0 + gap
    j = int(rng.integers(2, n - 1))
    lam[j + 1] = lam[j] * (1 + gap)
    if trial % 3 == 1:
        lam[:2] = -lam[:2]
    Q, _ = np.linalg.qr(rng.standard_normal((n, n)))
    G = Q @ np.diag(rng.uniform(0.5, 2, n)) @ Q.T
    G = (G + G.T) / 2
    L = np.linalg.cholesky(G)
    P, _ = np.linalg.qr(rng.standard_normal((n, n)))
    if trial % 3 == 2:
        V = np.eye(n) + 0.2 * rng.standard_normal((n, n)) / np.sqrt(n)
        K = G @ V @ np.diag(lam) @ np.linalg.inv(V)
    else:
        K = L @ P @ np.diag(lam) @ P.T @ L.T
        K = (K + K.T) / 2
    CASES[f"c{trial}_n{n}_top{top:g}_gap{gap:g}_{trial % 3}"] = {"K": K.tolist(), "G": G.tolist(), "ku": "", "gu": "",
                                                                "exact": lam.tolist()}
