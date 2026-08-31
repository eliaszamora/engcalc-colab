from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "src" / "engcalc_colab"
MONOLITH = SOURCE_DIR / "characteristics.py"
PACKAGE = SOURCE_DIR / "characteristics"
EXPECTED_MODULES = (
    "__init__.py",
    "domain.py",
    "candidates.py",
    "fallback.py",
    "roots.py",
    "intersections.py",
    "extrema.py",
    "piecewise_analysis.py",
)


if not MONOLITH.exists():
    missing = [name for name in EXPECTED_MODULES if not (PACKAGE / name).exists()]
    if missing:
        raise SystemExit(
            "Task 12 monolith is absent but package is incomplete: " + ", ".join(missing)
        )
    print("Task 12 decomposition already materialized.")
    raise SystemExit(0)

source = MONOLITH.read_text(encoding="utf-8")
lines = source.splitlines(keepends=True)
tree = ast.parse(source)

definitions: dict[str, ast.AST] = {}
assignments: dict[str, ast.AST] = {}
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        definitions[node.name] = node
    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                assignments[target.id] = node


def _node_text(node: ast.AST) -> str:
    if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
        raise SystemExit(f"Task 12 cannot extract node without source span: {node!r}")
    start = int(node.lineno)
    decorators = getattr(node, "decorator_list", ())
    if decorators:
        start = min(start, *(int(item.lineno) for item in decorators))
    end = int(node.end_lineno)
    return "".join(lines[start - 1 : end]).rstrip()


def definition(name: str) -> str:
    try:
        return _node_text(definitions[name])
    except KeyError as exc:
        raise SystemExit(f"Task 12 definition not found: {name}") from exc


def assignment(name: str) -> str:
    try:
        return _node_text(assignments[name])
    except KeyError as exc:
        raise SystemExit(f"Task 12 assignment not found: {name}") from exc


def write_module(
    filename: str,
    header: str,
    names: tuple[str, ...],
    *,
    assignment_names: tuple[str, ...] = (),
    extra_blocks: tuple[str, ...] = (),
) -> None:
    blocks: list[str] = [header.strip()]
    blocks.extend(assignment(name) for name in assignment_names)
    blocks.extend(block.strip() for block in extra_blocks if block.strip())
    blocks.extend(definition(name) for name in names)
    (PACKAGE / filename).write_text("\n\n\n".join(blocks).rstrip() + "\n", encoding="utf-8")


PACKAGE.mkdir(parents=True, exist_ok=True)

write_module(
    "domain.py",
    r'''
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import sympy as sp

from ..errors import EngEvaluationError
''',
    (
        "AnalysisDomain",
        "ContinuousRegion",
        "_analysis_variable",
        "_has_explicit_nonfinite_value",
        "_evaluate_domain_bound",
        "normalize_analysis_domain",
        "_quantity_is_zero",
    ),
)

write_module(
    "fallback.py",
    r'''
from __future__ import annotations

import math
from typing import Any

import mpmath as mp
import sympy as sp
from pint.errors import DimensionalityError

from ..errors import EngEvaluationError
from ..models import CharacteristicPoint
from .domain import AnalysisDomain
''',
    (
        "_fallback_response_quantity",
        "_fallback_magnitude_in_unit",
        "_fallback_canonical_unit",
        "_fallback_root_point",
        "_fallback_roots",
    ),
    assignment_names=(
        "_FALLBACK_SCAN_COUNT",
        "_FALLBACK_REL_RESIDUAL_TOL",
        "_FALLBACK_X_DEDUP_REL_TOL",
    ),
    extra_blocks=(
        '''def _deduplicate_root_points(points, domain):\n    from .candidates import _deduplicate_root_points as deduplicate\n\n    return deduplicate(points, domain)''',
    ),
)

write_module(
    "candidates.py",
    r'''
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import sympy as sp
from pint.errors import DimensionalityError

from ..errors import EngEvaluationError
from ..models import CharacteristicPoint
from .domain import AnalysisDomain
from .fallback import _FALLBACK_X_DEDUP_REL_TOL, _fallback_roots
''',
    (
        "_ExactDiscovery",
        "_CandidateEvaluation",
        "_coerce_exact_discovery",
        "_exact_real_solution_set",
        "_normalize_candidate_quantity",
        "_candidate_in_domain",
        "_evaluate_root_candidate",
        "_ordered_unique_points",
        "_deduplicate_root_points",
        "_solve_continuous_zero_set",
    ),
)

write_module(
    "piecewise_analysis.py",
    r'''
from __future__ import annotations

import math
from typing import Any

import sympy as sp
from pint.errors import DimensionalityError

from ..errors import EngEvaluationError, diagnostic_hint
from ..models import CharacteristicInterval, CharacteristicPoint
from ..piecewise import extract_symbolic_breakpoints
from .candidates import _candidate_in_domain, _normalize_candidate_quantity
from .domain import AnalysisDomain, ContinuousRegion
''',
    (
        "_normalize_piecewise_breakpoint_quantity",
        "_piecewise_substitutions",
        "_condition_truth",
        "_select_piecewise_branch",
        "_same_branch_at_boundary",
        "_partition_piecewise_regions",
        "_candidate_in_region",
        "_point_is_covered_by_interval",
        "_piecewise_boundary_candidates",
    ),
)

write_module(
    "roots.py",
    r'''
from __future__ import annotations

from typing import Any

import sympy as sp

from ..errors import EngEvaluationError
from ..models import CharacteristicInterval, CharacteristicPoint
from .candidates import (
    _deduplicate_root_points,
    _evaluate_root_candidate,
    _solve_continuous_zero_set,
)
from .domain import AnalysisDomain, ContinuousRegion, _analysis_variable
from .piecewise_analysis import (
    _candidate_in_region,
    _partition_piecewise_regions,
    _piecewise_boundary_candidates,
    _point_is_covered_by_interval,
)
''',
    (
        "_zero_interval_for_region",
        "solve_roots_exact",
    ),
)

