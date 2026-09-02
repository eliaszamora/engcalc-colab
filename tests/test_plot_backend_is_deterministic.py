"""The test session must not depend on a GUI toolkit being installed.

The root `conftest.py` pins matplotlib to a non-interactive backend. This asserts that
it actually took effect, so deleting or moving that file is caught rather than silently
restoring an intermittent failure.

Honest about its own reach: on a headless Linux CI runner matplotlib selects `Agg` by
itself, so this passes there with or without the conftest. It is load-bearing on a
developer machine with a GUI toolkit available - which is precisely where the flake
lived, and where it cost an investigation. Measured before the fix: the pair
`tests/test_engine.py tests/test_magic.py` failed 4 runs in 10; after it, 0 in 10.
"""

from __future__ import annotations

import matplotlib


def test_the_session_uses_a_non_interactive_backend():
    backend = matplotlib.get_backend().lower()
    assert backend in {"agg", "pdf", "ps", "svg", "template"}, (
        f"the test session is using the interactive backend {backend!r}; plotting tests "
        "then depend on a GUI toolkit and fail intermittently. The root conftest.py "
        "pins this - check it still exists and is being collected."
    )


def test_pyplot_draws_without_a_display():
    """The behaviour the backend choice exists to protect."""
    import matplotlib.pyplot as plt

    figure = plt.figure()
    try:
        axes = figure.add_subplot(111)
        axes.plot([0, 1, 2], [0, 1, 4])
        figure.canvas.draw()
        assert axes.lines
    finally:
        plt.close(figure)
