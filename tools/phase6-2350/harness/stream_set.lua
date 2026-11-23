-- stream_set.lua (Server VM, 2026-11-22): put the player on a cine set's start mark and have it streamed in. The Wickfield sets
-- (Garden, BusStop) are far from the school spawn, and with StreamingEnabled their marks don't exist on the client until the player is
-- near them: approachcheck / sneakcheck / buscheck then can't find FenceZone / Stand. run_cut.sh runs this (SET is set by sed there).
local SET = "Garden"
local P = game.Players:GetPlayers()[1]
local F = workspace:WaitForChild("NHCineSets"):FindFirstChild(SET)
if not (P and P.Character and F) then return "stream_set: no player, character or set " .. SET end
local M = F:FindFirstChild(if SET == "Garden" then "Start" else "Stand")
if not M then return "stream_set: no start mark in " .. SET end
pcall(function() P:RequestStreamAroundAsync(M.Position, 10) end)
-- marks sit on the floor; a character's pivot is its root, 3 studs up (BusStop: on Stand itself, never on the bench behind it)
P.Character:PivotTo(M.CFrame + Vector3.new(0, 3, 0))
task.wait(2)
return "stream_set " .. SET .. " ok"
