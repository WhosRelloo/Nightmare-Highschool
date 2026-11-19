--[[
	Moments (client). Controllers.Gui.Moments  -- VFX Batch 2 "core feedback" (vault: Docs/VFX-Design-Bible.md)

	One queue, at most one Moment banner on screen at a time (style guide: "Moment" tier). Each beat replaces
	its old toast, so nothing shows twice.

		P0-8  School Bell & Period Card   ReplicatedStorage.SchoolClock "Period" changes (never on join)
		P1-4  Quest Beat banner           NHFx "QuestBeat" { Type = Start|Stage|Complete|Fail, Title, Text, Category, Story }
		P1-5  Clue Discovered             NHFx "Clue" { Name, Case, Pos? }  ink sparkles + a "+CLUE" slip into the Journal
		P1-6  Level-up "Bell Toll"        NHFx "LevelUp" { UserId, Level, Points }  (sent to players within 80 studs)
		P1-8  Purchase granted            NHFx "Purchase" { Title, Text }
		P1-9  "Roll call" respawn         client-only: any player's CharacterAdded after a death (never the menu spawn)

	Everything follows the settings through Controllers.Fx (shake, reduced flashing / motion, effects quality),
	and pauses while the player is in the main menu or mid tier-up (character attribute NH_Evolving).

	Dialogue: quests are accepted by choosing a reply, so a quest banner usually fires while the dialogue box
	(PlayerGui.Dialogue.Box, bottom of the screen) is open. Banners wait up to DIALOGUE_HOLD seconds for the
	conversation to end; if it is still open, or opens while a banner is up, the banner lifts to sit just
	above the box so it never covers the replies.
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local SoundService = game:GetService(`SoundService`)
local TweenService = game:GetService(`TweenService`)
local Lighting = game:GetService(`Lighting`)
local TextService = game:GetService(`TextService`)
local RunService = game:GetService(`RunService`)
local GuiService = game:GetService(`GuiService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Fx = require(script.Parent.Parent:WaitForChild(`Fx`))
local Classes = require(ReplicatedStorage.Config.Classes)
local SchoolTime = require(ReplicatedStorage.Functions.SchoolTime)

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local Fonts = Theme.Fonts

local GOLD = C.Gold
local IRON = C.Chalk
local FAIL = C.Danger
local INK_BLUE = Color3.fromRGB(92, 128, 210)
local VIOLET = Color3.fromRGB(120, 92, 190)

-- Roblox-licensed Pro Sound Effects (Creator Store), routed to the Effects volume.
local SOUNDS = {
	Bell = { Id = `rbxassetid://9113584435`, Volume = 0.32, Length = 2.4 },      -- Brass Hand Bell 7
	Stamp = { Id = `rbxassetid://9119907907`, Volume = 0.45, Length = 0.5 },     -- palm on wood (kit Stamp)
	Chime = { Id = `rbxassetid://9114058995`, Volume = 0.25, Length = 0.8 },     -- desk bell (kit Confirm)
	Tick = { Id = `rbxassetid://9120300134`, Volume = 0.3, Length = 0.4 },       -- typewriter key (kit Tick)
}

-- Which period changes ring the bell (the start and end of the school day's blocks).
local RING_KINDS = { Class = true; Passing = true; Break = true; Lunch = true; AfterSchool = true }
local CARD_KINDS = { Class = true; Passing = true; Break = true; Lunch = true; AfterSchool = true; BeforeSchool = true }

local Local = {}
local Shared = {}

---| sound |---

function Local.Sound(Name: string, VolumeScale: number?)
	local Def = SOUNDS[Name]
	if not Def then return end
	local S = Instance.new(`Sound`)
	S.Name = `NHMoment{Name}`
	S.SoundId = Def.Id
	S.Volume = Def.Volume * (VolumeScale or 1)
	local Master = SoundService:FindFirstChild(`NH_Master`)
	local Group = Master and Master:FindFirstChild(`NH_Effects`)
	if Group and Group:IsA(`SoundGroup`) then S.SoundGroup = Group end
	S.Parent = SoundService
	S:Play()
	task.delay(Def.Length, function()
		if not S.Parent then return end
		TweenService:Create(S, TweenInfo.new(0.35), { Volume = 0 }):Play()
		task.delay(0.4, function() S:Destroy() end)
	end)
end

---| screen |---

local Gui: ScreenGui? = nil
local function gui(): ScreenGui
	if Gui and Gui.Parent then return Gui end
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHMoments`
	G.ResetOnSpawn = false
	G.DisplayOrder = 11 -- above toasts (10), below menus
	G.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	Kit.AutoScale(G)
	G.Parent = Player:WaitForChild(`PlayerGui`)
	Gui = G
	return G
end

local function uiScale(): number
	local U = gui():FindFirstChild(`NHAutoScale`)
	return if U and U:IsA(`UIScale`) and U.Scale > 0 then U.Scale else 1
end

---| queue: one Moment at a time |---

local Queue = {} :: { () -> () }
local Pumping = false
local MAX_QUEUE = 6
local DIALOGUE_HOLD = 6 -- seconds a banner waits for an open conversation to end

function Local.Blocked(): boolean
	if Player:GetAttribute(`InMainMenu`) == true then return true end
	local Char = Player.Character
	return Char ~= nil and Char:GetAttribute(`NH_Evolving`) == true
end

function Local.Enqueue(Fn: () -> ())
	if #Queue >= MAX_QUEUE then table.remove(Queue, 1) end
	table.insert(Queue, Fn)
	if Pumping then return end
	Pumping = true
	task.spawn(function()
		while #Queue > 0 do
			local Waited = 0
			while Local.Blocked() and Waited < 30 do
				Waited += task.wait(0.25)
			end
			local Held = 0
			while Player:GetAttribute(`InDialogue`) == true and Held < DIALOGUE_HOLD do
				Held += task.wait(0.25)
			end
			local Next = table.remove(Queue, 1)
			local Ok, Err = pcall(Next)
			if not Ok then warn(`[Moments] {Err}`) end
		end
		Pumping = false
	end)
end

---| the banner |---

local WIDTH = 580
local BANNER_POS = UDim2.new(0.5, 0, 0.745, 0)
local DIALOGUE_GAP = 10 -- px between a lifted banner and the top of the dialogue box

-- top edge in screen pixels (a ScreenGui that keeps the top inset measures from below it)
function Local.ScreenTop(G: GuiObject): number
	local Sg = G:FindFirstAncestorWhichIsA(`ScreenGui`)
	local Inset = if Sg and Sg.IgnoreGuiInset then 0 else GuiService:GetGuiInset().Y
	return G.AbsolutePosition.Y + Inset
end

-- the dialogue box while a conversation is on screen
function Local.DialogueBox(): GuiObject?
	if Player:GetAttribute(`InDialogue`) ~= true then return nil end
	local D = Player.PlayerGui:FindFirstChild(`Dialogue`)
	local Box = D and D:FindFirstChild(`Box`)
	if not (Box and Box:IsA(`GuiObject`) and Box.Visible) then return nil end
	if D:IsA(`ScreenGui`) and not D.Enabled then return nil end
	return Box
end

-- keep a banner clear of the dialogue box: lift it just above the box, and back down once the box is gone.
-- Run every frame while the banner is up, so it also follows a box that opens, grows or closes mid-banner.
function Local.Fit(Root: GuiObject)
	local Box = Local.DialogueBox()
	local Offset = Root.Position.Y.Offset
	local Want = 0
	if Box then
		local Bottom = Local.ScreenTop(Root) + Root.AbsoluteSize.Y -- AbsolutePosition is always the top-left corner
		local Over = Bottom - (Local.ScreenTop(Box) - DIALOGUE_GAP)
		Want = math.min(0, Offset - Over / uiScale())
	end
	if math.abs(Want - Offset) > 0.5 then
		Root.Position = UDim2.new(BANNER_POS.X.Scale, BANNER_POS.X.Offset, BANNER_POS.Y.Scale, Want)
	end
end

-- wrapped height of a text block in design px (falls back to an estimate)
function Local.Measure(Text: string, FontArg: any, Size: number, Width: number): number -- (audit) a param named Font hid the Font datatype
	local Ok, H = pcall(function()
		local Params = Instance.new(`GetTextBoundsParams`)
		Params.Text = Text
		Params.Size = Size
		Params.Width = Width
		Params.Font = if typeof(FontArg) == `EnumItem` then Font.fromEnum(FontArg) else FontArg
		return TextService:GetTextBoundsAsync(Params).Y
	end)
	if Ok and typeof(H) == `number` and H > 0 then return math.ceil(H) end
	return math.ceil(#Text / 52) * math.ceil(Size * 1.3)
end

--[[ Opts: Caption, Title, Text, Color, Icon (a Theme.Images key: IconBanner*, Bell, IconNib), Glyph (short text on the icon), Hold, Sound
	Yields until the banner has gone. ]]
function Local.Banner(Opts)
	local Color = Opts.Color or GOLD
	local HasText = Opts.Text ~= nil and Opts.Text ~= ``
	local X = 98
	local BodyTop = if Opts.Caption then 60 else 50
	local BodySize = Theme.Sizes.TextSmall + 2
	-- story text is never cut off: the banner grows to fit the wrapped body
	local BodyH = if HasText then Local.Measure(Opts.Text, Fonts.Body, BodySize, WIDTH - X - 22) else 0
	local Height = math.max(76, if HasText then BodyTop + BodyH + 16 else (if Opts.Caption then 70 else 62))
	local Long = BodyH > BodySize * 2

	local Root = Instance.new(`Frame`)
	Root.Name = `MomentBanner`
	Root.AnchorPoint = Vector2.new(0.5, 1)
	Root.Position = BANNER_POS -- low centre, above the health bar and clear of the toast stack
	Root.Size = UDim2.fromOffset(WIDTH, Height)
	Root.BackgroundTransparency = 1
	Kit.Decorate(Root, { ornamentScale = 0.5, bgTransparency = 0.06, frameColor = Color:Lerp(C.Iron, 0.35) })

	local IconKey = Opts.Icon or `IconNoteMilestone`
	local Seal = Kit.Image(IconKey, {
		Name = `Seal`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0, 52, 0.5, 0);
		Size = UDim2.fromOffset(60, 60); ImageColor3 = if Theme.Baked and Theme.Baked[IconKey] then Color3.new(1, 1, 1) else Color; ZIndex = 8; Parent = Root;
	})
	if Opts.Glyph then
		Kit.Text({
			Name = `Glyph`; Text = Opts.Glyph; Font = Fonts.Title; TextSize = if #Opts.Glyph > 2 then 17 else 24;
			TextColor3 = C.Ink; TextStrokeTransparency = 1; TextXAlignment = Enum.TextXAlignment.Center;
			Size = UDim2.fromScale(1, 1); ZIndex = 9; Parent = Seal;
		})
	end

	if Opts.Caption then
		Kit.Text({
			Name = `Caption`; Text = string.upper(Opts.Caption); Font = Fonts.Title; TextSize = Theme.Sizes.TextTiny;
			TextColor3 = Color:Lerp(C.Text, 0.25); TextXAlignment = Enum.TextXAlignment.Left;
			Position = UDim2.fromOffset(X, 12); Size = UDim2.new(1, -X - 22, 0, 16); ZIndex = 8; Parent = Root;
		})
	end
	local Title = Kit.Text({
		Name = `Title`; Text = Opts.Title or ``; Font = Fonts.Title; TextSize = 25;
		TextColor3 = Color:Lerp(C.Text, 0.55); TextXAlignment = Enum.TextXAlignment.Left;
		TextTruncate = Enum.TextTruncate.AtEnd;
		Position = UDim2.fromOffset(X, if Opts.Caption then 28 else 18); Size = UDim2.new(1, -X - 22, 0, 30);
		ZIndex = 8; Parent = Root;
	})
	Kit.Emboss(Title, Color:Lerp(C.Ink, 0.4), 1.4)
	if HasText then
		Kit.Text({
			Name = `Body`; Text = Opts.Text; Font = Fonts.Body; TextSize = BodySize;
			TextColor3 = C.Text; TextXAlignment = Enum.TextXAlignment.Left; TextYAlignment = Enum.TextYAlignment.Top;
			TextWrapped = true;
			Position = UDim2.fromOffset(X, BodyTop); Size = UDim2.new(1, -X - 22, 0, BodyH + 4);
			ZIndex = 8; Parent = Root;
		})
	end

	-- single gold sheen across the title
	local Sheen = Instance.new(`UIGradient`)
	Sheen.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0); NumberSequenceKeypoint.new(0.45, 0); NumberSequenceKeypoint.new(0.5, 0.6);
		NumberSequenceKeypoint.new(0.55, 0); NumberSequenceKeypoint.new(1, 0);
	})
	Sheen.Offset = Vector2.new(-1, 0)

	Root.Parent = gui()
	Local.Fit(Root)
	local FitConn = RunService.RenderStepped:Connect(function() Local.Fit(Root) end)
	Kit.FadeIn(Root, 0.25)
	if not Fx.Reduced() then
		local Slide = Instance.new(`UIScale`)
		Slide.Scale = 0.92
		Slide.Parent = Root
		TweenService:Create(Slide, TweenInfo.new(0.3, Enum.EasingStyle.Back), { Scale = 1 }):Play()
		task.delay(0.08, function()
			if Seal.Parent then Fx.Pop(Seal, 1.6, 0.18) end
		end)
		Sheen.Parent = Title
		TweenService:Create(Sheen, TweenInfo.new(0.9, Enum.EasingStyle.Sine), { Offset = Vector2.new(1, 0) }):Play()
	end
	if Opts.Sound then Local.Sound(Opts.Sound) end
	task.delay(0.1, function() Local.Sound(`Stamp`, 0.6) end)

	local Hold = Opts.Hold or (if Long then 4.5 else 2.6)
	task.wait(0.25 + Hold)
	local Out = Kit.FadeOut(Root, 0.4)
	if Out then Out.Completed:Wait() else task.wait(0.4) end
	FitConn:Disconnect()
	Root:Destroy()
end

---| P0-8 School Bell & Period Card |---

function Local.ClockRim()
	local Hud = Player.PlayerGui:FindFirstChild(`ClockHud`)
	local Panel = Hud and Hud:FindFirstChild(`Panel`)
	if not Panel then return end
	local Rim = Kit.Slice(`FrameThin`, GOLD, { Name = `BellRim`; SliceScale = 0.45; ZIndex = 9; ImageTransparency = 0; Parent = Panel })
	Rim.Size = UDim2.fromScale(1, 1)
	local Tw = TweenService:Create(Rim, TweenInfo.new(1.1, Enum.EasingStyle.Sine), { ImageTransparency = 1 })
	Tw.Completed:Connect(function() Rim:Destroy() end)
	Tw:Play()
end

function Local.PulseWaypoint()
	local W = Player.PlayerGui:FindFirstChild(`ClassWaypoint`)
	if not (W and W:IsA(`BillboardGui`) and W.Enabled) then return end
	local Base = W.Size
	task.spawn(function()
		for _ = 1, 2 do
			if not W.Parent then return end
			local Up = TweenService:Create(W, TweenInfo.new(0.18, Enum.EasingStyle.Quad), { Size = UDim2.new(Base.X.Scale, Base.X.Offset * 1.25, Base.Y.Scale, Base.Y.Offset * 1.25) })
			Up:Play()
			Up.Completed:Wait()
			local Down = TweenService:Create(W, TweenInfo.new(0.3, Enum.EasingStyle.Sine), { Size = Base })
			Down:Play()
			Down.Completed:Wait()
		end
	end)
end

function Local.Bell(Clock: Instance)
	local Epoch = Clock:GetAttribute(`Epoch`)
	if not Epoch then return end
	local State = SchoolTime.GetState(Epoch, workspace:GetServerTimeNow())
	local Seg = State.Segment
	if not CARD_KINDS[Seg.Kind] then return end
	local Ring = RING_KINDS[Seg.Kind] == true

	local Caption, Title, Text
	local Until = SchoolTime.FormatClock(Seg.End)
	if Seg.Kind == `Class` then
		local Class = Classes.Periods[Seg.Name]
		Caption = `The bell rings`
		Title = Seg.Name
		if Class then
			local Room = Classes.Rooms and Classes.Rooms[Class.Room] or Class.Room
			Text = `{Class.Subject} · {Room} · until {Until}`
		else
			Text = `Until {Until}`
		end
	elseif Seg.Kind == `BeforeSchool` then
		Caption, Title, Text = `The gates open`, `Before School`, `Homeroom at {SchoolTime.FormatClock(Seg.End)}`
	elseif Seg.Kind == `AfterSchool` then
		Caption, Title, Text = `The bell rings`, `Classes are over`, `After school until {Until}`
	else
		Caption, Title, Text = `The bell rings`, Seg.Name, `Until {Until}`
	end

	-- the bell itself rings at once, even if a banner is still showing
	if Ring then
		Local.Sound(`Bell`)
		Local.ClockRim()
		if Seg.Kind == `Class` then task.delay(0.7, Local.PulseWaypoint) end
	end
	Local.Enqueue(function()
		Local.Banner({ Caption = Caption; Title = Title; Text = Text; Icon = `Bell`; Color = GOLD; Hold = 2.5 })
	end)
end

function Local.StartBell()
	local Clock = ReplicatedStorage:WaitForChild(`SchoolClock`)
	local Last = Clock:GetAttribute(`Period`) -- the value at join is a baseline, never a ring
	Clock:GetAttributeChangedSignal(`Period`):Connect(function()
		local Now = Clock:GetAttribute(`Period`)
		if Now == Last then return end
		local First = Last == nil
		Last = Now
		if First or Local.Blocked() then return end
		Local.Bell(Clock)
	end)
end

---| P1-4 Quest beats |---

function Local.RaceColor(): Color3
	local Ok, Col = pcall(function()
		local Lineage = require(ReplicatedStorage.Lineage)
		local Race = Player:GetAttribute(`Race`)
		local R = Race and Lineage.Races and Lineage.Races[Race]
		return R and R.Color
	end)
	return if Ok and typeof(Col) == `Color3` then Col else C.Crimson
end

function Local.QuestBeat(D)
	if typeof(D) ~= `table` then return end
	local Color = if D.Category == `Main` then GOLD elseif D.Category == `Rite` then Local.RaceColor() else IRON
	if D.Type == `Start` then
		Local.Enqueue(function()
			Local.Banner({ Caption = if D.Category == `Main` then `New main quest` else `New quest`; Title = D.Title; Text = D.Text; Color = Color; Icon = `IconBannerQuestNew`; Sound = `Chime` })
		end)
	elseif D.Type == `Stage` then
		Local.Enqueue(function()
			Local.Banner({ Caption = `New objective`; Title = D.Title; Text = D.Text; Color = Color; Icon = `IconBannerQuestStep`; Hold = 2.2 })
		end)
	elseif D.Type == `Complete` then
		Local.Enqueue(function()
			Local.Banner({ Caption = `Quest complete`; Title = D.Title; Text = D.Text; Color = Color; Icon = `IconBannerQuestDone`; Sound = `Chime` })
			if typeof(D.Story) == `string` and D.Story ~= `` then
				Local.Banner({ Caption = `Epilogue`; Title = D.Title; Text = D.Story; Color = C.Chalk; Icon = `IconNib`; Hold = math.clamp(#D.Story * 0.055, 4, 9) })
			end
		end)
	elseif D.Type == `Fail` then
		Local.Enqueue(function()
			Local.Banner({ Caption = `Quest failed`; Title = D.Title; Text = D.Text; Color = FAIL; Icon = `IconBannerQuestFailed`; Hold = 3.2 })
		end)
	end
end

---| (2.31) Standing Path tier |---

function Local.PathTier(D)
	if typeof(D) ~= `table` or typeof(D.Name) ~= `string` then return end
	Local.Enqueue(function()
		Local.Banner({ Caption = `Standing: {D.Path or ``}`; Title = string.upper(D.Name); Text = `The {D.Path} path, tier {D.Tier} of {D.Of}.`;
			Color = GOLD; Icon = `IconBannerQuestDone`; Sound = `Chime`; Hold = 3.2 })
	end)
end

---| P1-5 Clue Discovered |---

function Local.ClueWorld(Pos: Vector3)
	Fx.Burst(Pos, {
		Texture = Fx.Tex.Shards; Flipbook = `Grid2x2`; Count = 16;
		Color = ColorSequence.new(GOLD, INK_BLUE); Size = 0.35;
		Speed = NumberRange.new(1, 3); Spread = 70; Accel = Vector3.new(0, 2.5, 0);
		Lifetime = NumberRange.new(0.7, 1.3); LightEmission = 0.8;
	})
	Fx.Light(Pos, GOLD, 1.6, 10, 1)
	-- flash the found object, then fade (never a hard pop)
	local Params = OverlapParams.new()
	local Best, BestD = nil, math.huge
	for _, P in workspace:GetPartBoundsInRadius(Pos, 2, Params) do
		if P:GetAttribute(`QuestObject`) then
			local Dd = (P.Position - Pos).Magnitude
			if Dd < BestD then Best, BestD = P, Dd end
		end
	end
	if Best then
		local H = Instance.new(`Highlight`)
		H.Name = `NHClueFlash`
		H.FillColor = GOLD
		H.OutlineColor = GOLD
		H.FillTransparency = 0.55
		H.OutlineTransparency = 0
		H.DepthMode = Enum.HighlightDepthMode.Occluded
		H.Adornee = Best
		H.Parent = Best
		local Tw = TweenService:Create(H, TweenInfo.new(1.3, Enum.EasingStyle.Sine), { FillTransparency = 1; OutlineTransparency = 1 })
		Tw.Completed:Connect(function() H:Destroy() end)
		Tw:Play()
	end
end

function Local.TextWidth(Text: string, Size: number): number
	local Ok, W = pcall(function()
		local F = Fonts.Title
		return TextService:GetTextSize(Text, Size, if typeof(F) == `EnumItem` then F else Enum.Font.Garamond, Vector2.new(2000, 100)).X
	end)
	return if Ok and typeof(W) == `number` then W else #Text * Size * 0.55
end

function Local.ClueSlip(D)
	local Root = gui()
	local Label = `+ CLUE  ·  {D.Name or `Clue`}`
	local Slip = Kit.Plate({ text = Label; color = GOLD; textSize = 19; frameColor = GOLD:Lerp(C.Iron, 0.4) })
	Slip.Name = `ClueSlip`
	Slip.AnchorPoint = Vector2.new(0.5, 0.5)
	Slip.Position = UDim2.new(0.5, 0, 0.6, 0)
	Slip.Size = UDim2.fromOffset(math.clamp(Local.TextWidth(Label, 19) + 60, 220, 560), 44)
	Slip.ZIndex = 20
	Slip.Parent = Root
	local Sub = Kit.Text({
		Name = `Case`; Text = `Added to your case file{if D.Case then ` (` .. D.Case .. `)` else ``}`; Font = Fonts.Body;
		TextSize = Theme.Sizes.TextSmall; TextColor3 = C.Text; TextXAlignment = Enum.TextXAlignment.Center;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 1, 6); Size = UDim2.fromOffset(420, 20); ZIndex = 20; Parent = Slip;
	})
	Kit.FadeIn(Slip, 0.2)
	Fx.Pop(Slip, 1.4, 0.22)
	Local.Sound(`Tick`)
	task.delay(0.12, function() Local.Sound(`Stamp`, 0.5) end)
	task.wait(1.4)
	Sub:Destroy()

	-- fly to the Journal button (left edge), shrinking
	local Journal = Player.PlayerGui:FindFirstChild(`QuestJournal`)
	local Toggle = Journal and Journal:FindFirstChild(`Toggle`)
	local Scale = uiScale()
	local Target
	if Toggle and Toggle:IsA(`GuiObject`) and Toggle.Visible then
		-- both screens use the same inset, so absolute px / our design scale = our offset
		local Abs = Toggle.AbsolutePosition + Toggle.AbsoluteSize / 2
		Target = UDim2.fromOffset(Abs.X / Scale, Abs.Y / Scale)
	else
		Target = UDim2.new(0, 90, 0.5, 78)
	end
	local Time = if Fx.Reduced() then 0.25 else 0.55
	local Fly = TweenService:Create(Slip, TweenInfo.new(Time, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Position = Target })
	local U = Instance.new(`UIScale`)
	U.Parent = Slip
	TweenService:Create(U, TweenInfo.new(Time, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Scale = 0.35 }):Play()
	Fly:Play()
	Fly.Completed:Wait()
	if Toggle and Toggle:IsA(`GuiObject`) then Fx.Pop(Toggle, 1.2, 0.25) end
	local Out = Kit.FadeOut(Slip, 0.15)
	if Out then Out.Completed:Wait() end
	Slip:Destroy()
end

function Local.Clue(D)
	if typeof(D) ~= `table` then return end
	if typeof(D.Pos) == `Vector3` then Local.ClueWorld(D.Pos) end
	Local.Enqueue(function() Local.ClueSlip(D) end)
end

---| P1-6 Level-up "Bell Toll" |---

function Local.LevelUp(D)
	if typeof(D) ~= `table` then return end
	local Who = Players:GetPlayerByUserId(D.UserId or 0)
	local Char = Who and Who.Character
	local Root = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Mine = Who == Player
	if Root and (Mine or Fx.Near(Root.Position, 80)) then
		local Feet = Root.Position - Vector3.new(0, 2.8, 0)
		Fx.Burst(Feet, {
			Texture = Fx.Tex.Ember; Count = 40; Color = ColorSequence.new(Color3.fromRGB(255, 226, 150), GOLD);
			Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 0) });
			Speed = NumberRange.new(6, 11); Spread = 14; Accel = Vector3.new(0, 3, 0); Drag = 1.2;
			Lifetime = NumberRange.new(0.8, 1.4); LightEmission = 1;
		})
		Fx.Ring(Feet + Vector3.new(0, 0.1, 0), GOLD, 9, nil, 0.6)
		Fx.Light(Root.Position, GOLD, 2, 12, 1.2)
	end
	if not Mine then return end
	Local.Sound(`Bell`, 0.8)
	Fx.Shake(0.6, 0.35)
	Local.Enqueue(function()
		Local.Banner({
			Caption = `Level up`; Title = `Level {D.Level or `?`}`; Color = GOLD; Icon = `IconBannerLevelUp`; Glyph = tostring(D.Level or ``);
			Text = if D.Points and D.Points > 0 then `+{D.Points} stat points. Open your record (M) to spend them.` else nil;
		})
	end)
end

---| P1-8 Purchase granted |---

function Local.Purchase(D)
	if typeof(D) ~= `table` then return end
	Local.Enqueue(function()
		Local.Banner({ Caption = `Purchase complete`; Title = D.Title or `Thank you!`; Text = D.Text; Color = GOLD; Icon = `IconBannerPurchase`; Sound = `Chime` })
	end)
end

---| P1-17 tier-up: the "Evolved" banner, after the cutscene |---

-- The server fires this as the cutscene starts; the queue holds it while NH_Evolving is set, so it lands after.
function Local.Evolved(D)
	if typeof(D) ~= `table` then return end
	task.wait(0.5) -- let the NH_Evolving flag arrive first
	local Roman = { `I`, `II`, `III` }
	local Ok, Col = pcall(function()
		return require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`RaceFX`)).Color(D.Race)
	end)
	Local.Enqueue(function()
		Local.Banner({
			Caption = `Evolved`; Title = D.Name or `Evolved`; Color = if Ok and typeof(Col) == `Color3` then Col else C.Crimson;
			Text = `Tier {Roman[D.Tier or 0] or tostring(D.Tier)} {D.Race or ``}`; Icon = `IconBannerEvolved`; Sound = `Chime`;
		})
	end)
end

---| P1-9 "Roll call" respawn |---

function Local.OwnRespawn()
	local Veil = Instance.new(`Frame`)
	Veil.Name = `RollCallVeil`
	Veil.BorderSizePixel = 0
	Veil.BackgroundColor3 = C.Ink
	Veil.BackgroundTransparency = 0
	Veil.Size = UDim2.new(1, 0, 1, 80)
	Veil.Position = UDim2.fromOffset(0, -60)
	Veil.ZIndex = 30
	Veil.Parent = gui()
	local Tw = TweenService:Create(Veil, TweenInfo.new(0.5, Enum.EasingStyle.Sine), { BackgroundTransparency = 1 })
	Tw.Completed:Connect(function() Veil:Destroy() end)
	Tw:Play()
	-- colour comes back over 0.8 s
	local CC = Instance.new(`ColorCorrectionEffect`)
	CC.Name = `NHRollCall`
	CC.Saturation = -0.85
	CC.Parent = Lighting
	local Back = TweenService:Create(CC, TweenInfo.new(0.8, Enum.EasingStyle.Sine), { Saturation = 0 })
	Back.Completed:Connect(function() CC:Destroy() end)
	task.delay(0.3, function() Back:Play() end)
end

function Local.OtherRespawn(Char: Model)
	local Root = Char:WaitForChild(`HumanoidRootPart`, 5) :: BasePart?
	if not Root then return end
	task.wait(0.1)
	if not Fx.Near(Root.Position, 80) then return end
	local Feet = Root.Position - Vector3.new(0, 2.8, 0)
	Fx.Burst(Feet + Vector3.new(0, 1, 0), {
		Texture = Fx.Tex.Smoke; Flipbook = `Grid4x4`; Count = 10; Color = VIOLET;
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.2), NumberSequenceKeypoint.new(1, 2.4) });
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(1, 1) });
		Speed = NumberRange.new(1, 2.5); Spread = 180; Lifetime = NumberRange.new(0.8, 1.2); LightEmission = 0.2; Drag = 2;
	})
	Fx.Ring(Feet + Vector3.new(0, 0.1, 0), C.Chalk, 6, nil, 0.5)
end

function Local.WatchRespawns(P: Player)
	local WasInSchool = false
	local function onCharacter(Char: Model)
		local InSchool = P:GetAttribute(`InMainMenu`) ~= true
		local Play = WasInSchool and InSchool
		WasInSchool = InSchool
		if not Play then return end
		if P == Player then
			Local.OwnRespawn()
		else
			task.spawn(Local.OtherRespawn, Char)
		end
	end
	if P.Character then WasInSchool = P:GetAttribute(`InMainMenu`) ~= true end
	P.CharacterAdded:Connect(onCharacter)
end

---| start |---

function Shared.OnStart()
	Fx.On(`QuestBeat`, Local.QuestBeat)
	Fx.On(`PathTier`, Local.PathTier) -- (2.31) Standing Paths
	Fx.On(`Clue`, Local.Clue)
	Fx.On(`LevelUp`, Local.LevelUp)
	Fx.On(`Purchase`, Local.Purchase)
	Fx.On(`Evolved`, Local.Evolved)
	task.spawn(Local.StartBell)
	for _, P in Players:GetPlayers() do Local.WatchRespawns(P) end
	Players.PlayerAdded:Connect(Local.WatchRespawns)
end

-- other client systems can queue a Moment banner (VFX P2-1 full moon, ...): Opts = { Title, Text?, Caption?, Color?, Icon?, Glyph?, Sound?, Hold? }
function Shared.Banner(Opts) Local.Enqueue(function() Local.Banner(Opts) end) end

-- testing hooks (Studio command bar / test scripts)
Shared.Test = {
	Banner = function(Opts) Local.Enqueue(function() Local.Banner(Opts) end) end;
	Bell = function() Local.Bell(ReplicatedStorage:WaitForChild(`SchoolClock`)) end;
	QuestBeat = Local.QuestBeat; Clue = Local.Clue; LevelUp = Local.LevelUp; Purchase = Local.Purchase;
	Respawn = Local.OwnRespawn;
}

return Shared
