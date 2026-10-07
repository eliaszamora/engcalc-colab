"""Symmetric pencils: K PD with G indefinite/singular, mixed-sign lambda, |lambda| equal pairs,
springs on half / more than half the DOFs, soft clustered modes, Cholesky-count mismatches."""
import numpy as np

CASES = {}
rng = np.random.default_rng(808)


def congruent(lam, n_null=0, cond=1.0):
    """K = X^-T X^-1, G = X^-T diag(mu) X^-1 with mu = 1/lam (0 for null)."""
    n = len(lam) + n_null
    X = np.linalg.qr(rng.standard_normal((n, n)))[0] @ np.diag(10 ** rng.uniform(0, np.log10(cond), n))
    Xi = np.linalg.inv(X)
    mu = np.concatenate([1.0 / np.asarray(lam), np.zeros(n_null)])
    K = Xi.T @ Xi
    G = Xi.T @ np.diag(mu) @ Xi
    return (K + K.T) / 2, (G + G.T) / 2


for t in range(30):
    n = int(rng.integers(3, 12))
    lam = 10 ** rng.uniform(0, 4, n) * rng.choice([-1, 1], n)
    if t % 3 == 0:  # |lambda| equal pairs of both signs
        lam[1] = -lam[0]
        lam[3 % n] = -lam[2 % n] if n > 3 else lam[2 % n]
    nn = int(rng.integers(0, 3))
    K, G = congruent(lam, nn, cond=10 ** rng.uniform(0, 3))
    CASES[f"cong{t}_n{n}_null{nn}"] = {"K": K.tolist(), "G": G.tolist()}

# springs on exactly half / more than half of DOFs, with a mechanism-free beam chain; G indefinite
for t in range(24):
    n = int(rng.integers(4, 13))
    A = rng.standard_normal((n, n))
    K0 = A @ A.T / n + 0.1 * np.eye(n)
    frac = [0.5, 0.75, 1.0][t % 3]
    m = int(round(frac * n))
    dofs = rng.choice(n, m, replace=False)
    ks = 10.0 ** rng.choice([8, 12, 16, 20])
    K = K0.copy()
    for d in dofs:
        K[d, d] += ks * rng.uniform(1, 3)
    B = rng.standard_normal((n, n))
    G = (B + B.T) / 2 if t % 2 else B @ B.T / n
    if t % 4 == 3:
        G[:, dofs[:1]] = 0; G[dofs[:1], :] = 0
    CASES[f"spr{t}_n{n}_frac{frac}_ks{ks:g}_{'indef' if t % 2 else 'pd'}"] = {"K": K.tolist(), "G": G.tolist()}

# clustered soft modes from springs: chain with identical soft modes, springs elsewhere
for t in range(12):
    n = int(rng.integers(6, 15))
    K = np.diag(np.full(n, 2.0)) - np.diag(np.ones(n - 1), 1) - np.diag(np.ones(n - 1), -1)
    K[0, 0] = K[-1, -1] = 1.0  # free-free chain: singular (rigid mode)
    ks = 10.0 ** rng.choice([10, 14, 18, 20])
    m = n // 2 + (t % 3)
    for d in range(m):
        K[d, d] += ks
    G = np.eye(n) if t % 2 == 0 else np.diag(rng.uniform(0.5, 2, n))
    CASES[f"chainspr{t}_n{n}_m{m}_ks{ks:g}"] = {"K": K.tolist(), "G": G.tolist()}
