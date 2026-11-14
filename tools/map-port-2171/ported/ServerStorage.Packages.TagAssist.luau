--[[
	TagAssist (server): combat concept 21 (2.15.0). A study-group member nearby can be called in for one assist strike,
	which gives groups a reason to fight together. The assist key (Keybinds "Assist", G) does both halves:
	  * Call: in a fight (you landed a hit in the last 3 s on someone still standing within 30 studs), press it. Every
	    groupmate within 45 studs gets a toast: "<you> needs a hand. Press G!" for 2.5 s.
	  * Answer: a called groupmate presses it in time. They blink beside your target in a gold streak, throw a lunging
	    strike (the running M1), and it lands as an ASSIST: 1.5x their weapon's damage, a 1 s stun, +20 guard, a
	    shove, and +10 Heat for both of you.
	Nobody's character is moved unless they answer. One assist per group every 20 s. A groupmate is never the target.
	The hit goes through DamageLogic like any other (blocks, parries, dodges and the hall monitors all apply).
	Remote: ReplicatedStorage.NHAssist (RemoteEvent; the client sends "Press"). DamageLogic calls NoteHit.
	Off switch: ReplicatedStorage attribute NHAssistOff.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)

local Packets = require(ReplicatedStorage.Remotes.Packets)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)

local TagAssist = {}

TagAssist.IN_FIGHT = 3 -- s since your last landed hit
TagAssist.TARGET_RANGE = 30
TagAssist.CALL_RANGE = 45
TagAssist.WINDOW = 2.5
TagAssist.COOLDOWN = 20
TagAssist.DAMAGE = 1.5
TagAssist.HEAT = 10

local LastHit = setmetatable({}, { __mode = `k` }) :: { [Model]: { Target: Model, At: number } }
local Pending = {} :: { [string]: { Caller: Player, Target: Model, Until: number } }
local ReadyAt = {} :: { [string]: number }

local function On(): boolean
	return ReplicatedStorage:GetAttribute(`NHAssistOff`) ~= true
end

local function notify(P: Player, Title: string, Text: string?, Kind: string?, Duration: number?)
	pcall(function()
		require(ServerScriptService.Services.Features.Notifications).Notify(P, { Title = Title; Text = Text; Kind = Kind or `Info`; Duration = Duration or 2.5 })
	end)
end

local function alive(M: Model?): boolean
	local H = M and M:FindFirstChildWhichIsA(`Humanoid`)
	return H ~= nil and H.Health > 0 and not H:GetAttribute(`Downed`)
end

local function busy(C: Model): boolean
	return StateManager.HasState(C, { `Stun`, `ParryStun`, `Ragdoll`, `Paralyzed`, `Downed`, `Carried`, `Gripped`, `InActivity` })
end

local function rootOf(M: Model?): BasePart?
	local R = M and M:FindFirstChild(`HumanoidRootPart`)
	return if R and R:IsA(`BasePart`) then R else nil
end

-- DamageLogic: Character just landed a hit on Target
function TagAssist.NoteHit(Character: Model?, Target: Model?)
	if Character and Target and Players:GetPlayerFromCharacter(Character) then
		LastHit[Character] = { Target = Target; At = os.clock() }
	end
end

local function groupOf(P: Player): string?
	local G = P:GetAttribute(`NHParty`)
	return if typeof(G) == `string` and G ~= `` then G else nil
end

local function mates(P: Player): { Player }
	local G, Out = groupOf(P), {}
	if not G then return Out end
	for _, O in Players:GetPlayers() do
		if O ~= P and groupOf(O) == G then table.insert(Out, O) end
	end
	return Out
end

local function call(P: Player)
	local C, G = P.Character, groupOf(P)
	if not (C and alive(C)) or busy(C) then return end
	if not G then notify(P, `No study group`, `Form a study group to call in an assist.`, `Info`) return end
	local Now = os.clock()
	if Now < (ReadyAt[G] or 0) then
		notify(P, `Assist not ready`, string.format(`Your group can call again in %d s.`, math.ceil(ReadyAt[G] - Now)), `Warning`, 2)
		return
	end
	local L = LastHit[C]
	local Target = L and L.Target
	local TR, MR = rootOf(Target), rootOf(C)
	if not (L and Now - L.At <= TagAssist.IN_FIGHT and alive(Target) and TR and MR and (TR.Position - MR.Position).Magnitude <= TagAssist.TARGET_RANGE) then
		notify(P, `Not in a fight`, `Land a hit first, then call your group in.`, `Info`, 2)
		return
	end
	local TP = Players:GetPlayerFromCharacter(Target)
	if TP and groupOf(TP) == G then return end -- never against your own group
	local Called = {}
	for _, O in mates(P) do
		local OR = rootOf(O.Character)
		if OR and alive(O.Character) and (OR.Position - MR.Position).Magnitude <= TagAssist.CALL_RANGE then
			table.insert(Called, O)
		end
	end
	if #Called == 0 then notify(P, `No one close enough`, `Your study group is too far away.`, `Info`, 2) return end
	Pending[G] = { Caller = P; Target = Target; Until = Now + TagAssist.WINDOW }
	notify(P, `Assist called`, `Calling your study group...`, `Info`, TagAssist.WINDOW)
	for _, O in Called do
		notify(O, `{P.DisplayName} needs a hand!`, `Press G to assist.`, `Warning`, TagAssist.WINDOW)
	end
