"""python cmp.py refs.json branch.json main.json"""
import json
import sys

ref = json.load(open(sys.argv[1]))
br = json.load(open(sys.argv[2]))
mn = json.load(open(sys.argv[3]))


def judge(r, got):
    if "err" in got:
        return "REFUSED"
    v = got["vals"]
    if isinstance(r, str):
        return "ref:" + r
    r = [x for x in r if x != "IMAG"]
    if len(v) != len(r):
        return f"COUNT {len(v)}/{len(r)}"
    for a, b in zip(v, r):
        if abs(a - b) > 1e-4 * abs(b) + 1e-9 * max(abs(x) for x in r):
            return "WRONG"
    return "ok"


for name in ref:
    jb, jm = judge(ref[name], br[name]), judge(ref[name], mn[name])
    flag = "" if jb == "ok" else "  <<<"
    print(f"{name:26} branch={jb:12} main={jm:12} tb={br[name]['t']:.3f} tm={mn[name]['t']:.3f}{flag}")
    if jb != "ok" or "-v" in sys.argv:
        print("   ref   ", [f"{x:.8g}" if isinstance(x, float) else x for x in ref[name]] if not isinstance(ref[name], str) else ref[name])
        print("   branch", br[name].get("vals") and [f"{x:.8g}" for x in br[name]["vals"]] or br[name].get("err"))
        print("   main  ", mn[name].get("vals") and [f"{x:.8g}" for x in mn[name]["vals"]] or mn[name].get("err"))
