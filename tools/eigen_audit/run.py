import sys, contextlib, io
from IPython.display import Math
import engcalc_colab.magic as magic
src = open(sys.argv[1], encoding="utf-8").read()
out=[]
magic.display = out.append
buf=io.StringIO()
with contextlib.redirect_stdout(buf):
    magic.EngMagics().eng("", src)
for o in out:
    print(getattr(o,'data',o))
print("STDOUT:", buf.getvalue())
