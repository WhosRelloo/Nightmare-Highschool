-- hometowncheck (2.35.0, task 9): Controllers.Hometown, single-player. Client VM, one call, Play.
-- (1) Hidden() with fake "others"; (2) HideCharacter on a throwaway R6-like dummy (parts, decal, sound volume kept in NHVol,
-- billboard, name display) and back; (3) Cast: nil when missing, a local clone under NHHometownCast with the source hidden
-- (a stand-in __CastProbe under Workspace.Hometown), then everything restored and the folder gone when NHTutorial clears.
-- NHTutorial is set on the LocalPlayer from the CLIENT (it doesn't replicate, so no server state is touched).
-- This requires the Hometown module in this VM (a second copy; it has no game state of its own) and calls its OnStart so the
-- NHTutorial-cleared handler is live.
local Players = game:GetService("Players")
local Player = Players.LocalPlayer
local H = require(Player.PlayerScripts.Controllers.Hometown)
H.OnStart()
local Out, Pass = {}, true
local function check(Name, Cond, Extra)
	if not Cond then Pass = false end
	table.insert(Out, (Cond and "ok   " or "FAIL ") .. Name .. (Extra and (" " .. tostring(Extra)) or ""))
end
local function near(A, B) return math.abs(A - B) < 1e-3 end -- Volume is a float32
local function fake(Attr) return { GetAttribute = function(_, K) if K == "NHTutorial" then return Attr end end } end

Player:SetAttribute("NHTutorial", nil)
check("1a not in tutorial: others not hidden", H.Hidden(fake(true)) == false)
Player:SetAttribute("NHTutorial", true)
check("1b both in tutorial: hidden", H.Hidden(fake(true)) == true)
check("1c other not in tutorial: not hidden", H.Hidden(fake(nil)) == false)
check("1d self: not hidden", H.Hidden(Player) == false)

-- (2) dummy
local D = Instance.new("Model"); D.Name = "__HideProbe"
local Part = Instance.new("Part"); Part.Name = "Head"; Part.Parent = D
local Decal = Instance.new("Decal"); Decal.Transparency = 0.25; Decal.Parent = Part
local Snd = Instance.new("Sound"); Snd.Volume = 0.7; Snd.Parent = Part
local Bb = Instance.new("BillboardGui"); Bb.Parent = Part
local Hum = Instance.new("Humanoid"); Hum.Parent = D
D.Parent = workspace
H.HideCharacter(D, true)
check("2a part LTM 1", Part.LocalTransparencyModifier == 1)
check("2b decal hidden", Decal.Transparency == 1)
check("2c sound muted, original kept", Snd.Volume == 0 and near(Snd:GetAttribute("NHVol"), 0.7))
check("2d billboard off", Bb.Enabled == false)
check("2e name display none", Hum.DisplayDistanceType == Enum.HumanoidDisplayDistanceType.None)
H.HideCharacter(D, true) -- hiding twice must not clobber the saved volume
check("2f hide twice keeps original", near(Snd:GetAttribute("NHVol"), 0.7))
H.HideCharacter(D, false)
check("2g restored", Part.LocalTransparencyModifier == 0 and Decal.Transparency == 0.25 and near(Snd.Volume, 0.7) and Snd:GetAttribute("NHVol") == nil
	and Bb.Enabled == true and Hum.DisplayDistanceType == Enum.HumanoidDisplayDistanceType.Viewer)
D:Destroy()

-- (3) Cast
check("3a missing model -> nil", H.Cast("__NoSuchCast") == nil)
local Hometown = workspace:FindFirstChild("Hometown")
check("3b Workspace.Hometown exists", Hometown ~= nil)
if Hometown then
	local Src = Instance.new("Model"); Src.Name = "__CastProbe"
	local SP = Instance.new("Part"); SP.Name = "Body"; SP.Parent = Src
	local SS = Instance.new("Sound"); SS.Volume = 0.4; SS.Parent = SP
	Src.PrimaryPart = SP
	Src.Parent = Hometown
	local M = H.Cast("__CastProbe")
	local Folder = workspace:FindFirstChild("NHHometownCast")
	check("3c clone returned under NHHometownCast", M ~= nil and M ~= Src and Folder ~= nil and M.Parent == Folder)
	check("3d source hidden", SP.LocalTransparencyModifier == 1 and SS.Volume == 0)
	check("3e clone not hidden", M ~= nil and M.Body.LocalTransparencyModifier == 0 and near(M.Body.Sound.Volume, 0.4))
	check("3f second call returns same clone", H.Cast("__CastProbe") == M)
	Player:SetAttribute("NHTutorial", nil)
	task.wait(0.2)
	check("3g cast folder destroyed on clear", workspace:FindFirstChild("NHHometownCast") == nil)
	check("3h source restored on clear", SP.LocalTransparencyModifier == 0 and near(SS.Volume, 0.4))
	Src:Destroy()
end
Player:SetAttribute("NHTutorial", nil)
return (Pass and "PASS" or "FAIL") .. "\n" .. table.concat(Out, "\n")
