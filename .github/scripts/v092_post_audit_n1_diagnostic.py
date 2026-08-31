from __future__ import annotations

from decimal import Decimal

import sympy as sp

import engcalc_colab.characteristics.candidates as candidates
import engcalc_colab.characteristics.fallback as fallback
import engcalc_colab.engine as engine_module
from engcalc_colab.engine import EngineeringEngine
from engcalc_colab.models import RootsResult
from engcalc_colab.parser import parse_cell


FAMILY = (
    ("1.25", "0.75", "4.25"),
    ("2.87", "0.602", "3.755"),
    ("0.83", "1.125", "7.375"),
    ("3.41", "2.250", "5.625"),
    ("1.07", "0.333", "8.444"),
    ("4.20", "3.125", "6.875"),
)


def evaluate_cell(engine: EngineeringEngine, source: str):
    result = None
    for statement in parse_cell(source):
        result = engine.evaluate(statement)
    return result


def expanded_source(a: str, r1: str, r2: str) -> str:
    a_value = Decimal(a)
    r1_value = Decimal(r1)
    r2_value = Decimal(r2)
    linear = -(a_value * (r1_value + r2_value))
    constant = a_value * r1_value * r2_value
    return f"f(x) = {a_value}*x^2 + ({linear})*x + ({constant})"


def classify_one(a: str, r1: str, r2: str) -> str:
    engine = EngineeringEngine()
    evaluate_cell(engine, expanded_source(a, r1, r2))
    expression = engine.functions["f"].expression
    x = engine.resolve_symbol("x")
    discovery = candidates._coerce_exact_discovery(
        candidates._exact_real_solution_set(expression, x)
    )

    result = evaluate_cell(engine, "roots(f(x), x, 0, 10)")
    assert isinstance(result, RootsResult)

    print(f"=== FAMILY a={a} r1={r1} r2={r2} ===")
    print("SYMPY_VERSION=", sp.__version__)
    print("EXPRESSION=", repr(expression))
    print("SOLVESET=", repr(sp.solveset(sp.Eq(expression, 0), x, domain=sp.S.Reals)))
    print("DISCOVERY=", discovery)
    print("PUBLIC=", [repr(point.x_symbolic) for point in result.points])

    rejected = 0
    accepted = 0
    for candidate in discovery.candidates:
        symbolic_residual = sp.simplify(expression.subs(x, candidate))
        outcome = candidates._evaluate_root_candidate(
            expression,
            x,
            candidate,
            candidates.normalize_analysis_domain(engine.numeric_context, sp.Integer(0), sp.Integer(10))
            if hasattr(candidates, "normalize_analysis_domain")
            else None,
            engine.numeric_context,
            overrides=None,
            source_label="f(x)",
        ) if False else None
        # Recreate the same physical validation without relying on a private domain alias.
        from engcalc_colab.characteristics import normalize_analysis_domain
        domain = normalize_analysis_domain(engine.numeric_context, sp.Integer(0), sp.Integer(10))
        outcome = candidates._evaluate_root_candidate(
            expression,
            x,
            candidate,
            domain,
            engine.numeric_context,
            overrides=None,
            source_label="f(x)",
        )
        print("CANDIDATE=", repr(candidate), "RESIDUAL=", repr(symbolic_residual), "ACCEPTED=", outcome.point is not None)
        if outcome.point is None:
            rejected += 1
        else:
            accepted += 1

    try:
        from engcalc_colab.characteristics import normalize_analysis_domain
        domain = normalize_analysis_domain(engine.numeric_context, sp.Integer(0), sp.Integer(10))
        fallback_points = fallback._fallback_roots(
            expression, x, domain, engine.numeric_context, overrides=None, source_label="f(x)"
        )
        print("FALLBACK=", [repr(point.x_symbolic) for point in fallback_points])
    except Exception as exc:
        print("FALLBACK_ERROR=", type(exc).__name__, str(exc))

    if discovery.candidates == () and discovery.complete:
        mechanism = "AUTHORITATIVE_EMPTY_DISCOVERY"
    elif rejected:
        mechanism = "CANDIDATE_RESIDUAL_REJECTION"
    else:
        mechanism = "NO_FAILURE_AT_CANDIDATE_VALIDATION"
    print("MECHANISM=", mechanism)
    return mechanism


def main() -> None:
    mechanisms = [classify_one(*case) for case in FAMILY]
    empty_count = mechanisms.count("AUTHORITATIVE_EMPTY_DISCOVERY")
    rejection_count = mechanisms.count("CANDIDATE_RESIDUAL_REJECTION")
    print("EMPTY_DISCOVERY_COUNT=", empty_count)
    print("RESIDUAL_REJECTION_COUNT=", rejection_count)
    assert rejection_count >= 1
    print("N1_FAMILY_DIAGNOSTIC=PASS")


if __name__ == "__main__":
    main()
