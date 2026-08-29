from pathlib import Path
import tomllib

import engcalc_colab


EXPECTED_VERSION = "0.7.2"


def test_runtime_version_is_0_7_2():
    assert engcalc_colab.__version__ == EXPECTED_VERSION


def test_project_metadata_version_is_0_7_2():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == EXPECTED_VERSION
