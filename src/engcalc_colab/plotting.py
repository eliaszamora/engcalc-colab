from __future__ import annotations

import math
import re
from dataclasses import dataclass

from matplotlib.mathtext import MathTextParser
import sympy as sp
from typing import Any

from .models import PlotResult, PlotSeries
from .unit_text import unit_text
# A figure writes its mathematics the way the page writes it, and `renderer` is where the
# page's spellings live: the ceiling a number is written above, the `\times 10^{6}` it is
# written as, and `\mathrm{kgf} \cdot \mathrm{cm}`. Matplotlib reads that same LaTeX
# subset through mathtext, so a figure is handed the page's own strings rather than a
# second spelling of them - the drift #135 and #138 were about. `renderer` does not import
# this module, so there is no cycle.
from .renderer import (
    _FIXED_DECIMAL_CEILING,
    _brace_group,
    _latex_unit_text,
    _scientific_latex,
)


_PLOT_Y_MARGIN = 0.30
_CALLOUT_CLEARANCE_X = 1.08
_CALLOUT_CLEARANCE_Y = 1.16
_HORIZONTAL_ANNOTATION_OFFSETS = (18, 72, 126, 180, -18, -72, -126, -180, 0)
_VERTICAL_ANNOTATION_OFFSETS = (24, 72, 120, 168, -24, -72, -120, -168)
_ANNOTATION_CANDIDATES = tuple(
    (dx, dy)
    for dy in _VERTICAL_ANNOTATION_OFFSETS
    for dx in _HORIZONTAL_ANNOTATION_OFFSETS
)


def _unit_label(quantity) -> str:
    """The unit on an axis, typeset exactly as the page typesets it. See `_unit_mathtext`.

    There used to be a `moment` flag here, selecting a rule that read this string back
    and swapped its factors when a moment had come out length-first. Nothing on a page
    reached it - measured over nine sheets in four unit systems, with each palette and
    without, through `plot`, `envelope` and a sweep - because the registry's
    `_keep_written_unit_order` and the display path settle the order long before a label
    is built. `tests/test_a_moment_axis_is_labelled_force_first.py` asserts the property
    the rule was supposed to provide, over those same units, so the guarantee is stated
    rather than implemented twice.

    Removing it took a cluster with it: the flag was threaded through five functions
    across two modules, `_is_moment_plot` and its regex duplicated the engine's, and
    `_FORCE_UNITS`/`_LENGTH_UNITS` existed only to be split against. `series.is_moment`
    stays - it decides the positive-down convention, which is a different question.
    """
    return _unit_mathtext(quantity.units)


# One parser, and not one per call: matplotlib caches a parse on the parser object, so a
# fresh one costs 5.5 ms a label instead of nothing. Imported at the top rather than
# deferred like `pyplot`: `label_layout` already imports `matplotlib.text` at module
# level, which imports this, so by the time `%load_ext` returns it is loaded either way -
# measured, after writing the deferred version on a 0.17 s figure taken in isolation.
_MATHTEXT = MathTextParser("agg")


def _unit_mathtext(unit) -> str:
    r"""A unit as a figure writes it: `$\mathrm{kgf} \cdot \mathrm{cm}$`.

    The page's own `_latex_unit_text`, wrapped so matplotlib typesets it. Two spellings
    of one unit on one page is the defect #135 removed from the text and this removes
    from the figure, where the axis read `kgf·cm` two centimetres from a table header
    reading `kgf · cm`.

    `""` for a dimensionless unit, like `unit_text`: an axis reads `f(x)` rather than
    `f(x) [$$]`.

    **A quotient is written inline**, which is the one place a figure departs from the
    page. `~L` puts `kgf/cm` in a `\frac`, and a `\frac` on a rotated y label sets its
    numerator and denominator at about six points - measured, and worse than the plain
    text it replaces. The page renders the same fraction at body size, where it reads.

    The fallback is for the unit nobody enumerated. Mathtext is a subset of LaTeX, so a
    unit it cannot parse raises *at draw time* and takes the whole cell with it, where
    today there is a label. Thirty-eight units were measured - both palettes, four moment
    systems, imperial, velocity, density - and every one parses; that is the reason to
    expect this never fires, and no reason to let a figure die if it does.
    """
    plain = unit_text(unit)
    if not plain:
        return ""
    maths = f"${_inline_quotient(_latex_unit_text(unit))}$"
    try:
        _MATHTEXT.parse(maths)
    except Exception:  # noqa: BLE001 - any parse failure means "draw it as text"
        return plain
    return maths


