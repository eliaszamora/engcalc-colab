from pathlib import Path


path = Path("README.md")
text = path.read_text(encoding="utf-8")
anchor = "## v0.7.1 multi-argument functions and generalized partial evaluation\n"
if text.count(anchor) != 1:
    raise SystemExit(f"expected one README anchor, found {text.count(anchor)}")

section = r'''## v0.7.2 engineering tables

v0.7.2 adds native pointwise engineering tables to the same restricted, unit-aware `%%eng` workflow used for calculations and plots. The normal form uses automatic discretization: give the response, independent variable, start, end, and number of points. Both endpoints are included.

```text
%%eng

M(x) = q*x*(L-x)/2
q := 4*kN/m
L := 5*m

table(M(x), x, 0, L, 21)
```

When `L` already carries a length unit, the exact zero in `0, L` inherits the compatible unit automatically. You therefore do not need to write `0*m`. The example above evaluates 21 uniformly spaced positions from `0 m` through `5 m`.

Several dimensionally compatible responses may share one table and remain in source order:

```text
table(M_D(x), M_L(x), M_U(x), x, 0, L, 21)
```

When particular evaluation positions matter more than uniform discretization, declare their unit once:

```text
table(M(x), x, [0, 1, 1.5, 2], m)
```

Fully explicit compatible quantities remain available when individual points use different units:

```text
table(M(x), x, [0*m, 50*cm, 1*m])
```

Explicit points are normalized to one compatible point unit. Dimensionless tables are also supported, and uniform ranges may be descending, for example `table(V(x), x, L, 0, 21)`.

Inside `%%eng`, tables render as native HTML in source order alongside MathJax equations, headings, and existing plots. Units appear once in the table headers rather than in every cell, and the active `%eng_config` precision and zero tolerance are respected. EngCalc does not add pandas as a runtime dependency for this feature.

General Python list literals remain restricted: list syntax is accepted only in the approved table-point context and the existing plot/envelope sweep contexts. Export/download APIs and Cartesian multi-parameter table sweeps are outside the 0.7.2 scope.

'''

path.write_text(text.replace(anchor, section + anchor, 1), encoding="utf-8")
