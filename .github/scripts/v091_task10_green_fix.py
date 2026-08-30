from pathlib import Path

ENGINE = Path("src/engcalc_colab/engine.py")
PLOTTING = Path("src/engcalc_colab/plotting.py")

engine = ENGINE.read_text(encoding="utf-8")
plotting = PLOTTING.read_text(encoding="utf-8")

# The exact metadata path is presentation enrichment. A plot that the
# characteristic core cannot partition safely must retain the pre-0.9.1
# sampled presentation path rather than turning a previously valid plot into
# an evaluation error.
old = '''    def _plot_characteristics(
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
new = '''    def _plot_characteristics(
        self,
        expression,
        variable: str,
        domain,
        *,
        source_label: str,
        overrides=None,
    ) -> tuple[CharacteristicPoint, ...]:
        try:
            points, _intervals, _up, _down, unresolved = solve_extrema_exact(
                expression,
                self.engine.resolve_symbol(variable),
                domain,
                self.engine.numeric_context,
                overrides=overrides,
                source_label=source_label,
            )
        except (EngEvaluationError, TypeError, ValueError):
            return ()
        if unresolved:
            return ()
        return tuple(
            point
            for point in points
            if point.value_quantity is not None
            and any(role in {"global_max", "global_min"} for role in point.roles)
        )
'''
if old not in engine:
    raise SystemExit("Task 10 plot-characteristic compatibility anchor not found")
engine = engine.replace(old, new, 1)

# Preserve the historical presentation contract of at most one max and one
# min callout per series. The exact core may legitimately report multiple
# isolated points carrying the same global role (for example both zero-valued
# beam endpoints). The metadata remains complete; presentation chooses the
# first physically ordered authoritative point for each role.
old = '''        if result.kind == "plot" and series.characteristics:
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
'''
new = '''        if result.kind == "plot" and series.characteristics:
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
                    )
                )
            requests.extend(series_requests)
            continue
'''
if old not in plotting:
    raise SystemExit("Task 10 exact-request de-duplication anchor not found")
plotting = plotting.replace(old, new, 1)

ENGINE.write_text(engine, encoding="utf-8")
PLOTTING.write_text(plotting, encoding="utf-8")
