# EngCalc Dense Characteristic Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace visually rejected dense characteristic callouts with a compact, color-keyed characteristic summary below an unchanged-size EngCalc plot while preserving all engineering values and sparse inline behavior.

**Architecture:** `plotting.py` remains the engineering authority and gains one private characteristic-request sequence consumed by both rendering and presentation. `label_layout.py` remains presentation-only and converts only dense clusters into a compact secondary Matplotlib axes below the primary plot. The primary engineering axes stays `figure.axes[0]`, keeps its physical width/height, and no dense per-point leader lines remain.

**Tech Stack:** Python 3.13, Matplotlib/Agg, Pint quantities already used by EngCalc, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-30-engcalc-dense-characteristic-summary-design.md`

## Global Constraints

- Active branch: `feature/v0.8.0-characteristic-label-layout`.
- Package/runtime version remains `0.7.2`.
- Positive structural moment remains plotted downward.
- Sampling, extrema values, quantities, units, curve data, legend semantics, series colors, and public plot/envelope APIs must not change.
- Dense threshold remains `_DENSE_CLUSTER_SIZE = 3` and x clustering keeps `_CLUSTER_X_TOLERANCE_PX` semantics.
- Sparse clusters with fewer than 3 labels remain inline and baseline-sized.
- Figure width never increases.
- Primary axes physical width and height remain within ±1 px of baseline under Agg.
- The six-series summary adds less than the rejected 1.85 in of vertical height.
- Summary rows use exact `PlotSeries.display_label` and exact plotted-line colors.
- Dense leader lines are removed.
- x units appear once per dense-group header. A homogeneous y unit appears once per group value heading; heterogeneous-unit fallback may include the unit in each row value.
- No parser grammar, `PlotResult` public API, Piecewise, multiline-call parsing, `no_vertical_scroll()`, release/version bump, Codex invocation, or implicit merge is included.
- Production changes follow RED → GREEN; focused tests precede the complete suite.
- Do not merge without explicit user approval.

---

## File map

- `src/engcalc_colab/plotting.py`: private authoritative characteristic requests; multi-series renderer consumes them.
- `src/engcalc_colab/label_layout.py`: dense grouping and compact summary rendering; no extrema recomputation.
- `src/engcalc_colab/presentation.py`: unchanged public presentation entry point unless a private helper rename is required.
- `tests/test_characteristic_requests.py`: authoritative extrema/request regression.
- `tests/test_dense_characteristic_summary.py`: dense grouping semantics, ordering, colors, units.
- `tests/test_dense_characteristic_label_layout.py`: compact-summary geometry plus sparse regression.
- `tools/render_dense_characteristic_summary_qa.py`: temporary PNG/metrics harness.
- `.github/workflows/characteristic-label-validation.yml`: temporary full-suite + artifact workflow.
- `docs/project-context/CURRENT.md`: continuity state at every checkpoint.

---

### Task 1: Centralize characteristic requests in `plotting.py`

**Files:**
- Create: `tests/test_characteristic_requests.py`
- Modify: `src/engcalc_colab/plotting.py`
- Modify: `docs/project-context/CURRENT.md`

**Interfaces:**

```python
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


def _characteristic_requests(result: PlotResult) -> tuple[_CharacteristicRequest, ...]:
    ...
```

The body is specified in Step 3. `label_layout.py` consumes these private interfaces in Task 2.

- [ ] **Step 1: Write the failing authoritative-request test**

Create `tests/test_characteristic_requests.py` with imports:

```python
import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import _characteristic_requests
```

Use this exact fixture:

```python
def _eval_cell(engine, source: str):
    return [engine.evaluate(statement) for statement in parse_cell(source)]


def _dense_six_series_moment_plot():
    engine = EngineeringEngine()
    _eval_cell(engine, """
    L := 4*m
    A1 := -6*tonf*m
    C1 := 1.50*tonf/m
    B1 := 7.50*tonf
    A2 := -22.4*tonf*m
    C2 := 5.00*tonf/m
    B2 := 25.00*tonf
    A3 := -8*tonf*m
    C3 := 2.00*tonf/m
    B3 := 10.00*tonf
    A4 := -19.2*tonf*m
    C4 := 4.80*tonf/m
    B4 := 24.00*tonf
    A5 := -14*tonf*m
    C5 := 3.50*tonf/m
    B5 := 17.50*tonf
    A6 := -16*tonf*m
    C6 := 4.20*tonf/m
    B6 := 21.00*tonf
    M_C1(x) = A1 + B1*x - C1*x^2
    M_C2(x) = A2 + B2*x - C2*x^2
    M_S1(x) = A3 + B3*x - C3*x^2
    M_S2(x) = A4 + B4*x - C4*x^2
    M_S3(x) = A5 + B5*x - C5*x^2
    M_S4(x) = A6 + B6*x - C6*x^2
    """)
    return _eval_cell(
        engine,
        "plot(M_C1(x), M_C2(x), M_S1(x), M_S2(x), M_S3(x), M_S4(x), x, 0, L)",
    )[-1]
