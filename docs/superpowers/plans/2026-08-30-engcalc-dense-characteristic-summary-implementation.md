# EngCalc Dense Characteristic Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace visually rejected dense characteristic callouts with a compact, color-keyed characteristic summary below an unchanged-size EngCalc plot while preserving all engineering values and sparse inline behavior.

**Architecture:** Keep `render_plot()` as the engineering authority and `render_presented_plot()` as the presentation boundary. First centralize multi-series characteristic-request extraction in `plotting.py` so the renderer and presentation layer consume one private source of extrema truth. Then replace the bottom-callout implementation in `label_layout.py` with a compact secondary Matplotlib axes that contains dense groups while the primary axes retains its baseline physical width and height.

**Tech Stack:** Python 3.13, Matplotlib/Agg, Pint quantities already used by EngCalc, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-30-engcalc-dense-characteristic-summary-design.md`

## Global Constraints

- Active branch: `feature/v0.8.0-characteristic-label-layout`.
- Package/runtime version remains `0.7.2`; no version bump is part of this work.
- Positive structural moment remains plotted downward.
- Characteristic-point mathematics, curve sampling, units, extrema values, legend semantics, series colors, and plotted curve data must not change.
- Dense threshold remains `_DENSE_CLUSTER_SIZE = 3` and x clustering keeps the existing `_CLUSTER_X_TOLERANCE_PX` behavior.
- Sparse clusters with fewer than 3 labels retain the existing inline presentation exactly.
- Figure width must remain at the ordinary EngCalc/Matplotlib baseline width; the dense summary must never widen the figure.
- Primary plot axes must retain baseline physical width and height within ±1 px under the Agg renderer.
- The six-series QA fixture must add materially less than the rejected 1.85 in bottom-callout height.
- Dense summary entries use exact `PlotSeries.display_label` identity and the same series color as the plotted line.
- The x unit appears once in each dense-group header. A common y unit appears once in the group value heading; only heterogeneous-unit fallback repeats units per row.
- No dense per-point leader lines.
- No parser grammar, `PlotResult` public API, `plot(...)`, `envelope(...)`, numeric system, tables, Piecewise, multiline-call parsing, or `no_vertical_scroll()` work is included.
- Do not invoke Codex / `@codex review` / Codex Cloud.
- Do not merge without explicit user approval.
- Every production change follows RED → GREEN, focused tests first, then the complete source suite.

---

## File map

- `src/engcalc_colab/plotting.py`
  - Remains the engineering rendering authority.
  - Gains one private immutable `_CharacteristicRequest` representation and one private `_characteristic_requests(result)` function used by both rendering and presentation.
  - Multi-series rendering is refactored to consume that helper without changing visible output.
- `src/engcalc_colab/label_layout.py`
  - Remains the isolated presentation-only dense-layout module.
  - Stops recomputing extrema independently.
  - Replaces bottom callouts/leader lines with dense grouping plus a compact summary axes.
- `src/engcalc_colab/presentation.py`
  - Keeps the same public behavior and call order; change only if the summary integration needs a renamed presentation helper.
- `tests/test_characteristic_requests.py`
  - New focused regression file proving the shared request source reproduces the established engineering extrema and rendering behavior.
- `tests/test_dense_characteristic_summary.py`
  - New semantic tests for dense-group construction, ordering, identity, roles, units, and colors.
- `tests/test_dense_characteristic_label_layout.py`
  - Existing rejected bottom-band geometry contracts are replaced by compact-summary rendering contracts while preserving the sparse regression fixture.
- `tools/render_dense_characteristic_summary_qa.py`
  - Temporary reproducible QA renderer created only for visual validation; exports PNG + JSON metrics and is deleted after user acceptance.
- `.github/workflows/characteristic-label-validation.yml`
  - Temporarily extended to upload the QA artifact after the full suite passes; removed before integration closure because it is a task-specific validation workflow.
- `docs/project-context/CURRENT.md`
  - Updated at each state-changing checkpoint.

---

### Task 1: Centralize characteristic requests in the plotting authority

**Files:**
- Create: `tests/test_characteristic_requests.py`
- Modify: `src/engcalc_colab/plotting.py`
- Modify: `docs/project-context/CURRENT.md`

**Interfaces:**
- Produces: private immutable `_CharacteristicRequest` in `plotting.py` with fields:
  - `series_index: int`
  - `series: PlotSeries`
  - `sample_index: int`
  - `x_quantity: Any`
  - `y_quantity: Any`
  - `response_label: str`
  - `role: str` (`"max"` or `"min"`)
  - `inverted: bool`
- Produces: `_characteristic_requests(result: PlotResult) -> tuple[_CharacteristicRequest, ...]`
- Consumes later: `label_layout.py` imports `_CharacteristicRequest` and `_characteristic_requests` rather than recomputing extrema.

- [ ] **Step 1: Add the shared-request RED fixture and exact engineering assertions**

Create `tests/test_characteristic_requests.py` with the established six-series moment fixture. The core assertions must be concrete:

```python
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.parser import parse_cell
from engcalc_colab.plotting import _characteristic_requests, render_plot


