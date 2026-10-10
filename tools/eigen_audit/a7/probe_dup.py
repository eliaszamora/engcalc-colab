import os
import sys

import numpy as np

S = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("ENGROOT", S + "/../a6wt")
sys.path.insert(0, S + "/../a5")
from lib import lit  # noqa: E402
import engcalc_colab.matrix_numeric as mn  # noqa: E402

ns = {"__file__": S + "/../a6/cases8.py"}
exec(open(S + "/../a6/cases8.py", encoding="utf-8").read(), ns)
c = ns["CASES"][sys.argv[1] if len(sys.argv) > 1 else "portal_vib_sp1e+20_kN"]
K, G = np.array(c["K"], float), np.array(c["G"], float)
open(S + "/dup.eng", "w").write(f"K := {lit(K, c['ku'])}\nM := {lit(G, c['gu'])}\nl := eigenvals(K, M)\n")

orig = mn._polished
log = []


def spy(value, *a, **k):
    r = orig(value, *a, **k)
    log.append((value, r))
    return r


mn._polished = spy
print(mn._pencil_values(K * float(sys.argv[2]) if len(sys.argv) > 2 else K, G))
for v, r in log[:10]:
    print("%.10g -> %.10g %s" % (v, r[0], r[1]))
