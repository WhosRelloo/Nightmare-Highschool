AR = "ReplicatedStorage.Config.Armory"
DI = "ReplicatedStorage.Config.Discipline"

EDITS = [
    (AR, """Armory.Shop = { Name = `Iron Vigil Armoury`; Sub = `The armourer`; Text = `Everyone starts with their fists. Steel costs Yen.` }
""", """Armory.Shop = { Name = `Iron Vigil Armoury`; Sub = `The armourer`; Text = `Everyone starts with their fists. Steel costs Yen.` }

-- (2.14.0, combat concept 16) hand gear for fists: bought here, one worn at a time (PlayerData.Armory.Gear =
-- { Owned = { [Id] = true }, Worn = Id }). Effects: ServerStorage.Packages.HandGear. Icon / Mesh / textures are group
-- 15981569 uploads (art/group-upload-fistgear); while empty the shop shows the name and nothing is drawn on the hands.
Armory.Gear = {
	{ Id = `HandWraps`; Name = `Hand Wraps`; Price = 250; Icon = ``;
		Text = `Taped knuckles. You take 10% less guard damage while blocking.` };
	{ Id = `WeightedGloves`; Name = `Weighted Gloves`; Price = 500; Icon = ``;
		Text = `Iron in the knuckles. +20% guard damage, but your swings are 5% slower.` };
	{ Id = `BrassKnuckles`; Name = `Brass Knuckles`; Price = 800; Icon = ``; Contraband = true;
		Text = `+15% fist damage, +10% guard damage. Contraband: a hall monitor who sees you fight takes them.` };
}
Armory.GearById = {}
for _, G in Armory.Gear do Armory.GearById[G.Id] = G end

local function GearSave(Data: any): { Owned: { [string]: boolean }, Worn: string? }?
	if typeof(Data) ~= `table` then return nil end
	if typeof(Data.Armory) ~= `table` then Data.Armory = {} end
	if typeof(Data.Armory.Gear) ~= `table` then Data.Armory.Gear = { Owned = {} } end
	if typeof(Data.Armory.Gear.Owned) ~= `table` then Data.Armory.Gear.Owned = {} end
	return Data.Armory.Gear
end

function Armory.OwnsGear(Data: any, Id: string?): boolean
	local G = typeof(Data) == `table` and typeof(Data.Armory) == `table` and Data.Armory.Gear
	return typeof(G) == `table` and typeof(G.Owned) == `table` and typeof(Id) == `string` and G.Owned[Id] == true
end

function Armory.WornGear(Data: any): string?
	local G = typeof(Data) == `table` and typeof(Data.Armory) == `table` and Data.Armory.Gear
	local W = typeof(G) == `table` and G.Worn
	return if typeof(W) == `string` and Armory.GearById[W] and Armory.OwnsGear(Data, W) then W else nil
end

function Armory.GrantGear(Data: any, Id: string)
	local G = GearSave(Data)
	if G and Armory.GearById[Id] then G.Owned[Id] = true end
end

function Armory.WearGear(Data: any, Id: string?)
	local G = GearSave(Data)
	if not G then return end
	G.Worn = if Id and Armory.OwnsGear(Data, Id) then Id else nil
end

-- confiscated (contraband): gone from the save, and off your hands
function Armory.TakeGear(Data: any, Id: string)
	local G = GearSave(Data)
	if not G then return end
	G.Owned[Id] = nil
	if G.Worn == Id then G.Worn = nil end
end
"""),
    (DI, """		Fighting         = { Points = 4; Text = `Fighting on school grounds` };""",
        """		Fighting         = { Points = 4; Text = `Fighting on school grounds` };
		Contraband       = { Points = 3; Text = `Caught with brass knuckles (confiscated)` }; -- (2.14.0) HallMonitor"""),
]
DL = "ServerStorage.Packages.DamageLogic"
M1 = "ServerScriptService.Services.Player.ActionManager.Combat.M1"
AM = "ServerScriptService.Services.Player.ActionManager"
PO = "ServerScriptService.Services.Features.Posture"
HM = "ServerScriptService.Services.School.HallMonitor"
PR = "StarterPlayer.StarterPlayerScripts.Controllers.Character.InputController.Combat.M1.Predict"

