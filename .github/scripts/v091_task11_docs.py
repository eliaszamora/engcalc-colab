from pathlib import Path

path = Path("README.md")
text = path.read_text(encoding="utf-8")

marker = "Current version: **0.9.0**.\n"
if marker not in text:
    raise SystemExit("README current-version anchor not found")
if "## v0.9.1 Exact characteristic analysis" in text:
    raise SystemExit("Task 11 README section already present")

section = r'''

## v0.9.1 Exact characteristic analysis

The next EngCalc release adds exact-first engineering characteristic analysis with three standalone calls:

```text
extrema(response, variable, lower, upper)
roots(response, variable, lower, upper)
intersections(response_1, response_2, variable, lower, upper)
```

In 0.9.1 these calls are **standalone statements**: do not assign them to another symbol and do not nest them inside `numeric(...)`, `table(...)`, or another expression. Exact symbolic solutions are preferred. When exact solving is unresolved, EngCalc uses its deterministic numerical fallback and rendered locations use `≈` rather than `=`.

### 1. Beam-like moment extrema

```text
L := 6*m
q := 12*kN/m
M(x) = q*x*(L-x)/2

extrema(M(x), x, 0, L)
```

For this beam-like parabola, the authoritative maximum is obtained from the characteristic solver rather than from a plotting grid: `x = L/2 = 3 m`, with `M = 54 kN·m`.

### 2. Shear roots

```text
V(x) = q*(L/2-x)

roots(V(x), x, 0, L)
```

The zero-shear location is reported exactly at `x = L/2 = 3 m`. Closed-domain endpoints are included when they are roots.

### 3. Response-case intersections

```text
M2(x) = q*x*(L-x)/3

intersections(M(x), M2(x), x, 0, L)
```

Intersections solve the response difference while preserving the common response value and physical units. In this example the curves meet at `x = 0 m` and `x = 6 m`.

### 4. Piecewise jump is not a false root

```text
J(x) = piecewise(-1, x < 2, 1)

roots(J(x), x, 0, 4)
```

The sign changes across `x = 2`, but the function is never zero there. EngCalc therefore reports no root; it does not bracket across a Piecewise jump and invent a crossing.

### 5. Indexed matrix scalar analysis

```text
K(x) = [x + L, 0; 0, 2*x + L]

roots(K(x)[1,1] - 7*m, x, 0, L)
```

Characteristic analysis is scalar-only, so a whole matrix is rejected. An indexed scalar entry is valid; here the root is `x = 1 m`. Unit literals such as `7*m` are resolved through the same Pint unit registry during physical validation.

### 6. Approximate numerical fallback

```text
roots(cos(x) - x, x, 0, 1)
```

This equation has no elementary closed-form root. EngCalc's deterministic fallback validates the numerical solution near `0.7390851332`; the standalone renderer marks the location with `≈` to distinguish numerical provenance from an exact symbolic result.

Ordinary `plot(...)` series in 0.9.1 can already use exact global-extremum metadata independently of their 201-point drawing grid. Exact envelope crossovers and governing intervals remain intentionally deferred to **0.9.2**; `envelope(...)` keeps its existing sampled governing mathematics in 0.9.1.
'''

text = text.replace(marker, marker + section, 1)
path.write_text(text, encoding="utf-8")
