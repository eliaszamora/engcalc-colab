# engcalc-colab

`engcalc-colab` is a compact engineering-calculation layer for Google Colab and Jupyter. It combines a restricted SymPy-backed symbolic language with a separate Pint-backed numerical context, so the same `%%eng` workflow can preserve formulas, evaluate them with physical units, and now plot unit-aware functions without redefining the problem in Python.

## Install in Google Colab

```python
%pip install -q --upgrade --no-cache-dir git+https://github.com/eliaszamora/engcalc-colab.git
%load_ext engcalc_colab
```

If the extension is already loaded after an update, use:

```python
%reload_ext engcalc_colab
```

## Symbolic + numerical workflow

Symbolic definitions use `=`. Numerical data use `:=`. The two contexts are intentionally separate: assigning a numerical value never overwrites the symbolic formula.

```text
%%eng

V_B = 3*q*L/8
V_A = 5*q*L/8
M_A = q*L^2/8

q := 2.8*tonf/m
L := 4*m

numeric(V_B)
numeric(V_A)
numeric(M_A)
```

The symbolic namespace still contains the original formulas, while `numeric(...)` evaluates them with the current numerical context and renders formula → numerical substitution → final quantity.

## Numerical context and units

Numeric assignments use:

```text
name := numeric_expression
```

Numerical values may reference earlier values:

```text
q := 2.8*tonf/m
L := 4*m
P := q*L
```

Supported unit aliases in v0.3.0:

- length: `mm`, `cm`, `m`
- force: `N`, `kN`, `kgf`, `tonf`
- pressure/stress: `Pa`, `kPa`, `MPa`, `GPa`
- other: `kg`, `s`, `rad`, `deg`

EngCalc defines:

\[
1\,\mathrm{tonf}=9.80665\,\mathrm{kN}.
\]

Units are interpreted only inside the numerical context. A name such as `m` remains available as a normal symbolic identifier in symbolic expressions.

Numerical quantities render with two decimal places by default. Global presentation settings can change that policy without altering stored values or symbolic formulas.

## v0.3.0 native plotting inside `%%eng`

v0.3.0 adds a restricted, unit-aware plotting command:

```text
plot(expression, variable, start, end)
```

The primary workflow is to define the engineering functions and numerical data once and plot them in the same EngCalc cell:

```text
%%eng

V(x) = 5*q*L/8 - q*x
M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2

q := 2.8*tonf/m
L := 4*m

numeric(V(x))
numeric(M(x))

plot(V(x), x, 0, L)
plot(M(x), x, 0, L)
```

`plot(...)` reuses the symbolic and numerical EngCalc state directly. No duplicate Python definitions of `q`, `L`, `V(x)` or `M(x)` are required.

Each call produces one Matplotlib figure and samples exactly 201 points, including both endpoints. The plotting variable is locally overridden during sampling, so an earlier value such as:

```text
x := 2.5*m
```

does not collapse `plot(M(x), x, 0, L)` to one point and is not modified by plotting.

Plot bounds are unit-aware. The common structural form:

```text
plot(M(x), x, 0, L)
```

works when `L := 4*m`: the exact dimensionless zero is promoted to the compatible dimensional unit of `L`. Incompatible bounds are rejected instead of silently converted.

The first evaluated ordinate establishes the y-axis unit and every later sample is converted to that same compatible unit. The default figure therefore labels axes automatically, for example:

```text
x [m]
M(x) [tonf·m]
```

Each figure contains the requested curve, a horizontal `y = 0` reference, automatic axis labels, the expression/function name as title, and `tight_layout()`. EngCalc deliberately does not impose a separate plot color/theme: the figure inherits the active Matplotlib `rcParams`.

`plot(...)` is a standalone output statement. It does not create an extra MathJax equation row. When a plot occurs between calculations, EngCalc preserves source order by flushing the preceding equation group, displaying the figure, and then continuing with subsequent equations.

