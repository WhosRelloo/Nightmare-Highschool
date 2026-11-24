--[[
	StaffConsole (client): the Headmaster's Console (spec docs/superpowers/specs/2026-11-23-admin-console-design.md, 1a).
	F3 toggles it for staff (the server decides); NHAdminOpen (other UI, tests) opens it. Moderate / Test sides, sections,
	cards from the server's registry (Info().Registry) plus StaffConsole.Tools' own-client cards, Ctrl+K palette,
	hold-to-confirm on danger cards, favourites and recent students for the session, a results feed.
	Keys: F3 open/close, 1-7 sections, Tab side, Ctrl+K palette, Esc closes (on GuiService.MenuOpened: Roblox keeps
	Escape). Controller: LB / RB sections, A run, Y favourite, B closes.
	Studio probe (HudState.Probe "Console"): Open, Close, Side, Section, Search, Info, Pick.
]]
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local ContextActionService = game:GetService("ContextActionService")
local GuiService = game:GetService("GuiService")
local Kit = require(ReplicatedStorage:WaitForChild("UI"):WaitForChild("Components"))
local SC = require(ReplicatedStorage:WaitForChild("Functions"):WaitForChild("StaffConsole"))
local Model = require(script:WaitForChild("Model"))
local View = require(script:WaitForChild("View"))
local Palette = require(script:WaitForChild("Palette"))
local Tools = require(script:WaitForChild("Tools"))

local Player = Players.LocalPlayer
local Shared = {}
local S = Model.New()
local U = nil :: any
local Open = false
local Info, Status, Inspect = nil :: any, nil :: any, nil :: any
local Values = {} :: { [string]: any }
local Busy = false

local function remotes()
	local F = ReplicatedStorage:FindFirstChild("NHAdmin")
	if not (F and F:GetAttribute("Ready")) then return nil end
	return F
end

local function defs(): any
	local Out = {}
	for _, D in (Info and Info.Registry) or {} do table.insert(Out, D) end
	for _, D in Tools.Defs do if D.Level <= S.Level then table.insert(Out, D) end end
	return Out
end

local function ctx(): any
	return { S = S; Info = Info; Status = Status; Defs = defs(); Values = Values; Lists = Info and Info.Lists; Inspect = Inspect;
		Reduced = Kit.ReducedMotion and Kit.ReducedMotion() or false; Handlers = Shared.Handlers }
end

-- a redraw rebuilds the dynamic layer, so the gamepad selection is found again by its full name
-- Keep (the 1 s status refresh): the scroll lists (cards, rows, context) stay where the reader left them
function Shared.Redraw(Keep: boolean?)
	if not (U and Open) then return end
	local Sel = GuiService.SelectedObject
	local Name = if Sel and Sel:IsDescendantOf(U.Gui) then Sel:GetFullName() else nil
	local Scroll = {}
	if Keep and U.Dyn then
		for _, D in U.Dyn:GetDescendants() do if D:IsA("ScrollingFrame") then Scroll[D:GetFullName()] = D.CanvasPosition end end
	end
	View.Redraw(U, ctx())
	if Keep then
		-- AutomaticCanvasSize settles after layout, which can clamp the position: set it now and again next frame
		local Dyn = U.Dyn
		local function restore()
			if not Dyn.Parent then return end
			for _, D in Dyn:GetDescendants() do
				local P = D:IsA("ScrollingFrame") and Scroll[D:GetFullName()]
				if P then D.CanvasPosition = P end
			end
		end
		restore()
		task.spawn(function() task.wait() restore() end)
	end
	if Name then
		for _, D in U.Gui:GetDescendants() do
			if D:IsA("GuiObject") and D:GetFullName() == Name then GuiService.SelectedObject = D break end
		end
	end
end

