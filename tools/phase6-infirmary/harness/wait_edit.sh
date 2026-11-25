#!/bin/bash
# wait_edit.sh [tries]: wait (30 s steps) until NH Combat Test is in Edit; prints EDIT or STILLPLAY
n=${1:-19}
for i in $(seq 1 $n); do s=$(python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py studios 2>&1); echo "$s" | grep -q '"mode":"Edit","name":"NH Combat' && { echo EDIT $(date +%T); exit 0; }; sleep 30; done; echo STILLPLAY; exit 1
