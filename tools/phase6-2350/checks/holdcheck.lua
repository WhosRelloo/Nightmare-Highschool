-- holdcheck (2.35.0, task 10 fix round 1): when TutorialBus's held title holds, and when it lets go. Client VM, ONE call.
-- MODE (sed 's/^local MODE = .*/local MODE = "leave"/'):
-- (task 11 fix round 1) TutorialBus has Replay = false now: the "replay" mode below is refused by the server (see replayrefused.lua); use "timeout"
--   "replay":  NOT in the tutorial (bridge TutorialLeave first), the script fires a journal Replay (mark TutorialBus Seen first).
--              The cut must blend out (phase Out seen), never hold (NHCineHold never true), leave the shared bus untouched
--              (same pivot, same Animator count, no playing track, no cast folder) and the character visible.
--   "timeout": in the tutorial, the caller starts the cut 3 s after this starts (bridge PlayCut $P '"TutorialBus"' false). Nothing
--              follows it: the hold must release by itself 9.5-12.5 s after it began, camera and controls handed back.
--   "leave":   as timeout, but 3 s into the hold the script clears NHTutorial on this client (what Tutorial.Leave does to
--              the client), and every frame until black is sampled: neither the source bus nor the player's character may be
--              visible (LocalTransparencyModifier 0) while the veil is still lifting from black, i.e. they come back only at full
--              black; afterwards the hold is released, the cast gone, no bus track left. The caller then runs TutorialLeave.
local MODE = "replay"
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Source = workspace.Hometown.BlackBus:FindFirstChild("WFBlackBus")
local function animators(M) local N, T = 0, 0 for _, D in M:GetDescendants() do if D:IsA("Animator") then N += 1 for _ in D:GetPlayingAnimationTracks() do T += 1 end end end return N, T end
local Rows, Name = {}, "HoldCheck_" .. math.random(1e6)
local SrcPivot = Source:GetPivot()
local SrcAnimators = animators(Source)
local function srcLtm()
	local P = Source:FindFirstChild("WFBlackBus_Main")
	return P and P.LocalTransparencyModifier or 0
end
RunService:BindToRenderStep(Name, Enum.RenderPriority.Last.Value, function()
	local UI = Player.PlayerGui:FindFirstChild("NHCineUI")
	local Veil = UI and UI:FindFirstChild("Veil")
	local Cast = workspace:FindFirstChild("NHHometownCast")
	local CastBus = Cast and Cast:FindFirstChild("WFBlackBus")
	local Playing = 0
	if CastBus then local _, T = animators(CastBus) Playing = T end
	local Head = Player.Character and Player.Character:FindFirstChild("Head")
	table.insert(Rows, { t = os.clock(); seam = Player:GetAttribute("NHCineSeam"); hold = Player:GetAttribute("NHCineHold") == true;
		veil = Veil and Veil.BackgroundTransparency or 1; src = srcLtm(); head = Head and Head.LocalTransparencyModifier or 0;
		cast = Cast ~= nil and CastBus ~= nil; playing = Playing; camType = workspace.CurrentCamera.CameraType })
end)
local Report, Pass = {}, true
local function chk(Label, Ok, Detail)
	Pass = Pass and Ok
	table.insert(Report, string.format("%s %s: %s", Ok and "ok  " or "FAIL", Label, Detail))
end
if MODE == "replay" then
	task.wait(0.5)
	game.ReplicatedStorage:WaitForChild("NHCine"):FireServer({ Kind = "Replay"; Id = "TutorialBus" })
end
local W0, Started = os.clock(), false
repeat
	task.wait(0.1)
	if Player:GetAttribute("NHCineSeam") ~= nil then Started = true end
until Started or os.clock() - W0 > 40
if not Started then RunService:UnbindFromRenderStep(Name) return "HOLD FAIL\nthe cut never started" end
local HoldAt, ReleasedAt, LeaveAt = nil, nil, nil
repeat
	task.wait(0.05)
	if Player:GetAttribute("NHCineHold") == true and not HoldAt then HoldAt = os.clock() end
	if MODE == "leave" and HoldAt and not LeaveAt and os.clock() - HoldAt > 3 then
		LeaveAt = os.clock()
		Player:SetAttribute("NHTutorial", nil)
	end
	if HoldAt and not ReleasedAt and Player:GetAttribute("NHCineHold") ~= true then ReleasedAt = os.clock() end
until (Player:GetAttribute("NHCineSeam") == nil and not HoldAt and os.clock() - W0 > 33 and MODE == "replay")
	or (ReleasedAt and os.clock() - ReleasedAt > 1.5) or os.clock() - W0 > 70
task.wait(0.3)
RunService:UnbindFromRenderStep(Name)
local Last = Rows[#Rows]
if MODE == "replay" then
	local Out, EverHeld, HeadMax = 0, false, 0
	for _, R in Rows do
		if R.seam == "Out" then Out += 1 end
		if R.hold then EverHeld = true end
		HeadMax = math.max(HeadMax, R.head)
	end
	local N, T = animators(Source)
	chk("replay blends out", Out > 5 and not EverHeld and Last.seam == nil, string.format("Out frames %d, ever held %s", Out, tostring(EverHeld)))
	chk("shared bus untouched", (Source:GetPivot().Position - SrcPivot.Position).Magnitude < 1e-3 and N == SrcAnimators and T == 0 and not workspace:FindFirstChild("NHHometownCast"),
		string.format("pivot moved %.4f, Animators %d (was %d), playing tracks %d, cast folder %s", (Source:GetPivot().Position - SrcPivot.Position).Magnitude, N, SrcAnimators, T, tostring(workspace:FindFirstChild("NHHometownCast") ~= nil)))
	chk("player stays visible", HeadMax < 0.01, "max head LocalTransparencyModifier " .. HeadMax)
elseif MODE == "timeout" then
	local Dt = ReleasedAt and HoldAt and (ReleasedAt - HoldAt)
	chk("hold released by itself", Dt ~= nil and Dt >= 9.5 and Dt <= 12.5, "held " .. (Dt and string.format("%.2f s", Dt) or "never released"))
	-- (the cast stays: the player is still in Wickfield; it goes when NHTutorial clears)
	chk("handed back", Last.seam == nil and not Last.hold and Last.head < 0.01, string.format("hold %s, character visible again (head %.2f), camera %s", tostring(Last.hold), Last.head, tostring(Last.camType)))
else
	-- from the leave on: the first frame either the source or the character is visible must be at full black
	local First, Seen = nil, false
	for _, R in Rows do
		if LeaveAt and R.t >= LeaveAt then
			if (R.src < 0.5 or R.head < 0.5) and not First then First = R end
		end
	end
	chk("released", ReleasedAt ~= nil and not Last.hold, "hold released " .. tostring(ReleasedAt ~= nil))
	chk("nothing visible before black", First ~= nil and First.veil <= 0.02,
		First and string.format("first visible frame: veil transparency %.3f (0 = black), source LTM %.2f, head LTM %.2f", First.veil, First.src, First.head) or "never became visible")
	chk("everything back, cast gone", not Last.cast and Last.playing == 0 and Last.head < 0.01 and Last.src < 0.01, string.format("cast %s, bus tracks %d, head %.2f, source %.2f", tostring(Last.cast), Last.playing, Last.head, Last.src))
end
return (Pass and "HOLD OK " or "HOLD FAIL ") .. MODE .. "\n" .. table.concat(Report, "\n")
