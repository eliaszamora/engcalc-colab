from __future__ import annotations

import ast

import sympy as sp

from .errors import AmbiguousSolveError, EngCalcError, EngEvaluationError, EngSyntaxError
from .models import (
    EvaluationResult,
    NumericAssignmentResult,
    NumericEvaluationResult,
    ParsedNumericAssignment,
    ParsedStatement,
    UserFunction,
)
from .numeric import NumericContext


class EngineeringEngine:
    def __init__(self) -> None:
        self.namespace: dict[str, sp.Expr] = {}
        self.functions: dict[str, UserFunction] = {}
        self.symbols: dict[str, sp.Symbol] = {}
        self.numeric_context = NumericContext()

    def reset(self) -> None:
        self.namespace.clear()
        self.functions.clear()
        self.symbols.clear()
        self.numeric_context.reset()

    def resolve_symbol(self, name: str) -> sp.Symbol:
        if name not in self.symbols:
            self.symbols[name] = sp.Symbol(name)
        return self.symbols[name]

    def resolve_name(self, name: str):
        if name in self.namespace:
            return self.namespace[name]
        return self.resolve_symbol(name)

    def evaluate(
        self,
        statement: ParsedStatement | ParsedNumericAssignment,
    ) -> EvaluationResult | NumericAssignmentResult | NumericEvaluationResult:
        evaluator = _Evaluator(self)
        try:
            if isinstance(statement, ParsedNumericAssignment):
                quantity = self.numeric_context.assign(
                    statement.target,
                    statement.expression,
                )
                return NumericAssignmentResult(
                    statement=statement,
                    quantity=quantity,
                )

            if statement.target is not None:
                if statement.parameter is None and statement.target in self.functions:
                    raise EngEvaluationError(
                        f"redefinition conflict: '{statement.target}' is already a function"
                    )
                if statement.parameter is not None and statement.target in self.namespace:
                    raise EngEvaluationError(
                        f"redefinition conflict: '{statement.target}' is already a scalar"
                    )

            value = evaluator.visit(statement.expression.body)
            if evaluator.numeric_evaluation is not None:
                (
                    symbolic_expression,
                    substitutions,
                    quantity,
                    display_name,
                ) = evaluator.numeric_evaluation
                return NumericEvaluationResult(
                    statement=statement,
                    symbolic_expression=symbolic_expression,
                    substitutions=substitutions,
                    quantity=quantity,
                    display_name=display_name,
                )

            if statement.target is not None:
                if statement.parameter is not None:
                    self.resolve_name(statement.parameter)
                    self.functions[statement.target] = UserFunction(
                        parameter=statement.parameter,
                        expression=value,
                    )
                else:
                    self.namespace[statement.target] = value
            return EvaluationResult(
                statement=statement,
                display_input=evaluator.display_input,
                value=value,
            )
        except EngCalcError as exc:
            message = str(exc)
            if message.startswith("line "):
                raise
            raise type(exc)(f"line {statement.line_no}: {message}") from None
        except Exception as exc:
            raise EngEvaluationError(
                f"line {statement.line_no}: symbolic evaluation failed: {exc}"
            ) from None


