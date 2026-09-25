r"""A kept name stays a name inside a function of the sheet.

    keep f_cw = 0.85*fc
    As_req(Mu) = f_cw*b*d/fy*(1 - sqrt(1 - 2*Mu/(phi*b*d^2*f_cw)))

printed `0.85 b d fc (1 - sqrt(1 - 2.35 Mu/(fc phi b d^2)))/fy`: `f_cw` expanded and
Whitney's 0.85 folded into 2/0.85 = 2.35 - the defect #310 fixed for `min` and `max`, still
there in a function, because a function's definition was never offered the formula as it
was written. Found writing `tools/portico_diseno.eng` on 2026-09-24; dealt with among the
pending points he asked for (*"abarques todos esos puntos pendientes"*).

Only a function that reaches a kept name is written as typed: every other function prints
as it always has, so no page moves.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic

VALUES = (
    "fc := 210*kgf/cm^2\nfy := 4200*kgf/cm^2\nb := 30*cm\nd := 44*cm\nphi := 0.9\n"
    "keep f_cw = 0.85*fc\n"
)
FUNCTION = "As_req(Mu) = f_cw*b*d/fy*(1 - sqrt(1 - 2*Mu/(phi*b*d^2*f_cw)))\n"


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str) -> tuple[str, str]:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            magic.EngMagics().eng("", VALUES + source)
        return " ".join(item.data for item in captured if isinstance(item, Math)), console.getvalue()

    return run


def row(page: str, head: str) -> str:
    return page.split(head + r" & = & \displaystyle ", 1)[1].split(r"\\", 1)[0]


def test_the_kept_name_stays_in_the_definition(sheet):
    page, console = sheet(FUNCTION)
    assert not console, console
    definition = row(page, r"\mathrm{As}_{req}\left(\mathrm{Mu}\right)")
    assert "f_{cw}" in definition, definition
    assert "2.35" not in definition and "0.85" not in definition, definition


def test_the_value_is_the_same(sheet):
    page, console = sheet(FUNCTION + "As_1 := As_req(876940*kgf*cm)\n")
    assert not console, console
    assert r"5.55\,\mathrm{cm}^{2}" in page, page


def test_a_function_without_a_kept_name_prints_as_before(sheet):
    page, console = sheet("M(x) = -2*kgf*cm + 3*kgf*x - fy*cm*x^2/2\n")
    assert not console, console
    definition = row(page, r"M\left(x\right)")
    # SymPy's order, as 0.35.0 prints it: the written order would put -2 kgf cm first.
    assert definition.startswith(r"3\,\mathrm{kgf}\,x - 2\,\mathrm{kgf}"), definition


def test_a_call_keeps_the_kept_name_and_its_argument(sheet):
    page, console = sheet(FUNCTION + "As_2 = As_req(876940*kgf*cm)\nnumeric(As_2)\n")
    assert not console, console
    rows = page.split(r"\mathrm{As}_{2} & = & ", 1)[1].split(r"\end{array}", 1)[0]
    assert r"\mathrm{As}_{req}\left(876940\,\mathrm{kgf} \cdot \mathrm{cm}\right)" in rows, rows
    assert "f_{cw}" in rows and r"2 \cdot 876940" in rows, rows
    assert "2.06" not in rows and "0.85" not in rows.split(r"\left(178.50", 1)[0], rows
    assert rows.rstrip().endswith(r"5.55\,\mathrm{cm}^{2}"), rows


def test_a_written_form_agrees_when_a_float_sits_under_a_root():
    """The check that a written form is the value found no proof on Colab's SymPy.

    SymPy 1.13.3 - Colab's - builds `As_req(876940*kgf*cm)` with the numbers taken out of
    the root, `sqrt(219235)*sqrt(4.85e-7 - ...)`, and `cancel` cannot bring that back to
    the written `sqrt(1 - 2*876940 kgf cm/(phi f_cw b d^2))`. The written form was thrown
    away and the page printed `2.61 b d fc sqrt(219235) ...`. Found running the suite
    against the 0.36.0 wheel in a Colab-like environment, before the release merged.
    The expression below is the one 1.13.3 builds, so this fails on any SymPy.
    """
    import sympy as sp

    from engcalc_colab.engine import _agrees_with

    b, d, fc, fy, phi, cm, kgf, f_cw = sp.symbols("b d fc fy phi cm kgf f_cw", positive=True)
    written = b * d * f_cw * (1 - sp.sqrt(1 - 2 * 876940 * kgf * cm / (phi * f_cw * b * d**2))) / fy
    value = (
        sp.Float("0.85") * b * d * fc
        * (-sp.Float("3.06785995538948") * sp.sqrt(219235)
           * sp.sqrt(sp.Float("4.846397701097e-7") - cm * kgf / (b * d**2 * fc * phi)) + 1)
        / fy
    )
    assert _agrees_with(written, value, {f_cw: sp.Float("0.85") * fc})
    # And a written form that is not the value is still refused.
    assert not _agrees_with(written * 2, value, {f_cw: sp.Float("0.85") * fc})
