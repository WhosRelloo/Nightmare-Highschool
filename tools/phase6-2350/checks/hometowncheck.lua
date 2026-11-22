-- hometowncheck (2.35.0, task 9): Controllers.Hometown, single-player. Client VM, one call, Play.
-- (1) Hidden() with fake "others"; (2) HideCharacter on a throwaway R6-like dummy (parts, decal, sound volume kept in NHVol,
-- billboard, name display) and back; (3) Cast: nil when missing, a local clone under NHHometownCast with the source hidden
-- (a stand-in __CastProbe under Workspace.Hometown), then everything restored and the folder gone when NHTutorial clears.
-- NHTutorial is set on the LocalPlayer from the CLIENT (it doesn't replicate, so no server state is touched).
-- Decal.LocalTransparencyModifier is used (2b asserts it works). This requires the Hometown module in this VM (a second copy; it has no game state of its own) and calls its OnStart so the
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
-- (task 11 fix round 1, I3) setting NHTutorial casts Biscuit and starts his sleep loop at once (this copy and the game's own): wait for it,
-- check it, and count the watchers it left (the hidden source) as the baseline for the counts below
local Bis0 = os.clock()
repeat task.wait(0.1) until workspace:FindFirstChild("NHHometownCast") and workspace.NHHometownCast:FindFirstChild("WFBiscuit") or os.clock() - Bis0 > 5
task.wait(0.5)
do
	local B = workspace:FindFirstChild("NHHometownCast") and workspace.NHHometownCast:FindFirstChild("WFBiscuit")
	local A = B and B:FindFirstChildWhichIsA("Animator", true)
	local Playing = 0
	if A then for _, T in A:GetPlayingAnimationTracks() do Playing += 1 end end
	check("1e NHTutorial set: Biscuit cast with a clip playing on him", B ~= nil and Playing >= 1, Playing)
end
local Base = H.WatchedForTests()
check("1b both in tutorial: hidden", H.Hidden(fake(true)) == true)
check("1c other not in tutorial: not hidden", H.Hidden(fake(nil)) == false)
check("1d self: not hidden", H.Hidden(Player) == false)

-- (2) dummy
local D = Instance.new("Model"); D.Name = "__HideProbe"
local Part = Instance.new("Part"); Part.Name = "Head"; Part.Parent = D
local Decal = Instance.new("Decal"); Decal.Parent = Part
local Snd = Instance.new("Sound"); Snd.Volume = 0.7; Snd.Parent = Part
local Bb = Instance.new("BillboardGui"); Bb.Enabled = false; Bb.Parent = Part -- already off: it must stay off after the restore
local Hum = Instance.new("Humanoid"); Hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.Subject; Hum.Parent = D -- not the default: restored as is
D.Parent = workspace
H.HideCharacter(D, true)
check("2a part LTM 1", Part.LocalTransparencyModifier == 1)
check("2b decal hidden (LocalTransparencyModifier)", Decal.LocalTransparencyModifier == 1)
check("2c sound muted, original kept", Snd.Volume == 0 and near(Snd:GetAttribute("NHVol"), 0.7))
check("2d billboard off, original kept", Bb.Enabled == false and Bb:GetAttribute("NHEn") == false)
check("2e name display none", Hum.DisplayDistanceType == Enum.HumanoidDisplayDistanceType.None)
H.HideCharacter(D, true) -- hiding twice must not clobber the saved volume
check("2f hide twice keeps original", near(Snd:GetAttribute("NHVol"), 0.7))
check("2f2 one watcher while hidden", H.WatchedForTests() == Base + 1)
-- (fix round 1, I2) things that arrive after the hide are hidden too
local Acc = Instance.new("Accessory"); local Handle = Instance.new("Part"); Handle.Name = "Handle"; Handle.Parent = Acc
local Late = Instance.new("Sound"); Late.Volume = 0.5; Late.Parent = Handle
Acc.Parent = D
local Tool = Instance.new("Tool"); local TH = Instance.new("Part"); TH.Name = "Handle"; TH.Parent = Tool
local TD = Instance.new("Decal"); TD.Parent = TH
Tool.Parent = D
local Sound2 = Instance.new("Sound"); Sound2.Volume = 0.3; Sound2.Parent = Part
task.wait(0.2)
check("2h late accessory part hidden", Handle.LocalTransparencyModifier == 1)
check("2i late sound in it muted, original kept", Late.Volume == 0 and near(Late:GetAttribute("NHVol"), 0.5))
check("2j late tool part and decal hidden", TH.LocalTransparencyModifier == 1 and TD.LocalTransparencyModifier == 1)
check("2k late sound on the body muted", Sound2.Volume == 0)
H.HideCharacter(D, false)
check("2g restored", Part.LocalTransparencyModifier == 0 and Decal.LocalTransparencyModifier == 0 and near(Snd.Volume, 0.7) and Snd:GetAttribute("NHVol") == nil
	and Bb.Enabled == false and Bb:GetAttribute("NHEn") == nil and Hum.DisplayDistanceType == Enum.HumanoidDisplayDistanceType.Subject)
check("2g2 late things restored", Handle.LocalTransparencyModifier == 0 and near(Late.Volume, 0.5) and near(Sound2.Volume, 0.3))
check("2g3 watcher gone after restore", H.WatchedForTests() == Base)
-- a hidden model that is destroyed drops its watcher
H.HideCharacter(D, true)
check("2l watcher while hidden again", H.WatchedForTests() == Base + 1)
D:Destroy()
task.wait(0.1)
check("2m watcher gone when the model is destroyed", H.WatchedForTests() == Base)
D = Instance.new("Model") -- (the dummy is gone; the lines below only need something to destroy)
D:Destroy()

-- (3) Cast
Player:SetAttribute("NHTutorial", nil)
check("3a0 not in the tutorial -> nil even for a real model", H.Cast("__CastProbe") == nil)
Player:SetAttribute("NHTutorial", true)
check("3a missing model -> nil", H.Cast("__NoSuchCast") == nil)
local Hometown = workspace:FindFirstChild("Hometown")
check("3b Workspace.Hometown exists", Hometown ~= nil)
if Hometown then
	local Src = Instance.new("Model"); Src.Name = "__CastProbe"
	local SP = Instance.new("Part"); SP.Name = "Body"; SP.Parent = Src
	SP.CanCollide = true; SP.CanQuery = true; SP.CanTouch = false -- (I4) the originals come back as they were
	local SS = Instance.new("Sound"); SS.Volume = 0.4; SS.Parent = SP
	local SB = Instance.new("BillboardGui"); SB.Enabled = false; SB.Parent = SP
	local SH = Instance.new("Humanoid"); SH.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.Subject; SH.Parent = Src
	Src.PrimaryPart = SP
	Src.Parent = Hometown
	local M = H.Cast("__CastProbe")
	local Folder = workspace:FindFirstChild("NHHometownCast")
	check("3c clone returned under NHHometownCast", M ~= nil and M ~= Src and Folder ~= nil and M.Parent == Folder)
	check("3d source hidden", SP.LocalTransparencyModifier == 1 and SS.Volume == 0)
	check("3d2 source untouchable while cast", SP.CanCollide == false and SP.CanQuery == false and SP.CanTouch == false)
	check("3e clone not hidden, still solid", M ~= nil and M.Body.LocalTransparencyModifier == 0 and near(M.Body.Sound.Volume, 0.4)
		and M.Body.CanCollide == true and M.Body.CanQuery == true and M.Body.CanTouch == false)
	check("3f second call returns same clone", H.Cast("__CastProbe") == M)
	Player:SetAttribute("NHTutorial", nil)
	task.wait(0.8) -- (task 10) the cast goes at full black: the handler waits 0.2 s, then for any dip
	check("3g cast folder destroyed on clear", workspace:FindFirstChild("NHHometownCast") == nil)
	check("3h source restored on clear", SP.LocalTransparencyModifier == 0 and near(SS.Volume, 0.4))
	check("3i source collide/query/touch back to their originals", SP.CanCollide == true and SP.CanQuery == true and SP.CanTouch == false
		and SP:GetAttribute("NHCC") == nil)
	check("3j billboard and name display back to their originals", SB.Enabled == false and SH.DisplayDistanceType == Enum.HumanoidDisplayDistanceType.Subject)
	check("3k no watchers left", H.WatchedForTests() == 0)
	Src:Destroy()
end
Player:SetAttribute("NHTutorial", nil)
H.Stop() -- drops this copy's OnStart connections (the game's own copy keeps its own)
return (Pass and "PASS" or "FAIL") .. "\n" .. table.concat(Out, "\n")
