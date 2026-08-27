# EngCalc 0.2.0 — Numeric Context + Units Design

Date: 2026-08-27

## Goal

Extend EngCalc from a symbolic-only notebook language into a unified engineering-calculation interface that preserves symbolic derivations while evaluating them numerically with physical units.

The non-negotiable rule is that numerical data never overwrites the symbolic model. A symbol such as `q` remains symbolic in formulas even after a numerical value is associated with it.

## Scope of 0.2.0

Included:

1. Numeric assignment syntax with `:=`.
2. A numeric context independent from the symbolic namespace.
3. Pint-backed quantities and dimensional propagation.
4. `numeric(expr)` for evaluating symbolic expressions from the numeric context.
5. Memory-style rendering: symbolic formula -> substituted values -> final quantity.
6. Numeric RHS expressions may reference previously defined numeric values.
7. Final `numeric(...)` quantities display with two decimal places by default.
8. `%eng_reset` clears symbolic and numeric EngCalc state.
9. Documentation and regression tests.

Deferred:

- explicit target-unit conversion, e.g. `numeric(M_A, kN*m)`;
- configurable precision;
- keyword arguments;
- automatic expected dimensions from engineering variable names;
- arrays/tables and vectorized evaluation;
- arbitrary Python functions;
- multi-solution `solve` improvements.

## User-facing syntax

### Symbolic layer remains unchanged

```text
%%eng

V_B = 3*q*L/8
V_A = 5*q*L/8
M_A = q*L^2/8
```

The symbolic namespace continues to contain SymPy expressions such as `M_A -> q*L^2/8`.

### Numeric assignments

```text
%%eng

## Datos numericos

q := 2.8*tonf/m
L := 4*m
```

`:=` means: associate a numerical quantity with this symbolic identifier. It does not perform symbolic substitution and does not replace existing formulas.

A later assignment:

```text
q := 3.5*tonf/m
```

updates only the numeric context.

Numeric assignments may reference numeric values already defined:

```text
q := 2.8*tonf/m
L := 4*m
P := q*L
```

Here `P` receives a numeric quantity in the numeric context; any symbolic `P` remains a SymPy symbol/expression in the symbolic layer.

### Numerical evaluation

```text
%%eng

## Resultados numericos

numeric(V_B)
numeric(V_A)
numeric(M_A)
```

For a named symbolic result, EngCalc renders conceptually:

```text
V_B = 3*q*L/8 = 3*(2.80 tonf/m)*(4.00 m)/8 = 4.20 tonf
```

`numeric(expr)` also accepts a direct expression:

```text
numeric(q*L^2/8)
```

The symbolic expression remains the source of truth.

## Architecture

### Chosen approach: parallel NumericContext backed by Pint

The current symbolic engine remains responsible only for symbolic mathematics:

```text
EngineeringEngine
├── namespace       # SymPy scalar expressions
├── functions       # symbolic single-argument functions
├── symbols         # SymPy symbols
└── numeric_context # Pint-backed values keyed by identifier
```

A new focused module, proposed as `numeric.py`, owns:

- an internal Pint `UnitRegistry`;
- engineering unit aliases and the `tonf` definition;
- numeric values;
- restricted numeric RHS evaluation;
- evaluation of SymPy expressions using Pint quantities;
- quantity/unit formatting.

This preserves the current parser/engine/renderer separation instead of mixing Pint arithmetic into the symbolic evaluator.

### Rejected alternatives

1. **Overwrite symbolic values after numeric assignment:** simpler but destroys formulas and requires re-derivation when data changes.
2. **Use SymPy units instead of Pint:** tighter SymPy coupling but worse engineering-unit ergonomics and conversion behavior for this project.

## Parser contract

Introduce a dedicated parsed item such as `ParsedNumericAssignment` with:

- `line_no`
- `source`
- `target`
- `expression`
- `blank_before`

The parser detects a top-level `:=` before ordinary `=` processing.

Valid:

```text
q := 2.8*tonf/m
L := 4*m
E := 200*GPa
I := 850000000*mm^4
P := q*L
```

Invalid in 0.2.0:

```text
M(x) := 2*kN*m
```

Numeric targets must be simple identifiers.

Numeric RHS syntax remains restricted to numeric constants, names, parentheses, unary signs, and `+ - * / ^`. It does not allow attribute access, arbitrary calls, collections, imports, or Python execution.

`numeric` becomes a reserved EngCalc operation.

## Unit system

EngCalc owns an internal Pint registry. Users do not manage this registry inside `%%eng`.

Initial aliases:

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

