"""Render every sheet of his book with two source trees and list what differs."""
import concurrent.futures as cf
import hashlib
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(r"C:\Users\elias\Documents\EngCalc - Matrix Structural Analysis")
HERE = pathlib.Path(__file__).parent
PY = r"C:\Users\elias\engcalc\.venv\Scripts\python.exe"
TREES = {"main": HERE / "main-tree" / "src", "branch": HERE / "branch-tree" / "src"}
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 180


def render(tree: str, sheet: pathlib.Path):
    env = dict(os.environ, PYTHONPATH=str(TREES[tree]), PYTHONIOENCODING="utf-8")
    try:
        done = subprocess.run(
            [PY, str(HERE / "run.py"), str(sheet)], capture_output=True, text=True,
            encoding="utf-8", errors="replace", env=env, timeout=LIMIT,
        )
        return done.stdout + "\n--stderr--\n" + done.stderr[-2000:]
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def both(sheet: pathlib.Path):
    return str(sheet.relative_to(ROOT)), render("main", sheet), render("branch", sheet)


def main():
    folders = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else None
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    sheets = sorted(
        sheet for sheet in ROOT.rglob("*.eng")
        if folders is None or sheet.parent.name in folders
    )
    out = HERE / "corpus_out"
    out.mkdir(exist_ok=True)
    report = {}
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        for name, a, b in pool.map(both, sheets):
            if a == "TIMEOUT" or b == "TIMEOUT":
                status = f"timeout(main={a == 'TIMEOUT'}, branch={b == 'TIMEOUT'})"
            elif a == b:
                status = "same"
            elif render("main", ROOT / name) != a:
                status = "unstable-on-main"
            else:
                status = "differs"
                key = hashlib.md5(name.encode()).hexdigest()[:8]
                (out / f"{key}.main.txt").write_text(a, encoding="utf-8")
                (out / f"{key}.branch.txt").write_text(b, encoding="utf-8")
                status += f" {key}"
            report[name] = status
            print(name, status, flush=True)
    (HERE / "corpus_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    counts = {}
    for status in report.values():
        counts[status.split()[0]] = counts.get(status.split()[0], 0) + 1
    print(counts)


if __name__ == "__main__":
    main()
