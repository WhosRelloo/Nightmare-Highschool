# Staff in the School Day (2.28) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Four subject teachers and the Headmaster keep the school day. Each class period seats its own set of six
named students. A teacher at their desk books a fight in their room, and names themselves on a late mark. Students
far from every player have no body, so the school can grow without the frame rate paying for it.

**Architecture:**
- **Staff:** Mr. Hale already shows how staff work: `Config.Npcs` entries spawned by `Social.Npcs` at an `NpcPost`
  part. 2.28 adds a `Posts` table per staff member: a post per kind of school segment. `Social.Npcs` fades them from
  one post to the next as the segment changes, the way 2.24's `OffWhen` fades the Custodian.
- **Timetables:** `Social.Roster` gains `Plan`, which says where each set is in each period. `Features.Schedules`
  seats by it.
- **Witnesses:** a new `School.Teachers` listens to `Downed.OnDamage` and `Attendance.Recorded`, and reports
  through `Discipline`.
- **Off-screen students:** they're bodiless at their job's spot, run by a sleep/wake check in Schedules' existing
  1-second clock loop.

**Tech Stack:** Roblox Luau in NH Combat Test (placeId 98950102230473), through the Studio MCP and the
`tools/phase4-2280/harness` helpers (`install.py`, `dump.py`, `bridge.py`, `gamevm.py`, `snapshot.lua`, `restore.py`,
`start_play.lua`), run with `python -X utf8 -I`.

**Spec:** `docs/expansion/13-Living-School.md` §3 (2.28), §7, and the §9 deltas so far. This plan's own deltas are
listed at the end; record them in §9 at release.

## Global Constraints

- Build only in **NH Combat Test**. The Map place is read-only; new marks go in doc 11's port table.
- **Backup** before the first edit of each existing script: copy it into `ServerStorage.NH_Backup.Phase4_pre_<date>`
  (2.27 made `Phase4_pre_20261118`; add to it).
- **Mirror:**
  - `tools/phase4-2280/pre/` holds the first dump. Already done for Config.Npcs, Social.Npcs, NpcLooks, Discipline,
    Schedules, Roster, TestBridge and Dialogue.Hale.
  - Edit `tools/phase4-2280/live/<dotted path>.luau`, then install with `harness/install.py`.
  - Studio scripts that aren't modules are built by `.luau` files run with rbxc in Edit.
- **Tests:**
  - TestBridge commands (`bridge.py <Command> '$P'`) run in the game.
  - Checks of live state use `harness/gamevm.py <file>`, which runs inside the game. Plain MCP `execute_luau` gets its
    own copy of every module and can't see live state.
- **Test slot 2** only (`start_play.lua` picks it, and sets 21:30). Snapshot before and restore after any test that
  changes saved state. Never use slot 1.
- **Art and UI:** existing assets only: the `NpcLooks` clothing ids, catalog hair already used by the cast, and kit UI.
- **Code style:** `Shared` / `Local` tables, backtick strings, `-- (2.28)` on changed lines, no new per-frame server
  loop.
- **Commits:** `git -c user.name=Rello commit`, with the Co-Authored-By and Claude-Session lines, on
  `phase4-living-school`. Stage only this plan's files.

---

## File structure

| File (`tools/phase4-2280/live/…` unless noted) | Responsibility | New / changed |
|---|---|---|
| `ReplicatedStorage.Config.Npcs.luau` | Sallow, Pryce, Whitlock, Ashgrave; `Posts` for them and for Hale | changed |
| `ServerScriptService.Services.Features.NpcLooks.luau` | Looks for the four new staff | changed |
| `ServerStorage.Dialogue.{Sallow,Pryce,Whitlock,Ashgrave}.luau` | Their talk trees (`GiverTemplate`) | new |
| `tools/phase4-2280/marks_staff.luau` | Builds the staff `NpcPost` parts in `workspace.School.Quests.Staff` | new (Edit script) |
| `ServerScriptService.Services.Social.Npcs.luau` | `PostKey(NpcId, State)`, staff moving between posts on segment change | changed |
| `ServerScriptService.Services.Social.Roster.luau` | `Plan(SegName, Id, Day)`, `WhereNow(Id)`, the rotation and homeroom tables | changed |
| `ServerScriptService.Services.Features.Schedules.luau` | Seats by `Roster.Plan`; no 6-seat cap; standing at the back; skipping; sleep/wake | changed |
| `ServerScriptService.Services.School.Teachers.luau` | Who is at which desk; line of sight; booking fights; naming late marks | new |
| `ServerScriptService.Services.School.Discipline.luau` | A late mark's witness comes from `Teachers` | changed |
| `ServerScriptService.Services.Studio.TestBridge.luau` | `StaffTest`, `TimetableTest`, `WitnessTest`, `SleepTest` | changed |

---

### Task 1: The staff, their looks, talk and posts

**Files:**
- Modify: `ReplicatedStorage.Config.Npcs.luau`, `ServerScriptService.Services.Features.NpcLooks.luau`, TestBridge
- Create: `ServerStorage.Dialogue.Sallow.luau`, `.Pryce.luau`, `.Whitlock.luau`, `.Ashgrave.luau`;
  `tools/phase4-2280/marks_staff.luau`

**Interfaces:**
- Produces:
  - `Config.Npcs[Id].Posts = { Homeroom = key?, Class = key?, Other = key? }`. A key is an `NpcPost` value.
    `Homeroom` is used in the "Homeroom" segment, `Class` in the other class periods, and `Other` in Before School,
    Passing, Break, Lunch and After School. A missing key means the NPC is away (not spawned).
  - Post parts: `workspace.School.Quests.Staff.<key>`, invisible and anchored, with `NpcPost = <key>`.

- [x] **Step 1: Write the failing test.** Add to TestBridge:

```lua
-- (2.28) every staff post exists, and every staff member has a look and a talk tree
function Commands.StaffTest(PlayerName: string)
	local Cast = require(game:GetService(`ReplicatedStorage`).Config.Npcs)
	local Looks = require(game:GetService(`ServerScriptService`).Services.Features.NpcLooks)
	local Places = require(game:GetService(`ServerScriptService`).Services.Quests.Places)
	local Out = { Missing = {} }
	for _, Id in { `Sallow`, `Hale`, `Pryce`, `Whitlock`, `Ashgrave` } do
		local Npc = Cast[Id]
		if not Npc then table.insert(Out.Missing, `cast {Id}`) continue end
		if not Npc.Posts then table.insert(Out.Missing, `posts {Id}`) continue end
		for Slot, Key in Npc.Posts do
			if not Places.Find(`NpcPost`, Key) then table.insert(Out.Missing, `post {Id}.{Slot}={Key}`) end
		end
		if not Looks.Specs[Id] then table.insert(Out.Missing, `look {Id}`) end
		if not game:GetService(`ServerStorage`).Dialogue:FindFirstChild(Npc.Dialogue or ``) then table.insert(Out.Missing, `talk {Id}`) end
	end
	return Out
end
```

  Install the TestBridge, start Play, and run `bridge.py StaffTest '$P'`. Expected: `Missing` lists `cast Sallow`,
  `posts Hale`, and so on.

