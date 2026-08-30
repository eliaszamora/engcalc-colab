from pathlib import Path

engine_path = Path("src/engcalc_colab/engine.py")
engine = engine_path.read_text(encoding="utf-8")

old_table = '''        resolved_responses = [\n            self._resolve_response_expression(item, variable)\n            for item in response_nodes\n        ]\n\n        columns = []\n'''
new_table = '''        resolved_responses = [\n            self._resolve_response_expression(item, variable)\n            for item in response_nodes\n        ]\n        if any(\n            is_matrix(response.signed_expression)\n            or is_matrix(response.comparison_expression)\n            for response in resolved_responses\n        ):\n            raise EngEvaluationError("table response must be scalar")\n\n        columns = []\n'''
assert engine.count(old_table) == 1, engine.count(old_table)
engine = engine.replace(old_table, new_table, 1)

old_plot = '''        resolved_expressions = [\n            self._resolve_response_expression(item, variable)\n            for item in expression_nodes\n        ]\n        source_labels = [item.source_label for item in resolved_expressions]\n'''
new_plot = '''        resolved_expressions = [\n            self._resolve_response_expression(item, variable)\n            for item in expression_nodes\n        ]\n        if any(\n            is_matrix(expression.signed_expression)\n            or is_matrix(expression.comparison_expression)\n            for expression in resolved_expressions\n        ):\n            raise EngEvaluationError(f"{call_name} response must be scalar")\n        source_labels = [item.source_label for item in resolved_expressions]\n'''
assert engine.count(old_plot) == 1, engine.count(old_plot)
engine = engine.replace(old_plot, new_plot, 1)
engine_path.write_text(engine, encoding="utf-8")

readme_path = Path("README.md")
readme = readme_path.read_text(encoding="utf-8")
anchor = "Current version: **0.8.0**.\n\n"
assert readme.count(anchor) == 1, readme.count(anchor)
section = '''## Matrix/CAS — 0.9.0 development scope\n\nEngCalc's Matrix/CAS layer is currently being completed on the 0.9.0 development branch while the released runtime version remains 0.8.0. Matrix literals use mathematical/MATLAB-inspired syntax with mandatory commas between columns and semicolons between rows:\n\n```text\nA = [a, b; c, d]\nr = [a, b, c]\nv = [a; b; c]\n```\n\nMatrices use **1-based indexing**, so `A[1, 1]` is the upper-left scalar entry. Row and column vectors additionally accept one-index shorthand. Matrix algebra is exact and SymPy-backed: `A*B` is mathematical matrix multiplication, with constructors and operations such as `identity`, `zeros`, `diag`, `transpose`, `det`, `inv`, `trace`, `rank`, `rref`, `norm`, `size`, `eigenvals` and `eigenvects`. Exact linear systems use `solve(A, b)`.\n\nNumerical evaluation remains Pint-backed. `numeric(A)` evaluates a symbolic matrix cell by cell. Homogeneous matrices can share a compatible display/target unit, while heterogeneous engineering matrices preserve the physical dimensionality of each entry instead of inventing one matrix-wide unit. Matrix-valued functions, Piecewise scalar cells and exact `solve(A, b)` results can all flow into `numeric(...)`.\n\nExisting engineering table/plot APIs remain scalar-response APIs by design. An indexed matrix entry such as `K(x)[1, 1]` may be used in `table(...)`, `plot(...)` or `envelope(...)`; **whole-matrix** responses are rejected with a concise scalar-response diagnostic. Whole-matrix tables, plots and envelopes are outside the 0.9.0 core scope.\n\n'''
readme = readme.replace(anchor, anchor + section, 1)
readme_path.write_text(readme, encoding="utf-8")
