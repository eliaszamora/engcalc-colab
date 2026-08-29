from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise SystemExit(f"expected Task 3 block not found: {label}")


models_path = Path("src/engcalc_colab/models.py")
models = models_path.read_text(encoding="utf-8")

models = replace_once(
    models,
'''@dataclass(frozen=True)
class NumericEvaluationResult:
    statement: ParsedStatement
    symbolic_expression: Any
    substitutions: dict[str, Any]
    quantity: Any
    display_name: str | None = None
    display_argument: Any | None = None


@dataclass(frozen=True)
class PartialNumericEvaluationResult:
    statement: ParsedStatement
    symbolic_expression: Any
    substitutions: dict[str, Any]
    unresolved_symbols: tuple[str, ...]
    evaluated_terms: tuple[tuple[int, Any], ...] | None = None
    display_name: str | None = None
    display_argument: Any | None = None
''',
'''@dataclass(frozen=True, init=False)
class NumericEvaluationResult:
    statement: ParsedStatement
    symbolic_expression: Any
    substitutions: dict[str, Any]
    quantity: Any
    display_name: str | None = None
    display_arguments: tuple[Any, ...] | None = None

    def __init__(
        self,
        statement: ParsedStatement,
        symbolic_expression: Any,
        substitutions: dict[str, Any],
        quantity: Any,
        display_name: str | None = None,
        display_arguments: tuple[Any, ...] | None = None,
        *,
        display_argument: Any | None = None,
    ) -> None:
        if display_arguments is not None and display_argument is not None:
            raise TypeError("provide either display_arguments or display_argument, not both")
        normalized = (
            (display_argument,)
            if display_argument is not None
            else tuple(display_arguments) if display_arguments is not None else None
        )
        object.__setattr__(self, "statement", statement)
        object.__setattr__(self, "symbolic_expression", symbolic_expression)
        object.__setattr__(self, "substitutions", substitutions)
        object.__setattr__(self, "quantity", quantity)
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "display_arguments", normalized)

    @property
    def display_argument(self) -> Any | None:
        if self.display_arguments is not None and len(self.display_arguments) == 1:
            return self.display_arguments[0]
        return None


@dataclass(frozen=True, init=False)
class PartialNumericEvaluationResult:
    statement: ParsedStatement
    symbolic_expression: Any
    substitutions: dict[str, Any]
    unresolved_symbols: tuple[str, ...]
    evaluated_terms: tuple[tuple[int, Any], ...] | None = None
    display_name: str | None = None
    display_arguments: tuple[Any, ...] | None = None

    def __init__(
        self,
        statement: ParsedStatement,
        symbolic_expression: Any,
        substitutions: dict[str, Any],
        unresolved_symbols: tuple[str, ...],
        evaluated_terms: tuple[tuple[int, Any], ...] | None = None,
        display_name: str | None = None,
        display_arguments: tuple[Any, ...] | None = None,
        *,
        display_argument: Any | None = None,
    ) -> None:
        if display_arguments is not None and display_argument is not None:
            raise TypeError("provide either display_arguments or display_argument, not both")
        normalized = (
            (display_argument,)
            if display_argument is not None
            else tuple(display_arguments) if display_arguments is not None else None
        )
        object.__setattr__(self, "statement", statement)
        object.__setattr__(self, "symbolic_expression", symbolic_expression)
        object.__setattr__(self, "substitutions", substitutions)
        object.__setattr__(self, "unresolved_symbols", tuple(unresolved_symbols))
        object.__setattr__(self, "evaluated_terms", evaluated_terms)
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "display_arguments", normalized)

    @property
    def display_argument(self) -> Any | None:
        if self.display_arguments is not None and len(self.display_arguments) == 1:
            return self.display_arguments[0]
        return None
''',
    "numeric result display metadata",
)
models_path.write_text(models, encoding="utf-8")

engine_path = Path("src/engcalc_colab/engine.py")
engine = engine_path.read_text(encoding="utf-8")

engine = replace_once(
    engine,
'''                    display_name,
                    display_argument,
                ) = evaluator.partial_numeric_evaluation
                return PartialNumericEvaluationResult(
                    statement=statement,
                    symbolic_expression=symbolic_expression,
                    substitutions=substitutions,
                    unresolved_symbols=unresolved_symbols,
                    evaluated_terms=evaluated_terms,
                    display_name=display_name,
                    display_argument=display_argument,
                )
''',
'''                    display_name,
                    display_arguments,
                ) = evaluator.partial_numeric_evaluation
                return PartialNumericEvaluationResult(
                    statement=statement,
                    symbolic_expression=symbolic_expression,
                    substitutions=substitutions,
                    unresolved_symbols=unresolved_symbols,
                    evaluated_terms=evaluated_terms,
                    display_name=display_name,
                    display_arguments=display_arguments,
                )
''',
    "partial result construction",
)

