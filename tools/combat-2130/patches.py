H = "ServerStorage.Packages.HitBox"
D = "ServerStorage.Packages.DamageLogic"
A = "ServerScriptService.Services.Player.ActionManager"
T = "ServerScriptService.Services.Studio.TestBridge"

EDITS = [
    # ---------------- HitBox: lag compensation (concept 13) + the log (14); the dead 0.2 s prediction goes
    (H, """local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
""", """local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local LagComp = require(script.Parent.LagComp) -- (2.13.0) lag-compensated hits
local CombatLog = require(script.Parent.CombatLog) -- (2.13.0) Studio combat log
"""),
    (H, """	Prediction: boolean;
	CFrameDotCheck: boolean;
""", """	Prediction: boolean;
	CFrameDotCheck: boolean;
	Rewind: number?; -- (2.13.0) seconds to also test targets back in time; nil = LagComp.Rewind(the attacker)
"""),
    (H, """function Shared.Go(self: HitBoxProperties) -- s

	local PredictedCFrame = Local.Predict(.2, self.CFrame)

	local HitBoxShape = Local.GetShape(self.Shape)
	local BaseCFrame = PredictedCFrame or Local.GetBaseCFrame(self.CFrame)
""", """-- (2.13.0) the attacking character (the hitbox follows its root part), or nil
function Local.Attacker(self: HitBoxProperties): Model?
	local P = self.CFrame
	if typeof(P) == `Instance` and P.Parent and P.Parent:IsA(`Model`) then return P.Parent end
	return nil
end

-- (2.13.0, combat concept 13) how far back this hitbox also tests targets
function Local.RewindOf(self: HitBoxProperties): number
	if self.Rewind then return math.max(0, self.Rewind) end
	return LagComp.Rewind(Local.Attacker(self), false)
end

function Shared.Go(self: HitBoxProperties) -- s

	-- (2.13.0) the old 0.2 s "prediction" never ran (Local.Predict checked typeof(Part) == "BasePart", but typeof gives
	-- "Instance"), so hits were always judged at the attacker's current CFrame. That stays; lag compensation now
	-- rewinds the targets instead (LagComp).
	local HitBoxShape = Local.GetShape(self.Shape)
	local BaseCFrame = Local.GetBaseCFrame(self.CFrame)
"""),
    (H, """	local HitList = Local.CastShape(self.Shape, BaseCFrame * self.Offset, self.Size, self.Params)
	if not HitList then return self end

	for _, A in pairs(HitList) do""", """	local HitList = Local.CastShape(self.Shape, BaseCFrame * self.Offset, self.Size, self.Params)
	if not HitList then return self end
	local Before = self.HitList and #self.HitList or 0

	for _, A in pairs(HitList) do"""),
    (H, """			self.Touched:Fire(A, Humanoid)
			self:Destroy()
			break
		end

	end

	return self
end
""", """			self.Touched:Fire(A, Humanoid)
			self:Destroy()
			break
		end

	end

	-- (2.13.0, combat concept 13) also test everyone where they were on the attacker's screen
	if self.HitList and self.Touched then
		local Now = #self.HitList - Before
		local Rewind = Local.RewindOf(self)
		local Rewound = 0
		if Rewind > 0 and self.Shape == Enum.PartType.Block then
			local Skip = {}
			for _, Hum in self.HitList do if Hum and Hum.Parent then Skip[Hum.Parent] = true end end
			for _, Hit in LagComp.HitsAgo(BaseCFrame * self.Offset, self.Size, Rewind, self.Params, Skip) do
				if not (self.HitList and self.Touched) then break end
				if self.HitBoxDetection == `HitOnce` then
					self.Touched:Fire(Hit.Root, Hit.Humanoid)
					Rewound += 1
					self:Destroy()
					break
				end
				if not table.find(self.HitList, Hit.Humanoid) then
					table.insert(self.HitList, Hit.Humanoid)
					Rewound += 1
					self.Touched:Fire(Hit.Root, Hit.Humanoid)
				end
			end
		end
		if CombatLog.On() then
			CombatLog.Log(Local.Attacker(self), `hitbox`, string.format(`%d hit now, %d only on the attacker's screen (rewind %d ms)`, Now, Rewound, math.floor(Rewind * 1000 + 0.5)))
		end
	end

	return self
end
"""),
    (H, """function Shared.GetCast(self: HitBoxProperties): { Model }?
	local PredictedCFrame = Local.Predict(.2, self.CFrame)

	local HitBoxShape = Local.GetShape(self.Shape)
	local BaseCFrame = PredictedCFrame or Local.GetBaseCFrame(self.CFrame)
""", """function Shared.GetCast(self: HitBoxProperties): { Model }?
	local HitBoxShape = Local.GetShape(self.Shape)
	local BaseCFrame = Local.GetBaseCFrame(self.CFrame) -- (2.13.0) no dead prediction; targets are rewound below
"""),
    (H, """	local HitList = Local.CastShape(self.Shape, BaseCFrame * self.Offset, self.Size, self.Params)
	if not HitList then return end

	for Index, A in pairs(HitList) do""", """	local HitList = Local.CastShape(self.Shape, BaseCFrame * self.Offset, self.Size, self.Params)
	if not HitList then return end
	-- (2.13.0, combat concept 13) add the root of anyone who was inside it on the attacker's screen
	local Rewind = Local.RewindOf(self)
	if Rewind > 0 and self.Shape == Enum.PartType.Block then
		local Skip = {}
		for _, A in HitList do local M = A and A:FindFirstAncestorOfClass(`Model`) if M then Skip[M] = true end end
		for _, Hit in LagComp.HitsAgo(BaseCFrame * self.Offset, self.Size, Rewind, self.Params, Skip) do
			table.insert(HitList, Hit.Root)
		end
	end

	for Index, A in pairs(HitList) do"""),

    # ---------------- DamageLogic: what each hit came to (concept 14)
    (D, """
return Shared""", """
-- (2.13.0, combat concept 14) the Studio combat log: what each hit came to. Wraps the two entry points; nothing
-- changes when the log is off (outside Studio it's always off).
do
	local CombatLog = require(script.Parent.CombatLog)
	local RawProcessed, RawTakeAction = Shared.Processed, Shared.TakeAction
	Shared.Processed = function(DamageData: DamageData): boolean?
		if not CombatLog.On() then return RawProcessed(DamageData) end
		local Target = DamageData and DamageData.Target
		local Why = `out of reach / can't be hit`
		pcall(function()
			local Tags = TagService:ReturnTags(Target)
			if table.find(Tags, `IFrames`) then Why = `dodged (i-frames)`
			elseif table.find(Tags, `Parry`) or table.find(Tags, `AutoParry`) then Why = `parried`
			elseif ActionManager.isActionPlaying(Target, `Block`) then Why = `blocked`
			end
		end)
		local Hum = Target and Target:FindFirstChildWhichIsA(`Humanoid`)
		local P0 = Hum and Hum:GetAttribute(`Posture`) or 0
		local Result = RawProcessed(DamageData)
		local P1 = Hum and Hum:GetAttribute(`Posture`) or 0
		CombatLog.Log(DamageData and DamageData.Character, `hit`, string.format(`-> %s: %s (%.1f dmg%s, posture %.0f -> %.0f)`,
			Target and Target.Name or `?`, if Result then `LANDS` else `stopped, ` .. Why, DamageData and DamageData.Damage or 0,
			if DamageData and DamageData.Tag then `, ` .. DamageData.Tag else ``, P0, P1))
		return Result
	end
	Shared.TakeAction = function(DamageData: DamageData)
		if not CombatLog.On() then return RawTakeAction(DamageData) end
		local Target = DamageData and DamageData.Target
		local W = Target and Target:GetAttribute(`NHWindupUntil`)
		local Counter = typeof(W) == `number` and workspace:GetServerTimeNow() < W and StateManager.HasState(Target, `Attacking`)
		local Hum = Target and Target:FindFirstChildWhichIsA(`Humanoid`)
		local H0 = Hum and Hum.Health or 0
		local Result = RawTakeAction(DamageData)
		CombatLog.Log(DamageData and DamageData.Character, `damage`, string.format(`-> %s: health %.1f -> %.1f%s%s`,
			Target and Target.Name or `?`, H0, Hum and Hum.Health or 0, if Counter then `, COUNTER-HIT` else ``,
			if DamageData and DamageData.Heavy then `, heavy` else ``))
		return Result
	end
end

return Shared"""),

    # ---------------- ActionManager: inputs and actions (concept 14)
    (A, """local Packets = require(ReplicatedStorage.Remotes.Packets)
""", """local Packets = require(ReplicatedStorage.Remotes.Packets)
local CombatLog = require(game:GetService(`ServerStorage`).Packages.CombatLog) -- (2.13.0) Studio combat log
"""),
    (A, """		local Aerial = Flags % 2 == 1
		local Press = (Flags // 2) % 2 == 1
		local Character = Player.Character
		if not Character then return end
""", """		local Aerial = Flags % 2 == 1
		local Press = (Flags // 2) % 2 == 1
		local Character = Player.Character
		if not Character then return end
		if CombatLog.On() and Press then CombatLog.Log(Character, `in M1`, string.format(`press%s, ping %d ms`, if Aerial then ` (air)` else ``, math.floor(Player:GetNetworkPing() * 1000))) end
"""),
    (A, """		local Aerial = Flags % 2 == 1
		local HeldBy = Player.Character and Manager.new(Player.Character)""", """		local Aerial = Flags % 2 == 1
		if CombatLog.On() and Player.Character and Flags >= 2 then CombatLog.Log(Player.Character, `in M2`, if (Flags // 4) % 2 == 1 then `let go` else `press`) end
		local HeldBy = Player.Character and Manager.new(Player.Character)"""),
    (A, """	if not self:CanActivate(Action, ...) then
		return
	end

	local Activate = Module.Activate :: (self: ActionManager, ...any) -> ()
	if not Activate then return end
""", """	if not self:CanActivate(Action, ...) then
		if CombatLog.On() and (Module.Class == `Attack` or Action == `Block` or Action == `Dodge`) then
			CombatLog.Log(self.Character, `refused`, Action .. (if self.Action then ` (busy: ` .. tostring(self.Action) .. `)` else ``))
		end
		return
	end

	local Activate = Module.Activate :: (self: ActionManager, ...any) -> ()
	if not Activate then return end
	if CombatLog.On() and (Module.Class == `Attack` or Action == `Block` or Action == `Dodge`) then
		CombatLog.Log(self.Character, `start`, Action .. (if self.Action and self.Action ~= Action then ` (cancels ` .. tostring(self.Action) .. `)` else ``))
	end
"""),

    # ---------------- TestBridge: read the log
    (T, """function Commands.SetTime(TimeText: string, Day: number?)""", """---| Combat log (2.13.0, combat concept 14) |---

function Commands.CombatLog(Count: number?)
	return require(ServerStorage.Packages.CombatLog).Get(Count)
end

function Commands.CombatLogClear()
	require(ServerStorage.Packages.CombatLog).Clear()
	return true
end

function Commands.SetTime(TimeText: string, Day: number?)"""),
]
S = "ServerScriptService.Services.Player.ActionManager.Combat.M1"
C = "StarterPlayer.StarterPlayerScripts.Controllers.Character.InputController.Combat.M1"
A = "ServerScriptService.Services.Player.ActionManager"

