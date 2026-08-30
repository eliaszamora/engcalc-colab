from pathlib import Path

TARGET = Path("src/engcalc_colab/characteristics.py")
SOURCE = Path(".github/scripts/v091_task6_green.py")

text = TARGET.read_text(encoding="utf-8")
if "def _solve_piecewise_extrema_exact(" in text:
    raise SystemExit("Task 6 Piecewise extrema solver already present; guarded patch will not reapply")

marker = "\ndef solve_extrema_exact(\n"
if text.count(marker) != 1:
    raise SystemExit("Task 6 patch guard failed: expected exactly one solve_extrema_exact definition")

source_text = SOURCE.read_text(encoding="utf-8")
prefix = "append = r'''"
start = source_text.index(prefix) + len(prefix)
end = source_text.index("\n'''\n\n# Remove a deliberately unreachable helper stub", start)
append = source_text[start:end]

bad_start = append.find("\n\ndef _piecewise_near_breakpoint_quantity(")
bad_end = append.find("\n\ndef _piecewise_local_role_at_breakpoint(", bad_start)
if bad_start < 0 or bad_end < 0:
    raise SystemExit("Task 6 harness correction guard failed: invalid stub block not found")
append = append[:bad_start] + append[bad_end:]

text = text.replace(marker, "\ndef _solve_continuous_extrema_exact(\n", 1)
TARGET.write_text(text + append, encoding="utf-8")
