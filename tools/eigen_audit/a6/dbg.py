import os
import sys
import numpy as np

sys.path.insert(0, os.environ["ENGROOT"] + "/src")
from engcalc_colab import matrix_numeric as mn  # noqa: E402

orig = mn._polished


def spy(value, K, G, others, symmetric=True):
    out = orig(value, K, G, others, symmetric)
    print(f"  estimate {value!r:>24} -> {out[0]!r:>24} {out[1]}  sym={symmetric}")
    return out


mn._polished = spy

rng = np.random.default_rng(11)
for trial in range(66):
    n = int(rng.integers(3, 8))
    cg = 10 ** rng.uniform(-11, -3)
    spring = 10 ** rng.uniform(6, 14)
    Q, _ = np.linalg.qr(rng.standard_normal((n, n)))
    d = rng.uniform(0.5, 1.5, n)
    d[-1] = cg
    G = Q @ np.diag(d) @ Q.T
    G = (G + G.T) / 2
    K = np.diag(np.sort(rng.uniform(1, 3, n)))
    K[-1, -1] += spring
    asym = rng.choice([0.0, 1e-8, 1e-5])
    if asym:
        K = K + asym * rng.standard_normal((n, n)) * 0
        K[0, n - 1] += asym
    if trial == 65:
        np.save("t65K.npy", K)
        np.save("t65G.npy", G)
        print("cond G", np.linalg.cond(G))
        print(mn._pencil_values(K, G))