- [x] **Step 2: Add the staff to `Config.Npcs`.** Back it up first. Replace the `Hale` line and add after the
  Custodian:

```lua
	Hale = { Name = `Mr. Hale`; Role = `Chemistry, Room 103`; Color = Color3.fromRGB(196, 160, 112); Dialogue = `Hale`;
		-- (2.28) homeroom register at his Room 102 desk (2.24's post), Chemistry in Room 103, the Staff Room otherwise
		Posts = { Homeroom = `Hale`; Class = `Hale@R103`; Other = `Hale@Staff` } };
```

```lua
	-- (2.28) the subject teachers and the Headmaster (docs/expansion/13-Living-School.md §3.1). Posts by segment:
	-- Homeroom (the register), Class (the other periods), Other (before school, passing, break, lunch, after school).
	-- No key for a segment = not on campus then.
	Sallow = { Name = `Ms. Sallow`; Role = `Mathematics, Room 102`; Color = Color3.fromRGB(150, 150, 170); Dialogue = `Sallow`;
		Posts = { Class = `Sallow`; Other = `Sallow@Staff` } };
	Pryce = { Name = `Mr. Pryce`; Role = `English, Room 104`; Color = Color3.fromRGB(170, 120, 90); Dialogue = `Pryce`;
		Posts = { Class = `Pryce`; Other = `Pryce@Staff` } };
	Whitlock = { Name = `Dr. Whitlock`; Role = `History, Room 105`; Color = Color3.fromRGB(120, 100, 80); Dialogue = `Whitlock`;
		Posts = { Class = `Whitlock`; Other = `Whitlock@Staff` } };
	Ashgrave = { Name = `Headmaster Ashgrave`; Role = `Headmaster`; Color = Color3.fromRGB(60, 50, 70); Dialogue = `Ashgrave`;
		Posts = { Homeroom = `Ashgrave`; Class = `Ashgrave` } }; -- office hours by the Records Office door, class time only
```

- **Sallow's homeroom:** with no `Homeroom` key she's away during Homeroom; that's her prep time.
- **Hale's class:** he teaches Chemistry in every class period.
- **Room conflict:** Room 102 has Hale at Homeroom and Sallow in Periods 1 to 4, so the two never share it.

- [x] **Step 3: Looks.** Back up `NpcLooks`, then add these specs under the 2.24 staff:

```lua
	-- (2.28) the subject teachers and the Headmaster (existing clothing ids and cast hair)
	Sallow = { Body = 2; Skin = 1; Uniform = `crest-blazer`; Bottoms = `wide-leg-trousers`; Eyes = 2; Brows = `straight`; Mouth = `flat`; HairId = 1903448711 };
	Pryce = { Body = 1; Skin = 3; Uniform = `victorian-waistcoat`; Bottoms = `trousers-chelsea`; Eyes = 4; Brows = `angled`; Mouth = `smile`; HairId = 3379112107 };
	Whitlock = { Body = 2; Skin = 2; Uniform = `cropped-cardigan`; Bottoms = `velvet-midi`; Eyes = 3; Brows = `soft`; Mouth = `flat`; HairId = 3432180024 };
	Ashgrave = { Body = 1; Skin = 1; Uniform = `wool-overcoat`; Bottoms = `charcoal-slacks`; Eyes = 2; Brows = `furrowed`; Mouth = `flat`; HairId = 3609301673 };
```

- [x] **Step 4: The talk trees.** Each is a new ModuleScript in `ServerStorage.Dialogue`, in the Custodian's format.
  `Sallow.luau`:

```lua
-- Ms. Sallow (2.28). Mathematics, Room 102. Exact, dry; keeps a ruler she never uses.
local Template = require(script.Parent.GiverTemplate)

return Template({
	Greeting = `You're early, or you're late. Which?`;
	Bye = `Mind the margins.`;
	Talk = {
		{ Ask = `What are we doing in class?`; Answer = `Proofs. Everything in this school wants proving.` };
		{ Ask = `Why do you carry a ruler?`; Answer = `Lines should be straight. Very little here is.` };
		{ Ask = `Did you teach Mira Holt?`; Answer = `The register says I didn't. The register is usually right.` };
	};
})
```

`Pryce.luau`:

```lua
-- Mr. Pryce (2.28). English, Room 104. Theatrical; reads the register as if it were a play; kind to the quiet ones.
local Template = require(script.Parent.GiverTemplate)

return Template({
	Greeting = `Ah! Enter, stage left.`;
	Bye = `Exit, pursued by homework.`;
	Talk = {
		{ Ask = `What are we reading?`; Answer = `Ghost stories. This term they're the only honest kind.` };
		{ Ask = `Why do you read the register like that?`; Answer = `Every name deserves to be said properly. Some only get the once.` };
		{ Ask = `Any advice?`; Answer = `Speak up in class. The quiet ones get forgotten here.` };
	};
})
```

`Whitlock.luau`:

```lua
-- Dr. Whitlock (2.28). History, Room 105. The school's own historian: knows the False Explanation by heart, believes it.
local Template = require(script.Parent.GiverTemplate)

return Template({
	Greeting = `History is happening, you know. Sit down for it.`;
	Bye = `Mind the dates.`;
	Talk = {
		{ Ask = `How old is the school?`; Answer = `Founded 1887. A fire at the north gate that same year. Tragic. Well documented.` };
		{ Ask = `What happened to the students in the fire?`; Answer = `Transferred. It's all in the records. Every one of them.` };
		{ Ask = `Who's in the old painting?`; Answer = `The Class of 1887. All present and accounted for.` };
	};
})
```

`Ashgrave.luau`:

```lua
-- Headmaster Corvin Ashgrave (2.28). Keeps the Covenant; not a villain: believes the roll is the price of every
-- student's safety. Office hours by the Records Office door during class time.
local Template = require(script.Parent.GiverTemplate)

