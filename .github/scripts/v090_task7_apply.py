from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    assert text.count(old) == 1, (path, old[:80], text.count(old))
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


# ---------------------------------------------------------------------------
# models.py: explicit analysis/guard transport models + UserFunction provenance
# ---------------------------------------------------------------------------
models_path = "src/engcalc_colab/models.py"
replace_once(
    models_path,
    '''@dataclass(frozen=True)\nclass MatrixShape:\n    rows: int\n    cols: int\n\n\n@dataclass(frozen=True)\nclass ParsedStatement:''',
    '''@dataclass(frozen=True)\nclass MatrixShape:\n    rows: int\n    cols: int\n\n\n@dataclass(frozen=True)\nclass MatrixNumericGuard:\n    operation: str\n    source_matrix: Any\n\n\n@dataclass(frozen=True)\nclass EigenvalueEntry:\n    value: Any\n    multiplicity: int\n\n\n@dataclass(frozen=True)\nclass EigenvalueSet:\n    entries: tuple[EigenvalueEntry, ...]\n    source_matrix: Any\n\n\n@dataclass(frozen=True)\nclass EigenvectorEntry:\n    value: Any\n    multiplicity: int\n    vectors: tuple[Any, ...]\n\n\n@dataclass(frozen=True)\nclass EigenvectorSet:\n    entries: tuple[EigenvectorEntry, ...]\n    source_matrix: Any\n\n\n@dataclass(frozen=True)\nclass ParsedStatement:''',
)
replace_once(
    models_path,
    '''    derivative_variable: str | None = None\n    derivative_breakpoints: tuple[Any, ...] = ()\n\n    def __init__(\n        self,\n        parameters: tuple[str, ...] | str | None = None,\n        expression: Any = None,\n        derivative_variable: str | None = None,\n        derivative_breakpoints: tuple[Any, ...] = (),\n        *,\n        parameter: str | None = None,\n    ) -> None:''',
    '''    derivative_variable: str | None = None\n    derivative_breakpoints: tuple[Any, ...] = ()\n    numeric_guards: tuple[MatrixNumericGuard, ...] = ()\n\n    def __init__(\n        self,\n        parameters: tuple[str, ...] | str | None = None,\n        expression: Any = None,\n        derivative_variable: str | None = None,\n        derivative_breakpoints: tuple[Any, ...] = (),\n        numeric_guards: tuple[MatrixNumericGuard, ...] = (),\n        *,\n        parameter: str | None = None,\n    ) -> None:''',
)
replace_once(
    models_path,
    '''        object.__setattr__(self, "derivative_variable", derivative_variable)\n        object.__setattr__(self, "derivative_breakpoints", tuple(derivative_breakpoints))\n''',
    '''        object.__setattr__(self, "derivative_variable", derivative_variable)\n        object.__setattr__(self, "derivative_breakpoints", tuple(derivative_breakpoints))\n        object.__setattr__(self, "numeric_guards", tuple(numeric_guards))\n''',
)


# ---------------------------------------------------------------------------
# matrix_analysis.py: exact symbolic truth and deterministic eigen models
# ---------------------------------------------------------------------------
Path("src/engcalc_colab/matrix_analysis.py").write_text(
    '''from __future__ import annotations\n\nimport sympy as sp\n\nfrom .errors import EngEvaluationError\nfrom .models import (\n    EigenvalueEntry,\n    EigenvalueSet,\n    EigenvectorEntry,\n    EigenvectorSet,\n)\n\n\ndef _require_matrix(value, operation: str) -> sp.MatrixBase:\n    if not isinstance(value, sp.MatrixBase):\n        raise EngEvaluationError(f"{operation} requires a matrix")\n    return value\n\n\ndef _require_square(value, operation: str) -> sp.MatrixBase:\n    matrix = _require_matrix(value, operation)\n    if matrix.rows != matrix.cols:\n        raise EngEvaluationError(f"{operation} requires a square matrix")\n    return matrix\n\n\ndef matrix_rank(value):\n    return _require_matrix(value, "rank").rank()\n\n\ndef matrix_rref(value) -> sp.ImmutableMatrix:\n    reduced, _pivots = _require_matrix(value, "rref").rref()\n    return sp.ImmutableMatrix(reduced)\n\n\ndef matrix_norm(value):\n    matrix = _require_matrix(value, "norm")\n    terms = tuple(sp.Abs(entry) ** 2 for entry in matrix)\n    return sp.simplify(sp.sqrt(sp.Add(*terms)))\n\n\ndef matrix_eigenvals(value) -> EigenvalueSet:\n    matrix = sp.ImmutableMatrix(_require_square(value, "eigenvals"))\n    eigenvalues = matrix.eigenvals()\n    entries = tuple(\n        EigenvalueEntry(value=eigenvalue, multiplicity=int(multiplicity))\n        for eigenvalue, multiplicity in sorted(\n            eigenvalues.items(),\n            key=lambda item: sp.default_sort_key(item[0]),\n        )\n    )\n    return EigenvalueSet(entries=entries, source_matrix=matrix)\n\n\ndef matrix_eigenvects(value) -> EigenvectorSet:\n    matrix = sp.ImmutableMatrix(_require_square(value, "eigenvects"))\n    raw_entries = sorted(\n        matrix.eigenvects(),\n        key=lambda item: sp.default_sort_key(item[0]),\n    )\n    entries = tuple(\n        EigenvectorEntry(\n            value=eigenvalue,\n            multiplicity=int(multiplicity),\n            vectors=tuple(sp.ImmutableMatrix(vector) for vector in vectors),\n        )\n        for eigenvalue, multiplicity, vectors in raw_entries\n    )\n    return EigenvectorSet(entries=entries, source_matrix=matrix)\n''',
    encoding="utf-8",
)


