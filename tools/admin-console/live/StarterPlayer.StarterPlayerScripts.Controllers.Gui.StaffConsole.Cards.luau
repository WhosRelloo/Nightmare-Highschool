--[[ StaffConsole.Cards (client): one action card, its option controls, the list picker and the hold ring (spec §4-§5). ]]
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local GuiService = game:GetService("GuiService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Kit = require(ReplicatedStorage:WaitForChild("UI"):WaitForChild("Components"))
local Theme = Kit.Theme
local Art = require(ReplicatedStorage:WaitForChild("Config"):WaitForChild("ConsoleArt"))
local SC = require(ReplicatedStorage:WaitForChild("Functions"):WaitForChild("StaffConsole"))
local Cards = {}

local rgb = Color3.fromRGB
Cards.COL = {
	Iron = rgb(26, 23, 29); IronHi = rgb(44, 39, 48); Velvet = rgb(54, 10, 22); Brass = rgb(214, 170, 96);
	Bone = rgb(236, 226, 206); Dim = rgb(196, 184, 166); Crimson = rgb(214, 50, 62); Good = rgb(150, 200, 140);
}
local COL = Cards.COL
local FACE = { Body = Theme.FontFaces.Body; Bold = Theme.FontFaces.BodyBold; Title = Font.new(Theme.FontFaces.Title.Family, Enum.FontWeight.Bold) }

function Cards.New(Class: string, Props: any, Parent: Instance?): any
	local I = Instance.new(Class)
	for K, V in Props do (I :: any)[K] = V end
	if Parent then I.Parent = Parent end
	return I
end
local New = Cards.New

-- an art piece as a sliced ImageLabel, or a plain iron frame until its id exists
function Cards.Piece(Name: string, Parent: Instance, Pos: UDim2, Size: UDim2, Extra: any?): GuiObject
	local Img = Art.Image(Name)
	local Obj
	if Img then
		local S = Art.Slice[Name]
		Obj = New("ImageLabel", { Name = Name; Image = Img; BackgroundTransparency = 1; Position = Pos; Size = Size;
			ScaleType = if S[1] > 0 then Enum.ScaleType.Slice else Enum.ScaleType.Stretch;
			SliceCenter = Rect.new(S[1] * 2, S[2] * 2, S[3] * 2, S[4] * 2); SliceScale = 0.5 }, Parent)
	else
		Obj = New("Frame", { Name = Name; BackgroundColor3 = COL.Iron; BorderSizePixel = 0; Position = Pos; Size = Size }, Parent)
		New("UICorner", { CornerRadius = UDim.new(0, 10) }, Obj)
		New("UIStroke", { Color = COL.Brass; Thickness = 1.5; Transparency = 0.35 }, Obj)
	end
	for K, V in Extra or {} do (Obj :: any)[K] = V end
	return Obj
end

function Cards.Text(Parent: Instance, Name: string, Text: string, Size: number, Face: Font, Color: Color3, Pos: UDim2, Box: UDim2, Wrap: boolean?): TextLabel
	return New("TextLabel", { Name = Name; Text = Text; TextSize = math.max(20, Size); FontFace = Face; TextColor3 = Color;
		BackgroundTransparency = 1; Position = Pos; Size = Box; TextWrapped = Wrap == true; TextTruncate = if Wrap then Enum.TextTruncate.None else Enum.TextTruncate.AtEnd;
		TextXAlignment = Enum.TextXAlignment.Left; TextYAlignment = Enum.TextYAlignment.Top }, Parent)
end

function Cards.Icon(Parent: Instance, Def: any, Pos: UDim2, Size: number)
	local Img = Art.Image(Def.Icon) or Art.Image("Sec" .. tostring(Def.Section))
	if not Img then return end
	New("ImageLabel", { Name = "Icon"; Image = Img; BackgroundTransparency = 1; Position = Pos; Size = UDim2.fromOffset(Size, Size) }, Parent)
end

-- chips fit their text (about 11 px a character at 20 px bold, plus the 12 px sliced ends and some air)
local function chip(Parent: Instance, Name: string, Text: string, On: boolean, Danger: boolean?, W: number?): TextButton
	local Piece = if Danger then "ChipDanger" elseif On then "ChipOn" else "Chip"
	local Holder = Cards.Piece(Piece, Parent, UDim2.new(), UDim2.fromOffset(math.max(W or 0, 56, utf8.len(Text) * 11 + 30), 36))
	local B = New("TextButton", { Name = Name; Text = Text; TextSize = 20; FontFace = FACE.Bold; TextColor3 = if On then COL.Iron else COL.Bone;
		BackgroundTransparency = if Art.Image(Piece) then 1 else 0; BackgroundColor3 = if On then COL.Brass else COL.IronHi;
		Size = UDim2.fromScale(1, 1); AutoButtonColor = true; Selectable = true }, Holder)
	return B
end

-- Values[ArgName] holds the card's current option values (the shell keeps one table per card id).
-- Opts = { OnPick: (Arg, Choices, Done) -> () } opens the shared picker for long lists.
function Cards.Options(Row: Instance, Def: any, Values: any, Lists: any, Opts: any)
	for _, A in Def.Args do
		local Label = A.Label or A.Name
		if A.Kind == "choice" then
			local Choices = A.Choices
			if Choices and #Choices <= 5 and not A.From then
				for _, C in Choices do
					local Text = if A.Name == "Days" then (if C == 0 then "Forever" else C .. "d") elseif A.Name == "Tier" and typeof(C) == "number" then ({ "I", "II", "III" })[C] else tostring(C)
					local B = chip(Row, "Opt_" .. A.Name .. "_" .. tostring(C), Text, Values[A.Name] == C, A.Name == "Days" and C == 0)
					B.Activated:Connect(function() Values[A.Name] = C Opts.Redraw() end)
				end
			else
				local List = Choices or (Lists and Lists[A.From]) or {}
				local Cur = Values[A.Name]
				local Shown = Label
				for _, It in List do if It == Cur or (typeof(It) == "table" and It.Id == Cur) then Shown = if typeof(It) == "table" then It.Name else tostring(It) end end
				local B = chip(Row, "Opt_" .. A.Name, Shown .. " ▾", Cur ~= nil, false)
				B.Activated:Connect(function()
					Opts.OnPick(A, List, function(V) Values[A.Name] = V Opts.Redraw() end)
				end)
			end
		elseif A.Kind == "number" or A.Kind == "text" then
			local Box = New("TextBox", { Name = "Opt_" .. A.Name; PlaceholderText = Label; Text = if Values[A.Name] ~= nil then tostring(Values[A.Name]) else "";
				TextSize = 20; FontFace = FACE.Body; TextColor3 = COL.Bone; PlaceholderColor3 = COL.Dim; BackgroundColor3 = COL.IronHi;
				ClearTextOnFocus = false; Size = UDim2.fromOffset(if A.Kind == "number" then 100 else 220, 36); TextXAlignment = Enum.TextXAlignment.Left }, Row)
			New("UICorner", { CornerRadius = UDim.new(0, 8) }, Box)
			New("UIStroke", { Color = COL.Brass; Thickness = 1; Transparency = 0.5; ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, Box)
			New("UIPadding", { PaddingLeft = UDim.new(0, 10) }, Box)
			Box:GetPropertyChangedSignal("Text"):Connect(function()
				if A.Kind == "number" then
					local Clean = string.gsub(Box.Text, "[^%d%-%.]", "")
					if Clean ~= Box.Text then Box.Text = Clean return end
					Values[A.Name] = tonumber(Clean)
				else
					Values[A.Name] = Box.Text
				end
			end)
		elseif A.Kind == "toggle" then
			local On = Values[A.Name] ~= false
			Values[A.Name] = On
			local B = chip(Row, "Opt_" .. A.Name, Label .. (if On then ": on" else ": off"), On, false)
			B.Activated:Connect(function() Values[A.Name] = not (Values[A.Name] ~= false) Opts.Redraw() end)
		end
	end
end

-- the hold ring: a danger card's Run button runs only after a 0.8 s hold; letting go early cancels.
-- Cards.Holding is true while any hold runs (the shell holds its status redraw for it). A button destroyed mid-hold (a
-- redraw) cancels the hold: it never fires. Returns { Begin, Stop } for checks/console_hold.lua.
-- (Task 8) Keys: a GuiButton never gets InputBegan for Return (and a selected button not for gamepad A), so A / Return
-- are read from UserInputService while this button is the selected object; moving the selection off cancels.
-- Pointers: a mouse or touch that moves off the button cancels (MouseLeave isn't reliable for touch), and so does
-- that input ending anywhere (a finger lifted off the button never reaches its InputEnded).
Cards.Holding = false
local CurrentStop = nil :: (() -> ())?
local HOLD_KEYS = { [Enum.KeyCode.ButtonA] = true; [Enum.KeyCode.Return] = true }
-- (fix round 1) a key that a TextBox is taking (Enter on a palette query) never holds a selected Run: the box may
-- already have let go of focus by the time UserInputService sees the key, so a just-released box counts too
local BoxReleasedAt = -math.huge
UserInputService.TextBoxFocusReleased:Connect(function() BoxReleasedAt = os.clock() end)
local function typing(): boolean
	return UserInputService:GetFocusedTextBox() ~= nil or os.clock() - BoxReleasedAt < 0.25
end
-- the shell closes the console mid-hold: cancel it (a hidden gui may never see the button let go)
function Cards.CancelHold() if CurrentStop then CurrentStop() end end
function Cards.Hold(Button: GuiButton, Ring: GuiObject?, Reduced: boolean, OnDone: () -> ()): any
	local Holding = nil :: any
	local function stop()
		if Holding then
			Holding.Tween:Cancel()
			for _, C in Holding.Conns do C:Disconnect() end
			Holding = nil
			Cards.Holding = false
			if CurrentStop == stop then CurrentStop = nil end
		end
		if Ring then (Ring :: any).ImageTransparency = 1 end
	end
	local function off(P: Vector3): boolean
		local A, S = Button.AbsolutePosition, Button.AbsoluteSize
		return P.X < A.X or P.Y < A.Y or P.X > A.X + S.X or P.Y > A.Y + S.Y
	end
	-- Input: the InputObject that started it (a pointer or a key), nil for a check's plain Begin()
	local function begin(Input: InputObject?)
		stop()
		local Token = {}
		local V = Instance.new("NumberValue")
		local Tw = TweenService:Create(V, TweenInfo.new(SC.DANGER_HOLD, Enum.EasingStyle.Linear), { Value = 1 })
		-- alt-tab mid-hold: the window loses focus, the let-go may never arrive, so it cancels
		local Conns = { Button.Destroying:Connect(stop), UserInputService.WindowFocusReleased:Connect(stop) }
		Holding = { Token = Token; Tween = Tw; Conns = Conns }
		if Input then
			local Key = HOLD_KEYS[Input.KeyCode] == true
			table.insert(Conns, UserInputService.InputEnded:Connect(function(I)
				if I == Input or (Key and I.KeyCode == Input.KeyCode) then stop() end
			end))
			if Key then
				table.insert(Conns, GuiService:GetPropertyChangedSignal("SelectedObject"):Connect(function()
					if GuiService.SelectedObject ~= Button then stop() end
				end))
			else
				table.insert(Conns, UserInputService.InputChanged:Connect(function(I)
					local T = I.UserInputType
					if (T == Enum.UserInputType.Touch and (I == Input or Input.UserInputType == Enum.UserInputType.Touch)) or T == Enum.UserInputType.MouseMovement then
						if off(I.Position) then stop() end
					end
				end))
			end
		end
		Cards.Holding = true
		CurrentStop = stop
		if Ring then
			V.Changed:Connect(function(X) (Ring :: any).ImageTransparency = 1 - X * 0.9 if not Reduced then (Ring :: any).Rotation = X * 360 end end)
		end
		Tw.Completed:Connect(function(State)
			local Mine = Holding and Holding.Token == Token
			if Mine then
				for _, C in Holding.Conns do C:Disconnect() end
				Holding = nil
				Cards.Holding = false
				if CurrentStop == stop then CurrentStop = nil end
				if Ring then (Ring :: any).ImageTransparency = 1 end
			end
			V:Destroy()
			if State == Enum.PlaybackState.Completed and Mine and Button.Parent ~= nil then OnDone() end
		end)
		Tw:Play()
	end
	Button.InputBegan:Connect(function(I)
		local T = I.UserInputType
		if T == Enum.UserInputType.MouseButton1 or T == Enum.UserInputType.Touch then begin(I) end
	end)
	-- A / Return on the selected button (the gamepad and keyboard UI selection)
	local KeyConn = UserInputService.InputBegan:Connect(function(I)
		if HOLD_KEYS[I.KeyCode] and GuiService.SelectedObject == Button and not Holding and not typing() then begin(I) end
	end)
	Button.Destroying:Connect(function() KeyConn:Disconnect() end)
	Button.InputEnded:Connect(function(I)
		if not HOLD_KEYS[I.KeyCode] then stop() end
	end)
	Button.MouseLeave:Connect(stop)
	return { Begin = function() begin(nil) end; Stop = stop }
end

-- one card. Opts = { Values, Lists, Selected, Fav: boolean, OnRun(Def, Values), OnFav(Def), OnPick, Redraw, Reduced }
function Cards.Card(Parent: Instance, Def: any, Pos: UDim2, Opts: any): GuiObject
	local C = Cards.Piece("Card", Parent, Pos, UDim2.fromOffset(380, 168), { Name = "Card_" .. Def.Id })
	-- the art's icon well: a ring centred at (38, 38), about 48 px across inside; corner brackets 12-36 px in from each corner
	Cards.Icon(C, Def, UDim2.fromOffset(18, 18), 40)
	Cards.Text(C, "Title", (if Opts.Fav then "★ " else "") .. Def.Title, 22, FACE.Bold, if Def.Danger then COL.Crimson else COL.Bone, UDim2.fromOffset(76, 16), UDim2.fromOffset(264, 28))
	Cards.Text(C, "Help", Def.Help, 20, FACE.Body, COL.Dim, UDim2.fromOffset(76, 44), UDim2.fromOffset(284, 50), true)
	local Row = New("ScrollingFrame", { Name = "Options"; BackgroundTransparency = 1; Position = UDim2.fromOffset(24, 108); Size = UDim2.fromOffset(230, 44);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.X; ScrollingDirection = Enum.ScrollingDirection.X; ScrollBarThickness = 3;
		ScrollBarImageColor3 = COL.Brass; ScrollBarImageTransparency = 0.4; Selectable = false }, C)
	New("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal; VerticalAlignment = Enum.VerticalAlignment.Top; Padding = UDim.new(0, 6); SortOrder = Enum.SortOrder.LayoutOrder }, Row)
	Cards.Options(Row, Def, Opts.Values, Opts.Lists, Opts)
	local NeedsPos = false
	for _, A in Def.Args do if A.Kind == "position" then NeedsPos = true end end
	local Label = if NeedsPos then "Ctrl+click" elseif Def.Danger then "Hold" else "Run"
	local RunB = New("TextButton", { Name = "Run"; Text = Label; TextSize = 20; FontFace = FACE.Bold; TextColor3 = if Def.Danger then COL.Bone else COL.Iron;
		BackgroundColor3 = if Def.Danger then COL.Velvet else COL.Brass; Position = UDim2.fromOffset(262, 108); Size = UDim2.fromOffset(92, 40);
		AutoButtonColor = true; Selectable = not NeedsPos; Active = not NeedsPos }, C)
	New("UICorner", { CornerRadius = UDim.new(0, 8) }, RunB)
	if not NeedsPos then
		if Def.Danger then
			local Ring = New("ImageLabel", { Name = "HoldRing"; Image = Art.Image("HoldRing") or "rbxassetid://0"; BackgroundTransparency = 1; ImageTransparency = 1;
				AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromOffset(40, 40); ZIndex = 3 }, RunB)
			Cards.Hold(RunB, Ring, Opts.Reduced, function() Opts.OnRun(Def, Opts.Values) end)
		else
			RunB.Activated:Connect(function() Opts.OnRun(Def, Opts.Values) end)
		end
	end
	C.InputBegan:Connect(function(I)
		if I.UserInputType == Enum.UserInputType.MouseButton2 then Opts.OnFav(Def) end
	end)
	if not Opts.Reduced then
		C.MouseEnter:Connect(function() C.Position = Pos - UDim2.fromOffset(0, 2) end)
		C.MouseLeave:Connect(function() C.Position = Pos end)
	end
	return C
end

-- the shared list picker over the card grid
function Cards.Picker(Parent: Instance, Title: string, List: any, Done: (any) -> ()): GuiObject
	local Old = Parent:FindFirstChild("Picker")
	if Old then Old:Destroy() end
	local P = Cards.Piece("Side", Parent, UDim2.fromOffset(656, 170), UDim2.fromOffset(360, 460), { Name = "Picker"; ZIndex = 20 })
	Cards.Text(P, "Title", Title, 22, FACE.Bold, COL.Brass, UDim2.fromOffset(20, 14), UDim2.fromOffset(260, 28))
	local X = New("TextButton", { Name = "Close"; Text = "✕"; TextSize = 22; FontFace = FACE.Bold; TextColor3 = COL.Bone; BackgroundTransparency = 1;
		Position = UDim2.fromOffset(308, 8); Size = UDim2.fromOffset(40, 40); ZIndex = 21 }, P)
	X.Activated:Connect(function() P:Destroy() end)
	local L = New("ScrollingFrame", { Name = "List"; BackgroundTransparency = 1; Position = UDim2.fromOffset(16, 56); Size = UDim2.fromOffset(328, 390);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 6; ZIndex = 21 }, P)
	New("UIListLayout", { Padding = UDim.new(0, 4) }, L)
	for _, It in List do
		local V, Text = It, tostring(It)
		if typeof(It) == "table" then V, Text = It.Id, It.Name or tostring(It.Id) end
		local B = New("TextButton", { Name = "Pick_" .. tostring(V); Text = Text; TextSize = 20; FontFace = FACE.Body; TextColor3 = COL.Bone; BackgroundColor3 = COL.IronHi;
			Size = UDim2.new(1, -8, 0, 40); TextXAlignment = Enum.TextXAlignment.Left; ZIndex = 22 }, L)
		New("UIPadding", { PaddingLeft = UDim.new(0, 10) }, B)
		B.Activated:Connect(function() P:Destroy() Done(V) end)
	end
	return P
end

Cards.FACE = FACE
return Cards