def _eval_cell(engine, source):
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


def test_characteristic_requests_are_single_authoritative_sequence():
    result = _dense_six_series_moment_plot()
    requests = _characteristic_requests(result)

    assert len(requests) == 12
    assert [(r.series_index, r.role) for r in requests] == [
        (0, "max"), (0, "min"),
        (1, "max"), (1, "min"),
        (2, "max"), (2, "min"),
        (3, "max"), (3, "min"),
        (4, "max"), (4, "min"),
        (5, "max"), (5, "min"),
    ]
    assert [float(r.x_quantity.magnitude) for r in requests[::2]] == [2.5] * 6
    assert [float(r.x_quantity.magnitude) for r in requests[1::2]] == [0.0] * 6
    assert all(r.inverted for r in requests)
    assert [r.series.display_label for r in requests[::2]] == [
        "M_C1(x)", "M_C2(x)", "M_S1(x)", "M_S2(x)", "M_S3(x)", "M_S4(x)"
    ]
```

Also assert the exact established minimum magnitudes at x=0:

```python
assert [float(r.y_quantity.magnitude) for r in requests[1::2]] == [
    -6.0, -22.4, -8.0, -19.2, -14.0, -16.0
]
```

For maxima, use `pytest.approx` because the sampled quantities are floats:

```python
assert [float(r.y_quantity.magnitude) for r in requests[::2]] == pytest.approx(
    [3.375, 8.85, 4.5, 10.8, 7.875, 10.25]
)
```

- [ ] **Step 2: Run the focused RED test**

Run:

```bash
python -m pytest tests/test_characteristic_requests.py -q
```

Expected: collection/import FAIL because `_characteristic_requests` does not yet exist in `engcalc_colab.plotting`.

- [ ] **Step 3: Implement the private request type and extraction helper**

In `src/engcalc_colab/plotting.py`, import `dataclass`, `Any`, and `PlotSeries` as needed, then add:

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
```

- [ ] **Step 4: Refactor only `_render_multi_series()` to consume the shared requests**

Before plotting annotations, compute:

```python
requests = _characteristic_requests(result)
requests_by_series = {
    index: tuple(request for request in requests if request.series_index == index)
    for index in range(len(result.series))
}
```

During each series loop, use `request.sample_index` from `requests_by_series[series_index]` to draw the same characteristic markers. Preserve the existing marker size (`s=26`), line width, legend, axes styling, inversion, margins, and `tight_layout()`.

Store line colors by `series_index`:

```python
line_colors[series_index] = line.get_color()
```

After layout, annotate in the exact request sequence:

