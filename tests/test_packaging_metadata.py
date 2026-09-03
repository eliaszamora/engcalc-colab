from importlib import metadata


def test_project_metadata_declares_notebook_runtime_and_python_floor():
    project = metadata.metadata("engcalc-colab")
    assert project["Version"] == "0.25.0"
    assert project["Requires-Python"] == ">=3.10"
    requirements = project.get_all("Requires-Dist") or []
    normalized = {requirement.replace(" ", "").lower() for requirement in requirements}
    # Colab's own pin. A floor above it makes the install upgrade IPython underneath the
    # platform; `tests/test_colab_compatibility.py` is where that is reasoned about, and
    # this asserts the built metadata carries what pyproject declares.
    assert "ipython>=7.34" in normalized


def test_the_installed_metadata_matches_pyproject():
    """A stale editable install must fail loudly rather than pass misleadingly.

    `pip install -e` snapshots the metadata. Change `pyproject.toml` without
    reinstalling and every metadata assertion keeps checking the old file, so a local
    run goes green on a state that does not exist. That happened four times in one
    session, and once it hid a real failure that only CI - which always installs fresh -
    could see.

    In CI this always passes, which is the point: it exists for the machine where the
    install can drift.
    """
    import pathlib
    import sys

    if sys.version_info >= (3, 11):
        import tomllib
    else:  # pragma: no cover - exercised on 3.10 in CI
        import tomli as tomllib

    root = pathlib.Path(__file__).resolve().parents[1]
    declared = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata.metadata("engcalc-colab")

    assert project["Version"] == declared["project"]["version"], (
        "the installed metadata is stale; run `pip install -e '.[dev]'`"
    )

    installed = {
        requirement.replace(" ", "").lower()
        for requirement in (project.get_all("Requires-Dist") or [])
        if "extra ==" not in requirement
    }
    expected = {
        requirement.replace(" ", "").lower()
        for requirement in declared["project"]["dependencies"]
    }
    assert installed == expected, (
        "the installed requirements differ from pyproject.toml; "
        "run `pip install -e '.[dev]'`"
    )
