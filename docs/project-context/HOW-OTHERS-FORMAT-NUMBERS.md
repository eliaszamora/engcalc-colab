# How other tools decide how a number looks

Written because the engineer said, after the eighth display fix in one session:

> "Siento que estamos parchando sobre parches y no haciendo nada robusto. Si mejor
>  investigas cómo lo hacen librerías más conocidas o programas profesionales para no
>  tener que reinventar la rueda?"

He was right about the patching. What follows is what the established tools actually do,
measured by running them on the numbers of the braced-frame benchmark rather than by
reading their marketing.

The short version, up front:

1. The standard auto-prefix algorithm — Pint's `to_compact()`, forallpeople's
   `_auto_prefix` — **produces exactly the four defects the engineer rejected.** This was
   executed, not argued.
2. The matrix scale factor we added in #99 **is** prior art: MATLAB's `format short` has
   printed a common `1.0e+03` factor for decades, and siunitx calls it `fixed-exponent`.
3. What no professional tool does is **guess**. siunitx's default is to change nothing.
   Mathcad makes the engineer choose per result. EngCalc guesses in seven places, and
   none of the seven is configurable. That is the real architectural difference.

---

## 1. What each tool does

| tool | how many digits | where the exponent / prefix goes | per-result override |
|---|---|---|---|
| **siunitx** (the LaTeX standard for units in engineering documents) | `round-mode` = `none` \| `figures` \| `places` \| `uncertainty`; **default `none`**, `round-precision` 2 | `exponent-mode` = `input` \| `fixed` \| `engineering` \| `scientific` \| `threshold`; **default `input`**. `fixed-exponent` sets one exponent for a group. `engineering` forces a power of three. | yes, per `\num` |
| **Mathcad Prime** (the professional sheet) | Display Precision = **decimal places**. Separately `float` = significant digits, `round` = decimal places | Result Format = Decimal \| Scientific \| **Engineering** (exponents multiples of 3) \| General (exponential above threshold 3, not configurable) | **yes, per result** |
| **MATLAB** `format short` | scaled fixed point | **common scale factor `1.0e+03`** when the largest element exceeds 10³ or falls below 10⁻³ | no |
| **MATLAB** `format short g` | **5 significant digits** | whichever of fixed / scientific is more compact, per value | no |
| **NumPy** | `set_printoptions(precision=)`; `format_float_positional(..., fractional=False)` is significant figures | common factor for the whole array | per call |
| **handcalcs** (the closest prior art to EngCalc: Python calcs → LaTeX in Jupyter) | `display_precision: 3`, **decimal places**, `round(x, 3)`. A `# scientific` cell switches to `calculate_adjusted_precision`, which is significant figures | none of its own — defers to the units library | **yes, per cell** |
| **Pint** `to_compact()` / **forallpeople** | 3 fixed decimals on a mantissa that has already been normalised | **auto-prefix so the mantissa lands in [1, 1000)** | `.to()` / `.prefix()` |

---

## 2. The measurement that settles it

`forallpeople` is the unit library built for exactly this job — engineering calculation
sheets in Jupyter, by the author of handcalcs. Run on the braced-frame numbers:

| quantity | forallpeople | Pint `to_compact()` | the engineer's verdict, this session |
|---|---|---|---|
| `T` period | `16.756 ms` | `16.7562 ms` | *"¿por qué lo dejaste en ms?"* — rejected |
| `K_eq` | `70.303 MN/m` | `70.3032244 MN/m` | *"no me gusta que hayan algunos en kilo y otros en mega"* — rejected |
| `ω` | `0.375 ms⁻¹` | `374.98466 1/s` | "per millisecond" — unreadable |
| `I_c` | `2278125000.000 mm⁴` | `2278125000.0 mm⁴` | rejected |
| `C` | `-0.405 m⁻¹` | `-405.4 1/km` | "per kilometre" for a condensation coefficient |
| `E` | `210.000 GPa` | `210.0 GPa` | correct |

Two independent implementations of the standard algorithm, the same answers, and four of
six are the defects that were reported here as bugs.

**Why the standard rule fails a memoria.** The SI prefix convention optimises one
quantity *read on its own*: put the mantissa in [1, 1000) and pick the prefix. A
calculation sheet optimises something different — *comparability down the page*. The
engineer said this himself before any of this was researched:

> "¿Por qué hay valores con kN·m y otros en MN? ¿No deberían estar todos en la misma
>  unidad?"

Per-value optimality and page-level consistency are different objectives, and the
libraries implement the first. So "do it the way the well-known libraries do" is not
available as an answer: their answer is the one already rejected, on evidence.

---

## 3. Where fixed decimals actually break

