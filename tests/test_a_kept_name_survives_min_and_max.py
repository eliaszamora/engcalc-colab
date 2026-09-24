r"""A kept name stays a name inside `min` and `max`.

    keep f_cw = 0.85*fc
    keep As_min = max(0.8*sqrt(fc*kgf/cm^2)/fy*b*d, 14*kgf/cm^2/fy*b*d)
    keep As = max(f_cw*b*d/fy*(1 - sqrt(1 - 2*R_n/f_cw)), As_min)

The beam of the portal frame, designed. `As` printed `max(0.85 fc b d/fy (1 - sqrt(1 -
2.35 ...)), max(0.8 b d sqrt(...)/fy, 14 b d/fy))`: every kept name expanded, the two
`max` nested, and the 0.85 of Whitney's block folded into 2/0.85 = 2.35 - a formula no
reviewer can hold against the code. The written form is offered only for calls whose
second walk is pure arithmetic (`_WRITTEN_FORM_SAFE_CALLS`), and `min` and `max` were not
on the list; they are pure arithmetic, like `abs` beside them. Found writing
`tools/portico_diseno.eng` on 2026-09-24.
"""

import contextlib
import io

import pytest
from IPython.display import Math

import engcalc_colab.magic as magic

VALUES = "fc := 210*kgf/cm^2\nfy := 4200*kgf/cm^2\nb := 30*cm\nd := 44*cm\n"


@pytest.fixture
def sheet(monkeypatch):
    def run(source: str) -> str:
        captured = []
        monkeypatch.setattr(magic, "display", captured.append)
        with contextlib.redirect_stdout(io.StringIO()):
            magic.EngMagics().eng("", VALUES + source)
        return " ".join(item.data for item in captured if isinstance(item, Math))

    return run


def definition(page: str, name: str) -> str:
    return page.split(name + r" & = & \displaystyle ", 1)[1].split(r"\\", 1)[0]


def test_a_kept_name_stays_inside_max(sheet):
    page = sheet("keep f_cw = 0.85*fc\nkeep A_min = 5*cm^2\nkeep A_1 = max(f_cw*b/fc*2*cm, A_min)\n")
    row = definition(page, "A_{1}")
    assert r"f_{cw}" in row and r"A_{min}" in row, row
    assert "1.7" not in row, row


def test_a_kept_name_stays_inside_min(sheet):
    page = sheet("keep s_1 = d/2\nkeep s_2 = min(s_1, 60*cm)\n")
    row = definition(page, "s_{2}")
    assert r"s_{1}" in row, row


def test_the_value_is_the_same(sheet):
    page = sheet(
        "keep f_cw = 0.85*fc\nkeep R_n = 20*kgf/cm^2\n"
        "keep As_min = 14*kgf/cm^2/fy*b*d\n"
        "keep A_s = max(f_cw*b*d/fy*(1 - sqrt(1 - 2*R_n/f_cw)), As_min)\nreport(A_s)\n"
    )
    assert r"6.68\,\mathrm{cm}^{2}" in page, page
