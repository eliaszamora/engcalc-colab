from pathlib import Path

init_path = Path("src/engcalc_colab/__init__.py")
init_text = init_path.read_text(encoding="utf-8")
assert init_text.count('__version__ = "0.8.0"') == 1
init_path.write_text(init_text.replace('__version__ = "0.8.0"', '__version__ = "0.9.0"', 1), encoding="utf-8")

pyproject_path = Path("pyproject.toml")
pyproject = pyproject_path.read_text(encoding="utf-8")
assert pyproject.count('version = "0.8.0"') == 1
pyproject_path.write_text(pyproject.replace('version = "0.8.0"', 'version = "0.9.0"', 1), encoding="utf-8")

readme_path = Path("README.md")
readme = readme_path.read_text(encoding="utf-8")

replacements = {
    "Current version: **0.8.0**.": "Current version: **0.9.0**.",
    "## Matrix/CAS — 0.9.0 development scope": "## v0.9.0 Matrix/CAS",
    "EngCalc's Matrix/CAS layer is currently being completed on the 0.9.0 development branch while the released runtime version remains 0.8.0. Matrix literals use mathematical/MATLAB-inspired syntax with mandatory commas between columns and semicolons between rows:":
        "EngCalc 0.9.0 adds a native Matrix/CAS layer to the same restricted `%%eng` workflow. Matrix literals use mathematical/MATLAB-inspired syntax with mandatory commas between columns and semicolons between rows:",
    "v0.8.0 currently does not provide:": "v0.9.0 currently does not provide:",
    "Version: `0.8.0`.": "Version: `0.9.0`.",
}
for old, new in replacements.items():
    assert readme.count(old) == 1, (old, readme.count(old))
    readme = readme.replace(old, new, 1)

obsolete = "- general arrays or dedicated matrix syntax;\n"
assert readme.count(obsolete) == 1
readme = readme.replace(obsolete, "", 1)

version_anchor = "## Version notes\n\n- **0.8.0** —"
assert readme.count(version_anchor) == 1
readme = readme.replace(
    version_anchor,
    "## Version notes\n\n"
    "- **0.9.0** — native exact symbolic matrices/vectors, one-based indexing, matrix-valued CAS functions, Pint-backed per-entry numerical matrices, exact `solve(A, b)`, guarded rank/RREF/norm/eigen analysis, native MathJax matrix presentation, Piecewise-cell integration and indexed scalar table/plot/envelope workflows.\n"
    "- **0.8.0** —",
    1,
)

readme_path.write_text(readme, encoding="utf-8")
