# engcalc-colab

`engcalc-colab` is a compact engineering-calculation layer for Google Colab and Jupyter. It combines a restricted SymPy-backed symbolic language with a separate Pint-backed numerical context, so the same `%%eng` workflow can preserve formulas, evaluate them with physical units, and plot unit-aware engineering functions without redefining the problem in Python.

Current version: **0.6.1**.

## Install in Google Colab

```python
%pip install -q --upgrade --no-cache-dir git+https://github.com/eliaszamora/engcalc-colab.git
%load_ext engcalc_colab
```

If the extension is already loaded after an update, use:

```python
%reload_ext engcalc_colab
```

## v0.6.1 visual polish

v0.6.1 is a presentation-focused release. It does not change the structural mathematics, the 201-point sampling grid, unit handling, signed-envelope rules, magnitude-envelope rules, or the convention of **positive structural moment downward**.

The release refines two parts of the notebook output:

- **MathJax calculations** remain the single mathematical renderer. Formula, numerical-substitution and final-result stages are kept semantically separate and may wrap over several rows when required by the visual-width budget. Long additive expressions wrap at complete top-level terms rather than splitting mathematical fragments. Engineering identifiers such as `Sigma_F_y` retain their intended `\Sigma` rendering.
- **Characteristic plot values** are attached directly to the sampled points they describe. Multi-series plots, signed envelopes and magnitude envelopes no longer use a separate characteristic-value panel. Callouts show the x coordinate and response ordinate, preserve the legend, and are placed with axes-, legend-, curve- and callout-aware collision avoidance.

For example:

```text
%%eng

M_D(x) = q_D*x*(L-x)/2
M_L(x) = q_L*x*(L-x)/2

q_D := 8*kN/m
q_L := 5*kN/m
L := 6*m

plot(M_D(x), M_L(x), x, 0, L)
envelope(M_D(x), M_L(x), x, 0, L)
```

The curves and envelope are evaluated exactly as before; v0.6.1 changes how their characteristic values are presented.

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

Supported unit aliases include:

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

## Adaptive MathJax rendering

MathJax is the single mathematical renderer for symbolic and numerical calculations. This keeps font metrics, fraction sizing, subscripts and equation scale consistent throughout one engineering memory.

Numerical evaluations keep the calculation stages separate:

```text
formula
= numerical substitution
= final result
```

Formula and substitution stages use adaptive top-level term packing. EngCalc estimates the visual complexity of complete `+` / `-` terms and keeps adding whole terms to the current row while the row stays within a conservative visual budget. If the next term would exceed the budget, that term starts a continuation row.

A short expression such as:

```text
A + B - C + D
```

remains on one row when it fits. A longer engineering expression can instead be arranged as:

```text
[ long term 1 ] + [ long term 2 ]
- [ long term 3 ]
```

The final numerical result always starts its own row. The visual budget is a deterministic heuristic rather than a browser-pixel measurement.

## Global numerical presentation settings

Use `%eng_config` to control numerical formatting for later `%%eng` output in the current notebook session:

```python
%eng_config precision=3 zero_tolerance=1e-10
```

Defaults:

```text
precision=2
zero_tolerance=1e-10
```

Run `%eng_config` with no arguments to inspect the active settings.

`precision` accepts integers from 0 through 10 and applies to numerical assignments, substituted values, final `numeric(...)` results, and evaluated coefficients of partial numerical functions.

`zero_tolerance` is presentation-only. Values whose displayed magnitude is below the threshold render as zero, while the stored Pint quantity remains unchanged.

`%eng_reset` clears symbolic and numerical calculation state but does not change the active render configuration.

## Target-unit conversion

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

Target-unit expressions may contain products, divisions and powers:

```text
kN*m
N*mm
mm^4
mm/kN
```

The conversion applies to the final result. Formula and numerical-substitution stages preserve the units in which the input data were defined. Pint checks dimensional compatibility and rejects incompatible targets.

Target-unit conversion currently requires a fully numerical result. A partial function with a free independent variable should use `numeric(V(x))` without a target unit.

## Evaluated partial numerical functions

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

The numerical workflow also supports mixed engineering units:

```text
Delta_B0 = integral(M_0(x)*M_1(x)/(E*I), x, 0, L)
f_11 = integral(M_1(x)^2/(E*I), x, 0, L)

E := 200*GPa
I := 8.5e8*mm^4

numeric(Delta_B0)
numeric(f_11)
```

## Native plotting inside `%%eng`

The restricted unit-aware plotting command is:

```text
plot(expression, variable, start, end)
```

The primary workflow is to define engineering functions and numerical data once and plot them in the same cell:

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

Each plot samples exactly 201 positions including both endpoints. The plotting variable is locally overridden during sampling, so a previously stored value such as `x := 2.5*m` is neither used to collapse the plot nor modified by plotting.