# ---------------------------------------------------------------------------
# parser.py: expose and reserve the five approved analysis function names
# ---------------------------------------------------------------------------
parser_path = "src/engcalc_colab/parser.py"
replace_once(
    parser_path,
    '''    "piecewise", "identity", "zeros", "diag", "transpose", "det", "inv", "trace", "size",\n''',
    '''    "piecewise", "identity", "zeros", "diag", "transpose", "det", "inv", "trace", "size",\n    "rank", "rref", "norm", "eigenvals", "eigenvects",\n''',
)


# ---------------------------------------------------------------------------
# matrix_numeric.py: physical common-scale validation over QuantityMatrix truth
# ---------------------------------------------------------------------------
matrix_numeric_path = "src/engcalc_colab/matrix_numeric.py"
replace_once(
    matrix_numeric_path,
    '''from dataclasses import dataclass\nfrom typing import Any, Iterator\n\n\n@dataclass(frozen=True)\nclass QuantityMatrix:''',
    '''from dataclasses import dataclass\nfrom typing import Any, Iterator\n\nfrom pint.errors import DimensionalityError\n\nfrom .errors import EngEvaluationError\n\n\n@dataclass(frozen=True)\nclass QuantityMatrix:''',
)
with Path(matrix_numeric_path).open("a", encoding="utf-8") as stream:
    stream.write(
        '''\n\ndef ensure_common_scale(quantity_matrix: QuantityMatrix, operation: str):\n    """Return the common Pint unit, or None for dimensionless matrices.\n\n    Numerical zero is neutral. Nonzero physical entries must all be convertible\n    to one unit, and nonzero dimensionless entries may not mix with them.\n    """\n    common_unit = None\n    saw_dimensionless_nonzero = False\n\n    for quantity in quantity_matrix:\n        if float(quantity.magnitude) == 0.0:\n            continue\n        if quantity.dimensionless:\n            if common_unit is not None:\n                raise EngEvaluationError(\n                    f"matrix operation '{operation}' requires a dimensionless or common-scale matrix"\n                )\n            saw_dimensionless_nonzero = True\n            continue\n\n        if saw_dimensionless_nonzero:\n            raise EngEvaluationError(\n                f"matrix operation '{operation}' requires a dimensionless or common-scale matrix"\n            )\n        if common_unit is None:\n            common_unit = quantity.units\n            continue\n        try:\n            quantity.to(common_unit)\n        except DimensionalityError as exc:\n            raise EngEvaluationError(\n                f"matrix operation '{operation}' requires a dimensionless or common-scale matrix"\n            ) from exc\n\n    return common_unit\n'''
    )


