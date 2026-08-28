from pathlib import Path
import tomllib


def _project_metadata():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]


def test_runtime_dependencies_do_not_manage_ipython_in_notebook_hosts():
    dependencies = _project_metadata()["dependencies"]
    names = {dependency.split("[")[0].split(">=")[0].split("==")[0].strip().lower() for dependency in dependencies}
    assert "ipython" not in names


def test_pyproject_version_is_0_2_0():
    assert _project_metadata()["version"] == "0.2.0"


def test_pint_is_a_runtime_dependency():
    dependencies = _project_metadata()["dependencies"]
    names = {dependency.split("[")[0].split(">=")[0].split("==")[0].strip().lower() for dependency in dependencies}
    assert "pint" in names
