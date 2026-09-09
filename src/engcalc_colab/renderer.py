from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from html import escape

import sympy as sp
from sympy.printing.conventions import split_super_sub
from sympy.printing.latex import LatexPrinter

from pint.errors import DimensionalityError

from .matrix_numeric import QuantityMatrix
from .models import (
    AssumptionResult,
    CharacteristicInterval,
    CharacteristicPoint,
    EigenvalueSet,
    EigenvectorSet,
    EvaluationResult,
    ExtremaResult,
    GoverningResult,
    InequalityResult,
    IntersectionsResult,
    LoadCaseResult,
    LoadCombinationResult,
    MatrixShape,
    NumericAssignmentResult,
    NumericEvaluationResult,
    NumericMatrixEvaluationResult,
    PartialMatrixNumericEvaluationResult,
    PartialNumericEvaluationResult,
    RootsResult,
    SummaryResult,
    SystemSolveResult,
    TableResult,
)

CalculationResult = (
    EvaluationResult
    | NumericAssignmentResult
    | NumericEvaluationResult
    | NumericMatrixEvaluationResult
    | PartialNumericEvaluationResult
    | PartialMatrixNumericEvaluationResult
)


@dataclass(frozen=True)
class RenderSettings:
    """Global numerical presentation settings for EngCalc output."""

    precision: int = 2
    zero_tolerance: float = 1e-10
    figures: int = 3
    # The composite units this sheet's `:=` lines spelled. Read only by the
    # technical-stress convention, which yields to anything the engineer wrote.
    written_units: frozenset[str] = frozenset()
    # The palette `%eng_units` declared, by name; "" when none. A name rather than the
    # table itself, because this dataclass is frozen and a dict inside one is not
    # hashable. The tables live beside the family tables, which is where a reader looking
    # for "what unit does this sheet use" will go.
    palette: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.precision, bool) or not isinstance(self.precision, int):
            raise ValueError("precision must be an integer from 0 to 10")
        if not 0 <= self.precision <= 10:
            raise ValueError("precision must be an integer from 0 to 10")
        if isinstance(self.figures, bool) or not isinstance(self.figures, int):
            raise ValueError("figures must be an integer from 0 to 10")
        if not 0 <= self.figures <= 10:
            raise ValueError("figures must be an integer from 0 to 10")
        if self.zero_tolerance < 0:
            raise ValueError("zero_tolerance must be non-negative")


_DEFAULT_RENDER_SETTINGS = RenderSettings()


def _letters_of(latex: str) -> str:
    r"""The letters a reader would see, with LaTeX scaffolding stripped.

    `\Sigma` reads "Sigma" and `\mathrm{M}` reads "mathrmM"; either way it is not
    "Mu", and that difference is the whole test for whether a rendering still spells
    the name it was given.

    An earlier draft stripped `mathrm` first, so `\mathrm{M}` reduced to "M". It made
    no difference and is gone: every one of the fourteen entries SymPy renders that way
    is a capital Greek name mapped onto a Latin letter, and not one of them spells
    itself back with or without the strip.
    """
    return re.sub(r"[\\{}^_ ]", "", latex)


class _EngineeringLatexPrinter(LatexPrinter):
    def __init__(
        self,
        settings=None,
        *,
        unit_literals: frozenset[str] = frozenset(),
        render_settings: "RenderSettings | None" = None,
    ):
        super().__init__(settings)
        # Keyword-only: SymPy constructs printers positionally with a settings dict.
        self.unit_literals = frozenset(unit_literals)
        self.render_settings = render_settings or _DEFAULT_RENDER_SETTINGS

    def _print_Float(self, expr):
        r"""Shorten a number that is longer than the page's precision. Never reshape one.

        `a = As*fy/(0.85*fc*b)` puts 1/(2*0.85) into the expression for `a/2`, and SymPy
        prints a Float at its full binary precision, so the memoria carried

            0.588235294117647

        through the formula and again through the substitution: fifteen digits in the
        middle of a page whose every result is shown to two decimals.

        Only numbers longer than that precision are touched. A first draft rounded every
        Float and trimmed the trailing zeros, which read well until it turned the `1.0`
        of `0.9*D - 1.0*Lv` into `1`, deleting a load factor an engineer writes on
        purpose. What the engineer typed is left exactly as typed, which is the rule this
        renderer already follows for units.

        The rounded form goes through `_magnitude_text`, so one setting governs the whole
        page and `%eng_config precision=4` moves this with it.

        `figures` is deliberately switched off for this one path. It is a floor for
        *values* - a period, an area, a stiffness - that would otherwise lose their
        meaning, and 1/(2*0.85) is not a value: it is an artefact of the algebra, which
        the engineer never typed and does not read as a measurement. `0.59` has lost
        nothing, and letting the floor stretch it to `0.588` would both overturn a
        decision this page already made deliberately and shift where long expressions
        wrap, which nobody asked for.

        Everything after the first dot is counted, which is also what sends SymPy's own
        `1.0 \cdot 10^{-8}` down the rounding path: its tail is a whole exponent, always
        longer than any precision this accepts. That matters, because the rest of the
        page writes exponents with `\times` and two notations on one page is a wart. An
        explicit branch for it was written first, measured, and found unreachable.
        """
        written = super()._print_Float(expr)
        decimals = written.partition(".")[2]
        if len(decimals) <= self.render_settings.precision:
            return written
        return _magnitude_text(float(expr), replace(self.render_settings, figures=0))

    def _print_Symbol(self, expr, style=None):
        r"""Print a name so it reads as what the engineer wrote.

        Two rules, in order.

        A unit that survived into the expression is a unit, not a quantity. `subs(M(x),
        x, 3*m)` substitutes symbolically, so the metre stays behind as a free symbol
        and italic set it between `3` and `q` exactly as a variable would. The caller
        decides which names these are, because the alias table cannot: `m := 500*kg` is
        a mass and must keep its italic.

        Then: a multi-letter name is upright, so `eqFy` is not read as `e q F y`. Italic
        is for a quantity, which is a single letter. A name of several letters is a
        label, and setting it in italic makes MathJax space it as a product: the
        reactions block of a memoria showed `eqFy` and `eqMA` as four and four sliding
        letters. This is the ISO 80000-2 rule and what every typeset engineering
        document does.

        SymPy is left in charge only when it spells the base back. That test replaced
        "SymPy produced a backslash, so it recognised the name", which was true and
        beside the point: `translate("Mu")` returns `\mathrm{M}`, because capital mu has
        no glyph of its own, and a memoria that prints a factored moment as `M` has lost
        three characters where a reviewer cannot see them. The same guard catches
        `rebar`, which SymPy's modifier table reads as `re` under an overbar. `\Sigma`,
        `\mu` and `\theta` spell themselves and are untouched.

        Subscripts stay italic and stay exactly as written - `d_{max}` in italic is near
        universal in practice - but they are now braced. Handing SymPy a name carrying
        `\mathrm{...}` made `_split_super_sub` return early on the brace, so nothing was
        split and `\mathrm{As}_prov` subscripted the `p` alone, leaving `rov` beside it.
        """
        if expr.name in self.unit_literals:
            unit = sp.Symbol(rf"\mathrm{{{expr.name}}}")
            return super()._print_Symbol(unit, style) if style else super()._print_Symbol(unit)

        base, supers, subs = split_super_sub(expr.name)
        if len(base) <= 1 or self._sympy_spells_it_back(base):
            return super()._print_Symbol(expr, style) if style else super()._print_Symbol(expr)

        name = rf"\mathrm{{{base}}}"
        if style == "bold":
            name = rf"\mathbf{{{name}}}"
        if supers:
            name += "^{%s}" % " ".join(supers)
        if subs:
            name += "_{%s}" % " ".join(subs)
        return name

    def _sympy_spells_it_back(self, base: str) -> bool:
        """True when SymPy has a symbol for ``base`` and it still reads as ``base``."""
        rendered = super()._print_Symbol(sp.Symbol(base))
        if not rendered.startswith("\\"):
            return False
        return _letters_of(rendered) == base

    def _print_Mul(self, expr):
        if not expr.is_commutative:
            return super()._print_Mul(expr)

        if expr.could_extract_minus_sign():
            expr = -expr
            prefix = "- "
        else:
            prefix = ""

        numer, denom = sp.fraction(expr, exact=True)
        snumer = self._print_engineering_product(numer)
        if denom is sp.S.One:
            return prefix + snumer

        sdenom = self._print_engineering_product(denom)
        return rf"{prefix}\frac{{{snumer}}}{{{sdenom}}}"

    def _print_engineering_product(self, expr):
        if not expr.is_Mul:
            return self._print(expr)

        args = sorted(expr.args, key=_engineering_factor_key)
        separator = self._settings["mul_symbol_latex"]
        rendered: list[str] = []

        for index, term in enumerate(args):
            term_latex = self._print(term)
            if self._needs_mul_brackets(term, first=(index == 0), last=(index == len(args) - 1)):
                term_latex = rf"\left({term_latex}\right)"
            rendered.append(term_latex)

        return separator.join(rendered)


class _NumericSubstitutionLatexPrinter(_EngineeringLatexPrinter):
    def __init__(
        self,
        substitutions: dict[str, object],
        settings: RenderSettings,
        unit_literals: frozenset[str] = frozenset(),
    ):
        super().__init__(unit_literals=unit_literals, render_settings=settings)
        self.substitutions = substitutions

    def _print_Symbol(self, expr):
        quantity = self.substitutions.get(expr.name)
        if quantity is None:
            return super()._print_Symbol(expr)
        return rf"\left({_quantity_latex(quantity, settings=self.render_settings)}\right)"


def _engineering_factor_key(term):
    if term.is_Number:
        return (0, sp.default_sort_key(term))

    base = term.base if term.is_Pow else term
    if isinstance(base, sp.Symbol):
        first_alpha = next((char for char in base.name if char.isalpha()), "")
        if first_alpha.islower():
            group = 1
        elif first_alpha.isupper():
            group = 2
        else:
            group = 3
        return (group, sp.default_sort_key(term))

    return (3, sp.default_sort_key(term))


def _latex(
    expr,
    unit_literals: frozenset[str] = frozenset(),
    settings: RenderSettings = _DEFAULT_RENDER_SETTINGS,
) -> str:
    return _EngineeringLatexPrinter(
        unit_literals=unit_literals, render_settings=settings
    ).doprint(expr)


def _substitution_latex(expr, substitutions: dict[str, object], settings: RenderSettings = _DEFAULT_RENDER_SETTINGS, unit_literals: frozenset[str] = frozenset()) -> str:
    return _NumericSubstitutionLatexPrinter(substitutions, settings, unit_literals).doprint(expr)


# Ordered families of units an engineer actually writes for each dimension. Keyed by
# Pint's dimensionality, which reduces to base dimensions: a table keyed on "[force]"
# silently matches nothing.
#
# Keyed by the *sorted pairs*, not by `str(dimensionality)`. The string was the bug.
# Pint caches one dimensionality object per unit combination and prints its dimensions
# in whatever order the first computation to reach it happened to build them, so a
# flexural capacity written `phi*As*fy*z` produced
#
#     [length] ** 2 * [mass] / [time] ** 2
#
# and missed the moment family, while the same sheet after any earlier computation that
# had already touched that dimensionality produced
#
#     [mass] * [length] ** 2 / [time] ** 2
#
# and found it. Measured both ways in the same process: the memoria's units depended on
# what the notebook had computed before it. Sorted pairs cannot be ordered two ways.
_UNIT_FAMILIES: dict[tuple[tuple[str, int], ...], tuple[str, ...]] = {
    (("[length]", 1),): ("mm", "m"),
    (("[length]", 2),): ("cm ** 2", "m ** 2"),
    (("[length]", 4),): ("cm ** 4",),
    # Kilo is the top step, by the engineer's preference: a sheet stays in kN, m and s,
    # and a value too large for kN has its scale taken outside the brackets by
    # `_matrix_scale_exponent` rather than climbing to mega. Pressure keeps its own step
    # below - mega, not kilo - because nobody writes 25000 kPa for a concrete strength.
    (("[length]", 1), ("[mass]", 1), ("[time]", -2)): ("N", "kN"),
    # The same three steps forces have. With `kN * m` alone a family can change the
    # unit to one an engineer writes but cannot move the magnitude into the readable
    # band, and an assembled stiffness printed `517195.95 kN*m` beside a coupling
    # that had reached `209.67 MN` - one matrix, two scales, for no reason but a
    # missing member. Given the steps the band rule lands them together.
    (("[length]", 2), ("[mass]", 1), ("[time]", -2)): ("N * m", "kN * m"),
    # One member, and `GPa` is deliberately not the second. The exemption that put it
    # here was written from what the codes on the shelf print - "a modulus is 210 GPa" -
    # and the engineer has since said twice, unprompted, that he has never used it:
    # "el E del acero nunca lo he trabajado en GPa", "GPa nunca lo he usado". The code
    # on the shelf is not the sheet on his screen, and the sheet is the product.
    #
    # A sheet that writes GPa still reads in GPa, and nothing was added to make that so:
    # `GPa` is no longer a family member, so `_unit_is_the_engineers` reaches its shape
    # rule - a pressure against the family's own pressure - and keeps it. Removing a
    # member from a family is how a unit stops being *chosen*, not how it stops being
    # allowed.
    (("[length]", -1), ("[mass]", 1), ("[time]", -2)): ("MPa",),
    (("[mass]", 1), ("[time]", -2)): ("N / m", "kN / m"),
    # Time, and its reciprocal. A dynamics sheet ends in a frequency and a period,
    # and `sqrt(k/m)` produces fractional exponents - `GPa^0.5*mm/(kg^0.5*m^0.5)` -
    # that no amount of weighting can read. `1 / s` rather than `Hz`: a circular
    # frequency is rad/s and a natural frequency is Hz, Pint cannot tell them apart
    # because a radian is dimensionless, and `1 / s` is true of both.
    #
    # Seconds and nothing else. `("s", "ms")` was written here first, on the same
    # reasoning that sends a 0.02 m deflection to millimetres - and a period does not
    # obey that convention. It made a building with T = 0.24 s read `240.00 ms`, which
    # nobody writes. A period too short to show figures at the active precision is a
    # precision question, answered by `%eng_config precision=4`, not a unit one.
    (("[time]", 1),): ("s",),
    (("[time]", -1),): ("1 / s",),
}


