#!/bin/bash
# shot.sh <hour|off> [attr=value ...]: hold the look at an hour (World.DayCycle.HoldHour "SkyShot") with player preview
# attributes (NHMoonPhasePreview, NHSeasonPreview, NHSkyPreview, NHFxQuality), in the game VM; waits out a sky swap.
cd "$(dirname "$0")"
H=$1; shift
SETS=""
for kv in "$@"; do k=${kv%%=*}; v=${kv#*=}; if [ "$v" = "nil" ]; then SETS="$SETS P:SetAttribute(\"$k\", nil)"; else SETS="$SETS P:SetAttribute(\"$k\", \"$v\")"; fi; done
HOUR=$([ "$H" = "off" ] && echo nil || echo "$H")
cat > _shot.lua <<LUA
local P = game.Players.LocalPlayer
local S = Instance.new("LocalScript")
S.Source = [[
local P = game.Players.LocalPlayer
$SETS
local DC = require(P.PlayerScripts:FindFirstChild("World", true).DayCycle)
DC.HoldHour("SkyShot", $HOUR)
task.wait(4)
script:SetAttribute("Out", ("hour %.2f sky %s moon %s season %s"):format(DC.Hour(), tostring((DC.SkyAt(DC.Hour()))), tostring(DC.Moon()), tostring(DC.Season())))
]]
S.Parent = P.PlayerGui
local T = os.clock()
while S:GetAttribute("Out") == nil and os.clock() - T < 15 do task.wait(0.2) end
local O = S:GetAttribute("Out") S:Destroy() return tostring(O)
LUA
python -X utf8 -I client.py _shot.lua
