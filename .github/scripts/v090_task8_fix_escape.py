from pathlib import Path

path = Path("src/engcalc_colab/renderer.py")
text = path.read_text(encoding="utf-8")
old = 'body = r"\\".join(" & ".join(row) for row in rows)'
new = 'body = r"\\\\".join(" & ".join(row) for row in rows)'
assert old in text, text[text.find("def _matrix_from_cells_latex"):text.find("def _matrix_latex")]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
