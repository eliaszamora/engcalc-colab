from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


pyproject_path = Path("pyproject.toml")
pyproject = pyproject_path.read_text()
pyproject = replace_once(
    pyproject,
    'version = "0.7.0"',
    'version = "0.7.1"',
    "pyproject version",
)
pyproject_path.write_text(pyproject)

init_path = Path("src/engcalc_colab/__init__.py")
init_text = init_path.read_text()
init_text = replace_once(
    init_text,
    '__version__ = "0.7.0"',
    '__version__ = "0.7.1"',
    "runtime version",
)
init_path.write_text(init_text)

readme_path = Path("README.md")
readme = readme_path.read_text()
readme = replace_once(
    readme,
    "Current version: **0.7.0**.",
    "Current version: **0.7.1**.",
    "README current version",
)

section = r'''## v0.7.1 multi-argument functions and generalized partial evaluation

v0.7.1 generalizes EngCalc user-defined functions from one positional parameter to any positive number of ordered positional parameters while preserving the existing one-argument syntax. It also generalizes `numeric(...)` so known arguments and known numerical context values can be evaluated with Pint while one or more caller-supplied symbols remain symbolic.

```text
%%eng

M(x) = q*x*(L-x)/2
M_param(x, q) = q*x*(L-x)/2
M_base(x, q, L) = q*x*(L-x)/2
qU(qD, qL) = 1.2*qD + 1.6*qL
M_U(x) = M_base(x, qU(qD, qL), L)
v(x, A, L) = A*sin(pi*x/L)

qD := 10*kN/m
qL := 5*kN/m
L := 4*m
A := 20*mm

numeric(M_base(2*m, qD, L), kN*m)
numeric(M_base(x, qD, L))
numeric(v(x, A, L))
result(M_base(2*m, qD, L), kN*m)
plot(M_U(x), x, 0*m, L)
```

Function calls use exact positional arity. Parameter binding is simultaneous, local parameters shadow same-named symbolic or numerical context values only inside the function call, and redefining a function replaces its previous signature rather than creating an overload. Nested user-defined functions can be passed as arguments, including load-combination forms such as `M_base(x, qU(qD, qL), L)`.

For a partial numerical call such as `numeric(M_base(x, qD, L))`, EngCalc substitutes the known `qD` and `L` quantities while retaining the caller-side name `x` as unresolved. Multiple unresolved caller symbols are supported. Polynomial partials retain the existing evaluated-coefficient presentation when exactly one unresolved polynomial variable remains; non-polynomial partials such as `numeric(v(x, A, L))` render the known substitutions plus the remaining symbolic structure without fabricating a final quantity. Target-unit conversion still requires a fully numerical result.

Multi-argument functions integrate with the existing plotting and envelope APIs. Direct calls such as `plot(M_base(x, qD, L), x, 0*m, L)` and one-variable wrappers such as `M_U(x)` use the existing 201-point sampling grid and existing structural sign conventions.

v0.7.1 intentionally does **not** add default parameter values, keyword arguments, variadic parameters, function overloads by arity, or Cartesian multi-parameter sweeps. Existing single-parameter plot/envelope sweep behavior is unchanged.

'''
marker = "## v0.7.0 scalar engineering mathematics\n"
if "## v0.7.1 multi-argument functions and generalized partial evaluation" not in readme:
    readme = replace_once(readme, marker, section + marker, "README v0.7.1 section")
readme_path.write_text(readme)
