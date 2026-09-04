"""Blind external-user exercise for EngCalc.

This file intentionally uses only the public IPython extension surface. The physical
problem is the published StructurePoint ACI 318-14 simply-supported beam, converted to SI
after natural US-customary inputs (`ksi`, then `kip`) were rejected by the public DSL.
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
## Datos de diseño — mismo ejemplo StructurePoint convertido a SI
fc := 29.9922*MPa
fy := 413.6854*MPa
DL := 11.9670*kN/m
LL := 14.5939*kN/m
L := 7.62*m
h := 508.0*mm
b := 304.8*mm
cover := 38.1*mm
db_st := 9.525*mm
db_long := 28.6512*mm
phi := 0.9

## Carga factorizada y análisis estructural
wu = 1.2*DL + 1.6*LL
RA = wu*L/2
Mu = wu*L^2/8
numeric(wu, kN/m)
numeric(RA, kN)
numeric(Mu, kN*m)

## Diseño a flexión

d = h - cover - db_st - db_long/2
jd = 0.889*d
As_trial = Mu/(phi*fy*jd)
a_trial = As_trial*fy/(0.85*fc*b)
numeric(d, mm)
numeric(jd, mm)
numeric(As_trial, mm^2)
numeric(a_trial, mm)

## Verificación del acero provisto: 3 barras #9 = 1935.48 mm²
As_prov := 1935.48*mm^2
a_prov = As_prov*fy/(0.85*fc*b)
phiMn = phi*As_prov*fy*(d-a_prov/2)
DC = Mu/phiMn
numeric(a_prov, mm)
numeric(phiMn, kN*m)
numeric(DC)
"""
    flexure_text = run_eng(shell, flexure)
    if "engcalc:" in flexure_text:
        raise AssertionError(f"EngCalc reported an error in flexural design:\n{flexure_text}")

    # Independent conversion/hand-calculation values at default precision.
    require(
        flexure_text,
        "37.71", "143.68", "273.71", "446.05", "1853.90", "284.30", "0.96",
    )

    shear = r"""
## Diseño a corte — coeficiente equivalente al ejemplo imperial, expresado en SI
phi_v := 0.75
fyt := 413.6854*MPa
Av := 141.9352*mm^2
s_prov := 210.82*mm

Vu_d = RA - wu*d
Vc = 0.16606935*sqrt(fc/MPa)*MPa*b*d
phiVc = phi_v*Vc
Vs_req = Vu_d/phi_v - Vc
Av_over_s_req = (Vu_d-phiVc)/(phi_v*fyt*d)
s_req = Av/Av_over_s_req
s_max = d/2
phiVn = phi_v*(Vc + Av*fyt*d/s_prov)

numeric(Vu_d, kN)
numeric(phiVc, kN)
numeric(Vs_req, kN)
numeric(s_req, mm)
numeric(s_max, mm)
numeric(phiVn, kN)
"""
    shear_text = run_eng(shell, shear)
    if "engcalc:" in shear_text:
        raise AssertionError(f"EngCalc reported an error in shear design:\n{shear_text}")

    require(shear_text, "126.86", "92.74", "45.49", "575.70", "223.02", "185.91")

    print("EXTERNAL_USER_RC_BEAM: PASS")


if __name__ == "__main__":
    main()
