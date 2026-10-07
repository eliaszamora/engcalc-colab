"""Crafted pencils: ill-conditioned G + stiff spring + clusters (polish twin attack)."""
import numpy as np
from lib import sheet, ref, report

rng = np.random.default_rng(1)
for cg in (1e-6, 1e-9, 1e-10):
    for spring in (0, 1e4, 1e8, 1e12):
        for cl in (1e-3, 1e-2, 0.1):
            n = 6
            Q, _ = np.linalg.qr(rng.standard_normal((n, n)))
            G = Q @ np.diag([1, 1.3, 0.7, 1.1, 0.9, cg]) @ Q.T
            G = (G + G.T) / 2
            K = np.diag([1.0, 1 + cl, 1 + 2 * cl, 2, 3, 4])
            K[5, 5] += spring
            K = (K + K.T) / 2
            got, t = sheet(K, G, "", "")
            report(f"illG{cg:g}_sp{spring:g}_cl{cl:g}", ref(K, G), got, t)
