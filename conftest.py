"""Test-session configuration.

Pins matplotlib to a non-interactive backend before any test imports pyplot.

Without this, matplotlib picks a GUI backend, and on a Windows machine with a broken
Tcl installation the first test that draws anything fails:

    _tkinter.TclError: Can't find a usable init.tcl in the following directories: ...

Which test fails varies, because whichever plotting test runs first is the one that
decides the backend. Measured on `main` before this file existed, running
``pytest tests/test_engine.py tests/test_magic.py`` failed **4 runs out of 10**.

CI never sees it - Linux runners are headless and select Agg on their own - so the cost
is entirely local, and it is the worst kind: an intermittent failure in code that has
nothing to do with the change under test. It cost one real investigation before being
diagnosed.

An explicit ``MPLBACKEND`` is respected, so anyone who deliberately wants a GUI backend
still gets one.
"""

import os

import matplotlib

if not os.environ.get("MPLBACKEND"):
    matplotlib.use("Agg")
