--[[ (2.30) Broadcast (server). Services.World.Broadcast (docs/expansion/13-Living-School.md §5.1, §5.2): one source of
	content items and three outputs: the PA (all clients, ClockHud), the Gazette (Features.Phone) and the Night FM
	station (Features.Phone remote Station). The PA speaks only of real state and at most once per segment.
	API: Post(Kind, Text, Source?), Items(SinceId?), PA(Text, Emergency?), Station(P), Voice(P), PATestReset() ]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local Config = require(ReplicatedStorage.Config.Broadcast)

local Shared = {}
local Local = {}
local Items = {} :: { any }
local NextId = 0
local LastPASeg = nil :: string?
local Remote: RemoteEvent? = nil
local Rng = Random.new()

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Seg in Path:gmatch(`[^%.]+`) do Node = Node and Node:FindFirstChild(Seg) end
	local Ok, M = pcall(require, Node)
	return if Ok then M else nil
end
local function Clock() return require(ServerScriptService.Services.School.SchoolClock).GetState() end
local function pick(List) return List[Rng:NextInteger(1, #List)] end

function Shared.Post(Kind: string, Text: string, Source: string?)
	NextId += 1
	local It = { Id = NextId; Kind = Kind; Text = Text; T = os.time(); Source = Source }
	table.insert(Items, It)
	while #Items > Config.MaxItems do table.remove(Items, 1) end
	return It
end

function Shared.Items(SinceId: number?)
	local Out = {}
	for _, It in Items do if not SinceId or It.Id > SinceId then table.insert(Out, It) end end
	return Out
end

function Local.SegKey(): string
	local S = Clock()
	return `{S.Day}:{S.SegmentIndex}`
end

function Shared.PA(Text: string, Emergency: boolean?): boolean
	if not Emergency then
		local Key = Local.SegKey()
		if LastPASeg == Key then return false end
		LastPASeg = Key
	end
	Shared.Post(`Announcement`, Text, `PA`)
	if Remote then Remote:FireAllClients({ Kind = `PA`; Text = Text; Chime = Config.Chime }) end
	return true
end
function Shared.PATestReset() LastPASeg = nil end

function Local.OnAir(): boolean
	local H = Clock().Hour or 0
	return H >= Config.StationFrom or H < Config.StationTo
end

function Shared.Station(P: Player)
	local Phone = svc(`Features.Phone`)
	local Last = Phone and Phone.BroadcastRead and Phone.BroadcastRead(P) or 0
	local Out = {}
	for _, It in Items do if It.Kind ~= `Announcement` then table.insert(Out, It) end end
	return { OnAir = Local.OnAir(); Items = Out; LastRead = Last }
end

-- (2.30) Night FM's voices (Config.Voice). Heard[P] = { Key = this night or day, Set = the clips heard in it }
local Heard = {} :: { [Player]: { Key: string, Set: { [string]: boolean } } }
local BigDay = nil :: number? -- the last day with a campus report (a quiet day has none)
local function inHours(H: number, From: number?, To: number?): boolean
	if not From or not To then return true end
	if From <= To then return H >= From and H < To end
	return H >= From or H < To
end
function Shared.Voice(P: Player)
	local S = Clock()
	local H = (S.MinuteOfDay or ((S.Hour or 0) * 60)) / 60
	local OnAir = Local.OnAir()
	local Key = if OnAir then `N{if H >= 12 then S.Day else S.Day - 1}` else `D{S.Day}`
	local Mine = Heard[P]
	if not Mine or Mine.Key ~= Key then Mine = { Key = Key; Set = {} } Heard[P] = Mine end
	local V = Config.Voice
	local function ok(Name: string): boolean
		local C = V[Name]
		return C ~= nil and (typeof(C.Id) == `string` or (C.Id or 0) > 0) and not Mine.Set[Name] and inHours(H, C.From, C.To) and not (C.QuietOnly and BigDay == S.Day)
	end
	local Phone = svc(`Features.Phone`)
	local Pick = nil
	if OnAir and not Mine.Set.Intro then -- the host opens the night: an introduction the first time ever, else a welcome back
		local First = Phone and Phone.Tuned and not Phone.Tuned(P)
		Pick = if First and ok(`FirstTune`) then `FirstTune` elseif not First and ok(`WelcomeBack`) then `WelcomeBack` else nil
		if Pick then
			Mine.Set.Intro = true
			if Pick == `FirstTune` and Phone and Phone.SetTuned then Phone.SetTuned(P) end
		end
	end
	if not Pick and ok(`SignOff`) then Pick = `SignOff` end
	if not Pick then
		local Pool = {}
		for _, Name in { `PSA`, `Hello`, `Quiet`, `Lore1`, `Lore2`, `HallMonitor1`, `Afternoon`, `HallMonitor2` } do if ok(Name) then table.insert(Pool, Name) end end
		if #Pool > 0 then Pick = pick(Pool) end
	end
	if not Pick then return nil end
	Mine.Set[Pick] = true
	local C = V[Pick]
	return { Cue = Pick; Id = C.Id; Len = C.Len; Who = C.Who; Title = C.Title; Gap = Config.VoiceGap }
end
function Shared.UseVoice(Map) for K, Id in Map do if Config.Voice[K] then Config.Voice[K].Id = Id end end end -- tests: local clips (rbxasset://)
function Shared.VoiceTestReset(P: Player?, Quiet: boolean?) if P then Heard[P] = nil end if Quiet ~= nil then BigDay = if Quiet then nil else Clock().Day end end
Players.PlayerRemoving:Connect(function(P) Heard[P] = nil end)

function Local.OnSegment(State)
	local Kind = State.Segment and State.Segment.Kind
	local Lines = Kind and Config.PA[Kind]
	if not Lines then return end
	local Text = pick(Lines)
	Shared.PA(Text)
	if Kind == `BeforeSchool` then
		local Subs = svc(`School.Substitutes`)
		local E = Subs and Subs.Today and Subs.Today() -- today's substitute, if any (School.Substitutes)
		if E and E.Subject then Shared.Post(`Announcement`, (pick(Config.PA.Substitute):gsub("{Subject}", tostring(E.Subject))), `PA`) end
	end
end

function Shared.OnStart()
	local R = ReplicatedStorage:FindFirstChild(`NHBroadcast`) or Instance.new(`RemoteEvent`)
	R.Name = `NHBroadcast`
	R.Parent = ReplicatedStorage
	Remote = R
	task.defer(function()
		local Inc = svc(`World.Incidents`)
		if Inc then
			Inc.On(`*`, function(I)
				if (I.Severity or 1) >= 2 then
					local Ru = svc(`Social.Rumours`)
					local Rm = Ru and Ru.Make(I)
					if Rm then Shared.Post(`IncidentReport`, Ru.Text(Rm), I.Kind) BigDay = Clock().Day end -- (no longer a quiet day)
				end
				if I.Kind == `Scuffle` and I.Rumble then
					local Place = (require(ReplicatedStorage.Config.Rumours).Places[I.Region or ``]) or `the grounds`
					Shared.PA((pick(Config.PA.Rumble):gsub("{Place}", Place)), true)
				end
			end)
		end
	end)
	task.spawn(function()
		local LastSeg, CurfewDay, CallerSeen, TransNight = nil, nil, {}, nil
		while true do
			task.wait(2)
			local Ok, Err = pcall(function()
				local S = Clock()
				local Key = `{S.Day}:{S.SegmentIndex}`
				if Key ~= LastSeg then
					if LastSeg ~= nil then Local.OnSegment(S) end -- not on server start
					LastSeg = Key
				end
				local H = S.Hour or 0
				if H == Config.CurfewHour and CurfewDay ~= S.Day then
					CurfewDay = S.Day
					Shared.PA(pick(Config.PA.Curfew), true)
				end
				-- caller lines: a rumour that has travelled
				local Ru = svc(`Social.Rumours`)
				for _, Rm in (Ru and Ru.Live()) or {} do
					if Rm.Hops >= 2 and not CallerSeen[Rm.Id] then
						CallerSeen[Rm.Id] = true
						Shared.Post(`CallerLine`, `A caller says: "{Ru.Text(Rm)}"`, `Rumours`)
					end
				end
				-- one transmission a night, between 23:00 and 02:00
				local NightId = if H >= 12 then S.Day else S.Day - 1
				if (H >= 23 or H < 2) and TransNight ~= NightId and Rng:NextNumber() < 0.02 then
					TransNight = NightId
					Shared.Post(`Transmission`, pick(Config.Transmissions), `Story`)
				end
			end)
			if not Ok then warn(`[Broadcast] {Err}`) end
		end
	end)
end

return Shared
