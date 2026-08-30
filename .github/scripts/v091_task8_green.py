from pathlib import Path

PATH = Path("src/engcalc_colab/engine.py")
text = PATH.read_text(encoding="utf-8")

if "class _CharacteristicEvaluation:" in text:
    raise SystemExit("Task 8 engine dispatch already present; guarded patch will not reapply")

# 1. Import the already-validated characteristic core.
anchor = "from .errors import (\n"
if anchor not in text:
    raise SystemExit("Task 8 patch guard failed: errors import anchor not found")
characteristics_import = (
    "from .characteristics import (\n"
    "    normalize_analysis_domain,\n"
    "    solve_extrema_exact,\n"
    "    solve_intersections_exact,\n"
    "    solve_roots_exact,\n"
    ")\n"
)
text = text.replace(anchor, characteristics_import + anchor, 1)

# 2. Import the public typed result models that already exist from Task 1.
old = """    EigenvectorSet,
    EvaluationResult,
    MatrixNumericGuard,
"""
new = """    EigenvectorSet,
    EvaluationResult,
    ExtremaResult,
    IntersectionsResult,
    MatrixNumericGuard,
"""
if old not in text:
    raise SystemExit("Task 8 patch guard failed: first model import anchor not found")
text = text.replace(old, new, 1)

old = """    PlotResult,
    PlotSeries,
    TableColumn,
"""
new = """    PlotResult,
    PlotSeries,
    RootsResult,
    TableColumn,
"""
if old not in text:
    raise SystemExit("Task 8 patch guard failed: second model import anchor not found")
text = text.replace(old, new, 1)

# 3. Private immutable descriptor between evaluator and EngineeringEngine.evaluate.
marker = "\n\nclass EngineeringEngine:\n"
if text.count(marker) != 1:
    raise SystemExit("Task 8 patch guard failed: EngineeringEngine anchor mismatch")
descriptor = r'''

@dataclass(frozen=True)
class _CharacteristicEvaluation:
    kind: str
    variable: str
    lower_quantity: object
    upper_quantity: object
    points: tuple
    intervals: tuple
    first_symbolic_expression: object
    display_label: str | None = None
    left_label: str | None = None
    right_label: str | None = None
    unbounded_above: bool = False
    unbounded_below: bool = False
'''
text = text.replace(marker, descriptor + marker, 1)

# 4. Public return union.
old = """        | PartialMatrixNumericEvaluationResult
        | PlotResult
        | TableResult
    ):
"""
new = """        | PartialMatrixNumericEvaluationResult
        | PlotResult
        | TableResult
        | RootsResult
        | IntersectionsResult
        | ExtremaResult
    ):
"""
if old not in text:
    raise SystemExit("Task 8 patch guard failed: evaluate return union anchor not found")
text = text.replace(old, new, 1)

# 5. Wrap private descriptor into immutable public results before numeric result paths.
marker = """            if evaluator.partial_matrix_numeric_evaluation is not None:
"""
if text.count(marker) != 1:
    raise SystemExit("Task 8 patch guard failed: result wrapping anchor mismatch")
wrap = r'''            if evaluator.characteristic_evaluation is not None:
                characteristic = evaluator.characteristic_evaluation
                if statement.target is not None:
                    raise EngEvaluationError(
                        f"{characteristic.kind} must be a standalone statement"
                    )
                if characteristic.kind == "roots":
                    return RootsResult(
                        statement=statement,
                        display_label=characteristic.display_label or "response",
                        variable=characteristic.variable,
                        lower_quantity=characteristic.lower_quantity,
                        upper_quantity=characteristic.upper_quantity,
                        points=characteristic.points,
                        intervals=characteristic.intervals,
                    )
                if characteristic.kind == "intersections":
                    return IntersectionsResult(
                        statement=statement,
                        left_label=characteristic.left_label or "left",
                        right_label=characteristic.right_label or "right",
                        variable=characteristic.variable,
                        lower_quantity=characteristic.lower_quantity,
                        upper_quantity=characteristic.upper_quantity,
                        points=characteristic.points,
                        intervals=characteristic.intervals,
                    )
                if characteristic.kind == "extrema":
                    return ExtremaResult(
                        statement=statement,
                        display_label=characteristic.display_label or "response",
                        variable=characteristic.variable,
                        lower_quantity=characteristic.lower_quantity,
                        upper_quantity=characteristic.upper_quantity,
                        points=characteristic.points,
                        intervals=characteristic.intervals,
                        unbounded_above=characteristic.unbounded_above,
                        unbounded_below=characteristic.unbounded_below,
                    )
                raise EngEvaluationError(
                    f"unsupported characteristic result '{characteristic.kind}'"
                )

'''
text = text.replace(marker, wrap + marker, 1)

# 6. Evaluator state.
old = """        self.plot_evaluation: _PlotEvaluation | None = None
        self.table_evaluation: _TableEvaluation | None = None
        self.symbol_overrides: dict[str, sp.Symbol] = {}
"""
new = """        self.plot_evaluation: _PlotEvaluation | None = None
        self.table_evaluation: _TableEvaluation | None = None
        self.characteristic_evaluation: _CharacteristicEvaluation | None = None
        self.symbol_overrides: dict[str, sp.Symbol] = {}
"""
if old not in text:
    raise SystemExit("Task 8 patch guard failed: evaluator state anchor not found")
text = text.replace(old, new, 1)

