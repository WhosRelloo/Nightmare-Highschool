local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Actor = require(Players.LocalPlayer.PlayerScripts.Controllers.CineActor)
local TA = require(game.ReplicatedStorage.Config.TutorialAnim)
local Folder = game.ReplicatedStorage.NHCineClips.Tutorial
local function resolve(Name)
	local Seq = Folder:FindFirstChild(Name)
	if not Seq then return nil end
	return Seq:GetAttribute("PreviewId") or tostring(game:GetService("AnimationClipProvider"):RegisterAnimationClip(Seq))
end
local C = Players.LocalPlayer.Character
local Parts = { "Torso", "Head", "Left Arm", "Right Arm", "Left Leg", "Right Leg" }
local Samples, Marks = {}, {}
local Conn = RunService.RenderStepped:Connect(function()
	local P = {}
	for _, N in Parts do table.insert(P, C[N].Position) table.insert(P, (C[N].CFrame * CFrame.new(0, -1, 0)).Position) end
	local Prev = Samples[#Samples]
	if Prev then
		local Same = true
		for j = 1, #P do if P[j] ~= Prev[j] then Same = false break end end
		if Same then return end -- a render frame where the rig did not update is not a body frame (a track start costs one)
	end
	table.insert(Samples, P)
end)
local Chain = "TheBus"
Actor.Begin()
for _, St in TA.Chains[Chain] do St._at = nil end
local Tracks = Actor.Chain(Chain, resolve, nil, function(Piece) table.insert(Marks, { at = #Samples, name = "switch " .. Piece }) end)
local Last = TA.Chains[Chain][#TA.Chains[Chain]]
table.insert(Marks, { at = #Samples, name = "reseat " .. Last.Piece })
Actor.Reseat(Last.Piece, Last.EndOffset, resolve)
task.wait(0.6)
Actor.Release()
Conn:Disconnect()
local Acc = {}
for i = 3, #Samples do
	local M = 0
	for j = 1, #Samples[i] do
		local A = (Samples[i][j] - 2 * Samples[i - 1][j] + Samples[i - 2][j]).Magnitude * 3600
		if A > M then M = A end
	end
	Acc[i] = M
end
local Near, Inside = {}, {}
for _, Mk in Marks do for i = Mk.at - 4, Mk.at + 4 do Near[i] = true end end
for i = 3, #Samples do if not Near[i] then table.insert(Inside, Acc[i]) end end
table.sort(Inside)
local P99 = Inside[math.max(1, math.floor(#Inside * 0.99))] or 1
local Lines, Pass = {}, true
for _, Mk in Marks do
	local Peak = 0
	for i = Mk.at - 4, Mk.at + 4 do if Acc[i] and Acc[i] > Peak then Peak = Acc[i] end end
	local Ok = Peak <= P99 or Peak <= 45
	Pass = Pass and Ok
	table.insert(Lines, string.format("%s peak %.0f (p99 %.0f) %s", Mk.name, Peak, P99, Ok and "ok" or "POP"))
end
return (Pass and "BODY OK\n" or "BODY POP\n") .. table.concat(Lines, "\n")