```

Add:

```python
def test_characteristic_requests_are_single_authoritative_sequence():
    requests = _characteristic_requests(_dense_six_series_moment_plot())

    assert len(requests) == 12
    assert [(item.series_index, item.role) for item in requests] == [
        (0, "max"), (0, "min"),
        (1, "max"), (1, "min"),
        (2, "max"), (2, "min"),
        (3, "max"), (3, "min"),
        (4, "max"), (4, "min"),
        (5, "max"), (5, "min"),
    ]
    assert [float(item.x_quantity.magnitude) for item in requests[::2]] == pytest.approx([2.5] * 6)
    assert [float(item.x_quantity.magnitude) for item in requests[1::2]] == pytest.approx([0.0] * 6)
    assert [float(item.y_quantity.magnitude) for item in requests[::2]] == pytest.approx(
        [3.375, 8.85, 4.5, 10.8, 7.875, 10.25]
    )
    assert [float(item.y_quantity.magnitude) for item in requests[1::2]] == pytest.approx(
        [-6.0, -22.4, -8.0, -19.2, -14.0, -16.0]
    )
    assert [item.series.display_label for item in requests[::2]] == [
        "M_C1(x)", "M_C2(x)", "M_S1(x)", "M_S2(x)", "M_S3(x)", "M_S4(x)"
    ]
    assert all(item.inverted for item in requests)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_characteristic_requests.py -q
```

Expected: import/collection failure because `_characteristic_requests` does not exist in `plotting.py`.

- [ ] **Step 3: Implement the authoritative private request sequence**

In `plotting.py`, import `dataclass`, `Any`, and `PlotSeries`, add the dataclass above, then implement:

```python
def _characteristic_requests(result: PlotResult) -> tuple[_CharacteristicRequest, ...]:
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
            values[maximum_index], values[minimum_index], rel_tol=1e-12, abs_tol=1e-12
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
```

- [ ] **Step 4: Refactor `_render_multi_series()` to use that sequence without changing presentation**

At the start of `_render_multi_series()`:

```python
requests = _characteristic_requests(result)
requests_by_series = {
    series_index: tuple(item for item in requests if item.series_index == series_index)
    for series_index in range(len(result.series))
}
line_colors: dict[int, Any] = {}
```

Change the series loop to `for series_index, series in enumerate(result.series):`. After creating the line:

```python
line_colors[series_index] = line.get_color()
series_requests = requests_by_series[series_index]
marker_indices = sorted({item.sample_index for item in series_requests})
```

Use the existing scatter call with those `marker_indices`. Remove the old `characteristics` tuple accumulation and the second extrema computation. After layout:

```python
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
    )
```

Do not refactor `_render_single_series()`.

- [ ] **Step 5: Verify GREEN and no renderer regression**

Run:

```bash
python -m pytest tests/test_characteristic_requests.py tests/test_plotting.py tests/test_plot_engine.py tests/test_dense_characteristic_label_layout.py -q
python -m pytest -q
```

Expected: all PASS. Record exact count/duration in `CURRENT.md`.

- [ ] **Step 6: Commit**

```bash
git add src/engcalc_colab/plotting.py tests/test_characteristic_requests.py docs/project-context/CURRENT.md
git commit -m "refactor: centralize characteristic requests"
```

---

### Task 2: Build dense-summary semantic groups

**Files:**
- Create: `tests/test_dense_characteristic_summary.py`
- Modify: `src/engcalc_colab/label_layout.py`
- Modify: `docs/project-context/CURRENT.md`

**Interfaces:**

```python
@dataclass(frozen=True)
class _DenseSummaryEntry:
    request: _CharacteristicRequest
    color: Any


@dataclass(frozen=True)
class _DenseSummaryGroup:
    x_quantity: Any
    entries: tuple[_DenseSummaryEntry, ...]