EDITS = [
    # ---------------- client: predict the swing on the press (concept 12)
    (C, """	-- (combat audit) the packet is a flags byte: 1 = aerial, 2 = a new press (the server buffers only presses;
	-- the hold-repeats below send 0)
""", """	-- (combat audit) the packet is a flags byte: 1 = aerial, 2 = a new press (the server buffers only presses;
	-- the hold-repeats below send 0). (2.13.0, combat concept 12) + index * 8: the hit of the string this client
	-- already started playing (script.Predict); 0 = not predicted.
"""),
    (C, """		UnPackets.M1:Fire(if Pressed then 0 else 2)
		Pressed = true""", """		local Flags = if Pressed then 0 else 2
		if not Pressed and not InAir then
			local Ok, Index = pcall(require(script.Predict).Try, Character, Humanoid)
			if Ok and Index then Flags += Index * 8 end
		end
		UnPackets.M1:Fire(Flags)
		Pressed = true"""),

    # ---------------- server: read the guess
    (A, """	UnPackets.M1.OnServerEvent:Connect(function(Player: Player, Flags: number) -- (combat audit) 1 = aerial, 2 = a new press
		if typeof(Flags) ~= `number` then return end
		local Aerial = Flags % 2 == 1
		local Press = (Flags // 2) % 2 == 1""", """	UnPackets.M1.OnServerEvent:Connect(function(Player: Player, Flags: number) -- (combat audit) 1 = aerial, 2 = a new press
		if typeof(Flags) ~= `number` then return end
		local Aerial = Flags % 2 == 1
		local Press = (Flags // 2) % 2 == 1
		local Predicted = (Flags // 8) % 8 -- (2.13.0, combat concept 12) the hit the client already started, 0 = none"""),
    (A, """		if CombatLog.On() and Press then CombatLog.Log(Character, `in M1`, string.format(`press%s, ping %d ms`, if Aerial then ` (air)` else ``, math.floor(Player:GetNetworkPing() * 1000))) end

		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		local Paramaters = { 
			Aerial = Local.ServerAerial(Character, Humanoid, Aerial);
			Running = Humanoid:GetAttribute(`Sprint`) :: boolean
		}
""", """		if CombatLog.On() and Press then CombatLog.Log(Character, `in M1`, string.format(`press%s%s, ping %d ms`, if Aerial then ` (air)` else ``, if Predicted > 0 then `, client started hit ` .. Predicted else ``, math.floor(Player:GetNetworkPing() * 1000))) end

		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		local Paramaters = { 
			Aerial = Local.ServerAerial(Character, Humanoid, Aerial);
			Running = Humanoid:GetAttribute(`Sprint`) :: boolean;
			Predicted = if Press and Predicted > 0 then Predicted else nil; -- (2.13.0) Combat.M1
		}
"""),

    # ---------------- server M1: the predicted swing plays its timing copy almost invisibly; the hit rewinds further
    (S, """local HitBoxService = require(ServerStorage.Packages.HitBox)
""", """local HitBoxService = require(ServerStorage.Packages.HitBox)
local LagComp = require(ServerStorage.Packages.LagComp) -- (2.13.0) lag-compensated hits
local CombatLog = require(ServerStorage.Packages.CombatLog) -- (2.13.0) Studio combat log
"""),
    (S, """	Activate = function(self: ActionManager, Paramaters: { Aerial: boolean; Running: boolean })""",
        """	Activate = function(self: ActionManager, Paramaters: { Aerial: boolean; Running: boolean; Predicted: number? })"""),
    (S, """		local Track = TrackService.Play(Config.Animations.M1[NewCombo], self.Character, `Attack`, 0)
		Track:SetPriority(Enum.AnimationPriority.Action3)
""", """		local Track = TrackService.Play(Config.Animations.M1[NewCombo], self.Character, `Attack`, 0)
		Track:SetPriority(Enum.AnimationPriority.Action3)
		-- (2.13.0, combat concept 12) the client already started this exact hit the moment you clicked
		-- (InputController.Combat.M1.Predict). This copy keeps the timing (hit frame, end lag, cancels) and plays almost
		-- invisibly; the client's copy is the one everyone sees, and it stops when this one does.
		local Predicted = Paramaters.Predicted == NewCombo
		if Predicted then Track:SetWeight(0.01, 0) end
		if CombatLog.On() and Paramaters.Predicted then
			CombatLog.Log(self.Character, `predict`, if Predicted then `hit ` .. NewCombo .. ` matches the client` else string.format(`client guessed hit %d, server plays %d`, Paramaters.Predicted, NewCombo))
		end
"""),
    (S, """		HitBox.Offset = Config.Offset or CFrame.new(0, 0, -3.5)
		HitBox.HitBoxDetection = `Default`
""", """		HitBox.Offset = Config.Offset or CFrame.new(0, 0, -3.5)
		HitBox.HitBoxDetection = `Default`
		HitBox.Rewind = LagComp.Rewind(self.Character, Predicted) -- (2.13.0) judged where the target was on your screen
"""),
]
S = "ServerScriptService.Services.Player.ActionManager.Combat.M1"
A = "ServerScriptService.Services.Player.ActionManager"

