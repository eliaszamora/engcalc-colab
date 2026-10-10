<!-- Kept current release by release: mark a row FIXED (with the version) when it ships. -->

**Status after 0.47.1 (2026-10-10):** fixed in 0.47.1 - A1, A2, A3 (`2*3[m]`; `1e3[mm]` still
`1000.0[mm]`), A5, A6, A7, C10e, C3b, C2h, C8d, N1, N2 (`kip*ft + kip*ft` reading in SymPy's
order is left).

**Status after 0.48.0 (2026-10-10):** fixed in 0.48.0 - B10 (`km`, `lbf`, `lb` as a force,
`percent`), C9k (kip palette), C3e/C3e2 (named lists, ranges and names on `:=`), C3f (1x1 plus a
number), C2b (matrix functions on `:=`), C10b (`% break`), C3k (`{i}` in loop text), C10a
(`argmin`/`argmax`), C3d (`rank` on `:=`), C4a (`lam` written λ, `lambda` says what to write),
C5l (`numeric` of a matrix names the missing value). In progress on `fix/0.48.1`: C2j (`cos(45°)`)
and angle vectors in degrees.
Decided as the page's rules, not defects: C4k/C6c/C8i (two decimals; `%eng_config precision=`
changes it), and D1-D23 below.

# EngCalc open findings - inventory against `main` 9b09b02 (0.47.0)

Run 2026-10-09 on the repository's `src` with SymPy 1.14, no palette unless noted.
Every row was run; the repro sheets lived in a session scratchpad and are not kept - the short repro in each row reruns it.
Line numbers are `docs/project-context/CURRENT.md` at 9b09b02. Duplicates are merged into one id
(the other sources listed in "source").

Status: STILL / FIXED / UNCLEAR. Severity (STILL only): WRONG, CRASH (internal text on the page),
REFUSED, HANG/SLOW, MISSING, PRESENTATION, MESSAGE. Realism: H = an engineer's ordinary sheet hits it,
M = a book/matrix sheet hits it, L = constructed or rare.

## STILL

