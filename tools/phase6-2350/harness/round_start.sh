#!/bin/bash
# round_start.sh (2026-11-22): run right after Play starts. start_play (retried: it fails if the server isn't up yet), refuse anything but
# slot 2, take a FRESH snapshot into _slot2.json, print CineState and Origin, and mark __SeamlessTest Seen (skipcheck's replay needs it).
cd "$(dirname "$0")"
R="python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau"
PL="placeId: 98950102230473"
for i in 1 2 3 4; do out=$($R "$PL" Server @start_play.lua 2>&1); echo "$out" | grep -q "inMenu false" && break; sleep 6; done
S=$($R "$PL" Server @slot_check.lua); echo "$S"
echo "$S" | grep -q "Slot=2" || { echo "NOT SLOT 2: no snapshot taken"; exit 1; }
$R "$PL" Server @snapshot.lua > _snap_raw.txt 2>&1
python -X utf8 -I -c "
import json
t=open('_snap_raw.txt',encoding='utf-8').read().strip()
d=json.loads(t[t.index('{'):t.rindex('}')+1]); json.dump(d,open('_slot2.json','w',encoding='utf-8')); print('fresh snapshot ok')
"
echo "CineState before: $(python -X utf8 -I bridge.py CineState '$P')"
echo "Origin before: $($R "$PL" Server @origin.lua)"
python -X utf8 -I bridge.py CineMark '$P' '"__SeamlessTest"' '"Seen"' >/dev/null
