# Electives: Anatomy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add term electives to Nightmare Highschool and ship Anatomy end to end: enrol at the Registrar, sit the bench in R103 on Tuesday/Thursday periods 3 and 4, and dissect a hollow clockwork specimen with five physical tools.

**Architecture:**
- **Shared config.** `Config.Electives` lists the ten electives. `Config.Classes.For` answers "which class is this player in, in this slot today", and every timetable reader moves to it.
- **The game.** Anatomy is a normal Activities game module (`ServerStorage.Activities.AnatomyBench`) with `Bench = true`. The server judges the intents: Pick, Put, Use and Place.
- **The client.** A full-screen renderer (`Controllers.Gui.Activities.AnatomyBench`) draws the bench in a ViewportFrame + WorldModel, so the rigid-rig props and the seated R6 clips animate there.

**Tech Stack:** Luau in NH Combat Test (edited in place through rbxc), Blender 5.2 headless for the models, Python harness scripts.

**Spec:** `docs/superpowers/specs/2026-11-25-electives-anatomy-design.md` (approved 2026-11-25). Executors read both.

## Global Constraints

- **The place.** NH Combat Test, placeId 98950102230473. Never save the place without the owner's word.
- **One driver.** Only one session drives NH Combat Test at a time. Message the Skate/Pickups/UI session (`local_82def5e0` family, E:/NH-main) before any Play, and again when done.
- **Harness scripts.** Use private copies of the harness only, in `tools/electives/harness/`: `fetch.py`, `install_inplace.py`, `run_live.py` and `pure.py`. Never edit another feature's copies.
- **Snapshots.** Before editing a script, fetch its current Source into `tools/electives/pre/`. The edited copy goes in `tools/electives/live/<Dotted.Path>.luau`. Install it with `install_inplace.py`.
- **Play-round protocol, in order:**
  1. `start_stop_play` true.
  2. `bash tools/forms/harness/round_start.sh`.
  3. Cine check: `run_check.py Server tools/soccer2/checks/cine.lua`.
  4. Your checks.
  5. `python -X utf8 -I tools/forms/harness/restore.py`, repeated until it prints `restored`.
  6. Cine check again.
  7. Stop.
- **Rigs and import.** R6 rigs. R6 kneels copy Crouch 139672322709288. Reuse existing animations where they fit.
- **Unpublished clips.** They play in Studio through `KeyframeSequenceProvider:RegisterKeyframeSequence` from `ReplicatedStorage.AnatomyClips`. The owner publishes them.
- **Rigid rigs.** Multi-piece props follow `docs/Pipeline-Lessons.md`: the `RIGID` table, then `art/props/anim/<Prop>_rigid.json`, then import with "Import as rig" off, then `python tools/phase6-2350/stage/rigid_rig.py`. FBX imports come in about 100× too big. Textures go on with `stage/textures.lua`.
- **No clipping.** Every exported model passes `tools/electives/render/clipcheck.py` with 0 intersections outside `ALLOW`.
- **UI.** Built from `ReplicatedStorage.UI.Theme`, `Components` and `Motion`. Fonts are Cinzel and EB Garamond. The chrome images come from `art/ui/hud/make_anatomy_ui.py`.
- **Grading.** Accuracy 60%, process 25%, time 15%. Grades are A+ ≥ 97, A ≥ 90, B ≥ 80, C ≥ 70, D ≥ 60, else F. C passes.
- **Tool order and keys:** 1 Key, 2 Driver, 3 Loupe, 4 Scalpel, 5 Tweezers. Right-click or B puts a tool down.
- **Elective slots.** Period 3 (10:00–10:40) and Period 4 (10:45–11:25) on Tuesday (weekday 1) and Thursday (weekday 3), where weekday = `Day % 5`. Anatomy is in R103 with Mr. Sallow.
- **Commits.** Commit after each task on `claude/electives-22bb10`. End messages with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Don't push or merge without asking.
- **graphify.** Run `graphify update .` after code changes when graphify is installed. Today it is not, so note that in the REPORT.

## File map

| File | Responsibility |
|---|---|
| `ReplicatedStorage.Config.Electives` (new) | The ten electives, their rooms, teachers and seals; which are open |
| `ReplicatedStorage.Config.Classes` (modify) | Adds `ElectiveSlots` and `Classes.For(SegmentName, Day, PickOrPlayer)` |
| `ReplicatedStorage.Config.Anatomy` (new) | Species, steps, organs, tools, scoring constants |
| `ServerStorage.Activities.AnatomyBench` (new) | The rules and judging (server, pure; no instances) |
| `ServerScriptService.Services.School.Electives` (new) | Enrolment: term pick, the `ElectivePick` attribute, saving, the Registrar prompt |
| `ServerScriptService.Services.School.Activities` (modify) | Slot lookup through `Classes.For`, `Bench` sessions, the Specimen twist, the Anatomy rewards hook |
| `ServerScriptService.Services.School.Attendance` / `Substitutes` (modify) | Per-player slot lookup; electives join the substitute pool |
| `ReplicatedStorage.Config.Substitutes` (modify) | `Subjects` adds `Anatomy`; the `Specimen` twist |
| `StarterPlayerScripts.Controllers.Gui.{ClockHud, Moments, Timetable, Phone, KitUi}` (modify) | Read slots through `Classes.For` |
| `StarterPlayerScripts.Controllers.Gui.Activities` (modify) | Full-screen content for `Def.Bench` games |
| `StarterPlayerScripts.Controllers.Gui.Activities.AnatomyBench` (new) | The bench renderer: viewport, tools, input, clips |
| `StarterPlayerScripts.Controllers.Gui.Registrar` (new) | The seal-card enrolment board |
| `ReplicatedStorage.Anatomy` (new folder) | Bench models (rigid rigs), tool models, UI image ids |
| `ReplicatedStorage.AnatomyClips` (new folder) | Unpublished KeyframeSequences: nine R6 clips plus prop clips |
| `tools/electives/` | Harness copies, `pre/`, `live/`, `checks/`, `render/`, `REPORT.md`, `PUBLISH_LIST.md` |

---

### Task 1: Electives config and `Classes.For`

**Files:**
- Create: `tools/electives/live/ReplicatedStorage.Config.Electives.luau`
- Modify: `tools/electives/live/ReplicatedStorage.Config.Classes.luau` (copied from `pre/`)
- Create: `tools/electives/harness/pure.py` (a copy of `tools/soccer2/harness/pure.py`, unchanged)
- Test: `tools/electives/checks/classes_pure.lua`

**Interfaces:**
- Produces:
  - `Electives.List: { [Id]: { Id, Name, Room, Teacher, Open: boolean, Order: number } }`
  - `Electives.Get(Id: string?) -> Def?`
  - `Classes.ElectiveSlots = { Days = {[1]=true,[3]=true}, Segments = {["Period 3"]=true,["Period 4"]=true} }`
  - `Classes.StudyHall = { Subject = "Study Hall", Room = "R101" }`
  - `Classes.IsElectiveSlot(SegmentName: string, Day: number) -> boolean`
  - `Classes.For(SegmentName: string, Day: number, PickOrPlayer: string | Player | nil) -> { Subject, Room, Elective: boolean }?`. It returns nil for a segment that isn't a class.

- [ ] **Step 1: Write the failing pure check** `tools/electives/checks/classes_pure.lua`

```lua
-- classes_pure (electives Task 1). usage: python -X utf8 -I tools/electives/harness/pure.py tools/electives/checks/classes_pure.lua
local function load(name)
	local Src = __SRC and __SRC[name]
	if not Src then error("FAIL source not inlined: " .. name) end
	local Fn, Err = loadstring(Src)
	if not Fn then error("FAIL parse " .. name .. ": " .. tostring(Err)) end
	return Fn()
end
local Fails = {}
local function Eq(G, W, What) if G ~= W then table.insert(Fails, What .. ": got " .. tostring(G) .. " want " .. tostring(W)) end end
local E = load("ReplicatedStorage.Config.Electives.luau")
local n, open = 0, 0
for Id, D in E.List do n += 1 if D.Open then open += 1 end Eq(D.Id, Id, "id matches key " .. Id) end
Eq(n, 10, "ten electives") Eq(open, 1, "one open") Eq(E.Get("Anatomy").Room, "R103", "Anatomy room")
Eq(E.Get("Nope"), nil, "unknown id")
-- Classes.For: Config.Classes requires Electives through script.Parent, so the check swaps in a stub require
local RealRequire = require
getfenv().require = function(M) if M == "Electives" then return E end return RealRequire(M) end
local C = load("ReplicatedStorage.Config.Classes.luau")
Eq(C.For("Period 3", 0, "Anatomy").Subject, "English", "Monday P3 stays English")
Eq(C.For("Period 3", 1, "Anatomy").Subject, "Anatomy", "Tuesday P3 is the pick")
Eq(C.For("Period 4", 3, "Anatomy").Room, "R103", "Thursday P4 room")
Eq(C.For("Period 4", 3, "Anatomy").Elective, true, "flagged elective")
Eq(C.For("Period 3", 6, "Anatomy").Subject, "Anatomy", "day 6 is a Tuesday (6 % 5 = 1)")
Eq(C.For("Period 3", 1, nil).Subject, "Study Hall", "no pick: study hall")
Eq(C.For("Period 3", 1, "Workshop").Subject, "Study Hall", "a closed elective: study hall")
Eq(C.For("Period 2", 1, "Anatomy").Subject, "Chemistry", "other periods untouched")
Eq(C.For("Lunch", 1, "Anatomy"), nil, "not a class")
Eq(C.IsElectiveSlot("Period 4", 1), true, "slot yes") Eq(C.IsElectiveSlot("Period 2", 1), false, "slot no")
if #Fails > 0 then return "FAIL\n" .. table.concat(Fails, "\n") end
return "PASS classes_pure"
```

The stub `require` is there because a loadstring chunk has no sibling `Electives` to require. The module falls back to `require("Electives")` when `script.Parent.Electives` isn't there (see Step 3).

- [ ] **Step 2: Run it to see it fail**