return Template({
	Greeting = `Shouldn't you be in class?`;
	Bye = `Attend. Always attend.`;
	Talk = {
		{ Ask = `What's in the Records Office?`; Answer = `Every student who ever answered the register. You're in there too.` };
		{ Ask = `Who was Mira Holt?`; Answer = `There is no Mira Holt on my roll. I'd remember.` };
		{ Ask = `Why does the bell ring at night?`; Answer = `Old buildings make old noises. Go to bed early, and you won't hear it.` };
	};
})
```

- [x] **Step 5: The posts (`tools/phase4-2280/marks_staff.luau`).** Run it in Edit with rbxc. Desk posts stand 2.5
  studs behind each room's `TeacherDesk` part, on its far side from the chairs, facing the room. Staff Room posts are
  spread in `Area_StaffRoom`. Ashgrave's stands beside `Area_RecordsExit`, facing the corridor.

```lua
-- (2.28) staff NpcPost parts (docs/superpowers/plans/2026-11-18-staff-school-day.md Task 1). Re-runnable: replaces the folder.
local Quests = workspace.School.Quests
local Old = Quests:FindFirstChild(`Staff`) if Old then Old:Destroy() end
local F = Instance.new(`Folder`) F.Name = `Staff` F.Parent = Quests
local function Post(Key: string, Pos: Vector3, Look: Vector3)
	local P = Instance.new(`Part`)
	P.Name = Key P.Anchored = true P.CanCollide = false P.CanQuery = false P.CanTouch = false P.Transparency = 1
	P.Size = Vector3.new(2, 1, 2)
	P.CFrame = CFrame.lookAt(Pos, Vector3.new(Look.X, Pos.Y, Look.Z))
	P:SetAttribute(`NpcPost`, Key)
	P.Parent = F
end
local Chairs = workspace.School.NHProps
for Key, Room in { Sallow = `R102`, [`Hale@R103`] = `R103`, Pryce = `R104`, Whitlock = `R105` } do
	local Desk = workspace.School[Room].TeacherDesk
	-- the chairs' centre in this room decides which side of the desk faces the class
	local CF, Size = workspace.School[Room]:GetBoundingBox()
	local Sum, N = Vector3.zero, 0
	for _, C in Chairs:GetChildren() do
		if C.Name == `StudentChair` and C:IsA(`Model`) then
			local L = CF:PointToObjectSpace(C:GetPivot().Position)
			if math.abs(L.X) < Size.X / 2 and math.abs(L.Z) < Size.Z / 2 then Sum += C:GetPivot().Position N += 1 end
		end
	end
	local Class = if N > 0 then Sum / N else CF.Position
	local Away = ((Desk.Position - Class) * Vector3.new(1, 0, 1)).Unit
	Post(Key, Desk.Position + Away * 2.5 + Vector3.new(0, 2, 0), Class)
end
local SR = workspace.School.Quests:FindFirstChild(`Area_StaffRoom`, true) or workspace:FindFirstChild(`Area_StaffRoom`, true)
for I, Key in { `Hale@Staff`, `Sallow@Staff`, `Pryce@Staff`, `Whitlock@Staff` } do
	local X = (I - 2.5) * 4
	Post(Key, SR.Position + Vector3.new(X, -SR.Size.Y / 2 + 3, 4), SR.Position)
end
local Exit = workspace:FindFirstChild(`Area_RecordsExit`, true)
Post(`Ashgrave`, Exit.Position + Vector3.new(5, 0, 2), Exit.Position + Vector3.new(5, 0, 12))
return #F:GetChildren() .. ` posts`
```

- **Expected output:** `9 posts`.
- **Then check by screenshot:** `screen_capture` looking at each post. None may be inside a desk, wall or chair; if one
  is, move it by the measured amount and re-run.
- **Record the marks** in doc 11's Map port table as relative descriptions: behind the desk, in the Staff Room, by the
  Records door.

- [x] **Step 6: Install and run the test.** Install `Config.Npcs`, `NpcLooks`, the four dialogue files and the
  TestBridge, start Play, and run `bridge.py StaffTest '$P'`. Expected: `Missing []`.

- [x] **Step 7: Commit** `2.28 (1/7): the subject teachers and the Headmaster; their looks, talk and posts`.

---

### Task 2: Staff move between their posts

**Files:**
- Modify: `ServerScriptService.Services.Social.Npcs.luau` (`Local.Post`, `Local.Away`, `Local.Spawn`, `Local.Tick`, a
  test hook), TestBridge

**Interfaces:**
- Consumes: `Config.Npcs[Id].Posts` and the post parts (Task 1); `SchoolClock.GetState()` (`Segment.Kind`,
  `Segment.Name`)
- Produces:
  - `Npcs.PostKey(NpcId, Kind, Name) -> string?` (pure)
  - each active entry remembers `N.Key`

- [x] **Step 1: Write the failing test.** Add to TestBridge:

```lua
-- (2.28) which post each staff member uses in each segment (pure)
function Commands.StaffPlanTest(PlayerName: string)
	local Npcs = require(game:GetService(`ServerScriptService`).Services.Social.Npcs)
	local Out = {}
	for _, Seg in { { `BeforeSchool`, `Before School` }, { `Class`, `Homeroom` }, { `Class`, `Period 2` }, { `Lunch`, `Lunch` }, { `Night`, `Night` } } do
		local Row = {}
		for _, Id in { `Hale`, `Sallow`, `Ashgrave`, `Ezra` } do Row[Id] = Npcs.PostKey(Id, Seg[1], Seg[2]) or `-` end
		Out[Seg[2]] = Row
	end
	return Out
end
```

Expected before the change: an error (`PostKey` is nil).

- [x] **Step 2: Back up `Social.Npcs`.** Add the pure key function, and route every post lookup through the key:

```lua
-- (2.28) the post key for a segment: Config.Npcs Posts (Homeroom / Class / Other), else the NPC's own id
local OTHER = { BeforeSchool = true; Passing = true; Break = true; Lunch = true; AfterSchool = true }
function Shared.PostKey(NpcId: string, Kind: string?, Name: string?): string?
	local Npc = Cast[NpcId]
	if not Npc then return nil end
	if not Npc.Posts then return NpcId end
	if Kind == `Class` and Name == `Homeroom` then return Npc.Posts.Homeroom end
	if Kind == `Class` then return Npc.Posts.Class end
	if OTHER[Kind or ``] then return Npc.Posts.Other end
	return nil
end
function Local.KeyNow(NpcId: string): string?
	local Ok, Seg = pcall(function() return require(ServerScriptService.Services.School.SchoolClock).GetState().Segment end)
	return Shared.PostKey(NpcId, Ok and Seg and Seg.Kind or nil, Ok and Seg and Seg.Name or nil)
