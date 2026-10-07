import json
import sys
from lib import judge

refs = json.load(open(sys.argv[1]))
b = json.load(open(sys.argv[2]))
m = json.load(open(sys.argv[3]))
for name in b:
    if name not in m:
        continue
    jb, jm = judge(refs[name], b[name]["got"]), judge(refs[name], m[name]["got"])
    flag = "  <<<" if jb != "ok" else ""
    print(f"{name:34} br={jb:14} main={jm:14} tb={b[name]['t']:7.3f} tm={m[name]['t']:7.3f}{flag}")
