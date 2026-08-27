# EngCalc 0.2.0 — Numeric Context + Units Design

Date: 2026-08-27

## Goal

Extend EngCalc from a symbolic-only notebook language into a unified engineering-calculation interface that can preserve symbolic derivations while also evaluating them numerically with physical units.

The key requirement is that numerical data must never overwrite or destroy the symbolic model. A symbol such as `q` must remain symbolic in formulas even after a numerical value is associated with it.

## Scope of 0.2.0

Included:

1. Numeric assignment syntax with `:=`.
2. A numeric context independent from the symbolic namespace.
3. Pint-backed physical quantities and unit propagation.
4. `numeric(expr)` for evaluating symbolic expressions using the numeric context.
5. Calculation-memory rendering in the form formula -> substituted values -> final quantity.
6. Reset behavior that clears both symbolic and numeric EngCalc state.
7. Documentation and regression tests.

Deferred to a later milestone:

- explicit target-unit conversion syntax such as `numeric(M_A, kN*m)`;
- precision/configuration commands;
- keyword arguments;
- automatic dimensional expectations for named engineering quantities;
- numerical arrays/tables;
- vectorized evaluation of `V(x)` / `M(x)` over arrays;
- arbitrary Python functions;
- multi-solution `solve` improvements.

## User-facing syntax

### Symbolic calculation remains unchanged

```text
%%eng

V_B = 3*q*L/8
V_A = 5*q*L/8
M_A = q*L^2/8
```

The symbolic namespace stores:

```text
V_B -> 3*q*L/8
V_A -> 5*q*L/8
M_A -> q*L^2/8
```

### Numeric assignments

```text
%%eng

## Datos numericos

q := 2.8*tonf/m
L := 4*m
```

`:=` means "associate this numerical quantity with this symbolic identifier". It does not perform a symbolic assignment and does not replace `q` or `L` in existing formulas.

The numeric context stores Pint quantities:

```text
q -> 2.8 tonf / meter
L -> 4 meter
```

A later `q := 3.5*tonf/m` updates only the numeric context. Existing symbolic formulas remain unchanged.

### Numerical evaluation

```text
%%eng

## Resultados numericos

numeric(V_B)
numeric(V_A)
numeric(M_A)
```

For an expression with a symbolic definition, EngCalc should conceptually render:

```text
V_B = 3*q*L/8 = 3*(2.8 tonf/m)*(4 m)/8 = 4.20 tonf
```

The symbolic formula is retained as the source of truth. Numeric evaluation substitutes every required symbol from the numeric context, evaluates with Pint, simplifies units naturally, and displays the quantity.

`numeric(expr)` may also evaluate a direct symbolic expression, for example:

```text
numeric(q*L^2/8)
```

## Architectural decision

### Recommended approach: parallel NumericContext backed by Pint

Keep the current SymPy engine intact and add a second state container:

```text
EngineeringEngine
├── namespace       # symbolic scalar expressions
├── functions       # symbolic single-argument functions
├── symbols         # SymPy symbols
└── numeric_context # Pint quantities keyed by symbolic identifier
```

A dedicated module (proposed: `numeric.py`) owns:

- the internal Pint `UnitRegistry`;
- engineering-specific unit definitions such as `tonf`;
- the dictionary of numeric values;
- restricted evaluation of numeric RHS expressions;
- symbolic-expression substitution/evaluation with Pint quantities;
- unit-format helpers.

This keeps SymPy and Pint responsibilities isolated and testable.

### Alternatives rejected

1. **Overwrite symbolic values after numeric assignment.** Simpler, but destroys symbolic formulas and makes data changes require re-derivation.
2. **Use SymPy units instead of Pint.** Tighter integration with SymPy, but weaker ergonomics for engineering quantities/conversions and less aligned with the existing notebook setup.

## Parser changes

### New parsed item

Introduce a dedicated model such as:

```text
ParsedNumericAssignment
- line_no
- source
- target
- expression
- blank_before
```

The parser must detect top-level `:=` before ordinary `=` handling.

Valid examples:

```text
q := 2.8*tonf/m
L := 4*m
E := 200*GPa
I := 850000000*mm^4
```

Numeric assignment targets must be simple identifiers. Function targets such as `M(x) := ...` are rejected in 0.2.0.

The numeric RHS uses the existing restricted AST philosophy: numeric constants, names, parentheses, unary signs, and `+ - * / ^` only. No attributes, arbitrary calls, lists, dictionaries, imports, or Python execution.

`numeric` becomes a reserved EngCalc operation.

## Unit system

EngCalc owns an internal Pint `UnitRegistry` so the user does not need to expose or manage a registry inside `%%eng`.

Initial engineering aliases available in numeric assignments:

- length: `mm`, `cm`, `m`
- force: `N`, `kN`, `kgf`, `tonf`
- pressure/stress: `Pa`, `kPa`, `MPa`, `GPa`
- mass: `kg`
- time: `s`
- angle: `rad`, `deg`

`tonf` is defined as:

```text
1 tonf = 9.80665 kN
```