| id | source | finding | repro (short) | status | sev | real | notes |
|---|---|---|---|---|---|---|---|
| N1 | ch3 L1985 (table), found here | a `table` whose response is an expression (not a call) heads its column with the raw source; with bracket units the internal `__u_m` reaches the page | `r = 3[kN]/(1[kN/m]); x := 1[m]; table(r*y/x, y, 0[m], 1[m], 3)` -> header `\text{3*__u_m*y/x}`; `table(2*y, y, 0, 1, 3)` -> `\text{2*y}` | STILL | CRASH | M | the 1000x unit error of 3.2 did NOT reproduce (values right); the header is the defect |
| B6 | L1113 | `roots` of a cubic in symbols is slow and refuses | `roots(a*x^3 + b*x^2 + c*x - e, x, 0, 10)` | STILL | HANG/SLOW | L | 44 s, then "characteristic numerical fallback could not validate a solution set" |
| N6h | L2500-2501 | `extrema` hangs on `cos x + 1/sin x` [0.5,2.5], `1/sin(x²)` [1,2], `sin x + 1/cos(x/1000)` [0,3000] | `extrema(cos(x) + 1/sin(x), x, 0.5, 2.5)` (also N6e, N6f) | STILL | HANG/SLOW | L | all three > 100 s (killed by the harness timeout) |
| C2b | L1935, L2092 (ch4) | a matrix-valued function call refused on a `:=` line | `k := 1000[kN/m]; g(k) = [k, -k; -k, k]; u := [1[mm]; 2[mm]]; f := g(k)*u` | STILL | REFUSED | M | "numeric evaluation does not support symbolic type 'ImmutableDenseMatrix'" |
| C3d | L1988 | `rank` on a `:=` line refused, with a wrong hint | `K := [2,-1,0;-1,2,-1;0,-1,1]*1000[kN/m]; r := rank(K)` | STILL | REFUSED | L | hint "take one of its entries, such as d[1,1]"; `det` was fixed in 0.45.6 |
| C3e | L1989, L2181 (0.45.0 left) | a named index list refused on `:=` | `libres := [1, 2]; K_f := K[libres, libres]` | STILL | REFUSED | M | "an index on a := line is a whole number or a list of them" |
| C3e2 | L1989, L2207 (ch5) | `:` slice in an index refused on `:=` | `K_g := K[1:2, 1:2]` | STILL | REFUSED | M | same message |
| C3f | L1991, L2127 (ch4 "scalar minus 1x1") | a 1x1 matrix product plus/minus a scalar refused | `N := k*transpose(g)*D + 1[kN]`; `y := 5[kN/m] - k` with `k := [3]*1[kN/m]` | STILL | REFUSED | M | message also quotes internals: `'... + 1 * __u_kN' adds a number to a matrix` (see N2) |
| C3i | L1993 | `table` with response columns of different units refused | `table(x*1[kN/m], x^2, x, 0[m], L, 3)` | STILL | REFUSED | M | "table response columns have incompatible units" |
| A4 | L69-70, L2432 (ch9) | a placeholder holding an operator | `% op = '+'`; `y := 2[kN] {op} 3[{u}]` | STILL | REFUSED | L | "unsupported syntax 'Constant'" |
| C5i | L2180 (0.45.0 left) | `cosh` of an angle refused | `x := cosh(30[deg])` | STILL | REFUSED | L | "cosh requires a dimensionless argument" (sin/cos accept degrees) |
| C7a | L2303, L2376 (ch8 relational) | `assume(beta < pi/2)` / `assume(L < 3*L_e/2)` refused and stop the cell | `assume(beta < pi/2)` | STILL | REFUSED | M | line 1 stops; only sign assumptions supported |
| B10 | L1849, L2434 (ch9), L2658 (ch10 km) | `km`, `lbf`, `lb`, `percent` are not units: `[km]`/`[lbf]` refused, `L := 2*km` "unknown numeric name", on a `=` line `5*km`/`3*lbf` print as free letters | `L := 2*km`; `y := 1[lbf]`; `c = 5*km` | STILL | MISSING | M | the old "notice about a correct value" no longer fires; the units themselves are still missing |
| C9k | L2434 | no kip palette | `%eng_units kip` | STILL | MISSING | M | "unknown unit palette 'kip'; available: kN, kgf" |
| C2c | L1936-1937 | `numeric` of a formula still holding a free symbol; a target unit on a partial result | `u = P/k + x; numeric(u)`; `u(x) = P/k + x; numeric(u(x), mm)` | STILL | MISSING | L | "requires values for: x"; "target-unit conversion requires a fully numeric result" |
| C3k | L1994 | a loop value in narrative text is printed literally | `% for th in [30, 60]:` / `"""ángulo {th}"""` | STILL | MISSING | M | page reads `\{th\}` |
| C6a | L2252 | no virtual-increment name δθ / δv_A | `dtheta = 2; delta_theta = 3` | STILL | MISSING | M | `dtheta` italic word, `delta_theta` -> δ_θ |
| C6i | L2265 | `heaviside` | `y = heaviside(x - 2)` | STILL | MISSING | L | "unsupported function" |
| C7c | L2302 | a general `b(y)` inside `integrate` | `y = integrate(b(y)*y, y, 0, h)` | STILL | MISSING | L | "unsupported function 'b'" |
| C8j | L2376 | `cot`, `sec` | `y = cot(x) + sec(x)` | STILL | MISSING | L | unsupported function |
| C8k | L2376 | `dsolve` | `dsolve(diff(f(x), x, 2) + f(x), f(x))` | STILL | MISSING | L | unsupported |
| C9c | L2435 | a list inside a loop placeholder | `% for L in [[1, 2], [3, 4]]:` / `a_{L[0]} := {L}` | STILL | MISSING | L | clear refusal message |
| C10a | L2649 | no argmin / index of the governing entry | `g := max(f[1], f[2], f[3])` works; no index | STILL | MISSING | M | nothing named argmin/argmax in src |
| C10b | L2650 | no `% break` | `% break` inside `% for` | STILL | MISSING | M | "a line that starts with % is % if, ..." |
| C10d | L2651 | a `%` helper lambda cannot see another helper | `% f = lambda x: 2*x`, `% g = lambda x: f(x) + 1`, `y := {g(2)}` | STILL | MISSING | L | "f is neither a variable of the % lines nor a value of the sheet" |
| B7 | L1130 | `table` over a list names its rows only by number | `table(f(M), M, [M_1, M_2])` | STILL | MISSING | M | rows 3.00 / 5.00, not M_1 / M_2 (improvement, never requested) |
| M5 | L2207 | `member()` with a load over part of a span | (by `%eng_help member`: `load=w`, `load=[w_1, w_2]`, `point=[P, a]` only) | STILL | MISSING | M | not run; syntax has no partial span |
| C10e | L2653, L2371 (ch8) | a power of a fraction loses its parentheses: `(x[1]/y)^2` -> `\frac{x_1}{y}^{2}`; loop rule `(a/L)^(1/3)` -> `\frac{a_i}{1 m}^{1/3}` | `x := [3[kN]; 4[kN]]; y := 2[kN]; p := (x[1]/y)^2` | STILL | PRESENTATION | H | reads as x_1/y² - misleading; every Φ line of ch10 |
| C3b | L1983, L2436 (ch9) | `solve(K, -K*u)` written `K^{-1} -K u`; `solve(K, -2*F)` -> `K^{-1} -2 F` | `d := solve(K, -2*F)` | STILL | PRESENTATION | M | missing parentheses around a negative rhs |
| A5 | L70-71 | on a `=` line an exact range-solve root is written `2.0` | `x = solve(eq(x^2, 4[m^2]), x, 0[m], 5[m])` | STILL | PRESENTATION | M | `x = 2.0 m` |
| C4k | L2125 | values between 0.1 and 1 get two decimals | `A := 0.237[in^2]` -> `0.24 in²`; `r := 0.24` | STILL | PRESENTATION | H | two significant figures for in² areas |
| C6c | L2256 | ratios 0.597 / 0.605 both shown 0.60 | `r_1 := 0.597; r_2 := 0.605` | STILL | PRESENTATION | M | same family as C4k |
| C2j | L1944, L2085, L2124 | degrees in formulas: `cos(60 deg)` with a word, never `60°`; trig of degree values never reduced symbolically | `y = sin(30*deg)`; `F = P*cos(45*deg)` | STILL | PRESENTATION | H | `\sin(30\,\mathrm{deg})`, then 0.50 |
| C2l | L1945, L2251 | piecewise reads "for ... otherwise" in English | `q(x) = piecewise(1, x < 2, 0)` | STILL | PRESENTATION | H | his 2026-09-25 call covered `Where`/`Domain`/`x in` of the region block, not piecewise |
| C2e | L1939, L1998 (ch3), L2305 (ch7) | kept names lost in part assignment and `zeros(n,n) + M` | `keep k = E*A/L; K = zeros(2,2); K[1,1] = K[1,1] + k*c^2` -> `c² E A/L` | STILL | PRESENTATION | M | |
| C2f | L1940 | `solve` answers expand kept names | `keep k_b = E*A_b/L ... dP_b = solve(...)*k_b` -> `A_b T/(A_b + A_c)` | STILL | PRESENTATION | M | |
| C3o | L1999 | a function body expands kept names inside `piecewise` | `keep k = E*A/L; f(x) = piecewise(k*x, x < L, 0)` | STILL | PRESENTATION | M | `x E A/L` |
| B1 | L246, L1432-1436, L1469, L2718 | a substitution over plain definitions expands them (`phiMn`) | `d = h - cover; a = As*fy/(0.85*fc*b); phiMn = ...` BEFORE the `:=` values; `numeric(phiMn)` | STILL | PRESENTATION | H | FIXED when the values come first (rule 2, 0.42.0): `φ As fy (d - a/2)`. With definitions written before the values it still reads `h - 0.59 As fy/(fc b) - cover` over 2 rows (`keep` avoids it) |
| B2 | L452, L2306 (ch7) | a matrix of integrals drawn entry by entry, off the page | `B = [1, x, x^2; x, x^2, x^3]; K = integrate(transpose(B)*B*E*I/L^4, x, 0, L)` | STILL | PRESENTATION | M | 9 integrals then 9 results on one row |
| C4b | L2094 | a `=` matrix line drops the formula typed | `d = [2, 1; 1, 3]; f = inv(d)` | STILL | PRESENTATION | M | `f = [3/5, ...]`, no `d^{-1}` |
| C4d | L2096-2098, L2307 (ch7) | a factor in front of a matrix is pushed into every entry, not cancelled, never shown outside | `K = 6*E*I*L/L^3*[1, 2; 2, 1]` -> `6EIL/L^3` | STILL | PRESENTATION | M | also `2*a*[1, x; x, 1]*b`; `factor(K)` per entry (L2126) leaves entries unfactored |
| C4e | L2098, L2220, L2440 | matrices wider than the page drawn in full (numeric 13x13, symbolic 3x10); `identity(13)`/`zeros(3,3)` written as words | `K := identity(13)*1000[kN/m] + ...`; `T := [gamma, zeros(3,3); ...]` | STILL | PRESENTATION | M | summary only exists for loop assemblies |
| C4f | L2100 | a tiny length among mm reads `7.49 × 10^-7 m` | `d := 7.49e-7[m]` | STILL | PRESENTATION | L | |
| C9f | L2438, L2573 | `1e8[mm^4]` as an argument written `100000000.0`, value row `200000000.0 mm^4`; `1e12` in a matrix literal `1000000000000.0` | `f(I) = 2*I; y = f(1e8[mm^4])` | STILL | PRESENTATION | M | the value row is unformatted too |
| C4h | L2101, L2655-2656 (ch10) | loop counters/conditions with decimals: `% while` note "3.00 ≥ 3.00" without the counter's name; `% if` "Como 1.00 ≤ 1.00"; a while stop "φ = 1.00 ≥ 1.00" | `% k = 0 / % while k < 3:`; `phi := 0.996 / % while phi < 1:` | STILL | PRESENTATION | M | the φ case hides why it stopped |
| C8i | L2375 | `N := 40` shown 40.00 | `N := 40` | STILL | PRESENTATION | H | integers read as decimals everywhere |
| C10k | L2657 | integer and zero vectors written twice | `v := [1; 2; 3]` -> literal then `[1.00; 2.00; 3.00]` | STILL | PRESENTATION | M | |
| C5a | L1943 | a formula printed twice before `numeric` | `K = E*I/L^3*[...]; d = solve(K, [10*kN; 0*kN*m]); numeric(d)` | STILL | PRESENTATION | M | `d` row repeated, reordered |
| C2h | L1943 | `((8000 mm²))²` double parentheses | `A := 8000[mm^2]; x = A^2; numeric(x)` | STILL | PRESENTATION | H | |
| C8h | L2375 | `(15.00°) - (5.00°)` | `a := 15[deg]; b := 5[deg]; c = a - b; numeric(c)` | STILL | PRESENTATION | M | house style puts every value in brackets |
| C2k | L1944, L2085 | a bare `solve` of a named equation shows nothing on the left | `e1 = eq(2*x + 1, 5); solve(e1, x)` | STILL | PRESENTATION | M | row reads `& & 2` |
| C2m | L1945-1946 | plot: title `F(T)` for two series, legend `F_b(T)` raw, the kink unlabelled | `plot(F_a(T), F_b(T), T, 0, 10)` | STILL | PRESENTATION | M | legend texts are plain `F_a(T)` |
| C2d | L1938, L2258 | radicals not rationalised | `a = 1/sqrt(2)` | STILL | PRESENTATION | L | |
| C3l | L1995, L2310 | `$...$` in a `###` heading stays literal | `### Momento $M_u$` | STILL | PRESENTATION | M | heading is an HTML div holding `$M_u$` |
| C3p | L2000 | `numeric` of a piecewise substitutes every branch | `numeric(M(x))` over a 2-branch piecewise | STILL | PRESENTATION | L | arguably intended |
| C3q | L2000 | table headers drop fixed arguments | `f(x, c) = c*x; table(f(x, q), x, ...)` -> header `f(x)` | STILL | PRESENTATION | M | |
| C3r | L2002-2003 | mixed number formats in one matrix; `\frac{1 kN}{1 m}` for a bracket unit in a matrix | `K := [2690000, -332106.78; ...]*1[kN/m]`; `K = [1[kN/m], 0; 0, 2[kN/m]]` | STILL | PRESENTATION | M | `2.69 × 10^6` beside `-332106.78` |
| C5b | L2206 | `EI_theta_b` not Greek | `EI_theta_b = 2` | STILL | PRESENTATION | L | `EI_{theta b}` |
| C5e | L2217-2218 | loop rule writes `{A}e3[mm^2]` as `(Ae_3)_{mm^2}`; `{phi}*deg` as `φ deg` | `a_{i} := {A}e3[mm^2]; c_{i} := cos({phi}*deg)` in a `% for` | STILL | PRESENTATION | M | values in the table are right |
| C5m | L2218 | one loop assembling K and P says its "para" list twice | two part assemblies in one `% for` | STILL | PRESENTATION | L | one note per matrix |
| C5f | L2220 | `alpha` 1.2e-5 written 0.000012 | `alpha := 1.2e-5[1/degC]` | STILL | PRESENTATION | M | a plain `1.2e-5` reads `1.20 × 10^-5` |
| C5h | L2121, L2659 (ch10 "kip sheets in SI") | a kip/inch sheet's matrices read in SI | `E := 29000[ksi]; ... K := [k, k; k, k]` -> `10^3[42.32 ...] kN/m` | STILL | PRESENTATION | M | the scalar `numeric(k)` reads kip/ft |
| EXd | L2086 | kN/mm stiffnesses read in kN/m | `k := 5[kN/mm]; K := [k, -k; -k, k]` -> `10^3 [5.00 ...] kN/m` | STILL | PRESENTATION | M | family rule |
| C5l | L2232 (0.45.1 left) | `numeric` of a matrix with a missing name stops silently | `K = E*A/L*[1, -1; -1, 1]*q; numeric(K)` (q undefined) | STILL | MESSAGE | M | substitution row, no value, no console message (scalar says "requires values for") |
| C6d | L2256-2257 | the integral of a piecewise with a symbolic limit opens "for L < 0" | `f(x) = piecewise(x, x < L/2, L - x); integrate(f(x), x, 0, L)` | STILL | PRESENTATION | M | |
| C6j | L2257, L2276 (0.45.2 left) | a nested/product piecewise lists impossible branches | `g(x) = piecewise(f(x), x < 1, 0)` -> `x > 2 ∧ x < 1` | STILL | PRESENTATION | L | |
| C6e | L2258 | `log(-2L) - log(-L)` not simplified to `ln 2` | `y = log(-2*L) - log(-L)` | STILL | PRESENTATION | L | reads `= 0.69`; `simplify(y)` shows `y` then `(0.69)` |
| C6g | L2261 | `K = K + ...` in a loop prints every pass | `K = [1,0;0,1]*k`; `% for`: `K = K + [1,0;0,1]*k` | STILL | PRESENTATION | M | only part assignments are summarised |
| C6h | L2262 | a system with `:=` coefficients answers in names, no numbers | `a := 2.5; b := 3.7; solve(eq(a*x + b*y, 1), eq(b*x - a*y, 2), x, y)` | STILL | PRESENTATION | M | `x = (a + 2b)/(a² + b²)`; no 0.x value |
| C6l | L2263 | a sum of integrals reordered | `y = integrate(M(x), ...) + integrate(V*x, ...)` | STILL | PRESENTATION | L | V's integral printed first |
| C6m | L2255 | d/dx and ∂/∂x mixed | `V(x) = diff(M(x), x)` -> ∂/∂x; `y = diff(x^3, x)` -> d/dx | STILL | PRESENTATION | L | |
| C6k | L2277 (0.45.2 left) | `g(2[m])` with `q = P/2` shows `m P` | `q = P/2; g(x) = q*x; z = g(2[m])` | STILL | PRESENTATION | L | |
| C7b | L2303 | `$$` display math in a text block breaks | `"""Texto con $$x^2$$ ..."""` | STILL | PRESENTATION | L | `{$x^2}\text{\$ }` |
| C7f | L2308 | zeros unsimplified | `y = ((2 - pi)*L - (2 + 3*pi)*L + 4*pi*L)/(4*pi)` | STILL | PRESENTATION | L | formula kept, then `0.00` |
| C8d | L2372 | `x/0.85` in a function shown as `1.18 x` | `f(x) = x/0.85` | STILL | PRESENTATION | H | ACI-type coefficients |
| C9a | L2373 (ch8) | a loop's table printed before the inner `% while` rows that produced it | `% for` holding a `% while`, two `:=` lines | STILL | PRESENTATION | L | values now right (ch9's "tabulates values from before the while" is FIXED) |
| C9i | L2439 | nested loops: inner `:=` lines printed pass by pass, not gathered | `% for i` / `% for j` / two `:=` | STILL | PRESENTATION | M | |
| L44 | L2121, L2311 (ch4, ch7) | a loop of `:=` lines reading a matrix entry is never tabled | `y_{i} := x[{i}] - {-i}; z_{i} := 2*y_{i}` | STILL | PRESENTATION | M | `- {-i}` keeps its parentheses now (0.44.0 low item FIXED) |
| C10c | L2651 | values set in a `% if` inside a `% for` not tabulated | see repro_C10c2 | STILL | PRESENTATION | L | printed after the table, one by one |
| C10f | L2654 | a loop table converts a value typed in ft to inches | `L_{i} := {i}*10[ft]` + 2nd `:=` | STILL | PRESENTATION | M | column `L_i [in]` 120.00 |
| C10g | L2655 | a function call inside `solve` shown expanded | `E_t(s) = 29000[ksi]*(1 - s/50[ksi]); x = solve(eq(E_t(s)*2[in^2], 1000[kip]), s)` | STILL | PRESENTATION | M | answer `50 ksi - 25 kip/(29 in²)` left unevaluated too |
| C10h | L2655 | loop rule `{Lr}*r` reads `L_{Lr} = Lr r` | `% for Lr in [2, 3]:` / `L_{Lr} := {Lr}*r` | STILL | PRESENTATION | L | |
| C10l | L2657 | `Z*sigma_y` shown in kip·ft | `M_p := 96.8[in^3]*50[ksi]` -> 403.33 kip·ft | STILL | PRESENTATION | L | book writes kip·in |
| C10m | L2657 | `1000[kN]/1[kip]` not reduced | `r := 1000[kN]/1[kip]` | STILL | PRESENTATION | L | `1000.00 kN/kip` (max/min with it are right since 0.46.1) |
| C10n | L2656 | small forces switch to N in a kN vector | `F := [1[kN]; 1e-7[kN]]` -> `[1000.00; 0.0001] N` | STILL | PRESENTATION | M | the whole vector moves to N |
| B5 | L1094-1095 | the `% while` sentence writes abs(f(c)) as the expanded body | `f(c) = ...`; `% while abs(f(c)) > 0.001[cm^3]:` | STILL | PRESENTATION | L | |
| B8 | L1588-1590, L1744 | inside an integral a product reads `x R_A` | `keep R_A = q*L/2; V(x) = R_A - q*x; M(x) = integrate(V(x), x, 0, x)` | STILL | PRESENTATION | M | now the result reads `x R_A` too |
| SUMb | L2084, L2219 | `s k` with `s := 0` kept as a non-zero term | 12x12 `=` loop assembly with `[k, s*k; s*k, k]` | STILL | PRESENTATION | L | matrix fit the page so the "términos no nulos" count was not reached |
| A1 | L67-68 | a scalar from kip entries in a refused condition says `m·kg/s²` | `f := [3[kip]; 1[kip]]; F := f[1]; % if F > 0.5[m]:` | STILL | MESSAGE | L | "cannot compare F > 0.5[m]: m·kg/s² against m" |
| A2 | L68 | `3[m^0.5]` quoted `3[m^0].5` | `% if a > 3[m^0.5]:` | STILL | MESSAGE | L | |
| A3 | L69 | `2*3[m]` quoted `2 * (3[m])`; `1e3[mm]` quoted `1000.0[mm]` | `% if a > 2*3[m]:`; `% if a > 1e3[mm]:` | STILL | MESSAGE | L | |
| N2 | found here (C3f, C4n) | the matrix-plus-number refusal quotes internal names | `y := 5[kN/m] - k` (k 1x1) | STILL | MESSAGE | M | `'5 * __u_kN / __u_m - k' adds a number to a matrix` (0.46.2 removed `__u_m` from condition messages only) |
| B14 | L1904 | `case D = numeric(M(L/2))` advice fails when pasted | paste `case D = M(L/2)` | STILL | MESSAGE | L | the advice gives "a load case must be a function of exactly one variable" |
| B15 | L1905 | a two-name cycle names one | `a = b + 1; b = a + 1; c := a` | STILL | MESSAGE | L | "b is defined from itself"; page shows `b = b + 2` |
| C3h | L1992, L2499 (N6b) | `extrema` of `max(...)` and of `P/(x(3-x))` refuse with internal jargon | `f(x) = max(x*1[kN/m], (L - x)*2[kN/m]); extrema(f(x), x, 0[m], L)` | STILL | MESSAGE | M | "characteristic numerical fallback could not validate a solution set" (N6b no longer mislabels, it refuses) |
| C4a | L2093 | `lambda` as a name: no hint | `lambda := 2` | STILL | MESSAGE | M | "reserved identifier 'lambda'" (λ is natural for eigen/load factors) |
| C5k | L2233 (0.45.1 left) | the psi notice fires for US sheets meaning the unit | `y = 2*psi` | STILL | MESSAGE | L | notice tells to bracket it; arguably right |
| TOOL | L1947-1949 | `tools/render_memoria.py` typesets with MathJax 3.2.2, which lacks `\allowbreak` | tools/render_memoria.py:127 | STILL | PRESENTATION (tooling) | L | not the product; the harness does not show Colab's KaTeX |

