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

# 0.48.1: angles with their mark, powers of ten as powers of ten
check("an angle in degrees reads with its mark",
      "P := 10[kN]\nF = P*cos(45*deg)\nnumeric(F)\na := [30[deg], 45[deg]]",
      r"\cos{\left(45^{\circ} \right)}", r"30^{\circ}", absent=(r"\mathrm{deg}",))
check("a round-off entry does not move a vector to newtons",
      "F := [1[kN]; 1e-7[kN]]", r"\end{matrix}\right]\,\mathrm{kN}", absent=("1e-07", "1000.00"))

# 0.48.0: what a matrix sheet asks of := lines and loops
check("km, lb and percent are units",
      "L := 2[km]\nP := 1[kip] + 1000[lb]\nr := 5[percent]\nQ := r*100[kN]",
      r"2.00\,\mathrm{km}", r"5.00\,\mathrm{kN}", absent=("not a unit",))
check("the kip palette reads kips and inches",
      "L := 12[ft]\nP := 10[kip]\nM := P*L", r"1440.00\,\mathrm{kip} \cdot \mathrm{in}", units="kip")
check("a part of a matrix by a named list and by a range",
      "K := [2,-1,0;-1,2,-1;0,-1,1]*1000[kN/m]\nlibres := [1, 2]\nK_f := K[libres, libres]\nK_g := K[2:3, 2:3]",
      r"K_{g}", absent=("an index on a := line",))
check("a 1x1 matrix plus a number",
      "k := 100[kN/m]\ng := [1; -1]\nD := [2[mm]; 1[mm]]\nN := k*transpose(g)*D + 1[kN]", r"= 1.10\,\mathrm{kN}")
check("a matrix function on a := line",
      "k_e(E, A, L) = E*A/L*[1, -1; -1, 1]\nK_1 := k_e(200[GPa], 10[cm^2], 2[m])",
      r"\displaystyle 100.00 & \displaystyle -100.00", absent=("ImmutableDenseMatrix",))
check("% break stops a loop",
      "% for i in range(1, 6):\nP_{i} := {i}*10[kN]\n% if P_{i} > 25[kN]:\n% break\n% end\n% end",
      r"\text{: el ciclo se detiene.}", absent=("P_{4}",))
check("argmax and rank on a := line",
      "f := [3[kN]; 7[kN]; 2[kN]]\ni := argmax(f)\nK := [1,-1;-1,1]*5[kN/m]\nr := rank(K)",
      r"\operatorname{argmax}\left(f\right) = 2.00", r"\operatorname{rank}\left(K\right) = 1.00")

# 0.47.1: units of one kind cancel, parentheses where the reading needs them
check("a strain times a modulus reads as a stress",
      "r := 2[mm/m]*200000[MPa]", r"400.00\,\mathrm{MPa}", absent=(r"\mathrm{mm} \cdot",))
check("a bracketed moment reads force first",
      "M = 2.5[kip*ft]", r"\mathrm{kip} \cdot \mathrm{ft}")
check("a power of a fraction keeps its parentheses",
      "x := [3[kN]; 4[kN]]\ny := 2[kN]\np := (x[1]/y)^2", r"\left(\frac{x_{1}}{y}\right)^{2}")
check("a function dividing by a decimal is written as typed",
      "f(x) = x/0.85", r"\frac{x}{0.85}")
check("a matrix refusal quotes units as typed",
      "k := [2[kN/m]; 3[kN/m]]\ny := 5[kN/m] - k", "'5[kN/m] - k' adds a number", absent=("__u_",))

# 0.47.0: eigenvals(K, G) with a singular G, worked out exactly
check("eigenvals with a singular second matrix",
      "K := [2[kN/m], -1[kN/m]; -1[kN/m], 1[kN/m]]\nG := [1[kN/m], 0[kN/m]; 0[kN/m], 0[kN/m]]\nl := eigenvals(K, G)",
      r"\operatorname{eigenvals}\left(K, G\right)", r"& = & \displaystyle 1.00", absent=("singular",))
check("eigenvals of a pencil with a complex pair is refused",
      "K := [1[kN/m], 2[kN/m]; 2[kN/m], -1[kN/m]]\nG := [0[kN/m], 1[kN/m]; 1[kN/m], 0[kN/m]]\nl := eigenvals(K, G)",
      "not real")
# 0.46.2: a root in its own unit, refusals as typed
check("a range solve with bounds in inches",
      "x := solve(eq(x, 2[inch]), x, 0[inch], 10[inch])", r"x & = & \displaystyle 2.00\,\mathrm{in}",
      absent=("invalid syntax",))
check("a root in tonnes is not the sheet's t",
      "t := 10[mm]\nx := solve(eq(x, 2[ton]), x, 0[ton], 10[ton])",
      r"x & = & \displaystyle 2.00\,\mathrm{t}", absent=(r"20.00\,\mathrm{mm}",))
check("a refused condition is quoted as typed",
      "f := [100[kip]; 50[kip]]\n% if f[1] > 0.5[m]:\ny := 1\n% end",
      "f[1] > 0.5[m]: kN against m", absent=("__u_", "m·kg"))
