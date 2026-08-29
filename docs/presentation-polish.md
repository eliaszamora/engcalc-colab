# EngCalc presentation polish

This pre-release presentation feature builds on the validated narrative-text branch while keeping the package version at 0.7.2 until formal 0.8.0 release closure.

## Optional plot and envelope text

`plot(...)` and `envelope(...)` accept three optional presentation keywords:

- `title="..."` — figure title.
- `xlabel="..."` — x-axis label stem.
- `ylabel="..."` — y-axis label stem.

When an option is omitted, EngCalc keeps the existing automatic title/axis label exactly as before.

The labels are presentation text only. Units remain owned by EngCalc/Pint and are appended automatically from the evaluated quantities. For example, `xlabel="Longitud"` on a length-domain plot becomes `Longitud [m]`; `ylabel="Momento"` on a moment response becomes `Momento [kN·m]` when that is the active ordinate unit.

Examples:

```text
plot(M(x), x, 0, L)
```

keeps the existing automatic presentation.

```text
plot(M(x), x, 0, L, title="Diagrama de momento flector", xlabel="Longitud", ylabel="Momento")
```

customizes all three text fields while leaving units automatic.

Partial customization is valid:

```text
plot(M(x), x, 0, L, title="Diagrama de momento flector")
```

The same contract applies to envelopes:

```text
envelope(M_D(x), M_L(x), M_U(x), x, 0, L, title="Envolvente de momento", xlabel="Longitud", ylabel="Momento")
```

One existing parameter sweep may coexist with the presentation options:

```text
plot(M(x), x, 0, L, q=[5*kN/m, 10*kN/m], title="Comparación de cargas", xlabel="Longitud", ylabel="Momento")
```

EngCalc still exposes no arbitrary Matplotlib keyword surface. `title`, `xlabel`, and `ylabel` must be non-empty strings, and the existing one-sweep limit remains unchanged.

## Content-block spacing

Real Google Colab screenshots of the narrative-text feature confirmed correct source ordering and rendering, but showed that transitions among headings, prose, equations, and plots were slightly compressed.

The presentation polish therefore changes only the HTML margins around visible prose/headings:

- level-2 heading: `margin: 0.60rem 0 0.34rem 0`;
- level-3 heading: `margin: 0.46rem 0 0.24rem 0`;
- narrative block: `margin: 0.36rem 0 0.60rem 0`.

The mathematical MathJax spacing policy is deliberately unchanged. Existing 8-point spacing between ordinary calculation rows and 16-point spacing after explicit blank source lines remain part of the regression suite.

## Non-goals

This feature does not change numerical sampling, envelope mathematics, plot sign conventions, plot characteristic-point logic, Pint unit selection, the symbolic/numeric separation, or package versioning. Positive structural moment remains plotted downward.
