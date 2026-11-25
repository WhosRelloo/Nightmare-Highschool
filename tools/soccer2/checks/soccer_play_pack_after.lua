-- soccer_play_pack_after (soccer-2.0 Task 5, Client, Play, after soccer_match_end.lua): the normal pack is back.
local P = game.Players.LocalPlayer
local RS = game:GetService("ReplicatedStorage")
local Ctl = P.PlayerScripts:WaitForChild("Controllers")
local Pack = require(Ctl.Character.SoccerPack)
local AC = require(Ctl.Character.AnimationController)
local Fails = {}
local T0 = os.clock()
while Pack.StateForTests().On and os.clock() - T0 < 5 do task.wait(0.1) end
if Pack.StateForTests().On then return "FAIL the pack is still on" end
if AC.Overridden() then table.insert(Fails, "the override is still set") end
local Char = P.Character
local Hum = Char:FindFirstChildOfClass("Humanoid")
local W = Char:GetAttribute("Weapon")
local Want = (Hum:GetAttribute("Equip") and W and RS.Assets.Animations.Weapons:FindFirstChild(W)) or RS.Assets.Animations.Default
local Idle = AC.Controller.TrackTable.Idle
if not (Idle and Idle.Animation.AnimationId == Want.Movement.Idle.AnimationId) then table.insert(Fails, "Idle is " .. tostring(Idle and Idle.Animation.AnimationId) .. ", want " .. Want.Name .. "'s") end
if AC.DirectionalForTests().Back then table.insert(Fails, "the backpedal track is still loaded") end
if #Fails > 0 then return "FAIL soccer_play_pack_after\n" .. table.concat(Fails, "\n") end
return "PASS soccer_play_pack_after"