check("a placeholder in a unit's brackets",
      "P := 5[kN]\n% u = 'kN'\n% if P > 3[{u}]:\ny := 1\n% end", r"y & = & \displaystyle 1.00",
      absent=("holds no unit",))
# 0.46.1: what chapter 10 found
check("max of a ratio of units is compared converted",
      "r := max(1[kN]/1[kip], 0.5)", r"r & = & \displaystyle 0.50")
check("a value too large for a float is refused with a message",
      "x := 1e300*1e300", "too large for a number to hold", absent=("Traceback", "OverflowError"))
check("a placeholder in a name in a condition, an entry of a := matrix in another",
      "h_1 := 0\n% for e in [1]:\n% if h_{e} < 0.5:\ny_{e} := 1\n% end\n% end\n"
      "f := [1[kip]; 2[kip]]\n% if f[1] > 0.5[kip]:\nz := 1\n% end",
      r"y_{1}", r"f_{1} = ", absent=("is not one", "Use it on a := line"))
check("a range solve over entries of a := matrix",
      "f := [200[kip]; 900[kip*inch]]\ndf := [1[kip]; 2[kip*inch]]\n"
      "x := solve(eq(f[1] + x*df[1], 300[kip]), x, 0, 1000)",
      r"x & = & \displaystyle 100.00", absent=("unknown numeric name",))
# 0.46.0: lines that continue, T' and U^-1
check("a solve over three lines, T', U^-1 on a := line",
      "x_1 := solve(eq(x^2, 2),\n             x, 0, 3)\nU := [2, 0; 0, 4[kN/m]]\nV := U'\nX := U^-1",
      r"x_{1} & = & \displaystyle 1.41", r"U^{T}", r"U^{-1}",
      absent=("unbalanced", "invalid syntax", "not an operation"))
# 0.45.7: a complex pair beside a large eigenvalue
check("eigenvals refuses ±i beside 1e12",
      "A := [0, -1, 0; 1, 0, 0; 0, 0, 1e12]\nv := eigenvals(A)",
      "not real")
# 0.45.6: what chapter 9 found
check("a critical load by eigenvals, a rotation's zero without a metre, {a} in a while",
      "E := 200000[MPa]\nI := 8e7[mm^4]\nl := 4[m]\nK := E*I/l^3*[12, -6*l; -6*l, 4*l^2]\n"
      "G := -1/(30*l)*[36, -3*l; -3*l, 4*l^2]\nlam := eigenvals(K, -G)\nP_cr := lam[1]\n"
      "k := 1000[kN/m]\nS := [k, 0; 0, 2*k*1[m^2]]\nF := [10[kN]; 0]\nd := solve(S, F)\n"
      "theta := d[2]\n% for a in [2]:\nr := 1\n% while abs(r^2 - {a}) > 1e-9:\nr := (r + {a}/r)/2\n% end\n% end",
      r"2485.96\,\mathrm{kN}", r"\theta & = & \displaystyle d_{2} = 0.00 \\", r"r & = & \displaystyle 1.41",
      absent=("not a unit", "unsupported", "Set"))
# 0.45.5: what chapter 8 found
check("an angle root, subs on :=, an integral by quadrature",
      "a := 15[deg]\nt_1 := solve(eq(cos(a - t)^3, cos(a)), t, 0[deg], 15[deg])\ny := sin(t_1)\n"
      "f = 2*sin(t)\nt_0 := 30[deg]\nx_1 := subs(f, t, t_0)\n"
      "b := 1[m]\nc := 1.5[m]\nH := integrate(x^2/(1 - x/(2*b))^(3/2), x, b, c)",
      r"6.31^{\circ}", r"y & = & \displaystyle 0.11", r"3.96\,\mathrm{m}^{3}",
      absent=("unsupported", "does not support"))
# 0.45.4: what chapter 7 left
check("a rotation's inverse, a whole number, ln, a collected integral",
      "Q = inv([cos(t), sin(t); -sin(t), cos(t)])\nassume(L > 0)\nassume(n > 0, integer(n))\n"
      "s = sin(n*pi)\nh = ln(x)\nf(x) = (6/L^2 - 12*x/L^3)*((1 - x/L)*a + x/L*c)\n"
      "S = integrate(f(x), x, 0, L)",
      r"n \in \mathbb{Z}", r"\ln{\left(x \right)}", r"\frac{a - c}{L}",
      absent=(r"\log", "unsupported"))
# 0.45.3: what chapter 7 found read wrong or refused
check("a flexibility in kN and m, a stiffness assembled on := lines, an assumed psi",
      "E := 200000[MPa]\nI := 150e6[mm^4]\nL := 12[m]\nf := L/(E*I)\n"
      "k := 2[kN/m]\nK := zeros(3, 3)\n% for e in [1, 2]:\n"
      "K[[{e}, {e}+1], [{e}, {e}+1]] := K[[{e}, {e}+1], [{e}, {e}+1]] + k*[1, -1; -1, 1]\n% end\n"
      "assume(psi > 0)\nd = integrate(sin(phi), phi, 0, psi)",
      r"0.0004\,\frac{1}{\left(\mathrm{kN} \cdot \mathrm{m}\right)}", r"\displaystyle 4.00 & \displaystyle -2.00",
      r"\int\limits_{0}^{\psi}",
      absent=("MPa} \\cdot", "psi (pound", "invalid numeric assignment"))