## FIXED (did not reproduce on 9b09b02)

| id | source | finding | repro | status | notes |
|---|---|---|---|---|---|
| A6 | L71-72 | `2.5[kip*ft]` -> `ft·kip` | `M = 2.5[kip*ft]` (also with kN palette, in a product) | FIXED | reads `kip·ft`. Seen instead: `2.5[kip*ft] + 1[kip*ft]` reads `1 kip·ft + 2.5 kip·ft` with no value row |
| A7 | L61-63 | `2[mm/m]*200000[MPa]` reads `400000 mm·MPa/m` | `s := e*E`, `s = 2[mm/m]*200000[MPa]`, `max(e, 0.001)*E` | FIXED | all read 400.00 MPa |
| A8 | L175-177 | refusals quote `__u_m` / stand-in `3[1]` | `% if f[1] > 0.5[m]` | FIXED | 0.46.2; pinned by tests/test_what_the_audit_of_0_46_1_left_low.py |
| B4 | L1026-1028 | `max`/`min` rows in base units | kgf palette `Vu = max(V_1, V_2)`, `s_e = min(...)` | FIXED | kgf / cm |
| B9 | L1789-1790 | a kept argument expanded in the call's head | `keep d = L - a; y = M(d)` | FIXED | head reads `M(d)` |
| B11 | L1850 | a `% for` of `=` values tells each name | `L_{i} = {i}*m`, `M = q*L_1*L_2` | FIXED | one notice naming both |
| B12 | L1853 | partial call past a derivative breakpoint | `V(3[m])` of `diff` of a piecewise | FIXED | 20.00 kN |
| B13 | L1903 | bare `numeric(M(x))` crashes the renderer | `numeric(M(x))` | FIXED | substitution + law in x |
| C2g | L1941 | kept flexibility `7.50e-9 m/(mm²·MPa)` | `f = L/(E*A); d = f*P` | FIXED | `1.88 × 10^-6 m/kN` |
| C2i | L1943 | `(−1) f R`, `−0.00 EA` | `R = -f*R_1`; `s = -0.0001*E*A` | FIXED | |
| C2s | L1944, L2004, L2205 | a parameter `s` read as seconds | `f(c, s) = c + 2*s` | FIXED | 0.45.1 |
| C3a | L1982 | `N := k*0.5[mm]` reads `MPa·mm³/m` | | FIXED | `1.00 kN` |
| C3c | L1986 | the 3.2 ratio's unit off by 1000 in `table` | `table(r*y/x, ...)` | FIXED | values right; header defect is N1 |
| C3g | L1991 | `abs()` with bracket units | `z := abs(a - 3[kN] - b)` | FIXED | 6.00 kN |
| C3j | L1993 | `% for` over lists of DOF numbers | `% for dofs in [[1, 2], [2, 3]]:` | FIXED | |
| C3m | L1994 | symbolic answer with decimal coefficients | `x = solve(e, x)` with 0.4829 | FIXED | `0.24145 m P/(A E)` |
| C3u | L1982 | `F[1] + 1[kN]` in SI base | `S := F[1] + 1[kN]` | FIXED | 301.00 kN (0.43.4) |
| C4c | L2096 | `diff` of a named quantity writes out the expression | `keep k = E*A/L; y = diff(k*x^2, x)` | FIXED | `2 k x` |
| C4g | L2101 | compound units in typed literals read `kN m` | `k := 5[kN*m/rad]` | FIXED | `kN·m` |
| C4l | L2125 | units chosen per entry in one displacement vector | `d := [2[mm]; 0.0005[mm]; 3[m]]` | FIXED | one unit (mm) |
| C4s | L2147-2148 | re-running a problem cell without `%eng_reset` after its solve | two cells, same system solve | FIXED | both run |
| C5d | L2208 | 6x6 `[gamma, zeros(3,3); ...]` on `:=` | | FIXED | |
| C5g | L2221 | numbers typed into function arguments folded and rounded | `y = f(0.86*inch^2)` | FIXED | `0.86 in² E/ft` |
| C6b | L2255 | ∂²/∂x² left unevaluated inside an integrand | `integrate(diff(x^3*a, x, 2), x, 0, L)` | FIXED | `6 x a` |
| C6f | L2260 | a bracket literal folded into a rounded float coefficient | `32[mm]*P/(1000*k*1[mm])` | FIXED | reads `32 mm P/(1 · 1000 mm k)` (odd `1 ·`, no rounding) |
| C7g | L2309 | `:=` with `integrate` shows the value only | `k := integrate(x^2*1[kN/m^3], x, 0, L)` | FIXED | integral shown |
| C8a | L2368 | `plot` of `sqrt(t)/sin(t)` 40-80 s | `plot(sqrt(t)/sin(t), t, 0.1, 3)` | FIXED | 7.6 s |
| C8f | L2374 | `0.3` turning into `3.0`/`10.0` in a system solve | bare `solve(eq(0.3*x + y, 1), ...)` | FIXED | 2.11 / 0.37 |
| C8g | L2374 | unit order `in·kip` | `M := 3[kip*in]` | FIXED | `kip·in` |
| C9h | L2440 | `tan(π/4)` in a table reads `10.00 × 10⁻¹` | `table(tan(x), x, 0, pi/4, 3)` | FIXED | 1.00 |
| C9j | L2433 | range solve says "no root" for incompatible units | `solve(eq(x + 1[m], 3[kN]), x, 0[m], 5[m])` | FIXED | "incompatible units" |
| C9a' | L2430 | `% for` holding `% while` tabulates values from before the while | see repro_C9a | FIXED | table 1.00 / 2.00 (order issue kept under C9a) |
| EXa | L2084 | `inv` of a stiffness in `s²/kg` | `F := inv(K)` | FIXED | `10^-3 [...] m/kN` |
| N6a | L2497 | `P/(x-2)` on [1, 3] labels ends global min/max | `extrema(P/(x - 2), x, 1, 3)` | FIXED | "no finite characteristic points" (does not say unbounded) |
| N6c | L2499 | `transpose(transpose(T))` renders `T^{T}^{T}` | `U := transpose(transpose(T)); V := T''` | FIXED | `(T^{T})^{T}` |
| AU4 | L2532-2533 | `inv(K)*F` leaves a zero plain; `d[3] + 1[mm]` silently 1 mm | `e := inv(K)*F; g := d[2] + 1[mm]` | FIXED | both columns in mm; sum right |