Pint handles dimensional propagation. Incompatible arithmetic must raise a concise EngCalc error rather than a raw traceback.

## Numeric evaluation semantics

### Resolving a symbolic expression

For `numeric(V_B)`:

1. Resolve `V_B` through the symbolic namespace.
2. Obtain the SymPy expression `3*q*L/8`.
3. Determine required free symbols (`q`, `L`).
4. Require a numeric-context value for every free symbol.
5. Evaluate the expression recursively using Pint quantities, not by unrestricted `eval`.
6. Return a structured numeric result containing:
   - original symbolic expression;
   - mapping of substituted symbols to quantities;
   - evaluated Pint quantity.

If a required symbol has no numeric value, raise a concise error such as:

```text
engcalc: line 4: numeric evaluation requires values for: L, q
```

### Defined symbolic functions

0.2.0 should support numerical evaluation of a function call when all arguments and remaining symbols can be resolved, for example:

```text
V(x) = 5*q*L/8 - q*x
x := 2*m
q := 2.8*tonf/m
L := 4*m
numeric(V(x))
```

This uses the existing symbolic function expansion first, then the numeric context.

## Result models

Do not overload ordinary symbolic results with ad-hoc Pint fields. Introduce explicit result types, for example:

```text
NumericAssignmentResult
- statement
- quantity

NumericEvaluationResult
- statement
- symbolic_expression
- substitutions
- quantity
- display_name (optional)
```

`magic.py` can group symbolic and numeric rows together through a common rendering interface or flush groups when result types require different rendering. The exact class names may vary, but result semantics must remain explicit.

## Rendering

### Numeric assignment

```text
q := 2.8*tonf/m
```

renders as a normal three-column EngCalc row:

```text
q | = | 2.8 tonf/m
```

### numeric(expr)

The desired memory-style output is:

```text
symbolic formula | = | substituted expression = final quantity
```

For example:

```text
V_B | = | 3*q*L/8 = 3*(2.8 tonf/m)*(4 m)/8 = 4.20 tonf
```

The existing left / equals / right three-column layout is preserved.

Units should be rendered upright (`\mathrm{}`-style) rather than as italic mathematical variables.

0.2.0 may use Pint's compact engineering unit names for the final result. Automatic target-unit selection beyond Pint's natural simplified units is deferred.

## State and reset

`%eng_reset` clears:

- symbolic namespace;
- symbolic functions;
- cached symbols;
- numeric context.

The output message should be updated from "symbolic state cleared" to a more general wording such as:

```text
engcalc state cleared
```

## Error handling

All user-facing failures remain concise and line-aware.

Required cases:

- malformed `:=` assignment;
- numeric assignment to invalid target;
- unknown/unsupported unit name;
- unsupported syntax in numeric RHS;
- missing numeric values for `numeric(...)`;
- incompatible units during arithmetic;
- `numeric(...)` wrong arity;
- use of `numeric` as an assignment target.

No Pint or Python traceback should be printed through `%%eng` for expected user errors.

## Dependency and versioning

Add Pint as a runtime dependency in `pyproject.toml`.

This is a public language/architecture expansion, so version moves from 0.1.9 to 0.2.0.

## Testing strategy

Implementation follows TDD.

### Parser tests

- parse `q := 2.8*tonf/m` as numeric assignment;
- ordinary `=` remains unchanged;
- reject function numeric assignment;
- reserve `numeric`;
- preserve blank-line metadata.

### Numeric-context tests

- store and update Pint quantities;
- `tonf` definition;
- references between numeric values if supported by the implementation;
- reject unknown units and unsafe syntax;
- reset clears numeric data.

### Numeric evaluation tests

- `V_B = 3*q*L/8` + `q := 2.8*tonf/m` + `L := 4*m` -> `4.2 tonf`;
- `M_A = q*L^2/8` -> `5.6 tonf*m`;
- symbolic expression remains unchanged after numeric assignment;
- changing `q` changes `numeric(M_A)` without changing `M_A`;
- missing values produce concise errors;
- incompatible dimensional arithmetic produces concise errors;
- numerical function evaluation works.

### Renderer/magic tests

- numeric assignments participate in the three-column layout;
- formula -> substitution -> quantity appears in one row;
- units render upright;
- existing 4 pt / 8 pt row spacing remains unchanged;
- headings and symbolic rendering regressions remain green.

### Full regression

All existing 0.1.9 tests must remain green.

## Acceptance example

The following notebook flow is the acceptance target for 0.2.0:

```text
%%eng

## Reacciones simbolicas

V_B = 3*q*L/8
V_A = 5*q*L/8
M_A = q*L^2/8

## Datos numericos

q := 2.8*tonf/m
L := 4*m

## Resultados numericos

numeric(V_B)
numeric(V_A)
numeric(M_A)
```

Expected final numerical quantities:

```text
V_B = 4.20 tonf
V_A = 7.00 tonf
M_A = 5.60 tonf*m
```

Re-running only:

```text
q := 3.5*tonf/m
numeric(M_A)
```

must update the numerical result while leaving the symbolic definition `M_A = q*L^2/8` intact.