```

Produces `_build_dense_summary_groups(axis, result: PlotResult) -> tuple[_DenseSummaryGroup, ...]`.

- [ ] **Step 1: Write semantic RED tests**

Create `tests/test_dense_characteristic_summary.py`, repeat the exact fixture from Task 1 in this test file, and add:

```python
import pytest

from engcalc_colab.label_layout import _build_dense_summary_groups
from engcalc_colab.plotting import render_plot


def test_dense_summary_groups_preserve_series_order_roles_and_colors():
    result = _dense_six_series_moment_plot()
    figure = render_plot(result)
    axis = figure.axes[0]
    groups = _build_dense_summary_groups(axis, result)

    assert len(groups) == 2
    assert [float(group.x_quantity.magnitude) for group in groups] == pytest.approx([0.0, 2.5])
    assert [len(group.entries) for group in groups] == [6, 6]

    left, interior = groups
    expected_labels = ["M_C1(x)", "M_C2(x)", "M_S1(x)", "M_S2(x)", "M_S3(x)", "M_S4(x)"]
    assert [entry.request.series.display_label for entry in left.entries] == expected_labels
    assert [entry.request.series.display_label for entry in interior.entries] == expected_labels
    assert [entry.request.role for entry in left.entries] == ["min"] * 6
    assert [entry.request.role for entry in interior.entries] == ["max"] * 6

    line_colors = {line.get_label(): line.get_color() for line in axis.lines}
    for group in groups:
        for entry in group.entries:
            assert entry.color == line_colors[entry.request.series.display_label]

    keys = {
        (entry.request.series_index, entry.request.role)
        for group in groups
        for entry in group.entries
    }
    assert len(keys) == 12
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_dense_characteristic_summary.py -q
```

Expected: import/collection failure because `_build_dense_summary_groups` does not exist.

- [ ] **Step 3: Remove presentation-layer extrema duplication and add immutable summary types**

In `label_layout.py`:

```python
from dataclasses import dataclass
from typing import Any

from .plotting import _CharacteristicRequest, _characteristic_requests
```

Delete the local `_extreme_indices()` and local `_characteristic_requests()`. Add the two dataclasses exactly as specified above.

- [ ] **Step 4: Implement `_build_dense_summary_groups()` completely**

```python
def _build_dense_summary_groups(axis, result: PlotResult) -> tuple[_DenseSummaryGroup, ...]:
    requests = _characteristic_requests(result)
    positioned: list[tuple[float, _CharacteristicRequest]] = []

    for request in requests:
        x = float(request.x_quantity.magnitude)
        y = float(request.y_quantity.magnitude)
        display_x, _ = axis.transData.transform((x, y))
        positioned.append((float(display_x), request))

    positioned.sort(key=lambda item: item[0])
    clusters: list[list[tuple[float, _CharacteristicRequest]]] = []
    for item in positioned:
        if not clusters or abs(item[0] - clusters[-1][-1][0]) > _CLUSTER_X_TOLERANCE_PX:
            clusters.append([item])
        else:
            clusters[-1].append(item)

    role_order = {"max": 0, "min": 1}
    groups: list[_DenseSummaryGroup] = []
    for cluster in clusters:
        if len(cluster) < _DENSE_CLUSTER_SIZE:
            continue

        cluster_requests = [item[1] for item in cluster]
        cluster_requests.sort(
            key=lambda request: (request.series_index, role_order[request.role])
        )
        entries: list[_DenseSummaryEntry] = []
        for request in cluster_requests:
            color = _series_color(axis, request.series.display_label)
            if color is None:
                continue
            entries.append(_DenseSummaryEntry(request=request, color=color))

        if len(entries) >= _DENSE_CLUSTER_SIZE:
            groups.append(
                _DenseSummaryGroup(
                    x_quantity=entries[0].request.x_quantity,
                    entries=tuple(entries),
                )
            )

    groups.sort(key=lambda group: float(group.x_quantity.magnitude))
    return tuple(groups)