# How deep the floor may go before an exponent reads better than more zeros. Six
# decimal places, because the engineer named his own floor - "0.00002 sería lo máximo
# que acepto" - and six covers it with one to spare. Past that the reader is counting
# zeros, which is the job notation was invented to remove: `1.00 \times 10^{-8}` rather
# than `0.00000001`. Below the limit the escape to scientific notation still fires on
# its own terms, because a value that shows no figure at six decimals shows none.
_FIGURES_DECIMAL_LIMIT = 6

# "The value really is exactly this" - loose enough that arithmetic noise at the
# fifteenth decimal still counts as exact, tight enough that a real digit does not.
_EXACT_TOLERANCE = 1e-12


def _is_reduced(magnitude, settings: RenderSettings) -> bool:
    """Has the page's decimal count left this value with a single digit or none?

    The one place that answers it. `_decimals_for` asks in order to rescue the value,
    and `_magnitude_text` asks again in order to decide whether the rescue told the
    truth; when the two conditions were written separately they disagreed, and `0.963`
    - which the rescue deliberately leaves as `0.96` - was sent to `9.63 x 10^{-1}` by
    a faithfulness test that thought it had been rescued.
    """
    if settings.figures <= 0:
        return False
    magnitude = abs(float(magnitude))
    if magnitude == 0.0 or not math.isfinite(magnitude):
        return False
    # Leading zeros only. `_significant_figures` strips both ends because it answers the
    # *band* question - whether a value sits in the natural range for its unit - and
    # there a trailing zero genuinely carries nothing. This is a different question, and
    # a trailing zero is a digit the renderer chose to print: `0.80` has lost no more
    # than `0.59` has. Counted the other way, a brace's two direction cosines came out
    # `0.804` and `-0.59`, one line apart, differing only in whether the second decimal
    # happened to be a zero.
    rendered = f"{magnitude:.{settings.precision}f}".replace(".", "").lstrip("0")
    return len(rendered) < 2


def _decimals_for(magnitude, settings: RenderSettings) -> int:
    """Decimal places for one magnitude: the page's precision, raised until the value
    shows `figures` significant digits.

    `precision` is a count of decimal places, which is what Mathcad's Display Precision
    and handcalcs' `display_precision` also mean. One such count cannot serve a page
    that spans seven orders of magnitude: at 2 decimals a period of 0.016756 s reads
    `0.02` and a second moment of 0.002278 m^4 reads `0.00`, while raising the page to
    6 prints a column stiffness as `517195.945000`.

    So `precision` stays a floor and `figures` is a second floor underneath it: never
    fewer decimals than the page asked for, and never so few that the number stops
    saying anything. A large value is untouched - 70303.22 already carries seven
    figures at two decimals - which is the deliberate difference from siunitx's
    `round-mode = figures`, where four figures would round it to `70300`. The engineer
    asked for more decimals on the small values and never for fewer digits on the
    large ones:

        "no tengo problemas en que hayan varios decimales con los segundos,
         0.00002 sería lo máximo que acepto"

    Zeros that reveal nothing are not padded, so `h := 3.70*m` stays `3.70` rather than
    becoming `3.700`; pure significant figures would pad it.

    It is a rescue and not a global guarantee, and the difference is the whole reason
    the page does not churn. The engineer reported `0.02` for a period and `0.00` for a
    second moment of area - one digit and none - and never complained about `0.88` or
    `2.85`, which are perfectly good numbers. So the floor fires only where a value has
    been reduced to a single digit or fewer, and then gives it `figures` of them:

        0.016756  ->  0.02    one digit    rescued to 0.0168
        0.002278  ->  0.00    none         rescued to 0.00228
        0.879     ->  0.88    two digits   left exactly as it was
        2.845     ->  2.85    three        left exactly as it was

    Phrased in digits rather than as `< 0.1` so that it moves with the page:
    `%eng_config precision=4` shifts what counts as reduced, as it should.
    """
    if not _is_reduced(magnitude, settings):
        return settings.precision
    decimals = settings.precision
    magnitude = abs(float(magnitude))
    needed = settings.figures - 1 - math.floor(math.log10(magnitude))
    if needed <= decimals:
        return decimals
    decimals = min(needed, _FIGURES_DECIMAL_LIMIT)
    if decimals <= settings.precision:
        return settings.precision
    # Give back only the decimals the value genuinely does not have. A trailing zero is
    # dropped when the shorter render still *is* the value, and kept when it is a
    # significant zero the rounding produced: `3.7` gives back its third decimal and
    # stays `3.70`, while a period of 0.0300406 keeps `0.0300` rather than collapsing
    # to `0.03` and reporting a number it is not.
    while decimals > settings.precision:
        shorter = float(f"{magnitude:.{decimals - 1}f}")
        if abs(shorter - magnitude) > abs(magnitude) * _EXACT_TOLERANCE:
            break
        decimals -= 1
    return decimals


def _significant_figures(magnitude, precision: int) -> int:
    """Digits that survive a fixed-decimal render and still carry information.

    Asked from five places, and it was tempting to make all five ask about the render
    that `figures` will actually perform. Measured, that is wrong, and the measurement
    is worth keeping: four of the five are choosing a *unit*, and what they mean by
    this question is "does the value sit in the natural band for that unit?" - a band
    question that happens to be spelled in digits.

    Unifying them broke `0.00008*m`, which an engineer writes as `0.08 mm` however many
    decimals the page is willing to print, and which the floor would have left as
    `0.00008 m`. So the band keeps asking about `precision` and only `_magnitude_text`,
    which is the one site actually formatting a number, consults `_decimals_for`.

    They share an implementation and not a meaning. Naming that is the separation
    siunitx gets by keeping `round-mode` and `exponent-mode` independent.
    """
    rendered = f"{abs(float(magnitude)):.{precision}f}".replace(".", "")
    return len(rendered.strip("0"))


# The same table for a sheet written in US customary units. It exists because the
# aliases alone leave one hole, and it is the hole RC-2B was: a flexural capacity comes
# out as `inch^3 * kip_per_square_inch`, four unit terms against the moment family's
# two, so `_unit_is_the_engineers` rightly refuses it and hands it to the family - which
# had only `kN * m` in it. An all-imperial page printed its capacity in kilonewton-metres.
#
# Everything else on such a page already survived: a declared unit is kept, and a
# computed `kip`, `foot * kip` or `inch` is no more complex than its family's canonical
# member. Only the units the algebra invents need somewhere imperial to land.
_US_CUSTOMARY_UNIT_FAMILIES: dict[tuple[tuple[str, int], ...], tuple[str, ...]] = {
    (("[length]", 1),): ("inch", "ft"),
    (("[length]", 2),): ("inch ** 2",),
    (("[length]", 4),): ("inch ** 4",),
    (("[length]", 1), ("[mass]", 1), ("[time]", -2)): ("lbf", "kip"),
    (("[length]", 2), ("[mass]", 1), ("[time]", -2)): ("kip * ft",),
    (("[length]", -1), ("[mass]", 1), ("[time]", -2)): ("psi", "ksi"),
    (("[mass]", 1), ("[time]", -2)): ("kip / ft",),
    # A second is a second in either system.
    (("[time]", 1),): ("s",),
    (("[time]", -1),): ("1 / s",),
}

# Pint's own names for the units the alias table exposes, plus the two spellings a
# conversion can produce on its own.
_US_CUSTOMARY_UNIT_NAMES = frozenset({
    "inch",
    "foot",
    "kip",
    "force_pound",
    "kip_per_square_inch",
    "pound_force_per_square_inch",
})


def _is_us_customary(quantity) -> bool:
    """True when any part of the unit the value already carries is US customary.

    Deliberately `any` and not a majority. A value whose units mix systems is one the
    engineer built out of both, and the alternative rule - SI wins unless everything is
    imperial - silently converts the imperial half of a page somebody wrote in imperial
    on purpose. This only ever decides where a *rejected* unit lands; a unit that came
    from what was typed is kept before the family is consulted at all.
    """
    try:
        return any(name in _US_CUSTOMARY_UNIT_NAMES for name in quantity.units._units)
    except Exception:
        return False


# The metric-technical system: kilogram-force and tonne-force, with stresses in
# kgf/cm^2. Half the Spanish-speaking world writes a memoria in it - Peru and Mexico put
# the steel modulus at 2.1e6 kgf/cm^2, and f'c and fy are written in it beside MPa - and
# without a table of its own such a sheet was converted to SI under the engineer, whose
# own words were: "si te los doy en kgf, entonces que sea kgf".
#
# Lengths, areas and time are deliberately the SI entries. A metre is a metre in both,
# and what distinguishes the systems is how force and stress are spelled.
_TECHNICAL_UNIT_FAMILIES: dict[tuple[tuple[str, int], ...], tuple[str, ...]] = {
    (("[length]", 1),): ("mm", "m"),
    (("[length]", 2),): ("cm ** 2", "m ** 2"),
    (("[length]", 4),): ("cm ** 4",),
    (("[length]", 1), ("[mass]", 1), ("[time]", -2)): ("kgf", "tonf"),
    (("[length]", 2), ("[mass]", 1), ("[time]", -2)): ("kgf * m", "tonf * m"),
    (("[length]", -1), ("[mass]", 1), ("[time]", -2)): ("kgf / cm ** 2",),
    (("[mass]", 1), ("[time]", -2)): ("kgf / m", "tonf / m"),
    (("[time]", 1),): ("s",),
    (("[time]", -1),): ("1 / s",),
}

# Pint's own names. `tonf` is defined by this package; `force_kilogram` is Pint's
# spelling of what the alias table exposes as `kgf`.
_TECHNICAL_UNIT_NAMES = frozenset({
    "force_kilogram",
    "tonf",
})


# One dimension in one system where the family is authoritative rather than a menu.
#
# In SI a stress reaches `MPa` on its own, because `MPa` is a *named* unit: its factor
# shape is a pressure, `N/mm^2`'s is a force and a length, and the shape rule sends the
# second to the first. The metric-technical system has no named unit for a stress - the
# convention is the composite `kgf/cm^2` - so `kgf/mm^2` and `kgf/cm^2` have the same
# shape and nothing about the units themselves separates them.
#
# What separates them is a fact about engineering practice rather than about units:
# f'c is 250 kgf/cm^2, fy is 4200, the steel modulus 2.1e6, and `kgf/mm^2` is not written
# in structural work at all. The engineer, shown a section in millimetres printing it:
#
#     "yo nunca he ocupado kgf/mm2. debería ser kgf/cm2 no? es lo más común?"
#
# It cost more than a unit. `25000 kgf / (300 mm x 450 mm)` printed `0.19 kgf/mm^2` where
# the stress is `18.52 kgf/cm^2`, and `0.19` is not a number anybody recognises.
#
# Written as a convention, and deliberately not as a rule. Three general rules were tried
# first - "the sheet never wrote this composite", "the family member has several factors",
# "a one-member family is authoritative" - and each one broke something that works: `mm^2`
# built from two declared `mm`, `N*mm` as Eurocode writes it, an inertia in `mm^4`. A
# convention table that says which conventions it holds is more honest than a rule that is
# wrong somewhere else.
_AUTHORITATIVE_TECHNICAL_DIMENSIONS = frozenset({
    (("[length]", -1), ("[mass]", 1), ("[time]", -2)),
})


def _is_technical(quantity) -> bool:
    """True when any part of the unit the value carries is kilogram- or tonne-force.

    `any`, for the same reason `_is_us_customary` uses it, and because the engineer
    said so directly when asked what should happen to a page that mixes the two:
    "si te los doy en ambos, elige kgf cm2".
    """
    try:
        return any(name in _TECHNICAL_UNIT_NAMES for name in quantity.units._units)
    except Exception:
        return False


# A palette is one unit per dimension, declared up front, and it beats everything that
# follows: the families, the bands, the shape rule, the technical convention. The engineer
# asked for it three times and the argument that settled it is his own -
#
#     "¿cómo sabrás tú qué es secciones o deflexiones?"
#
# It cannot be known. A span, a section depth and a deflection are one dimension, and
# every rule for telling them apart is a guess wearing a convention's clothes. So a sheet
# that declares a palette gets one unit per dimension and converts by hand where that is
# wrong, with `numeric(delta, mm)`, which the palette deliberately does not override.
#
# Keyed and spelled exactly like the family tables above, so the two read together. Same
# sorted-dimensionality key, for the same reason: `str(dimensionality)` is not stable and
# depending on it was #78.
#
# A dimension with no entry is left alone. Inventing one for everything anybody might
# reach - an angle, a temperature, a rate - is how a palette turns back into the rules it
# was brought in to replace.
_PALETTES: dict[str, dict[tuple[tuple[str, int], ...], str]] = {
    "kN": {
        (("[length]", 1),): "m",
        (("[length]", 2),): "m ** 2",
        (("[length]", 4),): "m ** 4",
        (("[length]", 1), ("[mass]", 1), ("[time]", -2)): "kN",
        (("[length]", 2), ("[mass]", 1), ("[time]", -2)): "kN * m",
        (("[length]", -1), ("[mass]", 1), ("[time]", -2)): "MPa",
        (("[mass]", 1), ("[time]", -2)): "kN / m",
        (("[mass]", 1),): "kg",
        (("[time]", 1),): "s",
        (("[time]", -1),): "1 / s",
    },
    "kgf": {
        (("[length]", 1),): "cm",
        (("[length]", 2),): "cm ** 2",
        (("[length]", 4),): "cm ** 4",
        (("[length]", 1), ("[mass]", 1), ("[time]", -2)): "kgf",
        (("[length]", 2), ("[mass]", 1), ("[time]", -2)): "kgf * cm",
        (("[length]", -1), ("[mass]", 1), ("[time]", -2)): "kgf / cm ** 2",
        (("[mass]", 1), ("[time]", -2)): "kgf / cm",
        (("[mass]", 1),): "kg",
        (("[time]", 1),): "s",
        (("[time]", -1),): "1 / s",
    },
}

# Public so the magic's `%eng_units` summary can read the units off the table
# rather than repeat them in a second place that would drift.
PALETTES = _PALETTES
PALETTE_NAMES = tuple(_PALETTES)


def _palette_unit(quantity, settings: RenderSettings) -> str | None:
    """The unit this sheet's palette fixes for that dimension, or None."""
    palette = _PALETTES.get(settings.palette)
    if not palette:
        return None
    try:
        key = tuple(sorted(quantity.dimensionality.items()))
    except Exception:
        return None
    return palette.get(key)


