-- lf_setup (playtest-blockers, Server, Play, run_live.py): the Lost & Found box is live, then a lost item is found
-- and picked up through the real pick-up path, and the player is stood at the box facing it (lf_after.lua checks the
-- hand-in that a real E press on the box's prompt makes).
local CS = game:GetService(`CollectionService`)
local LF = require(game.ServerScriptService.Services.Features.LostFound)
local Rep = require(game.ServerScriptService.Services.Social.Reputation)
local Data = require(game.ServerScriptService.Services.Player.Data)
local P = game.Players:GetPlayers()[1]
local C = P.Character
local R = C.HumanoidRootPart
local Boxes = CS:GetTagged(`NHLostFoundBox`)
if #Boxes == 0 then return `FAIL no Lost & Found box is tagged NHLostFoundBox` end
local Box = Boxes[1]
local Prompt = Box:FindFirstChild(`NHLostHandIn`, true)
if not (Prompt and Prompt:IsA(`ProximityPrompt`) and Prompt.Enabled) then return `FAIL the box has no hand-in prompt` end
local State = LF.State()
local Social = Rep.Get(P)
local L = Social and Social.LostFound
P:SetAttribute(`NHLFTestN`, if typeof(L) == `table` then L.N else -1)
P:SetAttribute(`NHLFTestDay`, if typeof(L) == `table` then L.Day else -1)
P:SetAttribute(`NHLFTestYen`, Data.GetProfile(P).Yen)
-- found: a lost item turns up by the player (the same spawn the world uses), and they pick it up
local M = LF.SpawnForTests(`PocketWatch`, R.CFrame * CFrame.new(0, -2.9, -2))
if not M then return `FAIL no item spawned` end
task.wait(0.3)
local Got = LF.PickUpForTests(P, M)
if Got ~= `PocketWatch` then return `FAIL pick-up gave {tostring(Got)}` end
local Held = C:FindFirstChild(`NHHeldLost`) ~= nil
-- stand 4 studs in front of the box, facing it
local At = Box:GetPivot()
local Front = At.Position - At.LookVector * 4
C:PivotTo(CFrame.lookAt(Vector3.new(Front.X, R.Position.Y > At.Position.Y and R.Position.Y or At.Position.Y + 1.5, Front.Z), Vector3.new(At.Position.X, At.Position.Y + 1.5, At.Position.Z)))
return string.format(`PASS box %s prompt "%s" (dist %d); loose items in the world %d; picked up %s (in hand %s)`,
	Box:GetFullName(), Prompt.ActionText, Prompt.MaxActivationDistance, #State.Loose, Got, tostring(Held))
