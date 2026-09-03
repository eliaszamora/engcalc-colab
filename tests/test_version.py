from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

import engcalc_colab

EXPECTED_VERSION = "0.25.0"


def test_runtime_version_is_0_25_0():
    assert engcalc_colab.__version__ == EXPECTED_VERSION


def test_project_metadata_version_is_0_25_0():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == EXPECTED_VERSION


def test_readme_release_version_is_0_25_0():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "Current version: **0.25.0**." in readme
    assert readme.rstrip().endswith("Version: `0.25.0`.")


def test_readme_version_notes_cover_0_25_0_0_24_0_and_0_23_0():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "- **0.25.0** —" in readme
    assert "- **0.24.0** —" in readme
    assert "- **0.23.0** —" in readme


def test_readme_matrix_cas_remains_documented():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "## v0.9.0 Matrix/CAS" in readme
    assert "0.9.0 development branch" not in readme
    assert "general arrays or dedicated matrix syntax" not in readme
    assert "[a, b; c, d]" in readme
    assert "solve(A, b)" in readme
    assert "numeric(A)" in readme
