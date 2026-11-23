--[[
	Infirmary (server). Services.Features.Infirmary  (phase6-strafes)
	Spec: docs/superpowers/specs/2026-11-22-strafes-npc-gestures-design.md §6.4.

	Nurse Agatha Thorne treats players. Deliberately MINIMAL and PLUGGABLE: an in-depth injury system (custom injury
	models per body type) is coming as its own design and will replace the rules. Nothing here makes injury states,
	injury visuals or injury models.
	  Infirmary.Treat(Player) -> (ok, reason?)   the ONLY entry point (the Nurse's prompt and her dialogue call it)
	      the Nurse must be within Config.Gestures.Treat.Range; Care.CanTreat says yes or why not; then the interaction:
	      both face each other, the player is planted and plays the Kit's own FirstAid clip, the Nurse plays Inspect then
	      ReachDown (StudentBrain.Gestures, Force), for Treat.Seconds. It cancels on a health drop, being downed, a combat
	      tag starting, or walking more than Treat.CancelRange away ("Hold still."). On completion: Care.Apply(Player).
	  Infirmary.Care                 the rules (child ModuleScript Care: CanTreat / Apply / Cost)
	  Infirmary.SetCare(Module)      the injury system swaps the rules in here
	  Infirmary.AttachPrompt(Model)  Social.Npcs calls it when the Nurse spawns: a "Get patched up" prompt
	Health today (read 2026-11-22): Progression regenerates 2 % of MaxHealth a second out of combat; Features.Kit's
	bandage heals over time and sets NHBandagedUntil / clears NHWounded. Care's default Apply matches the Kit's flags.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Config = require(ReplicatedStorage.Config.Gestures)
local KitConfig = require(ReplicatedStorage.Config.Kit)

local Infirmary = {}
Infirmary.Care = require(script:WaitForChild(`Care`))
local Busy = {} :: { [Player]: boolean }

local function notify(P: Player, Title: string, Text: string?, Kind: string?)
	pcall(function()
		require(ServerScriptService.Services.Features.Notifications).Notify(P, { Title = Title; Text = Text; Kind = Kind or `Info`; Duration = 4 })
	end)
end

local function gestures()
	return require(ServerScriptService.Services.AI.StudentBrain.Gestures)
end

function Infirmary.SetCare(Module: any)
	assert(type(Module) == `table` and Module.CanTreat and Module.Apply, `Care needs CanTreat and Apply`)
	Infirmary.Care = Module
end

function Infirmary.Nurse(): Model?
	local Ok, M = pcall(function() return require(ServerScriptService.Services.Social.Npcs).Get(`Nurse`) end)
	return if Ok then M else nil
end

local function face(Root: BasePart, At: Vector3)
	local To = Vector3.new(At.X, Root.Position.Y, At.Z)
	if (To - Root.Position).Magnitude > 0.2 then Root.CFrame = CFrame.lookAt(Root.Position, To) end
end

function Infirmary.Treat(P: Player): (boolean, string?)
	local T = Config.Treat
	if Busy[P] then return false, `busy` end
	local Char = P.Character
	local H = Char and Char:FindFirstChildOfClass(`Humanoid`)
	local Root = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Nurse = Infirmary.Nurse()
	local NRoot = Nurse and Nurse:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not (H and Root and NRoot) then return false, `no nurse` end
	if (NRoot.Position - Root.Position).Magnitude > T.Range + 0.5 then return false, `too far` end
	local Ok, Why = Infirmary.Care.CanTreat(P)
	if not Ok then
		if Why then notify(P, Why) end
		return false, Why
	end
	Busy[P] = true
	face(Root, NRoot.Position)
	face(NRoot, Root.Position)
	Char:SetAttribute(`NHKitSlow`, 0.01) -- planted (CombatSpeed applies NHKitSlow)
	local Track
	local Id = KitConfig.Anims and KitConfig.Anims[T.PlayerClip]
	if typeof(Id) == `number` and Id > 0 then
		local Animator = H:FindFirstChildOfClass(`Animator`)
		local A = Instance.new(`Animation`)
		A.AnimationId = `rbxassetid://{Id}`
		local Okl, Tr = pcall(function() return Animator:LoadAnimation(A) end)
		if Okl then Track = Tr Tr.Priority = Enum.AnimationPriority.Action Tr:Play(0.2) end
	end
	local G = gestures()
	local NS = G.Record(Nurse)
	G.Play(NS, `Inspect`, { Force = true; Seconds = T.Seconds / 2 })
	task.delay(T.Seconds / 2, function() if Busy[P] then G.Play(NS, `ReachDown`, { Force = true; Seconds = T.Seconds / 2 }) end end)
	local Start, Hp, Cancelled = os.clock(), H.Health, nil
	local Tag0 = P:GetAttribute(`CombatTagUntil`) or 0
	while os.clock() - Start < T.Seconds do
		task.wait(0.1)
		if not (H.Parent and P.Parent and NRoot.Parent) then Cancelled = `gone` break end
		if H.Health < Hp - 0.01 then Cancelled = `hit` break end
		if Char:GetAttribute(`DownedUntil`) or H:GetAttribute(`Downed`) then Cancelled = `downed` break end
		if (P:GetAttribute(`CombatTagUntil`) or 0) > Tag0 + 0.01 then Cancelled = `fight` break end
		if (NRoot.Position - Root.Position).Magnitude > T.CancelRange + T.Range then Cancelled = `walked` break end
		Hp = math.max(Hp, H.Health)
	end
	if Track then Track:Stop(0.25) end
	G.Stop(NS, 0.3)
	if Char.Parent then Char:SetAttribute(`NHKitSlow`, nil) end
	Busy[P] = nil
	if Cancelled then
		if P.Parent and Cancelled ~= `gone` then notify(P, `Hold still.`, `Nurse Agatha Thorne couldn't finish.`) end
		return false, Cancelled
	end
	Infirmary.Care.Apply(P)
	notify(P, `Patched up`, `"There. Try to keep it that way."`, `Good`)
	return true
end

function Infirmary.AttachPrompt(Model: Model)
	local Root = Model:FindFirstChild(`HumanoidRootPart`)
	if not Root or Root:FindFirstChild(`TreatPrompt`) then return end
	local Pr = Instance.new(`ProximityPrompt`)
	Pr.Name = `TreatPrompt`
	Pr.ActionText = `Get patched up`
	Pr.ObjectText = `Nurse Agatha Thorne`
	Pr.HoldDuration = 0.5
	Pr.MaxActivationDistance = Config.Treat.Range
	Pr.RequiresLineOfSight = false
	Pr.KeyboardKeyCode = Enum.KeyCode.F
	Pr.UIOffset = Vector2.new(0, 60) -- below the Talk prompt
	Pr.Parent = Root
	Pr.Triggered:Connect(function(P) task.spawn(Infirmary.Treat, P) end)
end

-- Studio probe commands (reached through ServerStorage.NHGestureProbe)
function Infirmary.Probe(Cmd: string, A: any, B: any, C: any)
	local P = (typeof(A) == `string` and Players:FindFirstChild(A)) or Players:GetPlayers()[1]
	if Cmd == `Treat` then
		local Ok, Why = Infirmary.Treat(P)
		local H = P.Character and P.Character:FindFirstChildOfClass(`Humanoid`)
		return { Ok = Ok; Why = Why; Health = H and H.Health; Max = H and H.MaxHealth; Wounded = P.Character and P.Character:GetAttribute(`NHWounded`) }
	elseif Cmd == `ResetCooldown` then
		if Infirmary.Care.Reset then Infirmary.Care.Reset(P) end
		return { Ok = true }
	elseif Cmd == `SetHealth` then
		local H = P.Character and P.Character:FindFirstChildOfClass(`Humanoid`)
		if H then H.Health = tonumber(B) or H.Health end
		return { Health = H and H.Health }
	elseif Cmd == `StubCare` then
		local Old = Infirmary.Care
		Infirmary.SetCare({ CanTreat = function() return true end; Apply = function(Pl)
			local H = Pl.Character and Pl.Character:FindFirstChildOfClass(`Humanoid`)
			if H then H.Health = 77 end
		end; Cost = function() return 0 end; Reset = function() end; Old = Old })
		return { Ok = true }
	elseif Cmd == `RestoreCare` then
		if Infirmary.Care.Old then Infirmary.Care = Infirmary.Care.Old end
		return { Ok = true }
	elseif Cmd == `NurseAt` then
		local N = Infirmary.Nurse()
		local R = N and N:FindFirstChild(`HumanoidRootPart`)
		return { Pos = R and R.Position; Prompt = R and R:FindFirstChild(`TreatPrompt`) ~= nil }
	end
	return { Error = `unknown command {Cmd}` }
end

function Infirmary.OnStart()
	Players.PlayerRemoving:Connect(function(P) Busy[P] = nil end)
end

return Infirmary
