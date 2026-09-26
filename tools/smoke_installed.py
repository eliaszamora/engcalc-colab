"""Smoke an installed EngCalc from outside the repository, the way a notebook loads it.

    python -m venv /tmp/v && /tmp/v/bin/pip install ipython==7.34.0 numpy==2.2.6 \\
        matplotlib==3.10.0 sympy==1.13.3
    /tmp/v/bin/pip install --upgrade --no-cache-dir \\
        git+https://github.com/eliaszamora/engcalc-colab.git@main
    cd / && /tmp/v/bin/python /path/to/tools/smoke_installed.py

It refuses to run against `src/`: what it certifies is the installed copy. Each check
starts from `%eng_reset`, so no check reads a name another one defined. The smokes of
0.31.x-0.41.0 lived in session scratchpads and were lost with them; this one is kept here
so the next release closure starts from it. Add a check for each release's new behaviour.

The other half of a closure is the page comparison: render every `tools/*.eng` sheet with
`tools/render_memoria.py` in each palette (none, kN, kgf) once from the installed package
and once with `PYTHONPATH=src`, and `cmp` the HTML files.
"""
import contextlib
import importlib.metadata
import io
import sys

import matplotlib

matplotlib.use("Agg")

from IPython.testing.globalipapp import start_ipython  # noqa: E402

ip = start_ipython()

import engcalc_colab  # noqa: E402
import engcalc_colab.magic as magic  # noqa: E402

if "site-packages" not in engcalc_colab.__file__:
    sys.exit(f"not an installed copy: {engcalc_colab.__file__}")

OUT = []
magic.display = lambda obj: OUT.append(obj)
ip.run_line_magic("load_ext", "engcalc_colab")


def run(cell, units=""):
    OUT.clear()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        ip.run_line_magic("eng_reset", "")
        ip.run_line_magic("eng_units", units)
        ip.run_cell_magic("eng", "", cell)
    text = [buf.getvalue()]
    for obj in OUT:
        for attr in ("data", "_repr_latex_", "_repr_html_", "_repr_markdown_"):
            value = getattr(obj, attr, None)
            if callable(value):
                value = value()
            if isinstance(value, str):
                text.append(value)
                break
    return "\n".join(text)


results = []


def check(name, cell, *want, absent=(), units=""):
    text = run(cell, units)
    missing = [w for w in want if w not in text]
    present = [a for a in absent if a in text]
    ok = not missing and not present
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        print("   missing", missing, "present", present, "\n", text[:1500])


version = importlib.metadata.version("engcalc-colab")
print(f"engcalc-colab {version} at {engcalc_colab.__file__}")
results.append(engcalc_colab.__version__ == version)
print(("PASS " if results[-1] else "FAIL ") + "__version__ matches the installed metadata")

# 0.41.0: a unit in brackets; a unit letter the sheet defined is that name
check("sheet formula outranks its unit spelling", "a := 2\nm = 3*a\nx := 4*m", "24.00")
check("bracketed unit", "L := 6[m]\nq := 10[kN/m]\nM := q*L^2/8",
      r"45.00\,\mathrm{kN} \cdot \mathrm{m}", r"6.00\,\mathrm{m}")
check("compound bracketed unit", "k := 2000[kN/m]", r"2000.00\,\frac{\mathrm{kN}}{\mathrm{m}}")
check("index stays an index", "d := [1, 2; 3, 4]\nu := d[2,1]", "3.00")
check("m as a name, bracketed units", "m := 500[kg]\nk := 2000[kN/m]\nw := sqrt(k/m)",
      r"63.25\,\frac{1}{\mathrm{s}}", absent=("kN/kg",))
check("re-run stop, not kN/kg", "k := 2000*kN/m\nm := 500*kg\nk := 2000*kN/m",
      "write the unit in brackets", "2000[kN/m]",
      absent=(r"\frac{\mathrm{kN}}{\mathrm{kg}}",))
check("unknown name in brackets refused", "L := 6[foo]", "line 1")
# 0.41.0: a computed angle in degrees
check("atan in degrees", "theta := atan(3/4)\ny := sin(theta)", r"36.87^{\circ}", "0.60")
check("negative angle keeps its sign", "t := atan(-1)", r"-45.00^{\circ}")
check("declared rad kept", "t := 0.5*rad", r"\mathrm{rad}", absent=(r"^{\circ}",))
check("rad/s untouched", "w := 3*rad/s", "3.00", absent=(r"^{\circ}",))
check("numeric of a value is one row",
      "k_2 := 2000[kN/m]\nm_2 := 500[kg]\nw_2 = sqrt(k_2/m_2)\nnumeric(w_2)", "63.25",
      absent=(r"w_{2} & = & \displaystyle w_{2}",))
# 0.40.0 and earlier, kept
check(":= reads =", "d_1 = 2*m\nD := [d_1; 3*m]", "2.00")
check("brackets once in a function", "theta := 0.5\ny = sin(theta)\nnumeric(y)", absent=("((",))
check("sum as written", "theta := 0.93\nphi := 0.59\ny = sin(theta + phi)\nnumeric(y)",
      r"\theta + \phi", absent=(r"\phi + \theta",))
check("substitution in written order",
      "h = 60*cm\ncover = 4*cm\ndb = 2*cm\ndb_st = 1*cm\nkeep d = h - cover - db_st - db/2",
      r"= & \displaystyle 60\,\mathrm{cm} - 4\,\mathrm{cm}")
check("min", "a := 2[m]\nb := 3[m]\nc := min(a, b)", r"2.00\,\mathrm{m}")
check("no real value refused", "z := sqrt(-4)", "has no real value",
      absent=("Traceback", "TypeError"))
check("% if", "a := 3\n% if a > 2\nb := 1\n% else\nb := 2\n% end", "b")
check("% for", "% for c in [1, 2]:\nz_{c} := {c}*3[m]\n% end", r"6.00\,\mathrm{m}", r"z_{2}")
check("% while counter", "i := 0\n% while i < 3\ni := i + 1\n% end", "3.00")
check("Hz", "f := 5*Hz", r"5.00\,\mathrm{Hz}")
check("eigen unit upright", "A = [2*kN/m, 0; 0, 3*kN/m]\neigenvals(A)", r"\mathrm{kN}")
check("kgf palette", "P := 1000[kgf]\nA := 10[cm^2]\ns := P/A",
      r"100.00\,\frac{\mathrm{kgf}}{\mathrm{cm}^{2}}", units="kgf")

OUT.clear()
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    ip.run_line_magic("eng_help", ":=")
help_text = buf.getvalue() + "".join(str(getattr(o, "data", "")) for o in OUT)
for name, want in (("eng_help := recommends 6[m]", "6[m]"), ("eng_help in Spanish", "Ejemplo")):
    results.append(want in help_text)
    print(("PASS " if results[-1] else "FAIL ") + name)

print(f"{sum(results)}/{len(results)}")
sys.exit(0 if all(results) else 1)
