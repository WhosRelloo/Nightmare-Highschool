# Broadcast & Curfew (2.30) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The school talks:
- a PA by day
- a live Gazette whose WHISPERS are the school's real rumours
- a Night FM "Midnight Broadcast" station from 21:00 to 03:00

Night FM itself is remade as a modern music app in the school's dress. A curfew runs from 22:00 to 06:00: a night hall
monitor walks the halls, and the Night Custodian keeps the Records Office.

**Architecture:**
- **Content:** `World.Broadcast` is one source with three outputs: the PA (a `RemoteEvent` to clients, drawn on the
  ClockHud with a chime), the Gazette (Phone server), and the Night FM station (a Phone remote).
- **Night FM:** moves out of the 111 KB phone controller into `Controllers.Gui.PhoneRadio`, laid out like the owner's
  reference (a Spotify-style home with chips, a "Tonight" banner and a list; a library; a Now Playing screen with
  generated cover art and a waveform scrubber; a bottom tab bar). It's dressed in the UI kit: ink panels and grain,
  gold titles, crimson and Night FM purple accents.
- **Curfew:** a reason in `School.HallMonitor`, which already knows when a player is inside the building
  (`Local.OnCampus`), with night added to its duty segments.

**Tech Stack:** Roblox Luau in NH Combat Test (placeId 98950102230473), through the Studio MCP and the
`tools/phase4-2300/harness` helpers (`install.py`, `dump.py`, `bridge.py`, `gamevm.py`, `snapshot.lua`, `restore.py`,
`start_play.lua`, `_stand.lua`, `_hall.lua`), run with `python -X utf8 -I`.

**Spec:** `docs/expansion/13-Living-School.md` §5 (2.30), §7, §9. The owner added the Night FM redesign on 2026-11-18,
with a reference image of three Spotify-like phone screens: home, library, now playing.

## Global Constraints

- Build only in **NH Combat Test**. The Map place is read-only.
- **Backup:** before the first edit, copy each script into `ServerStorage.NH_Backup.Phase4_pre_20261118`, named
  `<FullName> (2.29)` when an earlier copy exists.
- **Mirror:** `tools/phase4-2300/pre` (dumped: HallMonitor, Config.Discipline, Phone server, Phone client, ClockHud,
  TestBridge), edit `live/`, and install with `harness/install.py`.
- **Tests:** TestBridge commands, and `gamevm.py` for live state (MCP `execute_luau` has its own module copies).
- **Placeholders:** Luau backtick strings interpolate `{…}`. Templates with `{Placeholders}` are plain `"..."` strings.
  Never put a `--` comment in the middle of a one-line table (2.29 lost a field that way).
- **Test slot 2** only. Restore after every saving test, and check the result:
  - `restore.py` must print `restored`
  - the snapshot must then match `_slot2.json`, except `Discipline.LastDecayDay`
- **UI and art:** existing kit art only (`Theme.Images`, `Theme.Colors`, `Theme.Fonts`, `Kit` components).
  - Icons are text glyphs in the kit fonts (♪ ▶ ❚❚ ⏮ ⏭ ♡ ⟲ ⌂ ⌕), as the phone already uses ♪.
  - No new image uploads. Don't edit `ReplicatedStorage.UI.Components` (the peer session "UI kit" owns it).
- **The frame rate isn't measured** (owner, 2026-11-18).
- **Commits:** `git -c user.name=Rello`, with the Co-Authored-By and Claude-Session lines, on `phase4-living-school`.

---

## File structure

| File (`tools/phase4-2300/live/…`) | Responsibility | New / changed |
|---|---|---|
| `ReplicatedStorage.Config.Broadcast.luau` | PA triggers and wording, station transmissions, limits | new |
| `ServerScriptService.Services.World.Broadcast.luau` | Items, `Post`, the PA (rate limit, triggers from real state), the `NHBroadcast` remote, `Station(P)` | new |
| `StarterPlayer.StarterPlayerScripts.Controllers.Gui.ClockHud.luau` | A PA line (typed, chimed) | changed |
| `ServerScriptService.Services.Features.Phone.luau` | WHISPERS from live rumours, an ON CAMPUS article, `Phone.Liked` and `Phone.Broadcast` saving, `Station`/`SaveLiked`/`StationRead` remotes | changed |
| `StarterPlayer.StarterPlayerScripts.Controllers.Gui.PhoneRadio.luau` | The new Night FM app: home, library, now playing, station, tab bar | new |
| `StarterPlayer.StarterPlayerScripts.Controllers.Gui.Phone.luau` | `Local.Radio` hands over to PhoneRadio, and the refresh loop calls `PhoneRadio.Tick` | changed |
| `ReplicatedStorage.Config.Discipline.luau` | `HallMonitor.DutyKinds.Night = true`, `Curfew = { From = 22, To = 6 }` | changed |
| `ServerScriptService.Services.School.HallMonitor.luau` | `IsAfterHours`, the `Curfew` reason, its lines, exemptions | changed |
| `ServerScriptService.Services.Studio.TestBridge.luau` | `BroadcastTest`, `CurfewTest` | changed |

---

### Task 1: World.Broadcast and the PA

**Files:** create `Config.Broadcast` and `World.Broadcast`; modify `Controllers.Gui.ClockHud` and the TestBridge.

**Interfaces:**
- Produces:
  - **An item:** `{ Id: number, Kind: "Announcement" | "IncidentReport" | "CallerLine" | "Transmission", Text: string, T: number, Source: string? }`
  - `Broadcast.Post(Kind, Text, Source?) -> Item` (the rolling list keeps 40)
  - `Broadcast.Items(SinceId?) -> {Item}`
  - `Broadcast.PA(Text, Emergency?) -> boolean`. It fires `ReplicatedStorage.NHBroadcast` to all clients as
    `{ Kind = "PA", Text }`. It returns false if a non-emergency PA was already made in this segment.
  - `Broadcast.Station(P) -> { OnAir: boolean, Items: {Item}, LastRead: number }`
  - `Broadcast.PATestReset()`
- **Triggers** (from real state only):
  - **On segment change:**
    - Before School: the morning, plus a substitute today if `School.Substitutes.Upcoming()` is for today
    - Lunch
    - After School: dismissed, plus a match tonight if a club match is scheduled, read from `Sports.Matches`
      (otherwise none)
  - **At 22:00:** curfew in force (an emergency, not counted against the limit).
  - **From incidents:** a `Scuffle` with `Rumble = true` becomes a PA ("Students are to clear the …"), as an
    emergency. Every incident with `Severity >= 2` also becomes an `IncidentReport` item (no PA).
  - **From rumours:** a rumour that reaches 2 or more hops becomes a `CallerLine` item, once.
  - **Transmissions:** one per in-game night, at a random time between 23:00 and 02:00, from
    `Config.Broadcast.Transmissions`.

- [ ] **Step 1: Write the failing test.** Add to TestBridge:

```lua
-- (2.30) the broadcast: items roll at 40, a PA is limited to one per segment (emergencies aside), the station is on air at night
function Commands.BroadcastTest(PlayerName: string)
	local B = require(game:GetService(`ServerScriptService`).Services.World.Broadcast)
	local Player = Players:FindFirstChild(PlayerName)
	B.PATestReset()
	for I = 1, 45 do B.Post(`IncidentReport`, `Report {I}`) end
	local All = B.Items()
	local First = B.PA(`Test one.`)
	local Second = B.PA(`Test two.`)
	local Emergency = B.PA(`Emergency.`, true)
	B.PATestReset()
	local St = B.Station(Player)
	return { Count = #All; Newest = All[#All].Text; Oldest = All[1].Text; FirstPA = First; SecondPA = Second; EmergencyPA = Emergency;
		StationHasItems = #St.Items > 0; OnAirIsBool = typeof(St.OnAir) == `boolean` }
end
```

  Expected before the code: an error (no `World.Broadcast`).