Run: `python -X utf8 -I tools/electives/harness/pure.py tools/electives/checks/classes_pure.lua`. pure.py reads `live/` relative to the harness folder, so the check paths resolve to `tools/electives/live/`.
Expected: `FAIL ... no such file` (the live files don't exist yet).

- [ ] **Step 3: Write `Config.Electives` and change `Config.Classes`**

`tools/electives/live/ReplicatedStorage.Config.Electives.luau`:

```lua
--[[
	Electives (shared). One pick per term at the Registrar (Services.School.Electives); it fills
	Config.Classes.ElectiveSlots (Tue/Thu, periods 3 and 4). Only Open electives can be picked.
]]
local Electives = {}

Electives.List = {
	Anatomy     = { Id = `Anatomy`;     Name = `Anatomy`;     Room = `R103`; Teacher = `Mr. Sallow`; Open = true;  Order = 1 };
	Workshop    = { Id = `Workshop`;    Name = `Workshop`;    Room = `R103`; Teacher = ``; Open = false; Order = 2 };
	Photography = { Id = `Photography`; Name = `Photography`; Room = `R103`; Teacher = ``; Open = false; Order = 3 };
	Ceramics    = { Id = `Ceramics`;    Name = `Ceramics`;    Room = `R103`; Teacher = ``; Open = false; Order = 4 };
	Herbology   = { Id = `Herbology`;   Name = `Herbology`;   Room = `R103`; Teacher = ``; Open = false; Order = 5 };
	HomeEc      = { Id = `HomeEc`;      Name = `Home Ec`;     Room = `R103`; Teacher = ``; Open = false; Order = 6 };
	Sewing      = { Id = `Sewing`;      Name = `Sewing`;      Room = `R103`; Teacher = ``; Open = false; Order = 7 };
	Art         = { Id = `Art`;         Name = `Art`;         Room = `R103`; Teacher = ``; Open = false; Order = 8 };
	PE          = { Id = `PE`;          Name = `PE`;          Room = `R103`; Teacher = ``; Open = false; Order = 9 };
	Theatre     = { Id = `Theatre`;     Name = `Theatre`;     Room = `R103`; Teacher = ``; Open = false; Order = 10 };
}

function Electives.Get(Id: string?)
	return if typeof(Id) == `string` then Electives.List[Id] else nil
end

return Electives
```

The closed electives keep `R103` as a placeholder room. They can never be picked, so their room is never used until their own spec sets it.

In `Config.Classes`:
- Put the require above `return {`.
- Change `return {` to `local Classes = {`.
- Add the slots and the helpers.
- End the file with `return Classes`.

```lua
local Electives = if script and script.Parent and script.Parent:FindFirstChild(`Electives`) then require(script.Parent.Electives) else require("Electives")
local SchoolDays = 5 -- Config.SchoolSchedule.DayNames (Monday..Friday); weekday = Day % SchoolDays

-- (after the Attendance table, before `return Classes`)
Classes.ElectiveSlots = {
	Days = { [1] = true; [3] = true };                       -- Tuesday, Thursday
	Segments = { [`Period 3`] = true; [`Period 4`] = true };
}
Classes.StudyHall = { Subject = `Study Hall`; Room = `R101` }

function Classes.IsElectiveSlot(SegmentName: string, Day: number): boolean
	return Classes.ElectiveSlots.Segments[SegmentName] == true and Classes.ElectiveSlots.Days[Day % SchoolDays] == true
end

-- The class a player has in a slot. PickOrPlayer: an elective id, or a Player (reads its ElectivePick attribute).
function Classes.For(SegmentName: string, Day: number, PickOrPlayer: any)
	local Base = Classes.Periods[SegmentName]
	if not Base then return nil end
	if typeof(Day) ~= `number` or not Classes.IsElectiveSlot(SegmentName, Day) then
		return { Subject = Base.Subject; Room = Base.Room; Elective = false }
	end
	local Pick = PickOrPlayer
	if typeof(PickOrPlayer) == `Instance` then Pick = PickOrPlayer:GetAttribute(`ElectivePick`) end
	local Def = Electives.Get(Pick)
	if Def and Def.Open then
		return { Subject = Def.Id; Room = Def.Room; Elective = true }
	end
	return { Subject = Classes.StudyHall.Subject; Room = Classes.StudyHall.Room; Elective = true }
end
```

Also add `R103 = \`Room 103\`` (it is already in `Rooms`). Leave `Periods` unchanged.

- [ ] **Step 4: Run the check to see it pass**

Run: `python -X utf8 -I tools/electives/harness/pure.py tools/electives/checks/classes_pure.lua`
Expected: `PASS classes_pure`

- [ ] **Step 5: Install and commit**

```bash
python -X utf8 -I tools/electives/harness/install_inplace.py tools/electives/live/ReplicatedStorage.Config.Classes.luau
python -X utf8 -I tools/electives/harness/install_inplace.py tools/electives/live/ReplicatedStorage.Config.Electives.luau --create ModuleScript
git add tools/electives && git commit -m "Electives: Config.Electives and Classes.For (Tue/Thu periods 3-4)"
```

`install_inplace.py` is a copy of the admin-console tool. If it has no `--create` flag, make the ModuleScript first with an rbxc one-liner (`Instance.new("ModuleScript", game.ReplicatedStorage.Config).Name = "Electives"`) and then install into it.

---

### Task 2: Server readers use `Classes.For`

**Files:**
- Modify (fetch into `pre/` first, then edit copies in `live/`):
  - `ServerScriptService.Services.School.Activities`
  - `ServerScriptService.Services.School.Attendance`
  - `ServerScriptService.Services.School.Substitutes`
  - `ServerScriptService.Services.Studio.TestBridge`
  - `ServerScriptService.Services.Features.Admin`
- Test: `tools/electives/checks/slots_edit.lua`

**Interfaces:**
- Consumes: `Classes.For` and `Classes.IsElectiveSlot` (Task 1).
- Produces:
  - `Activities.SlotFor(Player) -> ({Subject, Room, Elective}?, SegmentName?)` for the current clock state.
  - Lesson prompts exist on every room that any slot can use. That includes R103, which hosts both Chemistry and Anatomy.

- [ ] **Step 1: Fetch the current sources**

```bash
cd tools/electives && python -X utf8 -I harness/fetch.py pre ServerScriptService.Services.Studio.TestBridge ServerScriptService.Services.Features.Admin
```

(Activities, Attendance and Substitutes are already in `pre/` from planning. Re-fetch them if more than a day has passed.)

- [ ] **Step 2: Write the Edit check** `tools/electives/checks/slots_edit.lua`

```lua
-- slots_edit (electives Task 2): every server reader of Classes.Periods goes through Classes.For.
local Bad = {}
for _, Path in { "ServerScriptService.Services.School.Activities", "ServerScriptService.Services.School.Attendance",
		"ServerScriptService.Services.School.Substitutes" } do
	local N = game for S in Path:gmatch("[^%.]+") do N = N:FindFirstChild(S) end
	local Src = N.Source
	for Line in Src:gmatch("[^\n]+") do
		if Line:find("Classes.Periods[", 1, true) and not Line:find("-- base", 1, true) then table.insert(Bad, Path .. ": " .. Line) end
	end
	if not Src:find("Classes.For(", 1, true) then table.insert(Bad, Path .. ": never calls Classes.For") end
end
if #Bad > 0 then return "FAIL\n" .. table.concat(Bad, "\n") end
return "PASS slots_edit"
```

Run: `python -X utf8 -I tools/electives/harness/run_live.py Edit tools/electives/checks/slots_edit.lua`
Expected: FAIL. It lists Activities lines 124/449, Attendance and Substitutes.

- [ ] **Step 3: Change Activities**

Replace `Local.SubjectForRoom` and the slot test in `TryStart`:

```lua
-- the class this player has right now (nil outside class time)
function Shared.SlotFor(Player: Player)
	local State = SchoolClock.GetState()
	if State.Segment.Kind ~= `Class` then return nil, nil end
	return Classes.For(State.Segment.Name, State.Day, Player), State.Segment.Name
end
```

In `TryStart`, remove the old `local Subject = Local.SubjectForRoom(RoomId)` and the `Current` block, and use:

```lua
	local Slot = Shared.SlotFor(Player)
	local Subject = Slot and Slot.Subject
	if not Slot or Slot.Room ~= RoomId or not Config.Subjects[Subject] then
		local Here = Local.AnySubjectForRoom(RoomId)
		Notifications.Notify(Player, { Title = if Here then `No {Here} class for you right now` else `No class here right now`; Text = `Check the timetable.`; Kind = `Info`; Duration = 3 })
		return
	end
```

Keep a room-to-subject lookup for the message and the prompts, covering both base periods and electives:

```lua
local Electives = require(ReplicatedStorage.Config.Electives)
function Local.AnySubjectForRoom(RoomId: string): string?
	for _, Class in Classes.Periods do -- base
		if Class.Room == RoomId then return Class.Subject end
	end
	for _, D in Electives.List do if D.Open and D.Room == RoomId then return D.Name end end
	return nil
end
```

In `CreatePrompts`, loop over the set of rooms from `Classes.Periods` plus the open electives' rooms (dedupe with a table). Set `Prompt.ObjectText = \`Lesson\``, because one desk can host two subjects.

- [ ] **Step 4: Change Attendance and Substitutes**

- **Attendance.** Read its single `Classes.Periods[...]` use first. Wherever it resolves the current class for a player, replace it with `Classes.For(Segment.Name, State.Day, Player)`. If it computes per segment rather than per player, move the lookup inside the per-player loop.
- **Substitutes.** `Local.RoomFor(Subject)` gains an elective branch:

```lua
local Electives = require(ReplicatedStorage.Config.Electives)
function Local.RoomFor(Subject: string): string?
	for _, P in Classes.Periods do if P.Subject == Subject then return P.Room end end -- base
	local D = Electives.Get(Subject)
	return D and D.Room or nil
end
```

The same file must call `Classes.For` once. Do it in `For(Subject)`: today's entry for an elective only applies when today is an elective day (`Classes.IsElectiveSlot("Period 3", Day)`). Use `Classes.For("Period 3", Day, Subject).Subject == Subject` as the gate.

TestBridge and Admin keep their `Periods` reads (debug readouts). Add `-- base` to those lines so it's clear they show the base table.

- [ ] **Step 5: Install, re-run the check, commit**

```bash
for f in Activities Attendance Substitutes; do python -X utf8 -I tools/electives/harness/install_inplace.py tools/electives/live/ServerScriptService.Services.School.$f.luau; done
python -X utf8 -I tools/electives/harness/run_live.py Edit tools/electives/checks/slots_edit.lua
```

Expected: `PASS slots_edit`.

```bash
git add tools/electives && git commit -m "Electives: server timetable readers go through Classes.For"
```

---

### Task 3: Client readers use `Classes.For`

**Files:**
- Modify (fetch, edit, install): `StarterPlayer.StarterPlayerScripts.Controllers.Gui.{ClockHud, Moments, Timetable, Phone, KitUi}`
- Test: `tools/electives/checks/slots_client_edit.lua`

**Interfaces:**
- Consumes: `Classes.For(SegmentName, Day, Players.LocalPlayer)`. The client reads `ElectivePick`, which the server replicates as a Player attribute (Task 4).

- [ ] **Step 1: Fetch the five scripts and list every `Periods` line**

```bash
cd tools/electives && python -X utf8 -I harness/fetch.py pre StarterPlayer.StarterPlayerScripts.Controllers.Gui.ClockHud StarterPlayer.StarterPlayerScripts.Controllers.Gui.Moments StarterPlayer.StarterPlayerScripts.Controllers.Gui.Timetable StarterPlayer.StarterPlayerScripts.Controllers.Gui.KitUi
grep -n "Periods" pre/StarterPlayer.StarterPlayerScripts.Controllers.Gui.*.luau
```

(Phone is already in `pre/`.) Expect 2 + 1 + 3 + 2 + 4 hits.

- [ ] **Step 2: Write the check.** Copy `slots_edit.lua` and change the path list to the five client scripts. Expect FAIL before the edits.

- [ ] **Step 3: Change each reader**

Each one swaps `Classes.Periods[Name]` for `Classes.For(Name, Day, Players.LocalPlayer)`. Day comes from the same `SchoolTime.GetState(...)` the script already uses for the time (`St.Day`).
- **Whole-day lists (Timetable, Phone).** Loop over `Config.SchoolSchedule.Segments` in order and call `For` with the day being shown.
- **Studying a closed elective.** Timetable shows "Study Hall" with the hint "Enrol at the Registrar".
- **Live updates.** Every reader re-renders on `Players.LocalPlayer:GetAttributeChangedSignal("ElectivePick")`.

Lines that only list subjects (for example KitUi's subject-to-kit map) keep the base table and get `-- base`.

- [ ] **Step 4: Install, run the check (expect PASS), commit**

```bash
git add tools/electives && git commit -m "Electives: client timetable readers go through Classes.For"
```

---

### Task 4: Enrolment service and Registrar board

**Files:**
- Create: `tools/electives/live/ServerScriptService.Services.School.Electives.luau`
- Create: `tools/electives/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.Registrar.luau`
- Modify: `ReplicatedStorage.Remotes.Packets` (add `ElectiveEnrol`, client → server: `{ Id: string }`)
- Test: `tools/electives/checks/electives_play.lua` (Server, in a Play round)

**Interfaces:**
- Consumes: `Electives.Get`, `SchoolClock.Calendar() -> { Week, Term, Year, WeekCount }`, `Data.GetProfile(Player)`.
- Produces:
  - Player attribute `ElectivePick: string?`.
  - `Profile.Classes.Electives = { Term = number, Pick = string }`.
  - `Electives.Enrol(Player, Id) -> (ok: boolean, reason: string?)`.
  - `Electives.PickFor(Player) -> string?`.
  - Test hook `Electives.ForceForTests(Player, Id?)`.

- [ ] **Step 1: Write the Play check** `tools/electives/checks/electives_play.lua`

```lua
-- electives_play (Task 4): enrol, the attribute, the term lock, a closed elective refused. Server VM, in Play.
local SSS = game:GetService("ServerScriptService")
local E = require(SSS.Services.School.Electives)
local P = game:GetService("Players"):GetPlayers()[1]
assert(P, "FAIL no player")
local Fails = {}
local function Eq(G, W, What) if G ~= W then table.insert(Fails, What .. ": got " .. tostring(G) .. " want " .. tostring(W)) end end
E.ForceForTests(P, nil)
Eq(P:GetAttribute("ElectivePick"), nil, "cleared")
local ok, why = E.Enrol(P, "Workshop") Eq(ok, false, "closed refused") Eq(why, "Closed", "reason")
ok = E.Enrol(P, "Anatomy") Eq(ok, true, "Anatomy enrols") Eq(P:GetAttribute("ElectivePick"), "Anatomy", "attribute")
ok, why = E.Enrol(P, "Anatomy") Eq(ok, false, "same term again") Eq(why, "Locked", "locked this term")
Eq(E.PickFor(P), "Anatomy", "PickFor")
if #Fails > 0 then return "FAIL\n" .. table.concat(Fails, "\n") end
return "PASS electives_play"
```

- [ ] **Step 2: Write the service**

```lua
--[[
	Electives (server): one elective per term, picked at the Registrar desk next to NHEnrollDesk.
	Saved as Profile.Classes.Electives = { Term, Pick }; mirrored to the Player attribute ElectivePick
	(Config.Classes.For reads it on both sides). A pick holds for its term; a new term clears the lock, not the pick.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local Packets = require(ReplicatedStorage.Remotes.Packets)
local Config = require(ReplicatedStorage.Config.Electives)
local Interaction = require(ReplicatedStorage.Config.Interaction)
local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local Data = require(ServerScriptService.Services.Player.Data)
local Notifications = require(ServerScriptService.Services.Features.Notifications)

local Shared = {}
local Local = {}

function Local.Record(Player: Player)
	local Profile = Data.GetProfile(Player)
	if not Profile then return nil end
	if typeof(Profile.Classes) ~= `table` then Profile.Classes = {} end
	local R = Profile.Classes.Electives
	if typeof(R) ~= `table` then R = { Term = 0; Pick = `` } Profile.Classes.Electives = R end
	return R
end

function Shared.PickFor(Player: Player): string?
	local R = Local.Record(Player)
	local Def = R and Config.Get(R.Pick)
	return if Def and Def.Open then Def.Id else nil
end

function Shared.Enrol(Player: Player, Id: string): (boolean, string?)
	local Def = Config.Get(Id)
	if not Def then return false, `Unknown` end
	if not Def.Open then return false, `Closed` end
	local R = Local.Record(Player)
	if not R then return false, `NoData` end
	local Term = SchoolClock.Calendar().Term
	if R.Term == Term and R.Pick ~= `` then return false, `Locked` end
	R.Term, R.Pick = Term, Def.Id
	Player:SetAttribute(`ElectivePick`, Def.Id)
	Notifications.Notify(Player, { Title = `Enrolled: {Def.Name}`; Text = `Tuesdays and Thursdays, periods 3 and 4. Room {Def.Room:sub(2)}.`; Kind = `Success`; Duration = 4 })
	return true, nil
end

function Shared.ForceForTests(Player: Player, Id: string?)
	local R = Local.Record(Player)
	if R then R.Term, R.Pick = 0, Id or `` end
	Player:SetAttribute(`ElectivePick`, Id)
end

function Local.OnJoin(Player: Player)
	for _ = 1, 40 do if Data.GetProfile(Player) then break end task.wait(0.25) end
	Player:SetAttribute(`ElectivePick`, Shared.PickFor(Player))
end

function Local.Prompt()
	local Desk = workspace:FindFirstChild(`NHRegistrarDesk`, true)
	if not Desk then warn(`[Electives] NHRegistrarDesk missing`) return end
	local Part = if Desk:IsA(`BasePart`) then Desk else Desk.PrimaryPart or Desk:FindFirstChildWhichIsA(`BasePart`, true)
	local Prompt = Instance.new(`ProximityPrompt`)
	Prompt.Name = `RegistrarPrompt`
	Prompt.ActionText = `Choose an elective`
	Prompt.ObjectText = `The Registrar`
	Prompt.KeyboardKeyCode = Interaction.PromptKey
	Prompt.GamepadKeyCode = Interaction.GamepadKey
	Prompt.HoldDuration = 0.3
	Prompt.MaxActivationDistance = 10
	Prompt.Parent = Part
	Prompt.Triggered:Connect(function(Player)
		local R = Local.Record(Player)
		Packets.ElectiveEvent:FireClient(Player, { Type = `Open`; Pick = Shared.PickFor(Player); Locked = R and R.Term == SchoolClock.Calendar().Term and R.Pick ~= `` })
	end)
end

function Shared.OnStart()
	Players.PlayerAdded:Connect(Local.OnJoin)
	for _, P in Players:GetPlayers() do task.spawn(Local.OnJoin, P) end
	Packets.ElectiveEnrol.OnServerEvent:Connect(function(Player, Msg)
		if typeof(Msg) ~= `table` or typeof(Msg.Id) ~= `string` then return end
		local Ok, Why = Shared.Enrol(Player, Msg.Id)
		Packets.ElectiveEvent:FireClient(Player, { Type = `Result`; Ok = Ok; Why = Why; Pick = Shared.PickFor(Player) })
	end)
	Local.Prompt()
end

return Shared
```

Check how `Packets` declares remotes before adding these two: read `ReplicatedStorage.Remotes.Packets`, copy the `ActivityEvent` / `ActivityAction` pattern for `ElectiveEvent` / `ElectiveEnrol`, and check how services are started (an `OnStart` loader) so `Electives` is picked up.

- [ ] **Step 3: Place the Registrar desk**

1. Find `NHEnrollDesk` (`workspace:FindFirstChild("NHEnrollDesk", true)`).
2. Clone it as a Model named `NHRegistrarDesk`, offset 8 studs along the desk's right vector.
3. Raycast down so it rests on the floor, and check it doesn't overlap: `workspace:GetPartBoundsInBox` must return nothing but floor parts.
4. Add a `SurfaceGui` sign reading "THE REGISTRAR" (Cinzel, candle gold #ebcd78).

- [ ] **Step 4: Write the board UI** `Controllers.Gui.Registrar`

- **Layout.** Copy the approved canvas board (`Registrar.dc.html`). Ten seal cards in Order on a 5×2 grid. Anatomy shows "Open · Room 103". The others show "Later term" and, when tapped, the toast "Opens in a later term".
- **Detail panel.** For the selected open elective: the room, teacher and days line, the three "What it teaches you" lines, the species line, and the "Enrol for Term N" button. When `Locked`, the button reads "Enrolled for this term" and is disabled.
- **Build.** Use the kit: `ReplicatedStorage.UI.Components` (Board frame, Button), `Theme` and `Motion` (open/close 200–300 ms, a fade only when reduced motion is on). Pressing Enrol fires `ElectiveEnrol`. On `Result.Ok`, play the wax-seal stamp (AnatSeal image scaled 1.4 → 1 over 180 ms) and close after 900 ms.
- **Input.** Gamepad: D-pad moves between cards, A selects, B closes (follow `Controllers.Gui.GamepadControls`, the way Activities does).

- [ ] **Step 5: Play round**

1. Message the Skate session.
2. Run the play-round protocol (Global Constraints), with your check step being `python -X utf8 -I tools/electives/harness/run_live.py Server tools/electives/checks/electives_play.lua`. Expected: `PASS electives_play`.
3. Take one screenshot of the board open, at `tools/electives/shots/registrar.png`.
4. Restore, cine, stop, and message the Skate session.

- [ ] **Step 6: Commit**

```bash
git add tools/electives && git commit -m "Electives: Registrar desk, term enrolment, ElectivePick"
```

---

### Task 5: Anatomy config

**Files:**
- Create: `tools/electives/live/ReplicatedStorage.Config.Anatomy.luau`
- Test: `tools/electives/checks/anatomy_config_pure.lua`

**Interfaces:**
- Produces:
  - `Anatomy.Tools = { "Key", "Driver", "Loupe", "Scalpel", "Tweezers" }` (index = hotkey).
  - `Anatomy.Weights = { Accuracy = 0.6, Process = 0.25, Time = 0.15 }`.
  - `Anatomy.SpeciesFor(Level: number, Override: string?) -> SpeciesDef`.
  - `SpeciesDef = { Id, Name, Latin, Level, TimeLimit, Par, Steps: { Step }, Organs: { Organ }, Seam: { Rx, Ry }, FlagFrom: number? }`.
  - `Step = { Id, Tool, Target, Count? }`.
  - `Organ = { Id, Name, Slot, First?: boolean, Flag?: boolean }`.
  - `Anatomy.SlipCost = 0.08`, `Anatomy.RecoilSeconds = 0.8`, `Anatomy.TraceTolerance = 0.08`, `Anatomy.TraceCoverage = 0.9`, `Anatomy.UseInterval = 0.12`.

- [ ] **Step 1: Write the failing pure check**

```lua
-- anatomy_config_pure (Task 5)
local function load(name) local Fn = loadstring(__SRC[name]) return Fn() end
local A = load("ReplicatedStorage.Config.Anatomy.luau")
local Fails = {}
local function Eq(G, W, What) if G ~= W then table.insert(Fails, What .. ": got " .. tostring(G) .. " want " .. tostring(W)) end end
Eq(#A.Tools, 5, "five tools") Eq(A.Tools[1], "Key", "1 Key") Eq(A.Tools[5], "Tweezers", "5 Tweezers")
Eq(A.Weights.Accuracy + A.Weights.Process + A.Weights.Time, 1, "weights sum to 1")
Eq(A.SpeciesFor(1).Id, "Frog", "lvl 1 frog") Eq(A.SpeciesFor(2).Id, "Frog", "lvl 2 frog")
Eq(A.SpeciesFor(3).Id, "Raven", "lvl 3 raven") Eq(A.SpeciesFor(5).Id, "Wyvern", "lvl 5 wyvern")
Eq(A.SpeciesFor(1, "Wyvern").Id, "Wyvern", "crate override")
for _, Id in { "Frog", "Raven", "Wyvern" } do
	local S = A.Species[Id]
	local Valid = {} for _, T in A.Tools do Valid[T] = true end
	for _, St in S.Steps do if not Valid[St.Tool] then table.insert(Fails, Id .. " step " .. St.Id .. " bad tool") end end
	local Slots = {} for _, O in S.Organs do if not O.Flag then Eq(Slots[O.Slot], nil, Id .. " slot unique " .. O.Slot) Slots[O.Slot] = true end end
	Eq(S.Steps[#S.Steps].Id, "Lift", Id .. " ends with Lift")
end
Eq(#A.Species.Frog.Organs, 3, "frog organs")
if #Fails > 0 then return "FAIL\n" .. table.concat(Fails, "\n") end
return "PASS anatomy_config_pure"
```

Run it. Expected: FAIL, because the source isn't inlined yet.

- [ ] **Step 2: Write the config**

```lua
--[[
	Anatomy (shared): the bench elective. Species are data; the engine (ServerStorage.Activities.AnatomyBench)
	walks Steps in order, then the Lift step until every non-Flag organ is placed on its Slot.
	Tools are on the roll in hotkey order. Seam: the plate seam as an ellipse in plate space (unit = plate radius).
]]
local Anatomy = {}

Anatomy.Tools = { `Key`, `Driver`, `Loupe`, `Scalpel`, `Tweezers` }
Anatomy.Weights = { Accuracy = 0.6; Process = 0.25; Time = 0.15 }
Anatomy.SlipCost = 0.08        -- accuracy lost per slip (x2 under Crane's Inspection)
Anatomy.WrongToolCost = 0.15   -- process lost per use with the wrong tool or out of order
Anatomy.RecoilSeconds = 0.8    -- input ignored after a slip
Anatomy.TraceTolerance = 0.08  -- how far off the seam a trace point may be (fraction of the radius)
Anatomy.TraceCoverage = 0.9    -- share of the seam's angle a trace must sweep
Anatomy.UseInterval = 0.12     -- min seconds between counted Key/Driver turns

Anatomy.Species = {
	Frog = {
		Id = `Frog`; Name = `Clockwork Frog`; Latin = `Rana Horologica`; Level = 1; TimeLimit = 120; Par = 60;
		FlagFrom = 4; Seam = { Rx = 1; Ry = 1.3 };
		Steps = {
			{ Id = `Unwind`; Tool = `Key`; Target = `SideKey`; Count = 8 };
			{ Id = `Trace`; Tool = `Scalpel`; Target = `Seam` };
			{ Id = `Pry`; Tool = `Driver`; Target = `Plate` };
			{ Id = `Lift`; Tool = `Tweezers`; Target = `Organ` };
		};
		Organs = {
			{ Id = `HeartPump`; Name = `Heart-pump`; Slot = `Heart` };
			{ Id = `Lungs`; Name = `Bellows lungs`; Slot = `Lungs` };
			{ Id = `GearGut`; Name = `Gear-gut`; Slot = `Gut` };
			{ Id = `FlagCog`; Name = `Loose cog`; Slot = `Flag`; Flag = true };
		};
	};
	Raven = {
		Id = `Raven`; Name = `Clockwork Raven`; Latin = `Corvus Mechanicus`; Level = 3; TimeLimit = 150; Par = 80;
		FlagFrom = 4; Seam = { Rx = 1; Ry = 1.6 };
		Steps = {
			{ Id = `Unwind`; Tool = `Key`; Target = `SideKey`; Count = 8 };
			{ Id = `Unscrew`; Tool = `Driver`; Target = `WingPlate`; Count = 4 };
			{ Id = `Trace`; Tool = `Scalpel`; Target = `Seam` };
			{ Id = `Pry`; Tool = `Driver`; Target = `Plate` };
			{ Id = `Lift`; Tool = `Tweezers`; Target = `Organ` };
		};
		Organs = {
			{ Id = `HeartPump`; Name = `Heart-pump`; Slot = `Heart` };
			{ Id = `Lungs`; Name = `Bellows lungs`; Slot = `Lungs` };
			{ Id = `VoiceBox`; Name = `Voice-box`; Slot = `Voice` };
			{ Id = `WingSpring`; Name = `Wing spring`; Slot = `Wing` };
			{ Id = `FlagCog`; Name = `Loose cog`; Slot = `Flag`; Flag = true };
		};
	};
	Wyvern = {
		Id = `Wyvern`; Name = `Clockwork Wyvern`; Latin = `Draco Horologicus`; Level = 5; TimeLimit = 180; Par = 100;
		FlagFrom = 4; Seam = { Rx = 1; Ry = 1.8 };
		Steps = {
			{ Id = `Unwind`; Tool = `Key`; Target = `SideKey`; Count = 12 };
			{ Id = `Inspect`; Tool = `Loupe`; Target = `HiddenSeam` };
			{ Id = `Trace`; Tool = `Scalpel`; Target = `Seam` };
			{ Id = `Pry`; Tool = `Driver`; Target = `Plate` };
			{ Id = `Lift`; Tool = `Tweezers`; Target = `Organ` };
		};
		Organs = {
			{ Id = `FireGland`; Name = `Fire-gland`; Slot = `Fire`; First = true };
			{ Id = `HeartA`; Name = `Fore heart`; Slot = `HeartA` };
			{ Id = `HeartB`; Name = `Aft heart`; Slot = `HeartB` };
			{ Id = `Lungs`; Name = `Bellows lungs`; Slot = `Lungs` };
			{ Id = `GearGut`; Name = `Gear-gut`; Slot = `Gut` };
			{ Id = `FlagCog`; Name = `Loose cog`; Slot = `Flag`; Flag = true };
		};
	};
}

function Anatomy.SpeciesFor(Level: number, Override: string?)
	if Override and Anatomy.Species[Override] then return Anatomy.Species[Override] end
	local Best = Anatomy.Species.Frog
	for _, S in Anatomy.Species do
		if S.Level <= Level and S.Level > Best.Level then Best = S end
	end
	return Best
end

return Anatomy
```

The Flag organ ("Loose cog") only appears from level 4 (`FlagFrom`). At lower levels the engine leaves it out of the specimen.

- [ ] **Step 3: Run the check (expect PASS), install as a new ModuleScript, commit**

```bash
git add tools/electives && git commit -m "Anatomy: species, steps, organs, scoring constants"
```

---

### Task 6: The bench game module (server judging)

**Files:**
- Create: `tools/electives/live/ServerStorage.Activities.AnatomyBench.luau`
- Test: `tools/electives/checks/anatomy_bench_pure.lua`

**Interfaces:**
- Consumes: `Config.Anatomy` (Task 5) and the Activities game-module contract. The session table `S` arrives with `S.Sub` (a substitute entry or nil), and `S.Sub.Twist` / `S.Sub.Sub.Name` are set by Substitutes.
- Produces:
  - `Bench.TimeLimit(Level) -> number`.
  - `Bench.Start(S, Level, StartAt) -> { Species, Name, Latin, Tools, Steps, Organs (ids, names; slot names hidden under Moth's loose twist), TimeLimit, Hand = nil, Twist }`.
  - `Bench.Handle(S, Action, Data, Now) -> (Reply?, Finished)`.
  - `Bench.Tick(S, Now) -> (false, nil)`.
  - `Bench.Score(S) -> (number 0..100, 100)`.
  - `Bench.Breakdown(S) -> { Accuracy, Process, Time }` (each 0..1).
- **Actions:**
  - `Pick { Tool }`
  - `Put { Spot = "Roll" | "Desk" }`
  - `Use { Target, Organ?, Points? }`: Points is a list of `{x, y}` in plate space, for Trace.
  - `Place { Organ, Slot }`
- **Reply fields** (only the relevant ones are set): `{ Ok, Hand, Step, Progress, Slip, Recoil, Holding, Placed, Reveal, Done }`.

- [ ] **Step 1: Write the failing pure check** `tools/electives/checks/anatomy_bench_pure.lua`

```lua
-- anatomy_bench_pure (Task 6): a clean frog run, slips, wrong tool, flag, trace judging, the Wyvern's first-organ rule, the twists.
local function load(name) local Fn = loadstring(__SRC[name]) return Fn() end
local Cfg = load("ReplicatedStorage.Config.Anatomy.luau")
getfenv().__AnatomyConfig = Cfg -- the module takes its config from here when run outside the place
local B = load("ServerStorage.Activities.AnatomyBench.luau")
local Fails = {}
local function Eq(G, W, What) if G ~= W then table.insert(Fails, What .. ": got " .. tostring(G) .. " want " .. tostring(W)) end end
local function Ring(Rx, Ry, N, Noise) local P = {} for I = 0, N do local a = I / N * 2 * math.pi * 0.97 table.insert(P, { math.cos(a) * Rx * (1 + (Noise or 0)), math.sin(a) * Ry * (1 + (Noise or 0)) }) end return P end
local function Run(S, Steps)
	local t = 0
	for _, A in Steps do t += 0.3 local R, F = B.Handle(S, A[1], A[2], S.StartAt + t) if F then return R, true, t end end
	return nil, false, t
end
local function Frog(S)
	local Steps = { { "Pick", { Tool = "Key" } } }
	for _ = 1, 8 do table.insert(Steps, { "Use", { Target = "SideKey" } }) end
	table.insert(Steps, { "Pick", { Tool = "Scalpel" } })
	table.insert(Steps, { "Use", { Target = "Seam", Points = Ring(1, 1.3, 40) } })
	table.insert(Steps, { "Pick", { Tool = "Driver" } })
	table.insert(Steps, { "Use", { Target = "Plate" } })
	table.insert(Steps, { "Pick", { Tool = "Tweezers" } })
	for _, O in { { "HeartPump", "Heart" }, { "Lungs", "Lungs" }, { "GearGut", "Gut" } } do
		table.insert(Steps, { "Use", { Target = "Organ", Organ = O[1] } })
		table.insert(Steps, { "Place", { Organ = O[1], Slot = O[2] } })
	end
	return Steps
end
-- 1) a clean level-1 frog finishes with an A or better
local S = {} B.Start(S, 1, 0)
Eq(S.Species.Id, "Frog", "species")
local _, Done = Run(S, Frog(S))
Eq(Done, true, "clean run finishes")
local Score = B.Score(S)
if Score < 90 then table.insert(Fails, "clean run scored " .. Score) end
-- 2) wrong tool: using the Scalpel on the key costs process, not progress
S = {} B.Start(S, 1, 0)
local R = B.Handle(S, "Pick", { Tool = "Scalpel" }, 1)
R = B.Handle(S, "Use", { Target = "SideKey" }, 1.5)
Eq(R.Ok, false, "wrong tool refused") Eq(S.WrongTool, 1, "wrong tool counted") Eq(S.StepIndex, 1, "still on Unwind")
-- 3) a slip (lifting an organ before the plate is open) starts a recoil that swallows input
S = {} B.Start(S, 1, 0)
B.Handle(S, "Pick", { Tool = "Tweezers" }, 1)
R = B.Handle(S, "Use", { Target = "Organ", Organ = "HeartPump" }, 1.2)
Eq(R.Slip, true, "early lift slips") Eq(R.Recoil, true, "recoil flagged")
Eq(B.Handle(S, "Pick", { Tool = "Key" }, 1.5), nil, "input ignored during recoil")
Eq(B.Handle(S, "Pick", { Tool = "Key" }, 2.1).Hand, "Key", "input back after recoil")
-- 4) a sloppy trace scores lower accuracy than a clean one, and too little sweep is refused
local function TraceOnly(Points)
	local T = {} B.Start(T, 1, 0)
	B.Handle(T, "Pick", { Tool = "Key" }, 1) for i = 1, 8 do B.Handle(T, "Use", { Target = "SideKey" }, 1 + i * 0.2) end
	B.Handle(T, "Pick", { Tool = "Scalpel" }, 3)
	return T, B.Handle(T, "Use", { Target = "Seam", Points = Points }, 4)
end
local Clean = TraceOnly(Ring(1, 1.3, 40)).TraceAccuracy
local Messy = TraceOnly(Ring(1, 1.3, 40, 0.12)).TraceAccuracy
if not (Clean > 0.95 and Messy < Clean) then table.insert(Fails, ("trace accuracy clean %.2f messy %.2f"):format(Clean, Messy)) end
local Half = {} for I = 0, 20 do local a = I / 20 * math.pi table.insert(Half, { math.cos(a), math.sin(a) * 1.3 }) end
local _, HR = TraceOnly(Half) Eq(HR.Ok, false, "half a seam is not a trace")
-- 5) the Flag organ appears from level 4 (a Raven) and lifting it is a slip; below level 4 there is none
S = {} B.Start(S, 4, 0)
local HasFlag = false for _, O in S.Organs do if O.Flag then HasFlag = true end end
Eq(S.Species.Id, "Raven", "level 4 is a raven") Eq(HasFlag, true, "flag from level 4")
S.StepIndex = #S.Species.Steps S.Hand = "Tweezers"
Eq(B.Handle(S, "Use", { Target = "Organ", Organ = "FlagCog" }, 5).Slip, true, "lifting the flag slips")
S = {} B.Start(S, 2, 0) local NoFlag = true for _, O in S.Organs do if O.Flag then NoFlag = false end end Eq(NoFlag, true, "no flag below level 4")
-- 6) the Wyvern: lifting anything before the Fire-gland recoils
S = { Sub = { Twist = "Specimen"; Sub = { Name = "Mx. Ashgrove Hollow" } } } B.Start(S, 1, 0)
Eq(S.Species.Id, "Wyvern", "Hollow's crate brings the Wyvern at level 1")
S.StepIndex = #S.Species.Steps S.Hand = "Tweezers" -- jump to Lift for the rule test
R = B.Handle(S, "Use", { Target = "Organ", Organ = "HeartA" }, 5)
Eq(R.Slip, true, "heart before fire-gland slips")
R = B.Handle(S, "Use", { Target = "Organ", Organ = "FireGland" }, 6) Eq(R.Holding, "FireGland", "fire-gland first is fine")
-- 7) Crane's Inspection doubles the slip cost
local A1 = {} B.Start(A1, 1, 0) A1.Slips = 2 A1.TraceAccuracy = 1 A1.PlacedCount = A1.Need
local A2 = { Sub = { Twist = "Specimen"; Sub = { Name = "Mr. Thaddeus Crane" } } } B.Start(A2, 1, 0) A2.Slips = 2 A2.TraceAccuracy = 1 A2.PlacedCount = A2.Need
if not (B.Breakdown(A2).Accuracy < B.Breakdown(A1).Accuracy) then table.insert(Fails, "inspection should cost more") end
-- 8) Moth's loose specimen hides the slots until the Loupe is used on the card
S = { Sub = { Twist = "Specimen"; Sub = { Name = "Miss Delphine Moth" } } }
local Info = B.Start(S, 1, 0)
Eq(Info.Organs[1].Slot, nil, "slots hidden")
B.Handle(S, "Pick", { Tool = "Loupe" }, 1)
R = B.Handle(S, "Use", { Target = "Card" }, 1.3) Eq(R.Reveal ~= nil, true, "loupe reveals")
if #Fails > 0 then return "FAIL\n" .. table.concat(Fails, "\n") end
return "PASS anatomy_bench_pure"
```

Run it. Expected: FAIL (the module is missing).

- [ ] **Step 2: Write the module**

```lua
--[[
	Anatomy: "The Bench" (server logic). The client sends intents; this judges them.
	Steps run in order (Config.Anatomy.Species[*].Steps); the last step, Lift, repeats until every non-Flag organ
	is placed on its slot. A slip (wrong target, lifting out of turn, a flag organ, a wrong slot) costs accuracy and
	starts a Recoil during which input is ignored. Using the wrong tool costs process, not accuracy.
	Substitutes' Specimen twist: Hollow brings the Wyvern (crate), Crane doubles slip cost (Inspection),
	Moth shuffles the organs and hides the slots until the Loupe is used on the card. Lazzaro's bet is his rule.
]]
local Cfg = getfenv().__AnatomyConfig or require(game:GetService(`ReplicatedStorage`).Config.Anatomy)

local Bench = {}
Bench.Bench = true

local function Twist(S): string?
	local Sub = S.Sub
	if not (Sub and Sub.Twist == `Specimen` and Sub.Sub) then return nil end
	local N = Sub.Sub.Name or ``
	if N:find(`Hollow`) then return `Crate` end
	if N:find(`Crane`) then return `Inspection` end
	if N:find(`Moth`) then return `Loose` end
	if N:find(`Lazzaro`) then return `Bet` end
	return nil
end

function Bench.TimeLimit(Level: number): number
	return Cfg.SpeciesFor(Level).TimeLimit
end

function Bench.Start(S, Level: number, StartAt: number)
	S.Twist = Twist(S)
	local Species = Cfg.SpeciesFor(Level, if S.Twist == `Crate` then `Wyvern` else nil)
	S.Species = Species
	S.Level = Level
	S.StartAt = StartAt
	S.StepIndex = 1
	S.Count = 0
	S.LastUse = -math.huge
	S.Hand = nil
	S.Holding = nil
	S.Slips = 0
	S.WrongTool = 0
	S.TraceAccuracy = 0
	S.Placed = {}
	S.PlacedCount = 0
	S.RecoilUntil = -math.huge
	S.FinishedAt = nil
	S.Revealed = S.Twist ~= `Loose`
	S.Organs = {}
	for _, O in Species.Organs do
		if not O.Flag or Level >= (Species.FlagFrom or math.huge) then table.insert(S.Organs, O) end
	end
	S.Need = 0
	for _, O in S.Organs do if not O.Flag then S.Need += 1 end end
	if S.Twist == `Loose` then
		local Rng = Random.new()
		for I = #S.Organs, 2, -1 do local J = Rng:NextInteger(1, I) S.Organs[I], S.Organs[J] = S.Organs[J], S.Organs[I] end
	end
	local Organs = {}
	for _, O in S.Organs do table.insert(Organs, { Id = O.Id; Name = O.Name; Slot = if S.Revealed then O.Slot else nil }) end
	local Steps = {}
	for _, St in Species.Steps do table.insert(Steps, { Id = St.Id; Tool = St.Tool; Target = St.Target; Count = St.Count }) end
	return { Species = Species.Id; Name = Species.Name; Latin = Species.Latin; Tools = Cfg.Tools; Steps = Steps;
		Organs = Organs; TimeLimit = Species.TimeLimit; Twist = S.Twist; Level = Level }
end

local function Organ(S, Id)
	for _, O in S.Organs do if O.Id == Id then return O end end
	return nil
end

local function Slip(S, Now, Why)
	S.Slips += 1
	S.RecoilUntil = Now + Cfg.RecoilSeconds
	S.Holding = nil
	return { Ok = false; Slip = true; Recoil = true; Why = Why; Hand = S.Hand; Step = S.StepIndex }
end

local function Advance(S)
	S.StepIndex += 1
	S.Count = 0
end

local function JudgeTrace(S, Points): (boolean, number)
	if typeof(Points) ~= `table` or #Points < 8 or #Points > 400 then return false, 0 end
	local Rx, Ry = S.Species.Seam.Rx, S.Species.Seam.Ry
	local Good, Angles = 0, {}
	for _, P in Points do
		if typeof(P) ~= `table` or typeof(P[1]) ~= `number` or typeof(P[2]) ~= `number` then return false, 0 end
		local x, y = P[1] / Rx, P[2] / Ry
		local r = math.sqrt(x * x + y * y)
		if math.abs(r - 1) <= Cfg.TraceTolerance then Good += 1 end
		table.insert(Angles, math.atan2(y, x))
	end
	table.sort(Angles)
	local Gap = (Angles[1] + 2 * math.pi) - Angles[#Angles]
	for I = 2, #Angles do Gap = math.max(Gap, Angles[I] - Angles[I - 1]) end
	local Sweep = (2 * math.pi - Gap) / (2 * math.pi)
	return Sweep >= Cfg.TraceCoverage, Good / #Points
end

function Bench.Handle(S, Action: string, Data: any, Now: number)
	if S.FinishedAt or Now < S.StartAt - 0.5 or Now < S.RecoilUntil then return nil, false end
	if typeof(Data) ~= `table` then Data = {} end
	local Step = S.Species.Steps[S.StepIndex]

	if Action == `Pick` then
		local Valid = table.find(Cfg.Tools, Data.Tool)
		if not Valid or S.Holding then return nil, false end
		S.Hand = Data.Tool
		return { Ok = true; Hand = S.Hand; Step = S.StepIndex }, false
	elseif Action == `Put` then
		if S.Holding then return nil, false end -- set the organ down on the card first
		S.Hand = nil
		return { Ok = true; Hand = nil; Spot = if Data.Spot == `Desk` then `Desk` else `Roll` }, false
	elseif Action == `Use` then
		if not S.Hand then return nil, false end
		-- the Loupe on the card reveals hidden slots at any time (Moth's loose specimen)
		if S.Hand == `Loupe` and Data.Target == `Card` then
			if S.Revealed then return { Ok = true }, false end
			S.Revealed = true
			local Reveal = {}
			for _, O in S.Organs do Reveal[O.Id] = O.Slot end
			return { Ok = true; Reveal = Reveal }, false
		end
		if Data.Target ~= Step.Target then
			if Step.Id == `Lift` or Data.Target == `Organ` then return Slip(S, Now, `NotYet`), false end
			return { Ok = false; Why = `WrongTarget` }, false
		end
		if S.Hand ~= Step.Tool then
			S.WrongTool += 1
			return { Ok = false; Why = `WrongTool`; Step = S.StepIndex }, false
		end
		if Step.Id == `Trace` then
			local Ok, Acc = JudgeTrace(S, Data.Points)
			if not Ok then return { Ok = false; Why = `Incomplete` }, false end
			S.TraceAccuracy = Acc
			Advance(S)
			return { Ok = true; Step = S.StepIndex; TraceAccuracy = Acc }, false
		elseif Step.Id == `Lift` then
			local O = Organ(S, Data.Organ)
			if not O or S.Placed[O.Id] or S.Holding then return nil, false end
			if O.Flag then return Slip(S, Now, `Flag`), false end
			if not O.First then
				for _, F in S.Organs do
					if F.First and not S.Placed[F.Id] then return Slip(S, Now, `FirstOrgan`), false end
				end
			end
			S.Holding = O.Id
			return { Ok = true; Holding = O.Id }, false
		elseif Step.Count then
			if Now - S.LastUse < Cfg.UseInterval then return nil, false end
			S.LastUse = Now
			S.Count += 1
			if S.Count >= Step.Count then Advance(S) end
			return { Ok = true; Step = S.StepIndex; Progress = S.Count }, false
		else
			Advance(S)
			return { Ok = true; Step = S.StepIndex }, false
		end
	elseif Action == `Place` then
		local O = S.Holding and Organ(S, S.Holding)
		if not O or Data.Organ ~= O.Id then return nil, false end
		if Data.Slot ~= O.Slot then return Slip(S, Now, `WrongSlot`), false end
		S.Placed[O.Id] = true
		S.PlacedCount += 1
		S.Holding = nil
		local Done = S.PlacedCount >= S.Need
		if Done then S.FinishedAt = Now end
		return { Ok = true; Placed = O.Id; Done = Done }, Done
	end
	return nil, false
end

function Bench.Tick(S, Now: number)
	return false, nil
end

function Bench.Breakdown(S)
	local Steps = #S.Species.Steps
	local StepDone = if S.FinishedAt then 1 else math.clamp((S.StepIndex - 1) / Steps, 0, 1)
	local Organs = if S.Need > 0 then S.PlacedCount / S.Need else 1
	local Cost = Cfg.SlipCost * (if S.Twist == `Inspection` then 2 else 1)
	local Accuracy = math.clamp((S.TraceAccuracy * 0.4 + Organs * 0.6) - S.Slips * Cost, 0, 1)
	local Process = math.clamp(StepDone - S.WrongTool * Cfg.WrongToolCost, 0, 1)
	local Time = 0
	if S.FinishedAt then
		local Used = S.FinishedAt - S.StartAt
		local Par, Limit = S.Species.Par, S.Species.TimeLimit
		Time = if Used <= Par then 1 else math.clamp(1 - (Used - Par) / (Limit - Par), 0, 1)
	end
	return { Accuracy = Accuracy; Process = Process; Time = Time }
end

function Bench.Score(S): (number, number)
	local B = Bench.Breakdown(S)
	local W = Cfg.Weights
	return math.floor((B.Accuracy * W.Accuracy + B.Process * W.Process + B.Time * W.Time) * 100 + 0.5), 100
end

return Bench
```

Note: Lift never advances `StepIndex`, so a finished run counts as every step done (`StepDone = 1` once `FinishedAt` is set).

- [ ] **Step 3: Run the check until it passes**

Run: `python -X utf8 -I tools/electives/harness/pure.py tools/electives/checks/anatomy_bench_pure.lua`
Expected: `PASS anatomy_bench_pure`

- [ ] **Step 4: Install into `ServerStorage.Activities` (new ModuleScript `AnatomyBench`) and commit**

```bash
git add tools/electives && git commit -m "Anatomy: bench game module with server judging, twists, 60/25/15 scoring"
```

---

### Task 7: Activities and Substitutes hook Anatomy in

**Files:**
- Modify: `tools/electives/live/ReplicatedStorage.Config.Activities.luau`, adding:

```lua
Anatomy = { Type = `AnatomyBench`; Title = `The Bench`; Bench = true; Tagline = `Pick a tool from the roll: 1-5 or tap. Right-click or B puts it down.` };
```

- Modify: `Config.Substitutes` (`Subjects` gets `Anatomy`; add `Specimen` to each cast member's `Twists`, once per member) and `Services.School.Substitutes`.
- Modify: `Services.School.Activities` (the lesson result carries `Breakdown` and `Species`; the Journal; the rewards hook).
- Test: `tools/electives/checks/anatomy_play.lua` (Server, Play)

**Interfaces:**
- Consumes: `Bench.Breakdown`, `S.Species`, `Electives.PickFor`.
- Produces:
  - `Result.Breakdown = {Accuracy, Process, Time}` and `Result.Species = Id` in the `Result` message.
  - `Profile.Classes.Anatomy.Journal = { [SpeciesId] = BestGrade }`.
  - `Activities.Finished` already fires with the Result. The rewards in Task 12 listen to it.

- [ ] **Step 1: Write the Play check**

```lua
-- anatomy_play (Task 7): start Anatomy through the test hooks on a Tuesday period 3, run a clean frog, read the result.
local SSS = game:GetService("ServerScriptService")
local Act = require(SSS.Services.School.Activities)
local Clock = require(SSS.Services.School.SchoolClock)
local El = require(SSS.Services.School.Electives)
local P = game:GetService("Players"):GetPlayers()[1]
El.ForceForTests(P, "Anatomy")
Clock.SetTime("10:05", 6) -- day 6 = Tuesday
P:SetAttribute("ClassInRoom", true)
Act.StartForTests(P, "R103")
local S = Act.GetSessionForTests(P)
assert(S and S.Subject == "Anatomy", "FAIL lesson did not start as Anatomy: " .. tostring(S and S.Subject))
task.wait(3.5) -- intro
local function A(a, d) assert(Act.ActionForTests(P, a, d), "FAIL action " .. a) task.wait(0.2) end
A("Pick", { Tool = "Key" }) for _ = 1, 8 do A("Use", { Target = "SideKey" }) end
local Pts = {} for I = 0, 40 do local t = I / 40 * 2 * math.pi * 0.97 table.insert(Pts, { math.cos(t), math.sin(t) * 1.3 }) end
A("Pick", { Tool = "Scalpel" }) A("Use", { Target = "Seam", Points = Pts })
A("Pick", { Tool = "Driver" }) A("Use", { Target = "Plate" })
A("Pick", { Tool = "Tweezers" })
for _, O in { { "HeartPump", "Heart" }, { "Lungs", "Lungs" }, { "GearGut", "Gut" } } do A("Use", { Target = "Organ", Organ = O[1] }) A("Place", { Organ = O[1], Slot = O[2] }) end
task.wait(0.5)
assert(not Act.IsInActivity(P), "FAIL still in activity")
local J = require(SSS.Services.Player.Data).GetProfile(P).Classes.Anatomy
assert(J and J.Journal and J.Journal.Frog, "FAIL no journal entry")
return "PASS anatomy_play grade " .. J.Journal.Frog
```

- [ ] **Step 2: Change Activities `Local.Finish`**

Read lines 251–330 of `pre/ServerScriptService.Services.School.Activities.luau` first. After `Percent` is computed:

```lua
	if S.Game.Breakdown then
		local Ok, B = pcall(S.Game.Breakdown, S)
		if Ok then Result.Breakdown = B end
	end
	if S.Species then
		Result.Species = S.Species.Id
		local ClassData = Local.GetClassData(S.Player, S.Subject)
		if ClassData then
			ClassData.Journal = ClassData.Journal or {}
			local Old = ClassData.Journal[S.Species.Id]
			if Local.GradeRank(Grade) > Local.GradeRank(Old) then ClassData.Journal[S.Species.Id] = Grade end
		end
	end
```

(`S.Player` is the session's player field. Check the real name in `Local.Begin`.)

- [ ] **Step 3: Substitutes**

- **The Specimen twist.** In `Local.Entry`, when the twist rolled is `Specimen` and the subject is not a Bench subject, re-roll from the member's twists without `Specimen`. When the subject is a Bench subject and the twist is `Game`, `Swap` or `Errand`, leave it as it is.
- **Elective days only.** In `Plan`, an elective subject (one where `Electives.Get(Subject)` is set) can only be picked for weekday 1 or 3. Filter `Config.Subjects` by weekday before the random pick.
- **The rules.** They carry over unchanged through `Rule`.

- [ ] **Step 4: Play round**

1. Message the Skate session.
2. Run the protocol with `run_live.py Server tools/electives/checks/anatomy_play.lua`. Expected: `PASS anatomy_play grade A` (or A+).
3. Then run `SubForce("Anatomy", "Moth", "Specimen")` through the TestBridge hook and confirm that the `Start` payload's organs have no `Slot`.
4. Restore, cine, stop, and message the Skate session.

- [ ] **Step 5: Commit**

```bash
git add tools/electives && git commit -m "Anatomy: Activities subject, journal, Specimen twist in Substitutes"
```

---

### Task 8: Bench models (Blender → rigid rigs)

**Files:**
- Create: `tools/electives/render/export_bench.py` (Blender headless: builds each prop from `frog_lib` / `tools_lib`, runs `clipcheck`, exports FBX)
- Create: `art/props/anim/AnatFrog_rigid.json`, `AnatRaven_rigid.json`, `AnatWyvern_rigid.json`, `AnatTool<Name>_rigid.json` (×5), `AnatBenchSet_rigid.json`
- Create: `tools/electives/render/raven_lib.py`, `tools/electives/render/wyvern_lib.py`
- Output: `art/props/fbx/Anat*.fbx` and textures in `art/props/textures/Anat*`

**Interfaces:**
- Produces Studio models under `ReplicatedStorage.Anatomy.Models`:
  - `Frog`, `Raven`, `Wyvern`, each with these named parts:
    - `Body` (hollow; the lacquer interior is a second material);
    - `Plate` on a `PlateHinge` Motor6D;
    - one part per organ, named by organ Id (`HeartPump`, `Lungs`, …), each on its own Motor6D from `Body`;
    - `SideKey`;
    - a `Seam` attachment ring, 24 attachments named `Seam01`..`Seam24`, in plate space.
  - The five tools, each a rigid model with a `Grip` attachment (where the hand holds) and a `Tip` attachment (where it acts).
  - `BenchSet`: the tray, the wax and the roll, with five `Slot1`..`Slot5` attachments. Each attachment's CFrame is the rest pose of that tool.

- [ ] **Step 1: Read `docs/Pipeline-Lessons.md` end to end.** Note the import scale, the rigid table format, group asset ids and the slot 2 rules.

- [ ] **Step 2: Write `export_bench.py`**

1. Build each prop alone at the origin, with frog_lib/tools_lib at SCALE 1.
2. Name every mesh object after the part it becomes.
3. Run `clipcheck.run` (it must report 0).
4. Write `<Prop>_rigid.json` from the object hierarchy (parts, parents, pivot points), in the format `rigid_rig.py` reads. Copy the shape of an existing `art/props/anim/*_rigid.json`.
5. Export FBX with "Apply transform" on.
6. Bake the PBR maps per part to 1024² (albedo, normal, roughness, metal) with `mats_lib`'s materials, using a Cycles bake.

Exit non-zero if the clip check fails.

Run: `"E:/Blender/blender.exe" -b --factory-startup -P tools/electives/render/export_bench.py -- art/props/source art/props/fbx Frog`
Expected: `CLIPCHECK 0`, `EXPORT art/props/fbx/AnatFrog.fbx`, and the four textures.

- [ ] **Step 3: Model the Raven and the Wyvern**

- **`raven_lib.py` and `wyvern_lib.py`.** Follow `frog_lib.build_frog`:
  - a hollow shell with a 4.5 mm wall and a lacquer interior;
  - a seated deck;
  - organs per `Config.Anatomy`;
  - a hinged plate;
  - `carve()` for anything that reaches in.
- **Raven:** a teardrop body, folded wings held by four screwed wing plates (the Unscrew step), a voice-box (a small brass reed organ) and a wing spring.
- **Wyvern:**
  - a long body with two hearts, a fire-gland (a glass bulb with an ember emission, mounted forward) and a hidden seam on the plate's edge (the Inspect step);
  - folded wings and a coiled tail resting on the wax.
- **Before export.** Run the clip check in `bench_scene.py` with each species swapped in.

Render one close-up per species to `tools/electives/render/out/<Species>_close.jpg` for the REPORT.

- [ ] **Step 4: Import into Studio** (Edit only; no Play needed)

For each FBX:
1. Import with "Import as rig" off and the scale corrected per Pipeline-Lessons.
2. Run `python tools/phase6-2350/stage/rigid_rig.py <Prop>_rigid.json`.
3. Apply textures with `stage/textures.lua`.
4. Move the model to `ReplicatedStorage.Anatomy.Models`.

Record each texture upload in `PUBLISH_LIST.md`. Group-owned ids are required, as in Pipeline-Lessons.

- [ ] **Step 5: Edit check** `tools/electives/checks/anatomy_models_edit.lua`

For each species, assert that:
- every organ Id in `Config.Anatomy` has a part;
- `Plate`, `PlateHinge`, `SideKey` and `Seam01..24` exist;
- every tool has `Grip` and `Tip`;
- `BenchSet` has `Slot1..5`;
- no part in the set is anchored-overlapping another (`GetPartsInPart` with `CollisionFidelity` off, skipping the allowlisted pairs from `clipcheck.ALLOW`).

Expected: `PASS anatomy_models_edit`.

- [ ] **Step 6: Commit** (the scripts, JSON, FBX and textures; not the place)

```bash
git add tools/electives art/props && git commit -m "Anatomy: frog, raven, wyvern, tools and bench set as rigid rigs (clip-checked)"
```

---

### Task 9: Clips (seated R6 and props)

**Files:**
- Create: `tools/electives/anim/make_clips.lua` (builds KeyframeSequences in `ReplicatedStorage.AnatomyClips`)
- Create: `tools/electives/anim/clips.md` (the shot list, with timings per clip)

**Interfaces:**
- Produces `ReplicatedStorage.AnatomyClips`:
  - nine R6 KeyframeSequences: `BenchIdle`, `Unwind`, `Trace`, `Pry`, `Lift`, `Recoil`, `Loupe`, `Write`, `Done`. Each has a `Contact` keyframe marker where the action lands. Put-down is `Lift` played in reverse.
  - prop sequences, named `<Species>_PlateOpen` and `<Species>_<Organ>_Lift`.
  - a `Clips` ModuleScript mapping `Step.Id` to the R6 clip name.

- [ ] **Step 1: Load the skills.** Load `roblox-cinematic-animation` and then `r6-animation-cinematics`, and follow both (the house style wins where they differ). These clips are seated: the hips are fixed on the bench stool and only the torso and arms read.
  - Reuse the existing seated idle if one fits. Search `ReplicatedStorage` for "Sit" clips first.
  - Kneeling isn't used here.

- [ ] **Step 2: Write the shot list in `clips.md`.** For each clip, give its length, its Contact time, and the key poses (Right Arm and Left Arm C0 angles). Then write `make_clips.lua`, which builds the sequences from that table and registers them with `KeyframeSequenceProvider:RegisterKeyframeSequence`.

- [ ] **Step 3: Edit check** `tools/electives/checks/anatomy_clips_edit.lua`

Assert that all nine clips exist, each has a `Contact` marker, the prop sequences exist for every species/organ, and `RegisterKeyframeSequence` returns an id for each.
Expected: `PASS anatomy_clips_edit`.

- [ ] **Step 4: Commit**

```bash
git add tools/electives && git commit -m "Anatomy: nine seated R6 clips and prop clips (unpublished, registered in Studio)"
```

---

### Task 10: Full-screen Bench mode in the lesson UI

**Files:**
- Modify: `StarterPlayer.StarterPlayerScripts.Controllers.Gui.Activities` (fetched in `pre/`)
- Test: `tools/electives/checks/bench_mode_client.lua` (Client, Play)

**Interfaces:**
- Consumes: `Message.Def.Bench`. Add `Bench = Def.Bench` to the `Start` message in Activities `Local.Begin`, next to `Title`.
- Produces: for Bench games the renderer gets `Content` = a full-screen Frame (the ScreenGui's whole safe area). The chalkboard frame, the board title and the lesson timer bar are hidden; the renderer draws its own (AnatPlate holds the timer). `Api.SetTimerLabel(TextLabel)` hands the lesson countdown to the renderer's label. Intro and grade sheet are unchanged.

- [ ] **Step 1: Read `Local.Open` (lines 522–690).** Find where `Screen.Content` is built and the timer label is updated.

- [ ] **Step 2: Add the branch.** In `Local.Open`, when `Message.Bench` is true:
  - make a `Frame` named `BenchContent` (Size 1,1; transparent) parented to the activities ScreenGui;
  - set the board's `Visible = false` after the intro;
  - pass `BenchContent` as `Content`;
  - set `Api.SetTimerLabel = function(L) Local.TimerLabel = L end`, and have the timer update write to `Local.TimerLabel` when it's set.
  - "Leave lesson" stays as a small button bottom-left (Kit Button).

- [ ] **Step 3: Write the Client check.** It starts a lesson through the TestBridge, waits for the intro, asserts that `BenchContent` exists with an absolute size equal to the GUI inset area and the board is hidden, then quits.
  Expected: `PASS bench_mode_client`.

- [ ] **Step 4: Commit**

```bash
git add tools/electives && git commit -m "Activities UI: full-screen content for Bench games"
```

---

### Task 11: The bench renderer

**Files:**
- Create: `tools/electives/live/StarterPlayer.StarterPlayerScripts.Controllers.Gui.Activities.AnatomyBench.luau`
- Create: `tools/electives/live/ReplicatedStorage.UI.Theme.Anatomy.luau` (the image ids from `PUBLISH_LIST.md`: Plate, Procedure, Specimen, Seal, Hold, Tag)
- Test: `tools/electives/checks/anatomy_client.lua` (Client, Play) plus screenshots

**Interfaces:**
- Consumes:
  - the `Start` payload (Task 6);
  - the `Update` replies;
  - `ReplicatedStorage.Anatomy.Models`;
  - `ReplicatedStorage.AnatomyClips` and its `Clips` map;
  - `Api.Send(Action, Data)`: check the name the existing renderers use to send actions, in `Gui.Activities.MemoryMatch`.
- Produces: the `Renderer.new(Content, Payload, Api)` object with `:Update(Payload)`, `:Destroy()` and `:PadBack()`.

- [ ] **Step 1: Read an existing renderer.** Fetch and read `Controllers.Gui.Activities.MemoryMatch` for the exact `Api` (send, pad hints, input kind), and copy its structure.

- [ ] **Step 2: Build the viewport**

1. Create a `ViewportFrame` filling `Content`, with a `WorldModel` inside.
2. Clone `BenchSet` and the species model into it.
3. Clone an R6 dummy of the player (`Players:CreateHumanoidModelFromUserId` or the existing character archivable clone) with an `Animator`, seated at the bench's front edge so the arms reach the tray.
4. Set up the camera as in the approved Bench board: a high three-quarter view from the player's side, FOV 33, looking at the tray.
5. Lighting: `ViewportFrame.Ambient` (40, 34, 30) and `LightColor` (255, 214, 168), with `LightDirection` matching the key spot in the concept render.

- [ ] **Step 3: Tools and input**

- **Rest poses.** Each tool rests at its `Slot<n>` CFrame.
- **Picking up** (a click/tap on a tool, raycast through `ViewportFrame` with `Camera:ViewportPointToRay` into the WorldModel, or keys 1–5 / D-pad + A): send `Pick { Tool }`. On `Reply.Hand`, play `Lift`, then weld the tool's `Grip` to the dummy's Right Arm grip.
- **Using a tool.** Clicking a target part sends `Use` with `Target = <part name>`: `SideKey`, `Plate`, an organ (`Target = "Organ", Organ = <name>`), or `Card` (the Specimen card UI).
- **Holding to turn.** The Key and the Driver send a `Use` each time the hold ring fills (0.25 s per turn), and the hold ring (AnatHold) shows progress.
- **The trace.** With the Scalpel, press on the seam and drag. Sample the pointer every 1/30 s, project it onto the plate plane, and convert to plate space (divide by the plate radius). On release, send `Use { Target = "Seam", Points }`. Draw the trail as a Beam between attachments on the plate.
- **Putting down.** Right-click or B sends `Put`. If the pointer is over the roll, `Spot = "Roll"` and the tool tweens to its slot. Otherwise `Spot = "Desk"`, and the tool rests where the pointer meets the desk plane: raycast down and offset by the tool's bounding-box half-height so it doesn't clip. Play `Lift` in reverse.
- **Organs.** After `Holding`, the organ follows the tweezers' `Tip`. Clicking an outline on the Specimen card sends `Place`. On `Placed`, the organ tweens into the card's 3D slot marker and the outline fills (gold glow).
- **Slips.** On `Slip`, play `Recoil`, apply a short camera shake (≤ 6 px, 150 ms) and flash the procedure line red. Input is swallowed until the recoil ends (the server ignores it anyway).
- **Showing progress.** On a step change, tick the procedure card's line (strike-through, as on the canvas board) and play that step's clip from `Clips`.
- **Twists.** On `Reveal`, fade the outlines in. A `Twist` from the payload shows a small tag on the plate ("Inspection", "Loose specimen", "Crate specimen", "Lazzaro's bet").

- [ ] **Step 4: The chrome.** The plate (title, species, room/level/teacher line, timer through `Api.SetTimerLabel`), the procedure card, the Specimen card, the IN HAND box and the five tool tags all follow the canvas Bench board: same positions in scale units and same fonts. The images come from `Theme.Anatomy`. Tags dim when their tool isn't on the roll, and glow when their tool is in hand.

- [ ] **Step 5: Client check and screenshots**

1. Message the Skate session.
2. Run the protocol. The Client check starts Anatomy and drives a clean frog by firing the same input handlers (call the renderer's `_TestClick(partName)` / `_TestKey(n)` / `_TestTrace(points)` hooks, which only exist when `RunService:IsStudio()`). It asserts the result message arrives with `Grade` A or A+.
3. Take screenshots: the bench at the start, mid-trace, an organ held, a tool put down on the desk, and the grade sheet, into `tools/electives/shots/`.
4. Do a deliberate wrong slot and check that the `Recoil` clip played (`Animator:GetPlayingAnimationTracks()` names).
5. Restore, cine, stop, and message the Skate session.

- [ ] **Step 6: Commit**

```bash
git add tools/electives && git commit -m "Anatomy: bench renderer with physical tools, trace, organs, recoil"
```

---

### Task 12: Rewards (Healer perk, Journal, title, monocle)

**Files:**
- Modify: the healing source and the downed/revive source, as found in Step 1.
- Modify: `Services.School.Activities` (title and monocle grant on mastery).
- Modify: the Journal page in `Controllers.Gui.Phone` or a new `Controllers.Gui.Journal`, depending on what Step 1 finds about where the class report card lives.
- Test: `tools/electives/checks/anatomy_rewards_play.lua`

**Interfaces:**
- Consumes: `Profile.Classes.Anatomy.Level` and `.Journal`.
- Produces:
  - `Anatomy.HealMult(Level) = 1 + 0.10 * (Level - 1)`;
  - `Anatomy.ReviveMult(Level) = 1 - 0.08 * (Level - 1)` (the time multiplier);
  - title `Anatomist` and accessory `BrassLoupeMonocle` granted once all three species have an A or better.

- [ ] **Step 1: Find the hooks.** In Edit, search all scripts for `Heal`, `Bandage`, `Medkit`, `Revive` and `Downed`. A Downed system exists (see `docs/VFX-Audit.md`, "Downed 356-377"). Then:
  - **If there is a player-to-player revive:** apply `ReviveMult` to its duration.
  - **If healing comes only from items:** apply `HealMult` to the amount the item heals.
  - **If either mechanic doesn't exist:** don't invent one. Write the gap in `REPORT.md` and send the parent session one question asking whether to build it.

- [ ] **Step 2: Add the two helpers to `Config.Anatomy`** and extend `anatomy_config_pure.lua`:

```lua
function Anatomy.HealMult(Level: number): number return 1 + 0.10 * (math.clamp(Level, 1, 5) - 1) end
function Anatomy.ReviveMult(Level: number): number return 1 - 0.08 * (math.clamp(Level, 1, 5) - 1) end
```

Assertions: `Eq(A.HealMult(1), 1)`, `Eq(A.HealMult(5), 1.4)` (with Near), `Near(A.ReviveMult(5), 0.68)`.

- [ ] **Step 3: Grant mastery.** In the Journal update (Task 7 Step 2), after writing a grade, check whether `Frog`, `Raven` and `Wyvern` all rank ≥ A. If they do and it hasn't been granted yet, grant the title and the accessory through the existing title/accessory services (search for how the Superlatives titles and shop accessories are granted, and use the same calls).

- [ ] **Step 4: The Journal page.** It has one page per species, showing the specimen's close-up render (uploaded image), its Latin name and the best grade stamped with AnatSeal. A species with no grade yet shows a pencil outline and "Not yet dissected".

- [ ] **Step 5: Play check, then commit**

The Play check, in order:
1. Force a level-5 Anatomy record.
2. Verify the healing and revive values the found hook reads.
3. Force A grades into the Journal.
4. Finish one more lesson.
5. Assert that the title and the accessory are granted once.

```bash
git add tools/electives && git commit -m "Anatomy: Healer perk, Specimen Journal, Anatomist title and monocle"
```

---

### Task 13: Full Play round, report and publish list

**Files:**
- Create: `tools/electives/REPORT.md`, `tools/electives/PUBLISH_LIST.md`
- Modify: `docs/Class-Activities.md` (adds an "Electives and Anatomy" section)

- [ ] **Step 1: The end-to-end round.** Message the Skate session. Run the protocol once, with every check in order:
  1. `electives_play`
  2. `anatomy_play`
  3. `anatomy_client`, which covers:
     - the frog end to end to an A;
     - a deliberate Recoil;
     - putting a tool down on the desk and on the roll;
  4. the Moth Specimen twist, with the outlines hidden and then revealed;
  5. `anatomy_rewards_play`.

  Then restore, run cine, stop, and message the Skate session. Paste every PASS line into the REPORT.

- [ ] **Step 2: Write `REPORT.md`.** Cover:
  - what was built;
  - the scripts changed, each with its `pre/` and `live/` path;
  - the checks and their output;
  - the screenshots;
  - the clip report (0 intersections);
  - the open questions (for example, any Healer-perk gap from Task 12);
  - a note that graphify wasn't run, if it is still missing.

- [ ] **Step 3: Write `PUBLISH_LIST.md`.** List every asset for the owner to publish: the FBX meshes, the textures, the nine R6 clips plus the prop clips, the six UI images and the journal renders. For each, give the local path, the asset type and where its id goes after publishing (`Theme.Anatomy`, `Clips`, `Models`).

- [ ] **Step 4: Update `docs/Class-Activities.md`.** Add the elective slots, enrolment, The Bench (Anatomy), the Specimen twist and the test hooks (`ForceForTests`, `_Test*`).

- [ ] **Step 5: Commit.** Don't push, don't merge, and don't save the place. Ask the owner.

```bash
git add tools/electives docs && git commit -m "Electives: Anatomy end-to-end Play round, report and publish list"
```