```

This preserves current display-space clustering while restoring series order inside each dense group.

- [ ] **Step 5: Keep the old bottom renderer temporarily compatible**

Until Task 4, adapt callout functions to access `request.x_quantity`, `request.y_quantity`, `request.role`, and `request.inverted`. Obtain the leader color through `_series_color(axis, request.series.display_label)`. The visible output remains the rejected bottom band at this checkpoint.

- [ ] **Step 6: Verify semantic GREEN plus old visual regression**

Run:

```bash
python -m pytest tests/test_dense_characteristic_summary.py tests/test_dense_characteristic_label_layout.py -q
python -m pytest -q
```

Expected: all PASS. Update `CURRENT.md` with exact evidence.

- [ ] **Step 7: Commit**

```bash
git add src/engcalc_colab/label_layout.py tests/test_dense_characteristic_summary.py docs/project-context/CURRENT.md
git commit -m "refactor: model dense characteristic groups"
```

---

### Task 3: Replace rejected callout tests with compact-summary RED contracts

**Files:**
- Modify: `tests/test_dense_characteristic_label_layout.py`
- Modify: `docs/project-context/CURRENT.md`

**Renderer identifiers:**

- summary axes: `engcalc-characteristic-summary`
- title: `engcalc-summary-title`
- group header: `engcalc-summary-group-header`
- entry label: `engcalc-summary-entry-label`
- entry role: `engcalc-summary-entry-role`
- entry value: `engcalc-summary-entry-value`

- [ ] **Step 1: Remove rejected bottom-callout contracts**

Delete rail-alignment, vertical-rail-clearance, leader-presence, and “all labels below axes” assertions. Keep the six-series fixture, sparse two-series fixture, baseline renderer, annotation collector, overlap helper, and ±1 px primary-axes tolerance.

- [ ] **Step 2: Add RED summary-surface contract**

```python
def _summary_axes(figure):
    return [
        axis for axis in figure.axes[1:]
        if axis.get_gid() == "engcalc-characteristic-summary"
    ]


def test_dense_characteristics_move_to_compact_summary():
    figure, axis, items, renderer = _render_dense_case()
    assert len(items) == 0
    assert len(_summary_axes(figure)) == 1

    summary = _summary_axes(figure)[0]
    assert len([t for t in summary.texts if t.get_gid() == "engcalc-summary-group-header"]) == 2
    assert len([t for t in summary.texts if t.get_gid() == "engcalc-summary-entry-label"]) == 12
    assert len([t for t in summary.texts if t.get_gid() == "engcalc-summary-entry-role"]) == 12
    assert len([t for t in summary.texts if t.get_gid() == "engcalc-summary-entry-value"]) == 12
```

- [ ] **Step 3: Add RED geometry contract**

```python
def test_dense_summary_preserves_primary_plot_size_and_is_compact():
    result = _dense_six_series_moment_plot()
    baseline_figure, baseline_axis, baseline_renderer = _render_baseline(result)
    baseline_box = baseline_axis.get_window_extent(baseline_renderer)

    figure, axis, _, renderer = _render(result)
    box = axis.get_window_extent(renderer)

    assert figure.get_figwidth() == baseline_figure.get_figwidth()
    assert abs(float(box.width) - float(baseline_box.width)) <= 1.0
    assert abs(float(box.height) - float(baseline_box.height)) <= 1.0
    added_height = figure.get_figheight() - baseline_figure.get_figheight()
    assert 0.0 < added_height < 1.85
```

- [ ] **Step 4: Add RED containment/collision contract**

Collect texts whose gid starts with `engcalc-summary-`. Assert every bbox lies inside `figure.bbox`. For different logical rows, assert pairwise rectangle intersection area equals zero. Exclude comparisons among label/role/value texts belonging to the same row by grouping them in creation order: 12 labels, 12 roles, 12 values; row `i` consists of index `i` from each list.

Use:

```python
def _overlap_area(left, right):
    width = max(0.0, min(left.x1, right.x1) - max(left.x0, right.x0))
    height = max(0.0, min(left.y1, right.y1) - max(left.y0, right.y0))
    return width * height
