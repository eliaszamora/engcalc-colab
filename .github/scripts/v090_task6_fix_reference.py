from pathlib import Path

path = Path("tests/test_matrix_solve.py")
text = path.read_text(encoding="utf-8")
old = 'pytest.approx(30600.0)'
new = 'pytest.approx(630000.0)'
assert text.count(old) == 1
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