EDITS = [
    # ---------------- DamageLogic: hand gear guard multipliers (16), EX armour and Heat (18)
    (DL, """		local PostureGain = (DamageData.Posture or (DamageData.Damage * 1.7)) * (Target:GetAttribute(`NH_PostureGain`) or 1) -- progression (Grit, traits)
""", """		local PostureGain = (DamageData.Posture or (DamageData.Damage * 1.7)) * (Target:GetAttribute(`NH_PostureGain`) or 1) -- progression (Grit, traits)
		-- (2.14.0, combat concept 16) hand gear: wraps take less, gloves and knuckles deal more
		do
			local HandGear = require(script.Parent.HandGear)
			PostureGain *= HandGear.Mult(Target, `GuardTaken`) * HandGear.Mult(Character, `GuardDealt`)
		end
"""),
    (DL, """	if not inAir then
		ActionManager.CancelClass(Target, `Attack`)
	end""", """	-- (2.14.0, combat concept 18) an EX skill's wind-up is armoured: the hit hurts, but doesn't cancel it
	if not inAir and not require(script.Parent.Heat).Armored(Target) then
		ActionManager.CancelClass(Target, `Attack`)
	end"""),
    (DL, """
-- (2.13.0, combat concept 14) the Studio combat log: what each hit came to.""", """
-- (2.14.0, combat concepts 16 and 18) brass knuckles' fist damage, an EX skill's damage and armour, and Heat: landed
-- hits, counter-hits, parries and perfect dodges fill it (ServerStorage.Packages.Heat)
do
	local Heat = require(script.Parent.Heat)
	local HandGear = require(script.Parent.HandGear)
	local RawTakeAction, RawParry, RawDodge = Shared.TakeAction, Shared.Parry, Shared.PerfectDodge
	Shared.TakeAction = function(DamageData: DamageData)
		local Character = DamageData and DamageData.Character
		local Target = DamageData and DamageData.Target
		if Character and DamageData.Damage then
			DamageData.Damage *= HandGear.Mult(Character, `Damage`)
			if Heat.EXActive(Character) then DamageData.Damage *= Heat.EX_DAMAGE end
		end
		if Target and Heat.Armored(Target) then -- the EX wind-up: no stun, no knockback, no react
			DamageData.Stun = nil
			DamageData.StunLocked = false
			DamageData.LinearVelocity = nil
			DamageData.NoAnimation = true
			DamageData.States = {}
		end
		local W = Target and Target:GetAttribute(`NHWindupUntil`)
		local Counter = typeof(W) == `number` and workspace:GetServerTimeNow() < W and StateManager.HasState(Target, `Attacking`)
		local Result = RawTakeAction(DamageData)
		if Character then Heat.Add(Character, if Counter then Heat.GAIN.Counter else Heat.GAIN.Hit) end
		return Result
	end
	Shared.Parry = function(DamageData: DamageData, Parry: boolean?)
		local Result = RawParry(DamageData, Parry)
		if Parry and DamageData and DamageData.Target then Heat.Add(DamageData.Target, Heat.GAIN.Parry) end
		return Result
	end
	Shared.PerfectDodge = function(Character: Model, Target: Model)
		local Result = RawDodge(Character, Target)
		if Target then Heat.Add(Target, Heat.GAIN.Dodge) end
		return Result
	end
end

-- (2.13.0, combat concept 14) the Studio combat log: what each hit came to."""),

    # ---------------- Combat.M1: weighted gloves' swing speed (16), the race's 4th hit (17)
    (M1, """local LagComp = require(ServerStorage.Packages.LagComp) -- (2.13.0) lag-compensated hits
""", """local LagComp = require(ServerStorage.Packages.LagComp) -- (2.13.0) lag-compensated hits
local HandGear = require(ServerStorage.Packages.HandGear) -- (2.14.0) hand gear
local RaceFists = require(ServerStorage.Packages.RaceFists) -- (2.14.0) the race's 4th hit
"""),
    (M1, """		if Config.AnimationSpeed then
			Track:SetSpeed(Config.AnimationSpeed)
		end""", """		local SwingSpeed = (Config.AnimationSpeed or 1) * HandGear.Mult(self.Character, `SwingSpeed`) -- (2.14.0) weighted gloves
		if SwingSpeed ~= 1 then
			Track:SetSpeed(SwingSpeed)
		end"""),
    (M1, """			if not DamageLogic.Processed(DamageData) then
				return 
			end

			VowManager.VowAction(self.Character, `M1`, Humanoid)
			DamageLogic.TakeAction(DamageData)
		end)""", """			-- (2.14.0, combat concept 17) the last hit of a fist string carries the attacker's race
			local RaceHit = LastCombo and Weapon == `Fist`
			if RaceHit then RaceFists.Before(DamageData) end

			if not DamageLogic.Processed(DamageData) then
				return 
			end

			VowManager.VowAction(self.Character, `M1`, Humanoid)
			DamageLogic.TakeAction(DamageData)
			if RaceHit then pcall(RaceFists.After, DamageData, DamageLogic) end
		end)"""),

    # ---------------- ActionManager: a full Heat bar makes a skill an EX (18)
    (AM, """local CombatLog = require(game:GetService(`ServerStorage`).Packages.CombatLog) -- (2.13.0) Studio combat log
""", """local CombatLog = require(game:GetService(`ServerStorage`).Packages.CombatLog) -- (2.13.0) Studio combat log
local Heat = require(game:GetService(`ServerStorage`).Packages.Heat) -- (2.14.0) EX skills
"""),
    (AM, """		CombatLog.Log(self.Character, `start`, Action .. (if self.Action and self.Action ~= Action then ` (cancels ` .. tostring(self.Action) .. `)` else ``))
	end
""", """		CombatLog.Log(self.Character, `start`, Action .. (if self.Action and self.Action ~= Action then ` (cancels ` .. tostring(self.Action) .. `)` else ``))
	end
	-- (2.14.0, combat concept 18) a skill (ActionManager.Skills) started on a full Heat bar is an EX
	local SkillModule = script:FindFirstChild(Action, true)
	local SpentEX = SkillModule ~= nil and SkillModule.Parent ~= nil and SkillModule.Parent.Name == `Skills` and Heat.TrySpend(self.Character, Action)
	if SpentEX and CombatLog.On() then CombatLog.Log(self.Character, `EX`, Action .. ` (a full Heat bar)`) end
"""),
    (AM, """		local Success, Result = pcall(
			Activate,
			self,
			unpack(Paramaters)

		)
""", """		local Success, Result = pcall(
			Activate,
			self,
			unpack(Paramaters)

		)
		if SpentEX then Heat.EndEX(self.Character) end -- (2.14.0) the EX ends with its skill
"""),

    # ---------------- Posture: a ghoul's ROT holds the guard's recovery (17)
    (PO, """		if Now - (LastGain[Humanoid] or 0) < Config.PostureRegenDelay then continue end""",
         """		if Now - (LastGain[Humanoid] or 0) < Config.PostureRegenDelay then continue end
		local Rot = Humanoid.Parent:GetAttribute(`NHPostureRotUntil`) -- (2.14.0) a ghoul's 4th hit (RaceFists)
		if typeof(Rot) == `number` and workspace:GetServerTimeNow() < Rot then continue end"""),

    # ---------------- HallMonitor: brass knuckles are contraband (16)
    (HM, """			Local.Say(M, `I saw that! No fighting!`)
			Discipline.ReportIncident({
				Type = `Fighting`; Suspect = Player; Witness = `Hall Monitor`;
				Position = Root.Position; Recognized = true;
			})""", """			Local.Say(M, `I saw that! No fighting!`)
			Discipline.ReportIncident({
				Type = `Fighting`; Suspect = Player; Witness = `Hall Monitor`;
				Position = Root.Position; Recognized = true;
			})
			-- (2.14.0, combat concept 16) brass knuckles are contraband: a monitor who sees you fight with them takes them
			if Attacker:GetAttribute(`NHGear`) == `BrassKnuckles` then
				local Took = false
				pcall(function() Took = require(game:GetService(`ServerScriptService`).Services.Features.Armory).Confiscate(Player, `BrassKnuckles`) end)
				if Took then
					task.delay(1.6, function() Local.Say(M, `And I'll take those knuckles.`) end)
					Discipline.ReportIncident({
						Type = `Contraband`; Suspect = Player; Witness = `Hall Monitor`;
						Position = Root.Position; Recognized = true;
					})
				end
			end"""),

    # ---------------- client prediction: the gloves' swing speed too
    (PR, """	if Config.AnimationSpeed then Twin:AdjustSpeed(Config.AnimationSpeed) end""",
         """	-- the server's speed for this swing: the weapon's, times weighted gloves' 0.95 with fists (ServerStorage HandGear)
	local Speed = (Config.AnimationSpeed or 1) * (if Weapon == `Fist` and Character:GetAttribute(`NHGear`) == `WeightedGloves` then 0.95 else 1)
	if Speed ~= 1 then Twin:AdjustSpeed(Speed) end"""),
]
A = "ServerScriptService.Services.Features.Armory"

