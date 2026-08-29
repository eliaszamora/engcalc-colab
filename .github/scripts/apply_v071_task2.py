from pathlib import Path

path = Path("src/engcalc_colab/engine.py")
text = path.read_text(encoding="utf-8")

replacements = [
    (
'''def _substitute_preserving_inverse_trig(expr, symbol, replacement):
    expr = sp.sympify(expr)
    if expr == symbol:
        return replacement
    if symbol not in expr.free_symbols:
        return expr

    rebuilt_args = tuple(
        _substitute_preserving_inverse_trig(arg, symbol, replacement)
        for arg in expr.args
    )
    if expr.func in _INVERSE_TRIG_SYMBOLIC_FUNCTIONS:
        return expr.func(*rebuilt_args, evaluate=False)
    return expr.func(*rebuilt_args)
''',
'''def _substitute_preserving_inverse_trig(expr, bindings):
    expr = sp.sympify(expr)
    if isinstance(expr, sp.Symbol) and expr in bindings:
        return bindings[expr]
    if not expr.free_symbols.intersection(bindings):
        return expr

    rebuilt_args = tuple(
        _substitute_preserving_inverse_trig(arg, bindings)
        for arg in expr.args
    )
    if expr.func in _INVERSE_TRIG_SYMBOLIC_FUNCTIONS:
        return expr.func(*rebuilt_args, evaluate=False)
    return expr.func(*rebuilt_args)
'''
    ),
    (
'''            if statement.target is not None:
                if statement.parameter is None and statement.target in self.functions:
                    raise EngEvaluationError(
                        f"redefinition conflict: '{statement.target}' is already a function"
                    )
                if statement.parameter is not None and statement.target in self.namespace:
                    raise EngEvaluationError(
                        f"redefinition conflict: '{statement.target}' is already a scalar"
                    )

            value = evaluator.visit(statement.expression.body)
''',
'''            if statement.target is not None:
                if statement.parameters is None and statement.target in self.functions:
                    raise EngEvaluationError(
                        f"redefinition conflict: '{statement.target}' is already a function"
                    )
                if statement.parameters is not None and statement.target in self.namespace:
                    raise EngEvaluationError(
                        f"redefinition conflict: '{statement.target}' is already a scalar"
                    )

            if statement.parameters is not None:
                value = evaluator.visit_function_body(
                    statement.expression.body,
                    statement.parameters,
                )
            else:
                value = evaluator.visit(statement.expression.body)
'''
    ),
    (
'''            if statement.target is not None:
                if statement.parameter is not None:
                    self.resolve_name(statement.parameter)
                    self.functions[statement.target] = UserFunction(
                        parameter=statement.parameter,
                        expression=value,
                    )
                else:
                    self.namespace[statement.target] = value
''',
'''            if statement.target is not None:
                if statement.parameters is not None:
                    for parameter in statement.parameters:
                        self.resolve_symbol(parameter)
                    self.functions[statement.target] = UserFunction(
                        parameters=statement.parameters,
                        expression=value,
                    )
                else:
                    self.namespace[statement.target] = value
'''
    ),
    (
'''    def generic_visit(self, node):
        raise EngEvaluationError(f"unsupported syntax '{type(node).__name__}'")
''',
'''    def visit_function_body(self, node: ast.AST, parameters: tuple[str, ...]):
        previous = dict(self.symbol_overrides)
        try:
            for name in parameters:
                self.symbol_overrides[name] = self.engine.resolve_symbol(name)
            return self.visit(node)
        finally:
            self.symbol_overrides.clear()
            self.symbol_overrides.update(previous)

    def generic_visit(self, node):
        raise EngEvaluationError(f"unsupported syntax '{type(node).__name__}'")
'''
    ),
    (
'''        if name in self.engine.functions:
            if len(args) != 1:
                raise EngEvaluationError(f"function '{name}' expects 1 argument")
            function = self.engine.functions[name]
            parameter = self.engine.resolve_name(function.parameter)
            expression = sp.sympify(function.expression)
            if any(
                item.func in _INVERSE_TRIG_SYMBOLIC_FUNCTIONS
                for item in sp.preorder_traversal(expression)
            ):
                return _substitute_preserving_inverse_trig(
                    expression, parameter, args[0]
                )
            return expression.subs(parameter, args[0])
''',
'''        if name in self.engine.functions:
            function = self.engine.functions[name]
            self._require_user_function_arity(name, function, args)
            parameters = tuple(
                self.engine.resolve_symbol(parameter)
                for parameter in function.parameters
            )
            bindings = dict(zip(parameters, args))
            expression = sp.sympify(function.expression)
            if any(
                item.func in _INVERSE_TRIG_SYMBOLIC_FUNCTIONS
                for item in sp.preorder_traversal(expression)
            ):
                return _substitute_preserving_inverse_trig(
                    expression,
                    bindings,
                )
            return expression.xreplace(bindings)
'''
    ),
    (
'''    @staticmethod
    def _require_arity(name: str, args: list, count: int, signature: str) -> None:
''',
'''    @staticmethod
    def _require_user_function_arity(name: str, function: UserFunction, args: list) -> None:
        expected = len(function.parameters)
        received = len(args)
        if received == expected:
            return
        signature = ", ".join(function.parameters)
        raise EngEvaluationError(
            f"function '{name}' expects {expected} arguments ({signature}), "
            f"received {received}"
        )

    @staticmethod
    def _require_arity(name: str, args: list, count: int, signature: str) -> None:
'''
    ),
]

changed = False
for old, new in replacements:
    if old in text:
        text = text.replace(old, new, 1)
        changed = True
    elif new not in text:
        raise SystemExit("expected Task 2 engine block was not found")

if changed:
    path.write_text(text, encoding="utf-8")
    print("Task 2 engine patch applied")
else:
    print("Task 2 engine patch already applied")
