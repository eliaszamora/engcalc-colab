# engcalc-colab

`engcalc-colab` is a compact symbolic-calculation layer for Google Colab and Jupyter. You write engineering mathematics with `%%eng`; SymPy remains hidden behind the interface.

## Install in Google Colab

After this project is published to GitHub:

```python
%pip install -q git+https://github.com/eliaszamora/engcalc-colab.git
%load_ext engcalc_colab
```

For a folder uploaded directly to Colab:

```python
%pip install -q /content/engcalc-colab
%load_ext engcalc_colab
```

## Example — propped cantilever by the force method

```text
%%eng

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

You do not write `symbols()`, `Eq()`, `sp.integrate()`, `sp.solve()[0]`, `display()`, or SymPy printer boilerplate.

## v0.1 operations

- `A = expression`
- `M(x) = expression`
- powers with `^`
- automatic symbolic identifiers
- comments beginning with `#`
- `integral(expr, var, lower, upper)`
- `diff(expr, var)` and `diff(expr, var, order)`
- `solve(lhs = rhs, unknown)`
- `simplify(expr)`
- `expand(expr)`
- `factor(expr)`
- `subs(expr, variable, value)`

Definitions persist between `%%eng` cells. Reset only the engcalc symbolic state with:

```text
%eng_reset
```

## Example — internal forces and critical point

```text
%%eng

V(x) = R_A - q*x
x_crit = solve(V(x) = 0, x)

M(x) = M_A + R_A*x - q*x^2/2
M_crit = subs(M(x), x, x_crit)
dM = diff(M(x), x)
```

## Units

The symbolic v0.1 engine intentionally has no physical-unit propagation. Use Pint + Handcalcs for numerical substitution with units, and anaStruct/anaStruct Plus for structural-analysis verification.

## Safety

`%%eng` uses a restricted AST evaluator. Raw cell text is never forwarded to unrestricted Python `eval` or `exec`. Attribute access and arbitrary Python calls are rejected.

## Development

```bash
python -m pip install -e '.[dev]'
pytest -q
```

Version: `0.1.0`.