def _inline_quotient(latex: str) -> str:
    r"""`\frac{a}{b}` written `a/b`, and everything else left exactly as it came.

    Brace matching rather than a regular expression because the halves nest:
    `\frac{\mathrm{kgf}}{\mathrm{cm}^{2}}`. A unit is a single product of powers, so
    Pint's LaTeX has at most one `\frac` and it is the whole string; anything else falls
    through untouched.
    """
    prefix = r"\frac"
    if not latex.startswith(prefix):
        return latex
    numerator = _brace_group(latex, len(prefix))
    if numerator is None:
        return latex
    denominator = _brace_group(latex, numerator[1])
    if denominator is None or denominator[1] != len(latex):
        return latex
    return f"{numerator[0]}/{denominator[0]}"


def _scientific_mathtext(magnitude: float, precision: int) -> str:
    r"""A power of ten as a figure writes it: `$1.97 \times 10^{6}$`.

    The page's `_scientific_latex`, for the same reason the unit is. An HTML block needs
    the Unicode spelling because Colab typesets nothing inside one; a figure does not,
    and the two were visibly different beside each other - the Unicode `⁶` sits low and
    small next to the axis offset's mathtext superscript on the same axis.
    """
    return f"${_scientific_latex(magnitude, precision)}$"


def _in_bold(label: str) -> str:
    r"""Every `$...$` in a label, set at the weight of the text around it.

    Mathtext sets a formula in its own font and ignores the weight of the `Text` it sits
    in, so a semibold label came out with a light unit after it: `x = 300 cm` in two
    weights, one phrase, visible at the summary panel's own 8.2 pt. That panel's group
    header is the one bold label on a figure, and this is applied to the finished string
    rather than threaded through the two functions that built it - `\mathrm` is upright
    and `\mathbf` is upright bold, and a formula with no `\mathrm` in it, which is what a
    power of ten is, takes the wrapper instead.
    """

    def bolden(match: "re.Match[str]") -> str:
        maths = match.group(1)
        if r"\mathrm" in maths:
            return "$" + maths.replace(r"\mathrm", r"\mathbf") + "$"
        return r"$\mathbf{" + maths + "}$"

    return re.sub(r"\$(.+?)\$", bolden, label)


def _axis_label(name: str, quantity) -> str:
    """`Comparison [$\\mathrm{kgf} \\cdot \\mathrm{cm}$]`.

    The unit typesets and the name does not, which is `_table_header`'s decision applied
    to the figure so that a column header and the axis above it are built the same way:
    the unit comes from Pint and is mathematics, while the name is the text the engineer
    typed - `M(x)`, `Comparison`, `q_s(x)` - and turning that into LaTeX means parsing it.
    """
    unit = _unit_label(quantity)
    return name if not unit else f"{name} [{unit}]"


def _quantity_label(quantity) -> str:
    magnitude = float(quantity.magnitude)
    unit = _unit_label(quantity)
    value = f"{magnitude:.2f}"
    return value if not unit else f"{value} {unit}"


def _wants_exponent(values) -> bool:
    """Would any of these be written as a power of ten?

    Asked once for an axis, from the values the figure *draws*, and the answer is then
    used for every annotation on it. Annotated points lie on those curves, and matplotlib
    computes its own axis offset from the same data, so the label and the axis behind it
    cannot disagree.
    """
    for value in values:
        try:
            magnitude = abs(float(getattr(value, "magnitude", value)))
        except (TypeError, ValueError):
            continue
        if magnitude >= _FIXED_DECIMAL_CEILING:
            return True
    return False


def _annotation_exponents(result: PlotResult) -> tuple[bool, bool]:
    """`(abscissa, ordinate)`: how this figure writes each axis's annotations.

    Per axis and not per figure, for the reason #141 gave for a table's columns. A beam's
    abscissa runs 0 to 600 cm and reads perfectly well in decimals while its ordinate is
    in the millions; one answer for the whole figure would print `3.00×10²` for the
    mid-span station in order to tidy the moment beside it.
    """
    ordinates = [
        value
        for series in (*result.series, *result.source_series)
        for value in series.y_values
    ]
    return _wants_exponent(result.x_values), _wants_exponent(ordinates)


