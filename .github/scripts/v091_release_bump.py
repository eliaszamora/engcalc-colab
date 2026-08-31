from pathlib import Path


def replace_once(path: str, old: str, new: str) -> bool:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    if new in text and old not in text:
        print(f"{path}: release value already updated")
        return False
    if old not in text:
        raise SystemExit(f"{path}: expected release marker not found: {old!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{path}: updated")
    return True


changed = False
changed |= replace_once(
    "pyproject.toml",
    'version = "0.9.0"',
    'version = "0.9.1"',
)
changed |= replace_once(
    "src/engcalc_colab/__init__.py",
    '__version__ = "0.9.0"',
    '__version__ = "0.9.1"',
)
changed |= replace_once(
    "README.md",
    "Current version: **0.9.0**.",
    "Current version: **0.9.1**.",
)
changed |= replace_once(
    "README.md",
    "The next EngCalc release adds exact-first engineering characteristic analysis",
    "EngCalc 0.9.1 adds exact-first engineering characteristic analysis",
)

readme = Path("README.md")
text = readme.read_text(encoding="utf-8")
release_note = (
    "- **0.9.1** — exact-first roots, intersections and extrema with unit-aware "
    "Piecewise semantics, deterministic numerical fallback, and authoritative "
    "ordinary-plot extrema metadata.\n"
)
if "- **0.9.1** —" not in text:
    marker = "- **0.9.0** —"
    if marker not in text:
        raise SystemExit("README.md: 0.9.0 version-note marker not found")
    text = text.replace(marker, release_note + marker, 1)
    readme.write_text(text, encoding="utf-8")
    changed = True
    print("README.md: inserted 0.9.1 version note")
else:
    print("README.md: 0.9.1 version note already present")

changed |= replace_once(
    "README.md",
    "Version: `0.9.0`.",
    "Version: `0.9.1`.",
)

print("release bump changed files" if changed else "release bump already present")
