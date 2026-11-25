--[[
	Notoriety (server). Services.School.Notoriety  (2.37, the Bell Tower R2)
	Spec: docs/superpowers/specs/2026-11-20-notoriety-timetable-discipline-ui-design.md §3. Numbers: Config.Notoriety.

	Heat per player from misdeeds that staff witness -> five Bells (Murmur .. The Tolling) and a bell state:
	  Hollow (nobody knows the face), Tarnished (they do), Lit (a monitor sees you), Search (lost sight, < 30 s).
	Heat cools while unseen (faster hidden, fastest with an alibi). Rising tiers escalate: a monitor responds (Bell 3),
	every monitor converges and the PA calls a disturbance (Bell 4), an emergency PA (Bell 5).
	Caught = the violation + the tier bonus (Discipline.ReportIncident asks OnReport). Got away but identified =
	a summons (Discipline.Summons), served in Room 106 outside class; ignored past a day = Skipped Detention.

	Fed by: Discipline.ReportIncident -> Shared.OnReport; HallMonitor (chase start, a hit on a monitor) ->
	Shared.Witnessed; a character seen transforming -> Shared.Witnessed(Exposure).
	Player attributes: NHBells, NHBellState, NHSearchWhere, NHSummons (nil when there's nothing to show).
	Studio only: ServerStorage.NHNotorietyProbe (BindableFunction) for tools/belltower-r2/checks/nt_server.lua.
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)
local RunService = game:GetService(`RunService`)

local Config = require(ReplicatedStorage.Config.Notoriety)
local F = require(ReplicatedStorage.Functions.Notoriety)
local RegionsConfig = require(ReplicatedStorage.Config.Regions)
local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local Discipline = require(ServerScriptService.Services.School.Discipline)
local Notifications = require(ServerScriptService.Services.Features.Notifications)

local Local = {}
local Shared = {}
Shared.Changed = SignalPlus() -- (Player, Bells, State)

local States = {} :: { [Player]: any }
local Overrides = {} :: { [Player]: { Seen: boolean?, Mods: any? } } -- the probe's manual mode

---| Helpers |---

function Local.Lazy(Path: { string }): any?
	local Ok, M = pcall(function()
		local I: Instance = ServerScriptService
		for _, Name in Path do I = I:FindFirstChild(Name) :: Instance end
		return require(I :: ModuleScript)
	end)
	return if Ok then M else nil
end
function Local.HallMonitor(): any? return Local.Lazy({ `Services`, `School`, `HallMonitor` }) end
function Local.Broadcast(): any? return Local.Lazy({ `Services`, `World`, `Broadcast` }) end

function Local.Today(): number
	local St = SchoolClock.GetState()
	return St and St.Day or 0
end

function Local.Root(P: Player): BasePart?
	local C = P.Character
	return if C then C:FindFirstChild(`HumanoidRootPart`) :: BasePart? else nil
end

function Local.Get(P: Player)
	local S = States[P]
	if not S then
		S = {
			Heat = 0; Tier = 0; State = ``; T = 0; LastSeenAt = -math.huge; LastSeenPos = nil :: Vector3?; LitFor = 0;
			Misdeed = nil :: string?; Booked = true; Witness = nil :: string?; Identified = false;
			Responded = false; RespondOk = nil :: boolean?; Converged = false; Tolled = false;
		}
		States[P] = S
	end
	return S
end

function Local.FaceKnown(P: Player): boolean
	local D = Discipline.GetData(P)
	return D ~= nil and (D.FaceKnownUntilDay or -1) >= Local.Today()
end

function Local.Identify(P: Player)
	Local.Get(P).Identified = true
	local D = Discipline.GetData(P)
	if D then D.FaceKnownUntilDay = Local.Today() + 1 end
end

-- the region name at a point: the highest-priority box in workspace.Regions (Config.Regions)
function Local.WhereAt(Pos: Vector3?): string
	local Folder = workspace:FindFirstChild(`Regions`)
	if not (Pos and Folder) then return `` end
	local Best, BestPri = nil, -math.huge
	for _, Box in Folder:GetDescendants() do
		if not Box:IsA(`BasePart`) then continue end
		local Def = RegionsConfig.Defs[Box:GetAttribute(`RegionId`) or Box.Name]
		if not Def then continue end
		local L = Box.CFrame:PointToObjectSpace(Pos)
		local H = Box.Size / 2
		if math.abs(L.X) <= H.X and math.abs(L.Y) <= H.Y and math.abs(L.Z) <= H.Z and (Def.Priority or 0) > BestPri then
			Best, BestPri = Def, Def.Priority or 0
		end
	end
	return if Best then (Best.Title or Best.Name) else ``
end

function Local.Context(P: Player)
	local St = SchoolClock.GetState()
	local H = St and St.Hour or 12
	local L = P:GetAttribute(`DisciplineLevel`)
	return { Night = H >= 22 or H < 6; Probation = L == `Probation` or L == `Suspension` }
end

function Local.Mods(P: Player)
	local St = SchoolClock.GetState()
	local Kind = St and St.Segment and St.Segment.Kind
	local C = P.Character
	local Dorms = false
	pcall(function() Dorms = require(ServerScriptService.Services.Features.Regions).Inside(P, `Dorms`) end)
	local Off = false
	local HM = Local.HallMonitor()
	if HM and HM.OnCampus then
		local Ok, On = pcall(HM.OnCampus, P)
		Off = Ok and On == false
	end
	return {
		Alibi = (Kind == `Class` and P:GetAttribute(`ClassInRoom`) == true) or P:GetAttribute(`DetentionActive`) == true;
		Hidden = C ~= nil and C:GetAttribute(`Hidden`) == true;
		Dorms = Dorms;
		OffCampus = Off;
	}
end

function Local.InRoom106(P: Player): boolean
	local School = workspace:FindFirstChild(`School`)
	local Room = School and School:FindFirstChild(`R106`)
	local Zone = Room and Room:FindFirstChild(`Zone`) :: BasePart?
	local Root = Local.Root(P)
	if not (Zone and Root) then return false end
	local L = Zone.CFrame:PointToObjectSpace(Root.Position)
	local H = Zone.Size / 2
	return math.abs(L.X) <= H.X and math.abs(L.Y) <= H.Y and math.abs(L.Z) <= H.Z
end

---| State |---

function Local.Publish(P: Player)
	local S = Local.Get(P)
	local On = S.Tier > 0
	P:SetAttribute(`NHBells`, if On then S.Tier else nil)
	P:SetAttribute(`NHBellState`, if On and S.State ~= `` then S.State else nil)
	P:SetAttribute(`NHSearchWhere`, if On and S.State == `Search` then Local.WhereAt(S.LastSeenPos) else nil)
	local D = Discipline.GetData(P)
	local Count = if D and D.Summons then #D.Summons else 0
	P:SetAttribute(`NHSummons`, if Count > 0 then Count else nil)
end

function Local.Reset(P: Player)
	local S = Local.Get(P)
	S.Heat, S.Tier, S.State, S.LitFor = 0, 0, ``, 0
	S.Misdeed, S.Booked, S.Witness = nil, true, nil
	S.Responded, S.RespondOk, S.Converged, S.Tolled = false, nil, false, false
end

function Local.PA(Template: string, Where: string, Emergency: boolean)
	local B = Local.Broadcast()
	if not (B and B.PA) then return end
	local Text = Template:gsub(`{Where}`, if Where ~= `` then Where else `the school`)
	pcall(B.PA, Text, Emergency)
end

function Local.Escalate(P: Player)
	local S = Local.Get(P)
	local Root = Local.Root(P)
	local Pos = S.LastSeenPos or (if Root then Root.Position else nil)
	if not Pos then return end
	local HM = Local.HallMonitor()
	if S.Tier >= Config.HuntTier and not S.Responded then
		S.Responded = true
		if HM and HM.Respond then
			local Ok, R = pcall(HM.Respond, Pos)
			S.RespondOk = Ok and R == true
		end
	end
	if S.Tier >= Config.ConvergeTier and not S.Converged then
		S.Converged = true
		if HM and HM.Converge then pcall(HM.Converge, Pos) end
		Local.PA(Config.DisturbancePA, Local.WhereAt(Pos), false)
	end
	if S.Tier >= Config.TollTier and not S.Tolled then
		S.Tolled = true
		Local.PA(Config.TollPA, Local.WhereAt(Pos), true)
	end
end

function Local.AddHeat(P: Player, Amount: number)
	if Amount <= 0 then return end
	local S = Local.Get(P)
	local Old = S.Tier
	S.Heat = math.min(100, S.Heat + Amount)
	S.Tier = F.Tier(S.Heat)
	if S.Tier > Old then Local.Escalate(P) end
end

function Local.AddSummons(P: Player, Type: string, Witness: string?)
	local D = Discipline.GetData(P)
	if not D then return end
	D.Summons = D.Summons or {}
	if #D.Summons >= Config.SummonsLimit then return end
	table.insert(D.Summons, { Type = Type; Day = Local.Today(); Witness = Witness or `Staff` })
	Notifications.Notify(P, {
		Title = `Summons`;
		Text = `They know it was you. Report to Room 106 outside class by tomorrow.`;
		Kind = `Warning`;
		Duration = 6;
	})
end

-- the search is over: an identified student who got away gets a summons for what wasn't booked
function Local.Finish(P: Player)
	local S = Local.Get(P)
	if S.Misdeed and not S.Booked and (S.Identified or Local.FaceKnown(P)) then
		Local.AddSummons(P, F.BookType(S.Misdeed), S.Witness)
	end
	Local.Reset(P)
end

function Local.Step(P: Player, Dt: number)
	local S = Local.Get(P)
	if S.Heat <= 0 and S.Tier == 0 then return end
	S.T += Dt
	local O = Overrides[P]
	local Seen, Dist = false, math.huge
	if O and O.Seen ~= nil then
		Seen, Dist = O.Seen == true, 0
	else
		local HM = Local.HallMonitor()
		if HM and HM.SeenBy then
			local Ok, A, D = pcall(HM.SeenBy, P)
			if Ok then Seen, Dist = A == true, (if type(D) == `number` then D else math.huge) end
		end
	end
	if Seen then
		S.LastSeenAt = S.T
		local Root = Local.Root(P)
		if Root then S.LastSeenPos = Root.Position end
		S.LitFor += Dt
		if not S.Identified and (Dist <= Config.FaceSeenRange or S.LitFor >= Config.FaceLitSeconds) then Local.Identify(P) end
	else
		S.LitFor = 0
		local Mods = (if O and O.Mods then O.Mods else Local.Mods(P))
		S.Heat = F.Cool(S.Heat, Dt, S.T - S.LastSeenAt, F.CoolMult(Mods))
		S.Tier = F.Tier(S.Heat)
	end
	S.State = F.State(Seen, S.T - S.LastSeenAt, S.Identified)
	if S.Heat <= 0 then Local.Finish(P) end
	Local.Publish(P)
	Shared.Changed:Fire(P, S.Tier, S.State)
end

function Local.Serve(P: Player)
	local D = Discipline.GetData(P)
	if not (D and D.Summons and #D.Summons > 0) then return end
	local List = D.Summons
	D.Summons = {}
	for _, Sm in List do
		Discipline.AddViolation(P, Sm.Type, { Witness = `{Sm.Witness} (summons)` })
	end
	Notifications.Notify(P, { Title = `Summons answered`; Text = `Booked, without the hunt on top.`; Kind = `Info`; Duration = 5 })
	Local.Publish(P)
end

function Local.Summons(P: Player)
	local D = Discipline.GetData(P)
	if not (D and D.Summons and #D.Summons > 0) then return end
	local Today = Local.Today()
	for I = #D.Summons, 1, -1 do
		if Today > D.Summons[I].Day + Config.SummonsDays then
			table.remove(D.Summons, I)
			Discipline.AddViolation(P, `SkippedDetention`, { Witness = `Summons ignored` })
		end
	end
	local St = SchoolClock.GetState()
	local InClass = St and St.Segment and St.Segment.Kind == `Class`
	if not InClass and Local.InRoom106(P) then Local.Serve(P) end
	Local.Publish(P)
end

---| API |---

function Shared.Witnessed(P: Player, Misdeed: string, Pos: Vector3?, Witness: string?)
	if not (typeof(P) == `Instance` and P:IsA(`Player`)) or P:GetAttribute(`InMainMenu`) == true then return end
	local S = Local.Get(P)
	S.Misdeed, S.Booked, S.Witness = Misdeed, false, Witness
	if Pos then S.LastSeenPos = Pos end
	S.LastSeenAt = S.T
	if Local.FaceKnown(P) then S.Identified = true end
	Local.AddHeat(P, F.Gain(Misdeed, Local.Context(P)))
	if S.Tier > 0 and S.State == `` then S.State = `Lit` end
	Local.Publish(P)
	Shared.Changed:Fire(P, S.Tier, S.State)
end

-- Discipline.ReportIncident calls this for every report; the return is the bonus for a catch
function Shared.OnReport(Incident: any): number
	local P = Incident and Incident.Suspect
	if not (typeof(P) == `Instance` and P:IsA(`Player`)) then return 0 end
	local S = Local.Get(P)
	if Incident.Caught == true then
		local Bonus = F.Bonus(S.Tier)
		Local.Reset(P)
		Local.Publish(P)
		Shared.Changed:Fire(P, 0, ``)
		return Bonus
	end
	if Incident.Recognized == true then
		Local.Identify(P)
		S.Misdeed, S.Booked, S.Witness = Incident.Type, true, Incident.Witness
		if typeof(Incident.Position) == `Vector3` then S.LastSeenPos = Incident.Position end
		S.LastSeenAt = S.T
		Local.AddHeat(P, F.Gain(Incident.Type, Local.Context(P)))
		if S.Tier > 0 and S.State == `` then S.State = `Lit` end
	elseif S.Tier > 0 then
		-- got away: the heat came with the chase; remember what to book if they were identified
		S.Misdeed, S.Booked = Incident.Type, false
	end
	Local.Publish(P)
	Shared.Changed:Fire(P, S.Tier, S.State)
	return 0
end

function Shared.IsHunted(P: Player): boolean
	local S = States[P]
	return S ~= nil and S.Tier >= Config.HuntTier
end

function Shared.BookType(P: Player): string?
	local S = States[P]
	return if S and S.Misdeed then F.BookType(S.Misdeed) else nil
end

function Shared.Get(P: Player)
	local S = Local.Get(P)
	local D = Discipline.GetData(P)
	local Ctx = Local.Context(P)
	return {
		Heat = math.floor(S.Heat * 100 + 0.5) / 100; Tier = S.Tier; State = S.State; Misdeed = S.Misdeed; Booked = S.Booked;
		Identified = S.Identified; RespondOk = S.RespondOk; Summons = if D and D.Summons then #D.Summons else 0;
		Points = if D then D.Points else nil; Level = if D then D.Level else nil; Night = Ctx.Night; Probation = Ctx.Probation;
	}
end

-- (console 2) the staff console's Bell Tower cards
function Shared.Clear(P: Player)
	Local.Reset(P)
	local D = Discipline.GetData(P)
	if D then D.Summons = {} end
	Local.Publish(P)
	local S = Local.Get(P)
	Shared.Changed:Fire(P, S.Tier, S.State)
end

function Shared.SetHeat(P: Player, Heat: number)
	Heat = math.clamp(tonumber(Heat) or 0, 0, 100)
	if Heat <= 0 then
		-- reset like Clear, but keep the owed summons (only Clear notoriety drops those)
		Local.Reset(P)
		Local.Publish(P)
		Shared.Changed:Fire(P, 0, ``)
		return
	end
	local S = Local.Get(P)
	local Old = S.Tier
	S.Heat = Heat
	S.Tier = F.Tier(Heat)
	-- lowering re-arms the steps above the new bell, so raising again runs them again
	if S.Tier < Config.HuntTier then S.Responded, S.RespondOk = false, nil end
	if S.Tier < Config.ConvergeTier then S.Converged = false end
	if S.Tier < Config.TollTier then S.Tolled = false end
	S.LastSeenAt = S.T
	local Root = Local.Root(P)
	if Root then S.LastSeenPos = Root.Position end
	if S.Tier > Old then Local.Escalate(P) end
	if S.Tier > 0 and S.State == `` then S.State = `Lit` end
	Local.Publish(P)
	Shared.Changed:Fire(P, S.Tier, S.State)
end

function Shared.AddSummons(P: Player, Type: string): boolean
	local D = Discipline.GetData(P)
	if not D then return false end
	if D.Summons and #D.Summons >= Config.SummonsLimit then return false end
	Local.AddSummons(P, Type, `Staff`)
	Local.Publish(P)
	return true
end

---| The probe (Studio only) |---

function Local.Probe(Cmd: string, Name: string?, ...): any
	if Cmd == `Monitors` then
		local HM = Local.HallMonitor()
		local List = if HM and HM.GetMonitors then HM.GetMonitors() else {}
		local Out = {}
		for _, M in List do table.insert(Out, { Name = M.Name; State = M.State; Reason = M.Reason; Target = M.Target }) end
		return Out
	end
	local P = if Name then Players:FindFirstChild(Name) else nil
	if not (P and P:IsA(`Player`)) then return { Error = `no player` } end
	local A = { ... }
	if Cmd == `Manual` then Overrides[P] = { Seen = A[1]; Mods = A[2] } return true end
	if Cmd == `Live` then Overrides[P] = nil return true end
	if Cmd == `Reset` then
		Local.Reset(P)
		Local.Get(P).Identified = false
		local D = Discipline.GetData(P)
		if D then D.Summons = {} D.FaceKnownUntilDay = -1 end
		Local.Publish(P)
		return true
	end
	if Cmd == `Witness` then Shared.Witnessed(P, A[1], nil, `Probe`) return Shared.Get(P) end
	if Cmd == `Report` then
		Discipline.ReportIncident({ Type = A[1]; Suspect = P; Witness = `Probe`; Recognized = A[2] == true; Caught = A[3] == true })
		return Shared.Get(P)
	end
	if Cmd == `Advance` then
		for _ = 1, math.floor((tonumber(A[1]) or 0) / Config.Tick + 0.5) do Local.Step(P, Config.Tick) end
		return Shared.Get(P)
	end
	if Cmd == `Serve` then Local.Serve(P) return Shared.Get(P) end
	if Cmd == `AgeSummons` then
		local D = Discipline.GetData(P)
		for _, Sm in (if D and D.Summons then D.Summons else {}) do Sm.Day -= (tonumber(A[1]) or 2) end
		Local.Summons(P)
		return Shared.Get(P)
	end
	if Cmd == `Get` then return Shared.Get(P) end
	return { Error = `unknown command {Cmd}` }
end

---| Start |---

function Local.WatchCharacter(P: Player, C: Model)
	C:GetAttributeChangedSignal(`Transformation`):Connect(function()
		local Form = C:GetAttribute(`Transformation`)
		-- Transformation is true or a race string while transformed, and nil/false/"" when reverted (UI.Appearance.FormOf)
		if Form == nil or Form == false or Form == `` or Form == `Human` or Form == `Priest` then return end
		local HM = Local.HallMonitor()
		if not (HM and HM.SeenBy) then return end
		local Ok, Seen = pcall(HM.SeenBy, P)
		if Ok and Seen == true then
			local Root = Local.Root(P)
			Shared.Witnessed(P, `Exposure`, if Root then Root.Position else nil, `Hall Monitor`)
		end
	end)
end

function Shared.OnStart()
	local function Join(P: Player)
		if P.Character then Local.WatchCharacter(P, P.Character) end
		P.CharacterAdded:Connect(function(C) Local.WatchCharacter(P, C) end)
	end
	for _, P in Players:GetPlayers() do Join(P) end
	Players.PlayerAdded:Connect(Join)
	Players.PlayerRemoving:Connect(function(P) States[P] = nil Overrides[P] = nil end)

	if RunService:IsStudio() then
		local Probe = ServerStorage:FindFirstChild(`NHNotorietyProbe`) or Instance.new(`BindableFunction`)
		Probe.Name = `NHNotorietyProbe`
		Probe.OnInvoke = function(...)
			local Ok, R = pcall(Local.Probe, ...)
			return if Ok then R else { Error = tostring(R) }
		end
		Probe.Parent = ServerStorage
	end

	task.spawn(function()
		while true do
			task.wait(Config.Tick)
			for _, P in Players:GetPlayers() do
				if not Overrides[P] then
					local Ok, Err = pcall(Local.Step, P, Config.Tick)
					if not Ok then warn(`[Notoriety] {Err}`) end
				end
				pcall(Local.Summons, P)
			end
		end
	end)
end

return Shared
