from pathlib import Path

paths = [
    Path('.github/workflows/v091-task1-tdd.yml'),
    Path('.github/workflows/v091-task1-parser-green.yml'),
    Path('.github/workflows/v091-task1-models-green.yml'),
    Path('.github/workflows/v091-task1-full-gate.yml'),
    Path('.github/scripts/v091_task1_apply.py'),
    Path('.github/scripts/v091_task1_models_apply.py'),
]
for path in paths:
    if path.exists():
        path.unlink()
