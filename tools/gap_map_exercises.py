"""Real engineering exercises, written the way an engineer would write them.

Deliberately NOT adapted to what EngCalc currently accepts. Each line is executed
against main and the first failure of each line is recorded verbatim. The point is
the gap map, so a line that breaks is data, not something to work around.
"""

EXERCISES = [

("E1 Estatica - reacciones de viga simplemente apoyada", "estatica", """
L := 6*m
q := 10*kN/m
eqFy = eq(R_A + R_B, q*L)
eqMA = eq(R_B*L, q*L*L/2)
solve(eqFy, eqMA, R_A, R_B)
"""),

("E2 Estatica - viga con carga puntual y distribuida", "estatica", """
L := 8*m
P := 40*kN
a := 3*m
q := 12*kN/m
eqFy = eq(R_A + R_B, P + q*L)
eqMA = eq(R_B*L, P*a + q*L*L/2)
solve(eqFy, eqMA, R_A, R_B)
"""),

("E3 Estatica - armadura, metodo de los nudos", "estatica", """
P := 20*kN
theta := 30*deg
eq1 = eq(F_AB*cos(theta) + F_AC, 0)
eq2 = eq(F_AB*sin(theta) - P, 0)
solve(eq1, eq2, F_AB, F_AC)
"""),

("E4 MecMat - curva elastica por doble integracion", "mecmat", """
L := 6*m
q := 10*kN/m
E := 200*GPa
I := 80e6*mm**4
R_A = q*L/2
V(x) = R_A - q*x
M(x) = integral(V(x), x, 0, x)
theta(x) = integrate(M(x)/(E*I), x) + C1
v(x) = integrate(theta(x), x) + C2
bc1 = eq(subs(v(x), x, 0), 0)
bc2 = eq(subs(v(x), x, L), 0)
solve(bc1, bc2, C1, C2)
numeric(subs(v(x), x, L/2))
"""),

("E5 MecMat - flecha maxima y verificacion", "mecmat", """
L := 6*m
q := 10*kN/m
E := 200*GPa
I := 80e6*mm**4
d_max = 5*q*L^4/(384*E*I)
numeric(d_max)
d_adm = L/300
numeric(d_adm)
check(d_max <= d_adm)
"""),

("E6 MecMat - diagrama con carga puntual, Macaulay", "mecmat", """
L := 8*m
P := 40*kN
a := 3*m
R_A = P*(L-a)/L
M(x) = R_A*x - P*<x-a>^1
plot(M(x), x, 0, L)
"""),

("E7 MecMat - propiedades de seccion compuesta", "secciones", """
b1 := 300*mm
h1 := 100*mm
b2 := 100*mm
h2 := 400*mm
A1 = b1*h1
A2 = b2*h2
y1 := 450*mm
y2 := 200*mm
y_bar = (A1*y1 + A2*y2)/(A1 + A2)
numeric(y_bar)
I1 = b1*h1^3/12 + A1*(y1 - y_bar)^2
I2 = b2*h2^3/12 + A2*(y2 - y_bar)^2
I_total = I1 + I2
numeric(I_total)
"""),

("E8 MecMat - transformacion de esfuerzos", "esfuerzos", """
sx := 80*MPa
sy := 20*MPa
txy := 30*MPa
s_prom = (sx + sy)/2
R = sqrt(((sx - sy)/2)^2 + txy^2)
s1 = s_prom + R
s2 = s_prom - R
numeric(s1)
numeric(s2)
theta_p = atan(2*txy/(sx - sy))/2
numeric(theta_p, deg)
"""),

("E9 Estructuras - viga apuntalada por flexibilidad", "estructuras", """
L := 6*m
q := 20*kN/m
E := 200*GPa
I := 120e6*mm**4
M_0(x) = -q*x^2/2
M_1(x) = x
D_B0 = integral(M_0(x)*M_1(x)/(E*I), x, 0, L)
f_11 = integral(M_1(x)^2/(E*I), x, 0, L)
V_B = solve(eq(D_B0 + V_B*f_11, 0*m), V_B)
numeric(V_B)
"""),

("E10 Estructuras - combinaciones de carga", "estructuras", """
L := 6*m
qD := 8*kN/m
qL := 12*kN/m
M_D(x) = qD*x*(L-x)/2
M_L(x) = qL*x*(L-x)/2
case D = M_D(x)
case L = M_L(x)
combo U1 = 1.2*D + 1.6*L
plot(M_U1(x), x, 0, L)
"""),

("E11 Estructuras - envolvente gobernante", "estructuras", """
L := 6*m
qD := 8*kN/m
qL := 12*kN/m
M_U1(x) = 1.2*qD*x*(L-x)/2 + 1.6*qL*x*(L-x)/2
M_U2(x) = 1.4*qD*x*(L-x)/2
envelope(M_U1(x), M_U2(x), x, 0, L)
governing(M_U1(x), M_U2(x), x, 0, L)
"""),

("E12 Diseno - verificacion a flexion", "diseno", """
phi := 0.9
Mn := 161*kN*m
Mu := 121*kN*m
phi_Mn = phi*Mn
numeric(phi_Mn)
check(phi_Mn >= Mu)
DC = Mu/phi_Mn
numeric(DC)
"""),

("E13 Diseno - dimensionamiento por flecha", "diseno", """
L := 6*m
q := 10*kN/m
E := 200*GPa
d_adm = L/300
I_req = solve(eq(5*q*L^4/(384*E*I), d_adm), I)
numeric(I_req)
"""),

("E14 Diseno - pandeo de Euler, despejar", "diseno", """
E := 200*GPa
I := 40e6*mm**4
K := 1.0
assume(Lk > 0)
P_cr(Lk) = pi^2*E*I/(K*Lk)^2
L_max = solve(eq(P_cr(Lk), 500*kN), Lk)
numeric(L_max)
"""),

("E15 General - inecuacion, zona de momento positivo", "general", """
L := 6*m
q := 10*kN/m
M(x) = q*x*(L-x)/2
solve(M(x) > 20*kN*m, x, 0, L)
"""),

("E16 General - assumptions y simplificacion", "general", """
assume(L > 0, E > 0, I > 0)
a = sqrt(L^2)
simplify(a)
"""),

("E17 General - sumatoria evaluada de cargas", "general", """
n := 5
P := 10*kN
S = sum(P*i, i, 1, n)
numeric(S)
"""),

("E18 General - resultados y resumen de memoria", "general", """
L := 6*m
q := 10*kN/m
M_max = q*L^2/8
numeric(M_max)
report(M_max)
summary()
"""),
]