```python
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

Do not refactor single-series rendering in this task; the dense presentation path is multi-series and YAGNI applies.

- [ ] **Step 5: Run the new focused test and existing plot regressions**

Run:

```bash
python -m pytest tests/test_characteristic_requests.py tests/test_plotting.py tests/test_plot_engine.py tests/test_dense_characteristic_label_layout.py -q
```

Expected: all PASS; the existing bottom-callout presentation remains visually/behaviorally unchanged at this checkpoint.

- [ ] **Step 6: Run the complete source suite**

Run:

```bash
python -m pytest -q
```

Expected: all tests PASS. Record the exact pass count in `docs/project-context/CURRENT.md`; do not predict the count in advance.

- [ ] **Step 7: Update continuity context and commit**

Record that shared request extraction is now authoritative and that dense visual presentation is still the rejected bottom band pending Tasks 2–4.

Commit:

```bash
git add src/engcalc_colab/plotting.py tests/test_characteristic_requests.py docs/project-context/CURRENT.md
git commit -m "refactor: centralize characteristic requests"
```

---

### Task 2: Define dense-summary semantics and remove presentation-layer extrema duplication

**Files:**
- Create: `tests/test_dense_characteristic_summary.py`
- Modify: `src/engcalc_colab/label_layout.py`
- Modify: `docs/project-context/CURRENT.md`

**Interfaces:**
- Consumes: `plotting._CharacteristicRequest` and `plotting._characteristic_requests(result)` from Task 1.
- Produces private immutable `_DenseSummaryEntry`:
  - `request: _CharacteristicRequest`
  - `color: Any`
- Produces private immutable `_DenseSummaryGroup`:
  - `x_quantity: Any`
  - `entries: tuple[_DenseSummaryEntry, ...]`
- Produces `_build_dense_summary_groups(axis, result: PlotResult) -> tuple[_DenseSummaryGroup, ...]`.
- Keeps `reflow_dense_characteristic_labels(figure, result)` temporarily rendering the old bottom callout so the visual replacement remains isolated to Task 4.

- [ ] **Step 1: Write semantic RED tests for the two dense groups**

Create `tests/test_dense_characteristic_summary.py` using the same exact six-series fixture and a baseline `render_plot(result)` figure. Import the future helper:

```python
from engcalc_colab.label_layout import _build_dense_summary_groups
```

Core assertions:

```python
def test_dense_summary_groups_preserve_series_order_roles_and_coordinates():
    result = _dense_six_series_moment_plot()
    figure = render_plot(result)
    axis = figure.axes[0]

    groups = _build_dense_summary_groups(axis, result)
    assert len(groups) == 2
    assert [float(group.x_quantity.magnitude) for group in groups] == pytest.approx([0.0, 2.5])
    assert [len(group.entries) for group in groups] == [6, 6]

    left, interior = groups
    assert [entry.request.series.display_label for entry in left.entries] == [
        "M_C1(x)", "M_C2(x)", "M_S1(x)", "M_S2(x)", "M_S3(x)", "M_S4(x)"
    ]
    assert [entry.request.role for entry in left.entries] == ["min"] * 6
    assert [entry.request.role for entry in interior.entries] == ["max"] * 6
```

Add color identity assertions by comparing each entry color to the matching plotted line color:

```python
line_colors = {line.get_label(): line.get_color() for line in axis.lines}
for group in groups:
    for entry in group.entries:
        assert entry.color == line_colors[entry.request.series.display_label]
```

Add exact-one-to-one request accounting:

```python
assert sum(len(group.entries) for group in groups) == 12
assert len({(entry.request.series_index, entry.request.role) for group in groups for entry in group.entries}) == 12
```

- [ ] **Step 2: Run semantic RED**

Run:

```bash
python -m pytest tests/test_dense_characteristic_summary.py -q
```

Expected: import/collection FAIL because `_build_dense_summary_groups` does not exist.

- [ ] **Step 3: Replace the local extrema-request implementation with the shared plotting helper**

In `label_layout.py`:

- delete its local `_extreme_indices()`;
- delete its local `_characteristic_requests()`;
- import `_CharacteristicRequest` and `_characteristic_requests` from `.plotting`;
- retain `_series_color()` because presentation still needs the actual Matplotlib line color.

Add:

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

- [ ] **Step 4: Implement stable dense grouping without sorting rows by y value**

Keep the existing display-x tolerance to decide membership, but group rows in stable request order.

The helper must:

1. call `_characteristic_requests(result)` exactly once;
2. transform each request x/y to display coordinates for x clustering;
3. sort only cluster discovery by display x;
4. discard clusters smaller than `_DENSE_CLUSTER_SIZE`;
5. sort dense groups by x coordinate;
6. sort entries inside each group by `(request.series_index, role_order)` where `role_order = 0` for `max`, `1` for `min` so a same-series same-x coincidence remains deterministic;
7. attach the actual line color through `_series_color(axis, request.series.display_label)`;
8. return immutable tuples.

Use this concrete signature:

```python
def _build_dense_summary_groups(axis, result: PlotResult) -> tuple[_DenseSummaryGroup, ...]:
    ...
