"""Installing EngCalc must not upgrade Colab's IPython.

Colab pins `ipython==7.34.0`. EngCalc declared `ipython>=8.18`, so the very first
`%pip install` in a real notebook printed:

    google-colab 1.0.0 requires ipython==7.34.0, but you have ipython 9.17.1
    which is incompatible.

pip had upgraded IPython underneath the platform this package exists for. Nothing here
needed a newer one: the whole IPython surface is `Magics`, `cell_magic`, `line_magic`,
`magics_class`, `HTML`, `Math` and `display`, API that has been stable since IPython 1.x,
and the full product suite passes against 7.34.0.

Found by Elias running it in Colab, on the first try. No test could have found it,
because every test here runs in an environment EngCalc chose.
"""

import pathlib
import sys

import pytest
from packaging.requirements import Requirement

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised on 3.10 in CI
    import tomli as tomllib

# What Colab installs. Raising this is a decision about which notebooks EngCalc runs in,
# so it is written down rather than looked up at test time from a moving target.
COLAB_IPYTHON = "7.34.0"

PYPROJECT = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"


def _requirements() -> dict[str, Requirement]:
    document = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return {
        Requirement(line).name: Requirement(line)
        for line in document["project"]["dependencies"]
    }


def test_the_ipython_floor_admits_the_version_colab_pins():
    """A floor above Colab's pin makes pip upgrade IPython under the platform."""
    requirement = _requirements()["ipython"]
    assert requirement.specifier.contains(COLAB_IPYTHON), (
        f"engcalc-colab requires ipython{requirement.specifier}, which excludes Colab's "
        f"{COLAB_IPYTHON}; installing it would upgrade IPython underneath Colab"
    )


def test_no_dependency_is_pinned_to_a_single_version():
    """A pin here would fight whatever the notebook already has.

    Colab arrives with sympy, matplotlib and numpy already installed. Requiring an exact
    version of any of them turns an install into an upgrade of the platform, which is
    the same defect in a different dependency.
    """
    for name, requirement in _requirements().items():
        exact = [
            specifier
            for specifier in requirement.specifier
            if specifier.operator in ("==", "===")
        ]
        assert not exact, f"{name} is pinned to {exact}, which would fight Colab's own"


def test_the_ipython_surface_stays_small():
    """The floor is defensible only while the API used is ancient and stable.

    If a newer IPython feature is ever imported, this fails and the floor has to be
    reconsidered deliberately rather than raised by habit.
    """
    magic = (PYPROJECT.parent / "src" / "engcalc_colab" / "magic.py").read_text(
        encoding="utf-8"
    )
    imports = sorted(
        line.strip()
        for line in magic.splitlines()
        if line.startswith(("from IPython", "import IPython"))
    )
    assert imports == [
        "from IPython.core.magic import Magics, cell_magic, line_magic, magics_class",
        "from IPython.display import HTML, Math, display",
    ], imports


def test_no_other_module_reaches_for_ipython():
    """The magic is the only place the notebook is spoken to.

    An IPython import elsewhere would widen the surface without anyone weighing it
    against the floor above.
    """
    source = PYPROJECT.parent / "src" / "engcalc_colab"
    offenders = [
        path.name
        for path in sorted(source.glob("*.py"))
        if path.name != "magic.py" and "IPython" in path.read_text(encoding="utf-8")
    ]
    assert not offenders, offenders


def test_ci_runs_the_suite_against_colab_s_ipython():
    """The floor is a claim, and this is what keeps it true.

    Without a job pinned to 7.34.0, "the suite passes on Colab's IPython" is a sentence
    in a comment. It was measured once, by hand, in a scratch virtual environment that
    no longer exists.
    """
    import yaml

    workflow = yaml.safe_load(
        (PYPROJECT.parent / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
    )
    job = workflow["jobs"]["colab-ipython"]
    body = yaml.safe_dump(job)

    assert f"ipython=={COLAB_IPYTHON}" in body, body
    assert "pytest" in body