EDITS = [
    (A, """		Buy  (RF, class)   -> ok, message
]]""", """		Buy  (RF, class)   -> ok, message
		Gear (RF, action, id) (2.14.0, combat concept 16) -> ok, message. Actions: Buy, Wear, Remove.
	Hand gear (Config.Armory.Gear): bought for Yen, one worn at a time (PlayerData.Armory.Gear). The worn piece is the
	character attribute NHGear (its effects: ServerStorage.Packages.HandGear) and its mesh on both hands. A hall monitor
	who sees you fight in brass knuckles takes them (Shared.Confiscate, from Services.School.HallMonitor).
]]"""),
    (A, """local Data = require(ServerScriptService.Services.Player.Data)
local Armory = require(ReplicatedStorage.Config.Armory)
""", """local Data = require(ServerScriptService.Services.Player.Data)
local Armory = require(ReplicatedStorage.Config.Armory)
local HandGear = require(game:GetService(`ServerStorage`).Packages.HandGear) -- (2.14.0)
"""),
    (A, """	return { Yen = Profile and Profile.Yen or 0; Weapon = Profile and Profile.Weapon; Shop = Armory.Shop; Items = Items; Loaded = Profile ~= nil }
end""", """	-- (2.14.0) hand gear
	local Gear = {}
	local Worn = Armory.WornGear(Profile)
	for _, G in Armory.Gear do
		table.insert(Gear, { Id = G.Id; Name = G.Name; Price = G.Price; Text = G.Text; Icon = G.Icon; Contraband = G.Contraband;
			Owned = Armory.OwnsGear(Profile, G.Id); Worn = Worn == G.Id })
	end
	return { Yen = Profile and Profile.Yen or 0; Weapon = Profile and Profile.Weapon; Shop = Armory.Shop; Items = Items; Gear = Gear; Loaded = Profile ~= nil }
end

---| hand gear (2.14.0, combat concept 16) |---

-- the worn piece onto the character: the NHGear attribute (the effects) and the mesh on both hands
function Shared.SyncGear(P: Player)
	local C = P.Character
	if not C then return end
	local Worn = Armory.WornGear(Data.GetProfile(P))
	if C:GetAttribute(`NHGear`) == Worn and (Worn == nil or C:FindFirstChild(`NHGear_` .. Worn)) then return end
	C:SetAttribute(`NHGear`, Worn)
	pcall(HandGear.Dress, C, Worn)
end

function Shared.Gear(P: Player, Action: any, Id: any): (boolean, string)
	local G = typeof(Id) == `string` and Armory.GearById[Id]
	if not G then return false, `That isn't sold here.` end
	local Profile = Data.GetProfile(P)
	if not Profile then return false, `Your record isn't loaded yet.` end
	if Action == `Buy` then
		if Armory.OwnsGear(Profile, G.Id) then return false, `You already own the {G.Name}.` end
		if not Shared.Near(P) then return false, `Buy it at the armory.` end
		local Price = math.max(0, math.floor(tonumber(G.Price) or 0))
		if (tonumber(Profile.Yen) or 0) < Price then return false, `Not enough Yen. The {G.Name} cost \\u{A5}{Price}.` end
		if Price > 0 then Data.UpdateState(P, { type = `UpdateYen`; amount = -Price }) end
		Armory.GrantGear(Profile, G.Id)
		Armory.WearGear(Profile, G.Id) -- straight on
		Shared.SyncGear(P)
		return true, `The {G.Name} are yours, and on your hands.`
	elseif Action == `Wear` then
		if not Armory.OwnsGear(Profile, G.Id) then return false, `You don't own the {G.Name}.` end
		Armory.WearGear(Profile, G.Id)
		Shared.SyncGear(P)
		return true, `{G.Name} on.`
	elseif Action == `Remove` then
		if Armory.WornGear(Profile) == G.Id then Armory.WearGear(Profile, nil) end
		Shared.SyncGear(P)
		return true, `{G.Name} off.`
	end
	return false, `Something went wrong.`
end

-- contraband taken by a hall monitor: gone from the save and off the hands. True when there was something to take.
function Shared.Confiscate(P: Player, Id: string): boolean
	local Profile = Data.GetProfile(P)
	if not (Profile and Armory.OwnsGear(Profile, Id)) then return false end
	Armory.TakeGear(Profile, Id)
	Shared.SyncGear(P)
	return true
end"""),
    (A, """	local Buy = F:FindFirstChild(`Buy`) or Instance.new(`RemoteFunction`); Buy.Name = `Buy`; Buy.Parent = F
""", """	local Buy = F:FindFirstChild(`Buy`) or Instance.new(`RemoteFunction`); Buy.Name = `Buy`; Buy.Parent = F
	local GearRF = F:FindFirstChild(`Gear`) or Instance.new(`RemoteFunction`); GearRF.Name = `Gear`; GearRF.Parent = F -- (2.14.0)
"""),
    (A, """	Players.PlayerRemoving:Connect(function(P) Busy[P] = nil end)
""", """	GearRF.OnServerInvoke = function(P, Action, Id) -- (2.14.0) hand gear
		if Busy[P] then return false, `One moment...` end
		Busy[P] = true
		local Ok, A, B = pcall(Shared.Gear, P, Action, Id)
		Busy[P] = nil
		if not Ok then warn(`[Armory] {A}`) return false, `Something went wrong.` end
		return A, B
	end
	Players.PlayerRemoving:Connect(function(P) Busy[P] = nil end)
	-- (2.14.0) the worn hand gear back on every spawn (once the record has loaded)
	local function Watch(P: Player)
		P.CharacterAdded:Connect(function()
			task.spawn(function()
				for _ = 1, 60 do
					if Data.GetProfile(P) then break end
					task.wait(0.5)
				end
				task.wait(0.5)
				Shared.SyncGear(P)
			end)
		end)
		if P.Character then task.spawn(Shared.SyncGear, P) end
	end
	Players.PlayerAdded:Connect(Watch)
	for _, P in Players:GetPlayers() do Watch(P) end
"""),
]
EDITS.append((A, """		if Cmd == `Yen` and typeof(A) == `number` then Data.UpdateState(P, { type = `UpdateYen`; amount = math.floor(A) }) end""",
"""		if Cmd == `Yen` and typeof(A) == `number` then Data.UpdateState(P, { type = `UpdateYen`; amount = math.floor(A) }) end
		-- (2.14.0) Gear, id: owns and wears it (nil id: takes the worn one off)
		if Cmd == `Gear` then
			if typeof(A) == `string` then Armory.GrantGear(Profile, A) end
			Armory.WearGear(Profile, if typeof(A) == `string` then A else nil)
			Shared.SyncGear(P)
		end"""))