end

local function answer(P: Player, Pend)
	local C, Target, G = P.Character, Pend.Target, groupOf(P)
	local MR, TR = rootOf(C), rootOf(Target)
	if not (C and G and MR and TR and alive(C) and alive(Target)) or busy(C) then return end
	if (TR.Position - MR.Position).Magnitude > TagAssist.CALL_RANGE + 10 then notify(P, `Too far`, nil, `Info`, 1.5) return end
	Pending[G] = nil
	ReadyAt[G] = os.clock() + TagAssist.COOLDOWN
	local From = MR.Position
	-- blink to the target's side (the side you're coming from), facing it
	local Dir = (From - TR.Position) * Vector3.new(1, 0, 1)
	Dir = if Dir.Magnitude > 0.1 then Dir.Unit else -TR.CFrame.LookVector
	local At = TR.Position + Dir * 3.2
	At = Vector3.new(At.X, MR.Position.Y + (TR.Position.Y - MR.Position.Y), At.Z)
	C:PivotTo(CFrame.lookAt(At, Vector3.new(TR.Position.X, At.Y, TR.Position.Z)) * MR.CFrame:ToObjectSpace(C:GetPivot()))
	MR.AssemblyLinearVelocity = Vector3.zero
	Packets.Replicate:Fire(`Misc`, `Tag Assist`, { User = C; From = From; To = At; Target = Target })
	-- the lunging strike (the weapon's running M1), then the hit
	pcall(function()
		local Weapons = require(ReplicatedStorage.Config.Weapons)
		local W = Weapons[C:GetAttribute(`Weapon`) or `Fist`] or Weapons.Fist
		local Anim = W and W.Animations and (W.Animations.RunningM1 or (W.Animations.M1 and W.Animations.M1[4]))
		if Anim then
			local TrackService = require(ReplicatedStorage.Packages.TrackService)
			local T = TrackService.Play(Anim, C, `Attack`, 0.05)
			T:SetPriority(Enum.AnimationPriority.Action4)
		end
	end)
	task.wait(0.18)
	if not (alive(Target) and alive(C)) then return end
	local DamageLogic = require(ServerStorage.Packages.DamageLogic)
	local Weapons = require(ReplicatedStorage.Config.Weapons)
	local W = Weapons[C:GetAttribute(`Weapon`) or `Fist`] or Weapons.Fist
	local DamageData = {
		Character = C; Target = Target;
		Damage = (W and W.Damage or 3) * TagAssist.DAMAGE; Posture = 20;
		Stun = 1; StunLocked = false; States = { Stun = 1 };
		LinearVelocity = { Velocity = 30; Duration = 0.2 };
		React = `1`; Tag = `ASSIST`; Heavy = true;
	}
	if DamageLogic.Processed(DamageData) then DamageLogic.TakeAction(DamageData) end
	local Heat = require(ServerStorage.Packages.Heat)
	pcall(Heat.Add, C, TagAssist.HEAT)
	if Pend.Caller.Character then pcall(Heat.Add, Pend.Caller.Character, TagAssist.HEAT) end
	notify(Pend.Caller, `{P.DisplayName} jumped in!`, nil, `Good`, 2)
end

function TagAssist.Press(P: Player)
	if not On() then return end
	local G = groupOf(P)
	local Pend = G and Pending[G]
	if Pend and os.clock() <= Pend.Until and Pend.Caller ~= P then
		answer(P, Pend)
	else
		call(P)
	end
end

-- the remote, made once on first require (DamageLogic requires this at server start)
do
	local R = ReplicatedStorage:FindFirstChild(`NHAssist`) or Instance.new(`RemoteEvent`)
	R.Name = `NHAssist`
	R.Parent = ReplicatedStorage
	local Last = setmetatable({}, { __mode = `k` })
	R.OnServerEvent:Connect(function(P: Player, Kind: any)
		if Kind ~= `Press` then return end
		if os.clock() - (Last[P] or 0) < 0.4 then return end
		Last[P] = os.clock()
		task.spawn(TagAssist.Press, P)
	end)
	Players.PlayerRemoving:Connect(function(P)
		for G, Pend in Pending do if Pend.Caller == P then Pending[G] = nil end end
	end)
end

return TagAssist
