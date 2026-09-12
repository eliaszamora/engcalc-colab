"""How a unit is spelled when it is plain text rather than LaTeX.

One module because there are four callers and they must agree: a table header and its
cells, a plot's axis and its annotations, a characteristic value, a summary row, the
`%eng_units` announcement, and the two diagnostics that name a unit while saying what
went wrong. A reader sees several of those on one page.

Pint 0.26 is why this exists as a module rather than a call. It changed the separator
`~P` puts between two unit factors from U+00B7 MIDDLE DOT to U+22C5 DOT OPERATOR -
`product_fmt="⋅"`, hard-coded in `PrettyFormatter`, with no knob on the formatter object
- and ten contracts went red on a commit that had been green an hour before. Nothing in
EngCalc had changed; a dependency had, and the engineer's install line carries
`--upgrade`, so the next run of his first cell would have changed the character under a
memoria already written.

The wrong character was the visible half. The quiet half is worse: `plotting.py` reads
the formatted string back to apply the structural convention that a moment is written
force·length, by splitting on the middle dot. Handed `kN⋅m` that split finds nothing, so
the convention stops being applied and the plot goes on drawing, which is the silent kind
of failure section 9 of `HOW-THIS-WORK-GOES-WRONG.md` collects.

The middle dot is the one to keep: ISO 80000 writes a product of units with U+00B7, the
LaTeX path emits `\\cdot`, which typesets as that same glyph, and every page this project
has rendered uses it. A dependency's default is not a reason to change any of that.

This module imports nothing from the package, so every layer can use it.
"""

from __future__ import annotations

# The dot this project puts between two unit factors.
PRODUCT_DOT = "·"

# What a formatter might hand back instead. A tuple rather than one string because the
# question "which character does this version use" has already been answered two ways.
_FORMATTER_PRODUCT_DOTS = ("⋅",)


def unit_text(unit) -> str:
    """A unit as the page writes it: `kN·m`, `cm²`, `kgf/cm²`.

    `""` for a dimensionless unit, which is what every caller wants: a table header
    reads `x` rather than `x [dimensionless]`.
    """
    if str(unit) == "dimensionless":
        return ""
    return normalise(format(unit, "~P"))


def normalise(text: str) -> str:
    """The spelling decision, applied to text a formatter already produced.

    Separate from `unit_text` because two callers interpolate the unit into a longer
    string themselves - a diagnostic, a plotted value - and normalising the finished
    string is the same decision made once rather than a second code path.
    """
    for dot in _FORMATTER_PRODUCT_DOTS:
        text = text.replace(dot, PRODUCT_DOT)
    return text


def quantity_text(quantity) -> str:
    """A quantity as plain text: `40 kN`, `4078.86 kgf`, `2 m/s`, `30`.

    The spelling a figure's legend uses for a swept parameter. It lived in the engine,
    which builds that legend entry before any `RenderSettings` exists - so when the
    renderer had to rebuild the entry in the sheet's declared units, the choice was
    between importing from the engine (the wrong direction; the engine does not import
    the renderer) and writing the format a second time. A quantity spelled as plain text
    is this module's subject, so it lives here and both callers agree by construction.

    `%g` rather than the page's precision, because a swept parameter is a value the
    engineer typed - `P=[40*kN, 80*kN]` - and `40` is what he wrote. A dimensionless
    value keeps its number and drops the empty unit.
    """
    magnitude = float(quantity.magnitude)
    value = f"{magnitude:g}"
    unit = unit_text(quantity.units)
    return value if not unit else f"{value} {unit}"