```

Do not create the summary axes yet.

- [ ] **Step 5: Adapt the existing bottom-callout internals to `_CharacteristicRequest` fields**

Until Task 4 replaces the renderer, keep the old bottom-band output operational by updating tuple unpacking such as `request[0]` / `request[1]` to:

```python
request.x_quantity
request.y_quantity
request.role
request.inverted
```

Use `_series_color()` for the leader color where the old tuple previously carried color. This is temporary compatibility code and is deleted in Task 4.

- [ ] **Step 6: Run semantic tests plus old dense-layout regression**

Run:

```bash
python -m pytest tests/test_dense_characteristic_summary.py tests/test_dense_characteristic_label_layout.py -q
```

Expected: PASS. The semantic model is now GREEN while the visible renderer is intentionally still the rejected bottom band.

- [ ] **Step 7: Run complete suite and commit**

Run:

```bash
python -m pytest -q
```

Expected: all PASS.

Update `CURRENT.md` with the exact pass count and note that the semantic summary model exists but is not yet user-facing.

Commit:

```bash
git add src/engcalc_colab/label_layout.py tests/test_dense_characteristic_summary.py docs/project-context/CURRENT.md
git commit -m "refactor: model dense characteristic groups"
```

---

### Task 3: Replace rejected bottom-band contracts with compact-summary RED contracts

**Files:**
- Modify: `tests/test_dense_characteristic_label_layout.py`
- Modify: `docs/project-context/CURRENT.md`

**Interfaces:**
- Consumes: `_build_dense_summary_groups()` from Task 2.
- Specifies future renderer identifier: summary axes `gid == "engcalc-characteristic-summary"`.
- Specifies future text identifiers:
  - panel title: `gid == "engcalc-summary-title"`
  - group header: `gid == "engcalc-summary-group-header"`
  - entry label: `gid == "engcalc-summary-entry-label"`
  - entry role: `gid == "engcalc-summary-entry-role"`
  - entry value: `gid == "engcalc-summary-entry-value"`

- [ ] **Step 1: Replace bottom-callout-specific helpers and assertions**

Delete tests/helpers whose contract is now rejected:

- single vertical rail alignment;
- minimum rail vertical clearance;
- `arrow_patch is not None`;
- all dense annotation boxes below the main axes;
- explicit bottom-callout leader checks.

Keep the established `_dense_six_series_moment_plot()`, `_sparse_two_series_plot()`, baseline rendering helper, overlap calculation, and ±1 px primary-axes size tolerance.

- [ ] **Step 2: Add RED contract: dense annotations leave the primary axes and one summary axes appears**

```python
def _summary_axes(figure):
    return [axis for axis in figure.axes[1:] if axis.get_gid() == "engcalc-characteristic-summary"]


def test_dense_characteristics_move_to_one_compact_summary_without_leaders():
    figure, axis, items, renderer = _render_dense_case()

    assert len(items) == 0
    assert len(_summary_axes(figure)) == 1

    summary = _summary_axes(figure)[0]
    values = [text for text in summary.texts if text.get_gid() == "engcalc-summary-entry-value"]
    labels = [text for text in summary.texts if text.get_gid() == "engcalc-summary-entry-label"]
    roles = [text for text in summary.texts if text.get_gid() == "engcalc-summary-entry-role"]
    headers = [text for text in summary.texts if text.get_gid() == "engcalc-summary-group-header"]

    assert len(values) == 12
    assert len(labels) == 12
    assert len(roles) == 12
    assert len(headers) == 2
    assert all(item.arrow_patch is None for item in items)