def _compact_number(value: float, *, exponent: bool = False) -> str:
    """A coordinate the reader reads off the axes, in the economy the axes have.

    Fixed decimals below a million and a power of ten above it - not a new rule, but the
    page's own `_FIXED_DECIMAL_CEILING`, which every table and every value has followed
    since `I_z := 80e6*mm**4` printed eight zeros nobody counts. The annotation is the one
    place it never reached.

    Reached commonly once a declared palette started reaching the figure: on a `kgf` sheet
    the beam's envelope annotated `(447, 2211787.72)` beside an axis whose own ticks read
    `0.0, 0.5, 1.0 … ×10⁶`. Eleven significant figures on a chart showing two.

    `exponent` is the axis speaking for its annotations. Answering per value put
    `(300, 611829.73)` on one curve of a sweep and `(300, 1.22×10⁶)` on the other, on one
    axis - the same defect #141 fixed for a table column, asked about a figure. A zero
    stays a zero: it has no exponent to take, which is why that return sits above this.
    """
    if math.isclose(value, 0.0, rel_tol=0.0, abs_tol=5e-13):
        value = 0.0
    if value == 0.0:
        return "0"
    if exponent or abs(value) >= _FIXED_DECIMAL_CEILING:
        return _scientific_mathtext(value, 2)
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _compact_exact_x_label(symbolic, numeric: float, *, exponent: bool = False) -> str:
    if isinstance(symbolic, sp.Rational) and symbolic.q != 1:
        return f"{symbolic.p}/{symbolic.q}"
    return _compact_number(numeric, exponent=exponent)


def _coordinate_label(
    x: float,
    y: float,
    x_symbolic=None,
    *,
    exponents: tuple[bool, bool] = (False, False),
) -> str:
    x_exponent, y_exponent = exponents
    x_text = _compact_exact_x_label(x_symbolic, x, exponent=x_exponent)
    return f"({x_text}, {_compact_number(y, exponent=y_exponent)})"


def _extreme_indices(values: list[float]) -> tuple[int, int]:
    maximum = max(range(len(values)), key=values.__getitem__)
    minimum = min(range(len(values)), key=values.__getitem__)
    return maximum, minimum


def _response_symbol(label: str) -> str:
    label = label.strip()
    if label.startswith("|") and "|" in label[1:]:
        return label
    if " = " in label:
        return label
    return re.sub(r"\([^()]*\)$", "", label)


def _series_response_symbol(result: PlotResult, series) -> str:
    label = series.display_label
    if " = " in label:
        return _response_symbol(result.display_label)
    return _response_symbol(label)


@dataclass(frozen=True)
class _CharacteristicRequest:
    series_index: int
    series: PlotSeries
    sample_index: int
    x_quantity: Any
    y_quantity: Any
    response_label: str
    role: str
    inverted: bool
    x_symbolic: Any | None = None


def _nearest_sample_index(result: PlotResult, x_quantity) -> int:
    unit = result.x_values[0].units
    target = float(x_quantity.to(unit).magnitude)
    return min(
        range(len(result.x_values)),
        key=lambda index: abs(float(result.x_values[index].to(unit).magnitude) - target),
    )


