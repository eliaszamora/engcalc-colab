from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Task 11 anchor not found: {label}")
    return text.replace(old, new, 1)


pyproject_path = ROOT / "pyproject.toml"
pyproject = pyproject_path.read_text(encoding="utf-8")
pyproject = replace_once(
    pyproject,
    'dependencies = ["sympy>=1.13", "pint>=0.24", "matplotlib>=3.8"]',
    'dependencies = ["sympy>=1.13", "pint>=0.24", "matplotlib>=3.8", "ipython>=8.18"]',
    "runtime IPython dependency",
)
pyproject = replace_once(
    pyproject,
    'dev = ["pytest>=8"]',
    'dev = ["pytest>=8", "tomli>=2.0; python_version < \'3.11\'"]',
    "Python 3.10 TOML test support",
)
pyproject_path.write_text(pyproject, encoding="utf-8")


packaging_path = ROOT / "tests" / "test_packaging.py"
packaging = packaging_path.read_text(encoding="utf-8")
packaging = replace_once(
    packaging,
    "from pathlib import Path\nimport tomllib\nimport engcalc_colab",
    "from pathlib import Path\n\ntry:\n    import tomllib\nexcept ModuleNotFoundError:  # Python 3.10\n    import tomli as tomllib\n\nimport engcalc_colab",
    "test_packaging tomllib compatibility",
)
packaging = replace_once(
    packaging,
    'def test_runtime_dependencies_do_not_manage_ipython_in_notebook_hosts():\n    assert "ipython" not in _dependency_names()',
    'def test_ipython_is_a_runtime_dependency():\n    assert "ipython" in _dependency_names()',
    "test_packaging IPython runtime contract",
)
packaging_path.write_text(packaging, encoding="utf-8")


version_path = ROOT / "tests" / "test_version.py"
version_test = version_path.read_text(encoding="utf-8")
version_test = replace_once(
    version_test,
    "from pathlib import Path\nimport tomllib\nimport engcalc_colab",
    "from pathlib import Path\n\ntry:\n    import tomllib\nexcept ModuleNotFoundError:  # Python 3.10\n    import tomli as tomllib\n\nimport engcalc_colab",
    "test_version tomllib compatibility",
)
version_path.write_text(version_test, encoding="utf-8")


metadata_test = '''from importlib import metadata


def test_project_metadata_declares_notebook_runtime_and_python_floor():
    project = metadata.metadata("engcalc-colab")
    assert project["Requires-Python"] == ">=3.10"
    requirements = project.get_all("Requires-Dist") or []
    normalized = {requirement.replace(" ", "").lower() for requirement in requirements}
    assert "ipython>=8.18" in normalized
'''
(ROOT / "tests" / "test_packaging_metadata.py").write_text(
    metadata_test,
    encoding="utf-8",
)


ci_workflow = '''name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13", "3.14"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pip install --upgrade pip
      - run: python -m pip install -e '.[dev]'
      - run: python -m compileall -q src/engcalc_colab
      - run: python -m pytest -q
'''
workflows = ROOT / ".github" / "workflows"
workflows.mkdir(parents=True, exist_ok=True)
(workflows / "ci.yml").write_text(ci_workflow, encoding="utf-8")

print("Applied Task 11 metadata, Python 3.10 test compatibility, and permanent CI workflow.")
