import hashlib
import os
import sys
import time

import numpy as np

S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S + "/../a5")
from lib import sheet  # noqa: E402
from frames import build, units_for, convert  # noqa: E402

E = 2.0e8


def frame(bays, storeys, P=600.0):
    nc = bays + 1
    nodes = [(c * 6.0, l * 3.5) for l in range(storeys + 1) for c in range(nc)]
    elems = []
    for l in range(storeys):
        for c in range(nc):
            elems.append((l * nc + c, (l + 1) * nc + c, E, 0.011, 2.2e-4, P * (storeys - l) / storeys, 0.09))
    for l in range(1, storeys + 1):
        for c in range(bays):
            elems.append((l * nc + c, l * nc + c + 1, E, 0.008, 4e-4, 0.0, 0.06))
    return build(nodes, elems, list(range(3 * nc)), consistent=True)


K, G, M, free = frame(2, 6)
print("size", K.shape)
for name, A, B, ku, gu in (("vib", K, M * 1000, "kN", "kg"), ("buck", K, G, "kN", "kN"), ("inv", -G, K, "kN", "kN")):
    for r in range(3):
        got, t = sheet(convert(A, free, ku).tolist(), convert(B, free, gu).tolist(), units_for(free, ku), units_for(free, gu))
        h = hashlib.md5(repr(got).encode()).hexdigest()[:8]
        print(name, r, f"{t:.2f}s", h, got[:3] if not isinstance(got, str) else got[:60])
