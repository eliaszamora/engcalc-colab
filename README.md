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

For a folder uploaded directly to Colab:

```python
%pip install -q /content/engcalc-colab
%load_ext engcalc_colab
```

## Symbolic + numerical workflow

Symbolic definitions use `=`. Numerical data use `:=`. The two contexts are intentionally separate: assigning a numerical value never overwrites the symbolic formula.

```text
%%eng

## Reacciones simbólicas

V_B = 3*q*L/8
V_A = 5*q*L/8
M_A = q*L^2/8

## Datos numéricos

q := 2.8*tonf/m
L := 4*m

## Resultados numéricos

numeric(V_B)
numeric(V_A)
numeric(M_A)
```

The symbolic namespace still contains:

\[
V_B=\frac{3qL}{8},\qquad
V_A=\frac{5qL}{8},\qquad
M_A=\frac{qL^2}{8}.
\]

The numerical context contains the independent data `q = 2.8 tonf/m` and `L = 4 m`. `numeric(...)` evaluates the existing symbolic expressions and renders the calculation as formula → numerical substitution → final quantity. For the example above:

\[
V_B=4.20\,\mathrm{tonf},\qquad
V_A=7.00\,\mathrm{tonf},\qquad
M_A=5.60\,\mathrm{tonf\,m}.
\]

Because the contexts are separate, this is valid:

```text
q := 3.5*tonf/m
numeric(M_A)
```

The value changes while the symbolic definition `M_A = q*L^2/8` remains unchanged.

## Numerical context and units

Numeric assignments use:

```text
name := numeric_expression
```

A numeric expression may reference previously assigned numerical values and the supported unit aliases. Example:

```text
q := 2.8*tonf/m
L := 4*m
P := q*L
```

Supported unit aliases in v0.2.3:

- length: `mm`, `cm`, `m`
- force: `N`, `kN`, `kgf`, `tonf`
- pressure/stress: `Pa`, `kPa`, `MPa`, `GPa`
- other: `kg`, `s`, `rad`, `deg`

EngCalc defines:

\[
1\,\mathrm{tonf}=9.80665\,\mathrm{kN}.
\]

Units are interpreted only inside the numerical context. A name such as `m` remains available as a normal symbolic identifier in symbolic expressions.

For ordinary scalar expressions, `numeric(expr)` requires numerical values for every free symbol. Missing values produce a concise EngCalc error instead of a raw Pint traceback.

Final numerical quantities are rendered with two decimal places in v0.2.3.

## v0.2.3 evaluated partial numerical functions

v0.2.3 extends the partial-function workflow introduced in v0.2.2. When a user-defined function keeps its independent variable free, EngCalc now evaluates every known polynomial coefficient with Pint instead of stopping after textual substitution.

For example:

```text
V(x) = 5*q*L/8 - q*x

q := 2.8*tonf/m
L := 2*m

numeric(V(x))
```

The output follows the complete engineering-memory chain:

\[
V(x)=\frac{5qL}{8}-qx
\]

\[
=\frac{5(2.80\,\mathrm{tonf/m})(2.00\,\mathrm m)}{8}
 -(2.80\,\mathrm{tonf/m})x
\]

\[
=3.50\,\mathrm{tonf}
 -2.80\,\frac{\mathrm{tonf}}{\mathrm m}x.
\]

The same mechanism evaluates each coefficient of higher-order polynomial functions independently. For example,

```text
M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2
numeric(M(x))
```

with the same `q` and `L` produces a compact function equivalent to:

\[
M(x)=
-1.40\,\mathrm{tonf\,m}
+3.50\,\mathrm{tonf}\,x
-1.40\,\frac{\mathrm{tonf}}{\mathrm m}x^2.
\]

The symbolic definition remains unchanged. Only the numerical presentation is evaluated.

Partial coefficient evaluation is intentionally limited to functions that are polynomial in their free argument. If a partial function is not polynomial in that argument, EngCalc keeps the v0.2.2 substitution-only representation rather than failing or inventing an approximation.

This relaxation is still limited to user-defined function calls. EngCalc does **not** guess a free variable in an arbitrary direct expression:

```text
q := 2.8*tonf/m
numeric(q*x)
```

still requires a numerical value for `x`.

If the function argument does have a numerical value, EngCalc keeps the existing full-evaluation behavior:

```text
V(x) = 5*q*L/8 - q*x
q := 2.8*tonf/m
L := 2*m
x := 1*m

numeric(V(x))
```

Similarly, `numeric(M(L))` fully evaluates the function when `L` has a numerical value.

All non-argument symbols of a partially evaluated function must still have numerical values. For example, `numeric(V(x))` will report a missing `q` if `L` is known but `q` is not.

## v0.2.1 validation and function-evaluation polish

v0.2.1 validated the symbolic-to-numerical workflow against a complete force-method beam calculation using mixed engineering units (`tonf/m`, `m`, `GPa`, `mm^4`). It also improved numerical evaluation of user-defined symbolic functions.

Function calls keep their engineering label in the rendered memory:

```text
V(x) = 5*q*L/8 - q*x
M(x) = -q*L^2/8 + 5*q*L*x/8 - q*x^2/2

q := 2.8*tonf/m
L := 4*m
x := 2.5*m

numeric(V(x))
numeric(M(x))
numeric(M(L))
```

The left side remains `V(x)`, `M(x)` or `M(L)` rather than being replaced by the expanded expression. Function evaluation is performed with Pint before an exact symbolic zero can erase dimensional information, so a boundary value such as `numeric(M(L))` remains a zero **moment** rather than a dimensionless zero.

The validation case also covers displacement and flexibility quantities such as:

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

numeric(Delta_B0)
numeric(f_11)
numeric(V_B)
numeric(V_A)
numeric(M_A)

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
- `numeric(V_B)` — evaluate a named symbolic result with the current numerical context.
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

Consecutive calculation rows are rendered in a three-column mathematical block: left expressions are left-aligned, equal signs share one centered vertical column, and right expressions are left-aligned. Consecutive rows use 4 pt spacing; a source blank line uses 8 pt.

For commutative products, the renderer applies engineering-oriented factor order without changing the mathematics: numeric coefficient first, then lowercase-leading symbols, then uppercase-leading symbols. Examples include:

\[
M_A=\frac{qL^2}{2},\qquad
R_B=\frac{3qL}{8},\qquad
D=\frac{qL^4}{8EI}.
\]

## Google Colab side-by-side layout

Google Colab can place code on the left and output on the right for an individual cell. Put this Colab directive immediately below `%%eng`:

```text
%%eng
#@title { vertical-output: true }
```

EngCalc ignores the directive because it begins with a single `#`.

## Safety

`%%eng` uses restricted AST evaluators for both symbolic and numerical expressions. Raw cell text is never passed to unrestricted Python `eval` or `exec`. Attribute access, arbitrary Python calls, keyword arguments and unsupported syntax are rejected. Visible heading text is HTML-escaped before display.

## Current limitations

v0.2.3 intentionally does not yet provide:

- target-unit conversion in `numeric(...)`
- configurable numerical precision
- automatic compact coefficient evaluation for non-polynomial partial functions
- keyword arguments
- arrays/tables or dedicated matrix syntax
- arbitrary Python execution or arbitrary library functions
- multi-solution `solve(...)`
- full LaTeX parsing

These are separate future milestones rather than hidden behavior in v0.2.3.

## Development

```bash
python -m pip install -e '.[dev]'
pytest -q
```

Version: `0.2.3`.