def _unit_family(quantity) -> tuple[str, ...]:
    """The units this dimensionality is shown in, in the system the value is already in.

    A stand-in carrying a dimensionality and no units at all reads as SI, which is both
    the default system and what the one caller that passes such an object means.
    """
    try:
        key = tuple(sorted(quantity.dimensionality.items()))
    except Exception:
        return ()
    if _is_us_customary(quantity):
        table = _US_CUSTOMARY_UNIT_FAMILIES
    elif _is_technical(quantity):
        table = _TECHNICAL_UNIT_FAMILIES
    else:
        table = _UNIT_FAMILIES
    return table.get(key, ())


def _factor_shape(quantity) -> tuple[str, ...]:
    """The dimensions a unit is spelled out of, ignoring prefix and exponent.

    `kN/mm`, `tonf/m` and `kN/m` all come out as a force and a length. `GPa*mm` comes
    out as a pressure and a length. The four are the same dimension overall and only
    this tells them apart.
    """
    try:
        registry = quantity._REGISTRY
        # `tuple(sorted(items))` and not `str(...)`. Pint renders a dimensionality in the
        # order it happens to hold it, so `kgf` prints `[length] * [mass] / [time] ** 2`
        # and `tonf` prints `[mass] * [length] / [time] ** 2` for the same dimension. Read
        # as strings they are different shapes, and a soil pressure written `tonf/m^2`
        # therefore did not match a `kgf/cm^2` family member. `kN`, `N`, `kip` and `lbf`
        # split across the two renderings too, so this was wrong for every system at once
        # and only ever showed where a family member and a value used different spellings.
        return tuple(sorted(
            tuple(sorted(registry.Unit(name).dimensionality.items()))
            for name in quantity.units._units
        ))
    except Exception:
        return ()


def _unit_is_the_engineers(quantity, settings: RenderSettings) -> bool:
    """True when the unit came from the engineer's own inputs rather than the algebra.

    A family member is *not* the engineer's in this sense: metres are the family's own
    unit, so a value in metres is subject to the family's choice. A unit outside the
    family whose factors are shaped like one of the family's came from what was typed -
    ``tonf/m``, ``kN/mm``, ``kgf*cm`` - and is kept.

    Two questions, in order, and both about the unit rather than about the number:

    1. Is it the family's own unit? Then the family chooses.
    2. Are its factors shaped like the family's? `kN/mm`, `tonf/m` and `kgf*cm` reach
       their dimension through a force, because that is how a line load or a moment is
       spelled. `GPa*mm` reaches the same dimension through a *pressure*, which is what
       `E*t` leaves behind rather than anything a person writes.

    For most of this renderer's life the second question was `_unit_terms`, which summed
    a unit's exponents and kept the value's own unit when that cost no more than the
    family's canonical member. It was the source of every tie in the seven-places series
    and it is gone. What settled that it could go was not the suite falling quiet:

    * Both jobs its own docstring claimed are done by the shape. `MPa*mm^3` - the #78
      capacity that printed `2.84e8 MPa*mm^3` for `284.30 kN*m` - is a pressure and a
      length against `kN*m`'s force and length, so the shapes differ. `mm^4` and the
      inertia family's `cm^4` are each a single length, so they match and an inertia
      written in mm^4 is still left where the engineer put it.
    * An exhaustive search over twenty base units in six composite forms against all
      three family tables finds no unit with a family member's shape and a larger count,
      which is what the dimensional equation predicts: the shape fixes which dimensions
      appear, and the exponents then follow.

    This also opened with an empty-family shortcut, unreachable because its only caller
    returns first when the family is empty. That branch went the same way, for the same
    reason recorded in `HOW-THIS-WORK-GOES-WRONG.md` section 6.
    """
    family = _unit_family(quantity)
    own = str(quantity.units)
    for name in family:
        try:
            if str(quantity.to(name).units) == own:
                return False
        except DimensionalityError:
            continue

    # `_is_technical` is inert today and kept deliberately, which is a different thing
    # from the unreachable branches section 6 says to remove. Those could not be reached
    # by any input; this one cannot change an *outcome* only because of what the other
    # two family tables happen to hold: SI and US customary name their stress units
    # (`MPa`, `psi`), so a composite's factor shape already differs from theirs and the
    # shape rule sends it on without the convention being asked. Give either table a
    # composite member and this guard starts deciding. Mutation says it is inert; the
    # tables say it is load-bearing the moment they change.
    if _is_technical(quantity):
        try:
            key = tuple(sorted(quantity.dimensionality.items()))
        except Exception:
            key = ()
        if (
            key in _AUTHORITATIVE_TECHNICAL_DIMENSIONS
            and str(quantity.units) not in settings.written_units
        ):
            return False

    own_shape = _factor_shape(quantity)
    if own_shape:
        shapes = []
        for name in family:
            try:
                shapes.append(_factor_shape(quantity.to(name)))
            except DimensionalityError:
                continue
        if shapes and own_shape not in shapes:
            return False

    return True


def _is_genuine_zero(quantity, settings: RenderSettings) -> bool:
    """Decided in the stored unit, always, and never after a conversion.

    ``zero_tolerance`` is compared against a magnitude, so it means something
    different in every unit: 1e-7 kN/mm is below a 1e-6 tolerance and 1e-4 kN/m,
    the same value, is above it. Rescaling for display must not be able to turn an
    approved zero into a number.
    """
    try:
        return abs(float(quantity.magnitude)) < settings.zero_tolerance
    except (TypeError, ValueError):
        return False


def _band_distance(magnitude):
    """How far a magnitude sits from the readable band [1, 1000). Design 4.5.

    Significant figures cannot make this choice. `0.02 m` and `20.00 mm` retain one
    figure each, so the comparison ties and the value stays in metres at a display
    resolution of 25% - EP-1. Measured over the cases that reach this function, the
    band rule is right 10 times out of 10 where counting figures is right 8.
    """
    magnitude = abs(float(magnitude))
    if magnitude == 0.0:
        return (2, 0.0)
    if 1.0 <= magnitude < 1000.0:
        return (0, 0.0)
    if magnitude < 1.0:
        return (1, abs(math.log10(magnitude)))
    return (1, math.log10(magnitude / 1000.0))


def _best_in_family(quantity, family, settings: RenderSettings, *, start=None):
    candidates = [] if start is None else [start]
    for name in family:
        try:
            candidates.append(quantity.to(name))
        except DimensionalityError:
            continue
    if not candidates:
        return quantity

    figures = [
        _significant_figures(candidate.magnitude, settings.precision)
        for candidate in candidates
    ]
    if max(figures) <= 0:
        # Below the family floor nothing gains a figure, so moving the value only
        # obscures it: 1e-6 m reads as 1.00e-6 m, not as 1.00e-3 mm. Scientific
        # notation happens where the engineer left the value. Design 4.6.
        return quantity
    # ``min`` is stable and ``start`` - the unit the value already carries - is first,
    # so a band tie keeps it.
    #
    # This was documented as inert on the grounds that every family stepped by 1000 or
    # more, which made a band tie impossible. That reason is gone: the US customary
    # length family steps by 12, and `20 ft` and `240 in` sit in the readable band
    # together. The branch is inert for a different reason, and a sturdier one - a value
    # already wearing a family member's unit costs no more unit terms than the family's
    # canonical member, so `_unit_is_the_engineers` answers True and `_display_quantity`
    # returns before ever calling this function with a `start`. Re-measured after the
    # imperial families were added, on the full suite rather than a subset: removing
    # ``start`` still changes no test. Kept as the correct behaviour for any future
    # family whose members sit closer together, and no longer credited to a step size.
    return min(candidates, key=lambda candidate: _band_distance(candidate.magnitude))


# Pint calls these dimensionless, and they are, but an angle is not a ratio anyone
# wants reduced: 30 deg is 30 deg, not 0.52.
_ANGLE_UNIT_NAMES = frozenset({"degree", "radian"})


def _is_a_dimensionless_ratio(quantity) -> bool:
    """True when the units are left over from arithmetic on a value that is a number.

    The test is "dimensionless and not an angle", not "more than two unit symbols". The
    second was measured against the same defect in a different disguise - a demand in
    `N*m` over a capacity in `kN*m` reduces to `newton/kilonewton`, two symbols - and
    would have printed `1000.00 N/kN` while calling the ratio fixed.
    """
    if not getattr(quantity, "dimensionless", False):
        return False
    # No early return for a value that is already unitless: converting one to base units
    # is its own value, so the guard an earlier draft had here survived mutation and is
    # left out rather than kept as a branch no test can tell apart from its absence.
    return str(quantity.units) not in _ANGLE_UNIT_NAMES


def _display_quantity(quantity, settings: RenderSettings, *, declared: bool):
    """Choose the unit the reader sees.

    Three cases, and the middle one is why significant figures alone are not
    enough. The P-3 deflection carries ``kN/(GPa*m)`` and renders ``5625.00``,
    which retains *more* figures than ``5.63 mm`` — so a rule that only maximised
    figures would keep the compound and leave P-3 unfixed.

    - the unit is a **family member**: choose within the family by significant
      figures, ties keeping what the value already carries, so a 5 m span stays in
      metres and an admissible deflection of ``L/300`` moves to millimetres;
    - the unit is **not** a family member but is no more complex than one: it came
      from the engineer's own inputs, as ``tonf`` does, and is kept;
    - the unit is a compound the algebra invented: replaced, whatever it shows.

    A declared unit is kept in every case, unless rendering it would leave no
    significant figure at all.

    ``declared`` means the engineer wrote this unit, not that the statement used
    ``:=``. It once meant the second, and the difference is every line whose
    right-hand side is a product of other quantities: `phiMn := 0.9*As*fy*z` declares
    a name and no unit, and used to keep `MPa*mm^3` on the strength of an operator.
    `q := 2.8*tonf/m` still keeps its tonf, which is what the flag is for.
    """
    try:
        magnitude = float(quantity.magnitude)
    except (TypeError, ValueError):
        return quantity
    # A ratio that is physically a number reads as a number. `Mu/phiMn` with a capacity
    # computed from a stress and a volume carries `kN*m/(MPa*mm^3)`, which is
    # dimensionless with a scale factor of 1e6, so the page said 9.63e-7 for a
    # demand/capacity of 0.96.
    #
    # Above the zero-tolerance return, not below it. Below looked safer - the rule that
    # a zero is decided in its stored unit exists so rescaling m to mm cannot lift an
    # approved zero out of the band - but it was measured, and a ratio of exactly zero
    # printed `0.00 kN*m/(MPa*mm^3)`, carrying the artefact unit in the one place it is
    # least defensible. That rule is about choosing between units a value could
    # reasonably wear. A dimensionless value has only one, its own number, so deciding
    # zero-ness anywhere else decides it on a scale the algebra picked by accident.
    # `_magnitude_text` still applies the tolerance, now to the honest magnitude.
    if not declared and _is_a_dimensionless_ratio(quantity):
        return quantity.to_base_units()

    # A declared palette decides, and it decides before everything below: the zero
    # tolerance, the family, the band, the shape rule. That is the whole point of it -
    # `b := 500*mm` on a kN sheet reads `0.50 m` even though `mm` is what was written,
    # because the sheet said once what its units are and meant it.
    #
    # `numeric(b, mm)` still wins, and not by a check here: the five call sites that know
    # a unit was asked for hand this function a settings with the palette cleared.
    palette_unit = _palette_unit(quantity, settings)
    if palette_unit is not None:
        try:
            return quantity.to(palette_unit)
        except DimensionalityError:
            pass

    family = _unit_family(quantity)

    # Zero-ness is decided in a unit the reader will actually see, not in whatever the
    # arithmetic left behind. The rule that a zero is judged in its stored unit is right
    # and is why this returns early at all - rescaling metres to millimetres must not
    # lift a value its author already accepted as zero back out of the band. It just has
    # to be a unit its author would recognise.
    #
    # `P*L^3/(3*E*I)` carries `kN*m^3/(MPa*mm^4)`, which is 10^9 metres, so a deflection
    # of 3.95 mm has a magnitude of 3.95e-12 and every deflection under about 100 mm fell
    # under a 1e-10 tolerance. The page said `0.00`, and a deflection check is a
    # comparison against a limit, so a wrong zero passes it.
    #
    # The same argument is already made ten lines above for a dimensionless ratio, which
    # sits above this return for exactly that reason. It had never been extended to a
    # value with a dimension.
    #
    # Three arms, because "a unit the reader will see" is three different things here and
    # the first draft used only two. `_unit_is_the_engineers` answers *False* for a family
    # member - metres are the family's own unit, so the family chooses - which left every
    # zero anyone would actually write resting on `declared` alone, and `numeric(gap)`
    # reaches this with `declared` False.
    own_is_family_member = any(
        str(quantity.to(name).units) == str(quantity.units) for name in family
    )
    if abs(magnitude) < settings.zero_tolerance and (
        declared or own_is_family_member or _unit_is_the_engineers(quantity, settings)
    ):
        return quantity

    if not family:
        return quantity

    own_figures = _significant_figures(magnitude, settings.precision)
    if declared and own_figures > 0:
        return quantity

    if _unit_is_the_engineers(quantity, settings):
        # ``tonf``, ``kN/mm``: kept unless it says nothing at all.
        return quantity if own_figures > 0 else _best_in_family(quantity, family, settings)

    # `own_is_family_member` is computed once, above the zero-tolerance return that now
    # also needs it.
    start = quantity if own_is_family_member and own_figures > 0 else None
    return _best_in_family(quantity, family, settings, start=start)


def _scientific_latex(magnitude: float, precision: int) -> str:
    exponent = int(math.floor(math.log10(abs(magnitude))))
    mantissa = magnitude / (10.0**exponent)
    # `\times`, not `\cdot`. It is the conventional mark for a power of ten, and it keeps
    # the glyph distinct from the multiplication dot that starts a wrapped product line.
    # With both as dots a continuation read `· 1/(8.00 · 10^7 mm^4)`: the same mark
    # carrying two meanings four characters apart.
    return rf"{mantissa:.{precision}f} \times 10^{{{exponent}}}"


# Above this, a fixed-decimal render stops being readable: `I_z := 80e6*mm**4` printed
# as `80000000.00`, eight zeros nobody writes or counts. The ceiling is a million rather
# than a hundred thousand because a steel modulus is written `200000 MPa`, and rendering
# that as `2.00 * 10^5` would be worse than the problem.
_FIXED_DECIMAL_CEILING = 1e6