local function run(D: any, Vals: any)
	Vals = Vals or {}
	local Ok, Why = Model.Ready(D, Vals, S.Selected, Info and Info.Lists)
	if not Ok then Model.Push(S, false, Why :: string, D.Title) Shared.Redraw() return end
	if D.Local then
		local Ok2, Msg = Tools.Do(D.Id, Vals, S.Selected)
		if D.Id == "ToolInspect" and Ok2 and S.Selected then Inspect = Tools.Inspect(S.Selected) end
		Model.Push(S, Ok2, Msg, D.Title)
		Shared.Redraw()
		return
	end
	local F = remotes()
	if not F or Busy then return end
	Busy = true
	local Target = if D.Target ~= "none" then S.Selected else nil
	local OkCall, A, B = pcall(F.Run.InvokeServer, F.Run, D.Id, Target, Vals)
	Busy = false
	Model.Push(S, OkCall and A == true, if OkCall then tostring(B or (if A then "Done" else "Failed")) else "Request failed", D.Title)
	pcall(Kit.PlaySound, if OkCall and A then "Click" else "Error", 0.6)
	task.spawn(Shared.Refresh)
end

-- Tools' Ctrl+click and other callers: run by id
local function runId(Id: string, Args: any?, _Target: number?)
	for _, D in defs() do if D.Id == Id then run(D, Args) return end end
end

function Shared.Refresh()
	local F = remotes()
	if not F then return end
	local Ok, R = pcall(F.Info.InvokeServer, F.Info)
	if Ok then
		Info = R
		Model.SetLevel(S, (R and R.Level) or 0, (R and R.Sections) or SC.SECTIONS)
	end
	Shared.Redraw()
end

local function refreshStatus()
	local F = remotes()
	if not (F and Open and F:FindFirstChild("Status")) then return end
	local Ok, R = pcall(F.Status.InvokeServer, F.Status)
	if not (Ok and R) then return end
	Status = R
	-- the redraw rebuilds every control: don't pull a TextBox out from under the typist or close an open picker
	local Box = UserInputService:GetFocusedTextBox()
	if U and ((Box and Box:IsDescendantOf(U.Gui)) or U.Board:FindFirstChild("Picker")) then return end
	Shared.Redraw(true)
end

