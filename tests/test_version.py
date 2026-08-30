from pathlib import Path
import tomllib
import engcalc_colab

EXPECTED_VERSION = "0.8.0"

def test_runtime_version_is_0_8_0():
    assert engcalc_colab.__version__ == EXPECTED_VERSION

def test_project_metadata_version_is_0_8_0():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == EXPECTED_VERSION

def test_readme_release_version_is_0_8_0():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "Current version: **0.8.0**." in readme
    assert readme.rstrip().endswith("Version: `0.8.0`.")

def test_readme_version_notes_cover_0_8_0_and_0_7_2():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "- **0.8.0** —" in readme
    assert "- **0.7.2** —" in readme

def test_readme_current_limitations_are_current_for_piecewise():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "v0.8.0 currently does not provide:" in readme
    assert "`piecewise`/discontinuous-function plotting and jump markers" not in readme
    assert "general arrays or dedicated matrix syntax" in readme
