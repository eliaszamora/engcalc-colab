"""Shared Hypothesis strategies for the Deep Property Gate.

Values stay inside ordinary engineering ranges with three decimal places, because
the defects this gate exists to catch appeared with ordinary decimals rather than
with pathological floats. Separation guards use ``assume`` so a rejected draw is
reported as a filtered example rather than counted as one that exercised EngCalc.
"""

from __future__ import annotations

from hypothesis import strategies as st

# Roots and vertices across a domain of [-5, 5] with millimetre-scale resolution.
root_value = st.integers(min_value=-4000, max_value=4000).map(lambda n: n / 1000)

# Leading coefficients away from zero, so the polynomial keeps its degree.
lead_coefficient = (
    st.integers(min_value=-500, max_value=500)
    .filter(lambda n: abs(n) >= 20)
    .map(lambda n: n / 100)
)

positive_parameter = st.integers(min_value=1, max_value=1600).map(lambda n: n / 100)

curvature = st.integers(min_value=20, max_value=400).map(lambda n: n / 100)

offset = st.integers(min_value=-500, max_value=500).map(lambda n: n / 100)

piecewise_breakpoint = st.integers(min_value=50, max_value=550).map(lambda n: n / 100)

piecewise_operator = st.sampled_from(["<", "<=", ">", ">="])

distributed_load = st.integers(min_value=100, max_value=2500).map(lambda n: n / 100)

span_length = st.integers(min_value=100, max_value=1200).map(lambda n: n / 100)


MINIMUM_ROOT_SEPARATION = 0.05
"""Roots closer than this are a known uncovered family, not a target here."""


def sufficiently_separated(values: list[float], gap: float = MINIMUM_ROOT_SEPARATION) -> bool:
    ordered = sorted(values)
    return all(right - left > gap for left, right in zip(ordered, ordered[1:]))
