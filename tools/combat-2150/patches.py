DL = "ServerStorage.Packages.DamageLogic"

EDITS = [
    # ---------------- beast stagger (concept 22), in the 2.14 Heat / gear wrapper
    (DL, """	local Heat = require(script.Parent.Heat)
	local HandGear = require(script.Parent.HandGear)
	local RawTakeAction, RawParry, RawDodge = Shared.TakeAction, Shared.Parry, Shared.PerfectDodge""",
         """	local Heat = require(script.Parent.Heat)
	local HandGear = require(script.Parent.HandGear)
	local BeastStagger = require(script.Parent.BeastStagger) -- (2.15.0, combat concept 22)
	local RawTakeAction, RawParry, RawDodge = Shared.TakeAction, Shared.Parry, Shared.PerfectDodge"""),
    (DL, """			if Heat.EXActive(Character) then DamageData.Damage *= Heat.EX_DAMAGE end
		end""", """			if Heat.EXActive(Character) then DamageData.Damage *= Heat.EX_DAMAGE end
		end
		-- (2.15.0) a staggered beast takes more; this hit may fill its stagger meter (BeastStagger)
		if Target and DamageData.Damage then DamageData.Damage *= BeastStagger.DamageMult(Target) end
		local StaggerGain = BeastStagger.Before(DamageData)"""),
    (DL, """		local Result = RawTakeAction(DamageData)
		if Character then Heat.Add(Character, if Counter then Heat.GAIN.Counter else Heat.GAIN.Hit) end
		return Result""", """		local Result = RawTakeAction(DamageData)
		if Character then Heat.Add(Character, if Counter then Heat.GAIN.Counter else Heat.GAIN.Hit) end
		BeastStagger.After(DamageData, StaggerGain, Heat)
		return Result"""),
]
EDITS = [('ServerScriptService.Services.AI.StudentBrain', 'function React.Gawk(S, Snap)\n\tlocal T = Snap.Threat\n\tmood(S, `Watching`, 4)\n\tif not S.Seated then\n\t\tS.Model:SetAttribute(`NHActivity`, `Watching a fight`)\n\t\tS.Agent:Stop()\n\t\tpose(S, nil)\n\t\tS.Agent:Face(T.Pos)\n\tend\n\tlookAt(S, T.Pos + Vector3.new(0, 2, 0), 1.2)\n\tif os.clock() > (S.WatchUntil or 0) then -- just started watching\n\t\tif T.From and T.From.Player then memo(S, T.From.Player).Fought = os.clock() end\n\t\tif T.Heard and math.random() < 0.5 then\n\t\t\tsay(S, Lines.Heard.Fight, 10)\n\t\telse\n\t\t\tsayMatrix(S, `FightSeen`, T.From and T.From.Player, nil, 10, Lines.ByNature(S, Lines.Gawk, `Brave`))\n\t\tend\n\telseif math.random() < 0.08 then\n\t\tsayMatrix(S, `FightSeen`, T.From and T.From.Player, nil, 9, Lines.ByNature(S, Lines.Gawk, `Brave`))\n\tend\n\tS.WatchUntil = os.clock() + 6\n\tS.WatchAt = T.Pos\n\tS.Shaken = true\n\ttask.wait(0.4)\nend', "---| (2.15.0, combat concept 19) crowds at fights |---\n-- Gawkers form a ring round a fight at a safe distance (each one just outside their own Danger distance), face it,\n-- and act the part: the brave chant and shout bets, the timid beg them to stop or say they're glad it isn't them,\n-- the rest call the state of the fight, and about a third hold a phone up to record it. A ring of three or more\n-- draws the nearest hall monitor (School.HallMonitor.Respond, once every 25 s per ring; the Map has no monitors).\nlocal Rings = {} :: { any }\nlocal GOLDEN = math.rad(137.5)\nlocal RECORD_POSE = CFrame.Angles(0, math.rad(35), math.rad(140)) -- the right arm up in front, phone to the fight\n\nlocal function ringFor(Center: Vector3)\n\tlocal Now = os.clock()\n\tfor I = #Rings, 1, -1 do if Now - Rings[I].Last > 10 then table.remove(Rings, I) end end\n\tfor _, R in Rings do\n\t\tif (R.Center - Center).Magnitude < 16 then\n\t\t\tR.Center = R.Center:Lerp(Center, 0.3)\n\t\t\tR.Last = Now\n\t\t\treturn R\n\t\tend\n\tend\n\tlocal R = { Center = Center; Members = {}; Count = 0; Last = Now; Alerted = 0; Base = math.random() * math.pi * 2 }\n\ttable.insert(Rings, R)\n\treturn R\nend\n\n-- this student's spot in the ring: spread round it (golden angle), just outside the distance that would scare them off\nlocal function ringSpot(S, R): Vector3?\n\tlocal Slot = R.Members[S]\n\tif not Slot then R.Count += 1 Slot = R.Count R.Members[S] = Slot end\n\tlocal Close = 10 + (1 - (S.Bravery or 0.5)) * 12 -- the Danger distance (urgentNow)\n\tlocal Radius = Close + 2.5 + (Slot % 2) * 1.5\n\tlocal A = R.Base + Slot * GOLDEN\n\tlocal P = R.Center + Vector3.new(math.cos(A), 0, math.sin(A)) * Radius\n\treturn Nav.Floor(P, 6)\nend\n\nlocal function crowdCount(R): number\n\tlocal N = 0\n\tfor S in R.Members do if S.Model and S.Model.Parent and watching(S) then N += 1 end end\n\treturn N\nend\n\nlocal function crowdLine(S)\n\tlocal P, B = Lines.Crowd, S.Bravery or 0.5\n\tlocal Pool = if B > 0.65 then (if math.random() < 0.5 then P.Chant else P.Bet)\n\t\telseif B < 0.35 then (if math.random() < 0.5 then P.Beg else P.Glad)\n\t\telseif S.CrowdPhone then P.Phone\n\t\telse P.State\n\tsay(S, Pool, 9)\nend\n\n-- a phone held up at the fight while they watch (the fidget's phone, arm raised); it goes away when the watching ends\nlocal function holdPhone(S)\n\tif S.CrowdPhone or S.Seated or not (Brain._MakePhone and Brain._Shoulder) then return end\n\tlocal T, J = Brain._MakePhone(), Brain._Shoulder(S)\n\tif not (T and J and S.Hum) then if T then T:Destroy() end return end\n\tS.CrowdPhone = T\n\tT.Parent = S.Model\n\tpcall(function() S.Hum:EquipTool(T) end)\n\tJ.C0 = (J:GetAttribute(`NHBaseC0`) or J.C0) * RECORD_POSE\n\ttask.spawn(function()\n\t\twhile S.Model and S.Model.Parent and T.Parent and watching(S) do task.wait(0.3) end\n\t\tif T.Parent then T:Destroy() end\n\t\tif J.Parent then J.C0 = J:GetAttribute(`NHBaseC0`) or J.C0 end\n\t\tS.CrowdPhone = nil\n\tend)\nend\n\nfunction React.Gawk(S, Snap)\n\tlocal T = Snap.Threat\n\tmood(S, `Watching`, 4)\n\tlocal Started = os.clock() > (S.WatchUntil or 0)\n\tlocal R = ringFor(T.Pos)\n\tif not S.Seated then\n\t\tS.Model:SetAttribute(`NHActivity`, `Watching a fight`)\n\t\tpose(S, nil)\n\t\tlocal Spot = ringSpot(S, R)\n\t\tif Spot and S.Root and (S.Root.Position - Spot).Magnitude > 3 then\n\t\t\tS.Agent:GoTo(Spot, { Speed = 9 + (S.Bravery or 0.5) * 3; Arrive = 1.5 })\n\t\telse\n\t\t\tS.Agent:Stop()\n\t\tend\n\t\tS.Agent:Face(R.Center)\n\t\tif Started and math.random() < 0.35 then holdPhone(S) end\n\tend\n\tlookAt(S, R.Center + Vector3.new(0, 2, 0), 1.2)\n\tif Started then -- just started watching\n\t\tif T.From and T.From.Player then memo(S, T.From.Player).Fought = os.clock() end\n\t\tif T.Heard and math.random() < 0.5 then\n\t\t\tsay(S, Lines.Heard.Fight, 10)\n\t\telse\n\t\t\tsayMatrix(S, `FightSeen`, T.From and T.From.Player, nil, 10, Lines.ByNature(S, Lines.Gawk, `Brave`))\n\t\tend\n\telseif math.random() < 0.12 then\n\t\tcrowdLine(S)\n\tend\n\tS.WatchUntil = os.clock() + 6\n\tS.WatchAt = T.Pos\n\tS.Shaken = true\n\tif os.clock() - R.Alerted > 25 and crowdCount(R) >= 3 then\n\t\tR.Alerted = os.clock()\n\t\ttask.spawn(function()\n\t\t\tlocal School = ServerScriptService.Services:FindFirstChild(`School`)\n\t\t\tlocal M = School and School:FindFirstChild(`HallMonitor`)\n\t\t\tif not M then return end\n\t\t\tlocal Ok, HM = pcall(require, M)\n\t\t\tif Ok and typeof(HM) == `table` and HM.Respond then pcall(HM.Respond, R.Center) end\n\t\tend)\n\tend\n\ttask.wait(0.4)\nend"), ('ServerScriptService.Services.AI.StudentBrain', 'local function shoulder(S): Motor6D?', "local shoulder\n-- (2.15.0) the crowd's phone (React.Gawk, defined above, reaches these through Brain)\nBrain._MakePhone = function() return makePhone() end\nBrain._Shoulder = function(S) return shoulder(S) end\n\nfunction shoulder(S): Motor6D?"), ('ServerScriptService.Services.AI.StudentBrain.Lines', 'function Lines.ByNature(S, Pool: any, Kind: string): { string }', "-- (2.15.0, combat concept 19) a ring of students round a fight (StudentBrain crowds). No gore: hurt, never worse.\nLines.Crowd = {\n\tChant = { `Fight! Fight! Fight!`, `Get him!`, `Ooooh!`, `Hit him back!`, `Let's GO!`, `Again! Again!`, `Don't just stand there!`, `Finish it!` };\n\tBet = { `Ten yen says the new kid wins.`, `My lunch money's on the tall one.`, `Twenty on the left!`, `I'll bet my notes he goes down.`,\n\t\t`Double or nothing!`, `Pay up, I called it.`, `Nobody's taking my bet? Cowards.` };\n\tState = { `He's still standing?!`, `That's gotta hurt.`, `Oof. He felt that.`, `She's barely trying!`, `Somebody's getting detention.`,\n\t\t`He's done. He's so done.`, `Wait, he's getting back up!`, `That's the third time he's dodged that.` };\n\tBeg = { `Guys, stop, please!`, `Someone get a teacher...`, `This isn't funny any more!`, `Stop it, you'll get expelled!`, `Please, just walk away!`,\n\t\t`It's not worth it!` };\n\tGlad = { `Glad that's not me.`, `Better him than me.`, `I'm staying right back here.`, `Not my fight. Not my fight.`, `I'm just watching. From here.` };\n\tPhone = { `I'm so posting this.`, `Is this recording? It's recording.`, `Hold still, I'm filming!`, `This is going on the board tomorrow.`,\n\t\t`Somebody block the hall monitor's view.` };\n}\n\nfunction Lines.ByNature(S, Pool: any, Kind: string): { string }")]
DL = "ServerStorage.Packages.DamageLogic"
KB = "ReplicatedStorage.Packages.Bind.Keybinds.Config"
EDITS = [
    (DL, """	local BeastStagger = require(script.Parent.BeastStagger) -- (2.15.0, combat concept 22)""",
         """	local BeastStagger = require(script.Parent.BeastStagger) -- (2.15.0, combat concept 22)
	local TagAssist = require(script.Parent.TagAssist) -- (2.15.0, combat concept 21) who you last hit, for the call"""),
    (DL, """		BeastStagger.After(DamageData, StaggerGain, Heat)
		return Result""", """		BeastStagger.After(DamageData, StaggerGain, Heat)
		if Character and Target then TagAssist.NoteHit(Character, Target) end
		return Result"""),
    (KB, """		LockOn = { `MouseButton3` }; -- (combat A5) middle mouse; pads and touch get aim assist on each swing instead (no free button)
""", """		LockOn = { `MouseButton3` }; -- (combat A5) middle mouse; pads and touch get aim assist on each swing instead (no free button)
		Assist = { `G` }; -- (2.15.0, combat concept 21) call your study group in / answer their call (no free pad button)
"""),
]
EL = "ServerScriptService.Services.Managers.EntityLoader"
NC = "ReplicatedStorage.Config.NPC"
NA = "ServerScriptService.Services.AI.AI.NPCActions"
EDITS = [
    (EL, """		clonedData.Weapon = `Katana` -- (armory) students now start on Fist; NPCs and dummies keep their old Katana default""",
         """		-- (2.15.0, owner) enemy NPCs fight with their fists by default (some carry contraband: NPCActions.EquipNow); an NPC
		-- whose config names another weapon gets it when it equips. The named test dummies below keep the katana.
		clonedData.Weapon = `Fist`"""),
    (NC, """		Weapon = `Katana`;
		AttackCooldown = 0.4;""", """		Weapon = `Fist`; -- (2.15.0, owner) enemy NPCs fight with their fists by default
		ContrabandChance = 0.25; -- (2.15.0) a fist NPC carries brass knuckles this often (NHContraband attribute: true forces, false never)
		AttackCooldown = 0.4;"""),
    (NA, """	local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)
	local Config = WeaponsConfig[WeaponName]

	if not Config then
		return
	end

	Humanoid:SetAttribute(`Equip`, true)

	if WeaponName == `Fist` then
		return
	end""", """	local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)
	local Config = WeaponsConfig[WeaponName]

	if not Config then
		return
	end

	Humanoid:SetAttribute(`Equip`, true)
	-- (2.15.0) the class it equips is the class it fights with (the profile and the Weapon attribute agree)
	pcall(function()
		local Profile = require(ServerScriptService.Services.Managers.EntityLoader).GetProfile(Character)
		if Profile then Profile.Weapon = WeaponName end
	end)
	Character:SetAttribute(`Weapon`, WeaponName)

	if WeaponName == `Fist` then
		-- (2.15.0, owner) some enemy NPCs carry contraband: brass knuckles on their hands, with their bonus (HandGear)
		local Forced = Character:GetAttribute(`NHContraband`)
		local Chance = 0
		pcall(function() Chance = require(ReplicatedStorage.Config.NPC).Default.ContrabandChance or 0 end)
		local Carry = if Forced ~= nil then Forced == true else math.random() < Chance
		if Carry and Character:GetAttribute(`NHGear`) == nil then
			Character:SetAttribute(`NHGear`, `BrassKnuckles`)
			pcall(function() require(game:GetService(`ServerStorage`).Packages.HandGear).Dress(Character, `BrassKnuckles`) end)
		end
		return
	end"""),
]
