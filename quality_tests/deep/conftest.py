"""Hypothesis profile for the Deep Property Gate.

Exploration is the point of this suite, so ``derandomize`` stays False. A
derandomized profile would replay the same examples on every run, which is right
for the Fast Gate but would make this suite stop discovering anything after its
first execution.

The example database is left enabled so a counterexample found in one run is
replayed first in the next. That cache is a convenience, never authority: a
counterexample only becomes protection once it is committed as a deterministic
regression.

**Every setting the environment could otherwise decide is set here explicitly.**
Hypothesis auto-loads a built-in ``ci`` profile when it detects CI, and a profile
registered afterwards inherits whatever that profile left in place. The Deep Gate
inherited ``database=None`` that way for its entire existence: locally the database
resolved to ``.hypothesis/examples`` and stored counterexamples, and in CI there was
no database at all, so nothing was ever saved, the cache restored nothing and the
artifact had nothing to upload. Finding QG-3.

That also corrects QG-1, which attributed the empty artifact to ``upload-artifact``
skipping hidden files. The flag it added is harmless and probably right, but it was
never the cause: there was no database to skip.
"""

from __future__ import annotations

from pathlib import Path

from hypothesis import HealthCheck, settings
from hypothesis.database import DirectoryBasedExampleDatabase

# Rooted at the repository, not at the working directory, so the path matches the one
# the workflow caches and uploads however pytest is invoked.
_DATABASE_DIRECTORY = Path(__file__).resolve().parents[2] / ".hypothesis" / "examples"

settings.register_profile(
    "quality_deep",
    deadline=None,
    derandomize=False,
    database=DirectoryBasedExampleDatabase(_DATABASE_DIRECTORY),
    print_blob=True,
    suppress_health_check=[HealthCheck.too_slow],
)

settings.load_profile("quality_deep")
