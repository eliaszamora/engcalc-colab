"""Find a small hand-writable pencil giving a duplicated (wrong) eigenvalue."""
import numpy as np
from lib6 import sheet, ref, judge2

rng = np.random.default_rng(5)
found = 0
for trial in range(4000):
    n = 3
    A = np.round(rng.uniform(-1, 1, (n, n)), 1)
    G = np.round(A @ A.T + np.eye(n) * 0.5, 1)
    if np.linalg.eigvalsh(G).min() <= 0.05:
        continue
    k = sorted(rng.choice([1, 2, 3, 4, 5, 6], size=n, replace=False).tolist())
    K = np.diag(np.array(k, dtype=float))
    K[-1, -1] = 1e16
    # quick pre-screen with numpy: eigvals estimates vs true via eigh of Cholesky
    L = np.linalg.cholesky(G)
    Li = np.linalg.inv(L)
    true = np.linalg.eigvalsh(Li @ K @ Li.T)
    got, t = sheet(K, G, "", "")
    if isinstance(got, str):
        continue
    j = judge2(sorted(true.tolist()), got)
    if j != "ok":
        r = ref(K, G)
        j2 = judge2(r, got)
        if j2 != "ok":
            print("K diag", k[:-1], "G", G.tolist(), "ref", r, "got", got, j2, flush=True)
            found += 1
            if found >= 3:
                break
print("done", trial)
