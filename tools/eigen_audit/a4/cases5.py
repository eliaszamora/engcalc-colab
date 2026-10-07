import numpy as np

CASES = {}
CASES["NS_zero_rayleigh"] = {"K": np.array([[0.0, 1], [2, 3]]), "G": np.array([[0.0, 1], [1, 1]])}
CASES["NS_zero_rayleigh_b"] = {"K": np.array([[0.0, 4], [10, 1]]), "G": np.array([[0.0, 1], [2, 5]])}
for e in (1e-6, 1e-20, 1e-26):
    CASES[f"near_defective_{e:g}"] = {"K": np.array([[1, 3], [3, e]]), "G": np.array([[0.0, 1], [1, 0]])}
# plain-number pencils, no units
CASES["plain_sym"] = {"K": np.array([[4.0, 1], [1, 3]]), "G": np.array([[2.0, 0], [0, 1]]), "ku": "", "gu": ""}
