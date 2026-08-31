from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path("src/engcalc_colab/characteristics")


class Inventory(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.stack: list[str] = []
        self.calls: list[tuple[int, str, str, tuple[str, ...]]] = []

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
        if isinstance(func, ast.Attribute) and func.attr == "evaluate_symbolic":
            receiver = ast.unparse(func.value)
            keywords = tuple(sorted(keyword.arg or "**" for keyword in node.keywords))
            self.calls.append(
                (
                    node.lineno,
                    self.stack[-1] if self.stack else "<module>",
                    receiver,
                    keywords,
                )
            )
        self.generic_visit(node)


def main() -> None:
    all_calls: list[tuple[str, int, str, str, tuple[str, ...]]] = []
    for path in sorted(ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        inventory = Inventory(path)
        inventory.visit(tree)
        for lineno, function, receiver, keywords in inventory.calls:
            all_calls.append((path.name, lineno, function, receiver, keywords))

    print(f"EVALUATE_SYMBOLIC_CALL_COUNT={len(all_calls)}")
    without_overrides = 0
    for filename, lineno, function, receiver, keywords in all_calls:
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
    assert all_calls, "expected characteristic evaluate_symbolic calls"
    print("N3_EVALUATE_SYMBOLIC_INVENTORY=PASS")


if __name__ == "__main__":
    main()