```

- [ ] **Step 5: Preserve sparse regression**

The sparse fixture must still assert:

```python
assert len(items) == 4
assert len(_summary_axes(figure)) == 0
assert all(item.arrow_patch is None for item in items)
assert figure.get_figwidth() == matplotlib.rcParams["figure.figsize"][0]
assert figure.get_figheight() == matplotlib.rcParams["figure.figsize"][1]
```

Keep the existing within-main-axes bbox assertion for those four annotations.

- [ ] **Step 6: Verify intentional RED and commit tests only**

Run:

```bash
python -m pytest tests/test_dense_characteristic_label_layout.py -q
```

Expected: compact-summary dense tests FAIL against the old bottom band; sparse test PASS. Record exact failures/count in `CURRENT.md`.

Commit:

```bash
git add tests/test_dense_characteristic_label_layout.py docs/project-context/CURRENT.md
git commit -m "test: specify compact characteristic summary"
```

---

### Task 4: Implement compact summary rendering GREEN

**Files:**
- Modify: `src/engcalc_colab/label_layout.py`
- Modify: `src/engcalc_colab/presentation.py` only if private integration naming changes.
- Modify: `tests/test_dense_characteristic_summary.py` for unit-format assertions.
- Modify: `docs/project-context/CURRENT.md`

**Interfaces:** one secondary axes with `gid="engcalc-characteristic-summary"`; `render_presented_plot(result)` signature unchanged.

- [ ] **Step 1: Delete rejected callout-only implementation**

Remove `_MIN_BOTTOM_SPACE_IN`, `_BOTTOM_SPACE_PER_LABEL_IN`, `_BOTTOM_SPACE_PADDING_IN`, `_BAND_EDGE_MARGIN_PX`, `_RAIL_VERTICAL_GAP_PX`, `_LEADER_LINEWIDTH`, `_LEADER_ALPHA`, `_stack_vertical_centers()`, `_create_bottom_callout()`, and `_layout_bottom_cluster()`. Remove `_text_box()` if no production caller remains.

Rename `_reserve_bottom_space()` to `_reserve_summary_space()` without changing its proven physical-axis preservation formula.

- [ ] **Step 2: Add compact sizing constants and a complete height function**

```python
_SUMMARY_MAX_COLUMNS = 2
_SUMMARY_TITLE_HEIGHT_IN = 0.18
_SUMMARY_GROUP_HEADER_HEIGHT_IN = 0.16
_SUMMARY_ROW_HEIGHT_IN = 0.14
_SUMMARY_PANEL_PADDING_IN = 0.08
_SUMMARY_GROUP_GAP_FRACTION = 0.05


def _summary_height_inches(groups: tuple[_DenseSummaryGroup, ...]) -> float:
    grid_rows = [
        groups[index:index + _SUMMARY_MAX_COLUMNS]
        for index in range(0, len(groups), _SUMMARY_MAX_COLUMNS)
    ]
    body_height = sum(
        _SUMMARY_GROUP_HEADER_HEIGHT_IN
        + _SUMMARY_ROW_HEIGHT_IN * max(len(group.entries) for group in grid_row)
        for grid_row in grid_rows
    )
    return (
        2 * _SUMMARY_PANEL_PADDING_IN
        + _SUMMARY_TITLE_HEIGHT_IN
        + body_height
    )
```

The canonical two-group/six-row fixture computes to 1.18 in.

- [ ] **Step 3: Add exact x/y unit formatting helpers**

Import `_compact_number`, `_quantity_label`, and `_unit_label` from `.plotting`.

```python
def _group_x_header(group: _DenseSummaryGroup) -> str:
    quantity = group.x_quantity
    value = _compact_number(float(quantity.magnitude))
    unit = _unit_label(quantity)
    return f"x = {value}" if not unit else f"x = {value} {unit}"


def _common_y_unit(
    groups: tuple[_DenseSummaryGroup, ...], *, moment: bool
) -> str | None:
    units = {
        _unit_label(entry.request.y_quantity, moment=moment)
        for group in groups
        for entry in group.entries
    }
    return next(iter(units)) if len(units) == 1 else None


def _entry_value_text(entry: _DenseSummaryEntry, *, moment: bool, common_unit: str | None) -> str:
    if common_unit is not None:
        return _compact_number(float(entry.request.y_quantity.magnitude))
    return _quantity_label(entry.request.y_quantity, moment=moment)
```

- [ ] **Step 4: Add a secondary axes in the newly reserved vertical space**

After `_reserve_summary_space()`, compute:

```python
figure_width, figure_height = (float(value) for value in figure.get_size_inches())
main_position = axis.get_position()
panel_bottom_in = _SUMMARY_PANEL_PADDING_IN
panel_height_in = summary_height_in - 2 * _SUMMARY_PANEL_PADDING_IN
summary = figure.add_axes(
    [
        float(main_position.x0),
        panel_bottom_in / figure_height,
        float(main_position.width),
        panel_height_in / figure_height,
    ]
)
summary.set_gid("engcalc-characteristic-summary")
summary.set_xlim(0.0, 1.0)
summary.set_ylim(0.0, 1.0)
summary.set_axis_off()
```

Because figure width is unchanged and `main_position.x0/width` are retained by `_reserve_summary_space()`, the panel aligns with the engineering plot without shrinking it.

- [ ] **Step 5: Implement deterministic summary coordinates**

Use two columns maximum. Define:

```python
def _summary_grid_rows(groups: tuple[_DenseSummaryGroup, ...]):
    return tuple(
        groups[index:index + _SUMMARY_MAX_COLUMNS]
        for index in range(0, len(groups), _SUMMARY_MAX_COLUMNS)
    )
