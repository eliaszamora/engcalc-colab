#!/bin/sh
# Every audit case on the working tree, and his two sheets that use eigenvals(-K_g, K).
S="$(dirname "$0")"
export ENGROOT=C:/Users/elias/engcalc PYTHONIOENCODING=utf-8
PY=/c/Users/elias/engcalc/.venv/Scripts/python
echo "== a3 penalty"; $PY "$S/penalty_check.py"
echo "== a4"; sh "$S/a4/all.sh" 2>&1 | grep -v "^\[1\] [EFGH]_" | grep -v "^   main"
echo "== a5-a7 master"; $PY "$S/master.py" 2>&1 | tail -12
echo "== a8 portals with links"; (cd "$S/a8" && $PY p3.py 2>&1 | grep "<<<"; $PY p3.py 2>&1 | grep -c "GOT ERR")
echo "== a8 casesA/B"; (cd "$S/a8" && for c in A B; do $PY run8.py cases$c.py now$c.json 2>&1 | grep -E "WRONG|COUNT" | head -10; $PY -c "
import json; d=json.load(open('now$c.json')); print('$c', len(d), 'refused', sum(1 for v in d.values() if isinstance(v['got'], str)))"; done)
echo "== his sheets"; for f in p10_8 p10_9; do $PY "$S/run.py" "/c/Users/elias/Documents/EngCalc - Matrix Structural Analysis/hojas_ch10/$f.eng" 2>/dev/null > "$S/$f.now.txt"; grep -a STDOUT "$S/$f.now.txt" | cut -c1-160; done
$PY "$S/pdiff.py" "$S/corpus_out/2194dd71.main.txt" "$S/p10_9.now.txt" | wc -l
