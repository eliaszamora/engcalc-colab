# Dense Characteristic Summary — Planning Clarification

_Date: 2026-08-30_
_Status: planning-time clarification preserving the approved design intent_

## Reason

During implementation-plan review, the current `src/engcalc_colab/label_layout.py` was inspected closely and found to contain its own `_extreme_indices()` / `_characteristic_requests()` path. That means the current presentation layer independently recomputes extrema even though the approved dense-summary design requires `plotting.py` to remain the engineering authority.

## Clarification

The implementation is therefore explicitly allowed to make one private, behavior-preserving refactor in `src/engcalc_colab/plotting.py`:

- add a private immutable `_CharacteristicRequest` representation;
- add private `_characteristic_requests(result: PlotResult)` extraction;
- refactor only multi-series plotting to consume that same request sequence;
- make `label_layout.py` consume the same private request sequence instead of recomputing extrema.

This is not a new public API and does not change parser grammar, `PlotResult`, plot/envelope syntax, extrema mathematics, sampling, values, units, markers, colors, legend behavior, or sign convention. Single-series rendering does not need to be refactored for this task.

## Effect on the approved spec

This clarification supersedes only the expectation in Section 12 that `plotting.py` would probably remain untouched. It directly enforces Section 5.1, which says the plotting layer is authoritative and the presentation layer must not independently reimplement extrema mathematics.

All other requirements and non-goals of `2026-08-30-engcalc-dense-characteristic-summary-design.md` remain unchanged.