def _magnitude_text(magnitude, settings: RenderSettings) -> str:
    """Format one magnitude, in scientific notation outside the readable band.

    Only values above ``zero_tolerance`` are owed a readable form; below it a value
    is a genuine zero by an existing approved contract and still renders as zero.

    The floor case is P-1: a value so small that a fixed-decimal render keeps none of
    its digits. `figures` rescues most of those directly now, so what is left for
    scientific notation is the value a decimal render cannot tell the truth about.

    "Cannot tell the truth" is the test, and it is not the same as "shows no digit".
    Two values that both read `0.00` at two decimals part company here:

        0.00002   ->  0.00002        exactly what it is, and the engineer's own floor
        1.05e-5   ->  1.05 x 10^-5   `0.00001` would be a different number

    So a decimal render is kept when it either reaches `figures` significant digits or
    still agrees with the value; otherwise the exponent goes back. Without the second
    half, deepening the decimals turns a rounding into a quiet lie.

    Agreement is relative and not exact, because almost nothing on a calculation page
    is exact: a period of 0.03 s arrives as 0.030000000000000002, and an equality test
    called that a lie and printed `3.00 x 10^-2` for it. The tolerance is one part in
    10^figures - the same digits the floor is trying to secure - which noise at the
    fifteenth decimal passes and a truncated 1.05e-5 does not.

    The ceiling is the same failure from the other side - every digit is kept and none
    of them can be read.
    """
    magnitude = float(magnitude)
    if magnitude == 0.0 or abs(magnitude) < settings.zero_tolerance:
        return f"{0.0:.{settings.precision}f}"
    if abs(magnitude) >= _FIXED_DECIMAL_CEILING:
        return _scientific_latex(magnitude, settings.precision)
    text = f"{magnitude:.{_decimals_for(magnitude, settings)}f}"
    # Leading zeros only. A trailing zero here was printed on purpose and is a figure:
    # `0.0300` shows three, and counting it as one sent a 0.0300394 s period back to
    # `3.00 x 10^{-2}`. `_significant_figures` strips both ends because it is asking a
    # different question - whether the value sits in a unit's natural band - and there
    # a trailing zero genuinely carries nothing.
    shown = len(text.replace(".", "").replace("-", "").lstrip("0"))
    if shown == 0:
        return _scientific_latex(magnitude, settings.precision)
    if _is_reduced(magnitude, settings) and shown < settings.figures:
        tolerance = abs(magnitude) * 10.0 ** (-settings.figures)
        if abs(float(text) - magnitude) > tolerance:
            return _scientific_latex(magnitude, settings.precision)
    return text


def _quantity_latex(
    quantity,
    precision: int | None = None,
    *,
    settings: RenderSettings | None = None,
    declared: bool = True,
) -> str:
    active_settings = settings or _DEFAULT_RENDER_SETTINGS
    if precision is not None:
        active_settings = replace(active_settings, precision=precision)

    quantity = _display_quantity(quantity, active_settings, declared=declared)
    magnitude_latex = _magnitude_text(quantity.magnitude, active_settings)

    unit_name = str(quantity.units)
    if getattr(quantity, "dimensionless", False) and unit_name == "dimensionless":
        return magnitude_latex

    unit_latex = format(quantity.units, "~L")
    return rf"{magnitude_latex}\,{unit_latex}"


def _magnitude_latex(quantity, settings: RenderSettings) -> str:
    """Format a cell whose unit was already chosen for the whole aggregate.

    Deliberately does not rescale. A matrix prints one unit outside its brackets
    and a table prints one unit in its header, so a per-cell choice here would
    leave the cells reading against a unit that is not theirs.
    """
    return _magnitude_text(quantity.magnitude, settings)


def _matrix_from_cells_latex(rows: list[list[str]]) -> str:
    body = r"\\".join(" & ".join(row) for row in rows)
    return rf"\left[\begin{{matrix}}{body}\end{{matrix}}\right]"


def _matrix_latex(matrix) -> str:
    return _latex(sp.ImmutableMatrix(matrix))


def _matrix_substitution_latex(
    matrix,
    substitutions: dict[str, object],
    settings: RenderSettings,
) -> str:
    return _NumericSubstitutionLatexPrinter(substitutions, settings).doprint(
        sp.ImmutableMatrix(matrix)
    )


def _quantity_matrix_common_unit(quantity_matrix: QuantityMatrix):
    """Return one display unit when every physical cell is mutually convertible.

    Exact dimensionless zero cells are neutral, which preserves Task 5 adaptable-zero
    semantics. A nonzero dimensionless value mixed with physical entries makes the
    matrix heterogeneous for display.
    """
    physical = [
        quantity
        for quantity in quantity_matrix
        if not getattr(quantity, "dimensionless", False)
    ]
    if not physical:
        return None, True

    common_unit = physical[0].units
    for quantity in physical[1:]:
        try:
            quantity.to(common_unit)
        except DimensionalityError:
            return None, False

    for quantity in quantity_matrix:
        if getattr(quantity, "dimensionless", False):
            if abs(float(quantity.magnitude)) >= 1e-15:
                return None, False
    return common_unit, True


def _matrix_scale_exponent(magnitudes, settings: RenderSettings) -> int:
    """A power of ten to take outside the brackets, or zero to leave the matrix alone.

    An assembled stiffness runs to six digits a cell, and a matrix is where that is worst:
    the reader is comparing entries, and the digits are what they have to see past. Every
    textbook takes the scale outside once - `K = 10^3 [ ... ]` - and that is what this
    computes.

    A multiple of three, so the reader is choosing among the prefixes they already know,
    and sized on the largest entry so the matrix reads at the scale of its own biggest
    number.

    Declined in three cases. A matrix already inside the readable band has nothing to
    gain. A matrix holding both a large entry and a small one would flatten the small one
    to `0.00`, and losing a number is worse than reading a long one - the same rule that
    decides a family member elsewhere, asked here of every cell at once. And a single
    entry has nothing to line up with: `10^3 [70.30]` is longer than `70303.22`, not
    shorter.
    """
    values = [
        abs(float(magnitude))
        for magnitude in magnitudes
        if abs(float(magnitude)) >= settings.zero_tolerance
    ]
    if len(values) < 2:
        return 0
    largest = max(values)
    # Large means unwieldy; small means unreadable, and those are different questions.
    # Above the band a matrix is all digits and the scale is worth taking out. Below it,
    # what matters is whether the number still says anything: `-0.41` reads perfectly
    # and does not want to become `10^-3 [-405.41]`, while `0.0008` shows `0.00` and
    # does. The second test is the one the family rule already uses for a single value.
    if largest < 1000.0 and _significant_figures(largest, settings.precision) > 0:
        return 0
    exponent = int(math.floor(math.log10(largest) / 3.0)) * 3
    if exponent == 0:
        return 0
    # Every cell, not just the largest. One factor serves a matrix whose entries share
    # an order of magnitude, which a stiffness matrix in consistent units does by
    # construction. Where they do not - `[517.20 kN*m, 35472.97 kN/m]` spans two orders -
    # sizing on the largest turns the smaller into `0.52` and costs it three significant
    # figures. A factor that has to damage a cell to tidy another is not taken.
    for value in values:
        if not 1.0 <= value / 10.0**exponent < 1000.0:
            return 0
    return exponent


def _quantity_matrix_latex(
    quantity_matrix: QuantityMatrix,
    settings: RenderSettings = _DEFAULT_RENDER_SETTINGS,
    *,
    declared: bool = False,
) -> str:
    """Render a matrix of quantities.

    `declared` is the same word it is everywhere else here: the cells are already in
    the unit that should be shown, so nothing is to be chosen. It is set when
    `numeric(K, unit)` named one - the engine has converted every cell to it, and
    `_aggregate_unit` would otherwise choose again and convert them back.
    """
    common_unit, homogeneous = _quantity_matrix_common_unit(quantity_matrix)
    if homogeneous and not declared:
        common_unit = _aggregate_unit(list(quantity_matrix), settings, common_unit)

    # The unit each cell will be shown in has to be settled before the scale can be,
    # because the magnitudes it is computed from are the ones the reader will see.
    shown = []
    for quantity in quantity_matrix:
        if homogeneous:
            if common_unit is not None and not getattr(quantity, "dimensionless", False):
                quantity = quantity.to(common_unit)
        else:
            # `declared=False` and not `declared`, which a mixed cell can never see as
            # True: a target unit has to be compatible with every entry - the engine
            # refuses one that is not, naming the cell - and converting them all to it
            # makes the matrix homogeneous, so a requested unit always takes the branch
            # above. Written as `declared` first; mutation reported it inert, the full
            # suite agreed, and an unreachable branch is worse than the parameter it
            # was trying to respect.
            quantity = _display_quantity(quantity, settings, declared=False)
        shown.append(quantity)
    exponent = _matrix_scale_exponent(
        [quantity.magnitude for quantity in shown], settings
    )

    rows: list[list[str]] = []

    scale = 10.0**exponent
    index = 0
    for row in range(quantity_matrix.rows):
        rendered_row: list[str] = []
        for col in range(quantity_matrix.cols):
            quantity = shown[index]
            index += 1
            if exponent:
                quantity = quantity / scale
            if homogeneous:
                rendered_row.append(_magnitude_latex(quantity, settings))
            else:
                # The unit is already settled - `_display_quantity` chose it above, with
                # `declared=False`, because a cell of a computed matrix wrote no unit.
                # The default is True, and it left every cell of a mixed-dimension
                # matrix in whatever the algebra produced: `5.17 x 10^8 GPa*mm^4/m` for
                # a 517.20 kN*m rotational stiffness.
                magnitude = _magnitude_text(quantity.magnitude, settings)
                if getattr(quantity, "dimensionless", False) and str(quantity.units) == "dimensionless":
                    rendered_row.append(magnitude)
                else:
                    rendered_row.append(
                        rf"{magnitude}\,{format(quantity.units, '~L')}"
                    )
        rows.append(rendered_row)

    matrix_latex = _matrix_from_cells_latex(rows)
    if exponent:
        # Before the brackets, the way it is written by hand: `K = 10^3 [ ... ] kN`.
        matrix_latex = rf"10^{{{exponent}}}\," + matrix_latex
    if homogeneous and common_unit is not None:
        return rf"{matrix_latex}\,{format(common_unit, '~L')}"
    return matrix_latex


def _analysis_scalar_latex(value, settings: RenderSettings) -> str:
    if hasattr(value, "magnitude") and hasattr(value, "units"):
        return _quantity_latex(value, settings=settings)
    return _latex(value)


def _matrix_shape_latex(value: MatrixShape) -> str:
    return rf"\left({value.rows}, {value.cols}\right)"


def _eigenvalue_set_latex(value: EigenvalueSet, settings: RenderSettings) -> str:
    entries = [
        rf"\lambda={_analysis_scalar_latex(entry.value, settings)},\;m={entry.multiplicity}"
        for entry in value.entries
    ]
    return r"\left\{" + r"\; ; \;".join(entries) + r"\right\}"


def _eigenvector_set_latex(value: EigenvectorSet, settings: RenderSettings) -> str:
    entries: list[str] = []
    for entry in value.entries:
        vectors: list[str] = []
        for index, vector in enumerate(entry.vectors, start=1):
            if isinstance(vector, QuantityMatrix):
                vector_latex = _quantity_matrix_latex(vector, settings)
            else:
                vector_latex = _matrix_latex(vector)
            vectors.append(rf"\mathbf{{v}}_{{{index}}}={vector_latex}")
        vector_block = r",\;".join(vectors)
        entries.append(
            rf"\lambda={_analysis_scalar_latex(entry.value, settings)},"
            rf"\;m={entry.multiplicity},\;{vector_block}"
        )
    return r"\left\{" + r"\; ; \;".join(entries) + r"\right\}"


def _value_latex(value, settings: RenderSettings) -> str:
    if isinstance(value, MatrixShape):
        return _matrix_shape_latex(value)
    if isinstance(value, EigenvalueSet):
        return _eigenvalue_set_latex(value, settings)
    if isinstance(value, EigenvectorSet):
        return _eigenvector_set_latex(value, settings)
    if isinstance(value, QuantityMatrix):
        return _quantity_matrix_latex(value, settings)
    if isinstance(value, sp.MatrixBase):
        return _matrix_latex(value)
    return _latex(value)


def _partial_polynomial_latex(evaluated_terms: tuple[tuple[int, object], ...] | None, variable: str, settings: RenderSettings = _DEFAULT_RENDER_SETTINGS) -> str | None:
    if evaluated_terms is None:
        return None

    variable_latex = _latex(sp.Symbol(variable))
    rendered: list[str] = []

    for power, coefficient in evaluated_terms:
        magnitude = float(coefficient.magnitude)
        if abs(magnitude) < settings.zero_tolerance:
            continue

        coefficient_latex = _quantity_latex(abs(coefficient), settings=settings)
        if power == 0:
            term_latex = coefficient_latex
        elif power == 1:
            term_latex = rf"{coefficient_latex}\,{variable_latex}"
        else:
            term_latex = rf"{coefficient_latex}\,{variable_latex}^{{{power}}}"

        if not rendered:
            prefix = "- " if magnitude < 0 else ""
        else:
            prefix = " - " if magnitude < 0 else " + "
        rendered.append(prefix + term_latex)

    zero_latex = f"{0.0:.{settings.precision}f}"
    return "".join(rendered) if rendered else zero_latex


def _piecewise_partial_latex(piecewise, substitutions: dict[str, object], settings: RenderSettings) -> str:
    variable_latex = _latex(sp.Symbol(piecewise.interval_variable))
    operator_latex = {
        "<": "<",
        "<=": r"\leq",
        ">": ">",
        ">=": r"\geq",
    }
    rendered = []
    for branch in piecewise.branches:
        value = branch.value
        if hasattr(value, "magnitude") and hasattr(value, "units"):
            value_latex = _quantity_latex(value, settings=settings)
        elif branch.evaluated_terms is not None:
            value_latex = _partial_polynomial_latex(
                branch.evaluated_terms,
                piecewise.interval_variable,
                settings,
            )
        else:
            value_latex = _substitution_latex(
                sp.sympify(value),
                substitutions,
                settings,
            )

        if branch.operator is None:
            rendered.append(rf"{value_latex} & \text{{otherwise}}")
            continue

        breakpoint = branch.breakpoint
        if hasattr(breakpoint, "magnitude") and hasattr(breakpoint, "units"):
            breakpoint_latex = _quantity_latex(breakpoint, settings=settings)
        else:
            breakpoint_latex = _substitution_latex(
                sp.sympify(breakpoint),
                substitutions,
                settings,
            )
        rendered.append(
            rf"{value_latex} & \text{{for}}\: "
            rf"{variable_latex} {operator_latex[branch.operator]} {breakpoint_latex}"
        )

    return r"\begin{cases} " + r" \\ ".join(rendered) + r" \end{cases}"