Plot bounds are unit-aware. The common structural form:

```text
plot(M(x), x, 0, L)
```

works when `L := 4*m`: the exact dimensionless zero is promoted to the compatible dimensional unit of `L`. Incompatible bounds are rejected.

The first evaluated ordinate establishes the y-axis unit and later samples are converted to that common unit. Axes are labeled automatically, for example:

```text
x [m]
M(x) [tonf·m]
```

Structural moment diagrams use **positive moment downward**.

### Multi-series plotting

Several dimensionally compatible functions may share one axis:

```text
plot(M_D(x), M_L(x), x, 0, L)
```

One function may also be swept over several numerical values of one parameter:

```text
plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m, 15*kN/m])
```

The sweep accepts exactly one keyword parameter with a non-empty list of complete numerical EngCalc expressions. `[5, 10, 15]*kN/m` is not supported. A sweep and multiple plotted expressions cannot be combined in the same call.

Sweep values are local overrides and do not mutate stored numerical state. All series on a shared y-axis must have compatible dimensions, and a multi-expression comparison cannot mix moment-classified and non-moment-classified responses.

Presentation in v0.6.1:

- a single series uses a line, translucent fill, endpoint/extrema markers and maximum/minimum point callouts;
- multiple series use clean lines without overlapping area fills, an automatic legend, restrained extrema markers and point-attached maximum/minimum callouts for each curve;
- each callout reports both x and ordinate, and the placement engine avoids the axes boundary, legend and already occupied callout regions before optimizing curve clearance.

One `plot(...)` statement creates exactly one Matplotlib figure in source order between surrounding MathJax calculation groups.

## Sampled engineering envelopes

`envelope(...)` reuses the same symbolic functions, numerical state, 201-point sampling grid, unit normalization and structural sign convention as `plot(...)`.

Several compatible responses may be reduced to one upper and one lower signed envelope:

```text
%%eng

M_A(x) = q_A*x*(L-x)/2
M_B(x) = -0.5*q_B*x*(L-x)/2

q_A := 8*kN/m
q_B := 10*kN/m
L := 6*m

envelope(M_A(x), M_B(x), x, 0, L)
```

The final three positional arguments are `variable, start, end`. Every earlier positional argument is a source response. A non-sweep envelope requires at least two response series.

One expression may also be enveloped over a restricted one-parameter sweep:

```text
%%eng

M(x) = q*x*(L-x)/2
L := 6*m

envelope(
    M(x),
    x,
    0,
    L,
    q=[-10*kN/m, 5*kN/m, 15*kN/m]
)
```

At each of the 201 shared sample positions, EngCalc computes the **signed algebraic maximum and signed algebraic minimum** across source series. A negative response can govern the lower envelope while a positive response governs the upper envelope. The governing source-series index is retained internally.

All source responses must be dimensionally compatible. Compatible values are normalized to a common unit before comparison. Mixed moment/non-moment series and incompatible dimensions such as shear versus moment are rejected.

The envelope figure:

- shows original source responses as faint context curves;
- emphasizes the upper and lower envelope boundaries;
- lightly fills the region between signed envelope boundaries;
- keeps the `y = 0` reference visible;
- places the global maximum and minimum directly at their governing sampled points with x/ordinate callouts;
- keeps positive moment downward for moment envelopes.

## Absolute-value / magnitude envelopes

`abs(...)` is a safe, composable symbolic/numerical operation. Applying it to every source of an envelope requests a nonnegative magnitude-demand envelope:

```text
%%eng

V_constr(x) = R_constr - q_constr*x
V_uso(x) = R_uso + q_uso*x

R_constr := 6*kN
q_constr := 4*kN/m
R_uso := -9*kN
q_uso := 1*kN/m
L := 2*m

envelope(abs(V_constr(x)), abs(V_uso(x)), x, 0, L)
```

At each sample EngCalc compares absolute magnitudes and keeps the maximum-magnitude demand. Original signed source curves remain available as faint context, so a negative response can govern magnitude without losing its original sign internally.

The same mode works with the restricted parameter sweep:

```text
%%eng

V(x) = q*(L/2-x)
L := 4*m

envelope(
    abs(V(x)),
    x,
    0,
    L,
    q=[2*tonf/m, 3*tonf/m, 4*tonf/m]
)
```

Every source in one envelope must use the same comparison mode. Mixing `abs(V_A(x))` with signed `V_B(x)` in the same envelope is rejected. There is no separate `abs_envelope(...)` alias.

Magnitude-envelope figures emphasize one `|response|_max` boundary, fill from zero to that boundary, retain signed source curves as faint context and attach one callout to the global maximum-magnitude point.

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

The result and plot calls reuse the same symbolic functions and numerical data; no duplicate Python definitions are required.