engine = replace_once(
    engine,
'''                    quantity,
                    display_name,
                    display_argument,
                ) = evaluator.numeric_evaluation
                return NumericEvaluationResult(
                    statement=statement,
                    symbolic_expression=symbolic_expression,
                    substitutions=substitutions,
                    quantity=quantity,
                    display_name=display_name,
                    display_argument=display_argument,
                )
''',
'''                    quantity,
                    display_name,
                    display_arguments,
                ) = evaluator.numeric_evaluation
                return NumericEvaluationResult(
                    statement=statement,
                    symbolic_expression=symbolic_expression,
                    substitutions=substitutions,
                    quantity=quantity,
                    display_name=display_name,
                    display_arguments=display_arguments,
                )
''',
    "numeric result construction",
)

engine = replace_once(
    engine,
'''    def _resolve_numeric_function_argument(self, node: ast.AST):
        if isinstance(node, ast.Name):
            symbolic = self.visit(node)
            if (
                isinstance(symbolic, sp.Symbol)
                and self.engine.numeric_context.get(node.id) is None
            ):
                return symbolic
        return self.engine.numeric_context.evaluate_expression(
            ast.Expression(body=node)
        )
''',
'''    def _resolve_numeric_function_argument(self, node: ast.AST):
        if isinstance(node, ast.Name):
            symbolic = self.visit(node)
            if (
                isinstance(symbolic, sp.Symbol)
                and self.engine.numeric_context.get(node.id) is None
            ):
                return symbolic
        return self.engine.numeric_context.evaluate_expression(
            ast.Expression(body=node)
        )

    def _resolve_numeric_user_function_argument(self, node: ast.AST):
        try:
            return self._resolve_numeric_function_argument(node)
        except EngEvaluationError as exc:
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in self.engine.functions
                and "unsupported numeric function" in str(exc)
            ):
                raise
            symbolic = self.visit(node)
            _, quantity = self.engine.numeric_context.evaluate_symbolic(symbolic)
            return quantity
''',
    "numeric nested user function resolver",
)

old_numeric = '''            display_name = argument.id if isinstance(argument, ast.Name) else None
            display_argument = None

            if (
                isinstance(argument, ast.Call)
                and isinstance(argument.func, ast.Name)
                and argument.func.id in self.engine.functions
            ):
                function_name = argument.func.id
                if len(argument.args) != 1:
                    raise EngEvaluationError(
                        f"function '{function_name}' expects 1 argument"
                    )
                function = self.engine.functions[function_name]
                argument_node = argument.args[0]
                argument_expression = self.visit(argument_node)
                argument_value = self._resolve_numeric_function_argument(argument_node)
                symbolic_expression = sp.sympify(function.expression)
                display_name = function_name
                display_argument = argument_expression

                if (
                    isinstance(argument_node, ast.Name)
                    and isinstance(argument_value, sp.Symbol)
                    and self.engine.numeric_context.get(argument_node.id) is None
                ):
                    if target_unit is not None:
                        raise EngEvaluationError(
                            "target-unit conversion requires a fully numeric result"
                        )
                    parameter = self.engine.resolve_symbol(function.parameter)
                    symbolic_expression = symbolic_expression.subs(
                        parameter,
                        argument_value,
                    )
                    substitutions, unresolved_symbols = (
                        self.engine.numeric_context.partial_substitutions(
                            symbolic_expression,
                            allowed_unresolved={argument_node.id},
                        )
                    )
                    evaluated_terms = self.engine.numeric_context.evaluate_partial_polynomial(
                        symbolic_expression,
                        argument_node.id,
                    )
                    self.partial_numeric_evaluation = (
                        symbolic_expression,
                        substitutions,
                        unresolved_symbols,
                        evaluated_terms,
                        display_name,
                        display_argument,
                    )
                    return symbolic_expression

                try:
                    substitutions, quantity = self.engine.numeric_context.evaluate_symbolic(
                        symbolic_expression,
                        overrides={function.parameter: argument_value},
                    )
                except EngEvaluationError as exc:
                    if "incompatible units" not in str(exc):
                        raise
                    hint = diagnostic_hint(
                        "incompatible_function_units",
                        function=function_name,
                    )
                    raise EngEvaluationError(
                        f"incompatible units while evaluating numeric function '{function_name}'. {hint}"
                    ) from exc
            else:
                symbolic_expression = self.visit(argument)
                substitutions, quantity = self.engine.numeric_context.evaluate_symbolic(
                    symbolic_expression
                )
'''