def _shows_as_stored(result) -> bool:
    """Was this result's unit asked for by name?

    `declared` means "keep the unit as stored", and a unit the engineer wrote into
    `numeric(expr, unit)` is the strongest case of a declared unit there is. It was the
    one case that did not get it: `convert_quantity` stored the value in exactly the
    unit asked for and the renderer then handed it to the family, which converted it
    back. `numeric(M, N*m)` printed `45.00 kN*m`.

    Narrower than it first looked. A requested unit outside every family survived by
    accident - `cm` and `inch` are one unit term each, so `_unit_is_the_engineers` kept
    them - and only a request the family also had an opinion about was overruled.
    """
    return bool(getattr(result, "unit_was_requested", False))


def _settings_for(result, settings: RenderSettings) -> RenderSettings:
    """The settings this result is shown with: the palette yields to a requested unit.

    `numeric(delta, mm)` is the whole answer to the question that decided the palette's
    shape - the renderer cannot know a length is a deflection, so the engineer says so on
    the line where it matters. A palette that overruled it would take away the only
    escape and make itself unusable on the first sheet with a deflection in it.
    """
    if _shows_as_stored(result) and settings.palette:
        return replace(settings, palette="")
    return settings


def _shown_substitutions(result, settings: RenderSettings) -> dict[str, object]:
    """The substituted values, each already converted to the unit it will be shown in.

    `_quantity_latex` takes `declared` - keep the unit as stored, or hand it to the
    family that makes it readable - and it defaults to True.
    `_NumericSubstitutionLatexPrinter._print_Symbol` never passed it, so every
    substituted value was treated as a unit the engineer wrote down, including the ones
    the algebra invented. A period derived from a circular frequency read

        T = 2 pi / (6.61 GPa^0.5*mm/(kg^0.5*m^0.5))
          = 0.0300 s

    the same quantity in two units, two lines apart, and the unreadable one in the
    middle of the derivation the reader is being asked to follow. It is also where the
    fractional unit exponents came from.

    Deciding it here rather than inside the printer is what keeps the change small: the
    printer, `_substitution_latex`, `_render_signed_term`, `_bounded_expression_rows`
    and five more would each have had to carry the set. Converting the dictionary first
    means the printer's `declared=True` becomes correct by construction - it keeps the
    unit it was handed, and the unit it is handed is already the right one.

    Only one value on a whole sheet actually turns on this: `d := 0.0105*m` is metres
    because the engineer wrote metres, and the family would make it `10.50 mm`.
    Everything else - `tonf/m`, `kN/mm`, `mm^4`, `MPa` - reads the same either way,
    which is why the set has to be right rather than large.
    """
    declared = getattr(result, "declared_names", frozenset())
    shown: dict[str, object] = {}
    for name, value in result.substitutions.items():
        if hasattr(value, "units"):
            value = _display_quantity(value, settings, declared=name in declared)
        shown[name] = value
    return shown


def _display_lhs(
    result: (
        NumericEvaluationResult
        | PartialNumericEvaluationResult
        | NumericMatrixEvaluationResult
        | PartialMatrixNumericEvaluationResult
    ),
) -> str | None:
    if result.display_name is None:
        return None
    if result.display_arguments is None:
        return _render_lhs(result.display_name, None)
    return _render_function_call_lhs(result.display_name, result.display_arguments)


def _shows_substitution(
    result: (
        NumericEvaluationResult
        | PartialNumericEvaluationResult
        | NumericMatrixEvaluationResult
        | PartialMatrixNumericEvaluationResult
    ),
) -> bool:
    """Return False for the compact result(...) presentation alias."""
    return re.match(r"^result\s*\(", result.statement.source.strip()) is None


_NUMERIC_ROW_VISUAL_BUDGET = 64.0
_COMPLETE_ROW_VISUAL_BUDGET = 104.0


def _latex_visual_width(latex: str) -> float:
    """Estimate rendered MathJax width from visual LaTeX complexity."""
    normalized = latex
    normalized = normalized.replace(r"\left", "").replace(r"\right", "")
    normalized = normalized.replace(r"\,", "").replace(r"\!", "")
    normalized = normalized.replace(r"\quad", "  ")
    normalized = normalized.replace(r"\cdot", "·")
    normalized = re.sub(r"\\mathrm\{([^{}]+)\}", r"\1", normalized)

    fraction_count = normalized.count(r"\frac")
    normalized = normalized.replace(r"\frac", "")
    normalized = re.sub(r"\\(?:displaystyle|textstyle|scriptstyle)", "", normalized)
    normalized = re.sub(r"\\[A-Za-z]+", "X", normalized)
    normalized = normalized.replace("{", "").replace("}", "")

    return float(len(normalized) + 6 * fraction_count)


def _render_signed_term(term: sp.Expr, *, substitutions: dict[str, object] | None, settings: RenderSettings, unit_literals: frozenset[str] = frozenset()) -> tuple[bool, str]:
    negative = term.could_extract_minus_sign()
    unsigned_term = -term if negative else term
    if substitutions is None:
        body = _latex(unsigned_term, unit_literals, settings)
    else:
        body = _substitution_latex(unsigned_term, substitutions, settings, unit_literals)
    return negative, body


def _adaptive_additive_rows(expression: sp.Expr, substitutions: dict[str, object] | None = None, *, visual_budget: float = _NUMERIC_ROW_VISUAL_BUDGET, settings: RenderSettings = _DEFAULT_RENDER_SETTINGS, unit_literals: frozenset[str] = frozenset()) -> list[str]:
    """Pack complete top-level additive terms into MathJax rows adaptively."""
    expression = sp.sympify(expression)
    terms = expression.as_ordered_terms() if expression.is_Add else [expression]
    rendered_terms = [_render_signed_term(term, substitutions=substitutions, settings=settings, unit_literals=unit_literals) for term in terms]

    packed: list[list[tuple[int, bool, str]]] = []
    current: list[tuple[int, bool, str]] = []
    current_width = 0.0

    for index, (negative, body) in enumerate(rendered_terms):
        sign_width = 0.0 if index == 0 and not negative else 2.0
        term_width = _latex_visual_width(body) + sign_width

        if current and current_width + term_width > visual_budget:
            packed.append(current)
            current = []
            current_width = 0.0

        current.append((index, negative, body))
        current_width += term_width

    if current:
        packed.append(current)

    rows: list[str] = []
    for row_terms in packed:
        pieces: list[str] = []
        for term_index_in_row, (global_index, negative, body) in enumerate(row_terms):
            if term_index_in_row == 0:
                if global_index == 0:
                    prefix = "- " if negative else ""
                else:
                    prefix = r"\quad - " if negative else r"\quad + "
            else:
                prefix = " - " if negative else " + "
            pieces.append(prefix + body)
        rows.append("".join(pieces))

    return rows


def _multiplicative_factor_key(term):
    denominator_factor = bool(term.is_Pow and term.exp.is_number and term.exp.is_negative)
    return (1 if denominator_factor else 0, _engineering_factor_key(term))


def _render_multiplicative_factor(
    factor: sp.Expr,
    substitutions: dict[str, object] | None,
    settings: RenderSettings,
    unit_literals: frozenset[str] = frozenset(),
) -> str:
    if substitutions is None:
        rendered = _latex(factor, unit_literals, settings)
    else:
        rendered = _substitution_latex(factor, substitutions, settings, unit_literals)
    if factor.is_Add:
        rendered = rf"\left({rendered}\right)"
    return rendered


def _bounded_product_rows(
    expression: sp.Expr,
    substitutions: dict[str, object] | None = None,
    *,
    settings: RenderSettings = _DEFAULT_RENDER_SETTINGS,
    unit_literals: frozenset[str] = frozenset(),
) -> list[str]:
    """Split one commutative product/fraction at factor boundaries for display."""
    expression = sp.sympify(expression)
    if expression.could_extract_minus_sign():
        expression = -expression
    if not expression.is_Mul:
        return []

    factors = sorted(expression.args, key=_multiplicative_factor_key)
    rendered_factors = [
        _render_multiplicative_factor(factor, substitutions, settings, unit_literals)
        for factor in factors
    ]

    rows: list[str] = []
    current = ""
    for factor_latex in rendered_factors:
        separator = "" if not current else " "
        candidate = f"{current}{separator}{factor_latex}"
        if current and _latex_visual_width(candidate) > _NUMERIC_ROW_VISUAL_BUDGET:
            rows.append(current)
            current = rf"\quad \cdot {factor_latex}"
        else:
            current = candidate

    if current:
        rows.append(current)
    return rows


def _split_overwide_terms(
    expression: sp.Expr,
    substitutions: dict[str, object] | None = None,
    *,
    settings: RenderSettings = _DEFAULT_RENDER_SETTINGS,
    unit_literals: frozenset[str] = frozenset(),
) -> list[str]:
    """Split only over-budget multiplicative terms while preserving additive signs."""
    expression = sp.sympify(expression)
    terms = expression.as_ordered_terms() if expression.is_Add else [expression]
    rows: list[str] = []

    for index, term in enumerate(terms):
        negative, body = _render_signed_term(
            term,
            substitutions=substitutions,
            settings=settings,
            unit_literals=unit_literals,
        )
        if index == 0:
            prefix = "- " if negative else ""
        else:
            prefix = r"\quad - " if negative else r"\quad + "

        if _latex_visual_width(prefix + body) <= _NUMERIC_ROW_VISUAL_BUDGET:
            rows.append(prefix + body)
            continue

        unsigned_term = -term if negative else term
        product_rows = _bounded_product_rows(
            unsigned_term,
            substitutions,
            settings=settings,
            unit_literals=unit_literals,
        )
        if not product_rows:
            rows.append(prefix + body)
            continue

        rows.append(prefix + product_rows[0])
        rows.extend(product_rows[1:])

    return rows


def _bounded_expression_rows(expression: sp.Expr, substitutions: dict[str, object] | None = None, *, settings: RenderSettings = _DEFAULT_RENDER_SETTINGS, unit_literals: frozenset[str] = frozenset()) -> list[str]:
    """Return additive rows and split overwide products/fractions at safe factor boundaries."""
    expression = sp.sympify(expression)
    rows = _adaptive_additive_rows(expression, substitutions, settings=settings, unit_literals=unit_literals)
    if all(_latex_visual_width(row) <= _NUMERIC_ROW_VISUAL_BUDGET for row in rows):
        return rows

    expanded = sp.expand(expression)
    if sp.sstr(expanded) != sp.sstr(expression):
        expanded_rows = _adaptive_additive_rows(expanded, substitutions, settings=settings, unit_literals=unit_literals)
        if max(_latex_visual_width(row) for row in expanded_rows) < max(_latex_visual_width(row) for row in rows):
            expression = expanded
            rows = expanded_rows
    if all(_latex_visual_width(row) <= _NUMERIC_ROW_VISUAL_BUDGET for row in rows):
        return rows

    split_rows = _split_overwide_terms(
        expression,
        substitutions,
        settings=settings,
        unit_literals=unit_literals,
    )
    if split_rows:
        return split_rows
    return rows


def _append_assignment_stage(rows: list[str], lhs: str | None, body_rows: list[str]) -> None:
    """Append one aligned stage without allowing a long body to enlarge the identity column."""
    if not body_rows:
        return

    if lhs is None:
        rows.append(rf" & & \displaystyle {body_rows[0]}")
        for continuation in body_rows[1:]:
            rows.append(rf" & & \displaystyle {continuation}")
        return

    candidate = rf"\displaystyle {lhs} & = & \displaystyle {body_rows[0]}"
    if _latex_visual_width(candidate) <= _COMPLETE_ROW_VISUAL_BUDGET:
        rows.append(candidate)
        for continuation in body_rows[1:]:
            rows.append(rf" & & \displaystyle {continuation}")
        return

    rows.append(rf"\displaystyle {lhs} & = &")
    for body in body_rows:
        rows.append(rf" & & \displaystyle {body}")


def _promotes_opening(
    lhs: str | None, formula_rows: list[str], first_body: str | None
) -> bool:
    """Does this evaluation's formula become the identity column of its own relation?

    Asked twice and answered once. `_relation_opening` asks in order to build the rows,
    and `_value_row_spacings` asks in order to say how many rows there will be - and
    that second question is checked against reality, which is how the first version of
    this change was caught: the spacing metadata still counted a formula stage the
    renderer had stopped emitting, and the invariant raised rather than shipping a page
    with the wrong gaps.
    """
    if lhs is not None or len(formula_rows) != 1 or first_body is None:
        return False
    return (
        _latex_visual_width(
            rf"\displaystyle {formula_rows[0]} & = & \displaystyle {first_body}"
        )
        <= _COMPLETE_ROW_VISUAL_BUDGET
    )


def _relation_opening(
    lhs: str | None,
    formula_rows: list[str],
    first_body: str | None,
    rows: list[str],
) -> str:
    """Emit the formula stage, and return what belongs in the identity column of the
    first `=` row after it.

    An evaluation with a name puts the name there and its formula beside it. An
    evaluation without one - `numeric(q*L)`, `numeric(subs(M(x), x, L/2))` - had its
    formula opened as ` & & body`, an empty identity column and no relation, which is
    what a *wrapped continuation* looks like everywhere else here. Consecutive
    statements share one aligned array, so on the reference memoria it landed directly
    under the previous statement and read as part of it:

        M(x)  =  q x L / 2 - q x^2 / 2
                 q L^2 / 8                  <- equal to what?
              =  (10.00 kN/m) (6.00 m)^2 / 8

    The expression is its own subject, so it goes where a subject goes and the next
    stage's `=` attaches to it, which is what a hand calculation does:

        q L^2 / 8  =  (10.00 kN/m) (6.00 m)^2 / 8
                   =  45.00 kN*m

    Only when the whole relation fits a row, measured with the budget
    `_append_assignment_stage` already uses for the named case. A formula too wide to
    sit beside its own value keeps the rows it had: an identity column the width of the
    page is a worse answer than the one being fixed. Multi-row formulas are declined for
    the same reason - there is no single line to promote.
    """
    if _promotes_opening(lhs, formula_rows, first_body):
        return rf"\displaystyle {formula_rows[0]}"
    _append_assignment_stage(rows, lhs, formula_rows)
    return ""


