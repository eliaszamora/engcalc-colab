"""Minimal non-symmetric pencils with a penalty spring."""
import numpy as np
from lib import sheet, ref, report

for spring in (1e12, 1e16, 1e20):
    for asym in (0.0, 1e-6, 1e-3):
        K = np.array([[spring + 2.0, -1.0, 0.0], [-1.0, 2.0, -1.0], [0.0, -1.0 * (1 + asym), 1.0]]) * 1000
        G = np.diag([1.0, 1.0, 1.0])
        got, t = sheet(K, G, "kN/m", "kN/m")
        report(f"chain3_spring{spring:g}_asym{asym:g}", ref(K, G), got, t, show=True)