# 0.45.2: what chapter 6 found breaking the page
check("an integral with bracket units, a nested piecewise, q = solve(..., q)",
      "L := 9[m]\nW = integrate((270[kN*m] - 30[kN]*x)*(L - x), x, 6[m], L)\n"
      "f(x) = piecewise(1, x < 1, piecewise(2, x < 2, 3))\n"
      "g(x) = q*x\nq = solve(eq(2*q, P), q)\nz = g(2)",
      r"- 5\,\mathrm{kN}\,L^{3}", r"3 & \text{otherwise} \end{cases}", r"& = & \displaystyle P",
      absent=("__u", "[4pt] [4pt]", "spacing metadata"))
# 0.45.1: what chapter 5 found
check("unknowns that cancel, the inch in brackets, a parameter s",
      "L_1 := 2[m]\nP := 10[kN]\ntheta = P*L_1^2/(E*I)\nr = E*I/L_1^2*theta\nnumeric(r)\n"
      "A := 10.6[in^2]\nf(c, s) = c + 2*s",
      r"10.00\,\mathrm{kN}", r"10.60\,\mathrm{in}^{2}", r"c + 2 s",
      absent=("requires values", "not a unit", r"\mathrm{s}"))
# 0.45.0: a temperature, the hyperbolic functions, a row on a := line
check("a temperature, sinh, a row on a := line",
      "alpha := 1.17e-5[1/degC]\ndT := 40[degC]\nL := 3[m]\nu := alpha*L*dT\n"
      "y := sinh(0.5)\nc := 0.6\ns := 0.8\nk := 2[kN/mm]\nd := [3[mm]; 1[mm]]\nF := k*[c, s]*d",
      r"40.00\,{}^{\circ}\mathrm{C}", r"1.40\,\mathrm{mm}", "0.52", r"5.20\,\mathrm{kN}",
      absent=("not a unit", "unsupported"))
# 0.44.1: what the book's worked examples found
check("a function reads what a later solve fixed; subs of a defined name",
      "y(x) = C_1*x + C_2 + p*x^2\nsolve(eq(subs(y(x), x, 0), 0), eq(subs(y(x), x, 1), 0), C_1, C_2)\n"
      "t = subs(diff(y(x), x), x, 0)\ng = diff(t, p)\nF = k*(u - x)\nu = P/k\nG = subs(F, u, 0)",
      r"g & = & \displaystyle \frac{d}{d p} \left(- p\right) = -1", r"G & = & \displaystyle - k x")
# 0.44.0: a loop that assembles shows it once; its := values are one table
check("an assembly is shown once, a table of the loop's values",
      "k := 100[kN/mm]\nK = zeros(3, 3)\n% for p, q in [(1, 2), (2, 3)]:\n"
      "K[[{p}, {q}], [{p}, {q}]] = K[[{p}, {q}], [{p}, {q}]] + k*[1, -1; -1, 1]\n% end\n"
      "% for i in [1, 2]:\nL_{i} := {i}[m]\nc_{i} := 2*L_{i}\n% end\nZ = zeros(36, 36)",
      r"\textbf{Ensamble en 2 pasos}", r"\hline", r"\mathbf{0}_{36 \times 36}",
      absent=("__u", r"L_{1} & = &"))
# 0.43.4: what chapter 3 of his book found
check("a bracket unit is read as its unit; no alias on the page",
      "k := 100[kN/mm]\nD := [3[mm]; 1[mm]]\nF := k*D\nS := F[1] + 1[kN]\n"
      "E := 200000[MPa]\nA := 1000[mm^2]\nK = A*E/(5[m])*[1, -1; -1, 1]\nnumeric(K)",
      r"301.00\,\mathrm{kN}", absent=(r"\mathrm{kg}}{\mathrm{s}^{2}}", "__u"))
# 0.43.3: what chapter 2 of his book found
check("a coefficient keeps its figures, a denominator its fraction, := solve",
      "k = 2.8*E*A/L\nu = 0.0025*L\nR = -k*u\nkeep c = A*E/L\nw = P/(5*c/4)\n"
      "a := 2[m]\nb := 3[kN/m]\nx_2 := solve(eq(b*x, a*b - x*b), x)",
      r"- 0.007 E A", r"\frac{P}{\frac{5 c}{4}}", r"1.00\,\mathrm{m}",
      absent=("0.01 E A", r"5 \frac{1}{4}", "unsupported numeric function"))
check("a bare solve says how to keep its answer",
      "q := 10[kN/m]\nL := 6[m]\nsolve(eq(2*T, q*L), T)\nZ = 2*T\nnumeric(Z)",
      "T on line 3 was solved on a line of its own", "write T = solve(...) to use it")
# 0.43.2: numeric inside a formula stops the line and writes it back without it; a condition reads it
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