def _numeric_evaluation_rows(result: NumericEvaluationResult, settings: RenderSettings) -> list[str]:
    formula_rows = _bounded_expression_rows(
        result.symbolic_expression,
        settings=settings,
        unit_literals=result.unit_literals,
    )
    final_latex = _quantity_latex(
        result.quantity,
        settings=_settings_for(result, settings),
        declared=_shows_as_stored(result),
    )
    lhs = _display_lhs(result)

    substituted_rows: list[str] = []
    if _shows_substitution(result):
        substituted_rows = _bounded_expression_rows(
            result.symbolic_expression,
            _shown_substitutions(result, settings),
            settings=settings,
            unit_literals=result.unit_literals,
        )

    rows: list[str] = []
    opening = _relation_opening(
        lhs,
        formula_rows,
        substituted_rows[0] if substituted_rows else final_latex,
        rows,
    )
    for index, body in enumerate(substituted_rows):
        if index == 0:
            rows.append(rf"{opening} & = & \displaystyle {body}")
            opening = ""
        else:
            rows.append(rf" & & \displaystyle {body}")
    rows.append(rf"{opening} & = & \displaystyle {final_latex}")
    return rows


def _partial_numeric_evaluation_rows(result: PartialNumericEvaluationResult, settings: RenderSettings) -> list[str]:
    formula_rows = _bounded_expression_rows(
        result.symbolic_expression,
        settings=settings,
        unit_literals=result.unit_literals,
    )
    evaluated_latex = None
    if result.piecewise_evaluation is not None:
        evaluated_latex = _piecewise_partial_latex(
            result.piecewise_evaluation,
            _shown_substitutions(result, settings),
            settings,
        )
    elif len(result.unresolved_symbols) == 1:
        evaluated_latex = _partial_polynomial_latex(result.evaluated_terms, result.unresolved_symbols[0], settings)
    lhs = _display_lhs(result)

    substituted_rows: list[str] = []
    if _shows_substitution(result):
        substituted_rows = _bounded_expression_rows(
            result.symbolic_expression,
            _shown_substitutions(result, settings),
            settings=settings,
            unit_literals=result.unit_literals,
        )

    rows: list[str] = []
    opening = _relation_opening(
        lhs,
        formula_rows,
        substituted_rows[0] if substituted_rows else evaluated_latex,
        rows,
    )
    for index, body in enumerate(substituted_rows):
        if index == 0:
            rows.append(rf"{opening} & = & \displaystyle {body}")
            opening = ""
        else:
            rows.append(rf" & & \displaystyle {body}")
    if evaluated_latex is not None:
        rows.append(rf"{opening} & = & \displaystyle {evaluated_latex}")
    return rows


def _matrix_stage_rows(lhs: str | None, stages: list[str]) -> list[str]:
    if not stages:
        return []
    if lhs is None:
        rows = [rf" & & \displaystyle {stages[0]}"]
    else:
        rows = [rf"\displaystyle {lhs} & = & \displaystyle {stages[0]}"]
    rows.extend(rf" & = & \displaystyle {stage}" for stage in stages[1:])
    return rows


def _numeric_matrix_evaluation_rows(
    result: NumericMatrixEvaluationResult,
    settings: RenderSettings,
) -> list[str]:
    stages = [_matrix_latex(result.symbolic_matrix)]
    if _shows_substitution(result):
        stages.append(
            _matrix_substitution_latex(
                result.symbolic_matrix,
                _shown_substitutions(result, settings),
                settings,
            )
        )
    stages.append(_quantity_matrix_latex(result.quantity_matrix, _settings_for(result, settings), declared=_shows_as_stored(result)))
    return _matrix_stage_rows(_display_lhs(result), stages)


def _partial_matrix_numeric_evaluation_rows(
    result: PartialMatrixNumericEvaluationResult,
    settings: RenderSettings,
) -> list[str]:
    stages = [_matrix_latex(result.symbolic_matrix)]
    if _shows_substitution(result):
        stages.append(
            _matrix_substitution_latex(
                result.symbolic_matrix,
                _shown_substitutions(result, settings),
                settings,
            )
        )
    return _matrix_stage_rows(_display_lhs(result), stages)


def _standard_result_row(result: CalculationResult, settings: RenderSettings) -> str:
    rendered = render_result(result, settings=settings)
    if " = " in rendered:
        left, right = rendered.split(" = ", 1)
        return rf"\displaystyle {left} & = & \displaystyle {right}"
    return rf"\displaystyle {rendered} & &"


def _equality_stage_rows(display_input: sp.Equality, settings: RenderSettings) -> list[str]:
    """Render the equation being solved entirely in the right-hand block."""
    lhs_rows = _bounded_expression_rows(display_input.lhs, settings=settings)
    rhs_latex = _latex(display_input.rhs, settings=settings)
    rows: list[str] = []
    for index, equation_row in enumerate(lhs_rows):
        if index == len(lhs_rows) - 1:
            rows.append(rf" & & \displaystyle {equation_row} = {rhs_latex}")
        else:
            rows.append(rf" & & \displaystyle {equation_row}")
    return rows


def _load_case_rows(result, settings: RenderSettings) -> list[str]:
    """`D(x) = <expression>` - a named load case reads as the function it is."""
    lhs = _render_lhs(result.name, result.variable)
    rows: list[str] = []
    _append_assignment_stage(
        rows, lhs, _bounded_expression_rows(result.expression, settings=settings)
    )
    return rows


def _load_combination_rows(result, settings: RenderSettings) -> list[str]:
    """`U1(x) = 1.2 D(x) + 1.6 Lv(x)` - the factors, not their product with the bodies.

    Written as an ordinary definition this renders `0.6 qD x (L - x) + 0.8 qL x (L - x)`:
    the same number, and no longer a load combination. A reviewer checking 1.2 and 1.6
    against the code that requires them cannot, because the page no longer has them.
    """
    pieces: list[str] = []
    for factor, case in result.terms:
        name = _render_lhs(case, result.variable)
        negative = factor.could_extract_minus_sign()
        magnitude = -factor if negative else factor
        sign = "-" if negative else "+"
        term = (
            name
            if magnitude == 1
            else rf"{_latex(magnitude)} \, {name}"
        )
        pieces.append(term if not pieces and not negative else f"{sign} {term}")
    body = " ".join(pieces)

    rows: list[str] = []
    _append_assignment_stage(rows, _render_lhs(result.name, result.variable), [body])
    return rows


def _system_solve_rows(result: SystemSolveResult, settings: RenderSettings) -> list[str]:
    """One row per equation and one per unknown, in the sheet's own aligned array.

    This used to render its own single-column array and hand it to
    `_standard_result_row`, which splits a rendering on its first " = " and wraps the
    halves in column separators. The split landed inside the nested array, so `& = &`
    was injected into an environment declared `{l}`: the first solution picked up
    separators, the other three had none, and none of them lined up with the equations
    above. A reader sees a block that drifts left for no reason.

    Rows here mean the unknowns share the `=` column with everything else on the page,
    which is the whole point of the aligned array.
    """
    rows = [rf" & & \displaystyle {_latex(equation)}" for equation in result.equations]
    for name, value in result.solutions:
        lhs = _render_lhs(name, None)
        rows.append(
            rf"\displaystyle {lhs} & = & \displaystyle {_value_latex(value, settings)}"
        )
    rows.extend(_discard_note_rows(result.discarded))
    return rows


def _symbolic_evaluation_rows(result: EvaluationResult, settings: RenderSettings) -> list[str]:
    return _symbolic_value_rows(result, settings) + _discard_note_rows(result.discarded)


def _shown_expression(result: EvaluationResult):
    """The formula as the engineer typed it when that was kept, the computed one if not.

    Only ever shown. `result.value` stays what everything else computes with, so a
    written form cannot reach `solve`, `subs` or a numeric evaluation - it is the page
    and nothing else. The engine verifies the two agree before it hands one over.
    """
    return result.value if result.written is None else result.written


def _symbolic_value_rows(result: EvaluationResult, settings: RenderSettings) -> list[str]:
    statement = result.statement
    lhs = _render_lhs(statement.target, statement.parameters)
    if isinstance(
        result.value,
        (sp.MatrixBase, MatrixShape, EigenvalueSet, EigenvectorSet, QuantityMatrix),
    ):
        return [_standard_result_row(result, settings)]

    value = sp.sympify(_shown_expression(result))
    display_input = result.display_input

    if display_input is None or sp.sstr(display_input) == sp.sstr(value):
        value_rows = _bounded_expression_rows(value, settings=settings)
        if len(value_rows) == 1:
            standard = _standard_result_row(result, settings)
            if _latex_visual_width(standard) <= _COMPLETE_ROW_VISUAL_BUDGET:
                return [standard]
        rows: list[str] = []
        _append_assignment_stage(rows, lhs, value_rows)
        return rows

    if isinstance(display_input, sp.Equality):
        rows = _equality_stage_rows(display_input, settings)
        value_rows = _bounded_expression_rows(value, settings=settings)
        _append_assignment_stage(rows, lhs, value_rows)
        return rows

    input_latex = _latex(display_input)
    value_rows = _bounded_expression_rows(value, settings=settings)
    lhs_width = _latex_visual_width(lhs) + 3.0 if lhs is not None else 0.0
    chain_width = lhs_width + _latex_visual_width(input_latex) + sum(_latex_visual_width(row) for row in value_rows) + 6.0
    if len(value_rows) == 1 and chain_width <= _NUMERIC_ROW_VISUAL_BUDGET:
        return [_standard_result_row(result, settings)]

    rows: list[str] = []
    input_candidate = rf"\displaystyle {lhs} & = & \displaystyle {input_latex}" if lhs is not None else rf" & & \displaystyle {input_latex}"
    if _latex_visual_width(input_candidate) <= _COMPLETE_ROW_VISUAL_BUDGET:
        rows.append(input_candidate)
    else:
        if lhs is not None:
            rows.append(rf"\displaystyle {lhs} & = &")
        rows.append(rf" & & \displaystyle {input_latex}")

    for index, body in enumerate(value_rows):
        if index == 0:
            rows.append(rf" & = & \displaystyle {body}")
        else:
            rows.append(rf" & & \displaystyle {body}")
    return rows


def _display_rows(result: CalculationResult, settings: RenderSettings) -> list[str]:
    if isinstance(result, NumericMatrixEvaluationResult):
        return _numeric_matrix_evaluation_rows(result, settings)
    if isinstance(result, PartialMatrixNumericEvaluationResult):
        return _partial_matrix_numeric_evaluation_rows(result, settings)
    if isinstance(result, NumericEvaluationResult):
        return _numeric_evaluation_rows(result, settings)
    if isinstance(result, PartialNumericEvaluationResult):
        return _partial_numeric_evaluation_rows(result, settings)
    if isinstance(result, LoadCombinationResult):
        return _load_combination_rows(result, settings)
    if isinstance(result, LoadCaseResult):
        return _load_case_rows(result, settings)
    if isinstance(result, SystemSolveResult):
        return _system_solve_rows(result, settings)
    if isinstance(result, EvaluationResult):
        return _symbolic_evaluation_rows(result, settings)
    return [_standard_result_row(result, settings)]


def _stage_spacing_sequence(stage_lengths: list[int]) -> list[str]:
    """Return semantic gaps: 4 pt within one stage and 8 pt between stages."""
    spacings: list[str] = []
    row_seen = False
    for stage_length in stage_lengths:
        if stage_length <= 0:
            continue
        for row_index in range(stage_length):
            if not row_seen:
                row_seen = True
                continue
            spacings.append("8pt" if row_index == 0 else "4pt")
    return spacings


def _assignment_stage_row_count(lhs: str | None, body_rows: list[str]) -> int:
    stage_rows: list[str] = []
    _append_assignment_stage(stage_rows, lhs, body_rows)
    return len(stage_rows)


def _internal_row_spacings(
    result: CalculationResult,
    result_rows: list[str],
    settings: RenderSettings,
) -> list[str]:
    """Classify internal rows as wrapped continuations or new mathematical stages."""
    # A discard note is a stage of its own, and the branches below size only the value
    # rows. Sizing it here rather than inside each of them keeps the count honest: the
    # guard at the end of this function refuses to render a mismatch, which is the whole
    # reason a new row cannot be added anywhere without being accounted for.
    # Only the symbolic path grows a row here. A system solve renders its own array and
    # carries the note inside it, so it arrives as a single row like any other.
    note_count = (
        len(_discard_note_rows(result.discarded))
        if isinstance(result, EvaluationResult)
        else 0
    )
    if note_count:
        return (
            _value_row_spacings(result, result_rows[:-note_count], settings)
            + ["8pt"]
            + ["4pt"] * (note_count - 1)
        )
    return _value_row_spacings(result, result_rows, settings)