local function bind()
	ContextActionService:BindActionAtPriority("NHConsolePad", function(Name, St, I)
		if St ~= Enum.UserInputState.Begin then return Enum.ContextActionResult.Pass end
		local Sections = (Info and Info.Sections) or SC.SECTIONS
		local List = Sections[S.Side] or {}
		local Cur = table.find(List, S.Section) or 1
		if I.KeyCode == Enum.KeyCode.ButtonL1 then Model.Section(S, math.max(1, Cur - 1), Sections) Shared.Redraw()
		elseif I.KeyCode == Enum.KeyCode.ButtonR1 then Model.Section(S, math.min(#List, Cur + 1), Sections) Shared.Redraw()
		elseif I.KeyCode == Enum.KeyCode.ButtonB then Shared.Toggle(false)
		elseif I.KeyCode == Enum.KeyCode.ButtonY then
			local Sel = GuiService.SelectedObject
			local CardObj = Sel and Sel:FindFirstAncestorWhichIsA("GuiObject")
			while CardObj and not string.match(CardObj.Name, "^Card_") do CardObj = CardObj.Parent :: any end
			if CardObj then Model.ToggleFav(S, string.sub(CardObj.Name, 6)) Shared.Redraw() end
		end
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.ButtonL1, Enum.KeyCode.ButtonR1, Enum.KeyCode.ButtonB, Enum.KeyCode.ButtonY)
end

function Shared.Toggle(On: boolean?)
	local Want = if On == nil then not Open else On
	if Want and S.Level < 1 then Shared.Refresh() if S.Level < 1 then return end end
	Open = Want
	if not U then U = View.Build() end
	U.Gui.Enabled = Open
	Player:SetAttribute("NHMenuOpen", if Open then true else nil)
	if Open then bind() Shared.Refresh() task.spawn(refreshStatus)
	else
		ContextActionService:UnbindAction("NHConsolePad")
		for _, N in { "Palette", "Picker" } do local X = U.Board:FindFirstChild(N) if X then X:Destroy() end end
		local Sel = GuiService.SelectedObject
		if Sel and U and Sel:IsDescendantOf(U.Gui) then GuiService.SelectedObject = nil end
	end
end

function Shared.IsOpen() return Open end

Shared.Handlers = {
	Side = function(Side: string) if table.find(Model.Sides(S.Level), Side) then S.Side = Side S.Section = ((Info and Info.Sections or SC.SECTIONS)[Side] or {})[1] Shared.Redraw() end end;
	Section = function(Name: string) if table.find((Info and Info.Sections or SC.SECTIONS)[S.Side] or {}, Name) then S.Section = Name Shared.Redraw() end end;
	Pick = function(UserId: number) Model.Pick(S, UserId) Inspect = nil S.PhoneRail = false Shared.Redraw() end;
	PhoneRail = function() S.PhoneRail = not S.PhoneRail S.PhoneContext = false Shared.Redraw() end;
	PhoneContext = function() S.PhoneContext = not S.PhoneContext S.PhoneRail = false Shared.Redraw() end;
	Filter = function(Q: string) S.Filter = Q Shared.Redraw() end;
	Run = function(D: any, Vals: any) task.spawn(run, D, Vals) end;
	Fav = function(D: any) Model.ToggleFav(S, D.Id) Shared.Redraw() end;
	Redraw = function() Shared.Redraw() end;
	Close = function() Shared.Toggle(false) end;
	Palette = function()
		if not U then return end
		Palette.Open(U.Board, { Defs = defs();
			OnRun = function(D) task.spawn(run, D, Values[D.Id] or {}) end;
			OnJump = function(D) S.Side = D.Side S.Section = D.Section Shared.Redraw() end })
	end;
}

function Shared.OnStart()
	Tools.Init(runId)
	UserInputService.InputBegan:Connect(function(I, Processed)
		if I.KeyCode == Enum.KeyCode.F3 and not Processed then Shared.Toggle() return end
		if not Open then return end
		local Typing = UserInputService:GetFocusedTextBox() ~= nil
		local Ctrl = UserInputService:IsKeyDown(Enum.KeyCode.LeftControl) or UserInputService:IsKeyDown(Enum.KeyCode.RightControl)
		if I.KeyCode == Enum.KeyCode.K and Ctrl then Shared.Handlers.Palette() return end
		if Typing then
			if I.KeyCode == Enum.KeyCode.Up and Palette.Move then Palette.Move(-1) elseif I.KeyCode == Enum.KeyCode.Down and Palette.Move then Palette.Move(1) end
			return
		end
		if I.KeyCode == Enum.KeyCode.Tab then
			local Sides = Model.Sides(S.Level)
			Shared.Handlers.Side(Sides[(table.find(Sides, S.Side) or 1) % #Sides + 1])
			return
		end
		local N = I.KeyCode.Value - Enum.KeyCode.One.Value + 1
		if N >= 1 and N <= 7 and Model.Section(S, N, (Info and Info.Sections) or SC.SECTIONS) then Shared.Redraw() end
	end)
	-- Esc: Roblox opens its menu and never hands Escape to the game, so close with it
	GuiService.MenuOpened:Connect(function() if Open then Shared.Toggle(false) end end)
	Player:GetAttributeChangedSignal("NHAdminOpen"):Connect(function()
		local V = Player:GetAttribute("NHAdminOpen")
		if V ~= nil then Shared.Toggle(V == true) end
	end)
	task.spawn(function()
		while true do
			task.wait(1)
			if Open then pcall(refreshStatus) end
		end
	end)
	task.spawn(function()
		local Mod = script.Parent:WaitForChild("HudState", 10)
		if not Mod then return end
		local Ok, Hud = pcall(require, Mod)
		if not Ok or typeof(Hud) ~= "table" or not Hud.Probe then return end
		Hud.Probe("Console", function(Cmd: string, A: any)
			if Cmd == "Open" then Shared.Toggle(true) return Open end
			if Cmd == "Close" then Shared.Toggle(false) return Open end
			if Cmd == "Side" then Shared.Handlers.Side(A) return S.Side end
			if Cmd == "Section" then Shared.Handlers.Section(A) return S.Section end
			if Cmd == "Pick" then Shared.Handlers.Pick(A) return S.Selected end
			if Cmd == "Search" then local R = {} for _, D in SC.Search(defs(), A) do table.insert(R, D.Id) end return R end
			if Cmd == "Info" then
				local Ids = {}
				for _, D in Model.Cards(defs(), S.Side, S.Section) do table.insert(Ids, D.Id) end
				local Feed = {}
				for _, E in S.Feed do table.insert(Feed, E.Text) end
				return { Open = Open; Side = S.Side; Section = S.Section; Cards = Ids; Feed = Feed; Level = S.Level; Selected = S.Selected }
			end
			return nil
		end)
	end)
end

return Shared
