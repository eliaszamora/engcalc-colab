import json
import re
import sys

res = json.load(open(sys.argv[1], encoding="utf-8"))
refs = json.load(open(__import__("os").environ["REFS"]))
other = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 else None


def shown(page, name="l"):
    if "\\operatorname{eigenvals}" not in page:
        return None, None
    tail = page.rsplit("\\operatorname{eigenvals}", 1)[1].split("\\end{array}", 1)[0]
    tail = tail.split("&", 2)[-1].replace("\\rule{0pt}{0.7em}", "")
    unit = tail.rsplit("\\right]", 1)[-1] if "\\right]" in tail else ""
    body = tail.rsplit("\\right]", 1)[0]
    nums = re.findall(r"-?\d+\.\d+(?: \\times 10\^\{-?\d+\})?", body)
    vals = []
    fac = re.search(r"10\^\{(-?\d+)\}[^\[]{0,20}\\left\[", tail)
    f = 10 ** int(fac.group(1)) if fac else 1
    for n in nums:
        if "\\times" in n:
            m, e = n.split(" \\times 10^{")
            vals.append(f * float(m) * 10 ** int(e.rstrip("}")))
        else:
            vals.append(f * float(n))
    return vals, unit.strip()


for name, ref in refs.items():
    r = res[name]
    vals, unit = shown(r["page"])
    lam = [x for x in ref["lam"] if abs(x) < 1e12]
    conv = {"kip": 4.4482216152605, "N": 1e-3}.get(ref["unit"], 1.0)
    if "kN" in (unit or "") and ref["unit"] in ("kip", "N"):
        lam = [x * conv for x in lam]
    status = "OK"
    note = ""
    if r["printed"] or r["error"]:
        status = "REFUSED"
        note = (r["printed"] + r["error"]).strip()[:200]
    elif vals is None:
        status = "NOPAGE"
    elif len(vals) != len(lam):
        status = "COUNT"
    else:
        for got, want in zip(vals, lam):
            # printed to 2 decimals or 2 decimals of mantissa
            tol = max(0.0051, 0.0051 * abs(want) / 100 if abs(want) >= 1000 else 0.0051) if abs(want) >= 0.01 else 0.0051
            if abs(want) >= 1000:
                tol = abs(want) * 1e-4 + 0.0051
            if abs(got - want) > tol and not (abs(want) < 0.01 and abs(got - want) <= max(abs(want) * 0.0051, 1e-30)):
                status = "MISMATCH"
    line = f"{status:9} {name:28} unit={unit!r:40} ref_unit={ref['unit']!r}"
    print(line)
    if status != "OK" or "-v" in sys.argv:
        print("    ref :", [f"{x:.6g}" for x in lam][:12])
        print("    page:", vals[:12] if vals else vals, note)
    if other is not None:
        if other[name]["page"] != r["page"] or other[name]["printed"] != r["printed"]:
            ov, ou = shown(other[name]["page"])
            print("    DIFF main:", ov[:12] if ov else ov, ou, other[name]["printed"].strip()[:200])