```

The old bottom-callout implementation should fail because it still leaves 12 `Annotation` objects and has no summary axes.

- [ ] **Step 3: Add RED contract: geometry preserves the plot and is compact**

```python
def test_dense_summary_preserves_figure_width_and_primary_axes_size():
    result = _dense_six_series_moment_plot()
    baseline_figure, baseline_axis, baseline_renderer = _render_baseline(result)
    baseline_box = baseline_axis.get_window_extent(baseline_renderer)

    figure, axis, _, renderer = _render(result)
    box = axis.get_window_extent(renderer)

    assert figure.get_figwidth() == baseline_figure.get_figwidth()
    assert abs(float(box.width) - float(baseline_box.width)) <= 1.0
    assert abs(float(box.height) - float(baseline_box.height)) <= 1.0
    assert 0.0 < figure.get_figheight() - baseline_figure.get_figheight() < 1.85
```

- [ ] **Step 4: Add RED contract: summary text is contained and collision-free**

Use the summary axes renderer to gather all texts with the five EngCalc summary gids. For every text box:

```python
box = text.get_window_extent(renderer)
assert box.x0 >= figure.bbox.x0
assert box.x1 <= figure.bbox.x1
assert box.y0 >= figure.bbox.y0
assert box.y1 <= figure.bbox.y1
```

Then pairwise assert overlap area is zero for entry labels against entry values/roles from other rows and for group headers against row texts. It is acceptable for a label and role/value on the same row to share y range; horizontal separation must keep their rectangle intersection at zero.

- [ ] **Step 5: Strengthen the existing sparse regression**

The sparse case remains:

```python
assert len(items) == 4
assert len(_summary_axes(figure)) == 0
assert all(item.arrow_patch is None for item in items)
assert figure.get_figwidth() == matplotlib.rcParams["figure.figsize"][0]
assert figure.get_figheight() == matplotlib.rcParams["figure.figsize"][1]
```

Also keep the current requirement that all sparse inline text remains within the ordinary plot region.

- [ ] **Step 6: Run the new renderer contracts and confirm intentional RED**

Run:

```bash
python -m pytest tests/test_dense_characteristic_label_layout.py -q
```

Expected: dense-summary tests FAIL for the old bottom band. Sparse regression must still PASS. Record the failing test names and the exact pass/fail count in `CURRENT.md`.

- [ ] **Step 7: Commit the intentional RED state**

```bash
git add tests/test_dense_characteristic_label_layout.py docs/project-context/CURRENT.md
git commit -m "test: specify compact characteristic summary"
```

Do not alter production in this commit.

---

### Task 4: Implement the compact dense-summary renderer GREEN

**Files:**
- Modify: `src/engcalc_colab/label_layout.py`
- Modify: `src/engcalc_colab/presentation.py` only if a helper rename is required; otherwise leave unchanged.
- Modify: `tests/test_dense_characteristic_summary.py` only for formatting assertions that cannot be expressed in geometry tests.
- Modify: `docs/project-context/CURRENT.md`

**Interfaces:**
- Consumes: `_DenseSummaryGroup` from Task 2.
- Produces: one secondary Matplotlib axes per dense figure with `gid="engcalc-characteristic-summary"`.
- Keeps public `render_presented_plot(result)` signature unchanged.

- [ ] **Step 1: Delete rejected callout-only constants and functions**

Remove from `label_layout.py` after no tests depend on them:

- `_MIN_BOTTOM_SPACE_IN`
- `_BOTTOM_SPACE_PER_LABEL_IN`
- `_BOTTOM_SPACE_PADDING_IN`
- `_BAND_EDGE_MARGIN_PX`
- `_RAIL_VERTICAL_GAP_PX`
- `_LEADER_LINEWIDTH`
- `_LEADER_ALPHA`
- `_text_box()` if no longer used by production
- `_stack_vertical_centers()`
- `_create_bottom_callout()`
- `_layout_bottom_cluster()`

Rename `_reserve_bottom_space()` to `_reserve_summary_space()` and keep its proven invariant: vertical figure growth while preserving primary axes physical size.

- [ ] **Step 2: Add compact, content-driven summary sizing**

Use two columns maximum to prevent horizontal crowding. Add these presentation constants:

```python
_SUMMARY_MAX_COLUMNS = 2
_SUMMARY_TITLE_HEIGHT_IN = 0.18
_SUMMARY_GROUP_HEADER_HEIGHT_IN = 0.16
_SUMMARY_ROW_HEIGHT_IN = 0.14
_SUMMARY_PANEL_PADDING_IN = 0.08
_SUMMARY_GROUP_GAP_FRACTION = 0.05
```

Compute grid rows in group chunks of two:

```python
def _summary_height_inches(groups: tuple[_DenseSummaryGroup, ...]) -> float:
    rows = [groups[index:index + _SUMMARY_MAX_COLUMNS] for index in range(0, len(groups), _SUMMARY_MAX_COLUMNS)]
    body = sum(
        _SUMMARY_GROUP_HEADER_HEIGHT_IN
        + _SUMMARY_ROW_HEIGHT_IN * max(len(group.entries) for group in grid_row)
        for grid_row in rows
    )
    return _SUMMARY_PANEL_PADDING_IN * 2 + _SUMMARY_TITLE_HEIGHT_IN + body
