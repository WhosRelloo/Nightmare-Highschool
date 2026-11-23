#!/bin/bash
# run_cut.sh <cut> <outfile> <check.lua> [skippable] (2026-11-22): the way the tutorial checks start a first-viewing cut.
#   env SET=Garden|BusStop  stream that set in and put the player on its start mark first (stream_set.lua); without it a
#                           Wickfield cut's marks may not exist on the client (the school spawn is far away)
#   env PLACE=<client lua>  run after that; DELAY=<s> between starting the check and PlayCut (default 3)
# It clears the cut's Seen mark, TutorialEnter, streams, starts the check in the background, plays the cut, waits for the output.
cd "$(dirname "$0")"
B="python -X utf8 -I bridge.py"
$B CineMark '$P' "\"$1\"" nil >/dev/null
$B TutorialEnter '$P' >/dev/null
sleep 1
if [ -n "$SET" ]; then
	sed "s/^local SET = .*/local SET = \"$SET\"/" stream_set.lua > _stream_set.lua
	python -X utf8 -I E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py luau "placeId: 98950102230473" Server @_stream_set.lua >/dev/null
fi
[ -n "$PLACE" ] && python -X utf8 -I client.py "$PLACE" >/dev/null
rm -f "$2"
(python -X utf8 -I client.py "$3" > "$2" 2>&1 &)
sleep ${DELAY:-3}
$B PlayCut '$P' "\"$1\"" ${4:-false} >/dev/null
timeout 240 bash -c "until [ -s '$2' ]; do sleep 2; done"
sleep 1
$B CineMark '$P' "\"$1\"" nil >/dev/null
cat "$2"
