"""Twin attack: a stiff spring makes 1e-6*spread swallow every gap; does polish land on a neighbour?"""
import numpy as np
from lib6 import sheet, ref, report2

bad = 0
tot = 0
rng = np.random.default_rng(11)
for trial in range(120):
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
        K = K + asym * rng.standard_normal((n, n)) * np.sqrt(np.outer(np.diag(K), np.diag(K))) * 0
        K[0, 1] *= 1
        K[0, n - 1] += asym
    got, t = sheet(K, G, "", "")
    r = ref(K, G)
    j = report2(f"t{trial}_n{n}_cg{cg:.1e}_sp{spring:.1e}_as{asym:g}", r, got, t)
    tot += 1
    bad += j not in ("ok", "REFUSED")
print("bad", bad, "of", tot)