end
```

- **`Local.Post`:** becomes
  `function Local.Post(NpcId: string): BasePart? local Key = Local.KeyNow(NpcId) return Key and Places.Find(\`NpcPost\`, Key) or nil end`.
- **`Local.Away(Npc)`:** at the start, add
  `if Npc.Posts then local Id = Npc.__Id return Local.KeyNow(Id) == nil end`. To make `Npc.__Id` available, at the top
  of `Shared.OnStart` add `for Id, Npc in Cast do Npc.__Id = Id end`.
- **`Local.Spawn`:** the warning about a missing post (`no part with NpcPost`) should only fire when
  `Local.KeyNow(NpcId)` isn't nil. Store the key on the entry:
  `local N = { Id = NpcId; Key = Local.KeyNow(NpcId); Model = …`.
- **`Local.Tick`:** extend the `OffWhen` loop to staff with `Posts`. Replace its first loop with:

```lua
	for NpcId, Npc in Cast do
		if not (Npc.OffWhen or Npc.Posts) then continue end
		local Away = Local.Away(Npc)
		local N = Active[NpcId]
		if Away and N then Local.Depart(NpcId)
		elseif N and Npc.Posts and N.Key ~= Local.KeyNow(NpcId) then
			Local.Depart(NpcId) -- (2.28) a new segment: fade out here, back at the new post next tick
		elseif not Away and not N and not Returning[NpcId] and Local.Post(NpcId) then
			Returning[NpcId] = true
			task.spawn(function() pcall(Local.Spawn, NpcId) Returning[NpcId] = nil end)
		end
	end
```

- **Avoid an empty post:** `Local.Depart` destroys after 0.8 s, so the new spawn starts on the next tick; the gap is at
  most one tick.
- **Update the header comment:** "(2.28) staff with Posts move between them by school segment".

- [x] **Step 3: Install and run the test.**
  - Install `Social.Npcs` and the TestBridge, start Play, and run `bridge.py StaffPlanTest '$P'`.
  - Expected:
    - `Before School`: `{Hale "Hale@Staff", Sallow "Sallow@Staff", Ashgrave "-", Ezra "Ezra"}`
    - `Homeroom`: `{Hale "Hale", Sallow "-", Ashgrave "Ashgrave", Ezra "Ezra"}`
    - `Period 2`: `{Hale "Hale@R103", Sallow "Sallow", Ashgrave "Ashgrave", Ezra "Ezra"}`
    - `Lunch`: `{Hale "Hale@Staff", Sallow "Sallow@Staff", Ashgrave "-", Ezra "Ezra"}`
    - `Night`: all staff `-`, and `Ezra "Ezra"`

- [x] **Step 4: The live check.** For each time, `bridge.py SetTime`, wait 5 s, then use `gamevm.py` to list the
  `workspace.Live` models with an `NpcId` among the staff, and how far each is from its expected post part:
  - **08:05:** Hale at `Hale`, Ashgrave at `Ashgrave`, Sallow absent.
  - **09:10:** Hale at `Hale@R103`, Sallow at `Sallow`, Pryce at `Pryce`, Whitlock at `Whitlock`.
  - **11:30:** all four teachers in the Staff Room, Ashgrave absent.
  - **21:30:** none of the five.
  - **Expected:** each within 3 studs of its post.
  - **Screenshot** one classroom with its teacher at 09:10 to `tools/phase4-2280/review/teacher_r104.jpg`.
  - Talk to Pryce (`Npcs.TalkForTests` in `gamevm.py`): his greeting is "Ah! Enter, stage left.".

- [x] **Step 5: Commit** `2.28 (2/7): staff fade between their posts as the day changes`.

---

### Task 3: Each set has its own timetable

**Files:**
- Modify: `ServerScriptService.Services.Social.Roster.luau` (`Plan`, `ROTATION`, `HOMEROOM`), `ServerScriptService.Services.Features.Schedules.luau` (`Local.OnSegment`, `Local.Class`, `IN_CLASS`), TestBridge

**Interfaces:**
- Consumes: `Config.Students` `Set` and `SkipChance` (2.27); `Config.Classes.Periods[SegName].Room`
- Produces:
  - `Roster.Plan(SegName: string, Id: string, Day: number) -> { Room: string? , Skip: boolean }` for class segments.
    `Room` is a room id (`R101` to `R105`); `Skip` is true when a Delinquent skips that period.
  - `Roster.ROTATION`, `Roster.HOMEROOM` (read-only tables)

- [x] **Step 1: Write the failing test.** Add to TestBridge:

```lua
-- (2.28) the set rotation, homeroom rooms and skipping (pure)
function Commands.TimetableTest(PlayerName: string)
	local Roster = require(game:GetService(`ServerScriptService`).Services.Social.Roster)
	local Out = { PerRoom = {}, Homeroom = {}, Skips = 0, SkipStable = true }
	for _, Seg in { `Period 1`, `Period 2`, `Period 3`, `Period 4` } do
		local Count = {}
		for _, E in Roster.All() do
			local P = Roster.Plan(Seg, E.Id, 7)
			if P.Room then Count[P.Room] = (Count[P.Room] or 0) + 1 end
		end
		Out.PerRoom[Seg] = Count
	end
	for _, E in Roster.All() do
		local R = Roster.Plan(`Homeroom`, E.Id, 7).Room
		Out.Homeroom[R or `-`] = (Out.Homeroom[R or `-`] or 0) + 1
		for Day = 1, 40 do
			local A = Roster.Plan(`Period 3`, E.Id, Day)
			if A.Skip then Out.Skips += 1 end
			if A.Skip ~= Roster.Plan(`Period 3`, E.Id, Day).Skip then Out.SkipStable = false end
			if A.Skip and E.Clique ~= `Delinquents` then Out.SkipStable = false end
		end
	end
	Out.Seg1SetA = Roster.Plan(`Period 1`, `OdetteMarsh`, 7).Room -- set A, Period 1: R102
	Out.Seg2SetA = Roster.Plan(`Period 2`, `OdetteMarsh`, 7).Room -- set A, Period 2: R103
	return Out
end
```

Expected before the change: an error (`Plan` is nil).

- [x] **Step 2: Add `Plan` to `Social.Roster`:**

```lua
-- (2.28) doc 13 §3.3: in each class period every subject room hosts one set; the sets rotate
Shared.ROTATION = {
	[`Period 1`] = { A = `R102`; B = `R103`; C = `R104`; D = `R105` };
	[`Period 2`] = { D = `R102`; A = `R103`; B = `R104`; C = `R105` };
	[`Period 3`] = { C = `R102`; D = `R103`; A = `R104`; B = `R105` };
	[`Period 4`] = { B = `R102`; C = `R103`; D = `R104`; A = `R105` };
}
-- homeroom: sets A and B in Room 101; C and D in Room 102 for Mr. Hale's register
Shared.HOMEROOM = { A = `R101`; B = `R101`; C = `R102`; D = `R102` }

function Shared.Plan(SegName: string, Id: string, Day: number)
	local E = Config.ById[Id]
	if not E then return { Room = nil; Skip = false } end
	if SegName == `Homeroom` then return { Room = Shared.HOMEROOM[E.Set]; Skip = false } end
	local Rot = Shared.ROTATION[SegName]
	if not Rot then return { Room = nil; Skip = false } end
	-- a Delinquent may skip; the same answer every time for this student, day and period
	local Skip = false
	if E.SkipChance then
		local R = Random.new(NpcBuilds.Seed(`Skip|{Id}|{Day}|{SegName}`))
		Skip = R:NextNumber() < E.SkipChance
	end
	return { Room = if Skip then nil else Rot[E.Set]; Skip = Skip }
end
```

  Add `Plan(SegName, Id, Day)` to the header's API line.

- [x] **Step 3: Seat by the plan in `Schedules`.**
  - **Back up `Schedules`.** Delete `local IN_CLASS = 6`.
  - **`Local.OnSegment`:** replace the `elseif Kind == \`Class\` then … end` branch with the code below.
    `State.Day` is the school clock's day number. In `PlanForTests`, it's nil, so use 1.

```lua
		elseif Kind == `Class` then
			-- (2.28) each set's own room (Roster.Plan, doc 13 §3.3); a Delinquent who skips hangs out instead
			local P = Roster.Plan(Seg.Name, S.RosterId, tonumber(State.Day) or 1)
			if P.Room then
				Local.Assign(S, Local.Class, P.Room, I)
			elseif P.Skip then
				Local.Assign(S, Local.Hangout)
			else
				Local.Assign(S, Local.Leave)
			end
```

  - **Add `local Roster = require(ServerScriptService.Services.Social.Roster)`** at the top of the module, next to the
    other requires. The one inside `OnStart` from 2.27 can then use it.

- [x] **Step 4: Extra students stand at the back.** In `Local.Class`, replace
  `if not Chair then Local.Mingle(S, Job) return end` with:

```lua
	if not Chair then -- (2.28) a full room: stand at the back of it (the far side from the teacher's desk)
		local Room = workspace.School:FindFirstChild(RoomId)
		local CF, Size = Local.Box(Room)
		local Desk = Room and Room:FindFirstChild(`TeacherDesk`)
		if not (CF and Desk) then Local.Mingle(S, Job) return end
		local Back = CF.Position + ((CF.Position - Desk.Position) * Vector3.new(1, 0, 1)).Unit * (Size.Z / 2 - 2.5)
		local Side = (Seat % 5 - 2) * 2.2
		local Spot = Local.Floor(Back + CF.RightVector * Side) or Back
		S.Model:SetAttribute(`NHActivity`, `In class ({RoomId}, standing)`)
		Local.WalkTo(S, Job, Spot)
		if S.Job == Job then
			Local.Face(S, Desk.Position)
			Brain.Idle(S, 3600, function() return S.Job == Job and not Paused end)
		end
		return
	end
```

- [x] **Step 5: Install and run the tests.**
  - Install `Roster`, `Schedules` and the TestBridge, start Play, and run `bridge.py TimetableTest '$P'`.
  - **Expected:**
    - every `PerRoom[Period n]` is `{R102 ≤6, R103 ≤6, R104 ≤6, R105 ≤6}`, and 6 in each room where no Delinquent
      skipped
    - `Homeroom` is `{R101 12, R102 12}`
    - `Skips` is between 4 and 14 (3 Delinquents × 40 days × about 0.17)
    - `SkipStable true`, `Seg1SetA "R102"`, `Seg2SetA "R103"`
  - **The live check:** `SetTime "09:10"` (Period 2), wait 40 s, then use `gamevm.py` to count `NHActivity` per room.
    Expected: about 6 `In class (R10x)` in each of R102 to R105, and none standing. At `SetTime "08:05"`
    (Homeroom): 9 seated and 3 standing in R101, and the same in R102.

- [x] **Step 6: Commit** `2.28 (3/7): each set's own timetable; full rooms stand at the back; Delinquents skip`.

---

### Task 4: Teachers witness fights and lateness

**Files:**
- Create: `ServerScriptService.Services.School.Teachers.luau`
- Modify: `ServerScriptService.Services.School.Discipline.luau` (the `Attendance.Recorded` handler), TestBridge

**Interfaces:**
- Consumes: `Npcs.Get(NpcId) -> Model?` (exists), `Npcs.PostKey` (Task 2), `Config.Npcs` `Posts`,
  `Regions.Inside(Player, RoomId)`, `Downed.OnDamage(Target, Damage, Attacker)`,
  `Discipline.ReportIncident({Type, Suspect, Witness, Position, Recognized})`
- Produces:
  - `Teachers.AtDesk(RoomId) -> (NpcId?, Model?)`: the teacher whose current post is that room's desk post and who is
    standing within 4 studs of it
  - `Teachers.Sees(Model, Position) -> boolean`: a raycast from the teacher's head that ignores characters
  - `Teachers.NameFor(RoomId) -> string`: the teacher's display name, or "Teacher"
  - `Teachers.WitnessForTests(Player, RoomId) -> { Teacher, Sees, Reported }`

- [x] **Step 1: Write the failing test.** Add to TestBridge:

```lua
-- (2.28) a fight in a class with its teacher at the desk is booked by that teacher; slot 2 is restored by the caller
function Commands.WitnessTest(PlayerName: string, RoomId: string)
	local Player = Players:FindFirstChild(PlayerName)
	return DeepCopy(require(game:GetService(`ServerScriptService`).Services.School.Teachers).WitnessForTests(Player, RoomId))
end
```

  Expected before the change: an error (no `Teachers` module).

- [x] **Step 2: Write `School.Teachers`:**

```lua
--[[ (2.28) Teachers (server). Services.School.Teachers: a subject teacher at their desk is a witness in their room.
	- A combat hit by a student inside a classroom, while that room's teacher stands at the desk and can see the
	  attacker (a raycast from the head that ignores characters), books Fighting through Discipline.ReportIncident,
	  once per player per period, with the teacher's name as the witness.
	- A late mark names the teacher of that room (Discipline asks NameFor).
	docs/expansion/13-Living-School.md §3.2. API: AtDesk(RoomId), Sees(Model, Position), NameFor(RoomId), WitnessForTests ]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Cast = require(ReplicatedStorage.Config.Npcs)

local Shared = {}
local Local = {}
local Reported = {} :: { [Player]: string } -- the period key each player was last booked in
local DESK_RANGE = 4

local function Npcs() return require(ServerScriptService.Services.Social.Npcs) end
local function Places() return require(ServerScriptService.Services.Quests.Places) end

-- the room each desk post belongs to (the Task 1 posts)
local DESK_ROOM = { Sallow = `R102`; [`Hale@R103`] = `R103`; Pryce = `R104`; Whitlock = `R105`; Hale = `R102` }

function Shared.AtDesk(RoomId: string): (string?, Model?)
	local State = require(ServerScriptService.Services.School.SchoolClock).GetState()
	local Seg = State.Segment
	if not (Seg and Seg.Kind == `Class`) then return nil, nil end
	for Id, Npc in Cast do
		if not Npc.Posts then continue end
		local Key = Npcs().PostKey(Id, Seg.Kind, Seg.Name)
		if Key and DESK_ROOM[Key] == RoomId then
			local M = Npcs().Get(Id)
			local Post = Places().Find(`NpcPost`, Key)
			local Root = M and M:FindFirstChild(`HumanoidRootPart`)
			if Root and Post and ((Root.Position - Post.Position) * Vector3.new(1, 0, 1)).Magnitude <= DESK_RANGE then
				return Id, M
			end
		end
	end
	return nil, nil
end

function Shared.Sees(M: Model, Position: Vector3): boolean
	local Head = M:FindFirstChild(`Head`)
	if not Head then return false end
	local Params = RaycastParams.new()
	Params.FilterType = Enum.RaycastFilterType.Exclude
	local Ignore = { M }
	for _, P in Players:GetPlayers() do if P.Character then table.insert(Ignore, P.Character) end end
	local Live = workspace:FindFirstChild(`Live`) if Live then table.insert(Ignore, Live) end
	local Sched = workspace:FindFirstChild(`NHSchedule`) if Sched then table.insert(Ignore, Sched) end
	Params.FilterDescendantsInstances = Ignore
	local Hit = workspace:Raycast(Head.Position, Position - Head.Position, Params)
	return Hit == nil or (Hit.Position - Position).Magnitude < 2
end

function Shared.NameFor(RoomId: string?): string
	local Id = RoomId and Shared.AtDesk(RoomId)
	return if Id then Cast[Id].Name else `Teacher`
end

function Local.RoomOf(Player: Player): string?
	local Regions = require(ServerScriptService.Services.Features.Regions)
	for _, Room in { `R101`, `R102`, `R103`, `R104`, `R105` } do
		if Regions.Inside(Player, Room) then return Room end
	end
	return nil
end

function Local.PeriodKey(): string
	local S = require(ServerScriptService.Services.School.SchoolClock).GetState()
	return `{S.Day}:{S.SegmentIndex}`
end

-- returns what happened, for tests
function Local.Witness(Player: Player): { [string]: any }
	local Room = Local.RoomOf(Player)
	if not Room then return { Room = false } end
	local Id, M = Shared.AtDesk(Room)
	if not (Id and M) then return { Room = Room; Teacher = false } end
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
	local Sees = Root ~= nil and Shared.Sees(M, Root.Position)
	if not Sees then return { Room = Room; Teacher = Id; Sees = false } end
	local Key = Local.PeriodKey()
	if Reported[Player] == Key then return { Room = Room; Teacher = Id; Sees = true; Reported = false; Already = true } end
	Reported[Player] = Key
	local Booked = require(ServerScriptService.Services.School.Discipline).ReportIncident({
		Type = `Fighting`; Suspect = Player; Witness = Cast[Id].Name; Position = Root.Position; Recognized = true;
	})
	return { Room = Room; Teacher = Id; Sees = true; Reported = Booked }
end

function Shared.WitnessForTests(Player: Player, RoomId: string)
	local Out = { AtDesk = (Shared.AtDesk(RoomId)) or false }
	Reported[Player] = nil
	local W = Local.Witness(Player)
	for K, V in W do Out[K] = V end
	return Out
end

function Shared.OnStart()
	local Downed = require(ServerScriptService.Services.Features.Downed)
	Downed.OnDamage:Connect(function(_Target, _Damage, Attacker)
		local Player = Attacker and Players:GetPlayerFromCharacter(Attacker)
		if not Player then return end
		local Ok, Err = pcall(Local.Witness, Player)
		if not Ok then warn(`[Teachers] {Err}`) end
	end)
	Players.PlayerRemoving:Connect(function(P) Reported[P] = nil end)
end

return Shared
```

  **Check before installing:** `Npcs.Get` exists (`Shared.Get(NpcId)`, line 306 of the 2.27 dump); `Places.Find`
  is in `Services.Quests.Places`; `Regions.Inside` is in `Features.Regions`. `SchoolClock.GetState()` returns
  `SegmentIndex`, as HallMonitor uses. If not, use `State.Segment.Name`.

- [x] **Step 3: Late marks name the teacher.** Back up `Discipline`. In its `Attendance.Recorded` handler, replace
  `Shared.AddViolation(Player, Record.Status, { Witness = \`Teacher\` })` with:

```lua
			local Witness = `Teacher`
			pcall(function() Witness = require(game:GetService(`ServerScriptService`).Services.School.Teachers).NameFor(Record.Room) end) -- (2.28)
			Shared.AddViolation(Player, Record.Status, { Witness = Witness })
```

- [x] **Step 4: Install and run the test.**
  - Install `Teachers`, `Discipline` and the TestBridge. Start Play, snapshot, then `SetTime "09:10"` (Period 2).
  - Move the player into Room 104 within the teacher's view: `gamevm.py` pivots the character to 6 studs in front of
    the `Pryce` post, facing it.
  - Run `bridge.py WitnessTest '$P' '"R104"'`. Expected: `AtDesk "Pryce"`, `Room "R104"`, `Teacher "Pryce"`,
    `Sees true`, `Reported true`. In Discipline's recent list (`gamevm.py`), the newest record is `Fighting` with
    `Witness "Mr. Pryce"`.
  - Run it again in the same period. Expected: `Already true`, `Reported false`.
  - **No teacher, no report:** `SetTime "11:30"` (Lunch), then the same command. Expected: `AtDesk false`,
    `Teacher false`.
  - **The real damage path:** at 09:10 in R104, call `Downed.OnDamage:Fire(<a student model>, 5, Player.Character)`
    from `gamevm.py`. One more `Fighting` record with Pryce as witness, if the per-period key was cleared first (stop
    and start Play to clear it).
  - Restore slot 2.

- [x] **Step 5: Commit** `2.28 (4/7): teachers at their desks book fights and name late marks`.

---

### Task 5: Students far from every player have no body

**Files:**
- Modify: `ServerScriptService.Services.Features.Schedules.luau` (`Local.Arrive`, the five jobs, the clock loop, a
  test hook); `ServerScriptService.Services.Social.Roster.luau` (`WhereNow`); TestBridge

**Interfaces:**
- Consumes: `Roster.Body(Id)` (2.27), `Local.Assign`, `S.LastJob`, `S.ReplanNow` (existing)
- Produces:
  - `Local.Arrive(S, Job, Where: Vector3?) -> boolean`. With `Where`, and no player within `WAKE` (160) studs of it, the
    student stays bodiless: `S.Asleep = { At = Where }`, and it returns false.
  - `S.Activity`: the text of what they're doing, set by `Assign`.
  - `Roster.WhereNow(Id) -> { Embodied: boolean, At: Vector3?, Activity: string? }`
  - `Schedules.SleepForTests() -> { Bodies: number, Asleep: number }`

- [x] **Step 1: Write the failing test.** Add to TestBridge:

```lua
-- (2.28) bodies only near players: how many students have a body, and how many are asleep at a spot
function Commands.SleepTest(PlayerName: string)
	return DeepCopy(require(game:GetService(`ServerScriptService`).Services.Features.Schedules).SleepForTests())
end
```

  Expected before the change: an error (`SleepForTests` is nil).

- [x] **Step 2: `Arrive` stays bodiless far from players.** In `Schedules`, add near the top
  `local WAKE, SLEEP = 160, 180 -- (2.28) bodies only near players (doc 13 §3.4); SLEEP > WAKE so they don't flicker`.
  Then replace `Local.Arrive`, and add `Local.Near`:

```lua
function Local.Near(P: Vector3, R: number): boolean
	for _, Pl in Players:GetPlayers() do
		local Root = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
		if Root and (Root.Position - P).Magnitude <= R then return true end
	end
	return false
end

function Local.Arrive(S, Job, Where: Vector3?): boolean
	if S.Model then S.Asleep = nil return true end
	if Where and not Local.Near(Where, WAKE) then -- (2.28) nobody near where they're going: be there, with no body
		S.Asleep = { At = Where }
		return false
	end
	local From = S.WakeAt or Local.Gate() -- (2.28) waking: appear where they already were
	S.WakeAt, S.Asleep = nil, nil
	Local.Spawn(S, From)
	task.wait(0.2)
	return S.Job == Job
end
```

- [x] **Step 3: Each job says where it's going.** Change the first line of each job:
  - **`Local.Mingle`:** `if not Local.Arrive(S, Job, Local.HallSpot()) then return end`
  - **`Local.Class`:** `local Chairs0 = Local.Chairs(RoomId)` and
    `if not Local.Arrive(S, Job, Chairs0[1] and Chairs0[1]:GetPivot().Position) then return end`. Keep the existing
    `local Chairs = Local.Chairs(RoomId)` line after it, and reuse `Chairs0` instead.
  - **`Local.Lunch`:** `local Tagged = CollectionService:GetTagged(\`NHLunchSpot\`)` and
    `if not Local.Arrive(S, Job, Tagged[1] and Tagged[1].Position) then return end`
  - **`Local.Hangout`:** `local Spot0 = S.Clique and Local.FreeSpot(S.Clique)` and
    `if not Local.Arrive(S, Job, if Spot0 then Spot0.Position else Local.HallSpot()) then return end`
  - **`Local.Club`:** `if not Local.Arrive(S, Job, Local.ClubSpot(S.Club) or Local.HallSpot()) then return end`
  - **`Local.Leave`:** add `S.Asleep = nil` before `if not S.Model then return end`. Going home ends being anywhere.

- [x] **Step 4: The sleep/wake check, in the existing 1-second clock loop.** In `Shared.OnStart`'s
  `while true do … task.wait(1) end`, before `task.wait(1)`, add `pcall(Local.SleepWake)`, and define:

```lua
-- (2.28) once a second: a body far from every player goes (they stay where they were, asleep); a sleeper a player
-- comes near wakes there and carries on with their job
function Local.SleepWake()
	if Paused then return end
	for _, S in Students do
		if S.Model and S.Root and not S.Reacting and not S.InScene then
			if not Local.Near(S.Root.Position, SLEEP) then
				local At = S.Root.Position
				Local.Despawn(S)
				S.Asleep = { At = At }
			end
		elseif S.Asleep and Local.Near(S.Asleep.At, WAKE) and S.LastJob then
			S.WakeAt = S.Asleep.At
			S.ReplanNow = true
			Local.Assign(S, S.LastJob.Fn, table.unpack(S.LastJob.Args, 1, S.LastJob.Args.n))
		end
	end
end

function Shared.SleepForTests()
	local Bodies, Asleep = 0, 0
	for _, S in Students do
		if S.Model then Bodies += 1 elseif S.Asleep then Asleep += 1 end
	end
	return { Bodies = Bodies; Asleep = Asleep }
end
```

- **`S.InScene`:** not used until 2.29's scene director; it's checked here so that release needs no change to this
  loop.
- **`S.Activity`:** in `Local.Assign`, after `S.LastJob = …`, add
  `S.Activity = debug.info(Fn, \`n\`) -- (2.28) for Roster.WhereNow`. `debug.info` returns the function name, e.g.
  `Class`; `Local.Class` is named `Class`.

- [x] **Step 5: `Roster.WhereNow`.** Add to `Social.Roster`:

```lua
-- (2.28) where a rostered student is: their body, or the spot they're at with no body
function Shared.WhereNow(Id: string)
	local S = Bodies[Id]
	if not S then return { Embodied = false } end
	if S.Model and S.Root then return { Embodied = true; At = S.Root.Position; Activity = S.Activity } end
	return { Embodied = false; At = S.Asleep and S.Asleep.At; Activity = S.Activity }
end
```

- [x] **Step 6: Install and run the test.**
  - Install `Schedules`, `Roster` and the TestBridge. Start Play (21:30 puts everyone at home).
  - `SetTime "11:30"` (lunch), wait 40 s, and run `bridge.py SleepTest '$P'` with the player beside the concession
    stand (`gamevm.py` pivots them there). Expected: `Bodies` is 24 (all at lunch near you), `Asleep 0`.
  - Move the player to the far end of the grounds, more than 200 studs from the stand (`gamevm.py`, the North Field
    or the Graveyard). Wait 3 s, then run `SleepTest`. Expected: `Bodies 0`, `Asleep 24`.
  - Move back to the stand. Wait 3 s, then run `SleepTest`. Expected: `Bodies 24` again, at the lunch spots (not the
    gate). `Roster.WhereNow("MaeGorse").Activity` (`gamevm.py`) is `"Lunch"`.
  - At `SetTime "09:10"`, stand in R104: about 6 bodies there, and the rest asleep in their rooms.
  - **Performance:** with the player at the stand, and then far away, run the 2.27 heartbeat sample (20 s, server and
    client). Report both against 2.27's numbers (24 students: 42.6 server / 45.9 client; none: 47.0 / 46.8).

- [x] **Step 7: Commit** `2.28 (5/7): students far from every player have no body; WhereNow`.

---

### Task 6: Regression

- [x] **Step 1: Self-tests in one session.**
  - **This release:** `StaffTest`, `StaffPlanTest`, `TimetableTest`, `SleepTest`, and `WitnessTest` with its setup.
  - **2.27:** `RosterTest`, `Rostered`, `RelationshipCapTest`, `MemoryTest`.
  - **Earlier:** `CineJudgeTest` 36/36, `CineGraphTest` 9/9, `CineQteTest`, `CineVoteTest`, `Phase1SelfTest`, and
    `AfterHoursMigrateTest` (1, 2, 5).
- [x] **Step 2: Story staff.**
  - **The prologue roll call** (`bridge.py PlayCut '$P' '"Prologue"' true`, with the 2.26 `t_prologue.lua` started
    first and `NHCinePath` cleared): it still plays with Mr. Hale, through both paths.
  - **The Custodian** still leaves his day post after hours.
  - **Orientation's** Hale talk still works at his Room 102 desk during Homeroom.
- [x] **Step 3: The school day.**
  - Sample 07:40, 08:05, 09:10, 11:30 and 15:30 with the 2.27 `_day.lua`, from near the rooms.
  - Expected: arrivals, homeroom 9+3 per room, sets of 6 in class, lunch, then clubs and hangouts.
- [x] **Step 4: The console.** No errors from Npcs, Teachers, Discipline, Schedules, Roster or StudentBrain.
- [x] **Step 5: Saving.** Run the rejoin and save check on slot 4 "Testy" (`ChooseSlot 4` from the main menu; snapshot
  and restore it). Restore slot 2, stop Play, and run `save_place`.

### Task 7: Docs and release 2.28.0

- [x] **Step 1: CHANGELOG `[2.28.0] - <date>: Staff in the school day (Living School 2 of 4)`.**
  - **Contents:** the staff, posts, timetables, witnesses, the off-screen simulation, and the TestBridge commands.
  - **Checked:** every number from Task 6.
  - **Not checked:** a two-player run, and phone screens.
  - If another session's hunk is in CHANGELOG, stage only this one.
- [x] **Step 2: The other docs.**
  - **README:** a Latest-update line.
  - **Implementation-Status:** a row.
  - **Discord:** a game update in `updates/discord/game-updates/<date>-teachers-take-the-register.md`, plus the index.
  - **Doc 13:** the status says "2.28 shipped", and §9 gets this plan's deltas.
  - **Doc 11:** the port table gets the staff post rows.
- [x] **Step 3: Vault.** Copy the docs over, and add the home-note line.
- [x] **Step 4: Commit and merge.** Commit `2.28.0: Staff in the school day`. Merge into `main` with `--no-ff` and
  `-F <file>`, stashing other sessions' changes around the merge. Don't push unless the owner asks.

---

## Outcome (2026-11-18)

All seven tasks are done; the numbers are in CHANGELOG `[2.28.0]`. Beyond the plan:
- **Mr. Hale:** stays at his Room 102 desk outside class periods (Other and a new Off key), for Orientation. The
  Orientation text was updated.
- **Mira's desk:** `Local.Chairs` leaves it out.
- **Late marks:** `Teachers.NameFor(Room, Period)` names the teacher by the timetable.
- **Room detection:** by the classroom folder (Regions is offset).
- **Sleep check:** cancels the running job before removing the body.
- **The plan's estimates:** the 4 to 14 skip estimate was wrong (about 20 expected), and the "6 bodies in R104"
  check doesn't apply (every classroom is within 160 studs of every other).

## Spec deltas (recorded in doc 13 §9 items 16 to 23)

1. **The Headmaster's office:** the place has no office, portrait or office area. Ashgrave keeps office hours at a new
   post beside the Records Office door during class periods. He maintains the official story, and the files are behind
   that door.
2. **Assemblies and crises:** no such systems exist yet, so the Headmaster doesn't appear at them in 2.28. He gains
   those posts when they're built.
3. **Staff move between posts by fading** (as 2.24's Custodian does), not by walking.
4. **Homeroom:** sets C and D take Mr. Hale's register in Room 102 (the prologue's room), not study hall in the
   Library. Each homeroom room seats 9 and has 3 standing.
5. **Late marks:** a late mark names the room's teacher if they're at the desk, otherwise "Teacher". Attendance still
   decides lateness.
6. **Sallow's homeroom:** she has no homeroom post. She's off during Homeroom, while Hale takes the register in her
   room.

## Self-review

- **Spec coverage (doc 13 §3):**
  - §3.1 is Tasks 1 and 2. The mini-arcs are excluded, as the spec says.
  - §3.2 is Task 4.
  - §3.3 is Task 3.
  - §3.4 is Task 5.
  - §3.5: the acceptance is in Tasks 4 to 6. The 60 fps target is reported against the measured baseline (the 2.27
    finding).
- **Placeholders:** none. The four dialogue trees are complete, and the post script is complete.
- **Types:**
  - `Posts` keys (`Homeroom`, `Class`, `Other`) are the same in Tasks 1, 2 and 4.
  - `PostKey(NpcId, Kind, Name)` is used in Tasks 2 and 4.
  - `Plan(SegName, Id, Day)` returns `{Room, Skip}`, in Task 3 and its test.
  - `S.Asleep.At`, `S.WakeAt` and `S.Activity` are in Task 5 and `WhereNow`.
  - `DESK_ROOM` uses Task 1's post keys.
- **Known risks:**
  - `debug.info(Fn, "n")` returns nil for anonymous functions. All five jobs are named `Local.X` functions, so it
    returns `X`.
  - Waking re-runs the last job from the start. A seated student who wakes walks from the spot to their chair, a few
    studs.
