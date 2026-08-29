from pathlib import Path

path = Path("src/engcalc_colab/engine.py")
text = path.read_text()


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one anchor, found {count}: {old[:80]!r}")
    text = text.replace(old, new, 1)


replace_once(
    "    PlotResult,\n    PlotSeries,\n    UserFunction,\n)",
    "    PlotResult,\n    PlotSeries,\n    TableColumn,\n    TableResult,\n    UserFunction,\n)",
)
replace_once(
    "from .numeric import NumericContext\n",
    "from .numeric import NumericContext\nfrom .tables import normalize_explicit_points, normalize_uniform_points\n",
)
replace_once(
    "@dataclass(frozen=True)\nclass _PlotEvaluation:\n    display_label: str\n    variable: str\n    x_values: tuple\n    series: tuple[PlotSeries, ...]\n    kind: str = \"plot\"\n    source_series: tuple[PlotSeries, ...] = ()\n    source_labels: tuple[str, ...] = ()\n    governing_max: tuple[int, ...] | None = None\n    governing_min: tuple[int, ...] | None = None\n    envelope_mode: str | None = None\n    governing_signed: tuple | None = None\n\n\nclass EngineeringEngine:",
    "@dataclass(frozen=True)\nclass _PlotEvaluation:\n    display_label: str\n    variable: str\n    x_values: tuple\n    series: tuple[PlotSeries, ...]\n    kind: str = \"plot\"\n    source_series: tuple[PlotSeries, ...] = ()\n    source_labels: tuple[str, ...] = ()\n    governing_max: tuple[int, ...] | None = None\n    governing_min: tuple[int, ...] | None = None\n    envelope_mode: str | None = None\n    governing_signed: tuple | None = None\n\n\n@dataclass(frozen=True)\nclass _TableEvaluation:\n    variable: str\n    point_unit: object\n    point_values: tuple\n    columns: tuple[TableColumn, ...]\n    mode: str\n    first_symbolic_expression: object\n\n\nclass EngineeringEngine:",
)
replace_once(
    "        | PartialNumericEvaluationResult\n        | PlotResult\n    ):",
    "        | PartialNumericEvaluationResult\n        | PlotResult\n        | TableResult\n    ):",
)
replace_once(
    "            if evaluator.partial_numeric_evaluation is not None:\n",
    "            if evaluator.table_evaluation is not None:\n                table_evaluation = evaluator.table_evaluation\n                if statement.target is not None:\n                    raise EngEvaluationError(\"table must be a standalone statement\")\n                return TableResult(\n                    statement=statement,\n                    variable=table_evaluation.variable,\n                    point_unit=table_evaluation.point_unit,\n                    point_values=table_evaluation.point_values,\n                    columns=table_evaluation.columns,\n                    mode=table_evaluation.mode,\n                )\n\n            if evaluator.partial_numeric_evaluation is not None:\n",
)
replace_once(
    "        self.plot_evaluation: _PlotEvaluation | None = None\n        self.symbol_overrides: dict[str, sp.Symbol] = {}\n",
    "        self.plot_evaluation: _PlotEvaluation | None = None\n        self.table_evaluation: _TableEvaluation | None = None\n        self.symbol_overrides: dict[str, sp.Symbol] = {}\n",
)
replace_once(
    "        if name == \"envelope\":\n            return self._evaluate_envelope(node)\n\n        if name == \"numeric\":",
    "        if name == \"envelope\":\n            return self._evaluate_envelope(node)\n\n        if name == \"table\":\n            return self._evaluate_table(node)\n\n        if name == \"numeric\":",
)
replace_once(
    "    def _evaluate_plot(self, node: ast.Call):\n",
    '''    def _resolve_table_numeric_value(self, node: ast.AST):\n        value = self._resolve_numeric_user_function_argument(node)\n        if isinstance(value, sp.Expr):\n            _, value = self.engine.numeric_context.evaluate_symbolic(value)\n        return value\n\n    def _evaluate_table(self, node: ast.Call):\n        args = node.args\n        point_list = None\n        declared_unit_node = None\n\n        if len(args) >= 3 and isinstance(args[-1], ast.List):\n            response_nodes = args[:-2]\n            variable_node = args[-2]\n            point_list = args[-1]\n        elif len(args) >= 4 and isinstance(args[-2], ast.List):\n            response_nodes = args[:-3]\n            variable_node = args[-3]\n            point_list = args[-2]\n            declared_unit_node = args[-1]\n        else:\n            response_nodes = args[:-4]\n            variable_node = args[-4]\n            lower_node, upper_node, count_node = args[-3:]\n\n        if not response_nodes:\n            raise EngEvaluationError(\"table requires at least one response expression\")\n        if not isinstance(variable_node, ast.Name):\n            raise EngEvaluationError(\"table variable must be a symbolic identifier\")\n        variable = variable_node.id\n        context = self.engine.numeric_context\n\n        if point_list is None:\n            lower = self._resolve_table_numeric_value(lower_node)\n            upper = self._resolve_table_numeric_value(upper_node)\n            count = self._resolve_table_numeric_value(count_node)\n            point_values = normalize_uniform_points(context, lower, upper, count)\n            mode = \"uniform\"\n        else:\n            raw_points = tuple(\n                self._resolve_table_numeric_value(element)\n                for element in point_list.elts\n            )\n            declared_unit = None\n            if declared_unit_node is not None:\n                declared_unit = context.evaluate_unit_expression(\n                    ast.Expression(body=declared_unit_node)\n                )\n            point_values = normalize_explicit_points(\n                context,\n                raw_points,\n                declared_unit,\n            )\n            mode = \"explicit\"\n\n        resolved_responses = [\n            self._resolve_response_expression(item, variable)\n            for item in response_nodes\n        ]\n\n        columns = []\n        canonical_unit = None\n        for response in resolved_responses:\n            values = []\n            for point in point_values:\n                _, quantity = context.evaluate_symbolic(\n                    response.comparison_expression,\n                    overrides={variable: point},\n                )\n                values.append(quantity)\n\n            if canonical_unit is None:\n                canonical_unit = values[0].units\n            try:\n                normalized_values = tuple(\n                    value.to(canonical_unit)\n                    for value in values\n                )\n            except DimensionalityError as exc:\n                raise EngEvaluationError(\n                    \"table response columns have incompatible units\"\n                ) from exc\n\n            columns.append(\n                TableColumn(\n                    display_label=response.display_label,\n                    unit=canonical_unit,\n                    values=normalized_values,\n                )\n            )\n\n        self.table_evaluation = _TableEvaluation(\n            variable=variable,\n            point_unit=point_values[0].units,\n            point_values=tuple(point_values),\n            columns=tuple(columns),\n            mode=mode,\n            first_symbolic_expression=resolved_responses[0].comparison_expression,\n        )\n        return resolved_responses[0].comparison_expression\n\n    def _evaluate_plot(self, node: ast.Call):\n''',
)

path.write_text(text)