# 7. Dispatch before generic call argument evaluation.
old = """        name = node.func.id

        if name == "piecewise":
"""
new = """        name = node.func.id

        if name in {"roots", "intersections", "extrema"}:
            return self._evaluate_characteristic(node, name)

        if name == "piecewise":
"""
if old not in text:
    raise SystemExit("Task 8 patch guard failed: visit_Call dispatch anchor not found")
text = text.replace(old, new, 1)

# 8. Dedicated characteristic evaluator. It resolves through the existing response
#    resolver and delegates all mathematics to characteristics.py.
marker = "\n    def _resolve_table_numeric_value(self, node: ast.AST):\n"
if text.count(marker) != 1:
    raise SystemExit("Task 8 patch guard failed: helper insertion anchor mismatch")
helper = r'''
    @staticmethod
    def _operation_specific_characteristic_error(name: str, exc: EngEvaluationError):
        message = str(exc)
        if message.startswith("characteristic domain"):
            message = name + message[len("characteristic"):]
        return EngEvaluationError(message)

    def _evaluate_characteristic(self, node: ast.Call, name: str):
        if node.keywords:
            raise EngEvaluationError(
                f"{name} accepts positional arguments only"
            )

        if name == "intersections":
            self._require_arity(
                name,
                node.args,
                5,
                "left_response, right_response, variable, lower, upper",
            )
            response_nodes = node.args[:2]
            variable_node = node.args[2]
            lower_node, upper_node = node.args[3:]
        else:
            self._require_arity(
                name,
                node.args,
                4,
                "response, variable, lower, upper",
            )
            response_nodes = node.args[:1]
            variable_node = node.args[1]
            lower_node, upper_node = node.args[2:]

        if not isinstance(variable_node, ast.Name):
            raise EngEvaluationError(
                f"{name} variable must be a symbolic identifier"
            )
        variable_name = variable_node.id
        variable_symbol = self.engine.resolve_symbol(variable_name)

        lower_expression = self.visit(lower_node)
        upper_expression = self.visit(upper_node)
        try:
            domain = normalize_analysis_domain(
                self.engine.numeric_context,
                lower_expression,
                upper_expression,
            )
        except EngEvaluationError as exc:
            raise self._operation_specific_characteristic_error(name, exc) from None

        sentinel = object()
        previous = self.symbol_overrides.get(variable_name, sentinel)
        self.symbol_overrides[variable_name] = variable_symbol
        try:
            resolved = tuple(
                self._resolve_response_expression(response_node, variable_name)
                for response_node in response_nodes
            )
        finally:
            if previous is sentinel:
                self.symbol_overrides.pop(variable_name, None)
            else:
                self.symbol_overrides[variable_name] = previous

        if any(
            is_matrix(item.signed_expression)
            or is_matrix(item.comparison_expression)
            for item in resolved
        ):
            raise EngEvaluationError(
                f"{name} response must be scalar; index the matrix first, "
                "for example A[1,1]"
            )

        if name == "roots":
            response = resolved[0]
            points, intervals, unresolved = solve_roots_exact(
                response.comparison_expression,
                variable_symbol,
                domain,
                self.engine.numeric_context,
                source_label=response.display_label,
            )
            if unresolved:
                raise EngEvaluationError(
                    "roots characteristic analysis could not resolve a safe solution set"
                )
            self.characteristic_evaluation = _CharacteristicEvaluation(
                kind="roots",
                variable=variable_name,
                lower_quantity=domain.lower_quantity,
                upper_quantity=domain.upper_quantity,
                points=tuple(points),
                intervals=tuple(intervals),
                first_symbolic_expression=response.comparison_expression,
                display_label=response.display_label,
            )
            return response.comparison_expression

        if name == "intersections":
            left, right = resolved
            points, intervals, unresolved = solve_intersections_exact(
                left.comparison_expression,
                right.comparison_expression,
                variable_symbol,
                domain,
                self.engine.numeric_context,
                left_label=left.display_label,
                right_label=right.display_label,
            )
            if unresolved:
                raise EngEvaluationError(
                    "intersections characteristic analysis could not resolve "
                    "a safe solution set"
                )
            self.characteristic_evaluation = _CharacteristicEvaluation(
                kind="intersections",
                variable=variable_name,
                lower_quantity=domain.lower_quantity,
                upper_quantity=domain.upper_quantity,
                points=tuple(points),
                intervals=tuple(intervals),
                first_symbolic_expression=left.comparison_expression,
                left_label=left.display_label,
                right_label=right.display_label,
            )
            return left.comparison_expression

        response = resolved[0]
        points, intervals, unbounded_above, unbounded_below, unresolved = (
            solve_extrema_exact(
                response.comparison_expression,
                variable_symbol,
                domain,
                self.engine.numeric_context,
                source_label=response.display_label,
            )
        )
        if unresolved:
            raise EngEvaluationError(
                "extrema characteristic analysis could not resolve a safe solution set"
            )
        self.characteristic_evaluation = _CharacteristicEvaluation(
            kind="extrema",
            variable=variable_name,
            lower_quantity=domain.lower_quantity,
            upper_quantity=domain.upper_quantity,
            points=tuple(points),
            intervals=tuple(intervals),
            first_symbolic_expression=response.comparison_expression,
            display_label=response.display_label,
            unbounded_above=unbounded_above,
            unbounded_below=unbounded_below,
        )
        return response.comparison_expression
'''
text = text.replace(marker, "\n" + helper + marker, 1)

PATH.write_text(text, encoding="utf-8")