def _value_row_spacings(
    result: CalculationResult,
    result_rows: list[str],
    settings: RenderSettings,
) -> list[str]:
    if len(result_rows) <= 1:
        return []

    if isinstance(result, (LoadCaseResult, LoadCombinationResult)):
        return _stage_spacing_sequence([len(result_rows)])

    if isinstance(result, SystemSolveResult):
        stage_lengths = [len(result.equations), len(result.solutions)]
        notes = len(_discard_note_rows(result.discarded))
        if notes:
            stage_lengths.append(notes)
        spacings = _stage_spacing_sequence(stage_lengths)
        if len(spacings) != len(result_rows) - 1:
            raise RuntimeError(
                "renderer semantic spacing metadata does not match rendered row count"
            )
        return spacings

    if isinstance(result, NumericMatrixEvaluationResult):
        stage_lengths = [1, 1]
        if _shows_substitution(result):
            stage_lengths.insert(1, 1)

    elif isinstance(result, PartialMatrixNumericEvaluationResult):
        stage_lengths = [1]
        if _shows_substitution(result):
            stage_lengths.append(1)

    elif isinstance(result, NumericEvaluationResult):
        formula_rows = _bounded_expression_rows(
            result.symbolic_expression,
            settings=settings,
        )
        substituted_rows = []
        if _shows_substitution(result):
            substituted_rows = _bounded_expression_rows(
                result.symbolic_expression,
                _shown_substitutions(result, settings),
                settings=settings,
            )
        final_latex = _quantity_latex(
            result.quantity,
            settings=_settings_for(result, settings),
            declared=_shows_as_stored(result),
        )
        lhs = _display_lhs(result)
        first_body = substituted_rows[0] if substituted_rows else final_latex
        stage_lengths = [
            0
            if _promotes_opening(lhs, formula_rows, first_body)
            else _assignment_stage_row_count(lhs, formula_rows)
        ]
        if substituted_rows:
            stage_lengths.append(len(substituted_rows))
        stage_lengths.append(1)

    elif isinstance(result, PartialNumericEvaluationResult):
        formula_rows = _bounded_expression_rows(
            result.symbolic_expression,
            settings=settings,
        )
        substituted_rows = []
        if _shows_substitution(result):
            substituted_rows = _bounded_expression_rows(
                result.symbolic_expression,
                _shown_substitutions(result, settings),
                settings=settings,
            )
        evaluated_latex = None
        if result.piecewise_evaluation is not None:
            evaluated_latex = _piecewise_partial_latex(
                result.piecewise_evaluation,
                _shown_substitutions(result, settings),
                settings,
            )
        elif len(result.unresolved_symbols) == 1:
            evaluated_latex = _partial_polynomial_latex(
                result.evaluated_terms,
                result.unresolved_symbols[0],
                settings,
            )
        lhs = _display_lhs(result)
        first_body = substituted_rows[0] if substituted_rows else evaluated_latex
        stage_lengths = [
            0
            if _promotes_opening(lhs, formula_rows, first_body)
            else _assignment_stage_row_count(lhs, formula_rows)
        ]
        if substituted_rows:
            stage_lengths.append(len(substituted_rows))
        if evaluated_latex is not None:
            stage_lengths.append(1)

    elif isinstance(result, EvaluationResult):
        statement = result.statement
        lhs = _render_lhs(statement.target, statement.parameters)
        value = sp.sympify(_shown_expression(result))
        display_input = result.display_input

        if display_input is None or sp.sstr(display_input) == sp.sstr(value):
            stage_lengths = [len(result_rows)]
        elif isinstance(display_input, sp.Equality):
            value_rows = _bounded_expression_rows(value, settings=settings)
            stage_lengths = [
                len(_equality_stage_rows(display_input, settings)),
                _assignment_stage_row_count(lhs, value_rows),
            ]
        else:
            input_latex = _latex(display_input)
            input_candidate = (
                rf"\displaystyle {lhs} & = & \displaystyle {input_latex}"
                if lhs is not None
                else rf" & & \displaystyle {input_latex}"
            )
            input_stage_length = 1
            if _latex_visual_width(input_candidate) > _COMPLETE_ROW_VISUAL_BUDGET:
                input_stage_length += 1 if lhs is not None else 0
            value_rows = _bounded_expression_rows(value, settings=settings)
            stage_lengths = [input_stage_length, len(value_rows)]

    else:
        stage_lengths = [len(result_rows)]

    spacings = _stage_spacing_sequence(stage_lengths)
    expected = len(result_rows) - 1
    if len(spacings) != expected:
        raise RuntimeError(
            "renderer semantic spacing metadata does not match rendered row count"
        )
    return spacings


def _opens_by_repeating(result_rows: list[str], previous_rows: list[str] | None) -> bool:
    """True when this block's first row is the row above it, character for character.

    `M = q*L^2/8` followed by `numeric(M)` printed the formula twice: once as the
    definition, once as the opening stage of the evaluation. `## v0.23.2 an equation is
    written once` fixed the same repeat for `solve`, using a different test - "the
    argument is a name already bound to an equation". Copying that here would be wrong,
    because an evaluation written some way below its definition needs that row: it is
    the only thing on the page saying which formula is being evaluated.

    Comparing rendered rows says exactly what is wrong and nothing more. It cannot
    over-apply to a formula that reads differently, to an evaluation of an inline
    expression, which has no left-hand side to match, or to one whose definition is not
    immediately above.

    A single-row block is never dropped. Two identical definitions in a row are a
    sheet's own business, and swallowing the second is a worse answer than printing it.
    """
    return (
        previous_rows is not None
        and len(result_rows) > 1
        and result_rows[0] == previous_rows[-1]
    )


def render_aligned_results(results: list[CalculationResult], *, settings: RenderSettings | None = None) -> str:
    """Render all calculation groups with one consistent MathJax array layout."""
    if not results:
        return ""

    active_settings = settings or _DEFAULT_RENDER_SETTINGS
    rows: list[str] = []
    previous_rows: list[str] | None = None
    for result_index, result in enumerate(results):
        result_rows = _display_rows(result, active_settings)

        # Spacings are computed from the whole block, before anything is dropped. They
        # correspond to `result_rows[1:]`, and `_internal_row_spacings` refuses a
        # mismatched count - which is exactly the guard that would fire if this were
        # measured against a shortened list instead.
        internal_spacings = _internal_row_spacings(
            result,
            result_rows,
            active_settings,
        )

        if _opens_by_repeating(result_rows, previous_rows):
            # The definition becomes the opening of the derivation rather than being
            # said twice. Every row after the first already carries an empty left-hand
            # side, so the array's alignment needs nothing else, and the separator
            # becomes the stage spacing this block would have used internally.
            for spacing, continuation_row in zip(internal_spacings, result_rows[1:]):
                rows.append(rf"\\[{spacing}]")
                rows.append(continuation_row)
            # The whole block, not the tail that was emitted. Only `[-1]` is ever read
            # and it is the same either way, so this cannot be observed: setting it to
            # None here changes no test. Kept because it is what the name says - the
            # rows of the block before this one - rather than for a result it produces.
            previous_rows = result_rows
            continue

        if result_index:
            spacing = "16pt" if result.statement.blank_before else "8pt"
            rows.append(rf"\\[{spacing}]")
        rows.append(result_rows[0])

        for spacing, continuation_row in zip(
            internal_spacings,
            result_rows[1:],
        ):
            rows.append(rf"\\[{spacing}]")
            rows.append(continuation_row)

        previous_rows = result_rows

    body = " ".join(rows)
    return rf"\hspace{{0.2em}}\begin{{array}}{{lcl}} {body} \end{{array}}"


def _table_unit_text(unit) -> str:
    if str(unit) == "dimensionless":
        return ""
    return format(unit, "~P")


def _table_header(label: str, unit) -> str:
    safe_label = escape(label)
    unit_text = _table_unit_text(unit)
    if not unit_text:
        return safe_label
    return f"{safe_label} [{escape(unit_text)}]"


def _in_unit(quantity, unit, settings: RenderSettings):
    """Convert for display, leaving dimensionless zeros and mismatches alone.

    A value that is a genuine zero in its stored unit is zeroed before conversion,
    so it cannot cross ``zero_tolerance`` on the way. See ``_is_genuine_zero``.
    """
    if unit is None or getattr(quantity, "dimensionless", False):
        return quantity
    if _is_genuine_zero(quantity, settings):
        quantity = quantity * 0.0
    try:
        return quantity.to(unit)
    except DimensionalityError:
        return quantity


def _table_magnitude(quantity, settings: RenderSettings) -> str:
    """A table column carries its unit in the header, so the unit is chosen once
    for the column and this only formats. See ``_aggregate_unit``."""
    return _magnitude_text(quantity.magnitude, settings)


def _aggregate_unit(quantities, settings: RenderSettings, fallback):
    """One unit for a whole table column or matrix, never one per cell.

    Scored by the significant figures the column keeps in total, so a single large
    value cannot drag the whole column into a unit that flattens the rest. Ties
    keep the unit the values already carry.
    """
    physical = [
        quantity
        for quantity in quantities
        if quantity is not None and not getattr(quantity, "dimensionless", False)
    ]
    if not physical or fallback is None:
        return fallback

    # The second of the two places a display unit is chosen. A palette that reached only
    # scalars would leave a frame analysis half converted, its matrices in whatever the
    # algebra left and its scalars in the declared units.
    palette_unit = _palette_unit(physical[0], settings)
    if palette_unit is not None:
        # A Pint unit, not the table's string: this returns the unit the whole matrix is
        # printed with, and the printer formats it. The family path returns one too.
        try:
            return physical[0].to(palette_unit).units
        except DimensionalityError:
            pass

    family = _unit_family(physical[0])
    if not family:
        return fallback
    if _unit_is_the_engineers(physical[0], settings) and all(
        _is_genuine_zero(quantity, settings)
        or _significant_figures(quantity.to(fallback).magnitude, settings.precision) > 0
        for quantity in physical
    ):
        # kN/mm is what the engineer typed and every cell still says something in it.
        return fallback

    def score(unit):
        total = 0.0
        for quantity in physical:
            try:
                converted = quantity.to(unit)
            except DimensionalityError:
                return None
            if abs(float(converted.magnitude)) < settings.zero_tolerance:
                continue
            band, distance = _band_distance(converted.magnitude)
            total += band + distance
        return total

    best_unit = fallback
    # No seed. The fallback used to start as champion and a strict `<` then handed it
    # every tie - and `GPa*mm^2/m` ties with `kN/m` always, because they are the same
    # unit under two names. An assembled stiffness matrix read `70303.22 GPa*mm^2/m`
    # while the scalar path replaced that very expression with `kN/m`: the same value,
    # two answers, decided by whether it sat in a matrix.
    #
    # The engineer's own unit is not defended by this seed and never was - the early
    # return above is what keeps `tonf/m`. Seeding the fallback's score as well was
    # measured against `tonf/m` matrices with and without a cell that shows no figures,
    # and changed nothing, so it is not here.
    best_score = None
    for name in family:
        candidate_score = score(name)
        if candidate_score is not None and (
            best_score is None or candidate_score < best_score
        ):
            best_unit, best_score = physical[0].to(name).units, candidate_score
    return best_unit


def render_table(
    result: TableResult,
    *,
    settings: RenderSettings | None = None,
) -> str:
    """Render a unit-aware engineering table as compact scoped HTML."""
    active_settings = settings or _DEFAULT_RENDER_SETTINGS
    point_unit = _aggregate_unit(result.point_values, active_settings, result.point_unit)
    column_units = [
        _aggregate_unit(column.values, active_settings, column.unit)
        for column in result.columns
    ]
    headers = [
        _table_header(result.variable, point_unit),
        *(
            _table_header(column.display_label, unit)
            for column, unit in zip(result.columns, column_units)
        ),
    ]
    header_html = "".join(f"<th>{header}</th>" for header in headers)

    rows: list[str] = []
    for row_index, point in enumerate(result.point_values):
        cells = [_table_magnitude(_in_unit(point, point_unit, active_settings), active_settings)]
        cells.extend(
            _table_magnitude(
                _in_unit(column.values[row_index], unit, active_settings), active_settings
            )
            for column, unit in zip(result.columns, column_units)
        )
        rows.append(
            "<tr>"
            + "".join(f"<td>{cell}</td>" for cell in cells)
            + "</tr>"
        )

    body_html = "".join(rows)
    return (
        '<style>'
        '.engcalc-table{margin:0.35rem 0 0.55rem 0;overflow-x:auto;}'
        '.engcalc-table table{border-collapse:collapse;font-size:0.92rem;line-height:1.35;}'
        '.engcalc-table th,.engcalc-table td{'
        'padding:0.28rem 0.62rem;border-bottom:1px solid rgba(127,127,127,0.20);'
        'text-align:right;white-space:nowrap;}'
        '.engcalc-table th{font-weight:600;border-bottom:1px solid rgba(127,127,127,0.42);}'
        '.engcalc-table th:first-child,.engcalc-table td:first-child{text-align:left;}'
        '</style>'
        '<div class="engcalc-table"><table>'
        f'<thead><tr>{header_html}</tr></thead>'
        f'<tbody>{body_html}</tbody>'
        '</table></div>'
    )



CharacteristicResult = RootsResult | IntersectionsResult | ExtremaResult | InequalityResult

# Results that are their own HTML block rather than a row in the aligned LaTeX array.
# `render_result` returns finished HTML for these, so anything that drops one into
# `render_aligned_results` embeds a <div> inside \begin{array} and the reader sees the
# markup as text. That is exactly what a notebook showed for `governing(...)` and
# `summary()`, in every release since 0.19.0, while the contracts stayed green by
# calling the renderers directly.
HtmlBlockResult = SummaryResult | GoverningResult


def _characteristic_role_text(role: str) -> str:
    return role.replace("_", " ")


def _characteristic_math(latex: str) -> str:
    return rf"\({latex}\)"


def _characteristic_quantity_math(quantity, settings: RenderSettings) -> str:
    return _characteristic_math(_quantity_latex(quantity, settings=settings))


def _characteristic_symbolic_math(value) -> str:
    return _characteristic_math(_latex(value))


def _characteristic_point_coordinate(
    point: CharacteristicPoint,
    variable: str,
    settings: RenderSettings,
) -> str:
    variable_html = _characteristic_symbolic_math(sp.Symbol(variable))
    if point.provenance == "numeric":
        return (
            f"{variable_html} ≈ "
            f"{_characteristic_quantity_math(point.x_quantity, settings)}"
        )

    symbolic = _characteristic_symbolic_math(point.x_symbolic)
    evaluated = _characteristic_quantity_math(point.x_quantity, settings)
    return f"{variable_html} = {symbolic} ({evaluated})"


def _characteristic_point_value(
    point: CharacteristicPoint,
    settings: RenderSettings,
) -> str | None:
    if point.value_symbolic is None and point.value_quantity is None:
        return None
    if point.provenance == "numeric" or point.value_symbolic is None:
        if point.value_quantity is None:
            return None
        return "value ≈ " + _characteristic_quantity_math(point.value_quantity, settings)

    symbolic = _characteristic_symbolic_math(point.value_symbolic)
    if point.value_quantity is None:
        return "value = " + symbolic
    evaluated = _characteristic_quantity_math(point.value_quantity, settings)
    return f"value = {symbolic} ({evaluated})"


def _characteristic_interval_text(
    interval: CharacteristicInterval,
    settings: RenderSettings,
) -> str:
    left = "[" if interval.lower_closed else "("
    right = "]" if interval.upper_closed else ")"
    lower = _quantity_latex(interval.lower_quantity, settings=settings)
    upper = _quantity_latex(interval.upper_quantity, settings=settings)
    return _characteristic_math(rf"{left}{lower},\;{upper}{right}")


def _characteristic_heading(result: CharacteristicResult) -> str:
    if isinstance(result, InequalityResult):
        return "Where " + escape(result.variable) + " satisfies the inequality"
    if isinstance(result, RootsResult):
        return f"Roots — {escape(result.display_label)}"
    if isinstance(result, IntersectionsResult):
        return (
            "Intersections — "
            f"{escape(result.left_label)} / {escape(result.right_label)}"
        )
    return f"Extrema — {escape(result.display_label)}"