# ---------------------------------------------------------------------------
# engine.py: analysis dispatch + deterministic guard provenance/numeric checking
# ---------------------------------------------------------------------------
engine_path = "src/engcalc_colab/engine.py"
replace_once(
    engine_path,
    '''from .models import (\n    EvaluationResult,\n''',
    '''from .models import (\n    EigenvalueEntry,\n    EigenvalueSet,\n    EigenvectorEntry,\n    EigenvectorSet,\n    EvaluationResult,\n    MatrixNumericGuard,\n''',
)
replace_once(
    engine_path,
    '''from .matrix_solve import solve_linear_system\nfrom .numeric import NumericContext\n''',
    '''from .matrix_analysis import (\n    matrix_eigenvals,\n    matrix_eigenvects,\n    matrix_norm,\n    matrix_rank,\n    matrix_rref,\n)\nfrom .matrix_numeric import ensure_common_scale\nfrom .matrix_solve import solve_linear_system\nfrom .numeric import NumericContext\n''',
)
replace_once(
    engine_path,
    '''        self.symbols: dict[str, sp.Symbol] = {}\n        self.numeric_context = NumericContext()\n\n    def reset(self) -> None:\n        self.namespace.clear()\n        self.functions.clear()\n        self.symbols.clear()\n        self.numeric_context.reset()\n''',
    '''        self.symbols: dict[str, sp.Symbol] = {}\n        self.numeric_guards: dict[str, tuple[MatrixNumericGuard, ...]] = {}\n        self.numeric_context = NumericContext()\n\n    def reset(self) -> None:\n        self.namespace.clear()\n        self.functions.clear()\n        self.symbols.clear()\n        self.numeric_guards.clear()\n        self.numeric_context.reset()\n''',
)
replace_once(
    engine_path,
    '''                        derivative_variable=evaluator.derivative_variable,\n                        derivative_breakpoints=evaluator.derivative_breakpoints,\n                    )\n                else:\n                    self.namespace[statement.target] = value\n''',
    '''                        derivative_variable=evaluator.derivative_variable,\n                        derivative_breakpoints=evaluator.derivative_breakpoints,\n                        numeric_guards=tuple(evaluator.numeric_guards),\n                    )\n                else:\n                    self.namespace[statement.target] = value\n                    if evaluator.numeric_guards:\n                        self.numeric_guards[statement.target] = tuple(evaluator.numeric_guards)\n                    else:\n                        self.numeric_guards.pop(statement.target, None)\n''',
)
replace_once(
    engine_path,
    '''        self.derivative_variable: str | None = None\n        self.derivative_breakpoints: tuple[object, ...] = ()\n\n    def visit_function_body(self, node: ast.AST, parameters: tuple[str, ...]):''',
    '''        self.derivative_variable: str | None = None\n        self.derivative_breakpoints: tuple[object, ...] = ()\n        self.numeric_guards: list[MatrixNumericGuard] = []\n\n    def _add_numeric_guard(self, guard: MatrixNumericGuard) -> None:\n        if not any(existing == guard for existing in self.numeric_guards):\n            self.numeric_guards.append(guard)\n\n    def _add_numeric_guards(self, guards) -> None:\n        for guard in guards:\n            self._add_numeric_guard(guard)\n\n    def _substitute_numeric_guard(self, guard: MatrixNumericGuard, bindings) -> MatrixNumericGuard:\n        source = substitute_symbolic_value(guard.source_matrix, bindings) if bindings else guard.source_matrix\n        return MatrixNumericGuard(\n            operation=guard.operation,\n            source_matrix=sp.ImmutableMatrix(source),\n        )\n\n    def _validate_numeric_guards(\n        self,\n        guards=None,\n        *,\n        overrides=None,\n        allowed_unresolved=None,\n    ):\n        validations = []\n        for guard in tuple(self.numeric_guards if guards is None else guards):\n            _substitutions, unresolved, quantity_matrix = self.engine.numeric_context.evaluate_matrix(\n                guard.source_matrix,\n                overrides=overrides,\n                allowed_unresolved=allowed_unresolved,\n            )\n            if unresolved:\n                continue\n            scale = ensure_common_scale(quantity_matrix, guard.operation)\n            validations.append((guard, scale))\n        return tuple(validations)\n\n    @staticmethod\n    def _guard_scale(validations, operation: str, source_matrix):\n        for guard, scale in reversed(validations):\n            if guard.operation == operation and guard.source_matrix == source_matrix:\n                return scale\n        return None\n\n    def _numeric_eigenvalue_set(self, value: EigenvalueSet, validations, target_unit=None):\n        scale = self._guard_scale(validations, "eigenvals", value.source_matrix)\n        entries = []\n        for entry in value.entries:\n            _substitutions, quantity = self.engine.numeric_context.evaluate_symbolic(entry.value)\n            if (\n                scale is not None\n                and quantity.dimensionless\n                and float(quantity.magnitude) == 0.0\n            ):\n                quantity = self.engine.numeric_context.ureg.Quantity(0, scale)\n            if target_unit is not None:\n                quantity = self.engine.numeric_context.convert_quantity(quantity, target_unit)\n            entries.append(EigenvalueEntry(value=quantity, multiplicity=entry.multiplicity))\n        return EigenvalueSet(entries=tuple(entries), source_matrix=value.source_matrix)\n\n    def _numeric_eigenvector_set(self, value: EigenvectorSet, validations, target_unit=None):\n        scale = self._guard_scale(validations, "eigenvects", value.source_matrix)\n        entries = []\n        for entry in value.entries:\n            _substitutions, quantity = self.engine.numeric_context.evaluate_symbolic(entry.value)\n            if (\n                scale is not None\n                and quantity.dimensionless\n                and float(quantity.magnitude) == 0.0\n            ):\n                quantity = self.engine.numeric_context.ureg.Quantity(0, scale)\n            if target_unit is not None:\n                quantity = self.engine.numeric_context.convert_quantity(quantity, target_unit)\n            numeric_vectors = []\n            for vector in entry.vectors:\n                _subs, unresolved, quantity_matrix = self.engine.numeric_context.evaluate_matrix(vector)\n                if unresolved:\n                    raise EngEvaluationError(\n                        "numeric eigenvectors require fully numeric vector entries"\n                    )\n                numeric_vectors.append(quantity_matrix)\n            entries.append(\n                EigenvectorEntry(\n                    value=quantity,\n                    multiplicity=entry.multiplicity,\n                    vectors=tuple(numeric_vectors),\n                )\n            )\n        return EigenvectorSet(entries=tuple(entries), source_matrix=value.source_matrix)\n\n    def visit_function_body(self, node: ast.AST, parameters: tuple[str, ...]):''',
)
replace_once(
    engine_path,
    '''        if node.id == "pi":\n            return sp.pi\n        return self.engine.resolve_name(node.id)\n''',
    '''        if node.id == "pi":\n            return sp.pi\n        if node.id in self.engine.namespace:\n            self._add_numeric_guards(self.engine.numeric_guards.get(node.id, ()))\n        return self.engine.resolve_name(node.id)\n''',
)
# Special numeric user-function path: inherit/substitute/validate function guards.
replace_once(
    engine_path,
    '''                if bindings:\n                    symbolic_expression = substitute_symbolic_value(\n                        symbolic_expression,\n                        bindings,\n                    )\n\n                if is_matrix(symbolic_expression):''',
    '''                if bindings:\n                    symbolic_expression = substitute_symbolic_value(\n                        symbolic_expression,\n                        bindings,\n                    )\n\n                effective_guards = tuple(\n                    self._substitute_numeric_guard(guard, bindings)\n                    for guard in function.numeric_guards\n                )\n                self._add_numeric_guards(effective_guards)\n                self._validate_numeric_guards(\n                    effective_guards,\n                    overrides=overrides,\n                    allowed_unresolved=allowed_unresolved,\n                )\n\n                if is_matrix(symbolic_expression):''',
)
# General numeric path: validate inherited/direct guards and handle eigen result models.
replace_once(
    engine_path,
    '''            else:\n                symbolic_expression = self.visit(argument)\n                if is_matrix(symbolic_expression):''',
    '''            else:\n                symbolic_expression = self.visit(argument)\n                guard_validations = self._validate_numeric_guards()\n                if isinstance(symbolic_expression, EigenvalueSet):\n                    return self._numeric_eigenvalue_set(\n                        symbolic_expression,\n                        guard_validations,\n                        target_unit=target_unit,\n                    )\n                if isinstance(symbolic_expression, EigenvectorSet):\n                    return self._numeric_eigenvector_set(\n                        symbolic_expression,\n                        guard_validations,\n                        target_unit=target_unit,\n                    )\n                if is_matrix(symbolic_expression):''',
)
# Analysis dispatch before user functions.
replace_once(
    engine_path,
    '''        if name == "size":\n            self._require_arity(name, args, 1, "matrix")\n            rows, cols = matrix_size(args[0])\n            return MatrixShape(rows=rows, cols=cols)\n\n        if name in self.engine.functions:''',
    '''        if name == "size":\n            self._require_arity(name, args, 1, "matrix")\n            rows, cols = matrix_size(args[0])\n            return MatrixShape(rows=rows, cols=cols)\n\n        if name in {"rank", "rref", "norm", "eigenvals", "eigenvects"}:\n            self._require_arity(name, args, 1, "matrix")\n            operations = {\n                "rank": matrix_rank,\n                "rref": matrix_rref,\n                "norm": matrix_norm,\n                "eigenvals": matrix_eigenvals,\n                "eigenvects": matrix_eigenvects,\n            }\n            result = operations[name](args[0])\n            source_matrix = sp.ImmutableMatrix(args[0])\n            self._add_numeric_guard(\n                MatrixNumericGuard(operation=name, source_matrix=source_matrix)\n            )\n            return result\n\n        if name in self.engine.functions:''',
)
# Generic symbolic user-function calls propagate substituted guard provenance.
replace_once(
    engine_path,
    '''            bindings = dict(zip(parameters, args))\n            return substitute_symbolic_value(function.expression, bindings)\n''',
    '''            bindings = dict(zip(parameters, args))\n            self._add_numeric_guards(\n                self._substitute_numeric_guard(guard, bindings)\n                for guard in function.numeric_guards\n            )\n            return substitute_symbolic_value(function.expression, bindings)\n''',
)
