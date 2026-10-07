import sys, difflib, re
split = lambda t: re.split(r"\\\[|\\ ", t)
a = split(open(sys.argv[1], encoding="utf-8").read())
b = split(open(sys.argv[2], encoding="utf-8").read())
for l in difflib.unified_diff(a, b, n=0, lineterm=""):
    print(l[:300])