def render_characteristic_result(
    result: CharacteristicResult,
    *,
    settings: RenderSettings | None = None,
) -> str:
    """Render one standalone exact-characteristic result as compact HTML/MathJax."""
    active_settings = settings or _DEFAULT_RENDER_SETTINGS
    domain = (
        _characteristic_quantity_math(result.lower_quantity, active_settings)
        + " to "
        + _characteristic_quantity_math(result.upper_quantity, active_settings)
    )

    rows: list[str] = []
    for point in result.points:
        parts = [
            _characteristic_point_coordinate(
                point,
                result.variable,
                active_settings,
            )
        ]
        value_text = _characteristic_point_value(point, active_settings)
        if value_text is not None and not isinstance(result, RootsResult):
            parts.append(value_text)
        if point.roles:
            parts.append(
                ", ".join(_characteristic_role_text(role) for role in point.roles)
            )
        if point.side != "at":
            parts.append(escape(point.side))
        rows.append("<div class=\"engcalc-characteristic-row\">" + " · ".join(parts) + "</div>")

    for interval in result.intervals:
        interval_text = _characteristic_interval_text(interval, active_settings)
        if isinstance(result, InequalityResult) or interval.role == "satisfies":
            text = f"{escape(result.variable)} in {interval_text}"
        elif isinstance(result, RootsResult) or interval.role == "roots":
            text = f"all x in {interval_text}"
        elif isinstance(result, IntersectionsResult) or interval.role == "coincident":
            text = f"coincident on {interval_text}"
        else:
            role = escape(_characteristic_role_text(interval.role))
            text = f"{role} on {interval_text}"
            if interval.value_quantity is not None:
                text += (
                    " · value = "
                    + _characteristic_quantity_math(
                        interval.value_quantity,
                        active_settings,
                    )
                )
        rows.append(f'<div class="engcalc-characteristic-row">{text}</div>')

    if isinstance(result, ExtremaResult):
        if result.unbounded_above:
            rows.append('<div class="engcalc-characteristic-row">unbounded above</div>')
        if result.unbounded_below:
            rows.append('<div class="engcalc-characteristic-row">unbounded below</div>')

    if not rows:
        rows.append('<div class="engcalc-characteristic-row">no finite characteristic points</div>')

    return (
        '<style>'
        '.engcalc-characteristics{margin:0.35rem 0 0.55rem 0;'
        'font-size:0.94rem;line-height:1.45;}'
        '.engcalc-characteristics-title{font-weight:600;margin-bottom:0.15rem;}'
        '.engcalc-characteristics-domain{opacity:0.78;margin-bottom:0.18rem;}'
        '.engcalc-characteristic-row{margin:0.08rem 0;}'
        '</style>'
        '<div class="engcalc-characteristics">'
        f'<div class="engcalc-characteristics-title">{_characteristic_heading(result)}</div>'
        f'<div class="engcalc-characteristics-domain">Domain: {domain}</div>'
        + "".join(rows)
        + '</div>'
    )

_ASSUMPTION_RELATIONS = {
    "positive": ">",
    "nonnegative": r"\geq",
    "negative": "<",
    "nonpositive": r"\leq",
}


def _discard_note_rows(discarded) -> list[str]:
    """Show what `assume` ruled out, as its own row.

    A discard the reader cannot see is indistinguishable from a solver that only ever
    found one answer, and the difference matters: the second is arithmetic, the first
    is a decision the engineer made on the line above.
    """
    if discarded is None:
        return []
    condition = (
        rf"{_render_lhs(discarded.variable, None)} "
        rf"{_ASSUMPTION_RELATIONS[discarded.condition]} 0"
    )
    values = r",\;\; ".join(_latex(value) for value in discarded.values)
    return [rf" & & \displaystyle \text{{discarded by }} {condition}:\;\; {values}"]


def render_assumption_result(result: AssumptionResult) -> str:
    """As given data, which is what it is: `L > 0,\\; E > 0`."""
    parts = [
        rf"{_render_lhs(name, None)} {_ASSUMPTION_RELATIONS[keyword]} 0"
        for name, keyword in result.assumptions
    ]
    return r",\; ".join(parts)


def render_governing_result(
    result: GoverningResult,
    *,
    settings: RenderSettings | None = None,
) -> str:
    """One row per interval: the span, then the response that governs it.

    HTML rather than a MathJax array, to match how the other standalone analyses -
    roots, extrema, intersections - already present themselves. This is a table of
    intervals, and it is read as one.
    """
    active_settings = settings or _DEFAULT_RENDER_SETTINGS
    rows: list[str] = []
    for interval in result.intervals:
        span = (
            _characteristic_quantity_math(interval.lower_quantity, active_settings)
            + " to "
            + _characteristic_quantity_math(interval.upper_quantity, active_settings)
        )
        rows.append(
            f"<tr><td>{span}</td><td>{escape(interval.label)}</td></tr>"
        )
    body = "".join(rows)
    return (
        '<div class="engcalc-characteristic">'
        f"<div><strong>Governing — {escape(result.variable)}</strong></div>"
        f"<table><tbody>{body}</tbody></table></div>"
    )


def render_summary_result(
    result: SummaryResult,
    *,
    settings: RenderSettings | None = None,
) -> str:
    """The reported values, in the order they were first marked.

    HTML, like the tables and the standalone analyses, because that is what it is: a
    short table the reader looks at instead of scrolling back through the working.
    """
    active_settings = settings or _DEFAULT_RENDER_SETTINGS
    # The name as mathematics and the value with `declared=False`, both to agree with
    # the line that produced them. A reported value is a computed one, and `numeric(...)`
    # shows a computed value in the unit of its own dimension: rendering it as declared
    # put `0.02 m` in the summary two lines under `20.00 mm` in the working, for the same
    # quantity. The name was plain text for the same reason - nobody checked the two
    # against each other, because nobody had seen them side by side.
    rows = "".join(
        f"<tr><td>{_characteristic_math(_render_lhs(name, None))}</td>"
        f"<td>{_characteristic_math(_quantity_latex(quantity, settings=active_settings, declared=False))}</td></tr>"
        for name, quantity in result.entries
    )
    return (
        '<div class="engcalc-characteristic">'
        "<div><strong>Summary</strong></div>"
        f"<table><tbody>{rows}</tbody></table></div>"
    )


def render_result(result: CalculationResult, *, settings: RenderSettings | None = None) -> str:
    if isinstance(result, SummaryResult):
        return render_summary_result(result, settings=settings)
    if isinstance(result, GoverningResult):
        return render_governing_result(result, settings=settings)
    if isinstance(result, AssumptionResult):
        return render_assumption_result(result)
    if isinstance(result, SystemSolveResult):
        raise TypeError(
            "render_result does not support system solve results; they are rows in the "
            "aligned array, and flattening one to a string is what misaligned them"
        )
    if isinstance(result, (RootsResult, IntersectionsResult, ExtremaResult)):
        raise TypeError(
            "render_result does not support characteristic results; "
            "use render_characteristic_result"
        )

    active_settings = settings or _DEFAULT_RENDER_SETTINGS

    if isinstance(result, NumericAssignmentResult):
        lhs = _render_lhs(result.statement.target, None)
        # `declared` asks whether the engineer wrote this unit, not whether the line
        # used `:=`. The two agree on `q := 2.8*tonf/m` and part company on
        # `phiMn := 0.9*As*fy*z`, where the units came from three stored values and the
        # statement declared only a name.
        return rf"{lhs} = {_quantity_latex(result.quantity, settings=active_settings, declared=bool(result.written_units))}"

    if isinstance(result, PartialMatrixNumericEvaluationResult):
        stages = [_matrix_latex(result.symbolic_matrix)]
        if _shows_substitution(result):
            stages.append(
                _matrix_substitution_latex(
                    result.symbolic_matrix,
                    _shown_substitutions(result, active_settings),
                    active_settings,
                )
            )
        right = " = ".join(stages)
        lhs = _display_lhs(result)
        return rf"{lhs} = {right}" if lhs is not None else right

    if isinstance(result, NumericMatrixEvaluationResult):
        stages = [_matrix_latex(result.symbolic_matrix)]
        if _shows_substitution(result):
            stages.append(
                _matrix_substitution_latex(
                    result.symbolic_matrix,
                    _shown_substitutions(result, active_settings),
                    active_settings,
                )
            )
        stages.append(_quantity_matrix_latex(result.quantity_matrix, _settings_for(result, active_settings), declared=_shows_as_stored(result)))
        right = " = ".join(stages)
        lhs = _display_lhs(result)
        return rf"{lhs} = {right}" if lhs is not None else right

    if isinstance(result, PartialNumericEvaluationResult):
        formula_latex = _latex(result.symbolic_expression)
        evaluated_latex = None
        if result.piecewise_evaluation is not None:
            evaluated_latex = _piecewise_partial_latex(
                result.piecewise_evaluation,
                _shown_substitutions(result, active_settings),
                active_settings,
            )
        elif len(result.unresolved_symbols) == 1:
            evaluated_latex = _partial_polynomial_latex(result.evaluated_terms, result.unresolved_symbols[0], active_settings)

        chain = [formula_latex]
        if _shows_substitution(result):
            chain.append(
                _substitution_latex(
                    result.symbolic_expression,
                    _shown_substitutions(result, active_settings),
                    active_settings,
                )
            )
        if evaluated_latex is not None:
            chain.append(evaluated_latex)
        right = " = ".join(chain)

        if result.display_name is not None:
            if result.display_arguments is None:
                lhs = _render_lhs(result.display_name, None)
            else:
                lhs = _render_function_call_lhs(result.display_name, result.display_arguments)
            return rf"{lhs} = {right}"
        return right

    if isinstance(result, NumericEvaluationResult):
        formula_latex = _latex(result.symbolic_expression)
        final_latex = _quantity_latex(
            result.quantity,
            settings=_settings_for(result, active_settings),
            declared=_shows_as_stored(result),
        )
        chain = [formula_latex]
        if _shows_substitution(result):
            chain.append(
                _substitution_latex(
                    result.symbolic_expression,
                    _shown_substitutions(result, active_settings),
                    active_settings,
                )
            )
        chain.append(final_latex)
        right = " = ".join(chain)
        if result.display_name is not None:
            if result.display_arguments is None:
                lhs = _render_lhs(result.display_name, None)
            else:
                lhs = _render_function_call_lhs(result.display_name, result.display_arguments)
            return rf"{lhs} = {right}"
        return right

    statement = result.statement
    lhs = _render_lhs(statement.target, statement.parameters)
    value_latex = _value_latex(_shown_expression(result), active_settings)

    if lhs is None:
        if result.display_input is not None:
            return rf"{_latex(result.display_input)} = {value_latex}"
        return value_latex

    if result.display_input is not None:
        input_latex = _latex(result.display_input)
        if sp.sstr(result.display_input) != sp.sstr(_shown_expression(result)):
            return rf"{lhs} = {input_latex} = {value_latex}"
    return rf"{lhs} = {value_latex}"


def _render_function_call_lhs(name: str, arguments: tuple) -> str:
    if not isinstance(arguments, tuple):
        arguments = (arguments,)
    name_latex = _latex(sp.Symbol(name))
    argument_latex = ", ".join(_latex(argument) for argument in arguments)
    return rf"{name_latex}\left({argument_latex}\right)"


def _render_lhs(
    target: str | None,
    parameters: tuple[str, ...] | str | None,
) -> str | None:
    if target is None:
        return None
    if target.startswith("Sigma_") and len(target) > len("Sigma_"):
        quantity = target[len("Sigma_"):]
        target_latex = rf"\Sigma {_latex(sp.Symbol(quantity))}"
    else:
        target_latex = _latex(sp.Symbol(target))
    if parameters is None:
        return target_latex
    if isinstance(parameters, str):
        parameters = (parameters,)
    parameter_latex = ", ".join(
        _latex(sp.Symbol(parameter)) for parameter in parameters
    )
    return rf"{target_latex}\left({parameter_latex}\right)"


_HELP_STYLE = (
    "<style>"
    ".engcalc-help{margin:0.35rem 0 0.55rem 0;font-size:0.94rem;line-height:1.5;}"
    ".engcalc-help code{background:rgba(127,127,127,0.12);padding:0.05rem 0.25rem;"
    "border-radius:3px;}"
    ".engcalc-help-name{font-weight:600;font-size:1.02rem;}"
    ".engcalc-help-summary{margin:0.1rem 0 0.35rem 0;}"
    ".engcalc-help-heading{font-weight:600;margin:0.4rem 0 0.1rem 0;}"
    ".engcalc-help-arg{margin:0.05rem 0 0.05rem 1.1rem;}"
    ".engcalc-help-example{margin:0.15rem 0 0 0;white-space:pre;"
    "background:rgba(127,127,127,0.10);padding:0.4rem 0.6rem;border-radius:4px;"
    "overflow-x:auto;}"
    ".engcalc-help-row{margin:0.08rem 0;}"
    "</style>"
)


def render_call_help(entry) -> str:
    """One call's forms, what goes in each slot, and an example that runs."""
    forms = "".join(
        f'<div class="engcalc-help-row"><code>{escape(form)}</code></div>'
        for form in entry.forms
    )
    arguments = "".join(
        f'<div class="engcalc-help-arg"><code>{escape(name)}</code> \u2014 {escape(meaning)}</div>'
        for name, meaning in entry.arguments
    )
    argument_block = (
        f'<div class="engcalc-help-heading">Arguments</div>{arguments}'
        if arguments
        else ""
    )
    return (
        _HELP_STYLE
        + '<div class="engcalc-help">'
        + f'<div class="engcalc-help-name">{escape(entry.name)}</div>'
        + f'<div class="engcalc-help-summary">{escape(entry.summary)}</div>'
        + forms
        + argument_block
        + '<div class="engcalc-help-heading">Example</div>'
        + f'<div class="engcalc-help-example">{escape(entry.example)}</div>'
        + "</div>"
    )


def render_call_index(entries) -> str:
    """Every call with its first form, for `%eng_help` with no argument."""
    rows = "".join(
        f'<div class="engcalc-help-row"><code>{escape(entry.forms[0])}</code>'
        f" \u2014 {escape(entry.summary)}</div>"
        for entry in entries
    )
    return (
        _HELP_STYLE
        + '<div class="engcalc-help">'
        + '<div class="engcalc-help-name">EngCalc calls</div>'
        + '<div class="engcalc-help-summary">'
        + "%eng_help &lt;name&gt; for the arguments and an example."
        + "</div>"
        + rows
        + "</div>"
    )