def _characteristic_requests(result: PlotResult) -> tuple[_CharacteristicRequest, ...]:
    inverted = all(series.is_moment for series in result.series)
    requests: list[_CharacteristicRequest] = []

    for series_index, series in enumerate(result.series):
        response_label = _series_response_symbol(result, series)
        if result.kind == "plot" and series.characteristics:
            x_unit = result.x_values[0].units
            y_unit = series.y_values[0].units
            series_requests: list[_CharacteristicRequest] = []
            for characteristic_role, request_role in (
                ("global_max", "max"),
                ("global_min", "min"),
            ):
                point = next(
                    (
                        item
                        for item in series.characteristics
                        if characteristic_role in item.roles
                        and item.value_quantity is not None
                    ),
                    None,
                )
                if point is None:
                    continue
                x_quantity = point.x_quantity.to(x_unit)
                y_quantity = point.value_quantity.to(y_unit)
                x_magnitude = float(x_quantity.magnitude)
                y_magnitude = float(y_quantity.magnitude)
                if any(
                    math.isclose(
                        x_magnitude,
                        float(existing.x_quantity.to(x_unit).magnitude),
                        rel_tol=1e-12,
                        abs_tol=1e-12,
                    )
                    and math.isclose(
                        y_magnitude,
                        float(existing.y_quantity.to(y_unit).magnitude),
                        rel_tol=1e-12,
                        abs_tol=1e-12,
                    )
                    for existing in series_requests
                ):
                    continue
                series_requests.append(
                    _CharacteristicRequest(
                        series_index=series_index,
                        series=series,
                        sample_index=_nearest_sample_index(result, x_quantity),
                        x_quantity=x_quantity,
                        y_quantity=y_quantity,
                        response_label=response_label,
                        role=request_role,
                        inverted=inverted,
                        x_symbolic=point.x_symbolic,
                    )
                )
            requests.extend(series_requests)
            continue

        values = [float(value.magnitude) for value in series.y_values]
        maximum_index, minimum_index = _extreme_indices(values)
        requests.append(
            _CharacteristicRequest(
                series_index=series_index,
                series=series,
                sample_index=maximum_index,
                x_quantity=result.x_values[maximum_index],
                y_quantity=series.y_values[maximum_index],
                response_label=response_label,
                role="max",
                inverted=inverted,
            )
        )
        if not math.isclose(
            values[maximum_index],
            values[minimum_index],
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            requests.append(
                _CharacteristicRequest(
                    series_index=series_index,
                    series=series,
                    sample_index=minimum_index,
                    x_quantity=result.x_values[minimum_index],
                    y_quantity=series.y_values[minimum_index],
                    response_label=response_label,
                    role="min",
                    inverted=inverted,
                )
            )
    return tuple(requests)


def _visual_above_for_role(role: str, inverted: bool) -> bool:
    mathematical_maximum = role == "max"
    return (mathematical_maximum and not inverted) or (not mathematical_maximum and inverted)


def _annotation_alignment(offset: tuple[int, int]) -> tuple[str, str]:
    dx, dy = offset
    if dx > 0:
        ha = "left"
    elif dx < 0:
        ha = "right"
    else:
        ha = "center"
    va = "bottom" if dy >= 0 else "top"
    return ha, va


def _create_annotation(axis, text: str, x: float, y: float, offset: tuple[int, int], line_color):
    dx, dy = offset
    ha, va = _annotation_alignment(offset)
    return axis.annotate(
        text,
        xy=(x, y),
        xytext=(dx, dy),
        textcoords="offset points",
        ha=ha,
        va=va,
        fontsize=8.5,
        color=line_color,
        zorder=7,
        annotation_clip=False,
    )


def _annotation_box(annotation, renderer):
    annotation.update_bbox_position_size(renderer)
    return annotation.get_window_extent(renderer)


def _bbox_overlap_area(left, right) -> float:
    width = max(0.0, min(left.x1, right.x1) - max(left.x0, right.x0))
    height = max(0.0, min(left.y1, right.y1) - max(left.y0, right.y0))
    return width * height


def _bbox_outside_amount(box, boundary) -> float:
    return (
        max(0.0, boundary.x0 - box.x0)
        + max(0.0, box.x1 - boundary.x1)
        + max(0.0, boundary.y0 - box.y0)
        + max(0.0, box.y1 - boundary.y1)
    )


def _curve_display_points(axis) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for line in axis.lines:
        if line.get_label() == "_zero":
            continue
        for x_value, y_value in zip(line.get_xdata(), line.get_ydata()):
            try:
                x = float(x_value)
                y = float(y_value)
            except (TypeError, ValueError):
                continue
            display_x, display_y = axis.transData.transform((x, y))
            points.append((float(display_x), float(display_y)))
    return points


def _curve_overlap_count(candidate_box, curve_points, anchor_display) -> int:
    anchor_x, anchor_y = anchor_display
    hits = 0
    for point_x, point_y in curve_points:
        if abs(point_x - anchor_x) < 1e-6 and abs(point_y - anchor_y) < 1e-6:
            continue
        if candidate_box.x0 <= point_x <= candidate_box.x1 and candidate_box.y0 <= point_y <= candidate_box.y1:
            hits += 1
    return hits


def _candidate_constraints(
    candidate_box,
    occupied_boxes: list,
    axes_box,
    legend_box,
    curve_points,
    anchor_display,
) -> tuple[float, float, float, int]:
    outside = _bbox_outside_amount(candidate_box, axes_box)
    occupied_overlap = sum(_bbox_overlap_area(candidate_box, occupied) for occupied in occupied_boxes)
    legend_overlap = 0.0 if legend_box is None else _bbox_overlap_area(candidate_box, legend_box)
    curve_overlap = _curve_overlap_count(candidate_box, curve_points, anchor_display)
    return outside, occupied_overlap, legend_overlap, curve_overlap


def _annotation_rank_score(
    axis,
    candidate_box,
    offset: tuple[int, int],
    *,
    x: float,
    role: str,
    inverted: bool,
    curve_points: list[tuple[float, float]],
) -> float:
    dx, dy = offset
    score = 0.0

    x0, x1 = axis.get_xlim()
    span = x1 - x0
    x_fraction = 0.5 if span == 0 else (x - x0) / span
    if x_fraction <= 0.10 and dx <= 0:
        score += 200_000.0
    if x_fraction >= 0.90 and dx >= 0:
        score += 200_000.0

    visually_above = _visual_above_for_role(role, inverted)
    if (dy > 0) != visually_above:
        score += 2_500.0

    score += 0.08 * math.hypot(dx, dy)
    return score


def _annotation_fallback_score(
    rank_score: float,
    outside: float,
    occupied_overlap: float,
    legend_overlap: float,
    curve_overlap: int,
) -> float:
    score = rank_score
    if outside > 0:
        score += 1_000_000.0 + 10_000.0 * outside
    if occupied_overlap > 0:
        score += 500_000.0 + 100.0 * occupied_overlap
    if legend_overlap > 0:
        score += 400_000.0 + 100.0 * legend_overlap
    if curve_overlap > 0:
        score += 600_000.0 + 10_000.0 * curve_overlap
    return score


def _place_annotation(
    annotation,
    axis,
    x: float,
    *,
    role: str,
    inverted: bool,
    occupied_boxes: list,
) -> None:
    figure = axis.figure
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    axes_box = axis.get_window_extent(renderer)
    legend = axis.get_legend()
    legend_box = None if legend is None else legend.get_window_extent(renderer).expanded(1.03, 1.08)
    curve_points = _curve_display_points(axis)
    anchor_display = tuple(float(value) for value in axis.transData.transform(annotation.xy))

    valid_candidates = []
    fallback_candidates = []
    for order, offset in enumerate(_ANNOTATION_CANDIDATES):
        ha, va = _annotation_alignment(offset)
        annotation.set_position(offset)
        annotation.set_ha(ha)
        annotation.set_va(va)
        candidate_box = _annotation_box(annotation, renderer).expanded(
            _CALLOUT_CLEARANCE_X,
            _CALLOUT_CLEARANCE_Y,
        )
        outside, occupied_overlap, legend_overlap, curve_overlap = _candidate_constraints(
            candidate_box,
            occupied_boxes,
            axes_box,
            legend_box,
            curve_points,
            anchor_display,
        )
        rank_score = _annotation_rank_score(
            axis,
            candidate_box,
            offset,
            x=x,
            role=role,
            inverted=inverted,
            curve_points=curve_points,
        )
        fallback_score = _annotation_fallback_score(
            rank_score,
            outside,
            occupied_overlap,
            legend_overlap,
            curve_overlap,
        )
        fallback_candidates.append((fallback_score, order, offset))
        if outside <= 0 and occupied_overlap <= 0 and legend_overlap <= 0 and curve_overlap == 0:
            valid_candidates.append((rank_score, order, offset))

    _, _, best_offset = min(valid_candidates or fallback_candidates)
    ha, va = _annotation_alignment(best_offset)
    annotation.set_position(best_offset)
    annotation.set_ha(ha)
    annotation.set_va(va)
    occupied_boxes.append(
        _annotation_box(annotation, renderer).expanded(
            _CALLOUT_CLEARANCE_X,
            _CALLOUT_CLEARANCE_Y,
        )
    )


def _annotate_characteristic(
    axis,
    x_quantity,
    y_quantity,
    response_label: str,
    *,
    role: str,
    inverted: bool,
    line_color,
    occupied_boxes: list,
    x_symbolic=None,
    exponents: tuple[bool, bool] = (False, False),
) -> None:
    x = float(x_quantity.magnitude)
    y = float(y_quantity.magnitude)
    text = _coordinate_label(x, y, x_symbolic, exponents=exponents)
    annotation = _create_annotation(axis, text, x, y, _ANNOTATION_CANDIDATES[0], line_color)
    _place_annotation(
        annotation,
        axis,
        x,
        role=role,
        inverted=inverted,
        occupied_boxes=occupied_boxes,
    )


def _style_axes(axis) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.set_axisbelow(True)
    axis.grid(True, which="major", alpha=0.22)
    # When the ticks share a power of ten matplotlib puts it in the corner and spells it
    # `1e6`, which is programmer notation and appears nowhere else in a memoria - two
    # centimetres above an annotation on the same axis reading `1.97×10⁶`, and below a
    # table reading `1.87 × 10⁶`. This changes the spelling only; whether an offset
    # appears at all is matplotlib's decision from the data, unchanged.
    axis.ticklabel_format(useMathText=True)


def _segment_slices(series: PlotSeries, count: int) -> tuple[tuple[int, int], ...]:
    starts = (0, *series.segment_starts)
    stops = (*series.segment_starts, count)
    return tuple((start, stop) for start, stop in zip(starts, stops) if stop > start)


def _plot_segmented_line(
    axis, x_values, y_values, series: PlotSeries, *, linewidth: float,
    zorder: int, label=None, alpha: float | None = None, color=None,
):
    first_line = None
    line_color = color
    for segment_index, (start, stop) in enumerate(_segment_slices(series, len(x_values))):
        kwargs = {
            "linewidth": linewidth,
            "zorder": zorder,
            "label": label if segment_index == 0 else "_nolegend_",
        }
        if alpha is not None:
            kwargs["alpha"] = alpha
        if line_color is not None:
            kwargs["color"] = line_color
        line = axis.plot(x_values[start:stop], y_values[start:stop], **kwargs)[0]
        if first_line is None:
            first_line = line
            line_color = line.get_color()
    return first_line


def _fill_segmented_between(
    axis, x_values, lower_values, upper_values, series: PlotSeries, *,
    color, alpha: float, zorder: int,
):
    for start, stop in _segment_slices(series, len(x_values)):
        axis.fill_between(
            x_values[start:stop],
            lower_values[start:stop] if hasattr(lower_values, "__getitem__") else lower_values,
            upper_values[start:stop] if hasattr(upper_values, "__getitem__") else upper_values,
            color=color, alpha=alpha, zorder=zorder,
        )


def _render_single_series(figure, axis, result: PlotResult) -> None:
    exponents = _annotation_exponents(result)
    series = result.series[0]
    x_values = [float(value.magnitude) for value in result.x_values]
    y_values = [float(value.magnitude) for value in series.y_values]
    line = _plot_segmented_line(
        axis, x_values, y_values, series, linewidth=2.2, zorder=3
    )
    line_color = line.get_color()
    _fill_segmented_between(
        axis, x_values, y_values, 0.0, series,
        color=line_color, alpha=0.12, zorder=1,
    )
    axis.axhline(0.0, linewidth=1.0, color=axis.spines["bottom"].get_edgecolor(), alpha=0.75, zorder=2)

    requests = _characteristic_requests(result)
    marker_points: dict[tuple[float, float], tuple[float, float, int]] = {}
    for index in (0, len(x_values) - 1):
        key = (round(x_values[index], 12), round(y_values[index], 12))
        marker_points[key] = (x_values[index], y_values[index], 20)
    for request in requests:
        x = float(request.x_quantity.magnitude)
        y = float(request.y_quantity.magnitude)
        key = (round(x, 12), round(y, 12))
        marker_points[key] = (x, y, 32)
    axis.scatter(
        [point[0] for point in marker_points.values()],
        [point[1] for point in marker_points.values()],
        s=[point[2] for point in marker_points.values()],
        color=line_color,
        zorder=4,
    )

    inverted = series.is_moment
    if inverted:
        axis.invert_yaxis()
    axis.set_xlabel(_axis_label(result.variable, result.x_values[0]))
    axis.set_ylabel(_axis_label(result.display_label, series.y_values[0]))
    axis.set_title(result.display_label, pad=10, fontweight=700)
    _style_axes(axis)
    axis.margins(x=0.02, y=_PLOT_Y_MARGIN)
    figure.tight_layout()

    occupied_boxes: list = []
    for request in requests:
        _annotate_characteristic(
            axis,
            request.x_quantity,
            request.y_quantity,
            request.response_label,
            role=request.role,
            inverted=request.inverted,
            line_color=line_color,
            occupied_boxes=occupied_boxes,
            x_symbolic=request.x_symbolic,
            exponents=exponents,
        )

def _render_multi_series(figure, axis, result: PlotResult) -> None:
    exponents = _annotation_exponents(result)
    x_values = [float(value.magnitude) for value in result.x_values]
    requests = _characteristic_requests(result)
    requests_by_series = {
        series_index: tuple(item for item in requests if item.series_index == series_index)
        for series_index in range(len(result.series))
    }
    line_colors: dict[int, Any] = {}

    for series_index, series in enumerate(result.series):
        y_values = [float(value.magnitude) for value in series.y_values]
        line = _plot_segmented_line(
            axis, x_values, y_values, series, linewidth=2.0,
            label=series.display_label, zorder=3,
        )
        line_colors[series_index] = line.get_color()
        series_requests = requests_by_series[series_index]
        axis.scatter(
            [float(item.x_quantity.magnitude) for item in series_requests],
            [float(item.y_quantity.magnitude) for item in series_requests],
            s=26,
            color=line_colors[series_index],
            zorder=4,
        )

    axis.axhline(0.0, linewidth=1.0, color=axis.spines["bottom"].get_edgecolor(), alpha=0.75, zorder=2)
    axis.legend(loc="upper right")
    moment = all(series.is_moment for series in result.series)
    if moment:
        axis.invert_yaxis()
    axis.set_xlabel(_axis_label(result.variable, result.x_values[0]))
    axis.set_ylabel(_axis_label(result.display_label, result.series[0].y_values[0]))
    axis.set_title(result.display_label, pad=10, fontweight=700)
    _style_axes(axis)
    axis.margins(x=0.02, y=_PLOT_Y_MARGIN)
    figure.tight_layout()

    occupied_boxes: list = []
    for request in requests:
        _annotate_characteristic(
            axis,
            request.x_quantity,
            request.y_quantity,
            request.response_label,
            role=request.role,
            inverted=request.inverted,
            line_color=line_colors[request.series_index],
            occupied_boxes=occupied_boxes,
            x_symbolic=request.x_symbolic,
            exponents=exponents,
        )


def _render_envelope_sources(axis, result: PlotResult, x_values):
    for source_series in result.source_series:
        source_y = [float(value.magnitude) for value in source_series.y_values]
        _plot_segmented_line(
            axis, x_values, source_y, source_series, linewidth=1.0,
            alpha=0.22, label="_nolegend_", zorder=1,
        )


def _render_signed_envelope(figure, axis, result: PlotResult) -> None:
    exponents = _annotation_exponents(result)
    x_values = [float(value.magnitude) for value in result.x_values]
    _render_envelope_sources(axis, result, x_values)
    maximum_series, minimum_series = result.series
    maximum_y = [float(value.magnitude) for value in maximum_series.y_values]
    minimum_y = [float(value.magnitude) for value in minimum_series.y_values]
    maximum_line = _plot_segmented_line(
        axis, x_values, maximum_y, maximum_series,
        linewidth=2.5, alpha=1.0, label=maximum_series.display_label, zorder=4,
    )
    minimum_line = _plot_segmented_line(
        axis, x_values, minimum_y, minimum_series,
        linewidth=2.5, alpha=1.0, label=minimum_series.display_label, zorder=4,
    )
    _fill_segmented_between(
        axis, x_values, minimum_y, maximum_y, maximum_series,
        color=maximum_line.get_color(), alpha=0.10, zorder=2,
    )
    axis.axhline(
        0.0,
        linewidth=1.0,
        color=axis.spines["bottom"].get_edgecolor(),
        alpha=0.75,
        label="_zero",
        zorder=3,
    )
    axis.legend(handles=[maximum_line, minimum_line], loc="upper right")

    maximum_index = max(range(len(maximum_y)), key=maximum_y.__getitem__)
    minimum_index = min(range(len(minimum_y)), key=minimum_y.__getitem__)
    coincident_extrema = (
        maximum_index == minimum_index
        and math.isclose(
            maximum_y[maximum_index],
            minimum_y[minimum_index],
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
    )
    marker_indices = [(maximum_index, maximum_y[maximum_index], maximum_line.get_color())]
    if not coincident_extrema:
        marker_indices.append((minimum_index, minimum_y[minimum_index], minimum_line.get_color()))
    axis.scatter(
        [x_values[index] for index, _, _ in marker_indices],
        [value for _, value, _ in marker_indices],
        s=[30] * len(marker_indices),
        color=[color for _, _, color in marker_indices],
        zorder=5,
    )

    moment = maximum_series.is_moment
    if moment:
        axis.invert_yaxis()
    axis.set_xlabel(_axis_label(result.variable, result.x_values[0]))
    axis.set_ylabel(_axis_label(result.display_label, maximum_series.y_values[0]))
    axis.set_title(f"{result.display_label} envelope", pad=10, fontweight=700)
    _style_axes(axis)
    axis.margins(x=0.02, y=_PLOT_Y_MARGIN)
    figure.tight_layout()

    occupied_boxes: list = []
    response_label = _response_symbol(result.display_label)
    _annotate_characteristic(
        axis,
        result.x_values[maximum_index],
        maximum_series.y_values[maximum_index],
        response_label,
        role="max",
        inverted=moment,
        line_color=maximum_line.get_color(),
        occupied_boxes=occupied_boxes,
        exponents=exponents,
    )
    if not coincident_extrema:
        _annotate_characteristic(
            axis,
            result.x_values[minimum_index],
            minimum_series.y_values[minimum_index],
            response_label,
            role="min",
            inverted=moment,
            line_color=minimum_line.get_color(),
            occupied_boxes=occupied_boxes,
            exponents=exponents,
        )


def _render_magnitude_envelope(figure, axis, result: PlotResult) -> None:
    exponents = _annotation_exponents(result)
    x_values = [float(value.magnitude) for value in result.x_values]
    _render_envelope_sources(axis, result, x_values)
    magnitude_series = result.series[0]
    magnitude_y = [float(value.magnitude) for value in magnitude_series.y_values]
    magnitude_line = _plot_segmented_line(
        axis, x_values, magnitude_y, magnitude_series,
        linewidth=2.5, alpha=1.0, label=magnitude_series.display_label, zorder=4,
    )
    _fill_segmented_between(
        axis, x_values, 0.0, magnitude_y, magnitude_series,
        color=magnitude_line.get_color(), alpha=0.10, zorder=2,
    )
    axis.axhline(
        0.0,
        linewidth=1.0,
        color=axis.spines["bottom"].get_edgecolor(),
        alpha=0.75,
        label="_zero",
        zorder=3,
    )
    axis.legend(handles=[magnitude_line], loc="upper right")

    maximum_index = max(range(len(magnitude_y)), key=magnitude_y.__getitem__)
    axis.scatter(
        [x_values[maximum_index]],
        [magnitude_y[maximum_index]],
        s=30,
        color=magnitude_line.get_color(),
        zorder=5,
    )

    moment = magnitude_series.is_moment
    if moment:
        axis.invert_yaxis()
    axis.set_xlabel(_axis_label(result.variable, result.x_values[0]))
    axis.set_ylabel(_axis_label(result.display_label, magnitude_series.y_values[0]))
    axis.set_title(f"|{result.display_label}| envelope", pad=10, fontweight=700)
    _style_axes(axis)
    axis.margins(x=0.02, y=_PLOT_Y_MARGIN)
    figure.tight_layout()

    response_label = f"|{_response_symbol(result.display_label)}|"
    _annotate_characteristic(
        axis,
        result.x_values[maximum_index],
        magnitude_series.y_values[maximum_index],
        response_label,
        role="max",
        inverted=moment,
        line_color=magnitude_line.get_color(),
        occupied_boxes=[],
        exponents=exponents,
    )


def _render_envelope(figure, axis, result: PlotResult) -> None:
    if result.envelope_mode == "magnitude":
        _render_magnitude_envelope(figure, axis, result)
    else:
        _render_signed_envelope(figure, axis, result)


def render_plot(result: PlotResult):
    """Create one closed Matplotlib figure from normalized EngCalc plot data."""
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots()
    if result.kind == "envelope":
        _render_envelope(figure, axis, result)
    elif len(result.series) == 1:
        _render_single_series(figure, axis, result)
    else:
        _render_multi_series(figure, axis, result)
    plt.close(figure)
    return figure
