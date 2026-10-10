#!/bin/sh
# Run the fourth audit's eigenvalue cases on the working tree and judge them against mpmath.
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8
PY=/c/Users/elias/engcalc/.venv/Scripts/python
for i in 1 2 3 4 5; do
  $PY h4.py C:/Users/elias/engcalc cases$i.py now$i.json >/dev/null 2>&1
  $PY cmp.py r$i.json now$i.json m$i.json | grep "<<<" | sed "s/^/[$i] /"
done
echo done
