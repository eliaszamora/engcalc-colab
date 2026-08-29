from pathlib import Path


replacements = {
    Path("pyproject.toml"): ('version = "0.7.1"', 'version = "0.7.2"'),
    Path("src/engcalc_colab/__init__.py"): ('__version__ = "0.7.1"', '__version__ = "0.7.2"'),
    Path("README.md"): ('Current version: **0.7.1**.', 'Current version: **0.7.2**.'),
}

for path, (old, new) in replacements.items():
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one {old!r}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