- [ ] **Step 2: `Config.Broadcast`.** PA lines are plain strings. `{Subject}`, `{Day}` and `{Place}` are filled by the
  service.

```lua
--[[ (2.30) Broadcast wording (World.Broadcast). The PA speaks only of real state (doc 13 §5.2), at most once per school
	segment (emergencies aside). The station (Night FM "Midnight Broadcast") is on air 21:00 to 03:00. ]]
return {
	PA = {
		BeforeSchool = { "Good morning, students. Homeroom begins at eight. Do not be late; the register is kept." };
		Substitute = { "A substitute will cover {Subject} today. Mind your manners." };
		Lunch = { "The lunch period has begun. Mrs. Okada's stand is open by the west doors." };
		AfterSchool = { "Classes are dismissed. Clubs meet now. The building closes at ten." };
		Curfew = { "Curfew is now in force. All students to the dorms. The halls are patrolled." };
		Rumble = { "Students are to clear {Place} at once. Staff are on their way." };
	};
	Transmissions = {
		"...and the roll is read. Holt. Mira Holt. ...No answer. No answer. No answer.",
		"A voice on the static, very calm: 'Answer the bell, and you will be kept.'",
		"Somewhere under the music, a register being read. One name too many.",
		"Static, and a girl humming the school hymn a beat behind the choir.",
	};
	Kickers = { Announcement = `ANNOUNCEMENT`; IncidentReport = `CAMPUS REPORT`; CallerLine = `CALLER LINE`; Transmission = `TRANSMISSION` };
	MaxItems = 40;
	StationFrom = 21; StationTo = 3; -- hours (wraps past midnight)
	CurfewHour = 22;
	Chime = `rbxassetid://9114058995`; -- the desk bell (the kit's Confirm and Moments' Chime)
}
```

- [ ] **Step 3: `World.Broadcast`.** The module:

```lua
--[[ (2.30) Broadcast (server). Services.World.Broadcast (docs/expansion/13-Living-School.md §5.1, §5.2): one source of
	content items and three outputs: the PA (all clients, ClockHud), the Gazette (Features.Phone) and the Night FM
	station (Features.Phone remote Station). The PA speaks only of real state and at most once per segment.
	API: Post(Kind, Text, Source?), Items(SinceId?), PA(Text, Emergency?), Station(P), PATestReset() ]]
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