```

For the canonical two-group/six-entry fixture this formula yields about 1.18 in, safely below the rejected 1.85 in while remaining readable at 8–8.5 pt.

- [ ] **Step 3: Implement unit formatting helpers with no per-row repetition for homogeneous plots**

Reuse existing private plotting formatters rather than creating a second unit convention. Import `_compact_number`, `_quantity_label`, and `_unit_label` from `.plotting`.

Add:

```python
def _group_x_header(group: _DenseSummaryGroup) -> str:
    quantity = group.x_quantity
    value = _compact_number(float(quantity.magnitude))
    unit = _unit_label(quantity)
    return f"x = {value}" if not unit else f"x = {value} {unit}"
```

Determine the common y unit across all dense entries:

```python
def _common_y_unit(groups, *, moment: bool) -> str | None:
    units = {
        _unit_label(entry.request.y_quantity, moment=moment)
        for group in groups
        for entry in group.entries
    }
    return next(iter(units)) if len(units) == 1 else None
```

When `common_y_unit` is not `None`, row values are just `_compact_number(magnitude)` and the group heading includes `Value [<unit>]`. When units differ, row values use `_quantity_label(..., moment=moment)` and the heading is simply `Value`.

- [ ] **Step 4: Add the secondary summary axes without changing the primary axes index**

After `_reserve_summary_space(figure, axis, summary_height_in)`, add one axes after the main plot so `figure.axes[0]` remains the engineering axes:

```python
summary = figure.add_axes([left_fraction, bottom_fraction, width_fraction, height_fraction])
summary.set_gid("engcalc-characteristic-summary")
summary.set_xlim(0.0, 1.0)
summary.set_ylim(0.0, 1.0)
summary.set_axis_off()
```

Align the panel horizontally to the main axes physical left/width. Keep a small physical gap between the primary x-axis label region and the summary by placing the summary entirely inside the newly added figure height.

- [ ] **Step 5: Render a restrained two-column engineering summary**

Use axes-fraction coordinates. Render:

1. one panel title `Characteristic points` with `gid="engcalc-summary-title"`, fontsize 8.5, semibold;
2. one group header per dense group using `_group_x_header(group)` and `gid="engcalc-summary-group-header"`, fontsize 8.2, semibold;
3. a `Value [unit]` heading at the right side of each group header when a common y unit exists;
4. for each entry row:
   - a small circular color key using `summary.plot(..., marker="o", linestyle="none", color=entry.color, transform=summary.transAxes)`;
   - exact `entry.request.series.display_label` text with `gid="engcalc-summary-entry-label"`;
   - `entry.request.role` text with `gid="engcalc-summary-entry-role"`;
   - formatted numeric value with `gid="engcalc-summary-entry-value"`, right-aligned;
5. at most one light horizontal separator beneath each group header; do not draw a cell grid.

Set each text object's gid immediately after creation:

```python
text = summary.text(...)
text.set_gid("engcalc-summary-entry-value")
```

Use the exact series color for the circular key and series label. Keep role/value text in normal Matplotlib foreground color for legibility.

- [ ] **Step 6: Rewrite `reflow_dense_characteristic_labels()` around groups instead of callouts**

The new control flow is:

```python
def reflow_dense_characteristic_labels(figure, result: PlotResult) -> None:
    if result.kind != "plot" or len(result.series) < 2:
        return

    axis = figure.axes[0]
    groups = _build_dense_summary_groups(axis, result)
    if not groups:
        return

    dense_requests = tuple(entry.request for group in groups for entry in group.entries)
    _remove_dense_inline_annotations(axis, dense_requests)
    summary_height_in = _summary_height_inches(groups)
    _reserve_summary_space(figure, axis, summary_height_in)
    _render_summary_panel(figure, axis, groups, summary_height_in=summary_height_in)
