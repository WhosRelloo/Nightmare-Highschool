#!/bin/bash
# round_start.sh (Quiet Corners, 2026-11-23): run right after Play starts: start_play (retried), a FRESH slot 2 snapshot into _slot2.json.
cd "$(dirname "$0")"
R="python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau"
PL="placeId: 98950102230473"
for i in 1 2 3 4; do out=$($R "$PL" Server @start_play.lua 2>&1); echo "$out" | grep -q "inMenu false" && break; sleep 6; done
echo "$out"
$R "$PL" Server @snapshot.lua > _snap_raw.txt 2>&1
python -X utf8 -I -c "
import json
t=open('_snap_raw.txt',encoding='utf-8').read().strip()
d=json.loads(t[t.index('{'):t.rindex('}')+1]); json.dump(d,open('_slot2.json','w',encoding='utf-8')); print('fresh snapshot ok')
"