Also recorded fixed by later releases and not re-run (their own sections close them): governing 54 s,
`As_req` kept name, `U1(L/2)`, "Governing - x", "Comparison envelope", moments/non-uniform loads in
`frame_plot` (0.36.0); `0*kN` reads `0.00 N` (0.37.0); long substitution row (0.37.0); `extrema(sqrt)`
(0.32.1); `extrema` over interp (0.32.1); `extrema(atan(x/L))` (0.41.2); `expand`/`simplify` kept names
(0.33.5); `numeric(M(L/2))` law in x (0.43.0); free argument named like a parameter (0.43.1); `numeric`
inside a product (0.43.2); ch2's 0.007 and `P/(5 1/4 k)` (0.43.3); plot hang, raw units (0.43.4);
assembly reprints (0.44.0); system-solve constants in diff, `subs` (0.44.1); temperature, sinh,
one-row literal (0.45.0); ch5 refusals (0.45.1); ch6 crashes (0.45.2); ch7 misreads, slow inv,
symbolic exponents, integer assumption, logs (0.45.3/0.45.4); ch8 deg roots, subs/sum on `:=`,
elliptic_k, interp plot (0.45.5); ch9 eigen/det on `:=`, placeholders in while (0.45.6); ch10 max/min,
det overflow, condition placeholders and entries, `{n} :=`, singular G (0.46.1-0.47.0).

