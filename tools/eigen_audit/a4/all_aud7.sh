#!/bin/sh
# Run the fourth audit's eigenvalue cases on the working tree and judge them against mpmath.
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8
PY=/c/Users/elias/engcalc/.venv/Scripts/python
for i in 1 2 3 4 5; do
  $PY h4.py C:/Users/elias/AppData/Local/Temp/claude/C--Users-elias-engcalc/89f737e6-e4f0-46d1-b5db-c6f2a2299f5f/scratchpad/aud7wt cases$i.py aud7_$i.json >/dev/null 2>&1
  $PY cmp.py r$i.json aud7_$i.json m$i.json | grep "<<<" | sed "s/^/[$i] /"
done
echo done
