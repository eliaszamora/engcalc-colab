"""The Deep Gate's Hypothesis profile must not be decided by the environment.

QG-3. Hypothesis auto-loads a built-in ``ci`` profile when it detects CI, and a
profile registered afterwards inherits whatever that one left in place. The Deep
Gate inherited ``database=None`` for its entire existence, so counterexamples were
stored locally and silently discarded in CI - which is where the gate actually runs.

Nothing caught it, and nothing could have: every run was green or, when forced red,
reported an absent database in a log nobody had reason to doubt. These tests run in
the ordinary suite on every push, in a subprocess with CI environment variables set,
because the defect only exists under those variables.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


_PROBE = """
import sys
sys.path.insert(0, "quality_tests/deep")
import conftest  # registers and loads the quality_deep profile
from hypothesis import settings
print("database:", settings.default.database)
print("derandomize:", settings.default.derandomize)
"""


def _profile_under(environment: dict[str, str]) -> dict[str, str]:
    import os

    result = subprocess.run(
        [sys.executable, "-c", _PROBE],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, **environment},
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return dict(
        line.split(": ", 1) for line in result.stdout.strip().splitlines() if ": " in line
    )


@pytest.mark.parametrize(
    "environment",
    [
        pytest.param({}, id="local"),
        pytest.param({"CI": "true", "GITHUB_ACTIONS": "true"}, id="ci"),
    ],
)
def test_deep_profile_keeps_its_example_database(environment):
    """The database must be real in both environments, and it was not in CI.

    Without an explicit ``database`` the CI profile supplies ``None``, so no
    counterexample is ever written, the workflow cache restores nothing and the
    artifact has nothing to upload. The whole persistence architecture is inert and
    every run still looks green.
    """
    resolved = _profile_under(environment)

    assert resolved["database"] != "None", (
        "the Deep Gate has no example database in this environment, so counterexamples "
        "are discarded: " + repr(resolved)
    )
    assert ".hypothesis" in resolved["database"], (
        f"the database is not the directory the workflow preserves: {resolved!r}"
    )


@pytest.mark.parametrize(
    "environment",
    [
        pytest.param({}, id="local"),
        pytest.param({"CI": "true", "GITHUB_ACTIONS": "true"}, id="ci"),
    ],
)
def test_deep_profile_keeps_exploring_in_ci(environment):
    """The CI profile also sets ``derandomize=True``, which would end exploration.

    The conftest already set this one explicitly, so it was never broken. It is
    asserted anyway: it was correct by luck of ordering rather than by protection,
    and the next setting anyone adds will inherit from the environment unless
    something says otherwise.
    """
    assert _profile_under(environment)["derandomize"] == "False"
