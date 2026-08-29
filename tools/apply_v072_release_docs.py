from pathlib import Path


path = Path("README.md")
text = path.read_text(encoding="utf-8")

replacements = [
    (
        "v0.7.0 intentionally does not yet provide:",
        "v0.7.2 currently does not provide:",
    ),
    (
        "- arrays/tables or dedicated matrix syntax;",
        "- general arrays or dedicated matrix syntax;",
    ),
    (
        "## Version notes\n\n- **0.7.0** — scalar engineering mathematics: `sqrt`, trig/inverse trig, `exp`, `log`, and `pi` with unit-aware numerical rules.",
        "## Version notes\n\n- **0.7.2** — native engineering tables with automatic unit-aware discretization, unit-once and fully explicit point forms, compatible multi-response columns, native HTML rendering, and source-order `%%eng` integration.\n- **0.7.1** — multi-argument user functions and generalized partial numerical evaluation.\n- **0.7.0** — scalar engineering mathematics: `sqrt`, trig/inverse trig, `exp`, `log`, and `pi` with unit-aware numerical rules.",
    ),
    (
        "Version: `0.7.0`.",
        "Version: `0.7.2`.",
    ),
]

for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one occurrence of {old!r}, found {count}")
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
