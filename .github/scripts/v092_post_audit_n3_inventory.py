from __future__ import annotations

import argparse
import ast
from collections import Counter
from pathlib import Path


ROOT = Path("src/engcalc_colab/characteristics")
SOLVER_BOUNDARIES = {
    "solve_roots_exact": 1,
    "solve_intersections_exact": 2,
    "solve_extrema_exact": 1,
}


class Inventory(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.stack: list[str] = []
        self.evaluate_calls: list[tuple[int, str, str, tuple[str, ...]]] = []
        self.unit_literal_calls: list[tuple[int, str, str]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        function = self.stack[-1] if self.stack else "<module>"
        if isinstance(func, ast.Attribute) and func.attr == "evaluate_symbolic":
            receiver = ast.unparse(func.value)
            keywords = tuple(sorted(keyword.arg or "**" for keyword in node.keywords))
            self.evaluate_calls.append((node.lineno, function, receiver, keywords))
        if isinstance(func, ast.Attribute) and func.attr == "unit_literal_overrides":
            self.unit_literal_calls.append((node.lineno, function, ast.unparse(func.value)))
        self.generic_visit(node)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-solver-boundaries", action="store_true")
    args = parser.parse_args()

    evaluate_calls: list[tuple[str, int, str, str, tuple[str, ...]]] = []
    unit_literal_calls: list[tuple[str, int, str, str]] = []
    for path in sorted(ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        inventory = Inventory(path)
        inventory.visit(tree)
        for lineno, function, receiver, keywords in inventory.evaluate_calls:
            evaluate_calls.append((path.name, lineno, function, receiver, keywords))
        for lineno, function, receiver in inventory.unit_literal_calls:
            unit_literal_calls.append((path.name, lineno, function, receiver))

    print(f"EVALUATE_SYMBOLIC_CALL_COUNT={len(evaluate_calls)}")
    without_overrides = 0
    for filename, lineno, function, receiver, keywords in evaluate_calls:
        has_overrides = "overrides" in keywords
        if not has_overrides:
            without_overrides += 1
        print(
            "CALL "
            f"file={filename} line={lineno} function={function} "
            f"receiver={receiver} overrides={'yes' if has_overrides else 'no'} "
            f"keywords={','.join(keywords) or '-'}"
        )
    print(f"EVALUATE_SYMBOLIC_WITHOUT_OVERRIDES={without_overrides}")

    boundary_counts = Counter(
        function
        for _filename, _lineno, function, _receiver in unit_literal_calls
        if function in SOLVER_BOUNDARIES
    )
    for filename, lineno, function, receiver in unit_literal_calls:
        if function in SOLVER_BOUNDARIES:
            print(
                "BOUNDARY "
                f"file={filename} line={lineno} function={function} receiver={receiver}"
            )
    for function, expected in SOLVER_BOUNDARIES.items():
        print(f"BOUNDARY_COUNT {function}={boundary_counts[function]} expected={expected}")

    assert evaluate_calls, "expected characteristic evaluate_symbolic calls"
    assert without_overrides == 0, "all characteristic evaluate_symbolic calls must receive overrides"
    if args.require_solver_boundaries:
        assert boundary_counts == Counter(SOLVER_BOUNDARIES), (
            f"solver boundary unit-literal resolution mismatch: {boundary_counts}"
        )
        print("N3_SOLVER_BOUNDARY_INVENTORY=PASS")
    print("N3_EVALUATE_SYMBOLIC_INVENTORY=PASS")


if __name__ == "__main__":
    main()