The initial v0.3.0 plotting contract intentionally does **not** include multiple curves, keyword/style arguments, custom plot-unit conversion, fills, legends, extrema/root annotations, discontinuity handling, `piecewise`, image export, or arbitrary Matplotlib access. Those can be added later without changing the four-argument base syntax.

## v0.2.9 global numerical presentation settings

Use `%eng_config` to control numerical formatting for all later `%%eng` output in the current notebook session:

```python
%eng_config precision=3 zero_tolerance=1e-10
```

The defaults are:

```text
precision=2
zero_tolerance=1e-10
```

Run `%eng_config` with no arguments to inspect the active settings.

`precision` accepts integers from 0 through 10 and applies consistently to numerical assignments, substituted values, final `numeric(...)` results, and evaluated coefficients of partial numerical functions.

`zero_tolerance` is a **presentation-only cleanup threshold**. If the absolute magnitude of the quantity in its currently displayed unit is smaller than the threshold, EngCalc renders that magnitude as zero. The stored Pint quantity is not changed and subsequent calculations continue using the original numerical value.

For example:

```python
%eng_config precision=4 zero_tolerance=1e-8
```

can render a tiny numerical residue as `0.0000` while keeping the underlying value intact.

`%eng_reset` clears symbolic and numerical calculation state but does not change the active render configuration.

Scientific-notation policy is intentionally separate from this formatting feature.

## v0.2.8 adaptive MathJax wrapping for split view

v0.2.8 restored **MathJax as the single mathematical renderer** for symbolic and numerical calculations. This keeps the same font metrics, fraction sizing, subscripts and equation scale throughout one engineering memory.

Numerical evaluations keep the calculation stages separate:

```text
formula
= numerical substitution
= final result
```

The formula and substitution stages use adaptive top-level term packing. EngCalc estimates the visual complexity of each complete `+` / `-` term and keeps adding whole terms to the current row while the row stays within a conservative visual budget. If the next term would exceed the budget, that term starts a continuation row.

A short expression such as:

```text
A + B - C + D
```

remains on one row when its estimated width fits. A longer engineering substitution can instead be arranged as:

```text
[ long term 1 ] + [ long term 2 ]
- [ long term 3 ]
```

The final numerical result always starts its own row to preserve the formula → substitution → result hierarchy.

The visual budget is a deterministic heuristic, not a browser-pixel measurement. The MathJax-only approach favors typographic consistency and predictable engineering layout.

## v0.2.4 target-unit conversion

A fully numerical evaluation may request a compatible target unit:

```text
numeric(expression, target_unit)
```

Examples:

```text
numeric(M_A, kN*m)
numeric(V_A, kN)
numeric(Delta_B0, mm)
numeric(f_11, mm/kN)
```

Target-unit expressions use the same engineering aliases and may contain products, divisions and powers:

```text
kN*m
N*mm
mm^4
mm/kN
```

The conversion applies to the final result. The formula and numerical-substitution stages preserve the units in which the input data were defined.

Pint checks dimensional compatibility. An incompatible target produces a concise EngCalc error rather than silently changing dimensions.

Target-unit conversion currently requires a fully numerical result. A partial function with a free independent variable should use `numeric(V(x))` without a target unit.

## v0.2.3 evaluated partial numerical functions

When a user-defined function keeps its independent variable free, EngCalc evaluates known polynomial coefficients with Pint instead of stopping after textual substitution.

```text
V(x) = 5*q*L/8 - q*x
q := 2.8*tonf/m
L := 2*m

numeric(V(x))
```

produces a compact numerical function equivalent to:

\[
V(x)=3.50\,\mathrm{tonf}
-2.80\,\frac{\mathrm{tonf}}{\mathrm m}x.
\]

Likewise:

```text
M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2
numeric(M(x))
```

with the same data produces a function equivalent to:

\[
M(x)=
-1.40\,\mathrm{tonf\,m}
+3.50\,\mathrm{tonf}\,x
-1.40\,\frac{\mathrm{tonf}}{\mathrm m}x^2.
\]

