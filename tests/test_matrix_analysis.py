import sympy as sp
import pytest

from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.errors import EngEvaluationError
from engcalc_colab.models import EvaluationResult
from engcalc_colab.parser import parse_cell


def run(engine: EngineeringEngine, source: str):
    return engine.evaluate(parse_cell(source)[0])


def test_rank_returns_exact_integer():
    engine = EngineeringEngine()
    run(engine, "A = [1, 2; 2, 4]")

    result = run(engine, "rank(A)")

    assert result.value == 1
    assert isinstance(result.value, (int, sp.Integer))


def test_rref_returns_exact_immutable_matrix():
    engine = EngineeringEngine()
    run(engine, "A = [1, 2; 3, 4]")

    result = run(engine, "rref(A)")

    assert isinstance(result.value, sp.ImmutableMatrix)
    assert result.value == sp.ImmutableMatrix([[1, 0], [0, 1]])


def test_norm_is_exact_frobenius_norm():
    engine = EngineeringEngine()
    run(engine, "v = [3, 4]")

    result = run(engine, "norm(v)")

    assert sp.simplify(result.value - 5) == 0


def test_eigenvals_return_deterministic_entries_with_multiplicity():
    engine = EngineeringEngine()
    run(engine, "A = diag(2, 1, 2)")

    result = run(engine, "eigenvals(A)")

    eigenvalues = result.value
    assert type(eigenvalues).__name__ == "EigenvalueSet"
    assert eigenvalues.source_matrix == engine.namespace["A"]
    assert tuple((entry.value, entry.multiplicity) for entry in eigenvalues.entries) == (
        (sp.Integer(1), 1),
        (sp.Integer(2), 2),
    )


def test_eigenvects_preserve_multiplicity_and_exact_eigen_relation():
    engine = EngineeringEngine()
    run(engine, "A = diag(2, 1, 2)")

    result = run(engine, "eigenvects(A)")

    eigenvectors = result.value
    assert type(eigenvectors).__name__ == "EigenvectorSet"
    assert tuple((entry.value, entry.multiplicity) for entry in eigenvectors.entries) == (
        (sp.Integer(1), 1),
        (sp.Integer(2), 2),
    )
    assert tuple(len(entry.vectors) for entry in eigenvectors.entries) == (1, 2)
    A = engine.namespace["A"]
    for entry in eigenvectors.entries:
        for vector in entry.vectors:
            assert isinstance(vector, sp.ImmutableMatrix)
            assert vector.shape == (3, 1)
            assert (A * vector - entry.value * vector).applyfunc(sp.simplify) == sp.zeros(3, 1)


def test_analysis_functions_require_matrix_arguments():
    engine = EngineeringEngine()

    for expression in ("rank(x)", "rref(x)", "norm(x)", "eigenvals(x)", "eigenvects(x)"):
        with pytest.raises(EngEvaluationError, match=r"requires a matrix"):
            run(engine, expression)


def test_analysis_function_names_are_reserved():
    for name in ("rank", "rref", "norm", "eigenvals", "eigenvects"):
        with pytest.raises(Exception, match=r"reserved identifier"):
            parse_cell(f"{name} = 3")
