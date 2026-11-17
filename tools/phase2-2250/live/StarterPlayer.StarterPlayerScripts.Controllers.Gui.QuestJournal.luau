--[[
	Quest journal (client, NH UI kit). Toggle with J or the "Journal" button (left edge, for touch).
	Tabs:
		Quests      active quests (objectives, timer, Track, Abandon for side quests), done, failed
		Case Files  clues you've found, the evidence board (pick two clues -> Connect), insights,
		            and the case's deduction question
	Every action goes to the server as Packets.QuestAction; the server decides the outcome.
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local UserInputService = game:GetService(`UserInputService`)
local Typing = require(game:GetService(`ReplicatedStorage`):WaitForChild(`Packages`):WaitForChild(`Bind`):WaitForChild(`Typing`)) -- (2.1.0) one "is the player typing?" for every key

---| Modules |---

local Theme = require(ReplicatedStorage.UI.Theme)
local Components = require(ReplicatedStorage.UI.Components)
local Packets = require(ReplicatedStorage.Remotes.Packets)
local QuestConfig = require(ReplicatedStorage.Config.Quests)
local Cases = require(ReplicatedStorage.Config.Cases)
local Npcs = require(ReplicatedStorage.Config.Npcs)
local StateController = require(script.Parent.Parent.StateController)
local Fx = require(script.Parent.Parent:WaitForChild(`Fx`))
local TweenService = game:GetService(`TweenService`)

local Player = Players.LocalPlayer
local C = Theme.Colors
local S = Theme.Sizes
local TOGGLE_KEY = Enum.KeyCode.J

local Local = {}
local Shared = {}

local Ui = nil
local Tab = 1
local Selected = {} :: { string } -- evidence board picks (max 2)
-- VFX P2-13: the newest link draws its string and types its insight; a wrong pair shakes; a solve stamps
local Fresh = nil :: string?   -- "Case|A|B" of a link the server just confirmed
local Typed = nil :: string?   -- "Case|A|B" whose insight text types out on the next render
local CRIMSON = Color3.fromRGB(200, 40, 60)
local THREAD = Color3.fromRGB(170, 28, 44)
local function pairKey(Case: string, A: string, B: string): string
	if A > B then A, B = B, A end
	return `{Case}|{A}|{B}`
end

---| Helpers |---

function Local.Text(Parent: Instance, Order: number, Text: string, Props: { [string]: any }?)
	local P = Props or {}
	return Components.Text({
		Text = Text; RichText = true; TextWrapped = true;
		Font = P.Font or Theme.Fonts.Body; TextSize = P.TextSize or S.TextBody;
		TextColor3 = P.Color or C.Text; TextXAlignment = P.Align or Enum.TextXAlignment.Left;
		Size = UDim2.new(1, 0, 0, 0); AutomaticSize = Enum.AutomaticSize.Y;
		LayoutOrder = Order; Parent = Parent;
	})
end

-- Kit card: the outer frame carries the art (bracket-corner border + slate, via Decorate); the
-- returned inner frame (a TextButton when clickable) holds the padded, listed content.
local BlockDecor = setmetatable({}, { __mode = `k` }) :: { [GuiObject]: any }
function Local.Block(Parent: Instance, Order: number, Clickable: boolean?): GuiObject
	local Outer = Instance.new(`Frame`)
	Outer.Name = `Card`
	Outer.BackgroundTransparency = 1
	Outer.Size = UDim2.new(1, -8, 0, 0)
	Outer.AutomaticSize = Enum.AutomaticSize.Y
	Outer.LayoutOrder = Order
	Outer.Parent = Parent
	local _, Decor = Components.Decorate(Outer, {
		ornament = `slot`; shadow = false; bgColor = if Clickable then Color3.fromRGB(78, 70, 88) else Color3.fromRGB(66, 58, 76);
		frameColor = C.RowFrame;
	})
	local F = Instance.new(if Clickable then `TextButton` else `Frame`) :: any
	if Clickable then
		F.Text = ``
		F.AutoButtonColor = false
		F.MouseEnter:Connect(function() if not F:GetAttribute(`Selected`) then Decor:SetFrameColor(C.Gold:Lerp(C.RowFrame, 0.5)) end end)
		F.MouseLeave:Connect(function() if not F:GetAttribute(`Selected`) then Decor:SetFrameColor(C.RowFrame) end end)
	end
	F.BackgroundTransparency = 1
	F.BorderSizePixel = 0
	F.Size = UDim2.new(1, 0, 0, 0)
	F.AutomaticSize = Enum.AutomaticSize.Y
	F.ZIndex = 2
	F.Parent = Outer
	local Pad = Instance.new(`UIPadding`)
	for _, Side in { `PaddingTop`, `PaddingBottom`, `PaddingLeft`, `PaddingRight` } do Pad[Side] = UDim.new(0, 14) end
	Pad.Parent = F
	local Layout = Instance.new(`UIListLayout`)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.Padding = UDim.new(0, 6)
	Layout.Parent = F
	BlockDecor[F] = Decor
	return F
end

-- Evidence-board pick: gold frame + warm fill instead of a flat colour.
function Local.SetSelected(Block: GuiObject, On: boolean)
	local Decor = BlockDecor[Block]
	Block:SetAttribute(`Selected`, On)
	if Decor then
		Decor:SetFrameColor(if On then C.Gold else C.RowFrame)
		Decor.Background.ImageColor3 = if On then Color3.fromRGB(120, 92, 48) else Color3.fromRGB(78, 70, 88)
	end
end

function Local.Row(Parent: Instance, Order: number): Frame
	local R = Instance.new(`Frame`)
	R.BackgroundTransparency = 1
	R.Size = UDim2.new(1, 0, 0, 44)
	R.LayoutOrder = Order
	R.Parent = Parent
	local Layout = Instance.new(`UIListLayout`)
	Layout.FillDirection = Enum.FillDirection.Horizontal
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.Padding = UDim.new(0, 8)
	Layout.Parent = R
	return R
end

function Local.Button(Parent: Instance, Order: number, Text: string, Style: string?, Width: number?, OnClick: () -> ())
	return Components.Button({
		text = Text; style = Style or `default`; onClick = function() OnClick() end;
		Size = UDim2.fromOffset(Width or 160, 44); LayoutOrder = Order; Parent = Parent;
	})
end

function Local.Send(Message)
	Packets.QuestAction:Fire(Message)
end

---| Build |---

function Local.Build()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `QuestJournal`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 7
	Gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	Components.AutoScale(Gui)

	local Toggle = Components.Button({
		text = if UserInputService.KeyboardEnabled then `Journal [J]` else `Journal`;
		style = `ghost`; onClick = function() Shared.Toggle() end;
		Name = `Toggle`; AnchorPoint = Vector2.new(0, 0.5); Position = UDim2.new(0, 8, 0.5, 78); -- below the Factions button
		Size = UDim2.fromOffset(150, 44); Parent = Gui;
	})
	-- phones: beside the Factions button instead of under it (the left column is short; see FactionsPanel)
	local function PhonePlace()
		if Components.Phone and Components.Phone() then
			Toggle.Position = UDim2.new(0, 148, 0.5, -55)
		else
			Toggle.Position = UDim2.new(0, 8, 0.5, 78)
		end
	end
	PhonePlace()
	if Components.PreviewChanged then Components.PreviewChanged:Connect(PhonePlace) end
	if workspace.CurrentCamera then workspace.CurrentCamera:GetPropertyChangedSignal(`ViewportSize`):Connect(PhonePlace) end

	local Panel, PanelApi = Components.Panel({
		title = `Journal`;
		Name = `Panel`;
		AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromOffset(1000, 720);
		maxSize = Vector2.new(1000, 720);
		Visible = false;
		Parent = Gui;
	})
	local Content = PanelApi.Content

	local Tabs, TabsApi = Components.TabBar({
		tabs = { `Quests`, `Case Files` };
		selected = 1;
		onChanged = function(i) Tab = i Local.Render() end;
		Name = `Tabs`; Size = UDim2.new(1, -60, 0, 48); Position = UDim2.fromOffset(0, 0); Parent = Content;
	})
	local Close = Components.Button({
		text = `X`; style = `ghost`; onClick = function() Shared.Toggle(false) end;
		Name = `Close`; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 2);
		Size = UDim2.fromOffset(48, 44); Parent = Content;
	})

	local Body = Instance.new(`ScrollingFrame`)
	Body.Name = `Body`
	Body.BackgroundTransparency = 1
	Body.BorderSizePixel = 0
	Body.Position = UDim2.fromOffset(0, 58)
	Body.Size = UDim2.new(1, 0, 1, -58)
	Body.CanvasSize = UDim2.new()
	Body.AutomaticCanvasSize = Enum.AutomaticSize.Y
	Body.ScrollBarThickness = 6
	Body.ScrollBarImageColor3 = C.Gold
	Body.Parent = Content
	local Layout = Instance.new(`UIListLayout`)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.Padding = UDim.new(0, 10)
	Layout.Parent = Body

	return { Gui = Gui; Toggle = Toggle; Panel = Panel; Body = Body; Tabs = Tabs; TabsApi = TabsApi; Close = Close }
end

---| Evidence strings (VFX P2-13) |---

-- crimson threads down the board's left edge, pinned to the two clue cards each insight joined
function Local.Strings(Board: GuiObject, CaseId: string, Insights)
	if not Board.Parent then return end
	local Outer = Board.Parent :: GuiObject
	local Old = Outer:FindFirstChild(`NHStrings`)
	if Old then Old:Destroy() end
	local Layer = Instance.new(`Frame`)
	Layer.Name = `NHStrings`
	Layer.BackgroundTransparency = 1
	Layer.Size = UDim2.fromScale(1, 1)
	Layer.ZIndex = 6
	Layer.Parent = Outer
	for _ = 1, 3 do game:GetService(`RunService`).RenderStepped:Wait() end
	if not Layer.Parent then return end
	local H = Layer.AbsoluteSize.Y
	if H <= 0 then return end
	local Lane = 0
	for _, Ins in Insights do
		local RA = Board:FindFirstChild(`Clue_{tostring(Ins.A)}`, true) :: GuiObject?
		local RB = Board:FindFirstChild(`Clue_{tostring(Ins.B)}`, true) :: GuiObject?
		if RA and RB then
			Lane += 1
			local X = 3 + Lane * 5
			local function frac(R: GuiObject): number
				local Card = R.Parent :: GuiObject -- the clue row's card frame
				local Y = Card.AbsolutePosition.Y + Card.AbsoluteSize.Y / 2
				return (Y - Layer.AbsolutePosition.Y) / H
			end
			local FA, FB = frac(RA), frac(RB)
			local Top, Bot = math.min(FA, FB), math.max(FA, FB)
			local Thread = Instance.new(`Frame`)
			Thread.Name = `Thread`
			Thread.BorderSizePixel = 0
			Thread.BackgroundColor3 = THREAD
			Thread.AnchorPoint = Vector2.new(0.5, 0)
			Thread.Position = UDim2.new(0, X, Top, 0)
			Thread.Size = UDim2.new(0, 2, Bot - Top, 0)
			Thread.ZIndex = 6
			Thread.Parent = Layer
			for _, F in { FA, FB } do
				local Pin = Instance.new(`Frame`)
				Pin.Name = `Pin`
				Pin.BorderSizePixel = 0
				Pin.BackgroundColor3 = CRIMSON
				Pin.AnchorPoint = Vector2.new(0.5, 0.5)
				Pin.Position = UDim2.new(0, X, F, 0)
				Pin.Size = UDim2.fromOffset(9, 9)
				Pin.ZIndex = 7
				local Round = Instance.new(`UICorner`)
				Round.CornerRadius = UDim.new(1, 0)
				Round.Parent = Pin
				local Rim = Instance.new(`UIStroke`)
				Rim.Color = Color3.fromRGB(60, 10, 18)
				Rim.Thickness = 1
				Rim.Parent = Pin
				Pin.Parent = Layer
			end
			if Fresh == pairKey(CaseId, Ins.A, Ins.B) then
				Fresh = nil
				-- the string draws from the first card to the second
				local From = if FA <= FB then Top else Bot
				Thread.Position = UDim2.new(0, X, From, 0)
				Thread.Size = UDim2.new(0, 2, 0, 0)
				TweenService:Create(Thread, TweenInfo.new(if Fx.Reduced() then 0.15 else 0.45, Enum.EasingStyle.Quad), {
					Position = UDim2.new(0, X, Top, 0); Size = UDim2.new(0, 2, Bot - Top, 0);
				}):Play()
				pcall(Components.PlaySound, `Tick`, 0.7, 0.8)
			end
		end
	end
end

-- a wrong pair: the two cards shake and flash red
function Local.Miss(D)
	if not Ui or not Ui.Panel.Visible or typeof(D) ~= `table` then return end
	local Board = Ui.Body:FindFirstChild(`Board_{tostring(D.Case)}`, true)
	if not Board then return end
	for _, Id in { D.A, D.B } do
		local Row = Board:FindFirstChild(`Clue_{tostring(Id)}`, true) :: GuiObject?
		if Row then
			local Decor = BlockDecor[Row]
			if Decor then
				Decor:SetFrameColor(C.Danger)
				task.delay(0.5, function() if Row.Parent then Decor:SetFrameColor(if Row:GetAttribute(`Selected`) then C.Gold else C.RowFrame) end end)
			end
			if not Fx.Reduced() then
				task.spawn(function()
					for I = 1, 6 do
						Row.Position = UDim2.fromOffset(if I % 2 == 0 then -6 else 6, 0)
						task.wait(0.04)
					end
					Row.Position = UDim2.fromOffset(0, 0)
				end)
			end
		end
	end
	pcall(Components.PlaySound, `Reject`, 0.8)
end

-- the case is cracked: the journal darkens and a SOLVED stamp lands
function Local.Solved(D)
	if not Ui then return end
	if not Ui.Panel.Visible then Shared.Toggle(true) Shared.SelectTab(2) end
	local Panel = Ui.Panel
	local Old = Panel:FindFirstChild(`NHSolved`)
	if Old then Old:Destroy() end
	local Veil = Instance.new(`Frame`)
	Veil.Name = `NHSolved`
	Veil.BackgroundColor3 = C.Ink
	Veil.BackgroundTransparency = 1
	Veil.BorderSizePixel = 0
	Veil.Size = UDim2.fromScale(1, 1)
	Veil.ZIndex = 40
	Veil.Parent = Panel
	local Stamp = Components.Text({
		Name = `Stamp`; Text = `SOLVED`; Font = Theme.Fonts.Title; TextSize = 96; TextColor3 = CRIMSON;
		TextXAlignment = Enum.TextXAlignment.Center; TextTransparency = 1;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.45); Size = UDim2.new(1, 0, 0, 110);
		Rotation = -8; ZIndex = 42; Parent = Veil;
	})
	local Stroke = Instance.new(`UIStroke`)
	Stroke.Color = Color3.fromRGB(70, 10, 20)
	Stroke.Thickness = 3
	Stroke.Transparency = 1
	Stroke.Parent = Stamp
	local Sub = Components.Text({
		Name = `Case`; Text = tostring(D and D.Name or ``); TextSize = 26; TextColor3 = C.Gold;
		TextXAlignment = Enum.TextXAlignment.Center; TextTransparency = 1;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromScale(0.5, 0.56); Size = UDim2.new(1, 0, 0, 34); ZIndex = 42; Parent = Veil;
	})
	local Scale = Instance.new(`UIScale`)
	Scale.Scale = if Fx.Reduced() then 1 else 1.8
	Scale.Parent = Stamp
	local function tw(I, T, P, St) TweenService:Create(I, TweenInfo.new(T, St or Enum.EasingStyle.Sine), P):Play() end
	tw(Veil, 0.25, { BackgroundTransparency = 0.45 })
	tw(Stamp, 0.16, { TextTransparency = 0 })
	tw(Stroke, 0.16, { Transparency = 0 })
	tw(Scale, if Fx.Reduced() then 0.01 else 0.18, { Scale = 1 }, Enum.EasingStyle.Back)
	task.delay(0.18, function()
		pcall(Components.PlaySound, `Stamp`, 1.2, 0.9)
		if not Fx.Reduced() then Fx.Shake(0.25, 0.2) end
		tw(Sub, 0.3, { TextTransparency = 0 })
	end)
	task.delay(2.4, function()
		tw(Veil, 0.6, { BackgroundTransparency = 1 })
		tw(Stamp, 0.6, { TextTransparency = 1 })
		tw(Stroke, 0.6, { Transparency = 1 })
		tw(Sub, 0.6, { TextTransparency = 1 })
		task.delay(0.65, function() Veil:Destroy() end)
	end)
