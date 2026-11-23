--[[
	HudState (client). Controllers.Gui.HudState  (2.38, Quiet Corners QC1)
	Spec: docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md §2. Rules: ReplicatedStorage.Functions.QuietCorners.

	One HUD state: Active, Calm (6 s with no movement), Combat (a hit taken, a Posture change, CombatTagUntil; it ends 4 s after
	the last), Cut (PlayerGui.NHCineUI is on), Dialogue (InDialogue), Lesson (PlayerGui.Lesson), Menu (NHMenuOpen: the book,
	the Evidence Wall). Published as the Player attribute NHHudState. HudMode (Settings) arrives as NHHudMode.
	Clusters are CanvasGroups adopted from their controllers (Adopt): TopLeft (NHTopBar), Compass (NHCompass), Vitals
	(KitHud.Bottom). Only their GroupTransparency is tweened. The Bell Tower is never adopted (plan ruling 2).
	In a Cut, NHCineUI fades the same groups and puts them back; HudState waits and comes back at Calm (spec §2).
	Waking: Wake(Cluster) (a change in it) or hovering it = full for 4 s; Tab / View = every cluster; health under 25% keeps
	Vitals awake. Studio only: PlayerGui.NHQuietProbe (BindableFunction) for tools/quietcorners/checks.
	API: Get(), Changed, Adopt(Gui, Cluster, Names?, Edge, Height), Wake(Cluster?), Poke(Kind), SlipsQueued(), Probe(Name, Fn)
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local QC = require(ReplicatedStorage:WaitForChild("Functions"):WaitForChild("QuietCorners"))

local Player = Players.LocalPlayer
local Local = {}
local Shared = {}
Shared.Changed = Instance.new("BindableEvent")

local Clusters = {} :: { [string]: { Group: CanvasGroup, Target: number?, AwakeUntil: number } }
local State = "Active"
local LastActive = os.clock()
local CombatUntil = 0
local Forced: string? = nil
local Probes = {} :: { [string]: (...any) -> any }

function Local.Reduced(): boolean return Player:GetAttribute("NHReducedMotion") == true end

function Local.LowHealth(): boolean
	local C = Player.Character
	local H = C and C:FindFirstChildOfClass("Humanoid")
	return H ~= nil and H.MaxHealth > 0 and H.Health / H.MaxHealth < 0.25
end

function Local.Inputs()
	local PG = Player:FindFirstChild("PlayerGui")
	local Cine = PG and PG:FindFirstChild("NHCineUI")
	return {
		Cut = Cine ~= nil and (Cine :: any).Enabled == true;
		Menu = Player:GetAttribute("NHMenuOpen") == true;
		Dialogue = Player:GetAttribute("InDialogue") == true;
		Lesson = PG ~= nil and PG:FindFirstChild("Lesson") ~= nil;
		Now = os.clock(); CombatUntil = CombatUntil; LastActive = LastActive;
	}
end

function Local.Apply(Instant: boolean?)
	local Now = os.clock()
	local New = Forced or QC.State(Local.Inputs())
	if New ~= State then
		local Was = State
		State = New
		Player:SetAttribute("NHHudState", State)
		if Was == "Cut" then LastActive = -math.huge end -- back to calm, never a flash to full
		Shared.Changed:Fire(State)
	end
	if State == "Cut" then return end -- NHCineUI owns the fade
	local Mode = QC.Mode(Player:GetAttribute("NHHudMode"))
	local Low = Local.LowHealth()
	for Name, C in Clusters do
		if not C.Group.Parent then Clusters[Name] = nil continue end
		local T = QC.HudTarget(State, Mode, Name, C.AwakeUntil > Now or (Name == "Vitals" and Low))
		if T ~= C.Target then
			C.Target = T
			local Secs = if Instant then 0 elseif Local.Reduced() then 0.2 elseif State == "Calm" then 0.6 else 0.25
			TweenService:Create(C.Group, TweenInfo.new(Secs, Enum.EasingStyle.Sine), { GroupTransparency = T }):Play()
		end
	end
end

-- wrap a cluster's top-level pieces in one CanvasGroup, pinned to the top or bottom edge, full width, Height design px tall
function Shared.Adopt(Gui: ScreenGui, Cluster: string, Names: { string }?, Edge: string, Height: number): CanvasGroup
	local G = Gui:FindFirstChild("QcFade") :: CanvasGroup?
	if not G then
		local New = Instance.new("CanvasGroup")
		New.Name = "QcFade"
		New.BackgroundTransparency = 1
		New.AnchorPoint = Vector2.new(0, if Edge == "Bottom" then 1 else 0)
		New.Position = UDim2.fromScale(0, if Edge == "Bottom" then 1 else 0)
		New.Size = UDim2.new(1, 0, 0, Height)
		New.Parent = Gui
		G = New
	end
	local Group = G :: CanvasGroup
	for _, Child in Gui:GetChildren() do
		if Child ~= Group and Child:IsA("GuiObject") and (Names == nil or table.find(Names, Child.Name) ~= nil) then Child.Parent = Group end
	end
	Clusters[Cluster] = { Group = Group; Target = nil; AwakeUntil = 0 }
	Group.MouseEnter:Connect(function() Shared.Wake(Cluster) end)
	Local.Apply(true)
	return Group
end

function Shared.Wake(Cluster: string?)
	local Until = os.clock() + QC.WAKE_FOR
	for Name, C in Clusters do if Cluster == nil or Name == Cluster then C.AwakeUntil = Until end end
	Local.Apply()
end

function Shared.Poke(Kind: string)
	if Kind == "Hit" then CombatUntil = os.clock() + QC.COMBAT_FOR end
	Local.Apply()
end

function Shared.Get(): string return State end
function Shared.SlipsQueued(): boolean return QC.SlipsQueued(State) end
function Shared.Probe(Name: string, Fn: (...any) -> any) Probes[Name] = Fn end

function Local.BindCharacter(C: Model)
	local H = C:WaitForChild("Humanoid", 10) :: Humanoid?
	if not H then return end
	local Last = H.Health
	H.HealthChanged:Connect(function(V)
		if V < Last - 0.5 then Shared.Poke("Hit") end
		Last = V
		Local.Apply()
	end)
	for _, I in { C, H } do I:GetAttributeChangedSignal("Posture"):Connect(function() Shared.Poke("Hit") end) end
end

Probes.Get = function()
	local T, Gs = {}, {}
	for N, C in Clusters do T[N] = C.Target Gs[N] = C.Group:GetFullName() end
	return { State = State; Mode = QC.Mode(Player:GetAttribute("NHHudMode")); Targets = T; Groups = Gs }
end
Probes.Force = function(S: string?) Forced = S Local.Apply() return State end
Probes.Poke = function(K: string) Shared.Poke(K) return State end
Probes.Wake = function(C: string?) Shared.Wake(C) return true end
Probes.Idle = function() LastActive = -math.huge for _, C in Clusters do C.AwakeUntil = 0 end Local.Apply() return State end

function Shared.OnStart()
	Player:SetAttribute("NHHudState", State)
	if Player.Character then task.spawn(Local.BindCharacter, Player.Character) end
	Player.CharacterAdded:Connect(Local.BindCharacter)
	Player:GetAttributeChangedSignal("CombatTagUntil"):Connect(function() Shared.Poke("Hit") end)
	for _, A in { "NHHudMode", "InDialogue", "NHMenuOpen" } do Player:GetAttributeChangedSignal(A):Connect(function() Local.Apply() end) end
	UserInputService.InputBegan:Connect(function(Input)
		if Input.KeyCode == Enum.KeyCode.Tab or Input.KeyCode == Enum.KeyCode.ButtonSelect then Shared.Wake(nil) end
	end)
	local Acc = 0
	RunService.Heartbeat:Connect(function(Dt)
		Acc += Dt
		if Acc < 0.1 then return end
		Acc = 0
		local C = Player.Character
		local H = C and C:FindFirstChildOfClass("Humanoid")
		if H and H.MoveDirection.Magnitude > 0.1 and State ~= "Cut" then LastActive = os.clock() end
		Local.Apply()
	end)
	if RunService:IsStudio() then
		local PG = Player:WaitForChild("PlayerGui")
		local B = PG:FindFirstChild("NHQuietProbe") or Instance.new("BindableFunction")
		B.Name = "NHQuietProbe"
		B.OnInvoke = function(Cmd, ...)
			local Fn = Probes[Cmd]
			if not Fn then return { Error = "unknown command " .. tostring(Cmd) } end
			local Ok, R = pcall(Fn, ...)
			return if Ok then R else { Error = tostring(R) }
		end
		B.Parent = PG
	end
end

return Shared
