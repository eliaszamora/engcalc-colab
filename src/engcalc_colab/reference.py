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
)

CATALOGUE: dict[str, CallHelp] = {entry.name: entry for entry in _ENTRIES}