## UNCLEAR (no faithful small repro, or ambiguous semantics)

| id | source | finding | why |
|---|---|---|---|
| U1 | L2148-2149 | `subs(g(x), C_2, 5)` of a function defined after the solve "stays wrong" | repro_C4q: `g(x)` displays `2x - 1`, `subs(g(x), C_2, 5)` gives `2x + 5` - inconsistent with its own row, but which answer is "right" is the recorded ambiguity |
| U2 | L2101 | solved constants still shown in later formulas | repro_C4p shows nothing wrong; needs the book sheet |
| U3 | L2440 | `det(B - λI)` with I the inertia | `eigenvals(B)` with `I := ...` shows no det row (repro_C9g2) |
| U4 | L2099, L2123 | `frame_plot` moment sign follows other members; no moment at a supported joint; value box covers a label | needs a frame and the figure image |
| U5 | L2652 | ~0.15 s per element per event (10.13b 852 s, 10.14 > 40 min) | not timed (too long for this pass) |
| U6 | L2218 | stacked fractions of loop rules touch | needs KaTeX in Colab |
| U7 | L2222, L2206 | fixed-end vector by parts never in numbers; 4x1 substitution row wider than the page | needs the ch5 sheet |
| U8 | L2254-2255, L2259 | a solve's equation row repeats the whole expression; a sum into 12 fractions (6.3); 25-digit radicals (6.8) | needs the ch6 sheets |
| U9 | L2304 | 7.4/7.6 unreadable | needs the ch7 sheets (logs part fixed in 0.45.4) |
| U10 | L2305 | product-rule derivatives uncollected | repro_C7d reads the ordinary product rule |
| U11 | L2373, L2374 | plot maxima sampled, not solved; substitution rows in another unit than the value | not reproduced in small sheets (repro_C8a, repro_C8m) |
| U12 | L2047-2049 | 0.44.0 low: draw/summary edge (±3% of 900 px), page order when a line reads K mid-assembly, `str(...)` helpers in a "con" row, rule row not wrapped | edge cases not built |
| U13 | L2095 | no "formula = 0" verification row | a feature request; no syntax to test |
| U14 | L2436-2439 | nested `% for` summary merged and printed after; pass 1's rows before the rule; nested loops dumping per-pass matrices (pages MB); loop tables print the raw tuple | small loops look right (repro_C5e2 table reads `1, 1, 30`); the MB pages need the ch9/ch10 sheets |
| U15 | L2262 | a substitution row leaving a `:=` name as a letter | not reproduced (repro_C6o) |
| U16 | L33-35 | eigenvals known limits (antisymmetric part under 1e-12, ~10 s at 60 DOF) | declared limits of 0.47.0, not re-measured |

