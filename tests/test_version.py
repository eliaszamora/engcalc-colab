from pathlib import Path
import tomllib

import engcalc_colab


EXPECTED_VERSION = "0.7.2"


def test_runtime_version_is_0_7_2():
    assert engcalc_colab.__version__ == EXPECTED_VERSION


def test_project_metadata_version_is_0_7_2():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == EXPECTED_VERSION


def test_readme_release_version_is_0_7_2():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "Current version: **0.7.2**." in readme
    assert readme.rstrip().endswith("Version: `0.7.2`.")


def test_readme_version_notes_cover_0_7_2_and_0_7_1():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "- **0.7.2** —" in readme
    assert "- **0.7.1** —" in readme


def test_readme_current_limitations_do_not_claim_tables_are_missing():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "v0.7.2 currently does not provide:" in readme
    assert "arrays/tables or dedicated matrix syntax" not in readme
