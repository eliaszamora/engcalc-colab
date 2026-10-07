"""python gen.py nspan spring > sheet.eng : pinned continuous column, supports as springs, units by DOF."""
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])
from beams import beam  # noqa: E402

nspan = int(sys.argv[1])
spring = float(sys.argv[2])
EI = float(sys.argv[3]) if len(sys.argv) > 3 else 2e4
K, G = beam(nspan, spring=0.0, EI=EI)
size = len(K)


def unit(i, j):
    a, b = i % 2, j % 2
    return {0: "kN/m", 1: "kN", 2: "kN*m"}[a + b]


def lit(M, extra=None):
    rows = []
    for i in range(size):
        cells = []
        for j in range(size):
            c = f"{M[i][j]!r}[{unit(i, j)}]"
            if extra and i == j and i % 2 == 0:
                c += " + k_s"
            cells.append(c)
        rows.append(", ".join(cells))
    return "[" + "; ".join(rows) + "]"


print(f"k_s := {spring!r}[kN/m]")
print("K := " + lit(K.tolist(), True))
print("G := " + lit(G.tolist()))
print("l := eigenvals(K, G)")
