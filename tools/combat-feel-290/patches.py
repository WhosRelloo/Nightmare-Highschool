# Combat feel set (concepts 1-4): counter-hits, directional hit reactions, heavy tells, combo counter + damage numbers.
# Every edit is tagged "(feel set)".
DMG = "ServerStorage.Packages.DamageLogic"
M1 = "ServerScriptService.Services.Player.ActionManager.Combat.M1"
RUN = "ServerScriptService.Services.Player.ActionManager.Combat.M1.Running M1"
UP = "ServerScriptService.Services.Player.ActionManager.Combat.Uppercut"
M2 = "ServerScriptService.Services.Player.ActionManager.Combat.M2"
M2F = "ServerStorage.Assets.M2.Fist"
SET = "ReplicatedStorage.UI.Settings"
MENU = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.SettingsMenu"
DT = "StarterPlayer.StarterPlayerScripts.Controllers.StateController.Misc.General.Damage Type"

EDITS = [
# ---------------- server: counter-hits ----------------
(DMG, r"""local MAX_REACH = 30 -- studs between attacker and target for a player's hit to count""",
      r"""local MAX_REACH = 30 -- studs between attacker and target for a player's hit to count
local COUNTER_STUN = 1.5 -- (feel set) a counter-hit stuns half as long again"""),
(DMG, r"""	local WasDowned = false
""",
      r"""	-- (feel set) a counter-hit: the target was winding up its own swing and hadn't reached its hit frame yet
	-- (NHWindupUntil, server time, set by M1 / Running M1 / M2 / Uppercut as the swing starts). It stuns longer and gets
	-- a bigger hit-stop, a flash and its own sound (StateController Damage Type).
	local Counter = false
	local WindupUntil = Target:GetAttribute(`NHWindupUntil`)
	if typeof(WindupUntil) == `number` and workspace:GetServerTimeNow() < WindupUntil and StateManager.HasState(Target, `Attacking`) then
		Counter = true
		Target:SetAttribute(`NHWindupUntil`, nil)
		if DamageData.Stun then DamageData.Stun *= COUNTER_STUN end
		DamageData.States.Stun = (DamageData.States.Stun or 0.4) * COUNTER_STUN
	end

	local WasDowned = false
"""),
(DMG, r"""		Packets.Replicate:Fire(`Misc`, `Damage Type`, { User = Target; Weapon = CharacterProfile.Weapon; Attacker = Character; Heavy = true }) -- (combat audit)""",
      r"""		Packets.Replicate:Fire(`Misc`, `Damage Type`, { User = Target; Weapon = CharacterProfile.Weapon; Attacker = Character; Heavy = true; Counter = Counter; Damage = DamageData.Damage }) -- (combat audit, feel set)"""),
(DMG, r"""	Packets.Replicate:Fire(`Misc`, `Damage Type`, { User = Target; Weapon = Weapon; Attacker = Character; Heavy = DamageData.Stun ~= nil or DamageData.AirDownslam == true })""",
      r"""	Packets.Replicate:Fire(`Misc`, `Damage Type`, { User = Target; Weapon = Weapon; Attacker = Character; Heavy = DamageData.Stun ~= nil or DamageData.AirDownslam == true;
		Counter = Counter; Damage = DamageData.Damage }) -- (feel set) the counter-hit and the number, for the readouts"""),
# ---------------- server: directional hit reactions ----------------
(DMG, r"""function Shared.Processed(DamageData: DamageData): boolean?""",
      r"""-- (feel set) the hit reaction follows where the hit came from. The four clips in Default.Hit, measured from their
-- keyframes: 1 and 2 double over forward (hips shift to the body's left / right), 3 and 4 snap the head back to the
-- left / right. Before, they simply cycled 1-4 whatever the direction.
local HIT_BY_SIDE = {
	Front = { `3`, `1`, `4`, `2` }; -- an exchange rocks side to side: head, body, head, body
	Back = { `1`, `2` }; -- shoved forward
	Right = { `3`, `1` }; -- hit on its right side: knocked to its left
	Left = { `4`, `2` }; -- hit on its left side: knocked to its right
}
function Local.HitReact(Attacker: Model, Target: Model, Count: number): Animation
	local Fallback = HitReacts[((Count - 1) % #HitReacts) + 1]
	local Ok, Rel = pcall(function() return Target:GetPivot():PointToObjectSpace(Attacker:GetPivot().Position) end)
	if not Ok then return Fallback end
	local Side = if -Rel.Z >= math.abs(Rel.X) then `Front` elseif Rel.Z >= math.abs(Rel.X) then `Back` elseif Rel.X > 0 then `Right` else `Left`
	local List = HIT_BY_SIDE[Side]
	return ReplicatedStorage.Assets.Animations.Default.Hit:FindFirstChild(List[((Count - 1) % #List) + 1]) or Fallback
end

function Shared.Processed(DamageData: DamageData): boolean?"""),
(DMG, r"""		local hitTrack = TrackService.Play(HitReacts[HitCount], Target, `Stun`, 0)""",
      r"""		local hitTrack = TrackService.Play(Local.HitReact(Character, Target, HitCount), Target, `Stun`, 0) -- (feel set) by direction"""),
# ---------------- server: the wind-up window on each swing ----------------
(M1, r"""		if Rate > 0 then EndLag /= Rate end""",
     r"""		if Rate > 0 then EndLag /= Rate end
		-- (feel set) until this swing's hit frame, a hit on you is a counter-hit (DamageLogic.TakeAction)
		self.Character:SetAttribute(`NHWindupUntil`, workspace:GetServerTimeNow() + (AnimMarkers.Time(Track, 'Hit') or 0.3) / (if Rate > 0 then Rate else 1))"""),
(M1, r"""		StateManager.RemoveAllStates(self.Character, `Freeze`)
	end;""",
     r"""		StateManager.RemoveAllStates(self.Character, `Freeze`)
		self.Character:SetAttribute(`NHWindupUntil`, nil) -- (feel set)
	end;"""),
(RUN, r"""	local Rate = if Track.Track.Speed > 0 then Track.Track.Speed else 1""",
      r"""	local Rate = if Track.Track.Speed > 0 then Track.Track.Speed else 1
	self.Character:SetAttribute(`NHWindupUntil`, workspace:GetServerTimeNow() + (Hit or 0.3) / Rate) -- (feel set) counter-hit window"""),
(UP, r"""		local EndLag = AnimMarkers.Time(Track, 'EndLag') or 1.2""",
     r"""		local EndLag = AnimMarkers.Time(Track, 'EndLag') or 1.2
		-- (feel set) a heavy tell, like M2's critical flash, so a defender can read the launcher coming; and its wind-up
		-- counts for counter-hits
		Packets.Replicate:Fire(`Indicators`, `CriticalIndicator`, { User = self.Character })
		self.Character:SetAttribute(`NHWindupUntil`, workspace:GetServerTimeNow() + (AnimMarkers.Time(Track, 'Hit') or 0.3) / 1.3)"""),
(UP, r"""		StateManager.RemoveState(self.Character, `Uppercutting`)
""",
     r"""		StateManager.RemoveState(self.Character, `Uppercutting`)
		self.Character:SetAttribute(`NHWindupUntil`, nil) -- (feel set)
"""),
(M2F, r"""	local EndLag = AnimMarkers.Time(Track, 'EndLag') or 0.6 -- (audit) nil without a marker = an endless Freeze""",
      r"""	local EndLag = AnimMarkers.Time(Track, 'EndLag') or 0.6 -- (audit) nil without a marker = an endless Freeze
	local SwingRate = (Track.Track and Track.Track.Speed) or 1
	self.Character:SetAttribute(`NHWindupUntil`, workspace:GetServerTimeNow() + (AnimMarkers.Time(Track, 'Hit') or 0.3) / (if SwingRate > 0 then SwingRate else 1)) -- (feel set)"""),
(M2, r"""		LinearVelocity.StopTaggedBodyMovers(self.Character, `M2Movement`)""",
     r"""		LinearVelocity.StopTaggedBodyMovers(self.Character, `M2Movement`)
		self.Character:SetAttribute(`NHWindupUntil`, nil) -- (feel set)"""),
# ---------------- settings: two toggles ----------------
(SET, r"""	AnimatedCursor = true,""",
      r"""	AnimatedCursor = true,
	ComboCounter = true, -- (feel set) your hit count while a string lands (StateController Damage Type)
	DamageNumbers = false, -- (feel set) numbers over what you hit; off by default"""),
(SET, r"""	  Keys[action]  -> InputController.Rebind(action, key)""",
      r"""	  ComboCounter / DamageNumbers -> read by StateController.Misc.General.Damage Type when your hit lands (feel set)
	  Keys[action]  -> InputController.Rebind(action, key)"""),
(MENU, r"""		Local.Note(`Off hides the weapon on your back while it's put away, for everyone. It always shows in your hand while it's out.`, 10)""",
       r"""		Local.Note(`Off hides the weapon on your back while it's put away, for everyone. It always shows in your hand while it's out.`, 10)
		-- (feel set) the combat readouts
		Local.Section(`Combat`, 11)
		Local.Toggle(`Combo Counter`, `ComboCounter`, 12)
		Local.Toggle(`Damage Numbers`, `DamageNumbers`, 13)
		Local.Note(`The combo counter shows your hit count while a string lands. Damage numbers float over what you hit.`, 14)"""),
# ---------------- client: counter flash, combo counter, damage numbers ----------------
(DT, r"""local function HitStop(Model: Model?, Duration: number)""",
     r"""-- (feel set) the readouts: a counter-hit flash and sound, your combo count, and optional damage numbers. Text only, in
-- the UI kit's fonts and colours; small, at the edge, and gone a moment after the string ends.
local TweenService = game:GetService(`TweenService`)
local CRIMSON = Color3.fromRGB(205, 58, 58)
local Readout = { N = 0; Last = 0; Gui = nil }
local function Setting(Key: string, Default: any): any
	local Ok, V = pcall(function() return require(ReplicatedStorage.UI.Settings).Get(Key) end)
	if Ok and V ~= nil then return V end
	return Default
end
local function Calm(): boolean return Players.LocalPlayer:GetAttribute(`NHReducedMotion`) == true end
local function Stroke(T: Instance) local S = Instance.new(`UIStroke`) S.Color = Color3.fromRGB(14, 10, 12) S.Thickness = 1.5 S.Transparency = 0.15 S.Parent = T end
local function ComboGui()
	if Readout.Gui and Readout.Gui.Parent then return Readout.Gui end
	local Kit = require(ReplicatedStorage.UI.Components)
	local Fonts, C = Kit.Theme.Fonts, Kit.Theme.Colors
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHComboCounter` G.ResetOnSpawn = false G.DisplayOrder = 4 G.IgnoreGuiInset = true
	local Root = Instance.new(`Frame`)
	Root.Name = `Root` Root.BackgroundTransparency = 1 Root.AnchorPoint = Vector2.new(1, 0.5)
	Root.Position = UDim2.new(1, -36, 0.4, 0) Root.Size = UDim2.fromOffset(160, 92) Root.Parent = G
	Instance.new(`UIScale`, Root).Name = `Pop`
	local Tag = Kit.Text({ Name = `Counter`; Text = `COUNTER`; Font = Fonts.Title; TextSize = 17; TextColor3 = CRIMSON; TextXAlignment = Enum.TextXAlignment.Right;
		Position = UDim2.fromOffset(0, 0); Size = UDim2.new(1, 0, 0, 20); Visible = false; Parent = Root })
	local Num = Kit.Text({ Name = `Count`; Text = `2`; Font = Fonts.Title; TextSize = 46; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Right;
		Position = UDim2.fromOffset(0, 18); Size = UDim2.new(1, 0, 0, 48); Parent = Root })
	local Word = Kit.Text({ Name = `Hits`; Text = `H I T S`; Font = Fonts.Title; TextSize = 13; TextColor3 = C.TextDim; TextXAlignment = Enum.TextXAlignment.Right;
		Position = UDim2.fromOffset(0, 66); Size = UDim2.new(1, 0, 0, 16); Parent = Root })
	for _, T in { Tag, Num, Word } do Stroke(T) end
	G.Parent = Players.LocalPlayer:WaitForChild(`PlayerGui`)
	Readout.Gui = G
	return G
end
local function Fade(G: ScreenGui, To: number, Time: number)
	for _, T in G.Root:GetChildren() do
		if T:IsA(`TextLabel`) then
			TweenService:Create(T, TweenInfo.new(Time), { TextTransparency = To }):Play()
			local S = T:FindFirstChildOfClass(`UIStroke`)
			if S then TweenService:Create(S, TweenInfo.new(Time), { Transparency = math.max(To, 0.15) }):Play() end
		end
	end
end
local function ShowCombo(Counter: boolean)
	local Now = os.clock()
	Readout.N = if Now - Readout.Last <= 1.6 then Readout.N + 1 else 1
	Readout.Last = Now
	if Readout.N < 2 and not Counter then return end -- one hit isn't a combo: nothing on screen
	local G = ComboGui()
	G.Root.Count.Text = tostring(Readout.N)
	G.Root.Count.Visible = Readout.N >= 2
	G.Root.Hits.Visible = Readout.N >= 2
	G.Root.Counter.Visible = Counter or (G.Root.Counter.Visible and Now - (Readout.CounterAt or 0) < 0.8)
	if Counter then Readout.CounterAt = Now end
	Fade(G, 0, 0.06)
	if not Calm() then
		G.Root.Pop.Scale = 1.22
		TweenService:Create(G.Root.Pop, TweenInfo.new(0.14, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
	end
	task.delay(1.6, function() if Readout.Last == Now and Readout.Gui then Fade(Readout.Gui, 1, 0.35) end end)
end
local function DamageNumber(Target: Model, Damage: number, Heavy: boolean, Counter: boolean)
	local Head = Target:FindFirstChild(`Head`) or Target:FindFirstChild(`HumanoidRootPart`)
	if not Head then return end
	local Kit = require(ReplicatedStorage.UI.Components)
	local B = Instance.new(`BillboardGui`)
	B.Name = `NHDamageNumber` B.Size = UDim2.fromOffset(90, 34) B.AlwaysOnTop = true B.LightInfluence = 0 B.MaxDistance = 90
	B.StudsOffsetWorldSpace = Vector3.new(math.random(-8, 8) / 10, 2.1, 0) B.Adornee = Head
	local V = math.floor(Damage * 10 + 0.5) / 10
	local T = Kit.Text({ Text = if V == math.floor(V) then tostring(math.floor(V)) else string.format(`%.1f`, V); Font = Kit.Theme.Fonts.Title;
		TextSize = if Heavy or Counter then 24 else 18; TextColor3 = if Counter then CRIMSON elseif Heavy then Kit.Theme.Colors.Gold else Color3.fromRGB(236, 228, 214);
		TextXAlignment = Enum.TextXAlignment.Center; Size = UDim2.fromScale(1, 1); Parent = B })
	Stroke(T)
	B.Parent = Players.LocalPlayer:WaitForChild(`PlayerGui`)
	local Rise = if Calm() then 0.4 else 1.3
	TweenService:Create(B, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { StudsOffsetWorldSpace = B.StudsOffsetWorldSpace + Vector3.new(0, Rise, 0) }):Play()
	TweenService:Create(T, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.35), { TextTransparency = 1 }):Play()
	Debris:AddItem(B, 0.8)
end
local function CounterFlash(Target: Model)
	local Root = Target:FindFirstChild(`HumanoidRootPart`)
	local S = ReplicatedStorage.Assets.Sounds.Default:FindFirstChild(`Critical`)
	if S and Root then
		local Ok, C = pcall(EmitManager.CloneSound, S, Root)
		if Ok and typeof(C) == `Instance` and C:IsA(`Sound`) then C.PlaybackSpeed = 1.35 end
	end
	if Players.LocalPlayer:GetAttribute(`NHReducedFlash`) == true then return end
	local Hl = Instance.new(`Highlight`)
	Hl.FillColor = Color3.new(1, 1, 1) Hl.OutlineColor = Color3.new(1, 1, 1)
	Hl.FillTransparency = 0.45 Hl.OutlineTransparency = 0.1 Hl.DepthMode = Enum.HighlightDepthMode.Occluded
	Hl.Adornee = Target Hl.Parent = workspace:FindFirstChild(`Visuals`) or workspace
	TweenService:Create(Hl, TweenInfo.new(0.22, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { FillTransparency = 1; OutlineTransparency = 1 }):Play()
	Debris:AddItem(Hl, 0.3)
end
local function Readouts(Paramaters, Me: Model?, Heavy: boolean, Counter: boolean)
	if Counter then CounterFlash(Paramaters.User) end
	if not (Me and Paramaters.Attacker == Me) then return end
	if Setting(`ComboCounter`, true) then ShowCombo(Counter) end
	if Setting(`DamageNumbers`, false) and typeof(Paramaters.Damage) == `number` then DamageNumber(Paramaters.User, Paramaters.Damage, Heavy, Counter) end
end

local function HitStop(Model: Model?, Duration: number)"""),
(DT, r"""	local Hold = if Heavy then 0.1 else 0.05""",
     r"""	local Counter = Paramaters.Counter == true -- (feel set)
	local Hold = if Heavy or Counter then 0.1 else 0.05"""),
(DT, r"""		EmitManager.ShakeCamera(if Heavy then 3 else 1.4, 10, 0, if Heavy then 0.3 else 0.16)
	end
""",
     r"""		EmitManager.ShakeCamera(if Heavy or Counter then 3 else 1.4, 10, 0, if Heavy or Counter then 0.3 else 0.16)
	end
	pcall(Readouts, Paramaters, Me, Heavy, Counter) -- (feel set) a readout must never stop the hit's own effects
"""),
]

# ---- then, applied on top: the combo counter moved clear of the quest tracker (q9b)
# Feel set, play-test fix: the combo counter sat behind the quest tracker; moved to the clear right edge at 60% height.
DT = "StarterPlayer.StarterPlayerScripts.Controllers.StateController.Misc.General.Damage Type"
EDITS_FIX = [
(DT, r"""	G.Name = `NHComboCounter` G.ResetOnSpawn = false G.DisplayOrder = 4 G.IgnoreGuiInset = true""",
     r"""	G.Name = `NHComboCounter` G.ResetOnSpawn = false G.DisplayOrder = 6 G.IgnoreGuiInset = true"""),
(DT, r"""	Root.Position = UDim2.new(1, -36, 0.4, 0) Root.Size = UDim2.fromOffset(160, 92) Root.Parent = G""",
     r"""	Root.Position = UDim2.new(1, -40, 0.6, 0) Root.Size = UDim2.fromOffset(160, 92) Root.Parent = G -- clear of the quest tracker (40% sat behind it)"""),
]
