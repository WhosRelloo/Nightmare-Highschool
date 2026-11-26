--[[
	Registrar (client). Controllers.Gui.Registrar: the elective board, opened by the Registrar desk's prompt
	(Services.School.Electives sends ElectiveEvent Open). Ten seal cards (Config.Electives, by Order); open ones can be
	picked, sealed ones say "Opens in a later term". The detail panel shows the room, teacher and days, what the class
	teaches, and "Enrol for Term N". Pressing it sends ElectiveEnrol; on success a wax seal stamps the card.
	Built from the UI kit (Panel, Button, Text; Theme colours; Motion via Kit.tween). Gamepad: cards are selectable
	buttons (D-pad + A), B closes.
	API: Open(Message), Close(), IsOpen()
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local GuiService = game:GetService(`GuiService`)
local UserInputService = game:GetService(`UserInputService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Packets = require(ReplicatedStorage.Remotes.Packets)
local Electives = require(ReplicatedStorage.Config.Electives)

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local Fonts = Theme.Fonts

-- what each open elective teaches (shown in the detail panel); closed ones only show their seal
local DETAIL = {
	Anatomy = {
		Blurb = `Open the school's preserved specimens on the bench: clockwork creatures first, stranger ones later. Pick the right tool, trace the seams, lift each part out and name it.`;
		Teaches = { `First-aid pouch heals +10% per level`, `Revive downed friends faster`, `The Specimen Journal \u{00B7} title "Anatomist" \u{00B7} the Brass Loupe Monocle` };
		Specimens = `Clockwork Frog \u{00B7} Lv 1    Clockwork Raven \u{00B7} Lv 3    Clockwork Wyvern \u{00B7} Lv 5`;
	};
}

local Shared = {}
local Local = {}
local Ui = nil
local State = { Pick = nil; Locked = false; Term = 0; Selected = `Anatomy` }

function Local.Label(Parent: Instance, Text: string, Size: number, Props)
	local T = Kit.Text({ Text = Text; TextSize = Size; TextColor3 = C.Text; RichText = true; TextWrapped = true;
		TextXAlignment = Enum.TextXAlignment.Left; Parent = Parent })
	for K, V in Props or {} do T[K] = V end
	return T
end

function Local.Sorted()
	local List = {}
	for _, D in Electives.List do table.insert(List, D) end
	table.sort(List, function(A, B) return A.Order < B.Order end)
	return List
end

function Local.Build()
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHRegistrar`
	G.ResetOnSpawn = false
	G.DisplayOrder = 14
	G.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	G.Enabled = false
	G.Parent = Player:WaitForChild(`PlayerGui`)
	Kit.AutoScale(G)

	local Panel, Api = Kit.Panel({ title = `The Registrar \u{00B7} Term`; Name = `Panel`; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromOffset(1040, 600); Parent = G })
	local B = Api.Content
	Kit.Button({ text = `X`; style = `ghost`; textSize = 16; Size = UDim2.fromOffset(36, 32); AnchorPoint = Vector2.new(1, 0);
		Position = UDim2.new(1, -2, 0, -4); Parent = B; onClick = function() Shared.Close() end })
	local Head = Local.Label(B, `Choose your elective`, 26, { Font = Fonts.Title; TextColor3 = C.Gold; Position = UDim2.fromOffset(8, 0); Size = UDim2.new(0, 600, 0, 32) })
	Local.Label(B, `Tuesdays and Thursdays, periods 3 and 4. Your choice holds for the term; change it when the next term begins.`, 15,
		{ TextColor3 = C.TextDim; Position = UDim2.fromOffset(8, 34); Size = UDim2.new(0, 600, 0, 40) })

	-- the cards: 5 x 2 on the left
	local Grid = Instance.new(`Frame`)
	Grid.Name = `Cards`
	Grid.BackgroundTransparency = 1
	Grid.Position = UDim2.fromOffset(8, 84)
	Grid.Size = UDim2.fromOffset(600, 440)
	Grid.Parent = B
	local L = Instance.new(`UIGridLayout`)
	L.CellSize = UDim2.fromOffset(112, 210)
	L.CellPadding = UDim2.fromOffset(9, 12)
	L.SortOrder = Enum.SortOrder.LayoutOrder
	L.Parent = Grid
	local Cards = {}
	for _, D in Local.Sorted() do
		local Card = Instance.new(`TextButton`)
		Card.Name = D.Id
		Card.LayoutOrder = D.Order
		Card.Text = ``
		Card.AutoButtonColor = false
		Card.BackgroundColor3 = C.Well
		Card.BackgroundTransparency = if D.Open then 0.05 else 0.35
		Card.BorderSizePixel = 0
		Card.Selectable = true
		Card.Parent = Grid
		local Stroke = Instance.new(`UIStroke`)
		Stroke.Color = if D.Open then C.Gold else C.IronDim
		Stroke.Thickness = if D.Open then 2 else 1
		Stroke.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
		Stroke.Parent = Card
		local Seal = Instance.new(`Frame`)
		Seal.Name = `Seal`
		Seal.AnchorPoint = Vector2.new(0.5, 0)
		Seal.Position = UDim2.new(0.5, 0, 0, 18)
		Seal.Size = UDim2.fromOffset(70, 70)
		Seal.BackgroundColor3 = if D.Open then C.Crimson else C.Iron
		Seal.Parent = Card
		local Round = Instance.new(`UICorner`)
		Round.CornerRadius = UDim.new(0.5, 0)
		Round.Parent = Seal
		Local.Label(Seal, D.Name:sub(1, 1), 34, { Font = Fonts.Title; TextColor3 = if D.Open then C.Gold else C.TextFaint;
			TextXAlignment = Enum.TextXAlignment.Center; Size = UDim2.fromScale(1, 1) })
		Local.Label(Card, D.Name, 18, { Font = Fonts.Title; TextXAlignment = Enum.TextXAlignment.Center;
			TextColor3 = if D.Open then C.Text else C.TextDim; Position = UDim2.fromOffset(4, 104); Size = UDim2.new(1, -8, 0, 44) })
		Local.Label(Card, if D.Open then `Open \u{00B7} Room {D.Room:sub(2)}` else `Later term`, 14,
			{ Name = `Status`; TextXAlignment = Enum.TextXAlignment.Center; TextColor3 = if D.Open then C.Gold else C.TextFaint;
			Position = UDim2.fromOffset(4, 150); Size = UDim2.new(1, -8, 0, 40) })
		Card.Activated:Connect(function()
			pcall(Kit.PlaySound, `Tick`)
			if not D.Open then
				Local.Say(`{D.Name} opens in a later term.`)
				return
			end
			State.Selected = D.Id
			Local.Render()
		end)
		Cards[D.Id] = { Card = Card; Stroke = Stroke }
	end

	-- the detail panel on the right
	local Detail = Instance.new(`Frame`)
	Detail.Name = `Detail`
	Detail.BackgroundColor3 = C.Well
	Detail.BackgroundTransparency = 0.2
	Detail.BorderSizePixel = 0
	Detail.Position = UDim2.fromOffset(628, 0)
	Detail.Size = UDim2.new(1, -636, 1, -8)
	Detail.Parent = B
	local Pad = Instance.new(`UIPadding`)
	for _, K in { `PaddingLeft`, `PaddingRight`, `PaddingTop`, `PaddingBottom` } do Pad[K] = UDim.new(0, 16) end
	Pad.Parent = Detail
	local Title = Local.Label(Detail, ``, 26, { Font = Fonts.Title; TextColor3 = C.Gold; Size = UDim2.new(1, 0, 0, 32) })
	local Where = Local.Label(Detail, ``, 15, { TextColor3 = C.TextDim; Position = UDim2.fromOffset(0, 34); Size = UDim2.new(1, 0, 0, 40) })
	local Blurb = Local.Label(Detail, ``, 16, { Position = UDim2.fromOffset(0, 78); Size = UDim2.new(1, 0, 0, 110); TextYAlignment = Enum.TextYAlignment.Top })
	Local.Label(Detail, `WHAT IT TEACHES YOU`, 13, { Font = Fonts.Title; TextColor3 = C.Gold; Position = UDim2.fromOffset(0, 194); Size = UDim2.new(1, 0, 0, 18) })
	local Teaches = Local.Label(Detail, ``, 15, { Position = UDim2.fromOffset(0, 214); Size = UDim2.new(1, 0, 0, 110); TextYAlignment = Enum.TextYAlignment.Top })
	Local.Label(Detail, `SPECIMENS`, 13, { Font = Fonts.Title; TextColor3 = C.Gold; Position = UDim2.fromOffset(0, 330); Size = UDim2.new(1, 0, 0, 18) })
	local Specimens = Local.Label(Detail, ``, 14, { TextColor3 = C.TextDim; Position = UDim2.fromOffset(0, 350); Size = UDim2.new(1, 0, 0, 40) })
	local Enrol, EnrolApi = Kit.Button({ text = `Enrol`; style = `gold`; textSize = 18; Size = UDim2.new(1, 0, 0, 46);
		AnchorPoint = Vector2.new(0, 1); Position = UDim2.new(0, 0, 1, -24); Parent = Detail;
		onClick = function() Local.Enrol() end })
	local Note = Local.Label(Detail, `Pressing it stamps your timetable with a wax seal.`, 13, { TextColor3 = C.TextFaint;
		TextXAlignment = Enum.TextXAlignment.Center; AnchorPoint = Vector2.new(0, 1); Position = UDim2.new(0, 0, 1, 0); Size = UDim2.new(1, 0, 0, 20) })
	local Stamp = Local.Label(Detail, `ENROLLED`, 30, { Name = `Stamp`; Font = Fonts.Title; TextColor3 = C.Crimson; Visible = false;
		TextXAlignment = Enum.TextXAlignment.Center; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 0, 0, 260); Size = UDim2.fromOffset(260, 60); Rotation = -12 })
	local StampScale = Instance.new(`UIScale`)
	StampScale.Parent = Stamp

	Ui = { Gui = G; Panel = Panel; Api = Api; Head = Head; Cards = Cards; Title = Title; Where = Where; Blurb = Blurb; Teaches = Teaches;
		Specimens = Specimens; Enrol = Enrol; EnrolApi = EnrolApi; Note = Note; Stamp = Stamp; StampScale = StampScale }
end

-- a short line under the button (sealed cards, refusals); clears itself
function Local.Say(Text: string)
	if not Ui then return end
	Ui.Note.Text = Text
	Ui.Note.TextColor3 = C.Gold
	local Mark = os.clock()
	Ui.NoteMark = Mark
	task.delay(3, function()
		if Ui and Ui.NoteMark == Mark then
			Ui.Note.Text = `Pressing it stamps your timetable with a wax seal.`
			Ui.Note.TextColor3 = C.TextFaint
		end
	end)
end

function Local.Render()
	if not Ui then return end
	local D = Electives.Get(State.Selected) or Electives.Get(`Anatomy`)
	local X = DETAIL[D.Id] or {}
	pcall(function() Ui.Api:SetTitle(`The Registrar \u{00B7} Term {State.Term}`) end)
	Ui.Title.Text = D.Name
	Ui.Where.Text = `Room {D.Room:sub(2)} \u{00B7} {D.Teacher} \u{00B7} Tue and Thu, periods 3 and 4`
	Ui.Blurb.Text = X.Blurb or ``
	Ui.Teaches.Text = if X.Teaches then `\u{2022} ` .. table.concat(X.Teaches, `\n\u{2022} `) else ``
	Ui.Specimens.Text = X.Specimens or ``
	local Mine = State.Pick == D.Id
	local Label = if Mine and State.Locked then `Enrolled for this term`
		elseif State.Locked then `Your pick holds until next term`
		else `Enrol for Term {State.Term}`
	Ui.EnrolApi:SetText(Label)
	Ui.Enrol.Active = not State.Locked
	Ui.Enrol.AutoButtonColor = not State.Locked
	for Id, Row in Ui.Cards do
		local Def = Electives.Get(Id)
		Row.Stroke.Thickness = if Id == State.Selected then 3 elseif Def.Open then 2 else 1
		Row.Stroke.Color = if Id == State.Pick then C.Crimson elseif Def.Open then C.Gold else C.IronDim
	end
	Ui.Stamp.Visible = Mine and State.Locked
end

function Local.Enrol()
	if State.Locked or not Ui then return end
	pcall(Kit.PlaySound, `Tick`)
	Packets.ElectiveEnrol:Fire({ Id = State.Selected })
end

function Local.StampIn()
	Ui.Stamp.Visible = true
	if Kit.ReducedMotion and Kit.ReducedMotion() then
		Ui.StampScale.Scale = 1
		return
	end
	Ui.StampScale.Scale = 1.4
	Ui.Stamp.TextTransparency = 1
	Kit.tween(Ui.StampScale, TweenInfo.new(0.18, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 })
	Kit.tween(Ui.Stamp, TweenInfo.new(0.12), { TextTransparency = 0 })
end

function Local.OnEvent(Message)
	if typeof(Message) ~= `table` then return end
	State.Pick = Message.Pick
	State.Locked = Message.Locked == true
	State.Term = Message.Term or State.Term
	if Message.Type == `Open` then
		Shared.Open()
	elseif Message.Type == `Result` then
		if Message.Ok then
			Local.Render()
			Local.StampIn()
			task.delay(0.9, Shared.Close)
		else
			local Why = ({ Far = `Come back to the Registrar's desk.`; Locked = `Your pick holds until next term.`; Closed = `That class opens in a later term.` })[Message.Why or ``]
			Local.Say(Why or `Couldn't enrol right now.`)
			Local.Render()
		end
	end
end

function Shared.IsOpen(): boolean return Ui ~= nil and Ui.Gui.Enabled end

function Shared.Open()
	if Player:GetAttribute(`InMainMenu`) == true then return end
	if not Ui then Local.Build() end
	State.Selected = State.Pick or `Anatomy`
	Local.Render()
	Ui.Gui.Enabled = true
	pcall(function() Kit.FadeIn(Ui.Panel, 0.22) end)
	if UserInputService.GamepadEnabled then GuiService.SelectedObject = Ui.Cards[State.Selected].Card end
end

function Shared.Close()
	if not (Ui and Ui.Gui.Enabled) then return end
	if GuiService.SelectedObject and GuiService.SelectedObject:IsDescendantOf(Ui.Gui) then GuiService.SelectedObject = nil end
	Ui.Gui.Enabled = false
end

function Shared.OnStart()
	Packets.ElectiveEvent.OnClientEvent:Connect(Local.OnEvent)
	UserInputService.InputBegan:Connect(function(Input)
		if Shared.IsOpen() and (Input.KeyCode == Enum.KeyCode.ButtonB or Input.KeyCode == Enum.KeyCode.Escape) then Shared.Close() end
	end)
end

return Shared
