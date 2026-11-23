#!/bin/bash
# round_end.sh (2026-11-22): clear the checkpoint and the test marks, TutorialLeave, restore slot 2 from this round's _slot2.json, print
# CineState and Origin. Then stop Play.
cd "$(dirname "$0")"
R="python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau"
PL="placeId: 98950102230473"
$R "$PL" Server @checkpoint_clear.lua >/dev/null
for c in __SeamlessTest TutorialSneak TutorialBus __BeatHoldTest; do python -X utf8 -I bridge.py CineMark '$P' "\"$c\"" nil >/dev/null; done
python -X utf8 -I bridge.py TutorialLeave '$P' >/dev/null
python -X utf8 -I restore.py | tr -d '\n'; echo
echo "CineState after: $(python -X utf8 -I bridge.py CineState '$P')"
echo "Origin after: $($R "$PL" Server @origin.lua)"