## DECISIONS (his call / approved rule / deliberately left) - not defects unless he reopens them

- D1 `max(2[mm/m], 0.001)` reads `0.002` (0.46.2, L61-63; re-run: `m := max(e, 0.001)` = 0.002).
- D2 A mixed-unit numeric matrix takes a `10^3` factor in front (his choice 2026-09-24, L668-673, L2691).
- D3 `%eng_units kN` writes `6000*mm^2` as `0.006 m²`, δ in m (closed, L1097, L1231).
- D4 English `Where` / `Domain: ... to ...` / `x in` of the region block, and the `extrema` block's words (L1228, L2351).
- D5 Band rule: a small force in N among kN, a lone zero in its family's first member (approved, L2023-2025; re-run: `Q := 0.001[kN]` -> 1.00 N). C10n is a vector case of it.
- D6 A value written with `=` folds into a formula beside a name that stays a name; the notice suggests `:=` (his decision, 0.43.0, L1809-1811). Related STILL-looking rows: `M = 2 m² q` (repro_B11b), `f(L)` -> `f(3 m)` (repro_C4j, ch4 L2120).
- D7 A bare `solve(eq(...), x)` defines nothing (reverted in 0.43.3, differs from what he approved, L1957-1964); a system `solve` does define its unknowns (L2082) - the asymmetry stands.
- D8 `\frac{P}{5 k/4}` vs a slash, his call (L1973).
- D9 A whole side `numeric(M, tonf*m)` in a condition written in the unit asked (differs from main, his call, L1899).
- D10 `x = 0 (0.00)` repeats a plain number; a `0*m` in a table prints `0` (left deliberately, L424-425).
- D11 An annotation of a million keeps the page's number while the axis reads `x10^6` (kept, L732-733).
- D12 House style: a lone fraction numerator/denominator or matrix entry keeps its brackets (`q/(L/2)`), values in brackets (L1791-1792); C8h follows from it.
- D13 An `N` never defined warns; refusing the line instead is his call (L2712-2713).
- D14 `acos(0.5)/kL` with a plain kL stays an angle (my judgement in 0.45.5, L2402-2403).
- D15 More Calcpad functions not added; `ceiling` first if a sheet asks (L396-398).
- D16 `% while` shows only the final result and the count (approved control-flow design, L995-997) - ch8's "never shows its update formula" (repro_C8e) is this.
- D17 A `:=` line shows its value only (the approved forms, L1118-1120) - ch3's "a scalar `:=` never shows its formula" (repro_C3t) is this.
- D18 Design question still open (L2369-2370): a function's body never takes `=` constants defined after it (`w(1) = sin(1) A_1 + A_2`, repro_C8b).
- D19 Left in 0.45.0 (L2179-2181): bare `degC` is a unit like `kN`; a mixed-unit row on `:=` accepted (repro_C5j).
- D20 eigenvals: complex λ refused even where main printed a real part; scope limited to symmetric pencils (his "acotar a simétricos", 0.47.0).
- D21 `numeric` of a call writes its argument (his decision, done in 0.43.0) - closed.
- D22 Rule 2: a formula whose names hold numbers stays a name (his yes, 0.42.0) - closed; B1's remaining case is outside it.
- D23 `0.90` -> `0.9`: first "decided not to do" (0.32.1), then fixed by #323 (0.38.0) - closed.
