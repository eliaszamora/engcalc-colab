"""What each call takes, and a worked example of it, for `%eng_help`.

A notebook gives no help for a cell magic's own language. `Shift+Tab` reads a Python
object's signature, and `integrate` inside `%%eng` is not one - it is a name in a
restricted grammar. So the help is a line magic, alongside `%eng_reset` and
`%eng_config`.

Every entry carries a runnable example rather than a sketch. A help text that does not
run is worse than none: it teaches a form the language refuses, and the reader blames
their own typing. `tests/test_eng_help.py` executes all of them, and also checks that the
catalogue and the parser's allowed calls are the same set in both directions, so a
function added without an entry fails the suite rather than being silently unhelpable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CallHelp:
    """One entry: the shapes the call accepts, what goes in each slot, and an example."""

    name: str
    summary: str
    forms: tuple[str, ...]
    arguments: tuple[tuple[str, str], ...]
    example: str
    # "call", or "statement" for the forms written without parentheses: `keep`, `case`,
    # `combo` and `:=`.
    kind: str = "call"
    # What it is for, when the forms and the example do not say it by themselves.
    note: str = ""

    def __post_init__(self) -> None:
        if not self.forms:
            raise ValueError(f"{self.name}: an entry must show at least one form")
        if not self.example.strip():
            raise ValueError(f"{self.name}: an entry must carry a runnable example")


def _scalar(name: str, summary: str, example_argument: str) -> CallHelp:
    return CallHelp(
        name=name,
        summary=summary,
        forms=(f"{name}(expression)",),
        arguments=(("expression", "the value to apply it to"),),
        example=f"y = {name}({example_argument})",
    )


_STATEMENTS: tuple[CallHelp, ...] = (
    CallHelp(
        name=":=",
        kind="statement",
        summary="Give a name its value, a number with its unit; a line that reads a matrix is worked out in numbers.",
        forms=("name := expression", "d := solve(K, F)"),
        arguments=(
            ("name", "the name the value is kept under"),
            ("expression", "a value with its unit, or arithmetic on values already given; with a matrix, solve, inv, transpose, + - *, and entries such as d[2,1]"),
        ),
        note=(
            "`=` defines a formula and keeps it in symbols; `:=` defines a value. "
            "numeric() puts the `:=` values into a `=` formula and shows the substitution. "
            "`d := solve(K, F)` solves in numbers - a symbolic solve of a real stiffness "
            "matrix would not finish - and the page writes the line as typed, then its numbers."
        ),
        example=(
            "L := 6*m\nq := 10*kN/m\nM = q*L^2/8\nnumeric(M)\n"
            "K = [2*kN/m, -1*kN/m; -1*kN/m, 1*kN/m]\nF = [0*kN; 10*kN]\nd := solve(K, F)"
        ),
    ),
    CallHelp(
        name="keep",
        kind="statement",
        summary="Define a value that later formulas show by its name, not by what it expands to.",
        forms=("keep name = expression",),
        arguments=(
            ("name", "the name later formulas keep, as the code names it: f_cw, R_n, As_min, d"),
            ("expression", "its definition, shown once, on its own row"),
        ),
        note=(
            "Without keep, a formula that uses the name is written with the name replaced "
            "by its definition. With f_cw = 0.85*fc, then C = f_cw*b*d, the page reads "
            "C = 0.85 b d fc. With keep f_cw = 0.85*fc it reads C = f_cw b d - the "
            "formula of the code - and the substitution puts in f_cw's own value "
            "(178.50 kgf/cm2). Use it for every intermediate a code or your reasoning "
            "names; a given value (fc := 210*kgf/cm^2) does not need it."
        ),
        example=(
            "fc := 210*kgf/cm^2\nb := 30*cm\nd := 44*cm\n"
            "keep f_cw = 0.85*fc\nC = f_cw*b*d\nnumeric(C)"
        ),
    ),
    CallHelp(
        name="case",
        kind="statement",
        summary="Name the response of one load case, as a function of the coordinate along the member.",
        forms=("case name = expression",),
        arguments=(
            ("name", "the case, such as D, Lv or EQ"),
            ("expression", "the response it gives, such as M_D(x)"),
        ),
        note=(
            "A combo adds cases with their factors. The coordinate is found rather than "
            "declared: it is the one name left once every other has a value."
        ),
        example=(
            "L := 6*m\nqD := 18*kN/m\nqL := 12*kN/m\n"
            "M_D(x) = qD*x*(L - x)/2\nM_L(x) = qL*x*(L - x)/2\n"
            "case D = M_D(x)\ncase Lv = M_L(x)\ncombo U1 = 1.2*D + 1.6*Lv\n"
            "M_u = U1(L/2)\nnumeric(M_u)"
        ),
    ),
    CallHelp(
        name="combo",
        kind="statement",
        summary="Combine load cases with the factors a code gives; the combination is then a function, U1(x).",
        forms=("combo name = factor*case + ...",),
        arguments=(
            ("name", "the combination, such as U1"),
            ("factor*case + ...", "each case by its factor, as 1.2*D + 1.6*Lv"),
        ),
        note=(
            "Written with its factors, so a reviewer checks it against the code without "
            "redoing the arithmetic. Use it as a function: U1(L/2), "
            "envelope(U1(x), U2(x), x, 0, L), governing(U1(x), U2(x), x, 0, L)."
        ),
        example=(
            "L := 6*m\nqD := 18*kN/m\nqL := 12*kN/m\n"
            "M_D(x) = qD*x*(L - x)/2\nM_L(x) = qL*x*(L - x)/2\n"
            "case D = M_D(x)\ncase Lv = M_L(x)\n"
            "combo U1 = 1.4*D\ncombo U2 = 1.2*D + 1.6*Lv\n"
            "governing(U1(x), U2(x), x, 0, L)"
        ),
    ),
)

_PLACING: tuple[CallHelp, ...] = (
    CallHelp(
        name="image",
        summary="Place a picture - a file or a URL - as a numbered Figura, embedded in the notebook.",
        forms=('image("file.png")', 'image("file.png", "caption", width=12*cm)'),
        arguments=(
            ("file", "in quotes: a path from where the notebook runs - in Colab /content, or /content/drive/MyDrive/... with Drive mounted - or an http(s) URL; png, jpg, gif, svg or webp"),
            ("caption", "optional, in quotes; it may hold $...$"),
            ("width", "optional, a length, such as 12*cm"),
        ),
        note="Figures are numbered on their own, image and frame_plot alike; a cell run again keeps its numbers and %eng_reset starts again at 1.",
        example='image("portico.png", "Geometría del pórtico", width=9*cm)',
    ),
    CallHelp(
        name="member",
        summary="Declare a member of a frame from what the sheet worked out, for frame_plot; it puts nothing on the page.",
        forms=(
            'member("name", start=[x_1, y_1], end=[x_2, y_2], forces=f)',
            'member("name", start=..., end=..., forces=f, displacements=u, EI=E*I, load=w)',
            'member("name", start=..., end=..., forces=f, load=[w_1, w_2], point=[P, a])',
        ),
        arguments=(
            ("name", "in quotes; declaring it again replaces it"),
            ("start, end", "its ends, two lengths each; x' runs from start to end, y' a quarter turn anticlockwise from it"),
            ("forces", "the six end forces in local axes, acting on the member, [N_i; V_i; M_i; N_j; V_j; M_j] - as k*T*D + f_0 gives them"),
            ("displacements", "the six end displacements in local axes, [u_i; v_i; θ_i; u_j; v_j; θ_j] - T*D; for the deformed shape"),
            ("EI", "its flexural stiffness; the deformed shape of a loaded member needs it"),
            ("load", "a load towards -y': w uniform, or [w_1, w_2] running linearly from start to end"),
            ("point", "[P, a], a load P towards -y' at a from start; several are rows, [P_1, a_1; P_2, a_2]"),
        ),
        note=(
            "Nothing is solved again. frame_plot applies equilibrium to each member from its "
            "start: N(s) = -N_i, V(s) = V_i minus the load up to s, M(s) = -M_i + V_i s minus "
            "the moment of that load. The load on a joint is read back from the end forces "
            "meeting there; a support is a joint the displacements hold still."
        ),
        example=(
            "L := 6*m\nP := 30*kN\nf := [0*kN; 20*kN; 0*kN*m; 0*kN; 10*kN; 0*kN*m]\n"
            'member("V", start=[0*m, 0*m], end=[L, 0*m], forces=f, point=[P, 2*m])\n'
            'frame_plot(M, "Momento flector")'
        ),
    ),
    CallHelp(
        name="frame_plot",
        summary="Draw M, V, N or the deformed shape on every member declared, as a numbered Figura.",
        forms=('frame_plot(M, "caption")', "frame_plot(V)", "frame_plot(N)", 'frame_plot(deformed, "caption", scale=150)'),
        arguments=(
            ("M, V, N, deformed", "the diagram; M is drawn on the tension side and is positive when it pulls the inside fibre, each member read as a beam seen from inside the frame"),
            ("caption", "optional, in quotes; the figure reads Figura n. caption"),
            ("scale", "deformed only: how many times the displacements are drawn; chosen when left out"),
        ),
        note=(
            "Values carry their sign, in boxes, in the unit the page writes; the moment's "
            "peak is marked where the shear crosses zero. The deformed shape follows the end "
            "displacements with the member's own shape functions and adds the deflection its "
            "load gives with both ends held."
        ),
        example=(
            "L := 6*m\nw := 12*kN/m\nf := [0*kN; 36*kN; 0*kN*m; 0*kN; 36*kN; 0*kN*m]\n"
            'member("V", start=[0*m, 0*m], end=[L, 0*m], forces=f, load=w)\n'
            'frame_plot(M, "Momento flector")\nframe_plot(V, "Fuerza cortante")'
        ),
    ),
)

_ENTRIES: tuple[CallHelp, ...] = (
    CallHelp(
        name="numeric",
        summary="Evaluate an expression with the values the sheet has given, and show the substitution.",
        forms=("numeric(expression)", "numeric(expression, unit)"),
        arguments=(
            ("expression", "what to evaluate; every name in it needs a `:=` value"),
            ("unit", "optional, the unit to show the answer in, as in `mm` or `kN*m`"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM_max = q*L^2/8\nnumeric(M_max, kN*m)",
    ),
    CallHelp(
        name="result",
        summary="Show the formula and its final value, without the substitution stage.",
        forms=("result(expression)", "result(expression, unit)"),
        arguments=(
            ("expression", "what to evaluate"),
            ("unit", "optional, the unit to show the answer in"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM_max = q*L^2/8\nresult(M_max, kN*m)",
    ),
    CallHelp(
        name="integrate",
        summary="Integrate an expression: two arguments for the antiderivative, four between bounds.",
        forms=(
            "integrate(expression, variable)",
            "integrate(expression, variable, lower, upper)",
        ),
        arguments=(
            ("expression", "what to integrate"),
            ("variable", "the variable of integration, as in `x`"),
            ("lower", "the lower bound; omit it, with `upper`, for the antiderivative"),
            ("upper", "the upper bound"),
        ),
        example=(
            "L := 6*m\nq := 10*kN/m\n"
            "V(x) = q*L/2 - q*x\n"
            "M(x) = integrate(V(x), x, 0, x)\n"
            "numeric(subs(M(x), x, L/2))"
        ),
    ),
    CallHelp(
        name="diff",
        summary="Differentiate an expression with respect to a variable.",
        forms=("diff(expression, variable)",),
        arguments=(
            ("expression", "what to differentiate"),
            ("variable", "the variable to differentiate by"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\nV(x) = diff(M(x), x)",
    ),
    CallHelp(
        name="solve",
        summary="Solve an equation, a system, or an inequality.",
        forms=(
            "solve(equation, unknown)",
            "solve(eq_1, ..., eq_n, x_1, ..., x_n)",
            "solve(inequality, variable, lower, upper)",
            "solve(matrix, vector)",
        ),
        arguments=(
            ("equation", "written `eq(left, right)`, or `left = right` inside the call"),
            ("unknown", "the name to solve for"),
            ("eq_1 ... eq_n", "n equations, followed by exactly n unknowns"),
            ("inequality", "a comparison such as `M(x) > 20*kN*m`"),
            ("lower, upper", "for an inequality, the domain; it is where the variable gets its unit"),
        ),
        example=(
            "L := 6*m\nq := 10*kN/m\n"
            "eqFy = eq(R_A + R_B, q*L)\n"
            "eqMA = eq(R_B*L, q*L*L/2)\n"
            "solve(eqFy, eqMA, R_A, R_B)"
        ),
    ),
    CallHelp(
        name="eq",
        summary="Build an equation from its two sides, for `solve`.",
        forms=("eq(left, right)",),
        arguments=(("left", "the left-hand side"), ("right", "the right-hand side")),
        example="L := 6*m\nq := 10*kN/m\neqFy = eq(R_A + R_B, q*L)",
    ),
    CallHelp(
        name="subs",
        summary="Replace a variable by a value in an expression.",
        forms=("subs(expression, variable, value)", "subs(expression, v1, x1, v2, x2, ...)"),
        arguments=(
            ("expression", "what to substitute into"),
            ("variable", "the name to replace"),
            ("value", "what to put in its place"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\nnumeric(subs(M(x), x, L/2))",
    ),
    CallHelp(
        name="sum",
        summary="Sum an expression over an index between two bounds.",
        forms=("sum(expression, index, lower, upper)",),
        arguments=(
            ("expression", "the term, written in terms of the index"),
            ("index", "the summation index, as in `i`"),
            ("lower", "the first value of the index"),
            ("upper", "the last value of the index"),
        ),
        example="n := 5\nP := 10*kN\nS = sum(P*i, i, 1, n)\nnumeric(S)",
    ),
    CallHelp(
        name="macaulay",
        summary="A Macaulay bracket, zero before its offset. Usually written `<x-a>^n`.",
        forms=("macaulay(shifted, order)", "<x-a>^n"),
        arguments=(
            ("shifted", "the shifted coordinate, as in `x - a`"),
            ("order", "the power; 1 for a point load in a moment law"),
        ),
        example=(
            "L := 8*m\nP := 40*kN\na := 3*m\n"
            "R_A = P*(L-a)/L\n"
            "M(x) = R_A*x - P*<x-a>^1\n"
            "numeric(subs(M(x), x, L))"
        ),
    ),
    CallHelp(
        name="assume",
        summary="State what is known about a symbol, before the symbol is first used.",
        forms=("assume(symbol > 0)", "assume(a > 0, b >= 0, ...)"),
        arguments=(
            ("symbol > 0", "a comparison against zero: `>`, `>=`, `<` or `<=`"),
        ),
        example="assume(Lk > 0)\nf(Lk) = Lk^2\nsolve(eq(f(Lk), 4), Lk)",
    ),
    CallHelp(
        name="report",
        summary="Show a value where it is written and mark it for the summary.",
        forms=("report(name)",),
        arguments=(("name", "a name the sheet has already defined"),),
        example="L := 6*m\nq := 10*kN/m\nM_max = q*L^2/8\nreport(M_max)",
    ),
    CallHelp(
        name="summary",
        summary="Print every value marked with `report`, in the order they were marked.",
        forms=("summary()",),
        arguments=(),
        example="L := 6*m\nq := 10*kN/m\nM_max = q*L^2/8\nreport(M_max)\nsummary()",
    ),
    CallHelp(
        name="plot",
        summary="Draw an expression against a variable over a range.",
        forms=("plot(expression, variable, lower, upper)",),
        arguments=(
            ("expression", "what to draw"),
            ("variable", "the horizontal variable"),
            ("lower", "the start of the range"),
            ("upper", "the end of the range"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\nplot(M(x), x, 0, L)",
    ),
    CallHelp(
        name="envelope",
        summary="Draw several expressions together with their upper and lower envelope.",
        forms=("envelope(expr_1, expr_2, variable, lower, upper)",),
        arguments=(
            ("expr_1, expr_2", "the responses to envelope"),
            ("variable", "the horizontal variable"),
            ("lower, upper", "the range"),
        ),
        example=(
            "L := 6*m\nq := 10*kN/m\n"
            "M1(x) = 1.2*q*x*(L-x)/2\nM2(x) = 1.4*q*x*(L-x)/2\n"
            "envelope(M1(x), M2(x), x, 0, L)"
        ),
    ),
    CallHelp(
        name="table",
        summary="Tabulate one or more expressions at evenly spaced stations.",
        forms=("table(expression, variable, lower, upper, steps)",),
        arguments=(
            ("expression", "what to tabulate"),
            ("variable", "the variable to step"),
            ("lower, upper", "the range"),
            ("steps", "how many intervals"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\ntable(M(x), x, 0, L, 4)",
    ),
    CallHelp(
        name="roots",
        summary="Where an expression crosses zero inside a domain.",
        forms=("roots(expression, variable, lower, upper)",),
        arguments=(
            ("expression", "the response"),
            ("variable", "the variable"),
            ("lower, upper", "the domain to search"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\nroots(M(x), x, 0, L)",
    ),
    CallHelp(
        name="extrema",
        summary="The maxima and minima of an expression inside a domain.",
        forms=("extrema(expression, variable, lower, upper)",),
        arguments=(
            ("expression", "the response"),
            ("variable", "the variable"),
            ("lower, upper", "the domain to search"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\nextrema(M(x), x, 0, L)",
    ),
    CallHelp(
        name="intersections",
        summary="Where two expressions cross inside a domain.",
        forms=("intersections(left, right, variable, lower, upper)",),
        arguments=(
            ("left, right", "the two responses"),
            ("variable", "the variable"),
            ("lower, upper", "the domain to search"),
        ),
        example=(
            "L := 6*m\nq := 10*kN/m\n"
            "M1(x) = q*x*(L-x)/2\nM2(x) = 10*kN*m\n"
            "intersections(M1(x), M2(x), x, 0, L)"
        ),
    ),
    CallHelp(
        name="governing",
        summary="Which of several responses is largest, over each stretch of the domain.",
        forms=("governing(expr_1, expr_2, variable, lower, upper)",),
        arguments=(
            ("expr_1, expr_2", "the responses to compare"),
            ("variable", "the variable"),
            ("lower, upper", "the domain"),
        ),
        example=(
            "L := 6*m\nqD := 8*kN/m\nqL := 12*kN/m\n"
            "M1(x) = 1.2*qD*x*(L-x)/2 + 1.6*qL*x*(L-x)/2\n"
            "M2(x) = 1.4*qD*x*(L-x)/2\n"
            "governing(M1(x), M2(x), x, 0, L)"
        ),
    ),
    CallHelp(
        name="piecewise",
        summary="A value that changes at a breakpoint.",
        forms=("piecewise(value_before, condition, value_after)",),
        arguments=(
            ("value_before", "the value while the condition holds"),
            ("condition", "one comparison, as in `x < L/2`"),
            ("value_after", "the value otherwise"),
        ),
        example="L := 6*m\nq := 10*kN/m\nw(x) = piecewise(q, x < L/2, 0*kN/m)\nnumeric(subs(w(x), x, 0*m))",
    ),
    CallHelp(
        name="simplify",
        summary="Simplify an expression, using whatever `assume` has stated.",
        forms=("simplify(expression)",),
        arguments=(("expression", "what to simplify"),),
        example="assume(L > 0)\na = sqrt(L^2)\nsimplify(a)",
    ),
    CallHelp(
        name="expand",
        summary="Multiply an expression out.",
        forms=("expand(expression)",),
        arguments=(("expression", "what to expand"),),
        example="p = expand((x + 2)*(x - 3))",
    ),
    CallHelp(
        name="factor",
        summary="Write an expression as a product of factors.",
        forms=("factor(expression)",),
        arguments=(("expression", "what to factor"),),
        example="p = factor(x^2 - x - 6)",
    ),
    CallHelp(
        name="abs",
        summary="The magnitude of an expression, without its sign.",
        forms=("abs(expression)",),
        arguments=(("expression", "the value"),),
        example="a = abs(-3)",
    ),
    CallHelp(
        name="min",
        summary="The smallest of several values, written in the order given.",
        forms=("min(a, b, ...)",),
        arguments=(("a, b, ...", "two or more values of one kind"),),
        example="L := 8*m\nb_w := 300*mm\nh_f := 120*mm\ns := 3*m\n"
        "b_eff = min(L/4, b_w + 16*h_f, s)\nnumeric(b_eff)",
    ),
    CallHelp(
        name="max",
        summary="The largest of several values, written in the order given.",
        forms=("max(a, b, ...)",),
        arguments=(("a, b, ...", "two or more values of one kind"),),
        example="V_A := 30*kN\nV_B := 45*kN\nV_max = max(V_B, V_A)\nnumeric(V_max)",
    ),
    CallHelp(
        name="interp",
        summary="A value read from a table, on the straight line between the two points around it.",
        forms=("interp(x, [x_1, x_2, ...], [y_1, y_2, ...])",),
        arguments=(
            ("x", "the point to read the table at, inside it"),
            ("[x_1, x_2, ...]", "the table's points, in increasing order"),
            ("[y_1, y_2, ...]", "the value at each point"),
        ),
        example="e_t := 0.003\nphi = interp(e_t, [0.002, 0.005], [0.65, 0.90])\nnumeric(phi)",
    ),
    _scalar("sqrt", "The square root.", "16"),
    _scalar("sin", "The sine of an angle.", "30*deg"),
    _scalar("cos", "The cosine of an angle.", "30*deg"),
    _scalar("tan", "The tangent of an angle.", "30*deg"),
    _scalar("asin", "The angle whose sine this is.", "0.5"),
    _scalar("acos", "The angle whose cosine this is.", "0.5"),
    _scalar("atan", "The angle whose tangent this is.", "1"),
    _scalar("exp", "The exponential.", "1"),
    _scalar("log", "The natural logarithm.", "1"),
    CallHelp(
        name="identity",
        summary="The identity matrix.",
        forms=("identity(size)",),
        arguments=(("size", "how many rows and columns"),),
        example="I3 = identity(3)",
    ),
    CallHelp(
        name="zeros",
        summary="A matrix of zeros.",
        forms=("zeros(rows, cols)",),
        arguments=(("rows", "how many rows"), ("cols", "how many columns")),
        example="Z = zeros(2, 3)",
    ),
    CallHelp(
        name="diag",
        summary="A diagonal matrix from the values given.",
        forms=("diag(v_1, v_2, ...)",),
        arguments=(("v_1, v_2, ...", "the diagonal entries"),),
        example="D = diag(1, 2, 3)",
    ),
    CallHelp(
        name="transpose",
        summary="Swap a matrix's rows and columns.",
        forms=("transpose(matrix)",),
        arguments=(("matrix", "the matrix"),),
        example="A = [1, 2; 3, 4]\nB = transpose(A)",
    ),
    CallHelp(
        name="det",
        summary="The determinant of a square matrix.",
        forms=("det(matrix)",),
        arguments=(("matrix", "a square matrix"),),
        example="A = [2, 0; 0, 4]\nd = det(A)",
    ),
    CallHelp(
        name="inv",
        summary="The inverse of a square matrix.",
        forms=("inv(matrix)",),
        arguments=(("matrix", "a square, invertible matrix"),),
        example="A = [2, 0; 0, 4]\nB = inv(A)",
    ),
    CallHelp(
        name="trace",
        summary="The sum of a square matrix's diagonal.",
        forms=("trace(matrix)",),
        arguments=(("matrix", "a square matrix"),),
        example="A = [2, 0; 0, 4]\nt = trace(A)",
    ),
    CallHelp(
        name="size",
        summary="A matrix's number of rows and columns.",
        forms=("size(matrix)",),
        arguments=(("matrix", "the matrix"),),
        example="A = [1, 2; 3, 4]\ns = size(A)",
    ),
    CallHelp(
        name="rank",
        summary="The rank of a matrix.",
        forms=("rank(matrix)",),
        arguments=(("matrix", "the matrix"),),
        example="A = [1, 2; 2, 4]\nr = rank(A)",
    ),
    CallHelp(
        name="rref",
        summary="The reduced row echelon form of a matrix.",
        forms=("rref(matrix)",),
        arguments=(("matrix", "the matrix"),),
        example="A = [1, 2; 3, 4]\nR = rref(A)",
    ),
    CallHelp(
        name="norm",
        summary="The norm of a matrix or vector.",
        forms=("norm(matrix)",),
        arguments=(("matrix", "the matrix or vector"),),
        example="v = [3; 4]\nn = norm(v)",
    ),
    CallHelp(
        name="eigenvals",
        summary="The eigenvalues of a square matrix, with their multiplicities.",
        forms=("eigenvals(matrix)",),
        arguments=(("matrix", "a square matrix"),),
        example="A = [2, 0; 0, 4]\ne = eigenvals(A)",
    ),
    CallHelp(
        name="eigenvects",
        summary="The eigenvectors of a square matrix.",
        forms=("eigenvects(matrix)",),
        arguments=(("matrix", "a square matrix"),),
        example="A = [2, 0; 0, 4]\nv = eigenvects(A)",
    ),
    CallHelp(
        name="dot",
        summary="The dot product of two vectors, a scalar.",
        forms=("dot(u, v)",),
        arguments=(("u, v", "two vectors of one length, written as rows or columns"),),
        example="u = [1; 2; 3]\nv = [4; 5; 6]\nd = dot(u, v)",
    ),
    CallHelp(
        name="cross",
        summary="The cross product of two vectors of length three, as the moment r × F.",
        forms=("cross(u, v)",),
        arguments=(("u, v", "two vectors of length 3; the result takes u's orientation"),),
        example="r = [2*m; 0*m; 1*m]\nF = [0*kN; 5*kN; 0*kN]\nM_O = cross(r, F)",
    ),
)

CATALOGUE: dict[str, CallHelp] = {
    entry.name: entry for entry in _STATEMENTS + _PLACING + _ENTRIES
}
