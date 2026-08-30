from pathlib import Path


matrix_core = Path("src/engcalc_colab/matrix_core.py")
text = matrix_core.read_text(encoding="utf-8")
append = '''


def map_matrix_entries(matrix, operation) -> sp.ImmutableMatrix:
    """Apply one scalar operation entrywise and preserve immutable matrix truth."""
    if not is_matrix(matrix):
        raise EngEvaluationError("matrix entry mapping requires a matrix")
    return sp.ImmutableMatrix(
        matrix.rows,
        matrix.cols,
        lambda row, col: sp.sympify(operation(matrix[row, col])),
    )
'''
assert "def map_matrix_entries(" not in text
matrix_core.write_text(text.rstrip() + append.rstrip() + "\n", encoding="utf-8")


engine = Path("src/engcalc_colab/engine.py")
text = engine.read_text(encoding="utf-8")

needle = '''from .matrix_core import (\n    build_matrix,\n    matrix_add,\n'''
replacement = '''from .matrix_core import (\n    build_matrix,\n    is_matrix,\n    map_matrix_entries,\n    matrix_add,\n'''
assert needle in text
text = text.replace(needle, replacement, 1)

needle = '''def _substitute_preserving_inverse_trig(expr, bindings):\n    expr = sp.sympify(expr)\n    if isinstance(expr, sp.Symbol) and expr in bindings:\n        return bindings[expr]\n    if not expr.free_symbols.intersection(bindings):\n        return expr\n\n    rebuilt_args = tuple(\n        _substitute_preserving_inverse_trig(arg, bindings)\n        for arg in expr.args\n    )\n    if expr.func in _INVERSE_TRIG_SYMBOLIC_FUNCTIONS:\n        return expr.func(*rebuilt_args, evaluate=False)\n    return expr.func(*rebuilt_args)\n\n'''
replacement = needle + '''\ndef substitute_symbolic_value(value, bindings):\n    """Substitute one scalar or immutable matrix while preserving scalar CAS semantics."""\n    if is_matrix(value):\n        return map_matrix_entries(\n            value,\n            lambda entry: substitute_symbolic_value(entry, bindings),\n        )\n\n    expression = sp.sympify(value)\n    if any(\n        item.func in _INVERSE_TRIG_SYMBOLIC_FUNCTIONS\n        for item in sp.preorder_traversal(expression)\n    ):\n        return _substitute_preserving_inverse_trig(expression, bindings)\n    return expression.xreplace(bindings)\n\n'''
assert needle in text
text = text.replace(needle, replacement, 1)

needle = '''        if name in self.engine.functions:\n            function = self.engine.functions[name]\n            self._require_user_function_arity(name, function, args)\n            parameters = tuple(\n                self.engine.resolve_symbol(parameter)\n                for parameter in function.parameters\n            )\n            bindings = dict(zip(parameters, args))\n            expression = sp.sympify(function.expression)\n            if any(\n                item.func in _INVERSE_TRIG_SYMBOLIC_FUNCTIONS\n                for item in sp.preorder_traversal(expression)\n            ):\n                return _substitute_preserving_inverse_trig(\n                    expression,\n                    bindings,\n                )\n            return expression.xreplace(bindings)\n\n'''
replacement = '''        if name in self.engine.functions:\n            function = self.engine.functions[name]\n            self._require_user_function_arity(name, function, args)\n            parameters = tuple(\n                self.engine.resolve_symbol(parameter)\n                for parameter in function.parameters\n            )\n            bindings = dict(zip(parameters, args))\n            return substitute_symbolic_value(function.expression, bindings)\n\n'''
assert needle in text
text = text.replace(needle, replacement, 1)

needle = '''        if name in _SCALAR_SYMBOLIC_FUNCTIONS:\n            self._require_arity(name, args, 1, "expression")\n            if name in {"asin", "acos", "atan"}:\n                return _SCALAR_SYMBOLIC_FUNCTIONS[name](args[0], evaluate=False)\n            return _SCALAR_SYMBOLIC_FUNCTIONS[name](args[0])\n\n'''
replacement = '''        if name in _SCALAR_SYMBOLIC_FUNCTIONS:\n            self._require_arity(name, args, 1, "expression")\n            if is_matrix(args[0]):\n                raise EngEvaluationError(\n                    f"{name} requires a scalar expression, not a matrix"\n                )\n            if name in {"asin", "acos", "atan"}:\n                return _SCALAR_SYMBOLIC_FUNCTIONS[name](args[0], evaluate=False)\n            return _SCALAR_SYMBOLIC_FUNCTIONS[name](args[0])\n\n'''
assert needle in text
text = text.replace(needle, replacement, 1)

