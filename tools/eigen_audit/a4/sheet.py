import contextlib
import io
import sys

root = sys.argv[1]
sys.path.insert(0, root + "/src")
from IPython.display import Math  # noqa: E402

import engcalc_colab.magic as magic  # noqa: E402

source = open(sys.argv[2], encoding="utf-8").read()
captured = []
magic.display = captured.append
out = io.StringIO()
with contextlib.redirect_stdout(out):
    magic.EngMagics().eng("", source)
print("PRINTED:", out.getvalue())
page = " ".join(item.data for item in captured if isinstance(item, Math))
print("PAGE TAIL:", page[-700:])
