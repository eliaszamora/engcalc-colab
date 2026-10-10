"""The third audit's column (stiff spring support), made slightly non-symmetric (one entry rounded)."""
import os
import re

import numpy as np
from lib import sheet, ref, report

src = open("col.eng", encoding="utf-8").read()


def parse(line):
    body = line.split(":=", 1)[1].strip()[1:-1]
    rows = [r.split(", ") for r in body.split("; ")]
    vals = np.array([[float(re.match(r"(.*)\[(.*)\]", c).group(1)) for c in r] for r in rows])
    units = [[re.match(r"(.*)\[(.*)\]", c).group(2) for c in r] for r in rows]
    return vals, units


K0, ku = parse(src.splitlines()[0])
G0, gu = parse(src.splitlines()[1])
sdof = 10
for spring in (1e6, 1e10, 1e14, 1e16, 1e20):
    for asym in (0.0, 1e-9, 1e-6, 1e-4):
        K = K0.copy()
        K[sdof, sdof] = 24000.000000000004 + spring
        K[1, 4] *= 1 + asym  # one off-diagonal entry differs from its mirror (typed rounded)
        got, t = sheet(K, G0, ku, gu)
        report(f"column_spring{spring:g}_asym{asym:g}", ref(K, G0, scale=1000.0), got, t, show=False)