needle = '''        if name == "integral":\n            self._require_arity(name, args, 4, "expression, variable, lower, upper")\n            expr, var, lower, upper = args\n            self.display_input = sp.Integral(expr, (var, lower, upper))\n            return sp.integrate(expr, (var, lower, upper))\n\n        if name == "diff":\n            if len(args) not in (2, 3):\n                raise EngEvaluationError(\n                    "diff expects 2 or 3 arguments: expression, variable[, order]"\n                )\n            expr, var = args[:2]\n            order = int(args[2]) if len(args) == 3 else 1\n            self.display_input = sp.Derivative(expr, (var, order))\n            if isinstance(var, sp.Symbol):\n                breakpoints = extract_symbolic_breakpoints(expr, var.name)\n                if breakpoints:\n                    self.derivative_variable = var.name\n                    self.derivative_breakpoints = breakpoints\n            return sp.diff(expr, var, order)\n\n'''
replacement = '''        if name == "integral":\n            self._require_arity(name, args, 4, "expression, variable, lower, upper")\n            expr, var, lower, upper = args\n            if is_matrix(expr):\n                self.display_input = map_matrix_entries(\n                    expr,\n                    lambda entry: sp.Integral(entry, (var, lower, upper)),\n                )\n                return map_matrix_entries(\n                    expr,\n                    lambda entry: sp.integrate(entry, (var, lower, upper)),\n                )\n            self.display_input = sp.Integral(expr, (var, lower, upper))\n            return sp.integrate(expr, (var, lower, upper))\n\n        if name == "diff":\n            if len(args) not in (2, 3):\n                raise EngEvaluationError(\n                    "diff expects 2 or 3 arguments: expression, variable[, order]"\n                )\n            expr, var = args[:2]\n            order = int(args[2]) if len(args) == 3 else 1\n            if is_matrix(expr):\n                self.display_input = map_matrix_entries(\n                    expr,\n                    lambda entry: sp.Derivative(entry, (var, order)),\n                )\n                if isinstance(var, sp.Symbol):\n                    breakpoints = []\n                    for entry in expr:\n                        for breakpoint in extract_symbolic_breakpoints(entry, var.name):\n                            if breakpoint not in breakpoints:\n                                breakpoints.append(breakpoint)\n                    if breakpoints:\n                        self.derivative_variable = var.name\n                        self.derivative_breakpoints = tuple(breakpoints)\n                return map_matrix_entries(\n                    expr,\n                    lambda entry: sp.diff(entry, var, order),\n                )\n\n            self.display_input = sp.Derivative(expr, (var, order))\n            if isinstance(var, sp.Symbol):\n                breakpoints = extract_symbolic_breakpoints(expr, var.name)\n                if breakpoints:\n                    self.derivative_variable = var.name\n                    self.derivative_breakpoints = breakpoints\n            return sp.diff(expr, var, order)\n\n'''
assert needle in text
text = text.replace(needle, replacement, 1)

needle = '''        if name in {"simplify", "expand", "factor"}:\n            self._require_arity(name, args, 1, "expression")\n            operation = {\n                "simplify": sp.simplify,\n                "expand": sp.expand,\n                "factor": sp.factor,\n            }[name]\n            return operation(args[0])\n\n        if name == "subs":\n            self._require_arity(name, args, 3, "expression, variable, value")\n            return sp.sympify(args[0]).subs(args[1], args[2])\n\n'''
replacement = '''        if name in {"simplify", "expand", "factor"}:\n            self._require_arity(name, args, 1, "expression")\n            operation = {\n                "simplify": sp.simplify,\n                "expand": sp.expand,\n                "factor": sp.factor,\n            }[name]\n            if is_matrix(args[0]):\n                return map_matrix_entries(args[0], operation)\n            return operation(args[0])\n\n        if name == "subs":\n            self._require_arity(name, args, 3, "expression, variable, value")\n            if is_matrix(args[0]):\n                return map_matrix_entries(\n                    args[0],\n                    lambda entry: sp.sympify(entry).subs(args[1], args[2]),\n                )\n            return sp.sympify(args[0]).subs(args[1], args[2])\n\n'''
assert needle in text
text = text.replace(needle, replacement, 1)

engine.write_text(text, encoding="utf-8")
