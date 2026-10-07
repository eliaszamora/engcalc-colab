"""Symmetric pencils, singular G (massless dofs), ill-conditioned K'bb, clustered low modes, wide spectrum."""
import sys
import numpy as np
from lib import sheet, ref, report, judge

rng = np.random.default_rng(int(sys.argv[1]) if len(sys.argv) > 1 else 11)
bad = 0
N = int(sys.argv[2]) if len(sys.argv) > 2 else 40
for trial in range(N):
    n = int(rng.integers(4, 9))   # massive dofs
    m = int(rng.integers(1, 4))   # massless dofs
    gap = 10.0 ** rng.uniform(-6, -2)
    top = 10.0 ** rng.uniform(2, 9)
    kbb_cond = 10.0 ** rng.uniform(0, 11)
    # condensed target K* with clustered spectrum over G = Mdiag
    Q, _ = np.linalg.qr(rng.standard_normal((n, n)))
    lam = np.concatenate([[1.0, 1 + gap, 1 + 2 * gap], np.logspace(0.3, np.log10(top), n - 3)])
    Mm = np.diag(rng.uniform(0.5, 2, n))
    Lm = np.sqrt(Mm)
    Kstar = Lm @ Q @ np.diag(lam) @ Q.T @ Lm
    # massless block Kbb with given condition, coupling Kab; Kaa = K* + Kab Kbb^-1 Kba
    Qb, _ = np.linalg.qr(rng.standard_normal((m, m)))
    Kbb = Qb @ np.diag(np.logspace(0, -np.log10(kbb_cond), m)) @ Qb.T * top
    Kab = rng.standard_normal((n, m)) * top * 1e-3
    Kaa = Kstar + Kab @ np.linalg.solve(Kbb, Kab.T)
    K = np.block([[Kaa, Kab], [Kab.T, Kbb]])
    K = (K + K.T) / 2
    G = np.zeros((n + m, n + m)); G[:n, :n] = Mm
    perm = rng.permutation(n + m)
    K = K[np.ix_(perm, perm)]; G = G[np.ix_(perm, perm)]
    got, t = sheet(K, G, "", "")
    r = ref(K, G, dps=80)
    j = judge(r, got)
    name = f"t{trial}_n{n}_m{m}_gap{gap:.1e}_top{top:.1e}_kbb{kbb_cond:.1e}"
    if j not in ("ok", "REFUSED"):
        bad += 1
        report(name, r, got, t)
        np.save(f"bad5_{sys.argv[1] if len(sys.argv) > 1 else 11}_{trial}.npy", np.stack([K, G]))
    else:
        print(name, j, flush=True)
print("bad", bad)