Unit aliases are interpreted as units only while evaluating numeric-context expressions. They do not become reserved symbolic identifiers globally. Therefore `m` may still be used as an ordinary symbolic variable outside `:=` and `numeric(...)`.

Pint handles dimensional propagation and incompatible arithmetic. EngCalc converts expected Pint failures into concise line-aware errors.

## Numeric evaluation semantics

For `numeric(V_B)`:

1. Resolve `V_B` through the symbolic namespace.
2. Obtain its SymPy expression, e.g. `3*q*L/8`.
3. Determine free symbols.
4. Require a numeric-context value for every required symbol.
5. Recursively evaluate the SymPy tree with Pint quantities; never use unrestricted `eval`.
6. Return a structured result containing the symbolic expression, substitutions, and final quantity.

If values are missing:

```text
engcalc: line 4: numeric evaluation requires values for: L, q
```

### Symbolic functions

0.2.0 supports numerical evaluation of an existing symbolic function call when its arguments and remaining symbols can be resolved:

```text
V(x) = 5*q*L/8 - q*x
x := 2*m
q := 2.8*tonf/m
L := 4*m
numeric(V(x))
```

The existing symbolic function expansion occurs first, then numeric evaluation.

## Result models

Use explicit result types instead of adding optional Pint fields to ordinary symbolic results. The implementation should introduce equivalents of:

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

Exact class names may vary, but symbolic and numeric result semantics remain explicit and separately testable.

## Rendering

### Numeric assignment

```text
q := 2.8*tonf/m
```

uses the existing three-column layout:

```text
q | = | 2.80 tonf/m
```

### `numeric(expr)`

Named result:

```text
V_B | = | 3*q*L/8 = 3*(2.80 tonf/m)*(4.00 m)/8 = 4.20 tonf
```

Direct expression:

```text
q*L^2/8 | = | (2.80 tonf/m)*(4.00 m)^2/8 = 5.60 tonf*m
```

Only the first equality uses the dedicated center column; later equalities remain in the right-hand column, consistent with existing integral/solve rendering.

Units render upright, not as italic mathematical variables. Existing 4 pt regular / 8 pt blank-line spacing remains unchanged.

The final quantity uses two decimal places by default in 0.2.0. Precision configuration is deliberately deferred.

## State and reset

`%eng_reset` clears:

- symbolic namespace;
- symbolic functions;
- cached symbols;
- numeric context.

The message becomes:

```text
engcalc state cleared
```

## Errors

All expected user errors remain concise and line-aware. Required coverage:

- malformed `:=`;
- invalid numeric target;
- unknown/unsupported unit or numeric name;
- unsupported numeric RHS syntax;
- missing values for `numeric(...)`;
- incompatible dimensions;
- wrong `numeric(...)` arity;
- use of `numeric` as an assignment target.

No expected Pint/Python traceback is printed by `%%eng`.

## Dependency and version

Add `pint` as a runtime dependency in `pyproject.toml`.

This public language and architecture expansion changes the package version from 0.1.9 to 0.2.0.

## Testing strategy

Implementation is TDD-first.

### Parser

- parse `q := 2.8*tonf/m` as numeric assignment;
- preserve ordinary `=` behavior;
- reject function numeric assignment;
- reserve `numeric`;
- preserve blank-line metadata.

### Numeric context

- store/update Pint quantities;
- verify `tonf`;
- allow numeric references such as `P := q*L`;
- reject unknown names and unsafe syntax;
- reset clears numeric data.

### Numeric evaluation

- `V_B = 3*q*L/8`, `q := 2.8*tonf/m`, `L := 4*m` -> `4.20 tonf`;
- `M_A = q*L^2/8` -> `5.60 tonf*m`;
- symbolic formulas remain unchanged after numeric assignment;
- changing `q` changes `numeric(M_A)` without changing `M_A`;
- missing values produce concise errors;
- dimensional incompatibility produces concise errors;
- numerical symbolic-function evaluation works.

### Renderer and magic

- numeric assignments use the three-column layout;
- formula -> substitution -> quantity stays in one row;
- units are upright;
- two-decimal default is stable;
- existing 4/8 pt spacing remains stable;
- headings and all symbolic regressions remain green.

### Regression

All 0.1.9 tests must remain green.

## Acceptance example

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

Expected final quantities:

```text
V_B = 4.20 tonf
V_A = 7.00 tonf
M_A = 5.60 tonf*m
```

Then:

```text
q := 3.5*tonf/m
numeric(M_A)
```

updates the numeric result to `7.00 tonf*m` while the symbolic definition `M_A = q*L^2/8` remains unchanged.
