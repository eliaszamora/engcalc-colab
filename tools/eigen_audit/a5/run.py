"""ENGROOT=<tree> python run.py cases6.py out.json [refs.json]  (refs computed if missing)"""
import json
import os
import sys

from lib import sheet, ref, report

ns = {}
exec(open(sys.argv[1], encoding="utf-8").read(), ns)
cases = ns["CASES"]
refs_file = sys.argv[3] if len(sys.argv) > 3 else sys.argv[1] + ".refs.json"
refs = json.load(open(refs_file)) if os.path.exists(refs_file) else {}
out = {}
only = os.environ.get("ONLY")
for name, c in cases.items():
    if only and only not in name:
        continue
    if name not in refs:
        refs[name] = ref(c.get("Kref", c["K"]), c.get("Gref", c["G"]), scale=c.get("scale", 1.0))
        json.dump(refs, open(refs_file, "w"), indent=0)
    got, t = sheet(c["K"], c["G"], c.get("ku", ""), c.get("gu", ""))
    out[name] = {"got": got, "t": t}
    report(name, refs[name], got, t)
json.dump(out, open(sys.argv[2], "w"), indent=0)