```

Inside `_render_summary_panel()`:

```python
def _render_summary_panel(figure, axis, groups, *, summary_height_in: float):
    moment = all(series.is_moment for series in groups[0].entries[0].request.series.__class__.__mro__[:0])
```

Do **not** use that line; compute `moment` from the plot result at the call site and pass it as a keyword argument. The actual signature must be:

```python
def _render_summary_panel(
    figure,
    axis,
    groups: tuple[_DenseSummaryGroup, ...],
    *,
    summary_height_in: float,
    moment: bool,
) -> None:
```

Create the axes exactly as Step 4 specifies. Then render the title:

```python
title = summary.text(
    0.0, 0.98, "Characteristic points",
    transform=summary.transAxes,
    ha="left", va="top", fontsize=8.5, fontweight="semibold",
)
title.set_gid("engcalc-summary-title")
```

For each grid row, allocate equal-width cells. With `column_count = len(grid_row)`:

```python
cell_width = (1.0 - _SUMMARY_GROUP_GAP_FRACTION * (column_count - 1)) / column_count
```

For each group at `column_index`, compute:

```python
cell_left = column_index * (cell_width + _SUMMARY_GROUP_GAP_FRACTION)
cell_right = cell_left + cell_width
marker_x = cell_left + 0.015 * cell_width
label_x = cell_left + 0.055 * cell_width
role_x = cell_left + 0.57 * cell_width
value_x = cell_right
```

Use physical row heights converted to panel fractions:

```python
panel_height_in = summary_height_in - 2 * _SUMMARY_PANEL_PADDING_IN
title_fraction = _SUMMARY_TITLE_HEIGHT_IN / panel_height_in
group_header_fraction = _SUMMARY_GROUP_HEADER_HEIGHT_IN / panel_height_in
row_fraction = _SUMMARY_ROW_HEIGHT_IN / panel_height_in
```

Initialize `cursor_y = 1.0 - title_fraction`. For each grid row, render all group headers at `cursor_y`, then decrement by `group_header_fraction`. Render row index `row_index` at `cursor_y - (row_index + 0.5) * row_fraction`. After the maximum entry count in that grid row, decrement `cursor_y` by `max_entries * row_fraction`.

For each group header:

```python
header = summary.text(
    cell_left, cursor_y, _group_x_header(group),
    transform=summary.transAxes,
    ha="left", va="top", fontsize=8.2, fontweight="semibold",
)
header.set_gid("engcalc-summary-group-header")
```

If `common_unit` is not `None`, render `f"Value [{common_unit}]"` at `cell_right`, right-aligned, with fontsize 7.8. If it is `None`, render `"Value"`.

For each entry row:

```python
summary.plot(
    [marker_x], [row_y],
    marker="o", markersize=4.0, linestyle="None",
    color=entry.color, transform=summary.transAxes, clip_on=False,
)
label = summary.text(
    label_x, row_y, entry.request.series.display_label,
    transform=summary.transAxes,
    ha="left", va="center", fontsize=8.0, color=entry.color,
)
label.set_gid("engcalc-summary-entry-label")
role = summary.text(
    role_x, row_y, entry.request.role,
    transform=summary.transAxes,
    ha="left", va="center", fontsize=7.8,
)
role.set_gid("engcalc-summary-entry-role")
value = summary.text(
    value_x, row_y,
    _entry_value_text(entry, moment=moment, common_unit=common_unit),
    transform=summary.transAxes,
    ha="right", va="center", fontsize=8.0,
)
value.set_gid("engcalc-summary-entry-value")
```

Draw only one light separator below each group header using `summary.plot([cell_left, cell_right], [separator_y, separator_y], linewidth=0.6, alpha=0.35, transform=summary.transAxes)`. Do not draw a cell grid.

- [ ] **Step 6: Rewrite dense reflow around the summary groups**

```python
def reflow_dense_characteristic_labels(figure, result: PlotResult) -> None:
    if result.kind != "plot" or len(result.series) < 2:
        return

    axis = figure.axes[0]
    groups = _build_dense_summary_groups(axis, result)
    if not groups:
        return

    dense_requests = tuple(
        entry.request for group in groups for entry in group.entries
    )
    _remove_dense_inline_annotations(axis, dense_requests)
    summary_height_in = _summary_height_inches(groups)
    _reserve_summary_space(figure, axis, summary_height_in)
    _render_summary_panel(
        figure,
        axis,
        groups,
        summary_height_in=summary_height_in,
        moment=all(series.is_moment for series in result.series),
    )
