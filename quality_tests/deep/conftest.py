"""Hypothesis profile for the Deep Property Gate.

Exploration is the point of this suite, so ``derandomize`` stays False. A
derandomized profile would replay the same examples on every run, which is right
for the Fast Gate but would make this suite stop discovering anything after its
first execution.

The example database is left enabled so a counterexample found in one run is
replayed first in the next. That cache is a convenience, never authority: a
counterexample only becomes protection once it is committed as a deterministic
regression.
"""

from __future__ import annotations

from hypothesis import HealthCheck, settings

settings.register_profile(
    "quality_deep",
    deadline=None,
    derandomize=False,
    suppress_health_check=[HealthCheck.too_slow],
)

settings.load_profile("quality_deep")