function Local.OnSegment(State)
	local Kind = State.Segment and State.Segment.Kind
	local Lines = Kind and Config.PA[Kind]
	if not Lines then return end
	local Text = pick(Lines)
	Shared.PA(Text)
	if Kind == `BeforeSchool` then
		local Subs = svc(`School.Substitutes`)
		local E = Subs and Subs.Upcoming and Subs.Upcoming()
		if E and E.Today then Shared.Post(`Announcement`, (pick(Config.PA.Substitute):gsub("{Subject}", tostring(E.Subject))), `PA`) end
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
					if Rm then Shared.Post(`IncidentReport`, Ru.Text(Rm), I.Kind) end
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
```

  **Check:** `School.Substitutes.Upcoming()` returns `{ Subject, Weekday, ... }` (Fortune's `Hint.Stranger` uses
  it). If it has no `Today` field, compare `E.Weekday` with today's weekday from `SchoolClock.GetState()`, the way
  Fortune's `WEEKDAYS` does.

- [ ] **Step 4: The PA on the ClockHud.**
  - **The label:** in `Local.CreateGui`, add `PA = Local.Label(Lines, \`PA\`, 0, 13, true);` to the labels table
    (order 0 puts it on top). Set `Labels.PA.Visible = false`, and `TextWrapped`, with a gold colour (`KitTheme.Colors.Gold`).
  - **Show it:** add `Shared.ShowPA(Text)`, which plays the chime, types the line in, holds, then fades:

```lua
-- (2.30) the PA (World.Broadcast): a chime, the line typed in, held, then gone
local PAToken = 0
function Shared.ShowPA(Text: string, Chime: string?)
	if not (Ui and Ui.Labels and Ui.Labels.PA) then return end
	PAToken += 1
	local Mine = PAToken
	local L = Ui.Labels.PA
	pcall(function()
		local S = Instance.new(`Sound`)
		S.SoundId = Chime or `rbxassetid://9114058995` S.Volume = 0.3
		S.Parent = game:GetService(`SoundService`) S:Play()
		game:GetService(`Debris`):AddItem(S, 3)
	end)
	L.Visible = true
	L.Text = `\u{1F4E2} `
	for I = 1, #Text do
		if PAToken ~= Mine then return end
		L.Text = `\u{1F4E2} ` .. Text:sub(1, I)
		task.wait(0.025)
	end
	task.wait(math.clamp(#Text * 0.06, 4, 10))
	if PAToken == Mine then L.Visible = false end
end
```

  - **Listen:** in `Shared.OnStart`, connect
    `ReplicatedStorage:WaitForChild(\`NHBroadcast\`, 30).OnClientEvent` to `task.spawn(Shared.ShowPA, M.Text, M.Chime)`
    when `M.Kind == \`PA\``.
  - **Check names:** read how the module stores its GUI. The labels table is created in `CreateGui` as
    `{ Time = …, Period = … }`. Use that table's real name (`Labels` or `Ui.Labels`) in `ShowPA`.

- [ ] **Step 5: Install and run the test.**
  - Install Config.Broadcast, Broadcast, ClockHud and the TestBridge, start Play, and run `bridge.py BroadcastTest '$P'`.
  - Expected: `Count 40`, `Newest "Report 45"`, `Oldest "Report 6"`, `FirstPA true`, `SecondPA false`,
    `EmergencyPA true`, `StationHasItems true`, `OnAirIsBool true`.
  - **Live:** `SetTime "11:24"`, wait for Lunch at 11:25, and screenshot the ClockHud while the PA line types
    (`review/pa_lunch.jpg`).

- [ ] **Step 6: Commit** `2.30 (1/7): World.Broadcast and the PA`.

---

### Task 2: The Gazette reads the school

**Files:** modify `Features.Phone` (server).

- [ ] **Step 1: The failing check.** From `gamevm.py`, emit a `Scene` incident (Locker) with a witness. Wait 1 s, then
  call `Phone.Gazette(P)`. Expected now: the WHISPERS article holds the old fixed strings, and there's no ON CAMPUS
  article.
- [ ] **Step 2: Live WHISPERS.** Replace the WHISPERS `table.insert` (`Body = RUMOURS[...]`) with:

```lua
	-- rumours (2.30: the school's live rumours, Social.Rumours; the fixed strings when the halls are quiet)
	local Ru = svc(`Social.Rumours`)
	local Live = (Ru and Ru.Live()) or {}
	local Heard = {}
	for K = #Live, math.max(1, #Live - 2), -1 do table.insert(Heard, `"{Ru.Text(Live[K])}"`) end
	table.insert(Articles, { Kicker = `WHISPERS`; Title = `Heard in the halls`;
		Body = if #Heard > 0 then table.concat(Heard, `\n\n`) .. `\n\n<i>Whether any of it is true is another matter.</i>`
			else RUMOURS[Day % #RUMOURS + 1] .. `\n\n` .. RUMOURS[(Day + 3) % #RUMOURS + 1] })
	-- (2.30) today's campus reports (World.Broadcast)
	local Bc = svc(`World.Broadcast`)
	local Reports = {}
	for _, It in (Bc and Bc.Items()) or {} do if It.Kind == `IncidentReport` then table.insert(Reports, It.Text) end end
	if #Reports > 0 then
		local Last = {}
		for K = #Reports, math.max(1, #Reports - 2), -1 do table.insert(Last, Reports[K]) end
		table.insert(Articles, { Kicker = `ON CAMPUS`; Title = `Today at school`; Body = table.concat(Last, `\n\n`) })
	end
```

  **Check:** Phone server has a `svc` helper. If not, add one as in Rumours (a `require` of
  `ServerScriptService.Services` by dotted path).

- [ ] **Step 3: Install and run the check again.** Expected: WHISPERS quotes the Locker rumour, and ON CAMPUS lists a
  report (Severity 2 or more; the Locker scene's Missed outcome is Size 3).
- [ ] **Step 4: Commit** `2.30 (2/7): the Gazette's whispers are the school's real rumours`.

---

### Task 3: Night FM, remade (with the Midnight Broadcast station)

The owner's reference: three phone screens.
1. **Home:** "Hello, Alex", round search and bell buttons, chips (All, New Artists…), a "For you" banner with art and
   a Start Listening button, and a "Popular" list of rows (cover, title, artist, round play button).
2. **Library:** "Your library", chips, rows with durations and play buttons.
3. **Now playing:** back, "Now Playing", a big cover with the neighbours peeking either side, the artist and title, a
   heart, a waveform scrubber with times, and loop, prev, a big pause, next and queue.

All three have a dark purple gradient and a floating pill tab bar (home, music, settings). **Our theme:** ink panels
with the kit's grain, gold titles (`Fonts.Title`), crimson-to-purple gradients, the kit's knob and orb art behind the
round buttons, and covers made from kit emblems.

**Files:**
- Create: `StarterPlayer.StarterPlayerScripts.Controllers.Gui.PhoneRadio.luau`
- Modify:
  - `Controllers.Gui.Phone`: `Local.Radio`, and the refresh loop's `Ui.Radio` block
  - `Features.Phone` server: `Sanitize` gains `Liked` and `Broadcast`; new remotes `SaveLiked`, `Station`,
    `StationRead`; and `BroadcastRead(P)`

**Interfaces:**
- **The handoff from Phone:**

  ```lua
  PhoneRadio.Open({ App = Ui.App, Music = Music, State = State, Play = Local.Play, Call = Local.Call, Home = Local.ShowHome, Kit = Kit, Theme = Theme })
  PhoneRadio.Tick()   -- every 0.25 s while the app is open
  ```

- **Server:** `Phone.BroadcastRead(P) -> number`, plus the remotes `Station` (RF) → `Broadcast.Station(P)`,
  `StationRead` (RF id), and `SaveLiked` (RF list).

- [ ] **Step 1: Server save fields and remotes** (`Features.Phone`).
  - **In `Shared.Sanitize`:**
    - `Out.Liked = {}`, filled from `Raw.Liked`: up to 30 positive integers below 1e15
    - `Out.Broadcast = 0`, from `Raw.Broadcast` if it's a number
  - **Add:**

```lua
-- (2.30) Night FM: liked tracks and the station's last read item (saved per slot)
function Shared.SaveLiked(P: Player, List: any): boolean
	if typeof(List) ~= `table` then return false end
	local Ph = Local.Get(P)
	if not Ph then return false end
	local Clean = {}
	for _, V in List do
		local N = tonumber(V)
		if N and N > 0 and N % 1 == 0 and N < 1e15 and #Clean < 30 and not table.find(Clean, N) then table.insert(Clean, N) end
	end
	Ph.Liked = Clean
	Local.Save(P, Ph)
	return true
end
function Shared.BroadcastRead(P: Player): number
	local Ph = Local.Get(P)
	return Ph and Ph.Broadcast or 0
end
function Shared.StationRead(P: Player, Id: any): boolean
	local Ph = Local.Get(P)
	local N = tonumber(Id)
	if not (Ph and N) then return false end
	Ph.Broadcast = math.max(Ph.Broadcast or 0, math.floor(N))
	Local.Save(P, Ph)
	return true
end
```

  - **Remotes:** in `OnStart`, beside `SaveRecent`, add `rf(\`SaveLiked\`)`, `rf(\`Station\`)` and `rf(\`StationRead\`)`,
    with `OnServerInvoke`s that call these, and `Station` calling
    `require(ServerScriptService.Services.World.Broadcast).Station(P)`. Use the module's existing rate-limit wrapper
    (`cached`, or the per-remote `LastCall` pattern) for `Station`.
  - **State:** `Shared.State(P)` must include `Liked` (and `Recent` as now).

- [ ] **Step 2: Write `PhoneRadio`.** The whole module:

```lua
--[[ (2.30) PhoneRadio (client). Controllers.Gui.PhoneRadio: Night FM, remade as a music app in the school's dress
	(the owner's reference, 2026-11-18: a Spotify-like home, library and now-playing, with a floating tab bar).
	Tabs: Home (greeting, chips, the Midnight Broadcast banner, recent tracks), Library (saved + recent, add by ID),
	Station (Midnight Broadcast, 21:00-03:00: caller lines, campus reports, transmissions; World.Broadcast), and the
	Now Playing sheet (cover, title, creator, like, waveform scrubber, loop / prev / play / next / volume).
	Art: only the kit's (Theme.Images emblems on gradients for covers, Knob / OrbRing behind round buttons, PanelBg grain).
	Driven by Controllers.Gui.Phone: Open(Ctx), Tick(). ]]
local Players = game:GetService(`Players`)
local MarketplaceService = game:GetService(`MarketplaceService`)
local UserInputService = game:GetService(`UserInputService`)

local Shared = {}
local Ctx = nil
local Ui = nil
local Tab = `Home`
local Chip = `All`
local Info = {} :: { [number]: { Title: string, Creator: string } }

local PURPLE = Color3.fromRGB(150, 95, 230)
local PURPLE_DEEP = Color3.fromRGB(46, 22, 78)
local COVERS = { `IconAppRadio`, `IconCandle`, `Crest`, `Seal`, `IconBannerFullMoon`, `IconBannerBlueMoon`, `IconBannerCrimsonMoon`, `IconNib`, `Bell`, `IconCardBack` }
local GRADS = {
	{ Color3.fromRGB(120, 60, 200), Color3.fromRGB(150, 30, 60) }, { Color3.fromRGB(70, 40, 150), Color3.fromRGB(20, 10, 40) },
	{ Color3.fromRGB(170, 70, 140), Color3.fromRGB(60, 20, 90) }, { Color3.fromRGB(90, 30, 40), Color3.fromRGB(150, 95, 230) },
}

local function new(Class: string, Props, Parent: Instance?)
	local I = Instance.new(Class)
	for K, V in Props do I[K] = V end
	if Parent then I.Parent = Parent end
	return I
end
local function corner(I, R) new(`UICorner`, { CornerRadius = if R then UDim.new(0, R) else UDim.new(1, 0) }, I) end
local function T() return Ctx.Theme end
local function label(Parent, Text, Size, Props)
	local L = new(`TextLabel`, { BackgroundTransparency = 1; Text = Text; TextSize = Size; Font = T().Fonts.Body; TextColor3 = T().Colors.Text;
		TextXAlignment = Enum.TextXAlignment.Left; RichText = true; TextTruncate = Enum.TextTruncate.AtEnd }, Parent)
	for K, V in Props or {} do L[K] = V end
	return L
end
local function hash(N: number): number return (N * 2654435761) % 4294967296 end

local function titleOf(Id: number): (string, string)
	local I = Info[Id]
	if I then return I.Title, I.Creator end
	Info[Id] = { Title = `Track {Id}`; Creator = `Night FM` }
	task.spawn(function()
		local Ok, P = pcall(MarketplaceService.GetProductInfo, MarketplaceService, Id, Enum.InfoType.Asset)
		if Ok and P then Info[Id] = { Title = P.Name or `Track {Id}`; Creator = (P.Creator and P.Creator.Name) or `Unknown` } end
	end)
	return Info[Id].Title, Info[Id].Creator
end

-- a cover: one of the kit's emblems on a gradient, picked by the track id (the same track, the same cover)
local function cover(Parent, Id: number, Size: number)
	local H = hash(Id)
	local G = GRADS[H % #GRADS + 1]
	local F = new(`Frame`, { BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; Size = UDim2.fromOffset(Size, Size) }, Parent)
	corner(F, math.floor(Size / 6))
	new(`UIGradient`, { Rotation = 35 + H % 90; Color = ColorSequence.new(G[1], G[2]) }, F)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = T().Images.Glow; ImageTransparency = 0.55; Size = UDim2.fromScale(1, 1) }, F)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = T().Images[COVERS[(H // 7) % #COVERS + 1]]; ScaleType = Enum.ScaleType.Fit;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(0.62, 0.62) }, F)
	return F
end

-- a round button on the kit's orb ring, with a glyph
local function roundBtn(Parent, Glyph: string, Size: number, Filled: boolean?, Fn)
	local B = new(`TextButton`, { Text = Glyph; Font = T().Fonts.Title; TextSize = math.floor(Size * 0.42); TextColor3 = if Filled then Color3.new(1, 1, 1) else T().Colors.Gold;
		BackgroundColor3 = if Filled then PURPLE else T().Colors.Ink; BackgroundTransparency = if Filled then 0 else 0.25; AutoButtonColor = true; Size = UDim2.fromOffset(Size, Size) }, Parent)
	corner(B)
	new(`UIStroke`, { Color = if Filled then Color3.fromRGB(210, 180, 255) else T().Colors.GoldDeep; Thickness = 1; Transparency = 0.35 }, B)
	if Filled then new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new(Color3.fromRGB(175, 120, 255), Color3.fromRGB(110, 50, 190)) }, B) end
	B.Activated:Connect(function() pcall(Ctx.Kit.PlaySound, `Tick`, 0.5, 1.3) Fn() end)
	return B
end

local function chip(Parent, Text: string, Active: boolean, Fn)
	local B = new(`TextButton`, { Text = Text; Font = T().Fonts.Body; TextSize = 13; TextColor3 = if Active then Color3.new(1, 1, 1) else T().Colors.TextDim;
		BackgroundColor3 = if Active then PURPLE else T().Colors.Ink; BackgroundTransparency = if Active then 0 else 0.3; AutomaticSize = Enum.AutomaticSize.X; Size = UDim2.fromOffset(0, 28) }, Parent)
	corner(B)
	new(`UIPadding`, { PaddingLeft = UDim.new(0, 14); PaddingRight = UDim.new(0, 14) }, B)
	new(`UIStroke`, { Color = if Active then Color3.fromRGB(210, 180, 255) else T().Colors.IronDim; Transparency = 0.4 }, B)
	B.Activated:Connect(Fn)
	return B
end

-- a track row: cover, title, creator, a round play button (the reference's list)
local function row(Parent, Id: number, Order: number)
	local R = new(`TextButton`, { Text = ``; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 52); LayoutOrder = Order }, Parent)
	local C = cover(R, Id, 44) C.Position = UDim2.fromOffset(0, 4)
	local Title, By = titleOf(Id)
	label(R, Title, 15, { Font = T().Fonts.Title; Position = UDim2.fromOffset(54, 7); Size = UDim2.new(1, -110, 0, 18) })
	label(R, By, 12, { TextColor3 = T().Colors.TextDim; Position = UDim2.fromOffset(54, 27); Size = UDim2.new(1, -110, 0, 16) })
	local Playing = Ctx.Music.Id == Id and Ctx.Music.Sound and Ctx.Music.Sound.IsPlaying
	local B = roundBtn(R, if Playing then `\u{275A}\u{275A}` else `\u{25B6}`, 34, false, function()
		if Ctx.Music.Id == Id and Ctx.Music.Sound then
			if Ctx.Music.Sound.IsPlaying then Ctx.Music.Sound:Pause() else Ctx.Music.Sound:Resume() end
		else Ctx.Play(Id) end
		Shared.Render()
	end)
	B.Position = UDim2.new(1, -38, 0, 9)
	R.Activated:Connect(function() if Ctx.Music.Id ~= Id then Ctx.Play(Id) end Shared.NowPlaying() end)
	return R
end

local function body(Parent)
	local S = new(`ScrollingFrame`, { BackgroundTransparency = 1; BorderSizePixel = 0; Position = UDim2.fromOffset(0, 0); Size = UDim2.new(1, 0, 1, -74);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 2; ScrollBarImageColor3 = T().Colors.IronDim }, Parent)
	new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 8) }, S)
	new(`UIPadding`, { PaddingLeft = UDim.new(0, 16); PaddingRight = UDim.new(0, 16); PaddingTop = UDim.new(0, 12); PaddingBottom = UDim.new(0, 12) }, S)
	return S
end

local function heading(Parent, Text, Order, Right, RightFn)
	local F = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 24); LayoutOrder = Order }, Parent)
	label(F, Text, 17, { Font = T().Fonts.Title; TextColor3 = T().Colors.Gold; Size = UDim2.new(1, -80, 1, 0) })
	if Right then
		local B = new(`TextButton`, { Text = Right .. ` \u{203A}`; Font = T().Fonts.Body; TextSize = 12; TextColor3 = T().Colors.TextDim; BackgroundTransparency = 1;
			AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 0); Size = UDim2.fromOffset(80, 24); TextXAlignment = Enum.TextXAlignment.Right }, F)
		B.Activated:Connect(RightFn)
	end
end

function Shared.Home(Parent)
	local S = body(Parent)
	-- greeting with avatar, search and bell (the reference's header)
	local Head = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 86); LayoutOrder = 1 }, S)
	local Av = new(`ImageLabel`, { BackgroundColor3 = T().Colors.Ink; Size = UDim2.fromOffset(40, 40) }, Head)
	corner(Av) new(`UIStroke`, { Color = T().Colors.Gold; Transparency = 0.3 }, Av)
	task.spawn(function()
		local Ok, Url = pcall(Players.GetUserThumbnailAsync, Players, Players.LocalPlayer.UserId, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size100x100)
		if Ok then Av.Image = Url end
	end)
	local B1 = roundBtn(Head, `\u{2315}`, 36, false, function() Tab = `Library` Shared.Render() end) B1.Position = UDim2.new(1, -82, 0, 2)
	local B2 = roundBtn(Head, `\u{1F514}`, 36, false, function() Tab = `Station` Shared.Render() end) B2.Position = UDim2.new(1, -38, 0, 2)
	local Hour = tonumber(os.date(`%H`)) or 20
	local Hi = if Hour < 12 then `Good morning` elseif Hour < 18 then `Good afternoon` else `Good evening`
	label(Head, `{Hi}, {Players.LocalPlayer.DisplayName}`, 22, { Font = T().Fonts.Title; Position = UDim2.fromOffset(0, 50); Size = UDim2.new(1, 0, 0, 30) })
	-- chips
	local Chips = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 30); LayoutOrder = 2 }, S)
	new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; Padding = UDim.new(0, 6) }, Chips)
	for _, Name in { `All`, `Recent`, `Saved`, `Station` } do
		chip(Chips, Name, Chip == Name, function()
			if Name == `Station` then Tab = `Station` else Chip = Name end
			Shared.Render()
		end)
	end
	-- the banner: tonight on Night FM (the reference's "For you" card)
	heading(S, `Tonight`, 3)
	local St = Ctx.Station or { OnAir = false }
	local Banner = new(`Frame`, { BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; Size = UDim2.new(1, 0, 0, 132); LayoutOrder = 4 }, S)
	corner(Banner, 16)
	new(`UIGradient`, { Rotation = 20; Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(110, 50, 190)), ColorSequenceKeypoint.new(1, Color3.fromRGB(140, 30, 60)) }) }, Banner)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = T().Images.PanelBg; ImageTransparency = 0.85; ScaleType = Enum.ScaleType.Crop; Size = UDim2.fromScale(1, 1) }, Banner)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = T().Images.IconAppRadio; ScaleType = Enum.ScaleType.Fit; AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, -10, 0.5, 0); Size = UDim2.fromOffset(104, 104) }, Banner)
	label(Banner, `Midnight Broadcast`, 18, { Font = T().Fonts.Title; Position = UDim2.fromOffset(14, 12); Size = UDim2.new(1, -130, 0, 22) })
	label(Banner, if St.OnAir then `On air now. Caller lines, campus reports, and things on the static.` else `Off air until 9 PM. The school talks after dark.`, 12,
		{ TextWrapped = true; TextTruncate = Enum.TextTruncate.None; TextColor3 = Color3.fromRGB(235, 225, 245); Position = UDim2.fromOffset(14, 38); Size = UDim2.new(1, -130, 0, 46) })
	local Go = new(`TextButton`, { Text = if St.OnAir then `Tune in` else `See tonight`; Font = T().Fonts.Title; TextSize = 13; TextColor3 = Color3.new(1, 1, 1);
		BackgroundColor3 = Color3.new(1, 1, 1); BackgroundTransparency = 0.82; Position = UDim2.fromOffset(14, 92); Size = UDim2.fromOffset(110, 28) }, Banner)
	corner(Go) new(`UIStroke`, { Color = Color3.new(1, 1, 1); Transparency = 0.5 }, Go)
	Go.Activated:Connect(function() Tab = `Station` Shared.Render() end)
	-- the list
	local Ids = if Chip == `Saved` then (Ctx.State.Liked or {}) else (Ctx.State.Recent or {})
	heading(S, if Chip == `Saved` then `Saved` else `Recently played`, 5, `Show all`, function() Tab = `Library` Shared.Render() end)
	if #Ids == 0 then label(S, `<i>Nothing here yet. Add a track by its audio ID in your library.</i>`, 13, { TextWrapped = true; TextTruncate = Enum.TextTruncate.None; TextColor3 = T().Colors.TextDim; Size = UDim2.new(1, 0, 0, 34); LayoutOrder = 6 }) end
	for K, Id in Ids do if K <= 6 then row(S, Id, 10 + K) end end
end

function Shared.Library(Parent)
	local S = body(Parent)
	label(S, `Your library`, 22, { Font = T().Fonts.Title; Size = UDim2.new(1, 0, 0, 30); LayoutOrder = 1 })
	local Chips = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 30); LayoutOrder = 2 }, S)
	new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; Padding = UDim.new(0, 6) }, Chips)
	for _, Name in { `All`, `Saved`, `Recent` } do chip(Chips, Name, Chip == Name, function() Chip = Name Shared.Render() end) end
	local Input, Api = Ctx.Kit.SearchBar({ placeholder = `Add a track: audio ID, then Enter`; Size = UDim2.new(1, 0, 0, 38); LayoutOrder = 3; Parent = S;
		onSubmit = function(Text) local N = tonumber((Text or ``):match(`%d+`)) if N then Ctx.Play(N) Shared.NowPlaying() end end })
	local Seen, Ids = {}, {}
	local function add(List) for _, Id in List or {} do if not Seen[Id] then Seen[Id] = true table.insert(Ids, Id) end end end
	if Chip ~= `Recent` then add(Ctx.State.Liked) end
	if Chip ~= `Saved` then add(Ctx.State.Recent) end
	if #Ids == 0 then label(S, `<i>Nothing yet.</i>`, 13, { TextColor3 = T().Colors.TextDim; Size = UDim2.new(1, 0, 0, 20); LayoutOrder = 4 }) end
	for K, Id in Ids do row(S, Id, 10 + K) end
end

function Shared.Station(Parent)
	local S = body(Parent)
	local St = Ctx.Station or { OnAir = false; Items = {}; LastRead = 0 }
	label(S, `Midnight Broadcast`, 22, { Font = T().Fonts.Title; Size = UDim2.new(1, 0, 0, 30); LayoutOrder = 1 })
	local Badge = new(`TextLabel`, { Text = if St.OnAir then `\u{25CF}  ON AIR` else `OFF AIR  \u{00B7}  9 PM to 3 AM`; Font = T().Fonts.Title; TextSize = 12;
		TextColor3 = Color3.new(1, 1, 1); BackgroundColor3 = if St.OnAir then T().Colors.Crimson else T().Colors.Iron; AutomaticSize = Enum.AutomaticSize.X;
		Size = UDim2.fromOffset(0, 24); LayoutOrder = 2 }, S)
	corner(Badge) new(`UIPadding`, { PaddingLeft = UDim.new(0, 12); PaddingRight = UDim.new(0, 12) }, Badge)
	local Kick = { Announcement = `ANNOUNCEMENT`; IncidentReport = `CAMPUS REPORT`; CallerLine = `CALLER LINE`; Transmission = `TRANSMISSION` }
	local Items = St.Items or {}
	if #Items == 0 then label(S, `<i>Quiet tonight. Nothing on the line yet.</i>`, 13, { TextColor3 = T().Colors.TextDim; Size = UDim2.new(1, 0, 0, 20); LayoutOrder = 3 }) end
	local Newest = 0
	for K = #Items, 1, -1 do
		local It = Items[K]
		Newest = math.max(Newest, It.Id)
		local Card = new(`Frame`, { BackgroundColor3 = T().Colors.Ink; BackgroundTransparency = 0.3; AutomaticSize = Enum.AutomaticSize.Y; Size = UDim2.new(1, 0, 0, 0); LayoutOrder = 100 - K + 10 }, S)
		corner(Card, 12) new(`UIStroke`, { Color = if It.Kind == `Transmission` then T().Colors.Crimson else T().Colors.IronDim; Transparency = 0.4 }, Card)
		new(`UIPadding`, { PaddingLeft = UDim.new(0, 12); PaddingRight = UDim.new(0, 12); PaddingTop = UDim.new(0, 8); PaddingBottom = UDim.new(0, 10) }, Card)
		new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 4) }, Card)
		label(Card, (if It.Id > (St.LastRead or 0) then `<font color="#{T().Colors.Gold:ToHex()}">\u{25CF} NEW</font>  ` else ``) .. (Kick[It.Kind] or It.Kind), 11,
			{ Font = T().Fonts.Title; TextColor3 = Color3.fromRGB(200, 170, 255); Size = UDim2.new(1, 0, 0, 14); LayoutOrder = 1 })
		label(Card, It.Text, 14, { TextWrapped = true; TextTruncate = Enum.TextTruncate.None; AutomaticSize = Enum.AutomaticSize.Y; Size = UDim2.new(1, 0, 0, 18); LayoutOrder = 2;
			Font = if It.Kind == `Transmission` then T().Fonts.Title else T().Fonts.Body })
	end
	if Newest > (St.LastRead or 0) then task.spawn(Ctx.Call, `StationRead`, Newest) end
end

-- the now playing sheet (the reference's third screen)
function Shared.NowPlaying()
	if not Ui then return end
	if Ui.Sheet then Ui.Sheet:Destroy() end
	local Id = Ctx.Music.Id
	if not Id then return end
	local Sheet = new(`Frame`, { Name = `NowPlaying`; BackgroundColor3 = Color3.new(1, 1, 1); Size = UDim2.fromScale(1, 1); ZIndex = 20 }, Ui.Root)
	new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(80, 40, 140)), ColorSequenceKeypoint.new(0.6, Color3.fromRGB(40, 20, 70)), ColorSequenceKeypoint.new(1, Color3.fromRGB(20, 12, 30)) }) }, Sheet)
	Ui.Sheet = Sheet
	local Back = roundBtn(Sheet, `\u{2039}`, 36, false, function() Sheet:Destroy() Ui.Sheet = nil end) Back.Position = UDim2.fromOffset(14, 10)
	label(Sheet, `Now Playing`, 14, { TextColor3 = T().Colors.TextDim; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(60, 10); Size = UDim2.new(1, -120, 0, 36) })
	-- the neighbours peek in from the sides, as in the reference
	local Recent = Ctx.State.Recent or {}
	local At = table.find(Recent, Id) or 1
	local Prev, Next = Recent[At + 1], Recent[At - 1]
	if Prev then local P = cover(Sheet, Prev, 170) P.Position = UDim2.new(0, -130, 0, 82) P.BackgroundTransparency = 0.4 end
	if Next then local N = cover(Sheet, Next, 170) N.Position = UDim2.new(1, -40, 0, 82) N.BackgroundTransparency = 0.4 end
	local Big = cover(Sheet, Id, 220) Big.AnchorPoint = Vector2.new(0.5, 0) Big.Position = UDim2.new(0.5, 0, 0, 62)
	new(`UIStroke`, { Color = Color3.fromRGB(210, 180, 255); Transparency = 0.5; Thickness = 1 }, Big)
	local Title, By = titleOf(Id)
	label(Sheet, By, 13, { TextColor3 = T().Colors.TextDim; Position = UDim2.fromOffset(22, 298); Size = UDim2.new(1, -90, 0, 16) })
	local TitleL = label(Sheet, Title, 22, { Font = T().Fonts.Title; Position = UDim2.fromOffset(22, 316); Size = UDim2.new(1, -90, 0, 28) })
	local Liked = table.find(Ctx.State.Liked or {}, Id) ~= nil
	local Heart Heart = roundBtn(Sheet, if Liked then `\u{2665}` else `\u{2661}`, 40, false, function()
		local L = table.clone(Ctx.State.Liked or {})
		local K = table.find(L, Id)
		if K then table.remove(L, K) else table.insert(L, 1, Id) end
		Ctx.State.Liked = L
		Heart.Text = if K then `\u{2661}` else `\u{2665}`
		Heart.TextColor3 = if K then T().Colors.Gold else T().Colors.Crimson
		task.spawn(Ctx.Call, `SaveLiked`, L)
	end)
	Heart.Position = UDim2.new(1, -62, 0, 302)
	if Liked then Heart.TextColor3 = T().Colors.Crimson end
	-- the waveform: bars from the track id, the played part lit; click or drag to seek
	local Wave = new(`TextButton`, { Text = ``; BackgroundTransparency = 1; Position = UDim2.fromOffset(22, 360); Size = UDim2.new(1, -44, 0, 44) }, Sheet)
	local Bars = {}
	local N = 46
	for K = 1, N do
		local Hh = 0.25 + ((hash(Id + K * 31) % 1000) / 1000) * 0.75
		local B = new(`Frame`, { BorderSizePixel = 0; BackgroundColor3 = Color3.fromRGB(120, 105, 140); AnchorPoint = Vector2.new(0, 0.5);
			Position = UDim2.new((K - 1) / N, 1, 0.5, 0); Size = UDim2.new(1 / N, -2, Hh, 0) }, Wave)
		corner(B, 2)
		Bars[K] = B
	end
	local Cur = label(Sheet, `0:00`, 11, { TextColor3 = T().Colors.TextDim; Position = UDim2.fromOffset(22, 406); Size = UDim2.fromOffset(60, 14) })
	local Len = label(Sheet, `0:00`, 11, { TextColor3 = T().Colors.TextDim; TextXAlignment = Enum.TextXAlignment.Right; Position = UDim2.new(1, -82, 0, 406); Size = UDim2.fromOffset(60, 14) })
	local function seek(X: number)
		local S = Ctx.Music.Sound
		if not (S and S.TimeLength > 0) then return end
		local A = math.clamp((X - Wave.AbsolutePosition.X) / Wave.AbsoluteSize.X, 0, 1)
		S.TimePosition = A * S.TimeLength
	end
	Wave.InputBegan:Connect(function(Inp)
		if Inp.UserInputType == Enum.UserInputType.MouseButton1 or Inp.UserInputType == Enum.UserInputType.Touch then seek(Inp.Position.X) end
	end)
	-- controls
	local Row = new(`Frame`, { BackgroundTransparency = 1; Position = UDim2.fromOffset(18, 436); Size = UDim2.new(1, -36, 0, 70) }, Sheet)
	local function place(B, X) B.AnchorPoint = Vector2.new(0.5, 0.5) B.Position = UDim2.new(X, 0, 0.5, 0) end
	local Loop = roundBtn(Row, `\u{27F2}`, 38, false, function() if Ctx.Music.Sound then Ctx.Music.Sound.Looped = not Ctx.Music.Sound.Looped end end) place(Loop, 0.08)
	place(roundBtn(Row, `\u{23EE}`, 44, false, function() if Prev then Ctx.Play(Prev) Shared.NowPlaying() elseif Ctx.Music.Sound then Ctx.Music.Sound.TimePosition = 0 end end), 0.29)
	local Pl Pl = roundBtn(Row, `\u{275A}\u{275A}`, 64, true, function()
		local S = Ctx.Music.Sound
		if not S then return end
		if S.IsPlaying then S:Pause() else S:Resume() end
	end) place(Pl, 0.5)
	place(roundBtn(Row, `\u{23ED}`, 44, false, function() if Next then Ctx.Play(Next) Shared.NowPlaying() end end), 0.71)
	place(roundBtn(Row, `\u{2630}`, 38, false, function() Sheet:Destroy() Ui.Sheet = nil Tab = `Library` Shared.Render() end), 0.92)
	Ctx.Kit.Slider({ label = `Volume`; min = 0; max = 100; step = 5; value = if Ctx.Music.Sound then math.floor(Ctx.Music.Sound.Volume * 100) else 50;
		Size = UDim2.new(1, -44, 0, 34); Position = UDim2.fromOffset(22, 520); Parent = Sheet;
		onChanged = function(V) if Ctx.Music.Sound then Ctx.Music.Sound.Volume = V / 100 end end })
	Ui.NP = { Bars = Bars; Cur = Cur; Len = Len; Play = Pl; Loop = Loop; Title = TitleL; Id = Id }
end

-- the floating tab bar (the reference's pill): Home, Library, Station
function Shared.TabBar(Parent)
	local Bar = new(`Frame`, { BackgroundColor3 = T().Colors.Ink; BackgroundTransparency = 0.1; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -12); Size = UDim2.fromOffset(186, 56); ZIndex = 10 }, Parent)
	corner(Bar) new(`UIStroke`, { Color = T().Colors.GoldDeep; Transparency = 0.45 }, Bar)
	new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; HorizontalAlignment = Enum.HorizontalAlignment.Center; VerticalAlignment = Enum.VerticalAlignment.Center; Padding = UDim.new(0, 10) }, Bar)
	for _, Def in { { `Home`, `\u{2302}` }, { `Library`, `\u{266A}` }, { `Station`, `\u{1F4FB}` } } do
		local B = roundBtn(Bar, Def[2], 46, Tab == Def[1], function() Tab = Def[1] Shared.Render() end)
		B.ZIndex = 11
	end
	if Ctx.Music.Id then -- a mini player above the bar
		local Mini = new(`TextButton`, { Text = ``; BackgroundColor3 = PURPLE_DEEP; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -74); Size = UDim2.new(1, -24, 0, 46); ZIndex = 10 }, Parent)
		corner(Mini, 12) new(`UIStroke`, { Color = PURPLE; Transparency = 0.5 }, Mini)
		local C = cover(Mini, Ctx.Music.Id, 34) C.Position = UDim2.fromOffset(6, 6) C.ZIndex = 11
		local Title = titleOf(Ctx.Music.Id)
		label(Mini, Title, 14, { Font = T().Fonts.Title; ZIndex = 11; Position = UDim2.fromOffset(48, 0); Size = UDim2.new(1, -100, 1, 0) })
		Mini.Activated:Connect(Shared.NowPlaying)
	end
end

function Shared.Render()
	if not (Ui and Ui.Root and Ui.Root.Parent) then return end
	for _, Ch in Ui.Root:GetChildren() do if Ch ~= Ui.Bg and Ch.Name ~= `NowPlaying` then Ch:Destroy() end end
	local Page = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, Ui.Root)
	if Tab == `Station` then
		task.spawn(function() Ctx.Station = Ctx.Call(`Station`) or Ctx.Station if Tab == `Station` and Page.Parent then Page:Destroy() Shared.Render() end end)
	end
	if Tab == `Home` then Shared.Home(Page) elseif Tab == `Library` then Shared.Library(Page) else Shared.Station(Page) end
	Shared.TabBar(Page)
end

function Shared.Open(C)
	Ctx = C
	local App = C.App
	for _, Ch in App:GetChildren() do if Ch.Name ~= `Grain` then Ch:Destroy() end end
	App.Visible = true
	local Root = new(`Frame`, { Name = `NightFM`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ClipsDescendants = true }, App)
	local Bg = new(`Frame`, { Name = `Bg`; BackgroundColor3 = Color3.new(1, 1, 1); Size = UDim2.fromScale(1, 1) }, Root)
	new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(58, 28, 96)), ColorSequenceKeypoint.new(0.45, Color3.fromRGB(26, 16, 36)), ColorSequenceKeypoint.new(1, Color3.fromRGB(14, 10, 18)) }) }, Bg)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = C.Theme.Images.PanelBg; ImageTransparency = 0.9; ScaleType = Enum.ScaleType.Crop; Size = UDim2.fromScale(1, 1) }, Bg)
	-- a back-to-home control in the corner (the phone's Home)
	Ui = { Root = Root; Bg = Bg }
	task.spawn(function() Ctx.Station = Ctx.Call(`Station`) if Ui and Tab == `Home` then Shared.Render() end end)
	Shared.Render()
	-- the phone's back: a thin gold chevron over the page, top-left of the status area
	local Back = new(`TextButton`, { Text = `\u{2039}`; Font = C.Theme.Fonts.Title; TextSize = 26; TextColor3 = C.Theme.Colors.Gold; BackgroundTransparency = 1; Position = UDim2.fromOffset(4, -2); Size = UDim2.fromOffset(26, 30); ZIndex = 30 }, Root)
	Back.Activated:Connect(function() C.Home() end)
end

function Shared.Tick()
	if not (Ui and Ui.Root and Ui.Root.Parent) then return end
	local NP = Ui.NP
	local S = Ctx.Music.Sound
	if NP and Ui.Sheet and Ui.Sheet.Parent and S then
		local A = if S.TimeLength > 0 then S.TimePosition / S.TimeLength else 0
		local Lit = math.floor(A * #NP.Bars + 0.5)
		for K, B in NP.Bars do B.BackgroundColor3 = if K <= Lit then Color3.fromRGB(205, 165, 255) else Color3.fromRGB(110, 96, 130) end
		local function mmss(X) X = math.floor(X) return string.format(`%d:%02d`, X // 60, X % 60) end
		NP.Cur.Text = mmss(S.TimePosition) NP.Len.Text = mmss(S.TimeLength)
		NP.Play.Text = if S.IsPlaying then `\u{275A}\u{275A}` else `\u{25B6}`
		NP.Loop.TextColor3 = if S.Looped then Color3.fromRGB(205, 165, 255) else Ctx.Theme.Colors.Gold
		NP.Title.Text = (titleOf(NP.Id))
	end
end

return Shared
```


- [ ] **Step 3: Phone hands over.**
  - In `Controllers.Gui.Phone`, replace the body of `Local.Radio()` with:

```lua
function Local.Radio() -- (2.30) Night FM is its own module now (Controllers.Gui.PhoneRadio), dressed like the owner's reference
	Ui.Radio = nil
	require(script.Parent:WaitForChild(`PhoneRadio`)).Open({ App = Ui.App; Music = Music; State = State; Play = Local.Play;
		Call = Local.Call; Home = Local.ShowHome; Kit = Kit; Theme = Theme })
	Ui.Home.Visible = false
end
```

  - **In the refresh loop:** replace the `if Ui.Radio and Ui.Radio.Title.Parent then … end` block with
    `pcall(function() require(script.Parent.PhoneRadio).Tick() end) -- (2.30)`.
  - **`Local.Play`:** `Music.Title` stays (the hotbar note uses it).
  - **Header comment:** update the Night FM line to "Night FM (2.30): home, library, now playing and the Midnight
    Broadcast station, in Controllers.Gui.PhoneRadio".
  - **Check:** `Local.Call` exists (Gazette uses it), and `Ui.App` is the app frame `Local.Page` clears.

- [ ] **Step 4: Install and look.**
  - Install Phone (server), PhoneRadio, Phone (client), Broadcast and Config.Broadcast. Start Play.
  - Take the phone out: press `Y`, or `Shared.Toggle(true)` through a real keypress, then open Night FM.
  - **Screenshots** (`review/nightfm_*.jpg`). Compare each with the reference's layout:
    - `home`: the greeting with avatar and two round buttons, chips, the Midnight Broadcast banner, the recent list
      with round play buttons, the pill tab bar
    - `library`: after adding audio ID `1837849285` (any public Roblox audio works), the row shows its title and
      creator
    - `nowplaying`: the big cover with neighbours, the title, the heart, the waveform lit to the position, the round
      controls, volume
    - `station` at 21:30 (`SetTime`): ON AIR and the items; and at 12:00, OFF AIR
  - **Fix overlaps:** text over the tab bar, clipped titles. Adjust sizes in PhoneRadio until each screen reads
    cleanly at the phone's 360×690.
  - **Liking:** like a track, stop and start Play, and the heart is still filled (`Phone.Liked` saved).
  - Restore slot 2, and check `restored`.

- [ ] **Step 5: Commit** `2.30 (3/7): Night FM remade (home, library, now playing, the Midnight Broadcast station)`.

---

### Task 4: Curfew

**Files:** modify `Config.Discipline` and `School.HallMonitor`; TestBridge.

**Interfaces:**
- Produces:
  - `HallMonitor.IsAfterHoursForTests(Player, Hour) -> (boolean, why: string)`
  - The rule:
    - curfew hours (22:00 to 06:00)
    - and `Local.OnCampus(Player)`, the building
    - and not `Regions.Inside(Player, "Dorms")`
    - **Exempt:** while `workspace.NHCinePlaying`, or the player's `Quests.Active.AfterHours` is set.

- [ ] **Step 1: Write the failing test.** Add to TestBridge:

```lua
-- (2.30) the curfew rule at a given hour, with the player where the caller put them
function Commands.CurfewTest(PlayerName: string)
	local HM = require(game:GetService(`ServerScriptService`).Services.School.HallMonitor)
	local P = Players:FindFirstChild(PlayerName)
	local A, Why23 = HM.IsAfterHoursForTests(P, 23)
	local B, Why15 = HM.IsAfterHoursForTests(P, 15)
	local C, Why5 = HM.IsAfterHoursForTests(P, 5)
	return { At23 = A; Why23 = Why23; At15 = B; Why15 = Why15; At5 = C; Why5 = Why5 }
end
```

  Expected before the code: an error.

- [ ] **Step 2: Config.** In `Config.Discipline.HallMonitor.DutyKinds`, add `Night = true;`. Under `HallMonitor`, add
  `Curfew = { From = 22; To = 6 }; -- (2.30) after hours: the building (not the dorms), patrolled at night`.
- [ ] **Step 3: HallMonitor.**
  - **Add `IsAfterHours`:**

```lua
-- (2.30) curfew (doc 13 §5.3): after hours, inside the school building but not the dorms, not during a cut or the
-- After Hours quest (whose night stages are the story)
function Local.IsAfterHours(Player: Player, Hour: number?): (boolean, string)
	local C = Settings.Curfew
	if not C then return false, `NoCurfew` end
	local H = Hour or (SchoolClock.GetState().Hour or 12)
	if not (H >= C.From or H < C.To) then return false, `Daytime` end
	if workspace:GetAttribute(`NHCinePlaying`) then return false, `Cutscene` end
	local Ok, Active = pcall(function()
		local Profile = require(ServerScriptService.Services.Player.Data).GetProfile(Player)
		return Profile and Profile.Quests and Profile.Quests.Active and Profile.Quests.Active.AfterHours ~= nil
	end)
	if Ok and Active then return false, `AfterHoursQuest` end
	if not Local.OnCampus(Player) then return false, `Outside` end
	local OkR, InDorms = pcall(function() return require(ServerScriptService.Services.Features.Regions).Inside(Player, `Dorms`) end)
	if OkR and InDorms then return false, `Dorms` end
	return true, `AfterHours`
end
function Shared.IsAfterHoursForTests(Player: Player, Hour: number) return Local.IsAfterHours(Player, Hour) end
```

  - **The chase rule:** change `if State.Segment.Kind == \`Class\` then` (the patrol's truant search) to
    `if State.Segment.Kind == \`Class\` or State.Segment.Kind == \`Night\` then`. Change the `Why` line to:

```lua
			local Why = if Local.IsTruant(Player, State) then `Truancy` elseif Local.IsTrespassing(Player, State) then `Trespassing`
				elseif Local.IsAfterHours(Player) and not (Caught[Player] and Caught[Player].Curfew == Local.PeriodKey(State)) then `Curfew` else nil -- (2.30)
```

  - **`StartChase`'s line:** add `elseif Reason == \`Curfew\` then \`Curfew! Back to the dorms, now.\``.
  - **`Catch`'s line:** add `elseif Reason == \`Curfew\` then \`Out after curfew. This goes on your record.\``.
  - **`Catch`'s report:** in `Discipline.ReportIncident({ Type = Reason; …`, use
    `Type = if Reason == \`Curfew\` then \`Trespassing\` else Reason;`. On a punished curfew catch, confiscate as the fight
    path does:
    `pcall(function() require(game:GetService(\`ServerScriptService\`).Services.Features.Armory).Confiscate(Player, \`BrassKnuckles\`) end)`.
  - **The chase check:** `if M.Reason == \`Trespassing\` and not Local.IsTrespassing(Player, State) then` ends a chase
    when the reason lapses. Add the same for Curfew: `if M.Reason == \`Curfew\` and not Local.IsAfterHours(Player) then`,
    with the same body.
  - **Check:** `HallMonitor` requires `SchoolClock` and `ServerScriptService` at the top. It does (`State` comes from
    `SchoolClock.GetState`, and `OnCampus` uses `ServerScriptService`).
  - **The PA:** curfew's PA is in Task 1 (22:00).
- [ ] **Step 4: Install and run.**
  - Install Config.Discipline, HallMonitor and the TestBridge, then start Play.
  - **In a hallway** (`_hall.lua`), run `bridge.py CurfewTest '$P'`. Expected: `At23 true`, `At15 false` (Daytime),
    `At5 true`.
  - **In the Dorms:** move the player there (the Dorms region box's position, via `gamevm.py`). Expected: `At23 false`,
    `Why23 "Dorms"`.
  - **Outside:** on the grounds, `Why23 "Outside"`.
  - **Live:** `SetTime "23:00"`, stand in the hall on the monitor's route, and wait up to 60 s. The monitor chases;
    when caught, the newest Discipline record is `Trespassing` with witness "Hall Monitor", and the PA said "Curfew is
    now in force…" at 22:00 if the clock passed it.
  - **The Records Office at night:** the existing Stealth watcher (the Night Custodian) still works. Walk into
    `Area_RecordsOffice` at 23:00 and be spotted.
  - Restore slot 2 (`restored`, then the snapshot matches).
- [ ] **Step 5: Commit** `2.30 (4/7): curfew: the night monitor walks the halls from 22:00`.

---

### Task 5: Regression

- [ ] **Step 1: Self-tests in one session.**
  - **This release:** `BroadcastTest`, `CurfewTest` (hallway).
  - **2.29:** `IncidentTest`, `RumourTest`, `RumourSafetyTest`.
  - **2.28:** `StaffTest`, `StaffPlanTest`, `TimetableTest`, `SleepTest`.
  - **2.27:** `RosterTest`, `Rostered`, `RelationshipCapTest`, `MemoryTest`.
  - **Earlier:** the cutscene and Phase 1 suite.
- [ ] **Step 2: Unchanged behaviour.**
  - The truancy chase in class still works: at 09:10, stand in a hallway, and the monitor chases for Truancy.
  - The Gazette opens.
  - Night FM plays and pauses.
  - The prologue's two paths: no curfew catch during the cut at night (`NHCinePlaying`).
  - The school day sample (07:40, 08:05, 09:10, 11:30, 15:30).
- [ ] **Step 3: The console.** No errors from Broadcast, Phone, PhoneRadio, ClockHud, HallMonitor, Rumours, Incidents
  or Scenes.
- [ ] **Step 4:** Restore slot 2 and check it, stop Play, and run `save_place`.

### Task 6: Docs, release 2.30.0, and the Phase 2 announcement

- [ ] **Step 1: CHANGELOG `[2.30.0]`,** plus README, Implementation-Status, and a Discord game update
  (`<date>-after-dark.md`).
- [ ] **Step 2: Doc 13.** The status says **"Phase 2 complete (2.27 to 2.30)"**, plus §9's deltas.
- [ ] **Step 3: The announcement:** `updates/discord/announcements/<date>-the-living-school-2.md`, "THE LIVING
  SCHOOL", for the Phase 2 wave (2.27 to 2.30). Emoji headers:
  - classmates with names
  - teachers and timetables
  - rumours and scenes
  - the PA and Night FM's Midnight Broadcast
  - curfew

  It ends with "Full notes in #game-updates". Update both indexes. (The Chapter One announcement from 2.26 is the
  model.)
- [ ] **Step 4: Vault** copies, the home-note game-update line and its announcement line.
- [ ] **Step 5: Commit and merge** (stage this plan's files and its CHANGELOG hunk; merge with `-F <file>`; stash
  around the merge). Don't push.

---

## Spec deltas (record in doc 13 §9 at release)

1. **The PA speakers:** no talking-face speakers on hall props. The PA is a chime and a typed line on the ClockHud.
   That's within the kit-only art rule; a speaker prop needs art.
2. **The station's "sound bed":** Night FM's station is text segments with the PA chime, with no audio bed. Players'
   own tracks keep playing underneath.
3. **Curfew's patrol:**
   - The night monitor walks the hall monitor's existing indoor route.
   - The Records Office keeps its existing night watcher (the Night Custodian, Stealth).
   - The Restricted outdoor areas (Graveyard, Boiler Yard) aren't patrolled. Being there isn't "in the building", so
     it isn't after-hours under this rule.
   - The building check is HallMonitor's `OnCampus` (rooms and hallways), since the Regions boxes don't line up.
4. **Confiscation on a curfew catch** uses HallMonitor's existing confiscation (brass knuckles). There's no new
   "carried for the night" rule.
5. **The phone's "monitors on their rounds" line** no longer exists (2.22 removed it), so there's nothing to make
   true.
6. **"A match tonight" and "an assembly"** announce only when those systems report one. There's no assembly system
   yet.
7. **Night FM was remade** (the owner's request, 2026-11-18): home, library, now playing and station, in
   `Controllers.Gui.PhoneRadio`. Liked tracks are saved per slot (`Phone.Liked`, 30 at most).

## Self-review

- **Spec coverage (doc 13 §5):**
  - §5.1 (items and config) is Task 1.
  - §5.2:
    - the Gazette: Task 2
    - the PA: Task 1
    - Night FM: Task 3
    - saving (`Phone.Broadcast`): Task 3
  - §5.3, curfew, is Task 4.
  - §5.4, the acceptance, is Tasks 1, 4 and 5.
  - The owner's Night FM request is Task 3.
- **Placeholders:**
  - None. `Substitutes.Upcoming`'s `Today` field is checked in Task 1 Step 3.
- **Types:**
  - The item fields (`Id`, `Kind`, `Text`, `T`) are the same in Broadcast, the Gazette, the station and PhoneRadio.
  - `Station(P)` returns `{OnAir, Items, LastRead}`, and PhoneRadio reads it.
  - The `Curfew` reason maps to the `Trespassing` violation.
