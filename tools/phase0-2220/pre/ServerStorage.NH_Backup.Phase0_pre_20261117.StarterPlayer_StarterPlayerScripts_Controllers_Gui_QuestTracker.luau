--[[
	Quest tracker (client, NH UI kit). Draws what the server already decided:
		- the tracked quest's current objective (+ count, timer) under the clock
		- a marker over the objective's target (NPC, object, area, or your dropped item)
		- quest-object prompts only for objects you have a use for, with a soft outline
		- the detection meter while you're inside a stealth zone
	Reads PlayerData.Quests through StateController; never decides progress.
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

---| Modules |---

local Theme = require(ReplicatedStorage.UI.Theme)
local Components = require(ReplicatedStorage.UI.Components)
local QuestConfig = require(ReplicatedStorage.Config.Quests)
local Cases = require(ReplicatedStorage.Config.Cases)
local StateController = require(script.Parent.Parent.StateController)

local Player = Players.LocalPlayer
local C = Theme.Colors

local Local = {}
local Shared = {}

local Ui = nil
local Highlights = {} :: { [BasePart]: Highlight }

---| Lookups (by attribute, same contract as the server's Places) |---

local Cache = {} :: { [string]: Instance }
local Missed = {} :: { [string]: number } -- VFX P1-15: a part that isn't there (streamed out) is re-scanned at most every 2 s
function Local.FindPart(Attribute: string, Value: any): BasePart?
	local Key = `{Attribute}={Value}`
	local Hit = Cache[Key]
	if Hit and Hit.Parent then return Hit :: BasePart end
	if Missed[Key] and os.clock() - Missed[Key] < 2 then return nil end
	for _, Part in workspace:GetDescendants() do
		if Part:IsA(`BasePart`) and Part:GetAttribute(Attribute) == Value then
			Cache[Key] = Part
			Missed[Key] = nil
			return Part
		end
	end
	Missed[Key] = os.clock()
	return nil
end

function Local.FindNpc(NpcId: string): BasePart?
	local Live = workspace:FindFirstChild(`Live`)
	for _, Model in Live and Live:GetChildren() or {} do
		if Model:GetAttribute(`NpcId`) == NpcId then return Model:FindFirstChild(`HumanoidRootPart`) :: BasePart? end
	end
	return nil
end

function Local.Quests()
	local Profile = StateController.GetProfile(false)
	return Profile and Profile.Quests
end

-- Live objectives (current + unfinished optional) of an active quest.
function Local.Live(Def, State): { any }
	local List = {}
	local Current = Def.Objectives[State.Stage]
	if Current then table.insert(List, Current) end
	for Index, Obj in Def.Objectives do
		if Obj.Optional and Index ~= State.Stage and ((State.Counts or {})[Obj.Id] or 0) < (Obj.Count or 1) then
			table.insert(List, Obj)
		end
	end
	return List
end

-- Quest objects the player currently has a use for.
function Local.Relevant(Q): { [string]: boolean }
	local Set = {}
	if not Q or typeof(Q.Active) ~= `table` then return Set end
	for Id, State in Q.Active do
		local Def = QuestConfig.Quests[Id]
		if not Def then continue end
		for _, Obj in Local.Live(Def, State) do
			if Obj.Type == `Interact` then
				Set[Obj.Object] = true
			elseif Obj.Type == `Collect` then
				local Searched = State.Data and State.Data.Searched or {}
				for _, Object in Obj.Objects do
					if not table.find(Searched, Object) then Set[Object] = true end
				end
			elseif Obj.Type == `Clues` then
				local Found = Q.Cases and Q.Cases[Obj.Case] and Q.Cases[Obj.Case].Clues or {}
				for ObjectId, ObjDef in QuestConfig.Objects do
					if ObjDef.Clue and ObjDef.Clue.Case == Obj.Case and not Found[ObjDef.Clue.Id] then Set[ObjectId] = true end
				end
			end
		end
	end
	return Set
end

---| Build |---

function Local.Build()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `QuestTracker`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 5 -- above the clock panel (4)
	Gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	Components.AutoScale(Gui, { phoneScale = 0.5 })

	-- Tracker card (under the clock, top right)
	local Card, CardApi = Components.Panel({
		ornament = `ornate`; ornamentScale = 0.6; -- matches the clock chip above it
		Name = `Tracker`;
		AnchorPoint = Vector2.new(1, 0);
		Position = UDim2.new(1, -30, 0, 200); -- lines up with ClockHud; keeps the drop shadow on screen (phones: Local.PhonePlace)
		Size = UDim2.fromOffset(380, 140); -- fits 3 objective lines at TextBody plus the footer
		Visible = false;
		Parent = Gui;
	})
	local Content = CardApi.Content
	-- phones: the left column under the compass (the right side holds the touch buttons)
	local function PhonePlace()
		if Components.Phone and Components.Phone() then
			Card.AnchorPoint = Vector2.new(0, 0)
			Card.Position = UDim2.new(0, 24, 0, 120)
		else
			Card.AnchorPoint = Vector2.new(1, 0)
			Card.Position = UDim2.new(1, -30, 0, 200)
		end
	end
	PhonePlace()
	if Components.PreviewChanged then Components.PreviewChanged:Connect(PhonePlace) end
	if workspace.CurrentCamera then workspace.CurrentCamera:GetPropertyChangedSignal(`ViewportSize`):Connect(PhonePlace) end
	local Name = Components.Text({
		Name = `QuestName`; Text = ``; Font = Theme.Fonts.Title; TextSize = Theme.Sizes.TextHeader;
		TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Left;
		Size = UDim2.new(1, 0, 0, 26); Position = UDim2.fromOffset(0, 0); Parent = Content;
	})
	Components.Emboss(Name, Color3.fromRGB(150, 118, 70), 1.4)
	local Objective = Components.Text({
		Name = `Objective`; Text = ``; Font = Theme.Fonts.Body; TextSize = Theme.Sizes.TextBody;
		TextColor3 = C.Text; TextWrapped = true; TextXAlignment = Enum.TextXAlignment.Left;
		TextYAlignment = Enum.TextYAlignment.Top; RichText = true;
		Size = UDim2.new(1, 0, 0, 64); Position = UDim2.fromOffset(0, 28); Parent = Content;
	})
	local Footer = Components.Text({
		Name = `Footer`; Text = `[J] Journal`; Font = Theme.Fonts.Body; TextSize = Theme.Sizes.TextSmall;
		TextColor3 = C.TextDim; TextXAlignment = Enum.TextXAlignment.Right;
		Size = UDim2.new(1, 0, 0, 20); Position = UDim2.new(0, 0, 1, -20); Parent = Content;
	})
	local Timer = Components.Text({
		Name = `Timer`; Text = ``; Font = Theme.Fonts.BodyBold; TextSize = Theme.Sizes.TextSmall;
		TextColor3 = C.Danger; TextXAlignment = Enum.TextXAlignment.Left;
		Size = UDim2.new(0.5, 0, 0, 20); Position = UDim2.new(0, 0, 1, -20); Parent = Content;
	})

	-- Detection meter (top centre, only inside stealth zones)
	local Eye, EyeApi = Components.Panel({
		ornament = `ornate`; ornamentScale = 0.6;
		Name = `Detection`;
		AnchorPoint = Vector2.new(0.5, 0);
		Position = UDim2.new(0.5, 0, 0, 150);
		Size = UDim2.fromOffset(360, 74);
		Visible = false;
		Parent = Gui;
	})
	local EyeLabel = Components.Text({
		Name = `Label`; Text = ``; Font = Theme.Fonts.Title; TextSize = Theme.Sizes.TextBody;
		TextColor3 = C.Text; Size = UDim2.new(1, 0, 0, 22); Parent = EyeApi.Content;
	})
	-- Iron-framed meter (kit look). Names Track / Track.Fill are what the update code uses.
	local Track = Instance.new(`Frame`)
	Track.Name = `Track`
	Track.BackgroundColor3 = C.Ink
	Track.BorderSizePixel = 0
	Track.Position = UDim2.fromOffset(0, 28)
	Track.Size = UDim2.new(1, 0, 0, 14)
	Track.Parent = EyeApi.Content
	Components.Slice(`FrameThin`, C.IronDim, { SliceScale = 0.22, ZIndex = 6, Parent = Track })
	local Fill = Instance.new(`Frame`)
	Fill.Name = `Fill`
	Fill.BorderSizePixel = 0
	Fill.Size = UDim2.fromScale(0, 1)
	Fill.BackgroundColor3 = C.Gold
	Fill.ZIndex = 2
	Fill.Parent = Track
	local FillGrad = Instance.new(`UIGradient`)
	FillGrad.Rotation = 90
	FillGrad.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(120, 110, 100))
	FillGrad.Parent = Fill

	-- Objective marker
	local Marker = Instance.new(`BillboardGui`)
	Marker.Name = `QuestMarker`
	Marker.AlwaysOnTop = true
	Marker.Size = UDim2.fromOffset(200, 48)
	Marker.StudsOffsetWorldSpace = Vector3.new(0, 4, 0)
	Marker.Enabled = false
	Marker.Parent = Gui
	-- Engraved plate marker (kit look); the update code writes Marker.Label.Text.
	local MarkerLabel = Components.Text({
		Name = `Label`; Text = ``; Font = Theme.Fonts.Title; TextSize = 18; TextXAlignment = Enum.TextXAlignment.Center;
		TextColor3 = C.Gold; TextStrokeTransparency = 0.3; Size = UDim2.fromScale(1, 1);
		BackgroundTransparency = 0.15; BackgroundColor3 = C.Ink; Parent = Marker;
	})
	Components.Slice(`FrameThin`, C.Gold:Lerp(C.Iron, 0.5), { SliceScale = 0.35, Parent = MarkerLabel })

	return {
		Gui = Gui; Card = Card; Name = Name; Objective = Objective; Timer = Timer; Footer = Footer;
		Eye = Eye; EyeLabel = EyeLabel; Fill = Fill; Marker = Marker; MarkerLabel = MarkerLabel;
	}
end

---| Update |---

function Local.Target(Q, Id: string, State, Obj): (BasePart?, string?)
	-- A dropped item comes first: you need it back.
	if Obj.Item and State.Items and State.Items[Obj.Item] == `Dropped` then
		local Drops = workspace:FindFirstChild(`QuestDrops`)
		for _, Part in Drops and Drops:GetChildren() or {} do
			if Part:GetAttribute(`DropOwner`) == Player.UserId and Part:GetAttribute(`DropItem`) == Obj.Item then
				return Part, `Pick it up`
			end
		end
	end

	local W = Obj.Waypoint
	if W then
		if W.Kind == `Npc` then return Local.FindNpc(W.Id), nil end
		if W.Kind == `Area` then return Local.FindPart(`QuestArea`, W.Id), nil end
		if W.Kind == `Object` then return Local.FindPart(`QuestObject`, W.Id), nil end
	end
	if Obj.Npc then return Local.FindNpc(Obj.Npc), nil end
	if Obj.Npcs then return Local.FindNpc(Obj.Npcs[1]), nil end
	if Obj.Area then return Local.FindPart(`QuestArea`, Obj.Area), nil end
	if Obj.Object then return Local.FindPart(`QuestObject`, Obj.Object), nil end

	-- Searches and clues: the nearest thing still worth checking.
	local Relevant = Local.Relevant(Q)
	local Candidates = {}
	if Obj.Type == `Collect` then
		for _, Object in Obj.Objects do if Relevant[Object] then table.insert(Candidates, Object) end end
	elseif Obj.Type == `Clues` then
		for Object in Relevant do
			local ObjDef = QuestConfig.Objects[Object]
			if ObjDef and ObjDef.Clue and ObjDef.Clue.Case == Obj.Case then table.insert(Candidates, Object) end
		end
	end
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Best, BestDistance = nil, math.huge
	for _, Object in Candidates do
		local Part = Local.FindPart(`QuestObject`, Object)
		if Part then
			local D = if Root then (Part.Position - Root.Position).Magnitude else 0
			if D < BestDistance then Best, BestDistance = Part, D end
		end
	end
	return Best, nil
end

function Local.ObjectiveLine(Q, Id: string, State, Obj): string
	local Need = Obj.Count or 1
	local Have = (State.Counts or {})[Obj.Id] or 0
	local Text = Obj.Text
	if Need > 1 then Text ..= `  ({Have}/{Need})` end
	if Obj.Item and State.Items and State.Items[Obj.Item] == `Dropped` then
		local Item = QuestConfig.Items[Obj.Item]
		Text = `<font color="#{C.Danger:ToHex()}">You dropped the {Item and Item.Name or Obj.Item}! Pick it back up.</font>`
	end
	return Text
end

function Local.UpdateTracker()
	local Q = Local.Quests()
	local Id = Q and Q.Tracked
	local State = Id and Id ~= `` and Q.Active and Q.Active[Id]
	local Def = State and QuestConfig.Quests[Id]
	local Obj = Def and Def.Objectives[State.Stage]
	if not Obj then
		Ui.Card.Visible = false
		Ui.Marker.Enabled = false
		return
	end

	Ui.Card.Visible = true
	Ui.Name.Text = Def.Name
	Ui.Name.TextColor3 = if Def.Category == `Main` then C.Gold else C.Text
	Ui.Objective.Text = Local.ObjectiveLine(Q, Id, State, Obj)

	if State.Deadline then
		local Left = math.max(0, State.Deadline - workspace:GetServerTimeNow())
		Ui.Timer.Text = string.format(`Time left %d:%02d`, Left // 60, Left % 60)
	else
		Ui.Timer.Text = ``
	end

	local Target, Override = Local.Target(Q, Id, State, Obj)
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if Target and Root then
		Ui.Marker.Adornee = Target
		Ui.Marker.Enabled = true
		local Distance = math.floor((Target.Position - Root.Position).Magnitude)
		Ui.MarkerLabel.Text = `◆ {Override or Def.Name}\n{Distance} studs`
	else
		Ui.Marker.Enabled = false
	end
end

function Local.UpdatePrompts()
	local Relevant = Local.Relevant(Local.Quests())
	-- (audit) drop highlights whose part streamed out or was removed (they leaked)
	for Part, H in Highlights do
		if not Part.Parent then H:Destroy() Highlights[Part] = nil end
	end
	for _, Prompt in workspace:GetDescendants() do
		if not Prompt:IsA(`ProximityPrompt`) then continue end
		local Object = Prompt:GetAttribute(`QuestObject`)
		local Owner = Prompt:GetAttribute(`DropOwner`)
		if Object then
			local Show = Relevant[Object] == true
			Prompt.Enabled = Show
			local Part = Prompt.Parent
			if Part and Part:IsA(`BasePart`) then
				local H = Highlights[Part]
				if Show and not H then
					H = Instance.new(`Highlight`)
					H.Name = `QuestHighlight`
					H.FillTransparency = 0.85
					H.FillColor = C.Gold
					H.OutlineColor = C.Gold
					H.OutlineTransparency = 0.2
					H.DepthMode = Enum.HighlightDepthMode.Occluded
					H.Adornee = Part
					H.Parent = Ui.Gui
					Highlights[Part] = H
				elseif not Show and H then
					H:Destroy()
					Highlights[Part] = nil
				end
			end
		elseif Owner then
			Prompt.Enabled = Owner == Player.UserId
		end
	end
end

function Local.UpdateEye()
	local Zone = Player:GetAttribute(`StealthZone`)
	if not Zone then
		Ui.Eye.Visible = false
		return
	end
	local Value = Player:GetAttribute(`Detection`) or 0
	local Seen = Player:GetAttribute(`DetectionSeen`) == true
	local Hidden = Player.Character and Player.Character:GetAttribute(`Hidden`) == true
	Ui.Eye.Visible = true
	Ui.Fill.Size = UDim2.fromScale(math.clamp(Value, 0, 1), 1)
	Ui.Fill.BackgroundColor3 = if Value >= 0.75 then C.Danger elseif Value >= 0.45 then C.Crimson else C.Gold
	Ui.EyeLabel.Text = if Hidden then `{Zone}  ·  HIDDEN`
		elseif Seen then `{Zone}  ·  SOMEONE SEES YOU`
		else `{Zone}  ·  unseen`
	Ui.EyeLabel.TextColor3 = if Seen then C.Danger elseif Hidden then C.Gold else C.Text
end

---| API |---

function Shared.OnStart()
	Ui = Local.Build()

	local Elapsed = 0
	RunService.Heartbeat:Connect(function(DeltaTime)
		Elapsed += DeltaTime
		Local.UpdateEye()
		if Elapsed < 0.25 then return end
		Elapsed = 0
		local Ok, Err = pcall(Local.UpdateTracker)
		if not Ok then warn(`[QuestTracker] {Err}`) end
	end)

	local function Refresh()
		local Ok, Err = pcall(Local.UpdatePrompts)
		if not Ok then warn(`[QuestTracker] {Err}`) end
	end
	StateController.ProfileUpdated:Connect(function(_, Action)
		if Action and Action.type == `SetQuests` then Refresh() end
	end)
	workspace.DescendantAdded:Connect(function(Child)
		if Child:IsA(`ProximityPrompt`) and (Child:GetAttribute(`QuestObject`) or Child:GetAttribute(`DropOwner`)) then
			task.defer(Refresh)
		end
	end)
	task.spawn(function()
		StateController.GetProfile(true)
		Refresh()
	end)
end

return Shared
