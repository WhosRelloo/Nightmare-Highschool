--[[
	CinePrompt (client, 2.25.0). Controllers.CinePrompt: one open prompt at a time during an interactive cut
	(Controllers.Cine opens it, Gui.CineUI draws it). Input is captured above combat (ContextActionService, sunk) so a
	prompt's key never swings a fist. Times are seconds after the prompt opened (CineJudge's time base).
	  Press / Mash / Hold: E, Space, gamepad A, or the big seal on screen (tap / click)
	  Direction: A D W S, the arrow keys, the D-pad, or the seals on screen
	  Choice: 1 2 3, the D-pad (left / up / right), or the buttons on screen
]]

local ContextActionService = game:GetService(`ContextActionService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local Judge = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`CineJudge`))

local Shared = {}
local Local = {}
local ACTION = `NHCinePrompt`
local Open = nil

local PRIMARY = { Enum.KeyCode.E, Enum.KeyCode.Space, Enum.KeyCode.ButtonA }
local DIRS = {
	[Enum.KeyCode.A] = `Left`; [Enum.KeyCode.Left] = `Left`; [Enum.KeyCode.DPadLeft] = `Left`;
	[Enum.KeyCode.D] = `Right`; [Enum.KeyCode.Right] = `Right`; [Enum.KeyCode.DPadRight] = `Right`;
	[Enum.KeyCode.W] = `Up`; [Enum.KeyCode.Up] = `Up`; [Enum.KeyCode.DPadUp] = `Up`;
	[Enum.KeyCode.S] = `Down`; [Enum.KeyCode.Down] = `Down`; [Enum.KeyCode.DPadDown] = `Down`;
}
local CHOICE_KEYS = { [Enum.KeyCode.One] = 1; [Enum.KeyCode.Two] = 2; [Enum.KeyCode.Three] = 3;
	[Enum.KeyCode.DPadLeft] = 1; [Enum.KeyCode.DPadUp] = 2; [Enum.KeyCode.DPadRight] = 3 }

local function UI() return require(script.Parent:WaitForChild(`Gui`):WaitForChild(`CineUI`)) end

function Local.Now(): number return os.clock() - Open.T0 end

function Local.Close()
	local O = Open
	if not O then return end
	Open = nil
	ContextActionService:UnbindAction(ACTION)
	for _, Cn in O.Conns do Cn:Disconnect() end
	local Outcome = Judge.Evaluate(O.P, O.Input)
	pcall(function() UI().PromptHide(Outcome) end)
	task.spawn(O.OnClose, O.Input)
end

function Local.Press(Down: boolean)
	local O = Open
	if not O then return end
	local T = Local.Now()
	local K = O.P.kind
	if K == `Press` then
		if Down then
			table.insert(O.Input.Times, T)
			pcall(function() UI().PromptHit() end)
			Local.Close()
		end
	elseif K == `Mash` then
		if Down then
			table.insert(O.Input.Times, T)
			O.Count += 1
			pcall(function() UI().PromptHit() UI().PromptMeter(math.min(1, O.Count / O.Need)) end)
		end
	elseif K == `Hold` then
		if Down and #O.Input.Times == 0 then
			table.insert(O.Input.Times, T)
			pcall(function() UI().PromptHold(true) end)
		elseif not Down and #O.Input.Times > 0 and not O.Input.Release then
			O.Input.Release = T
			Local.Close()
		end
	end
end

function Local.Pick(Id: string)
	local O = Open
	if not O or O.Input.Pick then return end
	O.Input.Pick = Id
	O.Input.PickAt = Local.Now()
	pcall(function() UI().PromptHit() end)
	Local.Close()
end

function Local.OnAction(_, State: Enum.UserInputState, Obj: InputObject)
	local O = Open
	if not O then return Enum.ContextActionResult.Pass end
	local Down = State == Enum.UserInputState.Begin
	local Up = State == Enum.UserInputState.End
	local K = O.P.kind
	if K == `Direction` then
		local Dir = DIRS[Obj.KeyCode]
		if Down and Dir and table.find(O.P.options or {}, Dir) then Local.Pick(Dir) end
	elseif K == `Choice` then
		local I = CHOICE_KEYS[Obj.KeyCode]
		local Opt = I and O.P.options and O.P.options[I]
		if Down and Opt then Local.Pick(Opt.id) end
	elseif table.find(PRIMARY, Obj.KeyCode) then
		if Down then Local.Press(true) elseif Up then Local.Press(false) end
	end
	return Enum.ContextActionResult.Sink
end

function Shared.Open(P, Opts, OnClose: (any) -> ())
	Shared.Cancel()
	local Touch = Opts.Touch == true
	local Rate = if Touch then (P.touchRate or 5) else (P.rate or 7)
	Open = { P = P; T0 = os.clock(); OnClose = OnClose; Conns = {}; Count = 0; Need = math.max(1, math.ceil(Rate * (P.dur or 2)));
		Input = { Times = {}; Touch = Touch; Reduced = Opts.Reduced == true } }
	local Keys = {}
	if P.kind == `Direction` then for K in DIRS do table.insert(Keys, K) end
	elseif P.kind == `Choice` then for K in CHOICE_KEYS do table.insert(Keys, K) end
	else Keys = table.clone(PRIMARY) end
	ContextActionService:BindActionAtPriority(ACTION, Local.OnAction, false, Enum.ContextActionPriority.High.Value + 50, table.unpack(Keys))
	pcall(function()
		UI().PromptShow(P, { Reduced = Opts.Reduced == true; Touch = Touch; OnTap = Local.Press; OnPick = Local.Pick })
	end)
	local Mine = Open
	task.delay(Judge.Window(P, Open.Input), function() if Open == Mine then Local.Close() end end)
	if RunService:IsStudio() then
		local Hook = ReplicatedStorage:FindFirstChild(`NHCineTestInput`)
		if Hook and Hook:IsA(`BindableEvent`) then
			table.insert(Open.Conns, Hook.Event:Connect(function(M)
				if typeof(M) ~= `table` then return end
				if M.Kind == `Down` then Local.Press(true) elseif M.Kind == `Up` then Local.Press(false)
				elseif M.Kind == `Pick` and typeof(M.Id) == `string` then Local.Pick(M.Id) end
			end))
		end
	end
end

function Shared.Cancel()
	local O = Open
	if not O then return end
	Open = nil
	ContextActionService:UnbindAction(ACTION)
	for _, Cn in O.Conns do Cn:Disconnect() end
	pcall(function() UI().PromptHide(nil) end)
end

function Shared.IsOpen(): boolean return Open ~= nil end

return Shared
