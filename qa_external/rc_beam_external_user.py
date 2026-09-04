"""Blind external-user exercise for EngCalc.

This file intentionally uses only the public IPython extension surface.  The calculation
was frozen from a published StructurePoint ACI 318-14 worked example before inspecting
EngCalc implementation details.
"""

from __future__ import annotations

from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output


def run_eng(shell: InteractiveShell, cell: str) -> str:
    with capture_output(stdout=True, stderr=True, display=True) as captured:
        shell.run_cell_magic("eng", "", cell)

    pieces = [captured.stdout, captured.stderr]
    for output in captured.outputs:
        data = getattr(output, "data", {}) or {}
        for key in ("text/plain", "text/latex", "text/html"):
            value = data.get(key)
            if value:
                pieces.append(str(value))
    text = "\n".join(piece for piece in pieces if piece)
    print(text)
    return text


def require(text: str, *needles: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"expected rendered values not found: {missing}\n\n{text}")


def main() -> None:
    shell = InteractiveShell.instance()
    shell.extension_manager.load_extension("engcalc_colab")
    shell.run_line_magic("eng_config", "precision=2 zero_tolerance=1e-10")

    flexure = r"""
## Design data
fc := 4.35*kip/inch^2
fy := 60*kip/inch^2
DL := 0.82*kip/ft
LL := 1.00*kip/ft
L := 25*ft
h := 20*inch
b := 12*inch
cover := 1.50*inch
db_st := 0.375*inch
db_long := 1.128*inch
phi := 0.9

## Factored load and structural analysis
wu = 1.2*DL + 1.6*LL
RA = wu*L/2
Mu = wu*L^2/8
numeric(wu, kip/ft)
numeric(RA, kip)
numeric(Mu, kip*ft)

## Flexural design

d = h - cover - db_st - db_long/2
jd = 0.889*d
As_trial = Mu/(phi*fy*jd)
a_trial = As_trial*fy/(0.85*fc*b)
numeric(d, inch)
numeric(jd, inch)
numeric(As_trial, inch^2)
numeric(a_trial, inch)

## Check provided longitudinal steel
As_prov := 3.00*inch^2
a_prov = As_prov*fy/(0.85*fc*b)
phiMn = phi*As_prov*fy*(d-a_prov/2)
DC = Mu/phiMn
numeric(a_prov, inch)
numeric(phiMn, kip*ft)
numeric(DC)
"""
    flexure_text = run_eng(shell, flexure)
    if "engcalc:" in flexure_text:
        raise AssertionError(f"EngCalc reported an error in flexural design:\n{flexure_text}")

    require(flexure_text, "2.58", "32.30", "201.88", "17.56", "2.87", "209.69", "0.96")

    shear = r"""
## Shear design
phi_v := 0.75
fyt := 60*kip/inch^2
Av := 0.22*inch^2
s_prov := 8.30*inch

Vu_d = RA - wu*d
Vc = 2*sqrt(1000*fc/(kip/inch^2))*(kip/inch^2)*b*d/1000
phiVc = phi_v*Vc
Vs_req = Vu_d/phi_v - Vc
Av_over_s_req = (Vu_d-phiVc)/(phi_v*fyt*d)
s_req = Av/Av_over_s_req
s_max = d/2
phiVn = phi_v*(Vc + Av*fyt*d/s_prov)

numeric(Vu_d, kip)
numeric(phiVc, kip)
numeric(Vs_req, kip)
numeric(s_req, inch)
numeric(s_max, inch)
numeric(phiVn, kip)
"""
    shear_text = run_eng(shell, shear)
    if "engcalc:" in shear_text:
        raise AssertionError(f"EngCalc reported an error in shear design:\n{shear_text}")

    require(shear_text, "28.52", "20.85", "10.23", "22.67", "8.78", "41.79")

    print("EXTERNAL_USER_RC_BEAM: PASS")


if __name__ == "__main__":
    main()