`precision` in EngCalc means decimal places, like Mathcad's Display Precision and
handcalcs' `display_precision`. That choice is not unusual. What is unusual is that
EngCalc has no second knob, so one page-wide number has to serve a sheet spanning seven
orders of magnitude:

| | `precision=2` (today) | `precision=6` | 4 significant figures |
|---|---|---|---|
| `I_c` (m⁴) | **0.00** | 0.002278 | 0.002278 |
| `A_d` (m²) | **0.00** | 0.000625 | 0.000625 |
| `T` (s) | **0.02** | 0.016756 | 0.01676 |
| `T` short (s) | **0.00** | 0.000020 | 0.00002 |
| `k` column (kN·m) | 517195.95 | **517195.945000** | 517200. |
| `ω` (1/s) | 374.98 | **374.984660** | 375.0 |

Four of thirteen values destroyed at the low end; raising the precision rescues them and
ruins the top of the page. Significant figures fix both ends at once — including the
`0.00002 s` the engineer named as his floor.

The cost, stated plainly: at four figures `70303.22` becomes `70300.`, and `B = 5.00 m`
becomes `5.`. Inside a matrix this does not bite, because the 10³ factor from #99 has
already normalised the cells; it bites on standalone scalars.

---

## 4. The structural finding

`_significant_figures(magnitude, precision)` is called from five places in
`src/engcalc_colab/renderer.py`:

| line | function | what it is doing there |
|---|---|---|
| 483 | `_best_in_family` | choosing a **unit** by asking whether the digits survive |
| 579 | `_display_quantity` | keeping a declared **unit** if the digits survive |
| 624 | `_magnitude_text` | the digit rule itself — escape to scientific notation |
| 743 | `_matrix_scale_exponent` | the group-exponent rule |
| 1778 | `_aggregate_unit` | choosing a matrix **unit** by the same question |

Three of the five are the *digit* rule leaking into the *unit* rule. That is the
mechanical cause of the "the display unit is decided in seven places" finding in
`NEXT.md`, and it is why each new page breaks a different one: they are five copies of
one decision, drifting apart.

siunitx keeps these two axes completely independent — `round-mode` knows nothing about
`exponent-mode`. That separation is the thing worth copying, and it is a deletion rather
than an addition, which is the only honest test of "robust" versus "another patch".

**The one rule in EngCalc that has never drifted is the declared unit.** `E := 210*GPa`
stays in GPa on every path, in every page, and always has. It has never needed a patch
because it is not a guess. Every rule that guesses has needed one.

---

## 5. What to do

Three options, in increasing order of size.

**A. Add `figures` as a rounding mode.** `round-mode=figures` exists in siunitx, in
handcalcs (`# scientific`), in Mathcad (`float`), and in NumPy. Default stays `places`,
so no existing page moves. Fixes `0.02 s` → `0.01676 s` and the four destroyed values.
Small, well-founded, and does not touch the unit machinery.

**B. Add a per-result override.** Mathcad formats an individual result independently of
the document; handcalcs overrides precision per cell; siunitx per `\num`. EngCalc has
only a page-level `%eng_config precision`, which is why a sheet spanning seven orders has
no good global setting. This is the piece EngCalc most conspicuously lacks.

**C. Declare instead of guess.** Let a sheet declare its base system once — the engineer
has already stated it: `kN, m, s`, with mm only below about 1/1000 — and let the families
/ band / term-weighting machinery shrink to serve that declaration rather than infer it.
Largest change, and the one that removes code.

**Not recommended: adopt auto-prefix.** Measured above; it is worse for this user.

Suggested order: **A, then B, then C.** A is one evening and closes the reported defect.
B makes the page workable without a global compromise. C is the architecture, and should
only start once A and B have shown what the declaration actually needs to cover.

---

## Sources

- siunitx manual, `round-mode` / `exponent-mode` / `fixed-exponent` — <https://github.com/josephwright/siunitx>
- MATLAB, *Display Format for Numeric Values* — <https://www.mathworks.com/help/matlab/matlab_prog/display-format-for-numeric-values.html>
- MATLAB, `format` reference — <https://www.mathworks.com/help/matlab/ref/format.html>
- PTC Mathcad, *To Format the Result Display* — <https://support.ptc.com/help/mathcad/r9.0/en/PTC_Mathcad_Help/to_format_the_result_display.html>
- handcalcs `config.json` and `calculate_adjusted_precision`, v1.11.0 (read from the installed package)
- forallpeople `_auto_prefix`, v3.0.0 (read from the installed package)
- Pint `Quantity.to_compact()` (executed against the project registry)
- Engineering notation, mantissa in [1, 1000) with exponents in multiples of three — <https://en.wikipedia.org/wiki/Engineering_notation>
