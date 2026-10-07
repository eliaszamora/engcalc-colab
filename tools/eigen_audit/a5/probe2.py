"""Non-symmetric pencils with ill-conditioned G (no polish) and condensation with ill-conditioned K'bb."""
import numpy as np
from lib import sheet, ref, report, judge

rng = np.random.default_rng(5)
bad = 0
total = 0
for trial in range(60):
    n = int(rng.integers(4, 10))
    cg = 10.0 ** rng.uniform(4, 10)
    U, _, Vt = np.linalg.svd(rng.standard_normal((n, n)))
    s = np.logspace(0, -np.log10(cg), n)
    G = U @ np.diag(s) @ Vt  # nonsym G, cond cg
    lam = np.sort(rng.uniform(1, 10, n))
    W = rng.standard_normal((n, n)) + 3 * np.eye(n)
    K = G @ W @ np.diag(lam) @ np.linalg.inv(W)
    # K now nonsym with real spectrum lam (as rounded)
    got, t = sheet(K, G, "", "")
    r = ref(K, G)
    j = judge(r, got)
    total += 1
    if j.startswith("WRONG") or j.startswith("COUNT") or j.startswith("ref"):
        bad += 1
        report(f"ns_illG_{trial}_n{n}_cg{cg:.1e}", r, got, t)
    else:
        print(f"ns_illG_{trial}_n{n}_cg{cg:.1e} {j}")
print("bad", bad, "of", total)