## Complete command reference

### Notebook magics

- `%%eng` — evaluate a whole EngCalc cell.
- `%eng_reset` — clear both symbolic and numerical EngCalc state.
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

### Plotting and envelopes

- `plot(expression, variable, start, end)` — create one unit-aware Matplotlib figure using 201 samples including both endpoints.
- `plot(expr1, expr2, ..., variable, start, end)` — overlay several dimensionally compatible expressions on one shared axis.
- `plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])` — plot one expression for several local values of one parameter.
- `envelope(expr1, expr2, ..., variable, start, end)` — compute and render signed pointwise upper/lower envelopes.
- `envelope(M(x), x, 0, L, q=[5*kN/m, 10*kN/m])` — compute an envelope from one expression over one local parameter sweep.
- `envelope(abs(V_A(x)), abs(V_B(x)), x, 0, L)` — compute a nonnegative maximum-magnitude envelope while retaining signed source context.
- the final three positional arguments are always `variable, start, end`.
- a parameter sweep accepts one keyword with a non-empty list of complete numerical expressions.
- sweeps do not persist or overwrite the swept parameter's stored numerical value.
- the plotting variable is locally overridden for sampling and any stored numeric value for that name is preserved.
- all y series on one shared axis must have compatible dimensions.
- all-moment plots and envelopes retain positive moment downward.
- plotting and envelopes are standalone statements; assigning `A = plot(...)` or `A = envelope(...)` is rejected.
- arbitrary plot styling/Matplotlib keyword arguments are not exposed.

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
- `abs(expr)` — symbolic/numerical absolute value; composes with plotting and magnitude envelopes.

`solve(...)` currently requires exactly one solution; zero or multiple solutions produce a concise EngCalc error.

## Engineering presentation syntax

- `Sigma_F_y = ...` — renders the `Sigma_` prefix as engineering equilibrium notation such as `\Sigma F_y`.
- `# text` — invisible comment.
- `## text` — visible section heading.
- `### text` — visible subsection heading.
- blank line — adds a larger visual separation inside the current equation group.

Calculation rows use compact three-column MathJax blocks. Consecutive source results use 4 pt spacing; a source blank line uses 8 pt. Complete and partial numerical evaluations use adaptive MathJax row packing.

For commutative products, the renderer applies engineering-oriented factor order without changing the mathematics.

## Google Colab side-by-side layout

Put this Colab directive immediately below `%%eng` when desired:

```text
%%eng
#@title { vertical-output: true }
```

EngCalc ignores the directive because it begins with a single `#`. Numerical equations continue to use the same MathJax renderer as symbolic equations, and native plots appear in source order between equation groups.

## Safety

`%%eng` uses restricted AST evaluators for symbolic expressions, numerical expressions and target-unit expressions. `plot(...)` and `envelope(...)` are restricted EngCalc operations: they do not expose arbitrary Matplotlib functions, callbacks, filenames or Python objects. Raw cell text is never passed to unrestricted Python `eval` or `exec`.

## Current limitations

v0.6.1 intentionally does not yet provide:

- subplots or multiple axes in one `plot(...)` or `envelope(...)` statement;
- arbitrary plot styling/options from EngCalc syntax;
- labeled dictionary cases such as named load combinations;
- multi-parameter/cartesian sweeps;
- dual y-axes for quantities with different dimensions;
- explicit plot/envelope x/y target-unit conversion;
- `piecewise`/discontinuous-function plotting and jump markers;
- automatic scientific-notation policy for very large/small displayed values;
- target-unit conversion of partially evaluated functions with a free independent variable;
- automatic compact coefficient evaluation for non-polynomial partial functions;
- exact browser-pixel-aware MathJax line wrapping;
- wrapping inside a single indivisible top-level mathematical term wider than the target budget;
- general keyword arguments or general list/dictionary syntax outside the restricted plot/envelope sweep slot;
- arrays/tables or dedicated matrix syntax;
- arbitrary Python execution or arbitrary library functions;
- multi-solution `solve(...)`;
- full LaTeX parsing.

## Version notes

- **0.6.1** — adaptive MathJax semantic-stage polish; point-attached, collision-aware characteristic callouts for multi-series plots and envelopes; no numerical-method changes.
- **0.6.0** — `abs(...)` and magnitude envelopes.
- **0.5.0** — sampled signed engineering envelopes.
- **0.4.0** — multi-series plotting and restricted one-parameter sweeps.
- **0.3.0** — native unit-aware plotting inside `%%eng`.
- **0.2.x** — numerical presentation settings, adaptive MathJax rendering, target-unit conversion and partial numerical functions.

## Development

```bash
python -m pip install -e '.[dev]'
pytest -q
```

Version: `0.6.1`.