EDITS.append((A, """		return { Weapon = Profile.Weapon; Owned = Owned; Yen = Profile.Yen; V = Profile.Armory and Profile.Armory.V }""",
"""		return { Weapon = Profile.Weapon; Owned = Owned; Yen = Profile.Yen; V = Profile.Armory and Profile.Armory.V; Gear = Armory.WornGear(Profile) }"""))
U = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.ArmoryUi"

EDITS = [
    (U, """local Ui = nil
local OpenAt: BasePart? = nil
local Inflight = false
""", """local Ui = nil
local OpenAt: BasePart? = nil
local Inflight = false
local Tab = `Classes` -- (2.14.0) or `Gear`: the hand gear tab
local GEAR_RARITY = { HandWraps = `Common`; WeightedGloves = `Rare`; BrassKnuckles = `Epic` }
"""),
    (U, """	Kit.Button({ text = `Close`; style = `ghost`; Size = UDim2.fromOffset(160, 40); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -8, 1, -52); Parent = Body;
		onClick = function() Shared.Close() end })
	Ui = { Gui = G; Panel = Api; Grid = Grid; Yen = YenApi; Status = Status; Sub = Sub }""", """	Kit.Button({ text = `Close`; style = `ghost`; Size = UDim2.fromOffset(160, 40); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -8, 1, -52); Parent = Body;
		onClick = function() Shared.Close() end })
	-- (2.14.0, combat concept 16) two tabs: the classes, and hand gear for fists
	local Tabs = {}
	for I, Name in { `Classes`, `Gear` } do
		local _, B = Kit.Button({ text = if Name == `Gear` then `Hand gear` else `Classes`; style = `ghost`; textSize = 15;
			Size = UDim2.fromOffset(120, 32); Position = UDim2.fromOffset(8 + (I - 1) * 128, 28); Parent = Body;
			onClick = function() Tab = Name Shared.Open(OpenAt) end })
		Tabs[Name] = B
	end
	Grid.Position = UDim2.fromOffset(0, 68)
	Grid.Size = UDim2.new(1, 0, 1, -128)
	Ui = { Gui = G; Panel = Api; Grid = Grid; Yen = YenApi; Status = Status; Sub = Sub; Tabs = Tabs }"""),
    (U, """function Local.Fill(Info)
	for _, Ch in Ui.Grid:GetChildren() do if Ch:IsA(`Frame`) then Ch:Destroy() end end
	Ui.Yen.Label.Text = `{YEN} {Info.Yen or 0}`
	local Shop = Info.Shop or ArmoryCfg.Shop
	if Ui.Panel.SetTitle then Ui.Panel:SetTitle(Shop.Name) end
	Ui.Sub.Text = `<i>{Shop.Sub}. {Shop.Text}</i>`
	for I, It in Info.Items or {} do Local.Cell(I, It, Info.Weapon == It.Class) end
end""", """-- (2.14.0) a hand gear cell: its icon (a group upload; the name until it's set), what it does, buy / wear / take off
function Local.GearCell(Order: number, It)
	local Cell = Instance.new(`Frame`)
	Cell.Name = It.Id
	Cell.BackgroundTransparency = 1
	Cell.LayoutOrder = Order
	Cell.Parent = Ui.Grid
	local HasIcon = typeof(It.Icon) == `string` and It.Icon ~= ``
	local Slot = Kit.ItemSlot({ item = { name = if HasIcon then `` else It.Name; rarity = GEAR_RARITY[It.Id] or `Common` }; size = 88;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 2); Parent = Cell })
	if HasIcon then
		local I = Instance.new(`ImageLabel`)
		I.Name = `NHIcon`
		I.BackgroundTransparency = 1
		I.Image = It.Icon
		I.AnchorPoint = Vector2.new(0.5, 0.5)
		I.Position = UDim2.fromScale(0.5, 0.5)
		I.Size = UDim2.fromScale(0.82, 0.82)
		I.ZIndex = 6
		I.Parent = Slot
	end
	Local.Label(Cell, It.Name, 18, { Font = Fonts.Title; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 96); Size = UDim2.new(1, 0, 0, 22) })
	Local.Label(Cell, It.Text or ``, 14, { TextColor3 = if It.Contraband then C.Gold else C.TextDim; TextXAlignment = Enum.TextXAlignment.Center;
		Position = UDim2.fromOffset(4, 120); Size = UDim2.new(1, -8, 0, 58) })
	local B
	if It.Worn then
		B = { text = `Take off`; style = `ghost`; onClick = function() Local.Gear(`Remove`, It.Id) end }
	elseif It.Owned then
		B = { text = `Wear`; style = `gold`; onClick = function() Local.Gear(`Wear`, It.Id) end }
	else
		B = { text = `Buy {YEN}{It.Price}`; style = `gold`; onClick = function() Local.Gear(`Buy`, It.Id) end }
	end
	Kit.Button({ text = B.text; style = B.style; textSize = 15; Size = UDim2.fromOffset(212, 38);
		Position = UDim2.fromOffset(4, 182); Parent = Cell; onClick = B.onClick })
end

function Local.Gear(Action: string, Id: string)
	local Ok, Msg = Local.Ask(`Gear`, Action, Id)
	if Ok then pcall(Kit.PlaySound, `Confirm`) end
	Shared.Open(OpenAt, Msg or (if Ok == nil then `One moment...` else nil))
end

function Local.Fill(Info)
	for _, Ch in Ui.Grid:GetChildren() do if Ch:IsA(`Frame`) then Ch:Destroy() end end
	Ui.Yen.Label.Text = `{YEN} {Info.Yen or 0}`
	local Shop = Info.Shop or ArmoryCfg.Shop
	if Ui.Panel.SetTitle then Ui.Panel:SetTitle(Shop.Name) end
	Ui.Sub.Text = `<i>{Shop.Sub}. {Shop.Text}</i>`
	if Tab == `Gear` and Info.Gear then
		for I, It in Info.Gear do Local.GearCell(I, It) end
	else
		for I, It in Info.Items or {} do Local.Cell(I, It, Info.Weapon == It.Class) end
	end
	-- the active tab reads as pressed
	for Name, B in Ui.Tabs or {} do
		pcall(function() if B.SetStyle then B:SetStyle(if Name == Tab then `gold` else `ghost`) end end)
	end
end"""),
]
A = "ServerScriptService.Services.Features.Armory"
EDITS = [(A, """		-- (2.14.0) Gear, id: owns and wears it (nil id: takes the worn one off)""", """		if Cmd == `Confiscate` and typeof(A) == `string` then Shared.Confiscate(P, A) end -- (2.14.0) what a hall monitor does
		-- (2.14.0) Gear, id: owns and wears it (nil id: takes the worn one off)""")]
U = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.ArmoryUi"
EDITS = [(U, """	for Name, B in Ui.Tabs or {} do
		pcall(function() if B.SetStyle then B:SetStyle(if Name == Tab then `gold` else `ghost`) end end)
	end""", """	for Name, B in Ui.Tabs or {} do
		pcall(function() B.Label.TextColor3 = if Name == Tab then C.Gold else C.TextDim end)
	end""")]
AR = "ReplicatedStorage.Config.Armory"
EDITS = [
 (AR, """	{ Id = `HandWraps`; Name = `Hand Wraps`; Price = 250; Icon = ``;""",
      """	{ Id = `HandWraps`; Name = `Hand Wraps`; Price = 250; Icon = ``; Mesh = ``; Textures = nil;
		Offset = CFrame.new(0, -0.677, -0.009); Size = Vector3.new(1.158, 0.784, 1.177);"""),
 (AR, """	{ Id = `WeightedGloves`; Name = `Weighted Gloves`; Price = 500; Icon = ``;""",
      """	{ Id = `WeightedGloves`; Name = `Weighted Gloves`; Price = 500; Icon = ``; Mesh = ``; Textures = nil;
		Offset = CFrame.new(0, -0.688, -0.016); Size = Vector3.new(1.166, 0.733, 1.198);"""),
 (AR, """	{ Id = `BrassKnuckles`; Name = `Brass Knuckles`; Price = 800; Icon = ``; Contraband = true;""",
      """	{ Id = `BrassKnuckles`; Name = `Brass Knuckles`; Price = 800; Icon = ``; Contraband = true; Mesh = ``; Textures = nil;
		Offset = CFrame.new(0, -0.729, -0.544); Size = Vector3.new(1.095, 0.679, 0.111);"""),
 (AR, """-- 15981569 uploads (art/group-upload-fistgear); while empty the shop shows the name and nothing is drawn on the hands.""",
      """-- 15981569 uploads (art/group-upload-fistgear); while empty the shop shows the name and nothing is drawn on the hands.
-- Mesh = the uploaded FBX's MeshId; Textures = { Color = id, Normal = id, Roughness = id, Metalness = id };
-- Offset / Size = where the mesh sits on each arm (art README, studs; the same part goes on both arms)."""),
]
