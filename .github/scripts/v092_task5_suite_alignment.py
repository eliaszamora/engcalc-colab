from pathlib import Path
import re


# Preserve inverse-trig physical angle semantics. The generic closed-number
# branch added for E/LambertW/CRootOf must not intercept asin/acos/atan before
# evaluate_scalar_function can attach the radian unit.
path = Path("src/engcalc_colab/numeric.py")
text = path.read_text()
old = "        if not expr.free_symbols and expr.is_number is True:\n"
new = (
    "        if (\n"
    "            not expr.free_symbols\n"
    "            and expr.is_number is True\n"
    "            and expr.func not in {sp.asin, sp.acos, sp.atan}\n"
    "        ):\n"
)
if new not in text:
    if old not in text:
        raise SystemExit("Task 5 inverse-trig numeric anchor not found")
    text = text.replace(old, new, 1)
path.write_text(text)


# Tests that intentionally compare engine-created symbolic objects must compare
# against the canonical symbols from that same engine now that those symbols
# carry the approved real=True assumption. Algebraic/visual expectations remain
# otherwise unchanged.
test_paths = [
    "tests/test_engine.py",
    "tests/test_matrix_calculus.py",
    "tests/test_matrix_functions.py",
    "tests/test_matrix_indexing.py",
    "tests/test_matrix_symbolic.py",
    "tests/test_matrix_user_functions.py",
    "tests/test_multiarg_functions.py",
    "tests/test_scalar_math_engine.py",
]

symbol_pattern = re.compile(r'sp\.Symbol\("([A-Za-z_][A-Za-z0-9_]*)"\)')
symbols_pattern = re.compile(r'sp\.symbols\("([A-Za-z_][A-Za-z0-9_ ]*)"\)')

for filename in test_paths:
    path = Path(filename)
    text = path.read_text()
    text = symbols_pattern.sub(
        lambda match: (
            'tuple(engine.resolve_symbol(name) for name in '
            f'"{match.group(1)}".split())'
        ),
        text,
    )
    text = symbol_pattern.sub(
        lambda match: f'engine.resolve_symbol("{match.group(1)}")',
        text,
    )
    path.write_text(text)

print("Applied Task 5 suite alignment and inverse-trig unit fix.")