The symbolic definition remains unchanged. Direct expressions remain strict: `numeric(q*x)` does not guess that `x` is an independent variable.

## Function evaluation and dimensional zeros

Fully evaluated user functions keep their engineering label in the rendered memory. Function evaluation is performed with Pint before an exact symbolic zero can erase dimensional information, so a boundary value such as `numeric(M(L))` remains a zero moment rather than a dimensionless zero.

The numerical workflow also supports mixed engineering units, for example:

```text
Delta_B0 = integral(M_0(x)*M_1(x)/(E*I), x, 0, L)
f_11 = integral(M_1(x)^2/(E*I), x, 0, L)

E := 200*GPa
I := 8.5e8*mm^4

numeric(Delta_B0)
numeric(f_11)
```

## Example — propped cantilever by the force method

```text
%%eng
#@title { vertical-output: true }

## Estado 0: cargas reales
### Reacciones de la estructura base

Sigma_F_y_0 = 0
V_A0 = q*L

Sigma_M_A_0 = 0
M_A0 = q*L^2/2

### Fuerzas internas

V_0(x) = V_A0 - q*x
M_0(x) = -M_A0 + V_A0*x - q*x^2/2

## Estado 1: carga unitaria en B
### Reacciones de la estructura base

Sigma_F_y_1 = 0
V_A1 = -1

Sigma_M_A_1 = 0
M_A1 = -L

### Fuerzas internas

V_1(x) = V_A1
M_1(x) = -M_A1 + V_A1*x

## Compatibilidad

Delta_B0 = integral(M_0(x)*M_1(x)/(E*I), x, 0, L)
f_11 = integral(M_1(x)^2/(E*I), x, 0, L)
Delta_B = Delta_B0 + V_B*f_11
V_B = solve(Delta_B = 0, V_B)

V_A = q*L - V_B
M_A = q*L^2/2 - V_B*L
V(x) = expand(V_0(x) + V_B*V_1(x))
M(x) = expand(M_0(x) + V_B*M_1(x))

## Datos numéricos

q := 2.8*tonf/m
L := 4*m
E := 200*GPa
I := 8.5e8*mm^4

## Resultados

numeric(Delta_B0, mm)
numeric(V_B, kN)
numeric(V_A, kN)
numeric(M_A, kN*m)

## Funciones con datos conocidos

numeric(V(x))
numeric(M(x))

## Diagramas

plot(V(x), x, 0, L)
plot(M(x), x, 0, L)
```

The last four calls reuse the same symbolic functions and numerical data: `numeric(...)` presents the functions and `plot(...)` samples them across the span without a second Python definition.

## Complete command reference

### Notebook magics

- `%%eng` — evaluate a whole EngCalc cell.
- `%eng_reset` — clear both the symbolic and numerical EngCalc state.
- `%eng_config precision=3 zero_tolerance=1e-10` — set global numerical presentation settings.
- `%eng_config` — show the active numerical presentation settings.

`%load_ext engcalc_colab` and `%reload_ext engcalc_colab` are IPython extension-management magics, not EngCalc expression commands.

### Symbolic definitions and expressions

- `A = expression` — scalar/symbolic assignment.
- `M(x) = expression` — single-argument symbolic function definition.
- `M(x)` — call a previously defined EngCalc function.
- standalone expressions are supported.
- identifiers are created symbolically on first use; no `symbols()` declaration is required.

### Numerical definitions and evaluation

- `q := 2.8*tonf/m` — associate a unit-aware numerical value with `q` without changing symbolic `q`.
- `P := q*L` — numerical values may reference earlier numerical values.
- `numeric(V_B)` — evaluate a named symbolic result with natural resulting units.
- `numeric(M_A, kN*m)` — evaluate a fully numerical result and convert its final quantity to the requested compatible unit.
- `numeric(q*L^2/8)` — evaluate a direct symbolic expression; every free symbol must have a numerical value.
- `numeric(V(x))` — partially evaluate a user-defined symbolic function if its argument is still free; fully evaluate it if the argument has a numerical value.
- `numeric(M(L))` — fully evaluate a user-defined symbolic function at another symbolic quantity whose numerical value is known.