```

Update `_request_matches_annotation()` to use `request.x_quantity` and `request.y_quantity`. No dense summary path may create an `Annotation` or `arrow_patch`.

- [ ] **Step 7: Add formatting assertions**

In `tests/test_dense_characteristic_summary.py`, after rendering `render_presented_plot(result)`, assert group headers contain `x = 0 m` and `x = 2.5 m` (allow the exact compact numeric formatting already used by `_compact_number`). Assert no entry value string contains `tonf` when the common unit header contains `tonf·m`.

- [ ] **Step 8: Verify focused GREEN and complete GREEN**

Run:

```bash
python -m pytest tests/test_characteristic_requests.py tests/test_dense_characteristic_summary.py tests/test_dense_characteristic_label_layout.py tests/test_plotting.py tests/test_plot_presentation_options.py -q
python -m pytest -q
```

Expected: all PASS. Record exact count/duration in `CURRENT.md`.

- [ ] **Step 9: Commit**

```bash
git add src/engcalc_colab/label_layout.py tests/test_dense_characteristic_summary.py docs/project-context/CURRENT.md
git add src/engcalc_colab/presentation.py  # only when actually changed
git commit -m "feat: render compact characteristic summary"
```

If `presentation.py` did not change, do not stage it.

---

### Task 5: Produce reproducible PNG + metrics and inspect visually

**Files:**
- Create temporarily: `tools/render_dense_characteristic_summary_qa.py`
- Modify temporarily: `.github/workflows/characteristic-label-validation.yml`
- Modify: `docs/project-context/CURRENT.md`

**Artifact:** `engcalc-characteristic-summary-qa` containing `dense_characteristic_summary.png` and `dense_characteristic_summary_metrics.json`.

- [ ] **Step 1: Create the deterministic QA script**

The script must:

1. call `matplotlib.use("Agg")` before importing pyplot/backend consumers;
2. rebuild the exact six-series definitions from Task 1 verbatim;
3. render `baseline_figure = render_plot(result)` and `figure = render_presented_plot(result)`;
4. create `FigureCanvasAgg` for both and call `draw()`;
5. identify the summary axes by gid;
6. collect summary text bboxes and count pairwise overlaps only across different logical rows/headers;
7. save `dense_characteristic_summary.png` with `figure.savefig(..., dpi=160, bbox_inches=None)`;
8. write JSON using only Python `float`, `int`, and `bool` values; never emit Base64/image bytes to logs.

Use this metric schema:

```python
metrics = {
    "baseline_figure_inches": [float(v) for v in baseline_figure.get_size_inches()],
    "presented_figure_inches": [float(v) for v in figure.get_size_inches()],
    "baseline_axes_px": [float(baseline_box.width), float(baseline_box.height)],
    "presented_axes_px": [float(main_box.width), float(main_box.height)],
    "dense_group_count": int(len(groups)),
    "summary_entry_count": int(sum(len(group.entries) for group in groups)),
    "summary_text_overlap_count": int(overlap_count),
    "all_summary_text_inside_figure": bool(contained),
    "dense_main_axis_annotation_count": int(len(dense_annotations)),
    "dense_leader_count": int(leader_count),
}
```

Hard assertions:

```python
assert metrics["dense_group_count"] == 2
assert metrics["summary_entry_count"] == 12
assert metrics["summary_text_overlap_count"] == 0
assert metrics["all_summary_text_inside_figure"] is True
assert metrics["dense_main_axis_annotation_count"] == 0
assert metrics["dense_leader_count"] == 0
assert abs(metrics["presented_axes_px"][0] - metrics["baseline_axes_px"][0]) <= 1.0
assert abs(metrics["presented_axes_px"][1] - metrics["baseline_axes_px"][1]) <= 1.0
assert metrics["presented_figure_inches"][0] == metrics["baseline_figure_inches"][0]
added_height = metrics["presented_figure_inches"][1] - metrics["baseline_figure_inches"][1]
assert 0.0 < added_height < 1.85
```

- [ ] **Step 2: Extend the temporary branch workflow after the full-suite step**

Append exactly:

```yaml
      - name: Render dense characteristic summary QA
        run: python tools/render_dense_characteristic_summary_qa.py
      - name: Upload dense characteristic summary QA
        uses: actions/upload-artifact@v4
        with:
          name: engcalc-characteristic-summary-qa
          path: |
            dense_characteristic_summary.png
            dense_characteristic_summary_metrics.json
