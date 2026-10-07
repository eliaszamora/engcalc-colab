"""python cmp3.py refs.json branch.json main.json : branch-not-ok vs main"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a6"))
from lib6 import judge2  # noqa: E402

refs = json.load(open(sys.argv[1]))
b = json.load(open(sys.argv[2]))
m = json.load(open(sys.argv[3]))
for name in b:
    if name not in m:
        continue
    jb, jm = judge2(refs[name], b[name]["got"]), judge2(refs[name], m[name]["got"])
    if jb != "ok":
        print(f"{name:40} br={jb:16} main={jm:16} tb={b[name]['t']:.2f} tm={m[name]['t']:.2f}")
