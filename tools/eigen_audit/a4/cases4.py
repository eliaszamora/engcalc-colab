import numpy as np

CASES = {}
for n in (2, 3, 4, 5):
    L = np.diag([2.0] * n) - np.diag([1.0] * (n - 1), 1) - np.diag([1.0] * (n - 1), -1)
    L[0, 0] = L[-1, -1] = 1.0
    for k in (1.0, 3.0, 7.3, 1e4, 2.1e5):
        for mname, m in (("I", np.eye(n)), ("d", np.diag(np.arange(1.0, n + 1))), ("d2", np.diag([2.0, 3, 5, 7, 11][:n]))):
            CASES[f"n{n}_k{k:g}_{mname}"] = {"K": k * L, "G": m, "ku": "kN/m", "gu": "kg", "scale": 1000.0}