EDITS = [
    # ---------------- server handler: tell the client when its predicted swing won't play
    (A, """		local ActionManager = Manager.new(Character)
		-- (fist moveset) M1 while holding block is the clinch (Combat.Clinch): a grab that goes through a guard
		if ActionManager.Action == `Block` and not Paramaters.Aerial and Local.IsFist(Character) then
			ActionManager:Activate(`Clinch`)
			return
		end""", """		local ActionManager = Manager.new(Character)
		-- (2.13.0, combat concept 12) the client started a swing this press won't play (refused, buffered for later, the
		-- clinch): bumping NHPredictRefused makes it drop its copy at once (InputController.Combat.M1.Predict)
		local function Refuse()
			if Paramaters.Predicted then Character:SetAttribute(`NHPredictRefused`, (Character:GetAttribute(`NHPredictRefused`) or 0) + 1) end
		end
		-- (fist moveset) M1 while holding block is the clinch (Combat.Clinch): a grab that goes through a guard
		if ActionManager.Action == `Block` and not Paramaters.Aerial and Local.IsFist(Character) then
			Refuse()
			ActionManager:Activate(`Clinch`)
			return
		end"""),
    (A, """		if not ActionManager:Activate(`M1`, Paramaters) and ActionManager.Action == `M1` and not Paramaters.Aerial and Press then
			ActionManager.BufferedM1 = os.clock()
		end""", """		if not ActionManager:Activate(`M1`, Paramaters) then
			Refuse()
			if ActionManager.Action == `M1` and not Paramaters.Aerial and Press then
				ActionManager.BufferedM1 = os.clock()
			end
		end"""),

    # ---------------- server M1: the air and running swings aren't the predicted one either
    (S, """		if Paramaters.Aerial and not self.Cooldowns[`Aerial M1`] then AerialM1(self) return end
		if Paramaters.Running and not self.Cooldowns[`Running M1`] then	RunningM1(self) return end""",
        """		-- (2.13.0) a predicted press that turns into another swing (or none) tells the client to drop its copy
		local function Refuse()
			if Paramaters.Predicted then self.Character:SetAttribute(`NHPredictRefused`, (self.Character:GetAttribute(`NHPredictRefused`) or 0) + 1) end
		end
		if Paramaters.Aerial and not self.Cooldowns[`Aerial M1`] then Refuse() AerialM1(self) return end
		if Paramaters.Running and not self.Cooldowns[`Running M1`] then Refuse() RunningM1(self) return end"""),
    (S, """		if not Profile then return end""", """		if not Profile then Refuse() return end"""),
    (S, """		if not Config then return end""", """		if not Config then Refuse() return end"""),
]
S = "ServerScriptService.Services.Player.ActionManager.Combat.M1"
EDITS = [
    (S, """				HitBox:Go()
				self.Character:SetAttribute(`Tick`, tick())""", """				HitBox:Go()
				self.Character:SetAttribute(`Tick`, tick())
				self.Character:SetAttribute(`NHHitAt`, workspace:GetServerTimeNow()) -- (2.13.0) the same moment on the synced clock, for the client's swing prediction"""),
]
B = "StarterPlayer.StarterPlayerScripts.Controllers.Character.InputController.General.Block"
EDITS = [
    (B, """	if InputState == `Began` then
		UnPackets.Block:Fire(`Activate`)

	else
		UnPackets.Block:Fire(`Release`)

	end""", """	-- (2.13.0) the local player's own "block is held" flag (client-set, never replicated): a click while it's held is
	-- the clinch, so InputController.Combat.M1.Predict doesn't start a punch for it
	Players.LocalPlayer:SetAttribute(`NHBlockHeld`, InputState == `Began`)
	if InputState == `Began` then
		UnPackets.Block:Fire(`Activate`)

	else
		UnPackets.Block:Fire(`Release`)

	end"""),
]
