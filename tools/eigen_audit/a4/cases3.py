import numpy as np

exec(open(__file__.replace("cases3.py", "cases2.py") if "__file__" in dir() else "cases2.py", encoding="utf-8").read())
CASES = {}
rng = np.random.default_rng(3)

Kf, Gf, Mf = frame(cols=2, levels=3, spring=0.0)
nd = Kf.shape[0]
Mfull = Mf.copy()
for d in range(nd):
    Mfull[d, d] += 500.0 if d % 3 != 2 else 50.0
CASES["F18_free_fullmass"] = {"K": Kf, "G": Mfull, "ku": units(nd, "stiff"), "gu": units(nd, "mass"), "scale": 1000.0}
Mlump = Mf.copy()
for d in range(nd):
    Mlump[d, d] += 500.0 if d % 3 != 2 else 0.0
CASES["F18_free_lump"] = {"K": Kf, "G": Mlump, "ku": units(nd, "stiff"), "gu": units(nd, "mass"), "scale": 1000.0}
# free frame buckling (G singular) - zero modes where G has something
CASES["F18_free_buckle"] = {"K": Kf, "G": Gf, "ku": units(nd, "stiff"), "gu": units(nd, "stiff")}

for n in (4, 8, 12):
    L = np.diag([2.0] * n) - np.diag([1.0] * (n - 1), 1) - np.diag([1.0] * (n - 1), -1)
    L[0, 0] = L[-1, -1] = 1.0
    Q, _ = np.linalg.qr(rng.standard_normal((n, n)))
    CASES[f"L_rot_mass_{n}"] = {"K": 7.3 * (Q @ L @ Q.T), "G": np.eye(n)}
    D = np.diag(rng.uniform(1, 5, n))
    CASES[f"L_diagmass_{n}"] = {"K": 1e4 * L, "G": D}
    Dz = D.copy(); Dz[1, 1] = 0.0; Dz[2, 2] = 0.0
    CASES[f"L_singmass_{n}"] = {"K": 1e4 * L, "G": Dz}
    # two-rigid-body mechanism
    L2 = L.copy(); L2[n // 2 - 1, n // 2] = L2[n // 2, n // 2 - 1] = 0.0
    L2[n // 2 - 1, n // 2 - 1] -= 1; L2[n // 2, n // 2] -= 1
    CASES[f"L_two_rigid_{n}"] = {"K": 3.0 * L2, "G": D}
    CASES[f"L_two_rigid_sing_{n}"] = {"K": 3.0 * L2, "G": Dz}
