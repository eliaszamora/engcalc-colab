from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


pyproject_path = ROOT / "pyproject.toml"
pyproject = pyproject_path.read_text(encoding="utf-8")
old_dependencies = 'dependencies = ["sympy>=1.13", "pint>=0.24", "matplotlib>=3.8"]'
new_dependencies = (
    'dependencies = ["sympy>=1.13", "pint>=0.24", "matplotlib>=3.8", '
    '"ipython>=8.18"]'
)
if old_dependencies in pyproject:
    pyproject = pyproject.replace(old_dependencies, new_dependencies, 1)
elif new_dependencies not in pyproject:
    raise SystemExit("Task 11 pyproject dependency anchor not found")
pyproject_path.write_text(pyproject, encoding="utf-8")


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

print("Applied Task 11 metadata, packaging regression, and permanent CI workflow.")
