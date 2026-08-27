# engcalc-colab

`engcalc-colab` is a compact symbolic-calculation layer for Google Colab and Jupyter. You write engineering mathematics with `%%eng`; SymPy remains hidden behind the interface.

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

## Google Colab side-by-side layout

Google Colab can place the code on the left and the output on the right for an individual cell. Put this Colab directive immediately below `%%eng`:

```text
%%eng
#@title { vertical-output: true }
```

The directive is cell-specific. Add it to each cell where you want the side-by-side layout, or duplicate a cell that already contains it. `engcalc-colab` ignores the line because it is a single-`#` comment.

## Example — propped cantilever by the force method

```text
%%eng
#@title { vertical-output: true }

M_0 = -q/2*(L-x)^2
m_B = L-x

Delta_B = integral(M_0*m_B/(E*I), x, 0, L)
f_BB = integral(m_B^2/(E*I), x, 0, L)

R_B = solve(Delta_B + R_B*f_BB = 0, R_B)
```

Expected symbolic results:

\[
\Delta_B=-\frac{qL^4}{8EI},\qquad
f_{BB}=\frac{L^3}{3EI},\qquad
R_B=\frac{3qL}{8}.
\]

The same `%%eng` cell can be executed repeatedly. Variables used as the unknown in `solve(...)` remain symbolic during the solve even if that name already has a previous result in the notebook state.

You do not write `symbols()`, `Eq()`, `sp.integrate()`, `sp.solve()[0]`, `display()`, or SymPy printer boilerplate.

## v0.1 operations

- `A = expression`
- `M(x) = expression`
- powers with `^`
- automatic symbolic identifiers
- invisible comments beginning with a single `#`
- visible headings with `##` and `###`
- `integral(expr, var, lower, upper)`
- `diff(expr, var)` and `diff(expr, var, order)`
- `solve(lhs = rhs, unknown)`
- `sum(expr, index, lower, upper)`
- `simplify(expr)`
- `expand(expr)`
- `factor(expr)`
- `subs(expr, variable, value)`

Definitions persist between `%%eng` cells. Reset only the engcalc symbolic state with:

```text
%eng_reset
```

## Visible calculation headings

Inside `%%eng`, a single `#` remains an invisible comment. Use `##` for a visible calculation title and `###` for a smaller visible subtitle:

```text
%%eng

# This comment is not rendered
## Cálculo de reacciones

Sigma_F_y = 0
V_A = q*L

### Equilibrio de momentos
Sigma_M_A = 0
M_A = q*L^2/2
```

Heading text is displayed as text, not interpreted as executable code. Level-2 headings (`##`) have stronger visual separation than level-3 headings (`###`) so calculation states and subsections remain easy to scan.

## Compact aligned equation blocks

Consecutive equations between headings are rendered as one aligned mathematical block. Equal signs share one vertical alignment column, routine rows use compact spacing, and a blank line in the source becomes a slightly larger internal row gap instead of a separate notebook output block. The source syntax does not change:

```text
%%eng

## Estado 0: cargas reales
### Reacciones de la estructura base

Sigma_F_y_0 = 0
R_A0 = q*L

Sigma_M_A_0 = 0
M_A0 = q*L^2/2

### Fuerzas internas

V_0(x) = R_A0 - q*x
M_0(x) = -M_A0 + R_A0*x - q*x^2/2
```

The output is composed as one compact `aligned` block per subsection, rather than one independent Jupyter/Colab display object per equation.

## Engineering factor order

For commutative products, the renderer uses an engineering-oriented display order without changing the symbolic mathematics. Numeric coefficients come first, then factors whose symbol names begin with lowercase letters, then factors whose symbol names begin with uppercase letters. For example:

\[
M_A=\frac{qL^2}{2},\qquad
R_B=\frac{3qL}{8},\qquad
D=\frac{qL^4}{8EI}.
\]

This factor ordering is only a presentation rule for products. It does not reorder additive expressions such as `x^2 + 2*x + 1`.

## Equilibrium notation and indexed sums

For engineering equilibrium equations, use a target beginning with `Sigma_`. The prefix is rendered as an uppercase Greek sigma followed by the engineering quantity, rather than as a subscript on sigma:

```text
%%eng

Sigma_F_x = R_Ax - P_x
Sigma_F_y = R_Ay + R_By - P_y
Sigma_M_A = R_By*L - P_y*a
```

These targets render as `\Sigma F_x`, `\Sigma F_y`, and `\Sigma M_A`.

For an indexed mathematical summation, use:

```text
%%eng

S = sum(F_i, i, 0, n)
```

which renders as

\[
S=\sum_{i=0}^{n}F_i.
\]

`sum(...)` is intentionally kept as a symbolic `Sum` instead of being automatically collapsed. This preserves indexed engineering notation such as `F_i` without incorrectly treating it as a constant with respect to `i`.

## Example — internal forces and critical point

```text
%%eng
#@title { vertical-output: true }

## Fuerzas internas
V(x) = R_A - q*x
x_crit = solve(V(x) = 0, x)

M(x) = M_A + R_A*x - q*x^2/2
M_crit = subs(M(x), x, x_crit)
dM = diff(M(x), x)
```

## Units

The symbolic v0.1 engine intentionally has no physical-unit propagation. Use Pint + Handcalcs for numerical substitution with units, and anaStruct/anaStruct Plus for structural-analysis verification.

## Safety

`%%eng` uses a restricted AST evaluator. Raw cell text is never forwarded to unrestricted Python `eval` or `exec`. Attribute access and arbitrary Python calls are rejected. Visible heading text is HTML-escaped before display.

## Development

```bash
python -m pip install -e '.[dev]'
pytest -q
```

Version: `0.1.6`.
