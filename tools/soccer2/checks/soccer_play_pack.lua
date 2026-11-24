-- soccer_play_pack (soccer-2.0 Task 5, Client, Play, during a solo match from soccer_match_start.lua): the Soccer pack.
local P = game.Players.LocalPlayer
local RS = game:GetService("ReplicatedStorage")
local Ctl = P.PlayerScripts:WaitForChild("Controllers")
local PackMod = Ctl.Character:FindFirstChild("SoccerPack")
if not PackMod then return "FAIL no Controllers.Character.SoccerPack" end
local Pack = require(PackMod)
local AC = require(Ctl.Character.AnimationController)
local Clips = require(Ctl.Gui.Soccer.Clips)
local Loco = require(RS.Functions.Locomotion)
local LocoCfg = require(RS.Config.Locomotion)
local Fails = {}
local T0 = os.clock()
while not Pack.StateForTests().On and os.clock() - T0 < 5 do task.wait(0.1) end
if not Pack.StateForTests().On then return "FAIL the pack isn't on (InSport=" .. tostring(P:GetAttribute("InSport")) .. ")" end
local function id(T) return T and T.Animation and T.Animation.AnimationId end
local TT = AC.Controller.TrackTable
if id(TT.Walk) ~= (Clips.Id("Jog")) then table.insert(Fails, "Walk is " .. tostring(id(TT.Walk))) end
-- a solo match can start with the ball at the player's feet (HasSportBall set by the server): the idle follows it
local StartBall = P.Character:GetAttribute("HasSportBall")
local StartIdle = if P.Character:GetAttribute("HasSportBall") then "IdleBall" else "Idle"
if id(TT.Idle) ~= (Clips.Id(StartIdle)) then table.insert(Fails, "Idle is " .. tostring(id(TT.Idle)) .. ", want " .. StartIdle) end
if not (TT.Idle and TT.Idle.Looped and TT.Walk and TT.Walk.Looped) then table.insert(Fails, "Idle / Walk don't loop") end
if TT.Sprint and id(TT.Sprint) ~= RS.Assets.Animations.Default.Movement.Sprint.AnimationId then table.insert(Fails, "Sprint isn't Default's") end
if not AC.Overridden() then table.insert(Fails, "no override") end
local D = Clips.Data()
local Leg = P.Character["Left Leg"].Size.Y
local Want = Loco.Rate(8, D.Stride.SoccerJog, Leg, LocoCfg)
if math.abs(AC.Rate(8, "Walk") - Want) > Want * 0.05 then table.insert(Fails, string.format("walk rate %.3f, want %.3f", AC.Rate(8, "Walk"), Want)) end
local Dir = AC.DirectionalForTests()
if not (Dir.Back and id(Dir.Back) == (Clips.Id("JogBack"))) then table.insert(Fails, "no Jog Backward track in the directional walk") end
-- the ball idle (a client-side stand-in for the server's HasSportBall)
P.Character:SetAttribute("HasSportBall", true)
task.wait(0.6)
if id(AC.Controller.TrackTable.Idle) ~= (Clips.Id("IdleBall")) then table.insert(Fails, "the ball idle is " .. tostring(id(AC.Controller.TrackTable.Idle))) end
P.Character:SetAttribute("HasSportBall", nil)
task.wait(0.6)
if id(AC.Controller.TrackTable.Idle) ~= (Clips.Id("Idle")) then table.insert(Fails, "the idle after the ball is " .. tostring(id(AC.Controller.TrackTable.Idle))) end
P.Character:SetAttribute("HasSportBall", StartBall) -- put the server's value back
if #Fails > 0 then return "FAIL soccer_play_pack\n" .. table.concat(Fails, "\n") end
return "PASS soccer_play_pack"
