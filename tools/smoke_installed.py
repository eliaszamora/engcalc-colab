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

# 0.43.2: numeric inside a formula stops the line and writes it back without it
check("numeric inside a formula is a line of its own",
      "L = 3*m\nq := 10[kN/m]\nM = q*numeric(L^2)/2",
      "numeric must be a standalone statement", "Write M = q*L^2/2, then numeric(M)",
      absent=(r"9\,\mathrm{m}^{2} \end{array}",))
check("numeric on a := line says := works out a number",
      "L_2 := 3[m]\nq_2 := 10[kN/m]\nM_3 := q_2*numeric(L_2^2)/2",
      "Write M_3 := q_2*L_2^2/2", absent=("unsupported numeric function",))
check("a condition reads numeric as its value",
      "L_2 := 3[m]\nq_2 := 10[kN/m]\nM_2 = q_2*L_2^2/2\n% if numeric(M_2) > 40*kN*m:\nnumeric(M_2)\n% end",
      r"\textbf{Como}", r"45.00\,\mathrm{kN} \cdot \mathrm{m}", absent=("standalone", "line 1"))
# 0.43.1: a free argument named like a parameter; a named numeric of a call; the := notice
check("a free argument kept apart, a named numeric, the := notice",
      "F(x, y) = x + 2*y\nnumeric(F(3, x))\nw = numeric(F(3, 4))\nu = 2*w\nL = 3*m\n"
      "M = q*L^2/2",
      "2 x + 3", r"u & = & \displaystyle 22", "'L' was defined with '='", "L := 3*m",
      absent=("argument", "2 x + 4 y"))
# 0.43.0: numeric of a call writes its argument on its first row
check("numeric of a call writes its argument",
      "L := 6[m]\nq := 10[kN/m]\na := 2[m]\nR_A = q*L/2\nM(x) = R_A*x - q*x^2/2\n"
      "numeric(M(L/2))\nM_D(x) = q*x*(L - x)/2\nnumeric(M_D(L - a))",
      r"R_{A}\,\left(\frac{L}{2}\right)", r"L - \left(L - a\right)",
      r"45.00\,\mathrm{kN} \cdot \mathrm{m}", absent=("L - L - a",))
# 0.42.3: a kept name in a matrix function; a derivative worked out with its factor
check("a kept name in a matrix function and a derivative's number",
      "E := 200[GPa]\nA := 10[cm^2]\nL := 3[m]\nk = E*A/L\nK(x) = [k*x, 0; 0, k]\n"
      "q := 10[kN/m]\nR_A = q*L/2\nZ = 2*diff(R_A*x^2, x)",
      r"\left[\begin{matrix}\displaystyle k x & \displaystyle 0", r"= 4 R_{A} x",
      absent=(r"\frac{E A x}{L}", r"2 \cdot 2 R_{A}"))
# 0.42.2: a kept name reaches an equation and numeric of a call
check("a kept name in an equation and a call",
      "L := 6[m]\nq := 10[kN/m]\nR_A = q*L/2\nV(x) = R_A - q*x\nx_0 = solve(eq(V(x), 0), x)\n"
      "M(x) = R_A*x - q*x^2/2\nnumeric(M(L/2))",
      r"R_{A} - q x = 0", r"\left(30.00\,\mathrm{kN}\right)", r"45.00\,\mathrm{kN} \cdot \mathrm{m}",
      absent=(r"\frac{q L}{2} - q x = 0",))
# 0.42.1: a kept name reaches an integral and a function of a function
check("a kept name inside an integral",
      "L := 6[m]\nq := 10[kN/m]\nR_A = q*L/2\nV(x) = R_A - q*x\nM(x) = integrate(V(x), x, 0, x)\n"
      "W(x) = 2*V(x)\nnumeric(M(L/2))",
      r"\int\limits_{0}^{x} \left(R_{A} - q x\right)\, dx", r"2 \left(R_{A} - q x\right)",
      r"45.00\,\mathrm{kN} \cdot \mathrm{m}", absent=(r"\frac{q L}{2} - q x",))
# 0.42.0: a formula whose names have values reads in its names; two numbers set apart
check("a valued formula stays a name",
      "phi := 0.9\nAs := 1500[mm^2]\nfy := 420[MPa]\nh := 500[mm]\ncover := 40[mm]\n"
      "b := 300[mm]\nfc := 28[MPa]\nd = h - cover\na = As*fy/(0.85*fc*b)\n"
      "phiMn = phi*As*fy*(d - a/2)\nnumeric(phiMn)",
      r"\left(d - \frac{a}{2}\right)", r"235.81\,\mathrm{kN} \cdot \mathrm{m}", absent=("0.59",))
check("a value written out still folds", "L = 6*m\nq = 10*kN/m\nM = q*L^2/8",
      r"45\,\mathrm{kN} \cdot \mathrm{m}")
check("two numbers set apart",
      "fc := 30[MPa]\nfy := 420[MPa]\nb := 300[mm]\nAs := 1935[mm^2]\nd := 446[mm]\n"
      "phiMn = fy*As*(d - fy*As/(0.85*fc*b)/2)", r"2 \cdot 0.85", absent=("2 0.85",))
# 0.41.2: a paragraph fills the width; extrema of an angle
check("a paragraph breaks where the page ends", '"""Una viga de $L = 6$ m de luz."""',
      r"\small \text{Una }\allowbreak", r"{L = 6}\text{ }\allowbreak", absent=(r"\footnotesize",))
check("extrema of an angle", "L := 4*m\nh(x) = atan(x/L)\nextrema(h(x), x, 0*m, L)",
      r"\left(45.00^{\circ}\right)", absent=("incompatible",))
# 0.41.1: the last definition is the one read
check("= drops a := value", "p := 500*kg\na := 2\np = 3*a\nx := 4*p",
      r"x & = & \displaystyle 24.00", absent=("2000.00",))
check("= after keep drops the kept number", "h := 60*cm\nkeep d = h - 4*cm\nd = 3*h\nx := 2*d",
      r"x & = & \displaystyle 360.00\,\mathrm{cm}", absent=("112.00",))
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

# 0.41.1: `%eng_units none` clears the palette
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    ip.run_line_magic("eng_units", "kN")
    ip.run_line_magic("eng_units", "none")
results.append("engcalc units: cleared (was kN)" in buf.getvalue())
print(("PASS " if results[-1] else "FAIL ") + "eng_units none clears the palette")

print(f"{sum(results)}/{len(results)}")
sys.exit(0 if all(results) else 1)