end

---| Quests tab |---

function Local.QuestCard(Parent: Instance, Order: number, Id: string, State, Q)
	local Def = QuestConfig.Quests[Id]
	local Card = Local.Block(Parent, Order)
	Card.Name = `Quest_{Id}`
	local Tag = if Def.Category == `Main` then `MAIN  ·  CHAPTER {Def.Chapter or 1}`
		elseif Def.Dare then `DARE  ·  GONE AT 6 AM` -- (1.33) a clique leader's daily dare
		elseif Def.Category == `Clique` then `CLIQUE`
		else `SIDE QUEST`
	local Tracked = Q.Tracked == Id
	Local.Text(Card, 1, `<font color="#{C.TextDim:ToHex()}">{Tag}</font>{if Tracked then `   <font color="#{C.Gold:ToHex()}">◆ tracked</font>` else ``}`, { TextSize = S.TextSmall })
	Local.Text(Card, 2, Def.Name, { Font = Theme.Fonts.Title; TextSize = S.TextHeader; Color = if Def.Category == `Main` then C.Gold else C.Text })
	Local.Text(Card, 3, `<i>{Def.Summary}</i>`, { TextSize = S.TextSmall; Color = C.TextDim })

	for Index, Obj in Def.Objectives do
		local Count = (State.Counts or {})[Obj.Id] or 0
		local Need = Obj.Count or 1
		local Done = Count >= Need
		local Current = Index == State.Stage
		local Mark = if Done then `<font color="#{C.On:ToHex()}">✓</font>` elseif Current then `<font color="#{C.Gold:ToHex()}">◆</font>` else `<font color="#{C.TextFaint:ToHex()}">○</font>`
		local Text = Obj.Text .. (if Need > 1 then `  ({Count}/{Need})` else ``)
		if not Done and not Current and not Obj.Optional then Text = `<font color="#{C.TextFaint:ToHex()}">{Text}</font>` end
		Local.Text(Card, 10 + Index, `{Mark}  {Text}`, { TextSize = S.TextBody })
	end

	if State.Deadline then
		local Left = math.max(0, State.Deadline - workspace:GetServerTimeNow())
		Local.Text(Card, 40, string.format(`Time left: %d:%02d`, Left // 60, Left % 60), { Color = C.Danger; TextSize = S.TextSmall })
	end

	local Buttons = Local.Row(Card, 50)
	if not Tracked then
		Local.Button(Buttons, 1, `Track`, `gold`, 140, function() Local.Send({ Action = `Track`; Quest = Id }) end)
	end
	-- (audit) owner: no Abandon for rite or showdown quests (the server refuses them too)
	if Def.Category ~= `Main` and Def.Category ~= `Rite` and not Def.Showdown then
		Local.Button(Buttons, 2, `Abandon`, `crimson`, 140, function() Local.Send({ Action = `Abandon`; Quest = Id }) end)
	end
	if #Buttons:GetChildren() <= 1 then Buttons:Destroy() end
end

function Local.RenderQuests(Q)
	local Body = Ui.Body
	local Order = 0
	local function Next() Order += 1 return Order end

	Components.SectionHeader({ text = `Active`; LayoutOrder = Next(); Size = UDim2.new(1, -8, 0, 34); Parent = Body })
	local Ids = {}
	for Id in Q.Active or {} do if QuestConfig.Quests[Id] then table.insert(Ids, Id) end end -- (audit) a removed quest id in a save crashed the sort
	table.sort(Ids, function(A, B)
		local DA, DB = QuestConfig.Quests[A], QuestConfig.Quests[B]
		if (DA.Category == `Main`) ~= (DB.Category == `Main`) then return DA.Category == `Main` end
		return DA.Name < DB.Name
	end)
	if #Ids == 0 then
		Local.Text(Body, Next(), `No active quests. Talk to people around campus; some of them need a hand.`, { Color = C.TextDim })
	end
	for _, Id in Ids do
		if QuestConfig.Quests[Id] then Local.QuestCard(Body, Next(), Id, Q.Active[Id], Q) end
	end

	local Failed = {}
	for Id, Reason in Q.Failed or {} do
		local Def = QuestConfig.Quests[Id]
		if Def and not (Q.Active or {})[Id] then
			local Giver = Def.Giver and Npcs[Def.Giver]
			table.insert(Failed, `<b>{Def.Name}</b>: {Reason}{if Giver then ` Talk to {Giver.Name} to try again.` else ``}`)
		end
	end
	if #Failed > 0 then
		Components.SectionHeader({ text = `Failed`; color = C.Crimson; LayoutOrder = Next(); Size = UDim2.new(1, -8, 0, 34); Parent = Body })
		for _, Line in Failed do Local.Text(Body, Next(), Line, { Color = C.TextDim }) end
	end

	local Done = {}
	for Id in Q.Done or {} do
		local Def = QuestConfig.Quests[Id]
		if Def then table.insert(Done, Def) end
	end
	if #Done > 0 then
		table.sort(Done, function(A, B) return A.Name < B.Name end)
		Components.SectionHeader({ text = `Completed`; LayoutOrder = Next(); Size = UDim2.new(1, -8, 0, 34); Parent = Body })
		for _, Def in Done do
			Local.Text(Body, Next(), `<font color="#{C.On:ToHex()}">✓</font>  {Def.Name}{if Def.Repeatable then `  <font color="#{C.TextFaint:ToHex()}">(daily)</font>` else ``}`, { Color = C.TextDim })
			if Def.Ending then
				Local.Text(Body, Next(), `      <i>{Def.Ending}</i>`, { Color = C.Gold; TextSize = S.TextSmall })
			end
		end
	end

	-- (2.24.0) cutscenes you've seen, to watch again (Controllers.Cine.Replay: the server plays it, always skippable)
	local CineOk, CineConfig = pcall(function() return require(ReplicatedStorage.Config.Cine) end)
	local Seen = {}
	local Grades = if typeof(Q.CineGrades) == `table` then Q.CineGrades else {} -- (2.25.0) best grade per interactive cut
	for Id, Mark in (if typeof(Q.Cine) == `table` then Q.Cine else {}) do
		local Cut = CineOk and CineConfig.Cuts[Id]
		if Mark == `Seen` and Cut and Cut.Replay and not Cut.Hidden then table.insert(Seen, { Id = Id; Name = Cut.Name; ShowGrade = Cut.ShowGrade ~= false }) end
	end
	if #Seen > 0 then
		table.sort(Seen, function(A, B) return A.Name < B.Name end)
		Components.SectionHeader({ text = `Cutscenes`; LayoutOrder = Next(); Size = UDim2.new(1, -8, 0, 34); Parent = Body })
		for _, Cut in Seen do
			local R = Local.Row(Body, Next())
			Components.Text({
				Text = if Grades[Cut.Id] and Cut.ShowGrade then `{Cut.Name}   <font color="#{C.Gold:ToHex()}">{Grades[Cut.Id].Best}</font>` else Cut.Name;
				RichText = true; Font = Theme.Fonts.Body; TextSize = S.TextBody; TextColor3 = C.TextDim;
				TextXAlignment = Enum.TextXAlignment.Left; TextTruncate = Enum.TextTruncate.AtEnd;
				Size = UDim2.new(1, -176, 0, 44); LayoutOrder = 1; Parent = R;
			})
			Local.Button(R, 2, `Watch again`, `default`, 160, function()
				local Ok, Director = pcall(function() return require(script.Parent.Parent:WaitForChild(`Cine`)) end)
				if not Ok or Director.IsPlaying() then return end
				Shared.Toggle(false)
				Director.Replay(Cut.Id)
			end)
		end
	end
end

---| Case files tab |---

function Local.RenderCases(Q)
	local Body = Ui.Body
	local Order = 0
	local function Next() Order += 1 return Order end
	local Any = false

	for CaseId, Case in Cases do
		local Saved = Q.Cases and Q.Cases[CaseId]
		local Found = Saved and Saved.Clues or {}
		local FoundList = {}
		for ClueId in Case.Clues do if Found[ClueId] then table.insert(FoundList, ClueId) end end
		if #FoundList == 0 then continue end
		Any = true
		table.sort(FoundList)

		Components.SectionHeader({ text = Case.Name; LayoutOrder = Next(); Size = UDim2.new(1, -8, 0, 34); Parent = Body })
		Local.Text(Body, Next(), `<i>{Case.Subject}</i>`, { Color = C.TextDim; TextSize = S.TextSmall })

		-- Clues (click to select for the evidence board)
		local Board = Local.Block(Body, Next())
		Board.Name = `Board_{CaseId}`
		Local.Text(Board, 0, `<b>Evidence board</b>  ·  pick two clues, then Connect.`, { TextSize = S.TextSmall; Color = C.TextDim })
		for Index, ClueId in FoundList do
			local Clue = Case.Clues[ClueId]
			local IsSelected = table.find(Selected, ClueId) ~= nil
			local Row = Local.Block(Board, Index, true)
			Row.Name = `Clue_{ClueId}`
			Local.SetSelected(Row, IsSelected)
			Local.Text(Row, 1, `<b>{Clue.Name}</b>   <font color="#{C.TextFaint:ToHex()}">{Clue.Where}</font>`, { TextSize = S.TextBody; Color = if IsSelected then C.Gold else C.Text })
			Local.Text(Row, 2, Clue.Text, { TextSize = S.TextSmall; Color = if IsSelected then C.Text else C.TextDim })
			Row.Activated:Connect(function()
				local At = table.find(Selected, ClueId)
				if At then table.remove(Selected, At)
				else
					table.insert(Selected, ClueId)
					while #Selected > 2 do table.remove(Selected, 1) end
				end
				Local.Render()
			end)
		end
		local Buttons = Local.Row(Board, 100)
		Local.Button(Buttons, 1, `Connect`, `gold`, 180, function()
			if #Selected == 2 then
				Local.Send({ Action = `Link`; Case = CaseId; A = Selected[1]; B = Selected[2] })
				Selected = {}
			end
		end)
		task.spawn(Local.Strings, Board, CaseId, Saved and Saved.Insights or {})

		-- Insights
		local Insights = Saved and Saved.Insights or {}
		if #Insights > 0 then
			local Box = Local.Block(Body, Next())
			Box.Name = `Insights_{CaseId}`
			Local.Text(Box, 0, `<b>Insights</b>`, { Color = C.Gold })
			for Index, Insight in Insights do
				local Label = Local.Text(Box, Index, `• {Insight.Text}`, { TextSize = S.TextSmall })
				if Label and Typed and Insight.A and Insight.B and Typed == pairKey(CaseId, Insight.A, Insight.B) then
					Typed = nil
					local N = utf8.len(Insight.Text) or #Insight.Text
					Label.MaxVisibleGraphemes = 0
					TweenService:Create(Label, TweenInfo.new(math.clamp(N * 0.025, 0.4, 2.2), Enum.EasingStyle.Linear), { MaxVisibleGraphemes = N + 2 }):Play()
				end
			end
		end

		-- Deduction
		if Saved and Saved.Solved then
			Local.Text(Body, Next(), `<font color="#{C.On:ToHex()}">✓ Solved:</font> {Saved.SolvedText or ``}`, { TextSize = S.TextBody })
		elseif #Insights > 0 and Case.Deduction then
			local Box = Local.Block(Body, Next())
			Box.Name = `Deduce_{CaseId}`
			Local.Text(Box, 0, `<b>{Case.Deduction.Question}</b>`, { Color = C.Gold })
			local Row = Local.Row(Box, 1)
			Row.Size = UDim2.new(1, 0, 0, 96)
			local Grid = Row:FindFirstChildOfClass(`UIListLayout`)
			if Grid then Grid.Wraps = true end
			for Index, Option in Case.Deduction.Options do
				Local.Button(Row, Index, Option, `default`, 230, function()
					Local.Send({ Action = `Deduce`; Case = CaseId; Option = Index })
				end)
			end
		end
	end

	if not Any then
		Local.Text(Body, 1, `No case files yet. Some things at this school don't add up; when you notice one, it goes here.`, { Color = C.TextDim })
	end
end

function Local.Render()
	if not Ui or not Ui.Panel.Visible then return end
	for _, Child in Ui.Body:GetChildren() do
		if Child:IsA(`GuiObject`) then Child:Destroy() end
	end
	local Q = (StateController.GetProfile(false) or {}).Quests
	if typeof(Q) ~= `table` then
		Local.Text(Ui.Body, 1, `Loading...`, { Color = C.TextDim })
		return
	end
	if Tab == 1 then Local.RenderQuests(Q) else Local.RenderCases(Q) end
end

---| API |---

function Shared.Toggle(Open: boolean?)
	if not Ui then return end
	if Open == nil then Open = not Ui.Panel.Visible end
	Ui.Panel.Visible = Open
	if Open then Local.Render() end
end

function Shared.SelectTab(Index: number)
	Tab = Index
	-- Keep the tab highlight in sync (silent: don't re-fire onChanged).
	if Ui and Ui.TabsApi then Ui.TabsApi:Select(Index, true) end
	Local.Render()
end

function Shared.OnStart()
	Ui = Local.Build()
	UserInputService.InputBegan:Connect(function(Input, Processed)
		if Processed or Input.KeyCode ~= TOGGLE_KEY then return end
		if Typing.Active() then return end
		Shared.Toggle()
	end)
	StateController.ProfileUpdated:Connect(function(_, Action)
		if Action and Action.type == `SetQuests` then Local.Render() end
	end)
	-- VFX P2-13: evidence-board feedback
	Fx.On(`LinkHit`, function(D)
		if typeof(D) ~= `table` then return end
		Fresh = pairKey(tostring(D.Case), tostring(D.A), tostring(D.B))
		Typed = Fresh
		Local.Render()
	end)
	Fx.On(`LinkMiss`, Local.Miss)
	Fx.On(`Solved`, function(D) task.delay(0.2, Local.Solved, D) end)
end

return Shared