```

`_remove_dense_inline_annotations()` must match requests using `request.x_quantity` and `request.y_quantity`. Sparse annotations remain untouched.

There must be no `Annotation` or `arrow_patch` created by the dense summary path.

- [ ] **Step 7: Run focused GREEN tests**

Run:

```bash
python -m pytest \
  tests/test_characteristic_requests.py \
  tests/test_dense_characteristic_summary.py \
  tests/test_dense_characteristic_label_layout.py \
  tests/test_plotting.py \
  tests/test_plot_presentation_options.py -q
```

Expected: all PASS.

- [ ] **Step 8: Run the complete source suite**

Run:

```bash
python -m pytest -q
```

Expected: all PASS. Record exact count and duration in `CURRENT.md`.

- [ ] **Step 9: Commit GREEN implementation**

```bash
git add src/engcalc_colab/label_layout.py src/engcalc_colab/presentation.py tests/test_dense_characteristic_summary.py docs/project-context/CURRENT.md
git commit -m "feat: render compact characteristic summary"
```

If `presentation.py` was unchanged, omit it from `git add`.

---

### Task 5: Generate reproducible PNG + metrics and perform assistant visual QA

**Files:**
- Create temporarily: `tools/render_dense_characteristic_summary_qa.py`
- Modify temporarily: `.github/workflows/characteristic-label-validation.yml`
- Modify: `docs/project-context/CURRENT.md`

**Interfaces:**
- Produces workflow artifact `engcalc-characteristic-summary-qa` containing:
  - `dense_characteristic_summary.png`
  - `dense_characteristic_summary_metrics.json`
- No production source behavior changes in this task.

- [ ] **Step 1: Add a deterministic QA renderer**

Create `tools/render_dense_characteristic_summary_qa.py`. It must use `matplotlib.use("Agg")`, rebuild the exact six-series fixture, render both `render_plot(result)` and `render_presented_plot(result)`, and save only the presented PNG.

Metrics must be converted to ordinary Python `float`, `int`, and `bool` before `json.dump()` to avoid the prior `numpy.int64` serialization failure.

Write at minimum:

```python
metrics = {
    "baseline_figure_inches": [float(v) for v in baseline_figure.get_size_inches()],
    "presented_figure_inches": [float(v) for v in figure.get_size_inches()],
    "baseline_axes_px": [float(baseline_box.width), float(baseline_box.height)],
    "presented_axes_px": [float(box.width), float(box.height)],
    "dense_group_count": int(len(groups)),
    "summary_entry_count": int(sum(len(group.entries) for group in groups)),
    "summary_text_overlap_count": int(overlap_count),
    "all_summary_text_inside_figure": bool(contained),
    "dense_main_axis_annotation_count": int(len(dense_annotations)),
    "dense_leader_count": int(leader_count),
}
```

Do not print image bytes or Base64 to logs.

- [ ] **Step 2: Add hard QA assertions inside the script**

Before saving metrics, assert:

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
assert 0.0 < metrics["presented_figure_inches"][1] - metrics["baseline_figure_inches"][1] < 1.85
```

- [ ] **Step 3: Extend the branch validation workflow only after the full suite step**

Append:

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

Keep the existing Python 3.13 install and full `python -m pytest -q` gate unchanged.

- [ ] **Step 4: Commit the temporary QA harness**

```bash
git add tools/render_dense_characteristic_summary_qa.py .github/workflows/characteristic-label-validation.yml docs/project-context/CURRENT.md
git commit -m "ci: capture characteristic summary visual qa"
```

The push triggers the workflow automatically.

- [ ] **Step 5: Inspect workflow evidence**

Require:

- complete source suite PASS;
- QA rendering step PASS;
- artifact present and non-expired;
- metrics satisfy all hard assertions.