write_module(
    "intersections.py",
    r'''
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import sympy as sp
from pint.errors import DimensionalityError

from ..errors import EngEvaluationError
from ..models import CharacteristicInterval, CharacteristicPoint
from ..piecewise import extract_symbolic_breakpoints
from .candidates import (
    _candidate_in_domain,
    _deduplicate_root_points,
    _normalize_candidate_quantity,
    _solve_continuous_zero_set,
)
from .domain import AnalysisDomain, _analysis_variable, _quantity_is_zero
from .fallback import _FALLBACK_REL_RESIDUAL_TOL, _fallback_roots
from .piecewise_analysis import (
    _normalize_piecewise_breakpoint_quantity,
    _point_is_covered_by_interval,
    _select_piecewise_branch,
)
''',
    (
        "IntersectionRegion",
        "_compatible_response_quantities",
        "_evaluate_response_pair",
        "_active_scalar_expression",
        "_intersection_boundaries",
        "_partition_intersection_regions",
        "_candidate_strictly_inside_intersection_region",
        "_intersection_source_label",
        "_evaluate_intersection_candidate",
        "_evaluate_numeric_intersection_candidate",
        "_coincident_interval",
        "_merge_coincident_intervals",
        "solve_intersections_exact",
    ),
)

write_module(
    "extrema.py",
    r'''
from __future__ import annotations

import math
from typing import Any

import sympy as sp
from pint.errors import DimensionalityError

from ..errors import EngEvaluationError
from ..models import CharacteristicInterval, CharacteristicPoint
from .candidates import (
    _candidate_in_domain,
    _deduplicate_root_points,
    _normalize_candidate_quantity,
    _ordered_unique_points,
)
from .domain import (
    AnalysisDomain,
    ContinuousRegion,
    _analysis_variable,
    _has_explicit_nonfinite_value,
    _quantity_is_zero,
)
from .piecewise_analysis import (
    _partition_piecewise_regions,
    _point_is_covered_by_interval,
    _select_piecewise_branch,
)
from .roots import solve_roots_exact
''',
    (
        "_extrema_quantity_is_finite",
        "_extrema_point_with_roles",
        "_evaluate_extrema_candidate",
        "_quantity_strictly_inside_domain",
        "_evaluate_extrema_nearby",
        "_classify_stationary_role",
        "_extrema_canonical_unit",
        "_extrema_magnitude_in_unit",
        "_assign_global_extrema_roles",
        "_constant_extrema_interval",
        "_continuous_unbounded_directions",
        "_solve_continuous_extrema_exact",
        "_piecewise_region_domain",
        "_point_without_global_roles",
        "_constant_piecewise_region_interval",
        "_piecewise_one_sided_point",
        "_piecewise_selected_boundary_point",
        "_piecewise_local_role_at_breakpoint",
        "_same_extrema_value",
        "_extrema_point_with_value_quantity",
        "_normalize_piecewise_zero_units",
        "_piecewise_breakpoint_records",
        "_ordered_unique_extrema_points",
        "_piecewise_global_roles",
        "_solve_piecewise_extrema_exact",
        "solve_extrema_exact",
    ),
)

(PACKAGE / "__init__.py").write_text(
    '''from .domain import AnalysisDomain, normalize_analysis_domain\nfrom .extrema import solve_extrema_exact\nfrom .intersections import solve_intersections_exact\nfrom .roots import solve_roots_exact\n\n__all__ = [\n    "AnalysisDomain",\n    "normalize_analysis_domain",\n    "solve_roots_exact",\n    "solve_intersections_exact",\n    "solve_extrema_exact",\n]\n''',
    encoding="utf-8",
)

fallback_test_path = ROOT / "tests" / "test_characteristics_fallback.py"
fallback_test = fallback_test_path.read_text(encoding="utf-8")
fallback_test = fallback_test.replace(
    "import engcalc_colab.characteristics as characteristics\n",
    "import engcalc_colab.characteristics.candidates as candidates\n"
    "import engcalc_colab.characteristics.fallback as fallback\n",
)
fallback_test = fallback_test.replace(
    "characteristics,\n        \"_exact_real_solution_set\"",
    "candidates,\n        \"_exact_real_solution_set\"",
)
fallback_test = fallback_test.replace(
    "characteristics._FALLBACK_",
    "fallback._FALLBACK_",
)
fallback_test_path.write_text(fallback_test, encoding="utf-8")

acceptance_test_path = ROOT / "tests" / "test_characteristics_acceptance.py"
acceptance_test = acceptance_test_path.read_text(encoding="utf-8")
acceptance_test = acceptance_test.replace(
    "import engcalc_colab.characteristics as characteristics\n",
    "import engcalc_colab.characteristics.candidates as candidates\n",
)
acceptance_test = acceptance_test.replace(
    "characteristics,\n        \"_exact_real_solution_set\"",
    "candidates,\n        \"_exact_real_solution_set\"",
)
acceptance_test_path.write_text(acceptance_test, encoding="utf-8")

remaining_private_targets: list[str] = []
for path in sorted((ROOT / "tests").glob("test_*.py")):
    text = path.read_text(encoding="utf-8")
    if "characteristics._" in text or (
        "monkeypatch.setattr(" in text and "characteristics," in text
    ):
        remaining_private_targets.append(path.name)
if remaining_private_targets:
    raise SystemExit(
        "Task 12 has unadapted private characteristics targets: "
        + ", ".join(remaining_private_targets)
    )

MONOLITH.unlink()
print("Applied behavior-preserving Task 12 characteristics package decomposition.")
