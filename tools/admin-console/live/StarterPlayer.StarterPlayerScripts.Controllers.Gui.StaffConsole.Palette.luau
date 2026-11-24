--[[ StaffConsole.Palette (client): Ctrl+K finds any action by title, help or synonym (StaffConsole.Search). Enter runs the
	top result when it needs no options and isn't dangerous; otherwise it jumps to the card. ]]
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SC = require(ReplicatedStorage:WaitForChild("Functions"):WaitForChild("StaffConsole"))
local Cards = require(script.Parent:WaitForChild("Cards"))
local New, Piece, Text, COL, FACE = Cards.New, Cards.Piece, Cards.Text, Cards.COL, Cards.FACE
local Palette = {}

-- Opts = { Defs, OnRun(Def), OnJump(Def) }
function Palette.Open(Board: Instance, Opts: any): GuiObject
	local Old = Board:FindFirstChild("Palette")
	if Old then Old:Destroy() end
	local P = Piece("Side", Board, UDim2.fromOffset(440, 120), UDim2.fromOffset(720, 540), { Name = "Palette"; ZIndex = 30 })
	local Box = New("TextBox", { Name = "Query"; PlaceholderText = "Find any action…"; Text = ""; TextSize = 24; FontFace = FACE.Body; TextColor3 = COL.Bone;
		PlaceholderColor3 = COL.Dim; BackgroundColor3 = COL.IronHi; ClearTextOnFocus = false; Position = UDim2.fromOffset(24, 20); Size = UDim2.fromOffset(672, 52);
		TextXAlignment = Enum.TextXAlignment.Left; ZIndex = 31 }, P)
	New("UIPadding", { PaddingLeft = UDim.new(0, 14) }, Box)
	local L = New("Frame", { Name = "Results"; BackgroundTransparency = 1; Position = UDim2.fromOffset(24, 84); Size = UDim2.fromOffset(672, 440); ZIndex = 31 }, P)
	New("UIListLayout", { Padding = UDim.new(0, 4) }, L)
	local Hits, Hi = {}, 1
	local function draw()
		for _, C in L:GetChildren() do if C:IsA("GuiObject") then C:Destroy() end end
		for I, D in Hits do
			if I > 8 then break end
			local R = New("TextButton", { Name = "Hit_" .. D.Id; Text = ""; BackgroundColor3 = if I == Hi then COL.Velvet else COL.IronHi; Size = UDim2.new(1, 0, 0, 50); ZIndex = 32 }, L)
			Cards.Icon(R, D, UDim2.fromOffset(8, 5), 40)
			Text(R, "Title", D.Title, 22, FACE.Bold, if D.Danger then COL.Crimson else COL.Bone, UDim2.fromOffset(58, 4), UDim2.fromOffset(380, 28))
			Text(R, "Where", `{D.Side} · {D.Section}`, 20, FACE.Body, COL.Dim, UDim2.fromOffset(440, 10), UDim2.fromOffset(224, 26))
			for _, K in R:GetDescendants() do if K:IsA("GuiObject") then K.ZIndex = 33 end end
			R.Activated:Connect(function() Hi = I Palette.Choose(P, Hits[Hi], Opts) end)
		end
	end
	Box:GetPropertyChangedSignal("Text"):Connect(function() Hits = SC.Search(Opts.Defs, Box.Text) Hi = 1 draw() end)
	Box.FocusLost:Connect(function(Enter) if Enter and Hits[Hi] then Palette.Choose(P, Hits[Hi], Opts) end end)
	P:SetAttribute("Open", true)
	Palette.Move = function(D: number) if P.Parent and #Hits > 0 then Hi = math.clamp(Hi + D, 1, math.min(8, #Hits)) draw() end end
	task.defer(function() Box:CaptureFocus() end)
	return P
end

function Palette.Choose(P: Instance, D: any, Opts: any)
	P:Destroy()
	if not D then return end
	if #D.Args == 0 and not D.Danger then Opts.OnRun(D) else Opts.OnJump(D) end
end

return Palette
