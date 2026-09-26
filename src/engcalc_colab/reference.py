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

The help is written in Spanish, as he asked on 2026-09-25 (*"Tradúcela al español"*): the
prose and the placeholders of each form. The names of the calls, their keywords and the
examples stay as the language writes them.
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
        forms=(f"{name}(expresión)",),
        arguments=(("expresión", "el valor al que se aplica"),),
        example=f"y = {name}({example_argument})",
    )


_STATEMENTS: tuple[CallHelp, ...] = (
    CallHelp(
        name=":=",
        kind="statement",
        summary="Da a un nombre su valor, un número con su unidad; una línea que lee una matriz se resuelve en números.",
        forms=("nombre := expresión", "d := solve(K, F)"),
        arguments=(
            ("nombre", "el nombre con que se guarda el valor"),
            ("expresión", "un valor con su unidad, o aritmética sobre valores ya dados; con una matriz, solve, inv, transpose, + - * y entradas como d[2,1]"),
        ),
        note=(
            "`=` define una fórmula y la conserva en símbolos; `:=` define un valor. "
            "numeric() pone los valores `:=` en una fórmula `=` y muestra la sustitución. "
            "Una línea := puede leer un nombre definido con `=`: toma su número con los "
            "valores dados hasta ahí, como D := [delta_ab; delta_ac]. "
            "`d := solve(K, F)` resuelve en números - resolver en símbolos una matriz de "
            "rigidez real no terminaría - y la memoria escribe la línea como se tipeó y "
            "luego sus números."
        ),
        example=(
            "L := 6*m\nq := 10*kN/m\nM = q*L^2/8\nnumeric(M)\n"
            "K = [2*kN/m, -1*kN/m; -1*kN/m, 1*kN/m]\nF = [0*kN; 10*kN]\nd := solve(K, F)"
        ),
    ),
    CallHelp(
        name="keep",
        kind="statement",
        summary="Define un valor que las fórmulas siguientes muestran por su nombre, no por lo que vale.",
        forms=("keep nombre = expresión",),
        arguments=(
            ("nombre", "el nombre que conservan las fórmulas siguientes, como lo llama la norma: f_cw, R_n, As_min, d"),
            ("expresión", "su definición, que se muestra una vez, en su propia fila"),
        ),
        note=(
            "Sin keep, una fórmula que usa el nombre se escribe con el nombre reemplazado "
            "por su definición. Con f_cw = 0.85*fc y luego C = f_cw*b*d, la memoria dice "
            "C = 0.85 b d fc. Con keep f_cw = 0.85*fc dice C = f_cw b d - la fórmula de "
            "la norma - y la sustitución pone el valor propio de f_cw (178.50 kgf/cm2). "
            "Úsalo en todo valor intermedio que la norma o tu razonamiento nombran; un dato "
            "(fc := 210*kgf/cm^2) no lo necesita."
        ),
        example=(
            "fc := 210*kgf/cm^2\nb := 30*cm\nd := 44*cm\n"
            "keep f_cw = 0.85*fc\nC = f_cw*b*d\nnumeric(C)"
        ),
    ),
    CallHelp(
        name="if",
        kind="statement",
        summary="Decide qué líneas se calculan: solo corre la rama cuya condición se cumple, y la memoria dice por qué.",
        forms=("% if condición:", "% elif condición:", "% else:", "% end"),
        arguments=(
            ("condición", "una comparación entre valores con unidades, como Vu > phi_v*V_c; se unen con and y or"),
        ),
        note=(
            "Una línea que empieza con % es de control, escrita como en Python, y % end "
            "cierra el bloque. La rama elegida abre con la condición en números - Como "
            "Vu = 7920.00 kgf > φ_v V_c = 7603.63 kgf: - que es lo que un revisor comprueba; "
            "la rama que no se cumple no se calcula ni se escribe. Los bloques se anidan."
        ),
        example=(
            "fc := 210*kgf/cm^2\nb := 30*cm\nd := 44*cm\nphi_v := 0.75\n"
            "V_c := 0.53*sqrt(fc*kgf/cm^2)*b*d\nVu := 7920*kgf\n"
            "% if Vu > phi_v*V_c:\nV_s = Vu/phi_v - V_c\nnumeric(V_s)\n"
            "% else:\nV_s := 0*kgf\n% end"
        ),
    ),
    CallHelp(
        name="for",
        kind="statement",
        summary="Repite líneas de la hoja una vez por cada valor; la memoria muestra las filas de cada vuelta, como escritas a mano.",
        forms=("% for variable in lista:", "% end", "% n = 0"),
        arguments=(
            ("variable", "el nombre que toma cada valor; varios a la vez con i, (a, b)"),
            ("lista", "una lista, range(...) o enumerate(..., start=1); puede seguir en las líneas % siguientes"),
        ),
        note=(
            "Las líneas % son Python y no se escriben en la memoria. {...} pone un valor de "
            "ellas en una línea de la hoja: M_U{i} se escribe M_U1, M({a}, {b}) se escribe "
            "M(1.4, 0). Un nombre de la hoja se escribe como nombre: con [F_1, F_2], {F} es "
            "F_1 y luego F_2. % n = 0 y % n += 1 guardan un contador. Dentro puede ir un % if."
        ),
        example=(
            "q_D := 18*kN/m\nq_L := 12*kN/m\nL := 6*m\n"
            "M(a, b) = (a*q_D + b*q_L)*L^2/8\n"
            "% for i, (a, b) in enumerate([(1.4, 0), (1.2, 1.6)], start=1):\n"
            "M_U{i} := M({a}, {b})\n% end"
        ),
    ),
    CallHelp(
        name="while",
        kind="statement",
        summary="Repite líneas mientras una condición se cumpla; la memoria muestra solo la última vuelta y cuántas hubo.",
        forms=("% while condición:", "% end"),
        arguments=(
            ("condición", "una comparación entre valores de la hoja, como abs(f(c)) > 0.001*kgf*cm; se une con and y or"),
        ),
        note=(
            "Cada vuelta se calcula pero no se escribe. Al terminar, la memoria dice En 4 "
            "iteraciones: y la condición en números, que ya no se cumple (así se ve que "
            "convergió), y luego las filas de la última vuelta. Si a las 1000 vueltas la "
            "condición sigue cumpliéndose, la celda se detiene con un mensaje: no converge "
            "desde ese valor inicial."
        ),
        example=(
            "x := 1*m\n"
            "% while abs(x^2 - 2*m^2) > 1e-6*m^2:\n"
            "x := (x + 2*m^2/x)/2\n% end"
        ),
    ),
    CallHelp(
        name="case",
        kind="statement",
        summary="Nombra la respuesta de un caso de carga, como función de la coordenada a lo largo del elemento.",
        forms=("case nombre = expresión",),
        arguments=(
            ("nombre", "el caso, como D, Lv o EQ"),
            ("expresión", "la respuesta que da, como M_D(x)"),
        ),
        note=(
            "Un combo suma casos con sus factores. La coordenada no se declara, se "
            "encuentra: es el único nombre que queda cuando todos los demás tienen valor."
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
        summary="Combina casos de carga con los factores de la norma; la combinación es luego una función, U1(x).",
        forms=("combo nombre = factor*caso + ...",),
        arguments=(
            ("nombre", "la combinación, como U1"),
            ("factor*caso + ...", "cada caso por su factor, como 1.2*D + 1.6*Lv"),
        ),
        note=(
            "Se escribe con sus factores, para que un revisor la contraste con la norma "
            "sin rehacer la aritmética. Se usa como función: U1(L/2), "
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
        summary="Coloca una imagen - un archivo o una URL - como Figura numerada, incrustada en el cuaderno.",
        forms=('image("archivo.png")', 'image("archivo.png", "leyenda", width=12*cm)'),
        arguments=(
            ("archivo", "entre comillas: una ruta desde donde corre el cuaderno - en Colab /content, o /content/drive/MyDrive/... con Drive montado - o una URL http(s); png, jpg, gif, svg o webp"),
            ("leyenda", "opcional, entre comillas; puede llevar $...$"),
            ("width", "opcional, una longitud, como 12*cm"),
        ),
        note="Las figuras se numeran solas, image y frame_plot por igual; una celda que se vuelve a correr conserva sus números y %eng_reset vuelve a empezar en 1.",
        example='image("portico.png", "Geometría del pórtico", width=9*cm)',
    ),
    CallHelp(
        name="member",
        summary="Declara un elemento de un pórtico con lo que la hoja ya calculó, para frame_plot; no escribe nada en la memoria.",
        forms=(
            'member("nombre", start=[x_1, y_1], end=[x_2, y_2], forces=f)',
            'member("nombre", start=..., end=..., forces=f, displacements=u, EI=E*I, load=w)',
            'member("nombre", start=..., end=..., forces=f, load=[w_1, w_2], point=[P, a])',
        ),
        arguments=(
            ("nombre", "entre comillas; declararlo otra vez lo reemplaza"),
            ("start, end", "sus extremos, dos longitudes cada uno; x' va de start a end, y' un cuarto de vuelta antihorario desde x'"),
            ("forces", "las seis fuerzas de extremo en ejes locales, que actúan sobre el elemento, [N_i; V_i; M_i; N_j; V_j; M_j] - como las da k*T*D + f_0"),
            ("displacements", "los seis desplazamientos de extremo en ejes locales, [u_i; v_i; θ_i; u_j; v_j; θ_j] - T*D; para la deformada"),
            ("EI", "su rigidez a flexión; la deformada de un elemento cargado la necesita"),
            ("load", "una carga hacia -y': w uniforme, o [w_1, w_2] lineal de start a end"),
            ("point", "[P, a], una carga P hacia -y' a una distancia a de start; varias van en filas, [P_1, a_1; P_2, a_2]"),
        ),
        note=(
            "No se vuelve a resolver nada. frame_plot aplica equilibrio a cada elemento desde "
            "su inicio: N(s) = -N_i, V(s) = V_i menos la carga hasta s, M(s) = -M_i + V_i s "
            "menos el momento de esa carga. La carga en un nudo se deduce de las fuerzas de "
            "extremo que llegan a él; un apoyo es un nudo que los desplazamientos mantienen quieto."
        ),
        example=(
            "L := 6*m\nP := 30*kN\nf := [0*kN; 20*kN; 0*kN*m; 0*kN; 10*kN; 0*kN*m]\n"
            'member("V", start=[0*m, 0*m], end=[L, 0*m], forces=f, point=[P, 2*m])\n'
            'frame_plot(M, "Momento flector")'
        ),
    ),
    CallHelp(
        name="frame_plot",
        summary="Dibuja M, V, N o la deformada sobre todos los elementos declarados, como Figura numerada.",
        forms=('frame_plot(M, "leyenda")', "frame_plot(V)", "frame_plot(N)", 'frame_plot(deformed, "leyenda", scale=150)'),
        arguments=(
            ("M, V, N, deformed", "el diagrama; M se dibuja del lado traccionado y es positivo si tracciona la fibra interior, cada elemento leído como una viga vista desde dentro del pórtico"),
            ("leyenda", "opcional, entre comillas; la figura dice Figura n. leyenda"),
            ("scale", "solo para deformed: cuántas veces se amplifican los desplazamientos; se elige solo si se omite"),
        ),
        note=(
            "Los valores llevan su signo, en recuadros, en la unidad de la memoria; el "
            "máximo del momento se marca donde el cortante pasa por cero. La deformada sigue "
            "los desplazamientos de extremo con las funciones de forma del elemento y suma la "
            "flecha que su carga produce con ambos extremos empotrados."
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
        summary="Evalúa una expresión con los valores que la hoja ha dado, y muestra la sustitución.",
        forms=("numeric(expresión)", "numeric(expresión, unidad)"),
        arguments=(
            ("expresión", "lo que se evalúa; cada nombre en ella necesita un valor `:=`"),
            ("unidad", "opcional, la unidad en que se muestra el resultado, como `mm` o `kN*m`"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM_max = q*L^2/8\nnumeric(M_max, kN*m)",
    ),
    CallHelp(
        name="result",
        summary="Muestra la fórmula y su valor final, sin la etapa de sustitución.",
        forms=("result(expresión)", "result(expresión, unidad)"),
        arguments=(
            ("expresión", "lo que se evalúa"),
            ("unidad", "opcional, la unidad en que se muestra el resultado"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM_max = q*L^2/8\nresult(M_max, kN*m)",
    ),
    CallHelp(
        name="integrate",
        summary="Integra una expresión: dos argumentos para la primitiva, cuatro entre límites.",
        forms=(
            "integrate(expresión, variable)",
            "integrate(expresión, variable, inferior, superior)",
        ),
        arguments=(
            ("expresión", "lo que se integra"),
            ("variable", "la variable de integración, como `x`"),
            ("inferior", "el límite inferior; se omite, con `superior`, para la primitiva"),
            ("superior", "el límite superior"),
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
        summary="Deriva una expresión respecto de una variable.",
        forms=("diff(expresión, variable)",),
        arguments=(
            ("expresión", "lo que se deriva"),
            ("variable", "la variable respecto de la cual se deriva"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\nV(x) = diff(M(x), x)",
    ),
    CallHelp(
        name="solve",
        summary="Resuelve una ecuación, un sistema o una inecuación.",
        forms=(
            "solve(ecuación, incógnita)",
            "solve(ec_1, ..., ec_n, x_1, ..., x_n)",
            "solve(ecuación, incógnita, inferior, superior)",
            "solve(inecuación, variable, inferior, superior)",
            "solve(matriz, vector)",
        ),
        arguments=(
            ("ecuación", "escrita `eq(izquierda, derecha)`, o `izquierda = derecha` dentro de la llamada"),
            ("incógnita", "el nombre que se despeja"),
            ("ec_1 ... ec_n", "n ecuaciones, seguidas de exactamente n incógnitas"),
            ("inecuación", "una comparación como `M(x) > 20*kN*m`"),
            ("inferior, superior", "el dominio; de ahí toma la variable su unidad. Con una ecuación, entrega la única raíz que hay entre ellos"),
        ),
        note=(
            "Con un intervalo, solve entrega una sola raíz: la que hay entre inferior y "
            "superior, aunque la ecuación no tenga forma cerrada. Sirve con := : "
            "c := solve(eq(b*c^2/2, n*A_s*(d - c)), c, 0*cm, d) escribe la ecuación y luego "
            "c = 10.55 cm. Si en el intervalo no hay raíz, o hay más de una, lo dice con sus "
            "valores."
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
        summary="Arma una ecuación con sus dos lados, para `solve`.",
        forms=("eq(izquierda, derecha)",),
        arguments=(("izquierda", "el lado izquierdo"), ("derecha", "el lado derecho")),
        example="L := 6*m\nq := 10*kN/m\neqFy = eq(R_A + R_B, q*L)",
    ),
    CallHelp(
        name="subs",
        summary="Reemplaza una variable por un valor en una expresión.",
        forms=("subs(expresión, variable, valor)", "subs(expresión, v1, x1, v2, x2, ...)"),
        arguments=(
            ("expresión", "donde se sustituye"),
            ("variable", "el nombre que se reemplaza"),
            ("valor", "lo que se pone en su lugar"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\nnumeric(subs(M(x), x, L/2))",
    ),
    CallHelp(
        name="sum",
        summary="Suma una expresión sobre un índice entre dos límites.",
        forms=("sum(expresión, índice, inferior, superior)",),
        arguments=(
            ("expresión", "el término, escrito en función del índice"),
            ("índice", "el índice de la suma, como `i`"),
            ("inferior", "el primer valor del índice"),
            ("superior", "el último valor del índice"),
        ),
        example="n := 5\nP := 10*kN\nS = sum(P*i, i, 1, n)\nnumeric(S)",
    ),
    CallHelp(
        name="macaulay",
        summary="Un paréntesis de Macaulay, nulo antes de su desplazamiento. Se suele escribir `<x-a>^n`.",
        forms=("macaulay(desplazada, orden)", "<x-a>^n"),
        arguments=(
            ("desplazada", "la coordenada desplazada, como `x - a`"),
            ("orden", "la potencia; 1 para una carga puntual en una ley de momentos"),
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
        summary="Declara lo que se sabe de un símbolo, antes de usarlo por primera vez.",
        forms=("assume(símbolo > 0)", "assume(a > 0, b >= 0, ...)"),
        arguments=(
            ("símbolo > 0", "una comparación con cero: `>`, `>=`, `<` o `<=`"),
        ),
        example="assume(Lk > 0)\nf(Lk) = Lk^2\nsolve(eq(f(Lk), 4), Lk)",
    ),
    CallHelp(
        name="report",
        summary="Muestra un valor donde se escribe y lo marca para el resumen.",
        forms=("report(nombre)",),
        arguments=(("nombre", "un nombre que la hoja ya definió"),),
        example="L := 6*m\nq := 10*kN/m\nM_max = q*L^2/8\nreport(M_max)",
    ),
    CallHelp(
        name="summary",
        summary="Escribe cada valor marcado con `report`, en el orden en que se marcó.",
        forms=("summary()",),
        arguments=(),
        example="L := 6*m\nq := 10*kN/m\nM_max = q*L^2/8\nreport(M_max)\nsummary()",
    ),
    CallHelp(
        name="plot",
        summary="Grafica una expresión contra una variable en un intervalo.",
        forms=("plot(expresión, variable, inferior, superior)",),
        arguments=(
            ("expresión", "lo que se grafica"),
            ("variable", "la variable horizontal"),
            ("inferior", "el inicio del intervalo"),
            ("superior", "el final del intervalo"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\nplot(M(x), x, 0, L)",
    ),
    CallHelp(
        name="envelope",
        summary="Grafica varias expresiones juntas con su envolvente superior e inferior.",
        forms=("envelope(expr_1, expr_2, variable, inferior, superior)",),
        arguments=(
            ("expr_1, expr_2", "las respuestas que se envuelven"),
            ("variable", "la variable horizontal"),
            ("inferior, superior", "el intervalo"),
        ),
        example=(
            "L := 6*m\nq := 10*kN/m\n"
            "M1(x) = 1.2*q*x*(L-x)/2\nM2(x) = 1.4*q*x*(L-x)/2\n"
            "envelope(M1(x), M2(x), x, 0, L)"
        ),
    ),
    CallHelp(
        name="table",
        summary="Tabula una o más expresiones en estaciones equiespaciadas.",
        forms=("table(expresión, variable, inferior, superior, estaciones)",),
        arguments=(
            ("expresión", "lo que se tabula"),
            ("variable", "la variable que avanza"),
            ("inferior, superior", "el intervalo"),
            ("estaciones", "cuántas filas, contando ambos extremos: 11 da x = 0, L/10, ..., L"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\ntable(M(x), x, 0, L, 4)",
    ),
    CallHelp(
        name="roots",
        summary="Dónde una expresión pasa por cero dentro de un dominio.",
        forms=("roots(expresión, variable, inferior, superior)",),
        arguments=(
            ("expresión", "la respuesta"),
            ("variable", "la variable"),
            ("inferior, superior", "el dominio donde se busca"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\nroots(M(x), x, 0, L)",
    ),
    CallHelp(
        name="extrema",
        summary="Los máximos y mínimos de una expresión dentro de un dominio.",
        forms=("extrema(expresión, variable, inferior, superior)",),
        arguments=(
            ("expresión", "la respuesta"),
            ("variable", "la variable"),
            ("inferior, superior", "el dominio donde se busca"),
        ),
        example="L := 6*m\nq := 10*kN/m\nM(x) = q*x*(L-x)/2\nextrema(M(x), x, 0, L)",
    ),
    CallHelp(
        name="intersections",
        summary="Dónde se cruzan dos expresiones dentro de un dominio.",
        forms=("intersections(izquierda, derecha, variable, inferior, superior)",),
        arguments=(
            ("izquierda, derecha", "las dos respuestas"),
            ("variable", "la variable"),
            ("inferior, superior", "el dominio donde se busca"),
        ),
        example=(
            "L := 6*m\nq := 10*kN/m\n"
            "M1(x) = q*x*(L-x)/2\nM2(x) = 10*kN*m\n"
            "intersections(M1(x), M2(x), x, 0, L)"
        ),
    ),
    CallHelp(
        name="governing",
        summary="Cuál de varias respuestas es la mayor, en cada tramo del dominio.",
        forms=("governing(expr_1, expr_2, variable, inferior, superior)",),
        arguments=(
            ("expr_1, expr_2", "las respuestas que se comparan"),
            ("variable", "la variable"),
            ("inferior, superior", "el dominio"),
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
        summary="Un valor que cambia en un punto de quiebre.",
        forms=("piecewise(valor_antes, condición, valor_después)",),
        arguments=(
            ("valor_antes", "el valor mientras se cumple la condición"),
            ("condición", "una comparación, como `x < L/2`"),
            ("valor_después", "el valor en otro caso"),
        ),
        example="L := 6*m\nq := 10*kN/m\nw(x) = piecewise(q, x < L/2, 0*kN/m)\nnumeric(subs(w(x), x, 0*m))",
    ),
    CallHelp(
        name="simplify",
        summary="Simplifica una expresión, con lo que `assume` haya declarado.",
        forms=("simplify(expresión)",),
        arguments=(("expresión", "lo que se simplifica"),),
        example="assume(L > 0)\na = sqrt(L^2)\nsimplify(a)",
    ),
    CallHelp(
        name="expand",
        summary="Desarrolla una expresión, multiplicando sus factores.",
        forms=("expand(expresión)",),
        arguments=(("expresión", "lo que se desarrolla"),),
        example="p = expand((x + 2)*(x - 3))",
    ),
    CallHelp(
        name="factor",
        summary="Escribe una expresión como producto de factores.",
        forms=("factor(expresión)",),
        arguments=(("expresión", "lo que se factoriza"),),
        example="p = factor(x^2 - x - 6)",
    ),
    CallHelp(
        name="abs",
        summary="El valor absoluto de una expresión, sin su signo.",
        forms=("abs(expresión)",),
        arguments=(("expresión", "el valor"),),
        example="a = abs(-3)",
    ),
    CallHelp(
        name="min",
        summary="El menor de varios valores, escritos en el orden dado.",
        forms=("min(a, b, ...)",),
        arguments=(("a, b, ...", "dos o más valores de una misma clase"),),
        example="L := 8*m\nb_w := 300*mm\nh_f := 120*mm\ns := 3*m\n"
        "b_eff = min(L/4, b_w + 16*h_f, s)\nnumeric(b_eff)",
    ),
    CallHelp(
        name="max",
        summary="El mayor de varios valores, escritos en el orden dado.",
        forms=("max(a, b, ...)",),
        arguments=(("a, b, ...", "dos o más valores de una misma clase"),),
        example="V_A := 30*kN\nV_B := 45*kN\nV_max = max(V_B, V_A)\nnumeric(V_max)",
    ),
    CallHelp(
        name="interp",
        summary="Un valor leído de una tabla, sobre la recta entre los dos puntos que lo rodean.",
        forms=("interp(x, [x_1, x_2, ...], [y_1, y_2, ...])",),
        arguments=(
            ("x", "el punto donde se lee la tabla, dentro de ella"),
            ("[x_1, x_2, ...]", "los puntos de la tabla, en orden creciente"),
            ("[y_1, y_2, ...]", "el valor en cada punto"),
        ),
        example="e_t := 0.003\nphi = interp(e_t, [0.002, 0.005], [0.65, 0.90])\nnumeric(phi)",
    ),
    _scalar("sqrt", "La raíz cuadrada.", "16"),
    _scalar("sin", "El seno de un ángulo.", "30*deg"),
    _scalar("cos", "El coseno de un ángulo.", "30*deg"),
    _scalar("tan", "La tangente de un ángulo.", "30*deg"),
    _scalar("asin", "El ángulo cuyo seno es este.", "0.5"),
    _scalar("acos", "El ángulo cuyo coseno es este.", "0.5"),
    _scalar("atan", "El ángulo cuya tangente es esta.", "1"),
    _scalar("exp", "La exponencial.", "1"),
    _scalar("log", "El logaritmo natural.", "1"),
    CallHelp(
        name="identity",
        summary="La matriz identidad.",
        forms=("identity(tamaño)",),
        arguments=(("tamaño", "cuántas filas y columnas"),),
        example="I3 = identity(3)",
    ),
    CallHelp(
        name="zeros",
        summary="Una matriz de ceros.",
        forms=("zeros(filas, columnas)",),
        arguments=(("filas", "cuántas filas"), ("columnas", "cuántas columnas")),
        example="Z = zeros(2, 3)",
    ),
    CallHelp(
        name="diag",
        summary="Una matriz diagonal con los valores dados.",
        forms=("diag(v_1, v_2, ...)",),
        arguments=(("v_1, v_2, ...", "las entradas de la diagonal"),),
        example="D = diag(1, 2, 3)",
    ),
    CallHelp(
        name="transpose",
        summary="Intercambia las filas y columnas de una matriz.",
        forms=("transpose(matriz)",),
        arguments=(("matriz", "la matriz"),),
        example="A = [1, 2; 3, 4]\nB = transpose(A)",
    ),
    CallHelp(
        name="det",
        summary="El determinante de una matriz cuadrada.",
        forms=("det(matriz)",),
        arguments=(("matriz", "una matriz cuadrada"),),
        example="A = [2, 0; 0, 4]\nd = det(A)",
    ),
    CallHelp(
        name="inv",
        summary="La inversa de una matriz cuadrada.",
        forms=("inv(matriz)",),
        arguments=(("matriz", "una matriz cuadrada e invertible"),),
        example="A = [2, 0; 0, 4]\nB = inv(A)",
    ),
    CallHelp(
        name="trace",
        summary="La suma de la diagonal de una matriz cuadrada.",
        forms=("trace(matriz)",),
        arguments=(("matriz", "una matriz cuadrada"),),
        example="A = [2, 0; 0, 4]\nt = trace(A)",
    ),
    CallHelp(
        name="size",
        summary="El número de filas y columnas de una matriz.",
        forms=("size(matriz)",),
        arguments=(("matriz", "la matriz"),),
        example="A = [1, 2; 3, 4]\ns = size(A)",
    ),
    CallHelp(
        name="rank",
        summary="El rango de una matriz.",
        forms=("rank(matriz)",),
        arguments=(("matriz", "la matriz"),),
        example="A = [1, 2; 2, 4]\nr = rank(A)",
    ),
    CallHelp(
        name="rref",
        summary="La forma escalonada reducida por filas de una matriz.",
        forms=("rref(matriz)",),
        arguments=(("matriz", "la matriz"),),
        example="A = [1, 2; 3, 4]\nR = rref(A)",
    ),
    CallHelp(
        name="norm",
        summary="La norma de una matriz o de un vector.",
        forms=("norm(matriz)",),
        arguments=(("matriz", "la matriz o el vector"),),
        example="v = [3; 4]\nn = norm(v)",
    ),
    CallHelp(
        name="eigenvals",
        summary="Los valores propios de una matriz cuadrada, con sus multiplicidades.",
        forms=("eigenvals(matriz)",),
        arguments=(("matriz", "una matriz cuadrada"),),
        example="A = [2, 0; 0, 4]\ne = eigenvals(A)",
    ),
    CallHelp(
        name="eigenvects",
        summary="Los vectores propios de una matriz cuadrada.",
        forms=("eigenvects(matriz)",),
        arguments=(("matriz", "una matriz cuadrada"),),
        example="A = [2, 0; 0, 4]\nv = eigenvects(A)",
    ),
    CallHelp(
        name="dot",
        summary="El producto escalar de dos vectores, un escalar.",
        forms=("dot(u, v)",),
        arguments=(("u, v", "dos vectores de igual largo, escritos como filas o columnas"),),
        example="u = [1; 2; 3]\nv = [4; 5; 6]\nd = dot(u, v)",
    ),
    CallHelp(
        name="cross",
        summary="El producto vectorial de dos vectores de largo tres, como el momento r × F.",
        forms=("cross(u, v)",),
        arguments=(("u, v", "dos vectores de largo 3; el resultado toma la orientación de u"),),
        example="r = [2*m; 0*m; 1*m]\nF = [0*kN; 5*kN; 0*kN]\nM_O = cross(r, F)",
    ),
)

CATALOGUE: dict[str, CallHelp] = {
    entry.name: entry for entry in _STATEMENTS + _PLACING + _ENTRIES
}
