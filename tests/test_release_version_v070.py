from pathlib import Path
import tomllib

import engcalc_colab


EXPECTED_VERSION = "0.7.0"


def test_package_version_is_v070():
    assert engcalc_colab.__version__ == EXPECTED_VERSION


def test_pyproject_version_is_v070():
    project_root = Path(__file__).resolve().parents[1]
    with (project_root / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    assert pyproject["project"]["version"] == EXPECTED_VERSION