### Plotting

- `plot(expression, variable, start, end)` — create one unit-aware Matplotlib figure using 201 samples including both endpoints.
- `plot(V(x), x, 0, L)` — plot a defined EngCalc function over a known span without redefining data in Python.
- the plotting variable is locally overridden for sampling and any stored numeric value for that name is preserved.
- plotting is a standalone statement; assigning `A = plot(...)` is rejected.
- keyword/style arguments are not supported in v0.3.0.

### Arithmetic syntax

- addition: `a + b`
- subtraction: `a - b`
- multiplication: `a*b`
- division: `a/b`
- powers: `a^2` or `a**2`
- unary signs: `+a`, `-a`
- parentheses: `( ... )`
- integer and decimal constants

### Symbolic operations

- `integral(expr, var, lower, upper)` — definite integral.
- `diff(expr, var)` — first derivative.
- `diff(expr, var, order)` — higher derivative.
- `solve(lhs = rhs, unknown)` — solve one equation for one unknown.
- `solve(expr, unknown)` — interpreted as `expr = 0`.
- `sum(expr, index, lower, upper)` — unevaluated indexed symbolic sum.
- `simplify(expr)` — simplify.
- `expand(expr)` — expand.
- `factor(expr)` — factor.
- `subs(expr, variable, value)` — symbolic substitution.
- `eq(lhs, rhs)` — explicit symbolic equality, mainly for advanced/internal use.

`solve(...)` currently requires exactly one solution; zero or multiple solutions produce a concise EngCalc error.

## Engineering presentation syntax

- `Sigma_F_y = ...` — renders the `Sigma_` prefix as engineering equilibrium notation such as `\Sigma F_y`.
- `# text` — invisible comment.
- `## text` — visible section heading.
- `### text` — visible subsection heading.
- blank line — adds a larger visual separation inside the current equation group.

All calculation rows use the compact three-column MathJax block. Consecutive source results use 4 pt spacing; a source blank line uses 8 pt. Complete and partial numerical evaluations use adaptive MathJax row packing.

For commutative products, the renderer applies engineering-oriented factor order without changing the mathematics.

## Google Colab side-by-side layout

Put this Colab directive immediately below `%%eng` when desired:

```text
%%eng
#@title { vertical-output: true }
```

EngCalc ignores the directive because it begins with a single `#`. Numerical equations continue to use the same MathJax renderer as symbolic equations, and native plots appear in source order between equation groups.

## Safety

`%%eng` uses restricted AST evaluators for symbolic expressions, numerical expressions and target-unit expressions. `plot(...)` is also a restricted EngCalc operation: it does not expose arbitrary Matplotlib functions, callbacks, filenames, Python objects, or keyword arguments. Raw cell text is never passed to unrestricted Python `eval` or `exec`.

## Current limitations

v0.3.0 intentionally does not yet provide:

- multiple curves in one native plot or subplots;
- plot styling/options from EngCalc syntax;
- explicit plot x/y target-unit conversion;
- automatic maxima, minima, roots or engineering annotations;
- `piecewise`/discontinuous-function plotting and jump markers;
- automatic scientific-notation policy for very large/small displayed values;
- target-unit conversion of partially evaluated functions with a free independent variable;
- automatic compact coefficient evaluation for non-polynomial partial functions;
- exact browser-pixel-aware MathJax line wrapping;
- wrapping inside a single indivisible top-level mathematical term wider than the target budget;
- keyword arguments;
- arrays/tables or dedicated matrix syntax;
- arbitrary Python execution or arbitrary library functions;
- multi-solution `solve(...)`;
- full LaTeX parsing.

These are separate future milestones rather than hidden behavior in v0.3.0.

## Development

```bash
python -m pip install -e '.[dev]'
pytest -q
```

Version: `0.3.0`.
