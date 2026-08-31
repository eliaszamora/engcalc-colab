from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Task 6 corrective anchor not found: {label}")
    return text.replace(old, new, 1)


def replace_in_function(text: str, function_name: str, old: str, new: str) -> str:
    start = text.find(f"def {function_name}(")
    if start == -1:
        raise SystemExit(f"Task 6 function not found: {function_name}")
    end = text.find("\ndef ", start + 4)
    if end == -1:
        end = len(text)
    segment = text[start:end]
    if new in segment:
        return text
    if old not in segment:
        raise SystemExit(f"Task 6 corrective anchor not found in {function_name}")
    segment = segment.replace(old, new, 1)
    return text[:start] + segment + text[end:]


# Preserve the physical unit of zero-valued bounds by allowing the evaluator to
# supply quantities resolved directly from the original AST before SymPy folds
# expressions such as 0*m to Integer(0).
path = Path("src/engcalc_colab/characteristics.py")
text = path.read_text()
old = '''def normalize_analysis_domain(
    context,
    lower_expression,
    upper_expression,
) -> AnalysisDomain:
    lower_symbolic = sp.sympify(lower_expression)
    upper_symbolic = sp.sympify(upper_expression)
    lower = _evaluate_domain_bound(context, lower_symbolic)
    upper = _evaluate_domain_bound(context, upper_symbolic)
'''
new = '''def normalize_analysis_domain(
    context,
    lower_expression,
    upper_expression,
    *,
    lower_quantity=None,
    upper_quantity=None,
) -> AnalysisDomain:
    lower_symbolic = sp.sympify(lower_expression)
    upper_symbolic = sp.sympify(upper_expression)
    lower = (
        lower_quantity
        if lower_quantity is not None
        else _evaluate_domain_bound(context, lower_symbolic)
    )
    upper = (
        upper_quantity
        if upper_quantity is not None
        else _evaluate_domain_bound(context, upper_symbolic)
    )
'''
text = replace_once(text, old, new, "normalize_analysis_domain physical quantities")

# Exact/boundary candidates can themselves contain direct unit literals.
text = replace_in_function(
    text,
    "_evaluate_root_candidate",
    '''    fixed_overrides = context.unit_literal_overrides(
        expression,
        overrides,
    )
''',
    '''    fixed_overrides = context.unit_literal_overrides(
        expression,
        overrides,
    )
    fixed_overrides = context.unit_literal_overrides(candidate, fixed_overrides)
''',
)
text = replace_in_function(
    text,
    "_evaluate_intersection_candidate",
    '''    fixed_overrides = dict(overrides or {})
''',
    '''    fixed_overrides = context.unit_literal_overrides(candidate, overrides)
''',
)
text = replace_in_function(
    text,
    "_evaluate_extrema_candidate",
    '''    fixed_overrides = dict(overrides or {})
    candidate = sp.sympify(candidate)
''',
    '''    candidate = sp.sympify(candidate)
    fixed_overrides = context.unit_literal_overrides(candidate, overrides)
''',
)
text = replace_in_function(
    text,
    "_piecewise_boundary_candidates",
    '''            _, quantity = context.evaluate_symbolic(
                candidate,
                overrides=dict(overrides or {}),
            )
''',
    '''            _, quantity = context.evaluate_symbolic(
                candidate,
                overrides=context.unit_literal_overrides(candidate, overrides),
            )
''',
)
path.write_text(text)


# Resolve physical domain values from the original AST. This preserves 0*m and
# keeps table's already-correct numeric AST route behind the same helper.
path = Path("src/engcalc_colab/engine.py")
text = path.read_text()
anchor = '''    @staticmethod
    def _operation_specific_characteristic_error(name: str, exc: EngEvaluationError):
'''
insert = '''    def _resolve_domain_numeric_value(self, node: ast.AST):
        value = self._resolve_numeric_user_function_argument(node)
        if isinstance(value, sp.Expr):
            _, value = self.engine.numeric_context.evaluate_symbolic(
                value,
                overrides=self.engine.numeric_context.unit_literal_overrides(value),
            )
        return value

    @staticmethod
    def _operation_specific_characteristic_error(name: str, exc: EngEvaluationError):
'''
text = replace_once(text, anchor, insert, "domain AST numeric resolver")

old = '''        lower_expression = self.visit(lower_node)
        upper_expression = self.visit(upper_node)
        try:
            domain = normalize_analysis_domain(
                self.engine.numeric_context,
                lower_expression,
                upper_expression,
            )
'''
new = '''        lower_expression = self.visit(lower_node)
        upper_expression = self.visit(upper_node)
        lower_quantity = self._resolve_domain_numeric_value(lower_node)
        upper_quantity = self._resolve_domain_numeric_value(upper_node)
        try:
            domain = normalize_analysis_domain(
                self.engine.numeric_context,
                lower_expression,
                upper_expression,
                lower_quantity=lower_quantity,
                upper_quantity=upper_quantity,
            )
'''
text = replace_once(text, old, new, "characteristic AST bound quantities")

old = '''    def _resolve_table_numeric_value(self, node: ast.AST):
        value = self._resolve_numeric_user_function_argument(node)
        if isinstance(value, sp.Expr):
            _, value = self.engine.numeric_context.evaluate_symbolic(
                value,
                overrides=self.engine.numeric_context.unit_literal_overrides(value),
            )
        return value
'''
new = '''    def _resolve_table_numeric_value(self, node: ast.AST):
        return self._resolve_domain_numeric_value(node)
'''
text = replace_once(text, old, new, "table shared domain numeric resolver")

old = '''        start_expression = self.visit(start_node)
        end_expression = self.visit(end_node)
        _, start_quantity = self.engine.numeric_context.evaluate_symbolic(
            start_expression,
            overrides=self.engine.numeric_context.unit_literal_overrides(start_expression),
        )
        _, end_quantity = self.engine.numeric_context.evaluate_symbolic(
            end_expression,
            overrides=self.engine.numeric_context.unit_literal_overrides(end_expression),
        )
        start_quantity, end_quantity = self.engine.numeric_context.normalize_plot_bounds(
            start_quantity,
            end_quantity,
        )
        analysis_domain = None
        if call_name == "plot":
            analysis_domain = normalize_analysis_domain(
                self.engine.numeric_context,
                start_expression,
                end_expression,
            )
'''
new = '''        start_expression = self.visit(start_node)
        end_expression = self.visit(end_node)
        start_quantity = self._resolve_domain_numeric_value(start_node)
        end_quantity = self._resolve_domain_numeric_value(end_node)
        start_quantity, end_quantity = self.engine.numeric_context.normalize_plot_bounds(
            start_quantity,
            end_quantity,
        )
        analysis_domain = None
        if call_name == "plot":
            analysis_domain = normalize_analysis_domain(
                self.engine.numeric_context,
                start_expression,
                end_expression,
                lower_quantity=start_quantity,
                upper_quantity=end_quantity,
            )
'''
text = replace_once(text, old, new, "plot AST bound quantities")
path.write_text(text)

print("Applied Task 6 zero-bound preservation and boundary-candidate correction.")