new_numeric = '''            display_name = argument.id if isinstance(argument, ast.Name) else None
            display_arguments = None

            if (
                isinstance(argument, ast.Call)
                and isinstance(argument.func, ast.Name)
                and argument.func.id in self.engine.functions
            ):
                function_name = argument.func.id
                function = self.engine.functions[function_name]
                self._require_user_function_arity(
                    function_name,
                    function,
                    argument.args,
                )
                argument_expressions = tuple(
                    self.visit(argument_node)
                    for argument_node in argument.args
                )
                argument_values = tuple(
                    self._resolve_numeric_user_function_argument(argument_node)
                    for argument_node in argument.args
                )
                symbolic_expression = sp.sympify(function.expression)
                display_name = function_name
                display_arguments = argument_expressions

                unresolved = [
                    (index, argument_node, argument_value)
                    for index, (argument_node, argument_value) in enumerate(
                        zip(argument.args, argument_values)
                    )
                    if isinstance(argument_value, sp.Symbol)
                ]
                if unresolved:
                    if len(argument.args) == 1:
                        _, argument_node, argument_value = unresolved[0]
                        if isinstance(argument_node, ast.Name):
                            if target_unit is not None:
                                raise EngEvaluationError(
                                    "target-unit conversion requires a fully numeric result"
                                )
                            parameter = self.engine.resolve_symbol(function.parameters[0])
                            bindings = {parameter: argument_value}
                            if any(
                                item.func in _INVERSE_TRIG_SYMBOLIC_FUNCTIONS
                                for item in sp.preorder_traversal(symbolic_expression)
                            ):
                                symbolic_expression = _substitute_preserving_inverse_trig(
                                    symbolic_expression,
                                    bindings,
                                )
                            else:
                                symbolic_expression = symbolic_expression.xreplace(bindings)
                            substitutions, unresolved_symbols = (
                                self.engine.numeric_context.partial_substitutions(
                                    symbolic_expression,
                                    allowed_unresolved={argument_node.id},
                                )
                            )
                            evaluated_terms = (
                                self.engine.numeric_context.evaluate_partial_polynomial(
                                    symbolic_expression,
                                    argument_node.id,
                                )
                            )
                            self.partial_numeric_evaluation = (
                                symbolic_expression,
                                substitutions,
                                unresolved_symbols,
                                evaluated_terms,
                                display_name,
                                display_arguments,
                            )
                            return symbolic_expression

                    unresolved_names = tuple(
                        sorted({value.name for _, _, value in unresolved})
                    )
                    hint = diagnostic_hint(
                        "unresolved_numeric_symbols",
                        names=unresolved_names,
                    )
                    raise EngEvaluationError(
                        "numeric evaluation requires values for: "
                        + ", ".join(unresolved_names)
                        + f". {hint}"
                    )

                overrides = dict(zip(function.parameters, argument_values))
                try:
                    substitutions, quantity = self.engine.numeric_context.evaluate_symbolic(
                        symbolic_expression,
                        overrides=overrides,
                    )
                except EngEvaluationError as exc:
                    if "incompatible units" not in str(exc):
                        raise
                    hint = diagnostic_hint(
                        "incompatible_function_units",
                        function=function_name,
                    )
                    raise EngEvaluationError(
                        f"incompatible units while evaluating numeric function '{function_name}'. {hint}"
                    ) from exc
            else:
                symbolic_expression = self.visit(argument)
                substitutions, quantity = self.engine.numeric_context.evaluate_symbolic(
                    symbolic_expression
                )
'''
engine = replace_once(engine, old_numeric, new_numeric, "numeric user function call")

engine = replace_once(
    engine,
'''                display_name,
                display_argument,
            )
''',
'''                display_name,
                display_arguments,
            )
''',
    "numeric evaluator payload",
)

engine_path.write_text(engine, encoding="utf-8")
print("Task 3 numeric multi-argument patch applied")