```

Keep the existing Python 3.13 setup and `python -m pytest -q` gate unchanged.

- [ ] **Step 3: Commit temporary QA harness**

```bash
git add tools/render_dense_characteristic_summary_qa.py .github/workflows/characteristic-label-validation.yml docs/project-context/CURRENT.md
git commit -m "ci: capture characteristic summary visual qa"
```

The push triggers the workflow.

- [ ] **Step 4: Require machine evidence before visual inspection**

Require full suite PASS, render step PASS, artifact present, and every hard metric assertion PASS. Record the workflow run/job/artifact IDs and validated SHA in `CURRENT.md`.

- [ ] **Step 5: Inspect the actual PNG before showing it to the user**

Assistant visual checklist:

- primary plot visibly retains baseline width/scale;
- positive moment remains downward;
- legend/title/axis labels are untouched;
- summary is materially more compact than the rejected 6.65 in figure;
- two groups are visually distinct;
- six rows in each group are aligned;
- series identity through color/label is immediate;
- no clipping, collision, leader lines, or spreadsheet-like heavy grid appears.

If any item fails, return to Task 4, modify presentation only, rerun focused/full tests, then regenerate the artifact. Do not ask the user to approve a PNG that fails assistant inspection.

- [ ] **Step 6: Present validated evidence to the user**

Report validated SHA, full-suite count/duration, figure dimensions, main-axes pixel dimensions, 2 groups, 12 entries, overlap count, containment status, and leader count. Show the PNG and request visual acceptance. Do not merge or remove QA evidence before acceptance.

---

### Task 6: Clean temporary QA after user acceptance and stop at merge gate

**Files:**
- Delete: `tools/render_dense_characteristic_summary_qa.py`
- Delete: `.github/workflows/characteristic-label-validation.yml`
- Modify: `docs/project-context/CURRENT.md`

- [ ] **Step 1: Preserve accepted evidence in context**

Record accepted validated SHA, source-suite evidence, workflow run/job/artifact IDs, and the user visual-acceptance decision in `CURRENT.md`.

- [ ] **Step 2: Remove task-specific QA files**

```bash
git rm tools/render_dense_characteristic_summary_qa.py
git rm .github/workflows/characteristic-label-validation.yml
```

- [ ] **Step 3: Commit administrative cleanup**

```bash
git add docs/project-context/CURRENT.md
git commit -m "chore: remove characteristic summary qa harness"
```

- [ ] **Step 4: Prove cleanup changed no product/test code**

Compare the accepted validated SHA to cleanup HEAD. The changed paths must be exactly:

- `.github/workflows/characteristic-label-validation.yml` deletion;
- `tools/render_dense_characteristic_summary_qa.py` deletion;
- `docs/project-context/CURRENT.md` modification.

If `src/` or `tests/` appears, investigate before claiming closure.

- [ ] **Step 5: Request explicit integration/merge decision**

Report the clean feature-branch checkpoint. Do not merge. Piecewise remains unimplemented until this graphics branch is explicitly integrated or otherwise dispositioned.

---

## Self-review coverage

- One extrema/request source lives in `plotting.py`; presentation does not recompute extrema.
- Dense threshold and display-x clustering semantics remain unchanged.
- Stable summary rows use exact `PlotSeries.display_label`, role, value, and plotted-line color.
- x/common-y units are not repeated per row unnecessarily.
- Dense annotations/leaders are removed, not hidden.
- Sparse behavior remains inline at 6.4 × 4.8 under the default fixture.
- `figure.axes[0]` remains the engineering plot and its physical data area is preserved.
- Figure width does not grow; canonical dense added height stays below 1.85 in.
- Geometry tests and real PNG inspection are both mandatory.
- Temporary QA workflow/script survive until user acceptance, then are deleted.
- No Piecewise, parser ergonomics, Colab scroll, release bump, Codex, or implicit merge is included.