class _Evaluator(ast.NodeVisitor):
    def __init__(self, engine: EngineeringEngine) -> None:
        self.engine = engine
        self.display_input = None
        self.numeric_evaluation = None
        self.symbol_overrides: dict[str, sp.Symbol] = {}

    def generic_visit(self, node):
        raise EngEvaluationError(f"unsupported syntax '{type(node).__name__}'")

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, bool) or node.value is None:
            raise EngEvaluationError("only numeric constants are supported")
        if isinstance(node.value, int):
            return sp.Integer(node.value)
        if isinstance(node.value, float):
            return sp.Float(str(node.value))
        raise EngEvaluationError("only numeric constants are supported")

    def visit_Name(self, node: ast.Name):
        if node.id in self.symbol_overrides:
            return self.symbol_overrides[node.id]
        return self.engine.resolve_name(node.id)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        value = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
        raise EngEvaluationError("unsupported unary operator")

    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add): return left + right
        if isinstance(node.op, ast.Sub): return left - right
        if isinstance(node.op, ast.Mult): return left * right
        if isinstance(node.op, ast.Div): return left / right
        if isinstance(node.op, ast.Pow): return left ** right
        raise EngEvaluationError("unsupported operator")

    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name):
            raise EngSyntaxError(f"unsupported syntax '{type(node.func).__name__}'")
        name = node.func.id

        if name == "sum":
            self._require_arity(name, node.args, 4, "expression, index, lower, upper")
            index_node = node.args[1]
            if not isinstance(index_node, ast.Name):
                raise EngEvaluationError("sum index must be a symbolic identifier")
            index_name = index_node.id
            index = self.engine.resolve_symbol(index_name)
            previous = self.symbol_overrides.get(index_name)
            self.symbol_overrides[index_name] = index
            try:
                expr = self.visit(node.args[0])
            finally:
                if previous is None:
                    self.symbol_overrides.pop(index_name, None)
                else:
                    self.symbol_overrides[index_name] = previous
            lower = self.visit(node.args[2])
            upper = self.visit(node.args[3])
            symbolic_sum = sp.Sum(expr, (index, lower, upper))
            self.display_input = symbolic_sum
            return symbolic_sum

        if name == "numeric":
            self._require_arity(name, node.args, 1, "expression")
            argument = node.args[0]
            display_name = argument.id if isinstance(argument, ast.Name) else None
            symbolic_expression = self.visit(argument)
            substitutions, quantity = self.engine.numeric_context.evaluate_symbolic(
                symbolic_expression
            )
            self.numeric_evaluation = (
                symbolic_expression,
                substitutions,
                quantity,
                display_name,
            )
            return symbolic_expression

        if name == "solve":
            self._require_arity(name, node.args, 2, "equation, unknown")
            unknown_node = node.args[1]
            if not isinstance(unknown_node, ast.Name):
                raise EngEvaluationError("solve unknown must be a symbolic identifier")
            unknown_name = unknown_node.id
            unknown = self.engine.resolve_symbol(unknown_name)
            previous = self.symbol_overrides.get(unknown_name)
            self.symbol_overrides[unknown_name] = unknown
            try:
                equation = self.visit(node.args[0])
            finally:
                if previous is None:
                    self.symbol_overrides.pop(unknown_name, None)
                else:
                    self.symbol_overrides[unknown_name] = previous
            if not isinstance(equation, sp.Equality):
                equation = sp.Eq(equation, 0, evaluate=False)
            self.display_input = equation
            solutions = sp.solve(equation, unknown)
            if len(solutions) == 0:
                raise EngEvaluationError(f"solve found no solution for {unknown}")
            if len(solutions) > 1:
                raise AmbiguousSolveError(
                    f"solve returned {len(solutions)} solutions for {unknown}; v0.1 requires one"
                )
            return solutions[0]

        args = [self.visit(arg) for arg in node.args]

        if name in self.engine.functions:
            if len(args) != 1:
                raise EngEvaluationError(f"function '{name}' expects 1 argument")
            function = self.engine.functions[name]
            parameter = self.engine.resolve_name(function.parameter)
            return sp.sympify(function.expression).subs(parameter, args[0])

        if name == "integral":
            self._require_arity(name, args, 4, "expression, variable, lower, upper")
            expr, var, lower, upper = args
            self.display_input = sp.Integral(expr, (var, lower, upper))
            return sp.integrate(expr, (var, lower, upper))

        if name == "diff":
            if len(args) not in (2, 3):
                raise EngEvaluationError(
                    "diff expects 2 or 3 arguments: expression, variable[, order]"
                )
            expr, var = args[:2]
            order = int(args[2]) if len(args) == 3 else 1
            self.display_input = sp.Derivative(expr, (var, order))
            return sp.diff(expr, var, order)

        if name == "eq":
            self._require_arity(name, args, 2, "left, right")
            return sp.Eq(args[0], args[1], evaluate=False)

        if name in {"simplify", "expand", "factor"}:
            self._require_arity(name, args, 1, "expression")
            operation = {
                "simplify": sp.simplify,
                "expand": sp.expand,
                "factor": sp.factor,
            }[name]
            return operation(args[0])

        if name == "subs":
            self._require_arity(name, args, 3, "expression, variable, value")
            return sp.sympify(args[0]).subs(args[1], args[2])

        raise EngSyntaxError(f"unsupported function '{name}'")

    @staticmethod
    def _require_arity(name: str, args: list, count: int, signature: str) -> None:
        if len(args) != count:
            raise EngEvaluationError(f"{name} expects {count} arguments: {signature}")
