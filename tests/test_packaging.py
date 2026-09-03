from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

import engcalc_colab


def _project_metadata():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]


def _dependency_names():
    dependencies = _project_metadata()["dependencies"]
    return {dependency.split("[")[0].split(">=")[0].split("==")[0].strip().lower() for dependency in dependencies}


def test_ipython_is_a_runtime_dependency():
    assert "ipython" in _dependency_names()


def test_pyproject_version_is_0_9_2():
    assert _project_metadata()["version"] == "0.23.3"


def test_runtime_version_is_0_9_2():
    assert engcalc_colab.__version__ == "0.23.3"


def test_pint_is_a_runtime_dependency():
    assert "pint" in _dependency_names()


def test_matplotlib_is_a_runtime_dependency():
    assert "matplotlib" in _dependency_names()


def test_latex2mathml_is_not_a_runtime_dependency():
    assert "latex2mathml" not in _dependency_names()
