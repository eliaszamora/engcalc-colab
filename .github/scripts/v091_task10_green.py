from pathlib import Path

MODELS = Path("src/engcalc_colab/models.py")
ENGINE = Path("src/engcalc_colab/engine.py")
PLOTTING = Path("src/engcalc_colab/plotting.py")

models = MODELS.read_text(encoding="utf-8")
engine = ENGINE.read_text(encoding="utf-8")
plotting = PLOTTING.read_text(encoding="utf-8")

if "characteristics: tuple[CharacteristicPoint, ...]" in models:
    raise SystemExit("Task 10 plot characteristics already present; guarded patch will not reapply")

# ---- models.py -----------------------------------------------------------
old = '''@dataclass(frozen=True)
class PlotSeries:
    display_label: str
    y_values: tuple[Any, ...]
    is_moment: bool
    segment_starts: tuple[int, ...] = ()
'''
new = '''@dataclass(frozen=True)
class PlotSeries:
    display_label: str
    y_values: tuple[Any, ...]
    is_moment: bool
    segment_starts: tuple[int, ...] = ()
    characteristics: tuple[CharacteristicPoint, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "y_values", tuple(self.y_values))
        object.__setattr__(self, "segment_starts", tuple(self.segment_starts))
        object.__setattr__(self, "characteristics", tuple(self.characteristics))
'''
if old not in models:
    raise SystemExit("Task 10 PlotSeries anchor not found")
models = models.replace(old, new, 1)

# ---- engine.py -----------------------------------------------------------
old = "from dataclasses import dataclass\n"
new = "from dataclasses import dataclass, replace\n"
if old not in engine:
    raise SystemExit("Task 10 dataclasses import anchor not found")
engine = engine.replace(old, new, 1)

old = '''from .models import (
    EigenvalueEntry,
'''
new = '''from .models import (
    CharacteristicPoint,
    EigenvalueEntry,
'''
if old not in engine:
    raise SystemExit("Task 10 model import anchor not found")
engine = engine.replace(old, new, 1)

marker = '''    def _evaluate_plot(self, node: ast.Call):
'''
helper = '''    def _plot_characteristics(
        self,
        expression,
        variable: str,
        domain,
        *,
        source_label: str,
        overrides=None,
    ) -> tuple[CharacteristicPoint, ...]:
        points, _intervals, _up, _down, unresolved = solve_extrema_exact(
            expression,
            self.engine.resolve_symbol(variable),
            domain,
            self.engine.numeric_context,
            overrides=overrides,
            source_label=source_label,
        )
        if unresolved:
            raise EngEvaluationError(
                "plot characteristic analysis could not resolve a safe solution set"
            )
        return tuple(
            point
            for point in points
            if point.value_quantity is not None
            and any(role in {"global_max", "global_min"} for role in point.roles)
        )

'''
if engine.count(marker) != 1:
    raise SystemExit("Task 10 _evaluate_plot insertion anchor mismatch")
engine = engine.replace(marker, helper + marker, 1)

old = '''        start_quantity, end_quantity = self.engine.numeric_context.normalize_plot_bounds(
            start_quantity,
            end_quantity,
        )

        resolved_expressions = [
'''
new = '''        start_quantity, end_quantity = self.engine.numeric_context.normalize_plot_bounds(
            start_quantity,
            end_quantity,
        )
        analysis_domain = None
        if call_name == "plot":
            analysis_domain = normalize_analysis_domain(
                self.engine.numeric_context,
                start_expression,
                end_expression,
            )

        resolved_expressions = [
'''
if old not in engine:
    raise SystemExit("Task 10 analysis-domain anchor not found")
engine = engine.replace(old, new, 1)

old = '''                call_name=call_name,
                preserve_signed_source=(
                    call_name == "envelope" and expression.is_absolute
                ),
            )
'''
new = '''                call_name=call_name,
                preserve_signed_source=(
                    call_name == "envelope" and expression.is_absolute
                ),
                analysis_domain=analysis_domain,
            )
'''
if old not in engine:
    raise SystemExit("Task 10 sweep-call anchor not found")
engine = engine.replace(old, new, 1)

old = '''                source_segment_starts = self.engine.numeric_context.piecewise_segment_starts(
                    expression.signed_expression, variable, x_values
                )
                raw_series.append(
                    PlotSeries(
                        display_label=expression.display_label,
                        y_values=y_values,
                        is_moment=self._is_moment_label(expression.source_label),
                        segment_starts=segment_starts,
                    )
                )
'''
new = '''                source_segment_starts = self.engine.numeric_context.piecewise_segment_starts(
                    expression.signed_expression, variable, x_values
                )
                characteristics = ()
                if call_name == "plot":
                    characteristics = self._plot_characteristics(
                        expression.comparison_expression,
                        variable,
                        analysis_domain,
                        source_label=expression.display_label,
                    )
                raw_series.append(
                    PlotSeries(
                        display_label=expression.display_label,
                        y_values=y_values,
                        is_moment=self._is_moment_label(expression.source_label),
                        segment_starts=segment_starts,
                        characteristics=characteristics,
                    )
                )
'''
if old not in engine:
    raise SystemExit("Task 10 non-sweep series anchor not found")
engine = engine.replace(old, new, 1)

old = '''        *,
        call_name: str,
        preserve_signed_source: bool,
    ) -> tuple[list[PlotSeries], list[PlotSeries], tuple]:
'''
new = '''        *,
        call_name: str,
        preserve_signed_source: bool,
        analysis_domain,
    ) -> tuple[list[PlotSeries], list[PlotSeries], tuple]:
'''
if old not in engine:
    raise SystemExit("Task 10 sweep signature anchor not found")
