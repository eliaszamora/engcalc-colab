"""ENGROOT=<tree> python page.py sheet.eng -> prints the eigenvalue column as shown and stdout."""
import contextlib
import io
import os
import sys

sys.path.insert(0, os.environ["ENGROOT"] + "/src")
from IPython.display import Math  # noqa: E402
import engcalc_colab.magic as magic  # noqa: E402

captured = []
magic.display = captured.append
out = io.StringIO()
with contextlib.redirect_stdout(out):
    magic.EngMagics().eng("", open(sys.argv[1], encoding="utf-8").read())
page = " ".join(item.data for item in captured if isinstance(item, Math))
col = page.split("l & = &", 1)[1] if "l & = &" in page else page[-1500:]
print(col.split(r"\end{array}", 1)[0][-1200:])
print("STDOUT:", out.getvalue()[:400])
