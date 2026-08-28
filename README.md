# engcalc-colab

`engcalc-colab` is a compact engineering-calculation layer for Google Colab and Jupyter. It combines a restricted SymPy-backed symbolic language with a separate Pint-backed numerical context, so the same `%%eng` workflow can preserve formulas and evaluate them later with physical units.

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

Supported unit aliases in v0.2.5:

- length: `mm`, `cm`, `m`
- force: `N`, `kN`, `kgf`, `tonf`
- pressure/stress: `Pa`, `kPa`, `MPa`, `GPa`
- other: `kg`, `s`, `rad`, `deg`

EngCalc defines:

\[
1\,\mathrm{tonf}=9.80665\,\mathrm{kN}.
\]

Units are interpreted only inside the numerical context. A name such as `m` remains available as a normal symbolic identifier in symbolic expressions.

Final numerical quantities are rendered with two decimal places in v0.2.5.

## v0.2.5 narrow numerical layout for split view

v0.2.5 changes the **display layout** of numerical evaluations so long engineering calculations remain readable when Google Colab shows code on the left and output on the right.

Earlier versions rendered a complete numerical chain on one mathematical line:

```text
M(x) = formula = full numerical substitution = result
```

For moments, deflections and other expressions with several additive terms, that line could become wider than the output pane and force horizontal scrolling.

`%%eng` now renders the same calculation as aligned vertical stages. A fully evaluated result follows this structure:

\[
\begin{aligned}
M(x) &= \text{symbolic formula}\\
     &= \text{first substituted term}\\
     &\quad + \text{second substituted term}\\
     &\quad - \text{third substituted term}\\
     &= \text{final quantity}.
\end{aligned}
\]

The breakpoints are mathematical rather than screen-width heuristics: each top-level additive term in a long numerical substitution gets its own continuation row. This keeps the presentation deterministic across notebook widths and avoids solving the problem by shrinking the font.

Short symbolic equations and numerical assignments remain compact. The extra vertical rows are used for `numeric(...)` and partial numerical function evaluations, where the formula → substitution → result chain would otherwise become excessively wide.

The standalone `render_result()` representation remains backward-compatible; the narrow layout is applied by the grouped renderer used by `%%eng`.

## v0.2.4 target-unit conversion

v0.2.4 added an optional target unit to fully numerical evaluations:

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

Target-unit expressions use the same engineering aliases and may contain products, divisions and powers, for example:

```text
kN*m
N*mm
mm^4
mm/kN
```

The conversion applies to the **final result**. The formula and numerical-substitution stages preserve the units in which the input data were defined. For example:

```text
M_A = q*L^2/8
q := 2.8*tonf/m
L := 4*m
numeric(M_A, kN*m)
```

renders the symbolic formula, substitutes `q` and `L` in their original `tonf/m` and `m` units, and finishes with approximately:

\[
M_A=54.92\,\mathrm{kN\,m}.
\]

The same syntax works for a user-defined function once its argument is numerically known:

```text
V(x) = 5*q*L/8 - q*x
q := 2.8*tonf/m
L := 4*m
x := 2*m

numeric(V(x), kN)
```

Pint checks dimensional compatibility. Asking for an incompatible target, such as converting a moment directly to `kN`, produces a concise EngCalc error instead of silently changing dimensions.

Target-unit conversion intentionally requires a **fully numerical result**. A partial function such as:

```text
numeric(V(x), kN)
```

with `x` still free is rejected. Use `numeric(V(x))` to keep the symbolic independent variable, or assign/evaluate the coordinate first and then request a target unit.

The original one-argument form `numeric(expr)` is unchanged.

## v0.2.3 evaluated partial numerical functions

When a user-defined function keeps its independent variable free, EngCalc evaluates every known polynomial coefficient with Pint instead of stopping after textual substitution.

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

The symbolic definition remains unchanged. Partial coefficient evaluation is limited to functions polynomial in their free argument; non-polynomial partial functions retain the substitution-only representation rather than being approximated.

Direct expressions remain strict: `numeric(q*x)` does not guess that `x` is an independent variable.

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
```

The last two calls keep `x` symbolic unless a numerical value has been assigned to `x`, while evaluating the known polynomial coefficients numerically.

## Complete command reference

### Notebook magics

- `%%eng` — evaluate a whole EngCalc cell.
- `%eng_reset` — clear both the symbolic and numerical EngCalc state.

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
- `numeric(V(x))` — partially evaluate a user-defined symbolic function if its argument is still free, including evaluation of known polynomial coefficients; fully evaluate it if the argument has a numerical value.
- `numeric(M(L))` — fully evaluate a user-defined symbolic function at another symbolic quantity whose numerical value is known.

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

Consecutive calculation rows are rendered in a three-column mathematical block. Consecutive source results use 4 pt spacing; a source blank line uses 8 pt. Internal stages of one numerical evaluation use compact 2 pt spacing.

For commutative products, the renderer applies engineering-oriented factor order without changing the mathematics.

## Google Colab side-by-side layout

Put this Colab directive immediately below `%%eng` when desired:

```text
%%eng
#@title { vertical-output: true }
```

EngCalc ignores the directive because it begins with a single `#`. In v0.2.5, long `numeric(...)` substitutions are also broken into vertical mathematical stages so this side-by-side mode does not require one extremely wide calculation row.

## Safety

`%%eng` uses restricted AST evaluators for symbolic expressions, numerical expressions and target-unit expressions. Raw cell text is never passed to unrestricted Python `eval` or `exec`. Attribute access, arbitrary Python calls, keyword arguments and unsupported syntax are rejected.

## Current limitations

v0.2.5 intentionally does not yet provide:

- configurable numerical precision or zero tolerance
- target-unit conversion of partially evaluated functions with a free independent variable
- automatic compact coefficient evaluation for non-polynomial partial functions
- keyword arguments
- arrays/tables or dedicated matrix syntax
- arbitrary Python execution or arbitrary library functions
- multi-solution `solve(...)`
- full LaTeX parsing

These are separate future milestones rather than hidden behavior in v0.2.5.

## Development

```bash
python -m pip install -e '.[dev]'
pytest -q
```

Version: `0.2.5`.