engine = engine.replace(old, new, 1)

old = '''            source_segment_starts = self.engine.numeric_context.piecewise_segment_starts(
                signed_expression, variable, x_values, overrides=overrides
            )
            comparison_series.append(
                PlotSeries(
                    display_label=case_label,
                    y_values=comparison_y_values,
                    is_moment=is_moment,
                    segment_starts=segment_starts,
                )
            )
'''
new = '''            source_segment_starts = self.engine.numeric_context.piecewise_segment_starts(
                signed_expression, variable, x_values, overrides=overrides
            )
            characteristics = ()
            if call_name == "plot":
                characteristics = self._plot_characteristics(
                    comparison_expression,
                    variable,
                    analysis_domain,
                    source_label=case_label,
                    overrides=overrides,
                )
            comparison_series.append(
                PlotSeries(
                    display_label=case_label,
                    y_values=comparison_y_values,
                    is_moment=is_moment,
                    segment_starts=segment_starts,
                    characteristics=characteristics,
                )
            )
'''
if old not in engine:
    raise SystemExit("Task 10 sweep series anchor not found")
engine = engine.replace(old, new, 1)

old = '''        normalized: list[PlotSeries] = []
        for item in series:
            try:
                y_values = tuple(value.to(target_unit) for value in item.y_values)
            except DimensionalityError as exc:
                raise EngEvaluationError(
                    f"{call_name} series have incompatible y dimensions"
                ) from exc
            normalized.append(
                PlotSeries(
                    display_label=item.display_label,
                    y_values=y_values,
                    is_moment=item.is_moment,
                    segment_starts=item.segment_starts,
                )
            )
'''
new = '''        normalized: list[PlotSeries] = []
        for item in series:
            try:
                y_values = tuple(value.to(target_unit) for value in item.y_values)
                characteristics = tuple(
                    replace(
                        point,
                        value_quantity=(
                            None
                            if point.value_quantity is None
                            else point.value_quantity.to(target_unit)
                        ),
                    )
                    for point in item.characteristics
                )
            except DimensionalityError as exc:
                raise EngEvaluationError(
                    f"{call_name} series have incompatible y dimensions"
                ) from exc
            normalized.append(
                PlotSeries(
                    display_label=item.display_label,
                    y_values=y_values,
                    is_moment=item.is_moment,
                    segment_starts=item.segment_starts,
                    characteristics=characteristics,
                )
            )
'''
if old not in engine:
    raise SystemExit("Task 10 normalization anchor not found")
engine = engine.replace(old, new, 1)

# ---- plotting.py ---------------------------------------------------------
old = '''def _characteristic_requests(result: PlotResult) -> tuple[_CharacteristicRequest, ...]:
    inverted = all(series.is_moment for series in result.series)
    requests: list[_CharacteristicRequest] = []

    for series_index, series in enumerate(result.series):
        values = [float(value.magnitude) for value in series.y_values]
        maximum_index, minimum_index = _extreme_indices(values)
        response_label = _series_response_symbol(result, series)

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
'''
new = '''def _nearest_sample_index(result: PlotResult, x_quantity) -> int:
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
            for characteristic_role, request_role in (
                ("global_max", "max"),
                ("global_min", "min"),
            ):
                for point in series.characteristics:
                    if characteristic_role not in point.roles or point.value_quantity is None:
                        continue
                    x_quantity = point.x_quantity.to(x_unit)
                    y_quantity = point.value_quantity.to(y_unit)
                    requests.append(
                        _CharacteristicRequest(
                            series_index=series_index,
                            series=series,
                            sample_index=_nearest_sample_index(result, x_quantity),
                            x_quantity=x_quantity,
                            y_quantity=y_quantity,
                            response_label=response_label,
                            role=request_role,
                            inverted=inverted,
                        )
                    )
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
'''
if old not in plotting:
    raise SystemExit("Task 10 characteristic request anchor not found")
plotting = plotting.replace(old, new, 1)

start = plotting.find("def _render_single_series(figure, axis, result: PlotResult) -> None:\n")
end = plotting.find("\ndef _render_multi_series(figure, axis, result: PlotResult) -> None:\n")
if start < 0 or end < 0 or end <= start:
    raise SystemExit("Task 10 single-series renderer anchors not found")
new_single = '''def _render_single_series(figure, axis, result: PlotResult) -> None:
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
    axis.set_ylabel(_axis_label(result.display_label, series.y_values[0], moment=series.is_moment))
    axis.set_title(result.display_label, pad=10, fontweight="semibold")
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
        )
'''
plotting = plotting[:start] + new_single + plotting[end:]

old = '''        marker_indices = sorted({item.sample_index for item in requests_by_series[series_index]})
        axis.scatter(
            [x_values[index] for index in marker_indices],
            [y_values[index] for index in marker_indices],
            s=26,
            color=line_colors[series_index],
            zorder=4,
        )
'''
new = '''        series_requests = requests_by_series[series_index]
        axis.scatter(
            [float(item.x_quantity.magnitude) for item in series_requests],
            [float(item.y_quantity.magnitude) for item in series_requests],
            s=26,
            color=line_colors[series_index],
            zorder=4,
        )
'''
if old not in plotting:
    raise SystemExit("Task 10 multi-series marker anchor not found")
plotting = plotting.replace(old, new, 1)

MODELS.write_text(models, encoding="utf-8")
ENGINE.write_text(engine, encoding="utf-8")
PLOTTING.write_text(plotting, encoding="utf-8")
