# Narrative text in `%%eng`

EngCalc can interleave explanatory prose with headings, equations, tables and plots by wrapping narrative text in triple double quotes.

## Short form

```text
%%eng

## Análisis de la viga

"""Se analiza una viga simplemente apoyada sometida a una carga uniformemente distribuida. La luz del elemento es de 6 m."""

L := 6*m
q := 10*kN/m
```

The delimiters are not shown in the rendered calculation memory. They only mark text that EngCalc should present as prose.

## Multiline form

```text
%%eng

"""
Se analiza una viga simplemente apoyada sometida a una carga
uniformemente distribuida. La luz del elemento es de 6 m.
"""
```

Consecutive non-empty source lines belong to the same paragraph and are joined naturally with spaces.

## Several paragraphs

A blank line inside the triple-quoted block starts a new paragraph:

```text
"""
Primero se determinan las cargas gravitacionales que actúan
sobre el elemento.

Luego se calculan las solicitaciones correspondientes a la
combinación última de diseño.
"""
```

## Source-order example

```text
%%eng

## Diseño a flexión

"""
Se determina inicialmente el momento máximo solicitado para la viga.
"""

Mu = 1.2*MD + 1.6*ML
numeric(Mu, kN*m)

"""La solicitación obtenida se compara con la resistencia de diseño de la sección."""

phiMn := 180*kN*m
numeric(phiMn, kN*m)
```

Narrative blocks are presentation boundaries: equations accumulated before a narrative block are rendered first, then the prose appears, and subsequent calculations continue in source order.

## Rules

- `"""text"""` and multiline `""" ... """` forms are both valid.
- The block must contain non-empty text.
- The closing `"""` must be present.
- No calculation or other content may appear after the closing delimiter on the same line.
- `#`, `##` and `###` inside a narrative block are literal text; outside the block the existing comment/heading rules remain unchanged.
- Narrative text is plain text, not Markdown or arbitrary HTML.
- User text is HTML-escaped before display.
- Narrative blocks do not modify EngCalc symbolic or numerical state.