Download the artifact cleanly and inspect the PNG itself. Do not treat machine PASS as visual acceptance.

- [ ] **Step 6: Apply the visual acceptance checklist before showing the user**

Assistant inspection must verify:

- the plot is visibly the same width/scale as the baseline;
- no curve or legend is covered by summary text;
- the summary feels materially more compact than the rejected 6.65 in figure;
- two dense groups are visually distinct;
- row identity/color mapping is immediate;
- labels, roles, and values align cleanly;
- no text appears clipped;
- no leader-line clutter exists;
- positive moment remains downward;
- the summary reads as part of the engineering figure rather than an unrelated spreadsheet.

If this inspection fails, do not ask the user to approve it. Return to Task 4, change presentation only, rerun focused/full tests, and regenerate the artifact.

- [ ] **Step 7: Present the accepted-by-assistant PNG and metrics to the user**

Report the exact validated SHA, source-suite count, figure dimensions, axes dimensions, overlap count, group/entry count, and absence of leader lines. Ask for visual acceptance only at this point.

Do not merge or clean up the task-specific workflow until the user accepts the rendered result.

---

### Task 6: User-acceptance cleanup and explicit integration gate

**Files:**
- Delete after user acceptance: `tools/render_dense_characteristic_summary_qa.py`
- Delete after user acceptance: `.github/workflows/characteristic-label-validation.yml`
- Modify: `docs/project-context/CURRENT.md`

**Interfaces:**
- Consumes: user acceptance of the exact PNG produced in Task 5.
- Produces: clean feature-branch checkpoint with no task-specific QA harness/workflow.
- Does not merge.

- [ ] **Step 1: Record the accepted implementation SHA before cleanup**

Capture the Task 5 commit SHA and workflow run/artifact IDs in `CURRENT.md`. That SHA remains the authoritative machine+visual validation checkpoint.

- [ ] **Step 2: Remove temporary QA instrumentation**

Delete:

```bash
git rm tools/render_dense_characteristic_summary_qa.py
git rm .github/workflows/characteristic-label-validation.yml
```

The workflow is task-specific and must not persist into integration closure.

- [ ] **Step 3: Update continuity context for closure**

`CURRENT.md` must state:

- dense characteristic summary visually accepted;
- authoritative validated SHA and test count;
- QA artifact/run identifiers;
- cleanup is administrative only;
- no production/test files changed after the validated SHA;
- branch still requires explicit merge approval;
- Piecewise remains unimplemented and next only after this graphics branch is integrated or otherwise dispositioned.

- [ ] **Step 4: Commit cleanup**

```bash
git add docs/project-context/CURRENT.md
git commit -m "chore: remove characteristic summary qa harness"
```

`git rm` paths are already staged.

- [ ] **Step 5: Prove cleanup did not change product/test code**

Compare the accepted Task 5 SHA to cleanup HEAD. The only changed paths must be:

- `.github/workflows/characteristic-label-validation.yml` deletion;
- `tools/render_dense_characteristic_summary_qa.py` deletion;
- `docs/project-context/CURRENT.md` update.

If `src/` or `tests/` appears in the comparison, stop and investigate before claiming closure.

- [ ] **Step 6: Request explicit integration decision**

Report the clean checkpoint and ask whether to integrate/merge. Do not merge implicitly.

---

## Plan self-review checklist

Before implementation begins, verify this plan against the approved spec:

- Shared characteristic request source removes the existing presentation-layer extrema duplication.
- Dense threshold and x clustering semantics are unchanged.
- Stable rows use exact `PlotSeries.display_label` and exact line colors.
- Group headers carry x coordinate/unit once; common y unit is not repeated per row.
- Dense leaders are removed rather than merely hidden.
- Sparse two-series behavior remains exactly baseline-sized and inline.
- Primary axes remains `figure.axes[0]` and preserves physical dimensions.
- Summary width never enlarges the figure; height is content-driven and below 1.85 in for the canonical fixture.
- Both geometry tests and real PNG inspection are required.
- Temporary QA files/workflow are removed only after user acceptance.
- No Piecewise, parser ergonomics, Colab scroll, release bump, Codex, or implicit merge work is included.
