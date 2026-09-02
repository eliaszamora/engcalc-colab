"""Execute each exercise line by line against main and record where it breaks."""

import json
import pathlib
import sys
import matplotlib

matplotlib.use("Agg")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gap_map_exercises import EXERCISES  # noqa: E402

from engcalc_colab.engine import EngineeringEngine  # noqa: E402
from engcalc_colab.models import ParsedHeading  # noqa: E402
from engcalc_colab.parser import parse_cell  # noqa: E402


def run_exercise(source: str):
    """Run every line. A failing line is recorded and execution continues."""
    engine = EngineeringEngine()
    trace = []
    for line in [ln for ln in source.strip().splitlines() if ln.strip()]:
        try:
            for item in parse_cell(line):
                if isinstance(item, ParsedHeading):
                    continue
                engine.evaluate(item)
            trace.append({"line": line.strip(), "ok": True, "error": None})
        except Exception as exc:  # noqa: BLE001 - the error type is the datum
            trace.append(
                {
                    "line": line.strip(),
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    return trace


results = []
for title, area, source in EXERCISES:
    trace = run_exercise(source)
    broken = [step for step in trace if not step["ok"]]
    results.append(
        {
            "title": title,
            "area": area,
            "lines": len(trace),
            "broken": len(broken),
            "trace": trace,
        }
    )

with open("gapmap.json", "w", encoding="utf-8") as handle:
    json.dump(results, handle, indent=2, ensure_ascii=False)

print(f"{'ejercicio':52s} {'lineas':>7s} {'rotas':>6s}")
print("-" * 68)
total_lines = total_broken = 0
for entry in results:
    total_lines += entry["lines"]
    total_broken += entry["broken"]
    mark = "" if entry["broken"] == 0 else "  <-"
    print(f"{entry['title']:52s} {entry['lines']:>7d} {entry['broken']:>6d}{mark}")
print("-" * 68)
clean = sum(1 for e in results if e["broken"] == 0)
print(f"{'TOTAL':52s} {total_lines:>7d} {total_broken:>6d}")
print(f"ejercicios que corren enteros: {clean}/{len(results)}")
