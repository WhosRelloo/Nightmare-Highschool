# Line Matrix + Outfits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Combat Test students speak by clique, attitude and moment. They remark on what you wear by clique taste,
and clique leaders and the Vigil's Night Study won't deal with a Neutral player who isn't dressed the part.

**Architecture:**
- **The lines** live in `ReplicatedStorage.Config.CliqueTalk`: one module per clique plus Generic, keyed
  `[Moment][Sub?][Attitude | Any]`.
- **`StudentBrain.Talk`** works out the attitude (standing, membership, memory), picks a fillable line, and judges an
  outfit from the `NHWear` attribute that `UI.Appearance.ApplyTo` stamps on player characters.
- **The brain** speaks through one new helper, `sayMatrix`, that falls back to today's pools.
- **The dress code** is a single `Social.Cliques.Dressed`, checked by `Quests.CanStart`, `Social.Hangouts` and a
  hangout watcher in the brain.

**Tech Stack:**
- Roblox Luau, installed into NH Combat Test (placeId 98950102230473) with the Roblox Studio MCP tools
  (`execute_luau`, `multi_edit`).
- Python 3 for the install-snippet helper.
- git in `E:\Nightmare-Highschool`.

**Spec:** `docs/superpowers/specs/2026-11-12-line-matrix-outfits-design.md` (read it with this plan).

## Global Constraints

**Places**
- Work only in **NH Combat Test** (placeId 98950102230473). Run `list_roblox_studios` first, because the studio id
  changes whenever Studio reopens (it was `21d5d261-aa69-451a-8807-b043a74fc61b`).
- **Never touch production "Nightmare High [Wave - 1]" (11109987840).**
- The Map is not part of this build.

**Installing**
- Install and edit scripts **only in Edit mode**. Other sessions play-test this place. If `list_roblox_studios` shows
  Play, read through the `Server` datamodel if you must, but wait (or ask the owner) before installing.
- Never use the shared `NHInstallBuffer` or `_G.NHCompileBuf`. The install snippets in this plan carry their own
  source and checksum.
- **Checksum:** `h = (h * 31 + byte) % 1000000007` over the source with `\r\n` turned into `\n`.
- Before editing an existing Studio script, checksum it against the repo copy, or pull it fresh. Other sessions edit
  this place too.

**Writing the lines**
- No gore and no blood words (the owner's Roblox account has a moderation warning).
- No slurs and no innuendo.
- No Bully names, places or lines.
- A line is 60 characters or fewer.
- A pool holds 3 to 5 lines.

**Moments, sub-keys, attitudes and placeholders**

| Kind | Values |
|---|---|
| Moments | `Greet`, `Bump`, `Crowded`, `Shoved`, `FightSeen`, `Flee`, `Transformed`, `Night`, `FullMoon`, `Race`, `Hurt`, `Outfit`, `DressCode` |
| `Race` sub-keys | `Human`, `Priest`, `Vampire`, `Werewolf`, `Ghoul`, `Wraith` |
| `Outfit` sub-keys | `FullLook`, `RivalLook`, `Likes`, `Mocks` |
| Attitudes | `Hostile`, `Wary`, `Neutral`, `Friendly`, `Respected`, plus `Any` |
| Placeholders | `{Name}`, `{Piece}`, `{Clique}`, `{Rival}`, `{Day}`, `{Period}`, `{Moon}` |

**Testing**
- Play tests use **slot 4 "Testy" only**. Set `SlotCount = 4; -- NH TEMP slot test: set back to 3` in
  `Config.MainMenu` and set the `NHTestNoMenuKeys` attribute; put both back afterwards.
- Never load Rello, Ren or Raiyon. Never chat-type from test players.

**Saving and committing**
- Save only through ProfileService PlayerData. Never let players set Race.
- Commit in `E:\Nightmare-Highschool` with `git -c user.name=Rello`, explicit paths (`git commit -- <files>`), and
  this last line in every message: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Then push.
- **Version:** the next minor after the top of `CHANGELOG.md` when you commit Task 9 (it was 1.89.0 when this plan was
  written). Code comments say `(line matrix)`, not a version number.

---

## File structure

**Repo**: everything new lives in `tools/line-matrix/`

| Path | What it holds |
|---|---|
| `install.py` | makes an Edit-mode install snippet for one file (source, path, class, checksum) |
| `Config.CliqueTalk.luau` | the loader: a table of its child modules |
| `CliqueTalk/Generic.luau` | lines for every moment, for students without a clique and as the fallback |
| `CliqueTalk/<Clique>.luau` | one per clique: Vigil, Court, Athletes, Delinquents, Pack, Ordinary, Choir, Ink |
| `Talk.luau` | `StudentBrain.Talk`: Attitude, Pool, Pick, Line, Wear, Outfit, Use, IsMember, FirstName |
| `tests/coverage.luau` | every clique, moment and attitude has its own line; length, placeholders, banned words |
| `tests/talk.luau` | attitude and memory, pool fallback, placeholder filtering, stand-ins |
| `tests/outfit.luau` | outfit verdicts per clique |
| `tests/wear.luau` | `NHWear` stamping on a dummy rig |
| `patches/*.json` | the `multi_edit` old/new pairs applied to existing Studio scripts, kept as a record |

**Changed**
- `tools/ct-npc-1862/StudentBrain.luau`: the full new source.
- `tools/npc-nudges/Nudges.luau`: the full new source. The Map copy is updated at the Map port, not now.

**Studio (Combat Test)**
- New:
  - `ReplicatedStorage.Config.CliqueTalk` and its 9 children;
  - `ServerScriptService.Services.AI.StudentBrain.Talk`.
- Changed:
  - `ServerScriptService.Services.AI.StudentBrain` and `StudentBrain.Nudges`;
  - `ReplicatedStorage.UI.Appearance`, `ReplicatedStorage.Config.Cliques`;
  - `ServerScriptService.Services.Social.Cliques`, `ServerScriptService.Services.Quests.Quests`;
  - `ServerScriptService.Services.Social.Dialogue`, `ServerStorage.Dialogue.QuestChoices`;
  - `ServerScriptService.Services.Social.Hangouts`.

**Docs:** `docs/Line-Matrix.md`, `CHANGELOG.md`, `updates/discord/game-updates/<date>-line-matrix.md`, and the vault
mirror.

---

### Task 1: Install helper, the CliqueTalk loader, Generic lines, coverage test

**Files:**
- Create:
  - `tools/line-matrix/install.py`
  - `tools/line-matrix/Config.CliqueTalk.luau`
  - `tools/line-matrix/CliqueTalk/Generic.luau`
  - `tools/line-matrix/tests/coverage.luau`
- Studio: create `ReplicatedStorage.Config.CliqueTalk` (ModuleScript) and its child `Generic`.

**Interfaces:**
- Produces:
  - `require(ReplicatedStorage.Config.CliqueTalk)` returns `{ [ModuleName]: { [Moment]: Node } }`.
  - A `Node` is `{ [Attitude | "Any"]: { string } }`, or for `Race` and `Outfit` it is `{ [Sub]: Node }`.
  - `python tools/line-matrix/install.py <file> <Instance.Path> [Class]` prints a Luau snippet.

- [ ] **Step 1: Write the install helper**

```python
"""Install one repo file into Roblox Studio (NH line matrix).

Usage: python tools/line-matrix/install.py <source.luau> <Instance.Path> [ModuleScript|Script|LocalScript]
Prints a Luau snippet. Run it with the Roblox Studio execute_luau tool, datamodel "Edit". It creates or replaces the
script, then checks its Source against the file's checksum (h = (h*31 + byte) % 1000000007, CRLF -> LF).
The source travels inside the snippet, so no shared install buffer is used.
"""
import pathlib
import sys

src = pathlib.Path(sys.argv[1]).read_bytes().replace(b"\r\n", b"\n")
path = sys.argv[2]
cls = sys.argv[3] if len(sys.argv) > 3 else "ModuleScript"
h = 0
for b in src:
    h = (h * 31 + b) % 1000000007
text = src.decode("utf-8")
eq = "="
while "]" + eq + "]" in text:
    eq += "="
parts = path.split(".")
if parts[0] == "game":
    parts = parts[1:]
parts_lua = ", ".join('"' + p + '"' for p in parts)
print("assert(not game:GetService('RunService'):IsRunning(), 'Studio is in Play mode: install in Edit only')")
print("local Src = [" + eq + "[")
print(text + "]" + eq + "]")
print("local Parts = { " + parts_lua + " }")
print("local CLS, SUM = '" + cls + "', " + str(h))
print("""local Node = game:GetService(Parts[1])
for I = 2, #Parts - 1 do
	Node = Node:FindFirstChild(Parts[I]) or error(`missing {Parts[I]} under {Node:GetFullName()}`)
end
local Name = Parts[#Parts]
local S = Node:FindFirstChild(Name)
if S and not S:IsA(CLS) then error(`{S:GetFullName()} is a {S.ClassName}, not a {CLS}`) end
if not S then S = Instance.new(CLS) S.Name = Name S.Parent = Node end
S.Source = Src
local H = 0
local Got = S.Source
for I = 1, #Got do H = (H * 31 + string.byte(Got, I)) % 1000000007 end
assert(H == SUM, `checksum {H} ~= {SUM}`)
return `installed {S:GetFullName()}: {#Got} b, checksum {H}`""")
```

To install a file:
1. Run `python tools/line-matrix/install.py <file> <path> > "<scratchpad>/install.luau"` from
   `E:\Nightmare-Highschool`.
2. Read that file and pass its whole text as `code` to `execute_luau` (datamodel `Edit`).
3. Expected result: `installed ...: N b, checksum H`.

- [ ] **Step 2: Write the coverage test**

`tools/line-matrix/tests/coverage.luau`:

```lua
-- Line matrix coverage (NH Combat Test, Edit mode, run with execute_luau). Set ONLY to one module's name
-- ("Generic", "Vigil", ...) to check just that one; nil checks Generic and all 8 cliques.
local ONLY = nil
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = ReplicatedStorage:WaitForChild("Config")
assert(Config:FindFirstChild("CliqueTalk"), "Config.CliqueTalk is not installed")
local CT = require(Config.CliqueTalk:Clone()) -- a clone, so never a cached copy
local Cliques = require(Config.Cliques)
local MOMENTS = { "Greet", "Bump", "Crowded", "Shoved", "FightSeen", "Flee", "Transformed", "Night", "FullMoon", "Race", "Hurt", "Outfit", "DressCode" }
local SUBS = { Race = { "Human", "Priest", "Vampire", "Werewolf", "Ghoul", "Wraith" }, Outfit = { "FullLook", "RivalLook", "Likes", "Mocks" } }
local ATTS = { "Hostile", "Wary", "Neutral", "Friendly", "Respected" }
local KEYS = { Name = true, Piece = true, Clique = true, Rival = true, Day = true, Period = true, Moon = true }
local BANNED = { "blood", "bloody", "bleed", "bleeding", "gore", "guts", "corpse", "stab", "kill", "murder" }
local Fails, Cells, Count = {}, 0, 0

local function fail(Text) table.insert(Fails, Text) end

local function checkPool(Where, Pool)
	if typeof(Pool) ~= "table" then fail(`{Where}: not a list`) return end
	if #Pool < 3 or #Pool > 5 then fail(`{Where}: {#Pool} lines (want 3 to 5)`) end
	for _, L in Pool do
		Count += 1
		if typeof(L) ~= "string" then fail(`{Where}: not a string`) continue end
		if #L > 60 then fail(`{Where}: {#L} chars: {L}`) end
		for K in L:gmatch("{(%w*)}") do
			if not KEYS[K] then fail(`{Where}: unknown placeholder {K}: {L}`) end
		end
		local Low = L:lower()
		for _, W in BANNED do
			if Low:find("%f[%a]" .. W .. "%f[%A]") then fail(`{Where}: banned word "{W}": {L}`) end
		end
	end
end

local function checkNode(Where, Node, NoAny)
	if typeof(Node) ~= "table" then fail(`{Where}: missing`) return end
	for K, Pool in Node do
		if K ~= "Any" and not table.find(ATTS, K) then fail(`{Where}: unknown key {K}`) end
		checkPool(`{Where}.{K}`, Pool)
	end
	if NoAny and Node.Any then fail(`{Where}: uses Any (Greet must give every attitude its own lines)`) end
	for _, A in ATTS do
		Cells += 1
		local P = Node[A] or Node.Any
		if typeof(P) ~= "table" or #P == 0 then fail(`{Where}: nothing for {A} (would fall through to Generic)`) end
	end
end

local Names = { "Generic" }
for _, Id in Cliques.Order do table.insert(Names, Id) end
for _, Name in Names do
	if ONLY and Name ~= ONLY then continue end
	local Mod = CT[Name]
	if typeof(Mod) ~= "table" then fail(`{Name}: module missing`) continue end
	for K in Mod do
		if not table.find(MOMENTS, K) then fail(`{Name}: unknown moment {K}`) end
	end
	for _, Moment in MOMENTS do
		if SUBS[Moment] then
			for _, Sub in SUBS[Moment] do
				checkNode(`{Name}.{Moment}.{Sub}`, Mod[Moment] and Mod[Moment][Sub], false)
			end
		else
			checkNode(`{Name}.{Moment}`, Mod[Moment], Moment == "Greet" and Name ~= "Generic")
		end
	end
end
return if #Fails == 0 then `PASS: {Cells} cells, {Count} lines`
	else `FAIL ({#Fails}):\n` .. table.concat(Fails, "\n", 1, math.min(#Fails, 60))
```

- [ ] **Step 3: Run it to see it fail**

Run `tests/coverage.luau` with `ONLY = "Generic"` through `execute_luau` (Edit).
Expected: an error, `Config.CliqueTalk is not installed`.

- [ ] **Step 4: Write the loader**

`tools/line-matrix/Config.CliqueTalk.luau`:

```lua
--[[
	CliqueTalk (Config). ReplicatedStorage.Config.CliqueTalk  (the line matrix)

	What students say, by clique, moment and attitude. One child module per clique (named exactly like the clique in
	Config.Cliques.Order) plus Generic, each returning { [Moment] = { [Attitude | "Any"] = { lines } } }.
	Race and Outfit nest one more level: Race[RaceName][Attitude], Outfit[Verdict][Attitude].
	Read by Services.AI.StudentBrain.Talk (see docs/Line-Matrix.md). No gore, no slurs, no innuendo; 60 characters max.
]]

local CliqueTalk = {}
for _, Child in script:GetChildren() do
	if Child:IsA(`ModuleScript`) then
		local Ok, Mod = pcall(require, Child)
		if Ok and typeof(Mod) == `table` then
			CliqueTalk[Child.Name] = Mod
		else
			warn(`[CliqueTalk] {Child.Name} did not load: {Mod}`)
		end
	end
end
return CliqueTalk
```

- [ ] **Step 5: Write Generic**

`tools/line-matrix/CliqueTalk/Generic.luau`:

```lua
-- CliqueTalk.Generic: students without a clique, and the fallback for any clique cell left empty (the line matrix)
return {
	Greet = {
		Hostile = { `Get lost.`, `Not you.`, `Keep walking.`, `We're not friends.` };
		Wary = { `...Hey.`, `Oh. It's you.`, `What do you want?`, `Hm. Hi, I guess.` };
		Neutral = { `Hey.`, `Hi.`, `Sup.`, `How's it going?` };
		Friendly = { "Hey, {Name}!", `Oh good, it's you.`, "{Name}! What's up?", `Hey you. Good day?` };
		Respected = { "{Name}! Looking sharp.", `There's the legend.`, "Always good to see you, {Name}.", `Make way, everyone.` };
	};
	Bump = { Any = { `Watch it!`, `Whoa, sorry.`, `Excuse you.`, `Easy!` } };
	Crowded = { Any = { `Personal space?`, `Little room, please.`, `You're kind of close.`, `Can I help you?` } };
	Shoved = { Any = { `Hey! What was that?`, `Rude much?`, `Okay, ow.`, `Did you just shove me?` } };
	FightSeen = { Any = { `Ooh, here we go.`, `Somebody stop them!`, `I'm not watching. Okay, I'm watching.`, `Someone's getting detention.` } };
	Flee = { Any = { `Whoa, not near me!`, `Take it outside!`, `Nope. I'm out.`, `Someone get a teacher!` } };
	Transformed = { Any = { `What IS that?`, `Stay back...`, `Okay, that's new.`, `Please don't eat me.` } };
	Night = { Any = { `What are you doing out this late?`, `Stay in the light.`, `Late night, huh?`, `Careful out here.` } };
	FullMoon = { Any = { `Full moon tonight. Be careful.`, `You feel that? Full moon.`, `Don't go near the oaks tonight.` } };
	Race = {
		Human = { Any = { `Just a normal kid, huh? Lucky.`, `No fangs, no tail. Refreshing.`, `Human? Stick close to the lamps.` } };
		Priest = { Any = { `Bless you. Or whatever you say.`, `Oh good, someone holy.`, `Keep that cross handy.` } };
		Vampire = { Any = { `Is it colder near you?`, `Nice fangs. Real?`, `You're very pale. Eating okay?` } };
		Werewolf = { Any = { `Nice ears.`, `Is that a tail?`, `You smell like the woods.` } };
		Ghoul = { Any = { `You look... tired.`, `Did you sleep at all?`, `You're kind of grey today.` } };
		Wraith = { Any = { `I didn't hear you come up.`, `You walk really quietly.`, `Were you always here?` } };
	};
	Hurt = { Any = { `You okay? You look rough.`, `Go see the nurse.`, `Who did that to you?`, `Sit down before you fall down.` } };
	Outfit = {
		FullLook = { Any = { "Full {Clique} look, huh?", "Dressed like one of {Clique}.", "Matching {Clique}? Bold." } };
		RivalLook = { Any = { "{Rival} colours? Here?", "Dressed like {Rival}? Brave.", "That's a {Rival} look. People notice." } };
		Likes = { Any = { "Nice {Piece}.", "Where'd you get the {Piece}?", "Okay, the {Piece} is cool." } };
		Mocks = { Any = { "Is that a {Piece}? Really?", "Bold choice, the {Piece}.", "Hm. The {Piece}. Interesting." } };
	};
	DressCode = { Any = { `Members' corner. Dress the part.`, `Come back in our colours.`, `Not dressed like that, you're not.` } };
}
```

- [ ] **Step 6: Install both into Studio (Edit)**

Make and run one snippet for each (see Step 1):
- `install.py tools/line-matrix/Config.CliqueTalk.luau ReplicatedStorage.Config.CliqueTalk`
- `install.py tools/line-matrix/CliqueTalk/Generic.luau ReplicatedStorage.Config.CliqueTalk.Generic`

Expected: two `installed ...` results.

- [ ] **Step 7: Run coverage to see it pass**

Run `tests/coverage.luau` with `ONLY = "Generic"`.
Expected: `PASS: 105 cells, 88 lines`. That is 21 nodes (11 plain moments, 6 races, 4 outfit verdicts) × 5
attitudes, and the lines in Step 5.

- [ ] **Step 8: Commit**

```bash
git -c user.name=Rello add tools/line-matrix/install.py tools/line-matrix/Config.CliqueTalk.luau tools/line-matrix/CliqueTalk/Generic.luau tools/line-matrix/tests/coverage.luau
git -c user.name=Rello commit -m "Line matrix: CliqueTalk loader, Generic lines, coverage test, install helper" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- tools/line-matrix/install.py tools/line-matrix/Config.CliqueTalk.luau tools/line-matrix/CliqueTalk/Generic.luau tools/line-matrix/tests/coverage.luau
```

---

### Task 2: `StudentBrain.Talk`: attitude, pools, picking

**Files:**
- Create: `tools/line-matrix/Talk.luau` and `tools/line-matrix/tests/talk.luau`.
- Studio: create `ServerScriptService.Services.AI.StudentBrain.Talk` (ModuleScript).

**Interfaces:**
- Consumes:
  - `StudentBrain.Lines.Pick(S, Pool, Ctx) -> string?`, which avoids recent lines and fills `{Keys}` from `Ctx`;
  - `Config.CliqueTalk` from Task 1.
- Produces:
  - `Talk.Attitudes: { string }`, lowest first.
  - `Talk.Attitude(S, Player?) -> string`.
  - `Talk.Pool(Clique: string?, Moment: string, Attitude: string, Sub: string?) -> { string }?`
  - `Talk.Pick(S, Moment: string, Player: Player?, Opts: { Sub: string?, Attitude: string?, Piece: string?, Ctx: {}? }?) -> string?`
  - `Talk.Line(Clique: string, Moment: string, Player: Player?, Opts?) -> string?`: a stand-in student, for dialogue
    and notifications.
  - `Talk.IsMember(Player, Clique) -> boolean` and `Talk.FirstName(Player) -> string`: replaceable by tests.
  - `Talk.Use(Data: {}?, CliqueCfg: {}?)`: swaps in the line data or the clique config (for tests).

`Talk.Pick` takes an `Opts` table where the spec says `Sub?`: `Opts.Sub` is the spec's `Sub`.

- [ ] **Step 1: Write the failing test**

`tools/line-matrix/tests/talk.luau`:

```lua
-- Talk.Attitude / Pool / Pick / Line (NH Combat Test, Edit mode, run with execute_luau)
local SSS = game:GetService("ServerScriptService")
local RS = game:GetService("ReplicatedStorage")
local Brain = SSS.Services.AI.StudentBrain
assert(Brain:FindFirstChild("Talk"), "StudentBrain.Talk is not installed")
local Tmp = Instance.new("Folder")
Tmp.Name = "NHTalkTest"
Brain.Lines:Clone().Parent = Tmp
local TalkMod = Brain.Talk:Clone()
TalkMod.Parent = Tmp
Tmp.Parent = game:GetService("ServerStorage")
local Results, Bad = {}, 0
local function check(Name, Got, Want)
	local Ok = Got == Want
	if not Ok then Bad += 1 end
	table.insert(Results, (if Ok then "ok   " else "FAIL ") .. Name .. ": got " .. tostring(Got) .. ", want " .. tostring(Want))
end
local Ok, Err = pcall(function()
	local Talk = require(TalkMod)
	local Data = require(RS.Config.CliqueTalk:Clone())
	Data.Test = {
		Greet = { Friendly = { "F1 {Name}", "F2", "F3" } };
		Bump = { Any = { "Hi {Name}", "Hi {Piece}", "Plain" } };
	}
	Talk.Use(Data)
	Talk.IsMember = function() return false end
	Talk.FirstName = function(P) return P.DisplayName end
	local function player(Attrs)
		return { UserId = 7; DisplayName = "Testy"; Character = nil; GetAttribute = function(_, K) return Attrs[K] end }
	end
	local Friendly = player({ CliqueTier_Test = "Friendly" })
	local Neutral = player({ CliqueTier_Test = "Neutral" })
	local Hostile = player({ CliqueTier_Test = "Hostile" })
	local Wary = player({ CliqueTier_Test = "Wary" })
	check("tier only", Talk.Attitude({ Clique = "Test" }, Friendly), "Friendly")
	check("no tier", Talk.Attitude({ Clique = "Test" }, player({})), "Neutral")
	check("no player", Talk.Attitude({ Clique = "Test" }, nil), "Neutral")
	check("fought: a step down", Talk.Attitude({ Clique = "Test"; Memory = { [7] = { Fought = os.clock(); Met = 0 } } }, Friendly), "Neutral")
	check("fought, already Hostile", Talk.Attitude({ Clique = "Test"; Memory = { [7] = { Fought = os.clock(); Met = 0 } } }, Hostile), "Hostile")
	check("met often: a step up", Talk.Attitude({ Clique = "Test"; Memory = { [7] = { Fought = -1e9; Met = 5 } } }, Neutral), "Friendly")
	check("met often never makes Respected", Talk.Attitude({ Clique = "Test"; Memory = { [7] = { Fought = -1e9; Met = 9 } } }, Friendly), "Friendly")
	Talk.IsMember = function() return true end
	check("member is at least Friendly", Talk.Attitude({ Clique = "Test" }, Wary), "Friendly")
	Talk.IsMember = function() return false end
	check("own pool", Talk.Pool("Test", "Greet", "Friendly")[1], "F1 {Name}")
	check("falls back to Generic", Talk.Pool("Test", "Greet", "Hostile"), Data.Generic.Greet.Hostile)
	check("no clique uses Generic", Talk.Pool(nil, "Bump", "Neutral"), Data.Generic.Bump.Any)
	check("unknown moment", Talk.Pool("Test", "NoSuchMoment", "Neutral"), nil)
	local Line = Talk.Pick({ Clique = "Test" }, "Greet", Friendly)
	check("pick fills the name", Line == "F1 Testy" or Line == "F2" or Line == "F3", true)
	local SawPiece = false
	for _ = 1, 40 do
		local L = Talk.Pick({ Clique = "Test" }, "Bump", Friendly)
		if L == nil or L:find("{", 1, true) then SawPiece = true end
	end
	check("never an unfilled line", SawPiece, false)
	local WithPiece = 0
	for _ = 1, 40 do
		if Talk.Pick({ Clique = "Test" }, "Bump", Friendly, { Piece = "top hat" }) == "Hi top hat" then WithPiece += 1 end
	end
	check("a piece line once a piece is given", WithPiece > 0, true)
	check("attitude override", Talk.Pick({ Clique = "Test" }, "Greet", Friendly, { Attitude = "Hostile" }) ~= nil, true)
	check("stand-in line", Talk.Line("Test", "Greet", Friendly) ~= nil, true)
	check("stand-in, missing moment", Talk.Line("Test", "NoSuchMoment", Friendly), nil)
end)
Tmp:Destroy()
if not Ok then return "ERROR: " .. tostring(Err) end
return (if Bad == 0 then "PASS\n" else `FAIL ({Bad})\n`) .. table.concat(Results, "\n")
```

- [ ] **Step 2: Run it to see it fail**

Run `tests/talk.luau` through `execute_luau` (Edit).
Expected: an error, `StudentBrain.Talk is not installed`.

- [ ] **Step 3: Write Talk**

`tools/line-matrix/Talk.luau`:

```lua
--[[
	Talk (server). Services.AI.StudentBrain.Talk  (the line matrix; spec docs/superpowers/specs/2026-11-12-line-matrix-outfits-design.md)

	What a student says depends on their clique (Config.CliqueTalk has one module per clique, plus Generic), how they
	feel about you, and the moment. How they feel: your standing tier with their clique (CliqueTier_<Id>), at least
	Friendly if you're a member, one step down if they saw you fight in the last 5 minutes, one step up (never past
	Friendly) if you've met 4 times or more.

	API
	  Talk.Attitude(S, Player?) -> "Hostile" | "Wary" | "Neutral" | "Friendly" | "Respected"
	  Talk.Pool(Clique?, Moment, Attitude, Sub?) -> lines?      the clique's own (attitude, then Any), then Generic's
	  Talk.Pick(S, Moment, Player?, Opts?) -> line?            Opts: Sub (race / verdict), Attitude, Piece, Ctx
	  Talk.Line(Clique, Moment, Player?, Opts?) -> line?        a stand-in student: a leader in dialogue, a notification
	  Talk.Wear(Player) -> { Top, Bottoms, Acc }?               from the character's NHWear (set by UI.Appearance)
	  Talk.Outfit(S, Player) -> (Verdict?, PieceName?)          FullLook | RivalLook | Likes | Mocks (Task 4)
	  Talk.Use(Data?, CliqueCfg?)                               tests: swap the line data / clique config
	Lines with a {Key} that can't be filled (no name, no piece) are skipped, never shown half-filled.
]]

local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Lines = require(script.Parent:WaitForChild(`Lines`))
local CliqueConfig = require(ReplicatedStorage.Config.Cliques)
local CliqueTalk = require(ReplicatedStorage.Config:WaitForChild(`CliqueTalk`))
local Accessories = require(ReplicatedStorage.Config.Accessories)

local Talk = {}
Talk.Attitudes = { `Hostile`, `Wary`, `Neutral`, `Friendly`, `Respected` }
local Rank = {}
for I, A in Talk.Attitudes do Rank[A] = I end

function Talk.Use(Data: { [string]: any }?, CliqueCfg: { [string]: any }?)
	if Data then CliqueTalk = Data end
	if CliqueCfg then CliqueConfig = CliqueCfg end
end

-- membership (Social.CliqueMembership)
function Talk.IsMember(Player: Player, Clique: string): boolean
	local Social = ServerScriptService:FindFirstChild(`Services`) and ServerScriptService.Services:FindFirstChild(`Social`)
	local Node = Social and Social:FindFirstChild(`CliqueMembership`)
	if not Node then return false end
	local Ok, Is = pcall(function() return require(Node).IsMember(Player, Clique) end)
	return Ok and Is == true
end

-- the name students use: the student's first name (Player.Identity), else the display name (as CliqueMembership does)
function Talk.FirstName(Player: Player): string
	local Name = Player.DisplayName
	pcall(function()
		local Identity = require(ServerScriptService.Services.Player.Identity)
		local Full = Identity.FullName(Identity.Get(Player))
		if typeof(Full) == `string` and Full ~= `` then Name = Full end
	end)
	return string.match(Name, `^(%S+)`) or Name
end

function Talk.Attitude(S, Player: Player?): string
	if not Player then return `Neutral` end
	local Tier = S.Clique and Player:GetAttribute(`CliqueTier_{S.Clique}`)
	local R = Rank[Tier or `Neutral`] or Rank.Neutral
	if S.Clique and Talk.IsMember(Player, S.Clique) then R = math.max(R, Rank.Friendly) end
	local M = S.Memory and S.Memory[Player.UserId]
	if M then
		if os.clock() - (M.Fought or -1e9) < 300 then
			R -= 1
		elseif (M.Met or 0) >= 4 and R < Rank.Friendly then
			R += 1
		end
	end
	return Talk.Attitudes[math.clamp(R, 1, #Talk.Attitudes)]
end

local function cell(Mod: any, Moment: string, Sub: string?, Attitude: string): { string }?
	local Node = typeof(Mod) == `table` and Mod[Moment] or nil
	if Node and Sub then Node = Node[Sub] end
	if typeof(Node) ~= `table` then return nil end
	local P = Node[Attitude]
	if typeof(P) == `table` and #P > 0 then return P end
	P = Node.Any
	if typeof(P) == `table` and #P > 0 then return P end
	return nil
end

function Talk.Pool(Clique: string?, Moment: string, Attitude: string, Sub: string?): { string }?
	return cell(Clique and CliqueTalk[Clique], Moment, Sub, Attitude) or cell(CliqueTalk.Generic, Moment, Sub, Attitude)
end

-- the lines whose every {Key} has a value
local function fillable(Pool: { string }, Ctx: { [string]: any }): { string }
	local Out = {}
	for _, L in Pool do
		local Ok = true
		for K in L:gmatch("{(%w+)}") do
			if Ctx[K] == nil then Ok = false break end
		end
		if Ok then table.insert(Out, L) end
	end
	return Out
end

function Talk.Pick(S, Moment: string, Player: Player?, Opts: { [string]: any }?): string?
	local O = Opts or {}
	local Attitude = O.Attitude or Talk.Attitude(S, Player)
	local Pool = Talk.Pool(S.Clique, Moment, Attitude, O.Sub)
	if not Pool then return nil end
	local Ctx = table.clone(O.Ctx or {})
	if Player then Ctx.Name = Talk.FirstName(Player) end
	Ctx.Piece = O.Piece
	local Def = S.Clique and CliqueConfig.Defs[S.Clique]
	if Def then
		Ctx.Clique = Def.Name
		local Rival = Def.Rival and CliqueConfig.Defs[Def.Rival]
		Ctx.Rival = Rival and Rival.Name
	end
	local Ready = fillable(Pool, Ctx)
	if #Ready == 0 then return nil end
	return Lines.Pick(S, Ready, Ctx)
end

local Stand = {} :: { [string]: { [string]: any } }
function Talk.Line(Clique: string, Moment: string, Player: Player?, Opts: { [string]: any }?): string?
	Stand[Clique] = Stand[Clique] or { Clique = Clique }
	return Talk.Pick(Stand[Clique], Moment, Player, Opts)
end

return Talk
```

- [ ] **Step 4: Install and run the test to see it pass**

Install with `install.py tools/line-matrix/Talk.luau ServerScriptService.Services.AI.StudentBrain.Talk`, then run
`tests/talk.luau`.

Expected: `PASS` followed by 18 `ok` lines.

`Talk` is not required by anything yet, so the live game is unchanged.

- [ ] **Step 5: Commit**

```bash
git -c user.name=Rello add tools/line-matrix/Talk.luau tools/line-matrix/tests/talk.luau
git -c user.name=Rello commit -m "Line matrix: StudentBrain.Talk (attitude, pools, picking) and its test" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- tools/line-matrix/Talk.luau tools/line-matrix/tests/talk.luau
```

---

### Task 3: Stamp what a player wears (`NHWear`)

**Files:**
- Studio: change `ReplicatedStorage.UI.Appearance` (`Appearance.ApplyTo`).
- Create: `tools/line-matrix/patches/Appearance.json` and `tools/line-matrix/tests/wear.luau`.

**Interfaces:**
- Produces the character attribute `NHWear = "<top id>|<bottoms id>|<acc id>,<acc id>..."`.
  - An unknown or avatar top or bottoms gives an empty field.
  - It is set on every non-NPC character `ApplyTo` dresses that is not in a transformed form.
  - Only the server's `ApplyTo` writes it.

- [ ] **Step 1: Check the fields this relies on**

Run in Edit:

```lua
local A = require(game.ReplicatedStorage.UI.Appearance:Clone())
local d = A.Sanitize({ Uniform = "varsity-jacket", Bottoms = "striped-joggers", Acc = { "hat-top", "collar-ruff" } })
return string.format("Uniform=%s Bottoms=%s Acc=%s UseAvatar=%s top=%s bottoms=%s", tostring(d.Uniform), tostring(d.Bottoms),
	typeof(d.Acc) == "table" and table.concat(d.Acc, ",") or tostring(d.Acc), tostring(d.UseAvatar),
	tostring(A.IdOf("Uniform", d.Uniform)), tostring(A.IdOf("Bottoms", d.Bottoms)))
```

**Expected:**
- `Uniform` and `Bottoms` are indices.
- `Acc` lists `hat-top,collar-ruff`.
- `top=varsity-jacket` and `bottoms=striped-joggers`.

If `Acc` is not a list of id strings, or the `IdOf` keys differ, stop. Adjust the stamp code in Step 3 to the real
shape and write it down in the patch file.

- [ ] **Step 2: Write the failing test**

`tools/line-matrix/tests/wear.luau`:

```lua
-- NHWear stamping (NH Combat Test, Edit mode, run with execute_luau): dress a dummy rig, read its NHWear
local Players = game:GetService("Players")
local A = require(game.ReplicatedStorage.UI.Appearance:Clone())
local Rig = Players:CreateHumanoidModelFromDescription(Instance.new("HumanoidDescription"), Enum.HumanoidRigType.R6)
Rig.Name = "NHWearTest"
Rig.Parent = workspace
local Ok, Err = pcall(A.ApplyTo, Rig, { Uniform = "varsity-jacket", Bottoms = "striped-joggers", Acc = { "hat-top", "collar-ruff" }, HairId = 0 })
local Got = Rig:GetAttribute("NHWear")
Rig:Destroy()
if not Ok then return "ERROR: " .. tostring(Err) end
local Want = "varsity-jacket|striped-joggers|hat-top,collar-ruff"
return if Got == Want then "PASS " .. Got else "FAIL got " .. tostring(Got) .. ", want " .. Want
```

- [ ] **Step 3: Run it to see it fail**

Expected: `FAIL got nil, want varsity-jacket|striped-joggers|hat-top,collar-ruff`.

If it errors before that (for example the rig can't be made in Edit mode), run the same check in Task 8 on Testy's
character instead and note that here.

- [ ] **Step 4: Add the stamp**

First checksum Studio's `UI.Appearance` against `Studio/audit_all/live2/187_ReplicatedStorage.UI.Appearance.luau`.
If they differ, read the live text around `ApplyTo` and match `old_string` to it.

Apply with `multi_edit` on `game.ReplicatedStorage.UI.Appearance` (Edit), and save the pair to
`tools/line-matrix/patches/Appearance.json`:

old_string:
```lua
	if Appearance.IsNpc(character) then
		data = Appearance.DressCode(character, data) -- NPCs only (never players, previews or the menu's posed students)
	end
```

new_string:
```lua
	if Appearance.IsNpc(character) then
		data = Appearance.DressCode(character, data) -- NPCs only (never players, previews or the menu's posed students)
	elseif not Appearance.FormOf(character) then
		-- (line matrix) what this character wears, for students' outfit remarks and the hangout dress codes
		-- (StudentBrain.Talk, Social.Cliques.Dressed): "top|bottoms|acc,acc". A transformed form keeps the last one.
		local acc = {}
		for _, id in ipairs(type(data.Acc) == "table" and data.Acc or {}) do
			if type(id) == "string" then
				table.insert(acc, id)
			end
		end
		local avatar = data.UseAvatar == true
		character:SetAttribute("NHWear", string.format("%s|%s|%s",
			(not avatar and Appearance.IdOf("Uniform", data.Uniform)) or "",
			(not avatar and Appearance.IdOf("Bottoms", data.Bottoms)) or "",
			table.concat(acc, ",")))
	end
```

- [ ] **Step 5: Run the test to see it pass**

Run `tests/wear.luau` again.
Expected: `PASS varsity-jacket|striped-joggers|hat-top,collar-ruff`.

- [ ] **Step 6: Commit**

```bash
git -c user.name=Rello add tools/line-matrix/patches/Appearance.json tools/line-matrix/tests/wear.luau
git -c user.name=Rello commit -m "Line matrix: UI.Appearance stamps NHWear (top|bottoms|accessories) on dressed characters" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- tools/line-matrix/patches/Appearance.json tools/line-matrix/tests/wear.luau
```

---

### Task 4: Clique taste and outfit verdicts

**Files:**
- Studio: change `ReplicatedStorage.Config.Cliques` (append before `return Cliques`).
- Modify: `tools/line-matrix/Talk.luau` (add `Wear` and `Outfit`).
- Create: `tools/line-matrix/patches/ConfigCliques.json` and `tools/line-matrix/tests/outfit.luau`.

**Interfaces:**
- Consumes `NHWear` from Task 3, and `Talk` from Task 2.
- Produces:
  - `Cliques.ParseWear(W: any) -> { Top: string, Bottoms: string, Acc: { string } }?`
  - `Cliques.WearsTop(Id: string, Top: string?) -> boolean` and `Cliques.WearsBottoms(Id: string, Bottoms: string?) -> boolean`.
    Each checks `Look.Tops`, `Look.FemaleTops`, `Look.Civ.Tops` and `Look.Civ.FemaleTops` (the bottoms version checks
    the bottoms lists the same way).
  - `Cliques.Defs[Id].Taste = { Likes = { Rule }, Mocks = { Rule } }`, where a `Rule` is `{ Id = }`, `{ Kit = }`,
    `{ Slot = }` or `{ Top = }`.
  - `Cliques.Defs[Id].Look.FemaleTops`.
  - `Talk.Wear(Player) -> { Top, Bottoms, Acc }?`
  - `Talk.Outfit(S, Player) -> (string?, string?)`: the verdict and the piece name in lower case.

**`FemaleTops`** adds the girls' clique tops so a girl in her clique's look counts as wearing it. This is a small
addition to the spec, which only lists `Look.Tops` and `Civ.Tops`.

- [ ] **Step 1: Write the failing test**

`tools/line-matrix/tests/outfit.luau`:

```lua
-- Talk.Outfit verdicts (NH Combat Test, Edit mode, run with execute_luau)
local SSS = game:GetService("ServerScriptService")
local RS = game:GetService("ReplicatedStorage")
local Brain = SSS.Services.AI.StudentBrain
local Tmp = Instance.new("Folder")
Tmp.Name = "NHOutfitTest"
Brain.Lines:Clone().Parent = Tmp
local TalkMod = Brain.Talk:Clone()
TalkMod.Parent = Tmp
Tmp.Parent = game:GetService("ServerStorage")
local Results, Bad = {}, 0
local Ok, Err = pcall(function()
	local Talk = require(TalkMod)
	local CC = require(RS.Config.Cliques:Clone())
	assert(CC.ParseWear and CC.WearsTop, "Config.Cliques has no ParseWear / WearsTop yet")
	Talk.Use(require(RS.Config.CliqueTalk:Clone()), CC)
	local function wearing(W)
		return { UserId = 7; DisplayName = "Testy"; GetAttribute = function() return nil end;
			Character = { GetAttribute = function(_, K) return if K == "NHWear" then W else nil end } }
	end
	local function case(Name, Clique, W, WantVerdict, WantPiece)
		local V, P = Talk.Outfit({ Clique = Clique }, wearing(W))
		local Good = V == WantVerdict and P == WantPiece
		if not Good then Bad += 1 end
		table.insert(Results, (if Good then "ok   " else "FAIL ") .. Name .. `: got {V}, {P}; want {WantVerdict}, {WantPiece}`)
	end
	case("Athletes full look", "Athletes", "varsity-jacket|striped-joggers|", "FullLook", nil)
	case("Athletes see an Ink top", "Athletes", "black-shirt|uniform-trousers|", "RivalLook", nil)
	case("Choir like the ruff", "Choir", "ivory-polo|khaki-trousers|collar-ruff", "Likes", "falling ruff")
	case("Athletes mock the grimoire", "Athletes", "navy-polo|uniform-trousers|grimoire-chained", "Mocks", "chained grimoire")
	case("Vigil: nothing to say", "Vigil", "navy-polo|uniform-trousers|", nil, nil)
	case("Vigil girl's full look", "Vigil", "vigil-vest-f|pleated-tartan-skirt|", "FullLook", nil)
	case("no NHWear", "Vigil", nil, nil, nil)
	case("clique-less student, one piece", nil, "navy-polo|uniform-trousers|hat-top", "Likes", "crimson-banded top hat")
	local W = CC.ParseWear("a|b|x,y")
	local Parsed = W and W.Top == "a" and W.Bottoms == "b" and #W.Acc == 2
	if not Parsed then Bad += 1 end
	table.insert(Results, (if Parsed then "ok   " else "FAIL ") .. "ParseWear")
	for Id, Def in CC.Defs do
		local Rival = Def.Rival and CC.Defs[Def.Rival]
		for _, R in (Def.Taste and Def.Taste.Likes) or {} do
			for _, R2 in (Rival and Rival.Taste and Rival.Taste.Likes) or {} do
				if R.Id and R.Id == R2.Id then Bad += 1 table.insert(Results, `FAIL {Id} and its rival both like {R.Id}`) end
			end
		end
	end
end)
Tmp:Destroy()
if not Ok then return "ERROR: " .. tostring(Err) end
return (if Bad == 0 then "PASS\n" else `FAIL ({Bad})\n`) .. table.concat(Results, "\n")
```

- [ ] **Step 2: Run it to see it fail**

Expected: `ERROR: ... Config.Cliques has no ParseWear / WearsTop yet`.

- [ ] **Step 3: Append the helpers, girls' tops and taste to Config.Cliques**

1. Pull the live `ReplicatedStorage.Config.Cliques` source.
2. Confirm it ends with `return Cliques`, and that every top id below is in `Appearance.Uniforms`. All of them were
   there on 2026-11-12.
3. Use `multi_edit`: `old_string` is the final `return Cliques`, and `new_string` is the block below followed by
   `return Cliques`.
4. Save the pair to `tools/line-matrix/patches/ConfigCliques.json`.

```lua
---| (line matrix) what you wear: NHWear, the clique looks, taste |---

-- what a character wears, from its NHWear attribute ("top|bottoms|acc,acc"; set by UI.Appearance.ApplyTo)
function Cliques.ParseWear(W: any): { Top: string, Bottoms: string, Acc: { string } }?
	if typeof(W) ~= `string` then return nil end
	local Top, Bottoms, Acc = string.match(W, `^([^|]*)|([^|]*)|(.*)$`)
	if not Top then return nil end
	local List = {}
	for Id in string.gmatch(Acc, `[^,]+`) do table.insert(List, Id) end
	return { Top = Top; Bottoms = Bottoms; Acc = List }
end

local function listed(L: { string }?, Id: string?): boolean
	return L ~= nil and Id ~= nil and Id ~= `` and table.find(L, Id) ~= nil
end

-- wearing one of a clique's tops (school or civvies, boys' or girls')
function Cliques.WearsTop(Id: string, Top: string?): boolean
	local L = Cliques.Defs[Id] and Cliques.Defs[Id].Look
	if not L then return false end
	return listed(L.Tops, Top) or listed(L.FemaleTops, Top) or (L.Civ ~= nil and (listed(L.Civ.Tops, Top) or listed(L.Civ.FemaleTops, Top)))
end

function Cliques.WearsBottoms(Id: string, Bottoms: string?): boolean
	local L = Cliques.Defs[Id] and Cliques.Defs[Id].Look
	if not L then return false end
	return listed(L.Bottoms, Bottoms) or listed(L.FemaleBottoms, Bottoms)
		or (L.Civ ~= nil and (listed(L.Civ.Bottoms, Bottoms) or listed(L.Civ.FemaleBottoms, Bottoms)))
end

-- the girls' versions of each clique's school top
local FemaleTops = {
	Vigil = { `vigil-vest-f` }; Court = { `crimson-court-blazer` }; Athletes = { `cheer-uniform`, `track-jacket` };
	Delinquents = { `delinquent-long-blazer` }; Pack = { `forest-vest-f` }; Ordinary = { `navy-vest-f`, `crest-blazer` };
	Choir = { `choir-capelet`, `chapel-corset` }; Ink = { `ink-club-blouse` };
}
for Id, Tops in FemaleTops do
	local Look = Cliques.Defs[Id] and Cliques.Defs[Id].Look
	if Look then Look.FemaleTops = Tops end
end

-- what each clique likes and mocks on you (Config.Accessories ids; a clique never likes what its rival likes)
local Taste = {
	Vigil = {
		Likes = { { Id = `watch-pocket` }, { Id = `lantern-candle` }, { Id = `tube-scroll` }, { Id = `coat-scholar` }, { Id = `coat-lamplighter` }, { Id = `book-strap` }, { Id = `pin-vigil` } };
		Mocks = { { Id = `hat-fascinator` }, { Id = `mask-gilt` }, { Id = `jacket-smoking` }, { Id = `parasol-lace` }, { Id = `pin-court` } };
	};
	Court = {
		Likes = { { Id = `hat-top` }, { Id = `mask-gilt` }, { Id = `clasp-opera` }, { Id = `jacket-smoking` }, { Id = `ring-bat-signet` }, { Id = `parasol-lace` }, { Id = `hat-fascinator` }, { Id = `pin-court` } };
		Mocks = { { Id = `coat-lamplighter` }, { Id = `bag-messenger` }, { Id = `tube-scroll` }, { Id = `cloak-oilskin` }, { Id = `pin-vigil` } };
	};
	Athletes = {
		Likes = { { Id = `jacket-varsity` }, { Id = `pin-athletes` }, { Id = `scarf-knit-crimson` }, { Id = `bag-messenger` } };
		Mocks = { { Id = `grimoire-chained` }, { Id = `case-violin` }, { Id = `collar-ruff` }, { Id = `parasol-lace` }, { Id = `pin-ink` } };
	};
	Delinquents = {
		Likes = { { Id = `coat-delinquent` }, { Id = `pin-delinquents` }, { Id = `mask-grille` }, { Id = `pauldrons-blackened` }, { Id = `gorget-steel` } };
		Mocks = { { Id = `sash-prefect` }, { Id = `tie-bow` }, { Id = `umbrella-crook` }, { Id = `book-strap` }, { Id = `pin-ordinary` } };
	};
	Pack = {
		Likes = { { Id = `necklace-wolf-fang` }, { Id = `fur-torn` }, { Id = `mask-wolf` }, { Id = `torc-moonstone` }, { Id = `jacket-hunting` }, { Id = `pin-pack` } };
		Mocks = { { Id = `collar-choir` }, { Id = `mask-wax` }, { Id = `pendant-crystal` }, { Id = `pin-choir` } };
	};
	Ordinary = {
		Likes = { { Id = `umbrella-crook` }, { Id = `cloak-oilskin` }, { Id = `tie-school` }, { Id = `coat-cardigan` }, { Id = `coat-cadet` }, { Id = `pin-ordinary` } };
		Mocks = { { Id = `mask-bone` }, { Id = `pendant-scythe` }, { Id = `crossbow-hunter` }, { Id = `pin-delinquents` } };
	};
	Choir = {
		Likes = { { Id = `collar-choir` }, { Id = `collar-ruff` }, { Id = `mask-wax` }, { Id = `pendant-crystal` }, { Id = `halo-rune` }, { Id = `pin-choir` } };
		Mocks = { { Id = `mask-wolf` }, { Id = `necklace-wolf-fang` }, { Id = `hat-witch` }, { Id = `grimoire-chained` }, { Id = `pin-pack` } };
	};
	Ink = {
		Likes = { { Id = `mask-fox` }, { Id = `mask-moth` }, { Id = `mask-domino` }, { Id = `backpack-batwing` }, { Id = `scarf-knit-violet` }, { Id = `bag-satchel` }, { Id = `pin-ink` } };
		Mocks = { { Id = `jacket-varsity` }, { Id = `sash-prefect` }, { Id = `sash-head` }, { Id = `tie-school` }, { Id = `pin-athletes` } };
	};
}
for Id, T in Taste do
	if Cliques.Defs[Id] then Cliques.Defs[Id].Taste = T end
end

```

- [ ] **Step 4: Add `Talk.Wear` and `Talk.Outfit`**

In `tools/line-matrix/Talk.luau`, put this immediately before the final `return Talk`:

```lua
---| outfits |---

function Talk.Wear(Player: Player?): { Top: string, Bottoms: string, Acc: { string } }?
	local C = Player and Player.Character
	return C and CliqueConfig.ParseWear(C:GetAttribute(`NHWear`)) or nil
end

-- the name of the worn piece a taste rule matches, in lower case
local function matched(Rule: { [string]: string }, W): string?
	if Rule.Top then return if W.Top == Rule.Top then (string.gsub(W.Top, `-`, ` `)) else nil end
	for _, Id in W.Acc do
		local It = Accessories.ById[Id]
		if It and (Rule.Id == Id or (Rule.Kit ~= nil and It.Kit == Rule.Kit) or (Rule.Slot ~= nil and It.Slot == Rule.Slot)) then
			return string.lower(It.Name)
		end
	end
	return nil
end

-- what this student thinks of your outfit (first match wins): their clique's full look, their rival's top, a piece
-- they like, a piece they mock. A student without a clique only remarks on a random accessory you wear.
function Talk.Outfit(S, Player: Player?): (string?, string?)
	local W = Talk.Wear(Player)
	if not W then return nil end
	local Id = S.Clique
	local Def = Id and CliqueConfig.Defs[Id]
	if not Def then
		if #W.Acc == 0 then return nil end
		local It = Accessories.ById[W.Acc[math.random(1, #W.Acc)]]
		if not It then return nil end
		return `Likes`, string.lower(It.Name)
	end
	if CliqueConfig.WearsTop(Id, W.Top) and CliqueConfig.WearsBottoms(Id, W.Bottoms) then return `FullLook` end
	if Def.Rival and CliqueConfig.WearsTop(Def.Rival, W.Top) then return `RivalLook` end
	local T = Def.Taste or {}
	for _, R in T.Likes or {} do
		local N = matched(R, W)
		if N then return `Likes`, N end
	end
	for _, R in T.Mocks or {} do
		local N = matched(R, W)
		if N then return `Mocks`, N end
	end
	return nil
end
```

- [ ] **Step 5: Reinstall Talk and run the tests to see them pass**

1. Reinstall `Talk.luau` with `install.py`.
2. Run `tests/outfit.luau`. Expected: `PASS` and 9 `ok` lines.
3. Run `tests/talk.luau` again. Expected: `PASS`.

- [ ] **Step 6: Commit**

```bash
git -c user.name=Rello add tools/line-matrix/Talk.luau tools/line-matrix/tests/outfit.luau tools/line-matrix/patches/ConfigCliques.json
git -c user.name=Rello commit -m "Line matrix: clique taste, girls' clique tops, NHWear parsing and outfit verdicts" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- tools/line-matrix/Talk.luau tools/line-matrix/tests/outfit.luau tools/line-matrix/patches/ConfigCliques.json
```

---

### Task 5: The brain speaks through the matrix

**Files:**
- Modify: `tools/ct-npc-1862/StudentBrain.luau` (then install it whole) and `tools/npc-nudges/Nudges.luau` (then
  install it whole).
- Studio: `ServerScriptService.Services.AI.StudentBrain` and its child `Nudges`.

**Interfaces:**
- Consumes `Talk.Attitude`, `Talk.Pick`, `Talk.Outfit` and `Appearance.FormOf`.
- Produces:
  - `sayMatrix(S, Moment, Pl?, Opts?, Cooldown?, Fallback?) -> boolean`, a local in StudentBrain;
  - `Nudges.OnShove: ((S, Rec) -> ())?`, called after the shove's look back.

- [ ] **Step 1: Check the repo copies are still current**

Checksum Studio's `StudentBrain` and `StudentBrain.Nudges` against the repo files.

| Script | Repo file | Size | Checksum |
|---|---|---|---|
| `StudentBrain` | `tools/ct-npc-1862/StudentBrain.luau` | 29,690 b | 651359752 |
| `StudentBrain.Nudges` | `tools/npc-nudges/Nudges.luau` | 11,984 b | 569008342 |

If either differs, pull the live source into the repo file first.

- [ ] **Step 2: Add requires and the Nudges handle**

In `StudentBrain.luau`, replace

```lua
local Lines = require(script:WaitForChild(`Lines`))
local CliqueConfig = require(ReplicatedStorage.Config.Cliques)
```

with

```lua
local Lines = require(script:WaitForChild(`Lines`))
local Talk = require(script:WaitForChild(`Talk`)) -- (line matrix) clique x attitude x moment
local CliqueConfig = require(ReplicatedStorage.Config.Cliques)
local Appearance = require(ReplicatedStorage.UI.Appearance)
```

and replace

```lua
Brain.OnBump = require(script:WaitForChild(`Nudges`)).Handle :: ((any, any, string) -> boolean)? -- (1.86.3) the nudges
```

with

```lua
local NudgeMod = require(script:WaitForChild(`Nudges`))
Brain.OnBump = NudgeMod.Handle :: ((any, any, string) -> boolean)? -- (1.86.3) the nudges
```

- [ ] **Step 3: Add `sayMatrix`**

Directly after the `sayText` function (it ends with `bubble(S, Lines.Fill(Text, ctx()))` and `end`), insert:

```lua
-- say a line from the line matrix (StudentBrain.Talk: this student's clique, how they feel about Pl, the moment), or
-- one from Fallback (today's pool) when the matrix has nothing. Opts: Sub (race / outfit verdict), Attitude, Piece.
local function sayMatrix(S, Moment: string, Pl: Player?, Opts: { [string]: any }?, Cooldown: number?, Fallback: { string }?): boolean
	if os.clock() - (S.SaidAt or -1e9) < (Cooldown or 8) or not S.Model then return false end
	local O = table.clone(Opts or {})
	O.Ctx = O.Ctx or ctx()
	local Ok, Text = pcall(Talk.Pick, S, Moment, Pl, O)
	if Ok and Text then
		bubble(S, Text)
		return true
	end
	return Fallback ~= nil and say(S, Fallback, Cooldown)
end

-- a shove (Nudges) gets its own line once the student turns to look at who did it
NudgeMod.OnShove = function(S, Rec)
	sayMatrix(S, `Shoved`, Rec and Rec.Player, nil, 0, Lines.MakeWay)
end
```

- [ ] **Step 4: Replace `greeting` and `greet`**

Replace the whole `local function greeting(S, Rec): { string }` ... `end` and the following
`local function greet(S, Rec): boolean` ... `end` with:

```lua
-- the time-of-day hello (today's pools), the matrix's fallback
local function daily(C): { string }
	local G = Lines.Greet
	if C.Night then
		if C.Moon == `Full` and math.random() < 0.6 then return G.FullMoon end
		if C.Moon == `New` and math.random() < 0.4 then return G.NewMoon end
		return G.Night
	end
	local H = game:GetService(`Lighting`).ClockTime
	return if H < 11 then G.Morning elseif H >= 16.5 then G.Evening else G.Day
end

-- the right hello for this player, now: a line-matrix moment (nil = today's pool only), its options, and today's pool
-- as the fallback. Order (the line matrix spec): saw you fight, your outfit, you're hurt, you're transformed, your race,
-- their clique, met before, night, time of day.
local function greeting(S, Rec): (string?, { [string]: any }?, { string })
	local C = ctx()
	local Pl = Rec and Rec.Player
	local M = memo(S, Pl)
	local G = Lines.Greet
	if os.clock() - (M.Fought or -1e9) < 300 then
		return `Greet`, { Attitude = if Talk.Attitude(S, Pl) == `Hostile` then `Hostile` else `Wary` }, G.Wary
	end
	local Ch = Pl and Pl.Character
	if Pl and os.clock() - (M.Outfit or -1e9) > 600 then
		local Ok, Verdict, Piece = pcall(Talk.Outfit, S, Pl)
		if Ok and Verdict and math.random() < (if S.Clique then 0.35 else 0.15) then
			M.Outfit = os.clock()
			return `Outfit`, { Sub = Verdict; Piece = Piece }, daily(C)
		end
	end
	local Hum = Ch and Ch:FindFirstChildWhichIsA(`Humanoid`)
	if Hum and Hum.MaxHealth > 0 and Hum.Health / Hum.MaxHealth < 0.35 and math.random() < 0.5 then
		return `Hurt`, nil, daily(C)
	end
	if Ch and Appearance.FormOf(Ch) then return `Transformed`, nil, Lines.ByNature(S, Lines.Monster, `Brave`) end
	local Race = Pl and Pl:GetAttribute(`Race`)
	if Race and math.random() < 0.3 then return `Race`, { Sub = Race }, G.Race[Race] or daily(C) end
	local Def = S.Clique and CliqueConfig.Defs[S.Clique]
	if Def and math.random() < 0.6 then
		local Tier = Pl and Pl:GetAttribute(`CliqueTier_{S.Clique}`)
		return `Greet`, nil, (Def.Reactions and Tier and Def.Reactions[Tier]) or daily(C)
	end
	if (M.Met or 0) >= 4 and math.random() < 0.6 then return nil, nil, G.Often end
	if (M.Met or 0) >= 1 and math.random() < 0.7 then return nil, nil, G.Again end
	if C.Night then
		if C.Moon == `Full` and math.random() < 0.6 then return `FullMoon`, nil, G.FullMoon end
		if C.Moon == `New` and math.random() < 0.4 then return nil, nil, G.NewMoon end
		return `Night`, nil, G.Night
	end
	return nil, nil, daily(C)
end

local function greet(S, Rec): boolean
	local Pl = Rec and Rec.Player
	local M = memo(S, Pl)
	if os.clock() - (M.Greeted or -1e9) < 60 then return false end
	local Moment, Opts, Pool = greeting(S, Rec)
	local Said = if Moment then sayMatrix(S, Moment, Pl, Opts, 6, Pool) else say(S, Pool, 6)
	if Said then
		M.Greeted = os.clock()
		M.Met = (M.Met or 0) + 1
		return true
	end
	return false
end
```

- [ ] **Step 5: Danger, Gawk, MakeWay, Space**

In `React.Danger`, replace `	say(S, Pool, 8)` (the line right after the `local Pool = ...` expression) with:

```lua
	local Who = T.From and T.From.Player
	local Moment = if T.Kind == `Monster` then `Transformed` elseif T.Kind == `Fight` then `Flee` else nil
	if not (Moment and Who and sayMatrix(S, Moment, Who, nil, 8, nil)) then say(S, Pool, 8) end
```

In `React.Gawk`, replace

```lua
		say(S, if T.Heard and math.random() < 0.5 then Lines.Heard.Fight else Lines.ByNature(S, Lines.Gawk, `Brave`), 10)
	elseif math.random() < 0.08 then
		say(S, Lines.ByNature(S, Lines.Gawk, `Brave`), 9)
```

with

```lua
		if T.Heard and math.random() < 0.5 then
			say(S, Lines.Heard.Fight, 10)
		else
			sayMatrix(S, `FightSeen`, T.From and T.From.Player, nil, 10, Lines.ByNature(S, Lines.Gawk, `Brave`))
		end
	elseif math.random() < 0.08 then
		sayMatrix(S, `FightSeen`, T.From and T.From.Player, nil, 9, Lines.ByNature(S, Lines.Gawk, `Brave`))
```

In `React.MakeWay`, replace

```lua
	if math.random() < 0.6 then say(S, if (Rec.Speed or 0) > 18 then Lines.Sprint else Lines.MakeWay, 10) end
```

with

```lua
	if math.random() < 0.6 then
		if (Rec.Speed or 0) > 18 then say(S, Lines.Sprint, 10) else sayMatrix(S, `Bump`, Rec.Player, nil, 10, Lines.MakeWay) end
	end
```

In `React.Space`, replace

```lua
	say(S, Lines.ByNature(S, Lines.Space, `Social`), 10)
```

with

```lua
	sayMatrix(S, `Crowded`, Rec.Player, nil, 10, Lines.ByNature(S, Lines.Space, `Social`))
```

- [ ] **Step 6: The shove hook in Nudges**

1. In `tools/npc-nudges/Nudges.luau`, confirm `local Nudges = {}` is declared before `local function shove`.
2. In `shove`, replace

```lua
	if R and S.Model then lookAt(S, R.Position + Vector3.new(0, 1.5, 0), 1.4) end
```

with

```lua
	if R and S.Model then lookAt(S, R.Position + Vector3.new(0, 1.5, 0), 1.4) end
	if Nudges.OnShove then task.spawn(Nudges.OnShove, S, Rec) end -- (line matrix) the brain's "Shoved" line
```

3. Directly above `-- Brain.OnBump: true when the nudge handled it`, add:

```lua
-- set by the brain (StudentBrain): called once a shoved student has turned to look back, to say their line
Nudges.OnShove = nil :: ((any, any) -> ())?
```

- [ ] **Step 7: Install both and check they load**

1. Install with `install.py` (Script class for the brain):
   - `install.py tools/npc-nudges/Nudges.luau ServerScriptService.Services.AI.StudentBrain.Nudges`
   - `install.py tools/ct-npc-1862/StudentBrain.luau ServerScriptService.Services.AI.StudentBrain ModuleScript`

   StudentBrain is a ModuleScript. The snippet refuses if the class doesn't match.

2. Check that both modules load, by requiring clones:

```lua
local SSS = game:GetService("ServerScriptService")
local Clone = SSS.Services.AI.StudentBrain:Clone()
Clone.Parent = game:GetService("ServerStorage")
local Ok, B = pcall(require, Clone)
Clone:Destroy()
return if Ok and type(B) == "table" and B.Init then "LOADS" else "ERROR: " .. tostring(B)
```

Expected: `LOADS`.

Speech is checked live in Task 8. Until the clique modules exist, every clique moment falls back to Generic, so
students already speak through the matrix.

- [ ] **Step 8: Commit**

```bash
git -c user.name=Rello commit -m "Line matrix: students greet, react and get shoved through StudentBrain.Talk (today's pools as fallback)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- tools/ct-npc-1862/StudentBrain.luau tools/npc-nudges/Nudges.luau
```

---

### Task 6: Each clique's lines (one sub-task per clique, 6a to 6h)

**Files (each sub-task):**
- Create: `tools/line-matrix/CliqueTalk/<Clique>.luau`.
- Studio: `ReplicatedStorage.Config.CliqueTalk.<Clique>`.

**Interfaces:**
- Consumes the module format from Task 1 and the placeholders in Global Constraints.

**Every clique module must:**
- give **all 13 moments**;
- give **`Race`** with all 6 races and **`Outfit`** with all 4 verdicts;
- give **`Greet`** its own pool for each of the 5 attitudes, with **no `Any`** (coverage enforces this);
- in the other moments, split by attitude wherever the attitude changes what they'd say. At least split
  `Outfit.FullLook`, `Outfit.RivalLook`, `Hurt` and `DressCode` into Hostile and Wary against Friendly and Respected,
  and use `Any` only where the attitude makes no difference (`Bump` and `Shoved` often);
- keep the voice already set by the clique's `Lines` and `Reactions` in `Config.Cliques`. Read those first;
- write every line that holds a placeholder in **double quotes** (`"Hey, {Name}!"`), never backticks: in Luau a
  backtick string interpolates `{Name}` at load time and stores `Hey, nil!`. Lines without placeholders may use either.

**Steps (the same for each clique):**

- [ ] **Step 1:** Run `tests/coverage.luau` with `ONLY = "<Clique>"`. Expected: `FAIL ... <Clique>: module missing`.
- [ ] **Step 2:** Write `tools/line-matrix/CliqueTalk/<Clique>.luau`, following the voice notes below. It starts with
  `-- CliqueTalk.<Clique>: <one-line voice summary> (the line matrix)` and returns a table in Generic's shape.
- [ ] **Step 3:** Install it with
  `install.py tools/line-matrix/CliqueTalk/<Clique>.luau ReplicatedStorage.Config.CliqueTalk.<Clique>`.
- [ ] **Step 4:** Run coverage with `ONLY = "<Clique>"`. Expected: `PASS: 105 cells, N lines`. Fix and reinstall until
  it passes.
- [ ] **Step 5:** Commit:

```bash
git -c user.name=Rello add tools/line-matrix/CliqueTalk/<Clique>.luau
git -c user.name=Rello commit -m "Line matrix: <Clique> lines" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- tools/line-matrix/CliqueTalk/<Clique>.luau
```

**Voice notes.** The example lines set the tone; write new ones in the same voice.

- **6a, Vigil** (scholars of the school's records, by lamplight; rival: the Court).
  - **Voice:** records, lamps, the charter, missing pages, being watched.
  - **Hostile:** cold and bureaucratic ("We have a file on you now.").
  - **Respected:** warm and conspiratorial ("Keeper. The lamps burn for you.").
  - **Outfit:**
    - likes: pocket watch, candle lantern, scroll tube, scholar's coat;
    - mocks: Court frills, "a fascinator? In the stacks?";
    - RivalLook: Court crimson.
  - **Transformed:** they take notes ("Hold still. I'm writing this down.").
  - **DressCode:** "The Archive is for the Vigil. Dress like it."
- **6b, Court** (old money and manners, the night belongs to them; rival: the Vigil).
  - **Voice:** money, manners, "darling", "how common".
  - **Hostile:** icy ("The Court has a long memory.").
  - **Respected:** gracious ("Do sit. You're one of us tonight.").
  - **Outfit:** they are the fashion critics, so the remarks are the sharpest. Mocks: lamplighter's coat, a messenger
    bag ("Did you walk here?").
  - **Night and FullMoon:** they relish the dark.
  - **DressCode:** "Crimson, darling. Or the door."
- **6c, Athletes** (the varsity Ravens; rival: Ink).
  - **Voice:** sport, coach, laps, hydration, team.
  - **Hostile:** "Bench warmer. Move."
  - **Respected:** "Team's here! {Name}!"
  - **Outfit:**
    - likes: varsity jacket;
    - mocks: grimoire ("Is that homework? On purpose?"), violin case, ruff.
  - **FightSeen:** they commentate it like a match.
  - **Hurt:** "Walk it off."
  - **DressCode:** "Gym's for the team. Get a jacket."
- **6d, Delinquents** (the Back Lot, turf and threats; rival: Ordinary).
  - **Voice:** turf, "keep walking", the hall monitor, shoes.
  - **Hostile:** the threat stays implied, never gore ("Nice teeth. Keep 'em.").
  - **Respected:** gruff respect ("Lot's yours too, {Name}.").
  - **Outfit:**
    - likes: the long coat, the grille mask;
    - mocks: prefect sash, bow tie, umbrella.
  - **Bump and Shoved:** they push back ("You lost?").
  - **DressCode:** "This lot's ours. You don't look it."
- **6e, Pack** (the Den, wolves at heart; rival: the Choir).
  - **Voice:** the moon, scent, "first-year", fear.
  - **Hostile:** predatory but clean ("Smell that? Nerves.").
  - **Respected:** the pack welcome ("Run with us tonight.").
  - **FullMoon:** their best lines.
  - **Race.Werewolf:** kinship.
  - **Outfit:**
    - likes: fang necklace, torn fur, wolf mask;
    - mocks: choir collar, wax saint mask.
  - **DressCode:** "Den smells like us. You don't."
- **6f, Ordinary** (nervous common sense, the Commons; rival: Delinquents).
  - **Voice:** keep your head down, go home before dark, strength in numbers, rumours about the moon.
  - **Hostile:** nervous avoidance, not threats ("Please just go away.").
  - **Respected:** grateful ("You stood up for us. Thanks.").
  - **Outfit:**
    - likes: umbrella, oilskin, cardigan coat;
    - mocks: bone mask, scythe pendant ("That's... a lot.").
  - **Flee and Transformed:** their strongest lines.
  - **DressCode:** "Commons is for... well, us. Sorry."
- **6g, Choir** (the Chapel, hymns and blessing; rival: the Pack).
  - **Voice:** blessings, candles, practice at dusk, "something unholy".
  - **Hostile:** pious contempt ("I'll pray for you. Briefly.").
  - **Respected:** a benediction ("The candles burn brighter for you.").
  - **Outfit:**
    - likes: choir collar, falling ruff, wax saint mask;
    - mocks: wolf mask, fang necklace, witch hat.
  - **Race.Priest:** kinship.
  - **Transformed:** "Begone" in the warding sense, kept funny and never cruel.
  - **DressCode:** "The chapel asks for proper dress."
- **6h, Ink** (the Ink Studio, art and pranks; rival: the Athletes).
  - **Voice:** murals, brushes, pranks, "art is a prank that took longer".
  - **Hostile:** a prankster's threat ("Sleep with one eye open.").
  - **Respected:** collaborator ("We're painting the gym. You in?").
  - **Outfit:**
    - likes: fox, moth and domino masks, the batwing backpack;
    - mocks: varsity jacket, prefect sash, school tie.
  - **FightSeen:** "Hold that pose."
  - **DressCode:** "Studio's for the Ink. You're very... clean."

After 6h, run coverage with `ONLY = nil`. Expected: `PASS: 945 cells, N lines` (9 modules × 105).

---

### Task 7: Dress codes

**Files:**
- Studio changes:
  - `ServerScriptService.Services.Social.Cliques` (`Dressed`);
  - `ServerScriptService.Services.Quests.Quests` (`CanStart`, `Offers`);
  - `ServerScriptService.Services.Social.Dialogue` (`ctx`);
  - `ServerStorage.Dialogue.QuestChoices`;
  - `ServerScriptService.Services.Social.Hangouts` (`OnStudy`).
- Modify: `tools/ct-npc-1862/StudentBrain.luau` (the hangout watcher).
- Create: `tools/line-matrix/patches/DressCode.json`, holding every `multi_edit` pair from this task.

**Interfaces:**
- Consumes `Cliques.WearsTop` and `Cliques.ParseWear` (Task 4), `Talk.Line` (Task 2) and `sayMatrix` (Task 5).
- Produces:
  - `Cliques.Dressed(P: Player, Id: string) -> boolean` (the service, `Social.Cliques`).
  - `Quests.CanStart` returns `false, "DressCode"`.
  - `Quests.Offers(Player, NpcId, WithDressCode: boolean?)`: entries of `Kind = "DressCode"`, only when asked for.
  - `ctx.DressLine(Clique) -> string?` in dialogue.

- [ ] **Step 1: See which quests the gate covers**

Run in Edit:

```lua
local Q = require(game.ReplicatedStorage.Config.Quests)
local Out = {}
for Id, Def in Q.Quests do
	local C = Def.Clique or (Def.Requires and Def.Requires.Clique and Def.Requires.Clique.Id)
	if C and not (Def.Dare or Def.Job or Def.Showdown) then table.insert(Out, `{Id} ({C}, giver {Def.Giver})`) end
end
table.sort(Out)
return #Out .. " gated:\n" .. table.concat(Out, "\n")
```

Expected: the cliques' leader quests (two per leader, opened at Neutral and Friendly by `Cliques.QuestOpen`).

If the config module isn't at `ReplicatedStorage.Config.Quests`, use the path `Quests.Quests` requires as `Config`.

- [ ] **Step 2: `Cliques.Dressed`**

`multi_edit` on `game.ServerScriptService.Services.Social.Cliques`:

old_string:
```lua
function Shared.Tier(Value: number): string
	return Config.Tier(Value)
end
```

new_string:
```lua
function Shared.Tier(Value: number): string
	return Config.Tier(Value)
end

-- (line matrix) the dress code: a clique deals with you in person if you wear one of its tops, you're Friendly or
-- better with it, or you're a member. Dares by phone and members' jobs never ask.
function Shared.Dressed(P: Player, Id: string): boolean
	if not Config.Defs[Id] then return true end
	local C = Shared.Get(P)
	local Tier = C and Config.Tier(C[Id] or 0)
	if Tier == `Friendly` or Tier == `Respected` then return true end
	local M = svc(`Social.CliqueMembership`)
	if M and M.IsMember and M.IsMember(P, Id) then return true end
	local W = P.Character and Config.ParseWear(P.Character:GetAttribute(`NHWear`))
	return W ~= nil and Config.WearsTop(Id, W.Top)
end
```

- [ ] **Step 3: The gate in `Quests.CanStart` and `Offers`**

`multi_edit` on `game.ServerScriptService.Services.Quests.Quests`.

**Edit 1 (`CanStart`):** insert the check after the `Requires` block, so Locked reasons win over it.

old_string:
```lua
		if Req.Clique then
			local Ok, C = pcall(function() return Cliques().Get(Player) end)
			if not (Ok and C) or (C[Req.Clique.Id] or 0) < (Req.Clique.Min or 0) then return false, `Locked` end
		end
	end
```

new_string:
```lua
		if Req.Clique then
			local Ok, C = pcall(function() return Cliques().Get(Player) end)
			if not (Ok and C) or (C[Req.Clique.Id] or 0) < (Req.Clique.Min or 0) then return false, `Locked` end
		end
	end
	-- (line matrix) a clique's in-person quests wait until you're dressed the part, liked, or a member
	local DressFor = Def.Clique or (Req and Req.Clique and Req.Clique.Id)
	if DressFor and not (Def.Dare or Def.Job or Def.Showdown) then
		local Ok, Dressed = pcall(function() return Cliques().Dressed(Player, DressFor) end)
		if Ok and Dressed == false then return false, `DressCode` end
	end
```

**Edit 2 (the `Offers` signature):**

old_string: `function Shared.Offers(Player: Player, NpcId: string): { { Id: string, Kind: string } }`

new_string: `function Shared.Offers(Player: Player, NpcId: string, WithDressCode: boolean?): { { Id: string, Kind: string } }`

**Edit 3 (the `Offers` body):**

old_string:
```lua
			local Ok = Shared.CanStart(Player, Id)
			if Ok then table.insert(List, { Id = Id; Kind = if Q.Failed[Id] then `Retry` else `Offer` }) end
```

new_string:
```lua
			local Ok, Why = Shared.CanStart(Player, Id)
			if Ok then
				table.insert(List, { Id = Id; Kind = if Q.Failed[Id] then `Retry` else `Offer` })
			elseif WithDressCode and Why == `DressCode` then -- (line matrix) the dialogue turns you away with a line
				table.insert(List, { Id = Id; Kind = `DressCode` })
			end
```

`Cliques()` is the existing lazy getter in `Quests`, and the old `Req.Clique` block already uses it. If the live code
names it differently, match that.

- [ ] **Step 4: Dialogue says why**

`multi_edit` on `game.ServerScriptService.Services.Social.Dialogue`:

old_string:
```lua
	function ctx.Offers() return Quests.Offers(Player, NpcId) end
```

new_string:
```lua
	function ctx.Offers() return Quests.Offers(Player, NpcId, true) end
	function ctx.DressLine(Clique: string): string? -- (line matrix) a clique giver turns you away for your clothes
		local Ok, Line = pcall(function()
			return require(game:GetService(`ServerScriptService`).Services.AI.StudentBrain.Talk).Line(Clique, `DressCode`, Player)
		end)
		return if Ok then Line else nil
	end
```

`multi_edit` on `game.ServerStorage.Dialogue.QuestChoices`.

**Edit 1:**

old_string:
```lua
	Nodes.Q_Status = {
```

new_string:
```lua
	Nodes.Q_DressCode = { -- (line matrix) the giver won't deal until you're dressed the part, liked, or a member
		Text = function(ctx)
			local D = Def(ctx)
			return (D.Clique and ctx.DressLine and ctx.DressLine(D.Clique)) or `Come back dressed the part.`
		end;
		Choices = { { Text = `Fair enough.`; Next = Back }, { Text = `Bye.` } };
	}
	Nodes.Q_Status = {
```

**Edit 2:**

old_string:
```lua
					return if Offer.Kind == `Active` then `Q_Status` else `Q_Offer`
```

new_string:
```lua
					return if Offer.Kind == `Active` then `Q_Status` elseif Offer.Kind == `DressCode` then `Q_DressCode` else `Q_Offer`
```

If a gated quest's `Def.Clique` is nil (it only has `Requires.Clique`), change `D.Clique` in `Q_DressCode` to
`(D.Clique or (D.Requires and D.Requires.Clique and D.Requires.Clique.Id))`.

- [ ] **Step 5: Night Study**

`multi_edit` on `game.ServerScriptService.Services.Social.Hangouts`:

old_string:
```lua
		Notifications.Notify(Player, { Title = `Night Study is after hours`; Text = `You should be in class right now.`; Kind = `Info`; Duration = 3 })
		return false
	end
```

new_string:
```lua
		Notifications.Notify(Player, { Title = `Night Study is after hours`; Text = `You should be in class right now.`; Kind = `Info`; Duration = 3 })
		return false
	end

	-- (line matrix) the dress code: the Vigil study with those in its colours, its friends and its members
	local OkC, Cl = pcall(require, ServerScriptService.Services.Social.Cliques)
	if OkC and Cl.Dressed and not Cl.Dressed(Player, `Vigil`) then
		local OkT, Line = pcall(function() return require(ServerScriptService.Services.AI.StudentBrain.Talk).Line(`Vigil`, `DressCode`, Player) end)
		Notifications.Notify(Player, { Title = `Not dressed for the Archive`; Text = (OkT and Line) or `Come back in the Vigil's colours.`; Kind = `Info`; Duration = 4 })
		return false
	end
```

- [ ] **Step 6: The line on walking into a hangout (brain)**

In `tools/ct-npc-1862/StudentBrain.luau`, add `local Cliques = require(ServerScriptService.Services.Social.Cliques)`
after the `Appearance` require. Then insert directly above `function Brain.Init(H)`:

```lua
---| dress codes (line matrix) |---

-- walk into a clique's hangout out of its colours and the nearest of its students (30 studs) says so: once a visit,
-- at most every 120 s for each player
local Visits = {} :: { [Player]: { In: string?, Told: number } }

local function hangoutOf(Root: BasePart): string?
	local Folder = workspace:FindFirstChild(`Regions`)
	if not Folder then return nil end
	for Id, Def in CliqueConfig.Defs do
		local Box = Def.Hangout and Folder:FindFirstChild(Def.Hangout)
		if Box and Box:IsA(`BasePart`) then
			local L = Box.CFrame:PointToObjectSpace(Root.Position)
			local H = Box.Size / 2 + Vector3.new(0, 6, 0)
			if math.abs(L.X) <= H.X and math.abs(L.Y) <= H.Y and math.abs(L.Z) <= H.Z then return Id end
		end
	end
	return nil
end

local function dressWatch()
	while true do
		task.wait(1)
		for _, P in Players:GetPlayers() do
			local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
			local V = Visits[P] or { Told = -1e9 }
			Visits[P] = V
			local Id = Root and hangoutOf(Root)
			if Id == V.In then continue end
			V.In = Id
			if not (Id and Root) or os.clock() - V.Told < 120 then continue end
			local Ok, Dressed = pcall(Cliques.Dressed, P, Id)
			if not Ok or Dressed then continue end
			local Best, BestD = nil, 30
			for _, S in (Host and Host.Students and Host.Students()) or {} do
				if S.Clique == Id and S.Root and S.Model and not S.Reacting then
					local D = (S.Root.Position - Root.Position).Magnitude
					if D < BestD then Best, BestD = S, D end
				end
			end
			if Best and sayMatrix(Best, `DressCode`, P, nil, 0, nil) then
				V.Told = os.clock()
				lookAt(Best, Root.Position + Vector3.new(0, 1.5, 0), 2)
			end
		end
		for P in Visits do
			if not P.Parent then Visits[P] = nil end
		end
	end
end
```

In `Brain.Init`, after `Senses.Init()`, add:

```lua
	task.spawn(dressWatch) -- (line matrix) hangout dress codes
```

- [ ] **Step 7: Install and check it loads**

1. Install `StudentBrain.luau` with `install.py`.
2. Re-run the load check from Task 5 Step 7. Expected: `LOADS`.
3. Check that each patched service loads, by requiring a clone (Edit):

```lua
local Out = {}
for _, Path in { "Services.Social.Cliques", "Services.Quests.Quests", "Services.Social.Hangouts", "Services.Social.Dialogue" } do
	local Node = game:GetService("ServerScriptService")
	for Part in Path:gmatch("[^%.]+") do Node = Node[Part] end
	local C = Node:Clone()
	C.Parent = Node.Parent
	local Ok, M = pcall(require, C)
	C:Destroy()
	table.insert(Out, Path .. ": " .. (if Ok then "LOADS" else "ERROR " .. tostring(M)))
end
return table.concat(Out, "\n")
```

Expected: four `LOADS`. Some services may wait for remotes or profiles when required in Edit. If one hangs or warns
about something other than syntax, record it, and rely on Task 8 for that service.

- [ ] **Step 8: Commit**

```bash
git -c user.name=Rello add tools/line-matrix/patches/DressCode.json
git -c user.name=Rello commit -m "Line matrix: hangout dress codes (Cliques.Dressed; leader quests, Night Study, walking in)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- tools/line-matrix/patches/DressCode.json tools/ct-npc-1862/StudentBrain.luau
```

---

### Task 8: Play test on slot 4 "Testy"

**Files:**
- Create: `tools/line-matrix/PLAYTEST.md`, recording what was run, what was seen, and anything left untested.

- [ ] **Step 1: Set up**

1. In Edit, set `SlotCount = 4; -- NH TEMP slot test: set back to 3` in `Config.MainMenu`.
2. Start Play.
3. Set `NHTestNoMenuKeys` on the player and load slot 4 "Testy" only.

- [ ] **Step 2: Check `NHWear` is stamped**

Server datamodel: `game.Players:GetPlayers()[1].Character:GetAttribute("NHWear")`.
Expected: Testy's real top, bottoms and accessories.

If Task 3's dummy test couldn't run in Edit mode, this check stands in for it.

- [ ] **Step 3: Outfit remarks**

1. Server-side, dress Testy in the Athletes look: `Appearance.ApplyTo` with Testy's sanitized profile look, with
   `Uniform = "varsity-jacket"` and `Bottoms = "striped-joggers"`. Do this as a test only; don't save it to the profile.
2. Walk Testy near an Athletes student and an Ink student (`Config.Cliques.Students`).
3. Set `S.Memory[UserId].Outfit = -1e9` through TestBridge or a direct server snippet, so the 600 s cooldown doesn't
   block the test.
4. Read the students' `NHSay` attributes.

Expected:
- an Athletes `Outfit.FullLook` line;
- an Ink `Outfit.RivalLook` line.

Repeat with the Ink look, and with `grimoire-chained` in front of an Athletes student (a `Mocks` line).

- [ ] **Step 4: Attitude tone**

Use TestBridge `AddStanding` (or `Commands.AddStanding`) to set Testy's Athletes standing to -50, -20, 0, 30 and 70.
At each value, trigger a greeting and read `NHSay`.

Expected: a line from the matching `Greet` attitude pool in `CliqueTalk.Athletes`.

- [ ] **Step 5: Dress codes**

1. Set Vigil standing to 0 (Neutral), wear no Vigil top, and run TestBridge `Hangouts.StudyForTests(Player)`.
   Expected: refused, with a Vigil `DressCode` notification.
2. Put on `vigil-vest` and run it again. Expected: Night Study starts.
3. Talk to a leader at Neutral standing, out of their colours.
   Expected: a `[Quest]` choice that leads to their `DressCode` line, not the offer. Dressed, the offer appears.
4. Walk into the Gymnasium region out of the Athletes look with an Athletes student within 30 studs.
   Expected: one `DressCode` line. Walk out and back in within 120 s. Expected: no second line.

- [ ] **Step 6: Bumps, crowding and shoves; no regressions**

1. Brush past a clique student (`Bump`), stand on top of one (`Crowded`), and sprint into one from behind with room
   ahead (`Shoved`, which fires when they look back).
2. Check a clique-less ambient student still greets and mutters as before.
3. Check the server output has no new errors (`get_console_output`).

- [ ] **Step 7: Tidy up and record**

1. Stop Play.
2. Set `SlotCount` back to 3 and clear `NHTestNoMenuKeys`.
3. Write `tools/line-matrix/PLAYTEST.md`: each check, what was seen (quote the `NHSay` lines), and anything left
   untested (for example a second player).
4. Commit:

```bash
git -c user.name=Rello add tools/line-matrix/PLAYTEST.md
git -c user.name=Rello commit -m "Line matrix: play test on slot 4 (Testy)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- tools/line-matrix/PLAYTEST.md
```

---

### Task 9: Docs, CHANGELOG, Discord post, vault

**Files:**
- Create:
  - `docs/Line-Matrix.md`
  - `updates/discord/game-updates/<YYYY-MM-DD>-line-matrix.md`
- Modify: `CHANGELOG.md`.
- Vault:
  - `E:\Download\Obsidian (VAULT)\Rello Memory\Nightmare Highschool\Docs\Line-Matrix.md`;
  - a link in the home note `Nightmare Highschool.md`;
  - `Memory/Next Up.md`.

- [ ] **Step 1: Write `docs/Line-Matrix.md`**

It covers:
- what the matrix is;
- the module format;
- the moments table: when each fires and its fallback;
- how attitude is worked out;
- how to add a line, a moment or a clique;
- how to change a clique's taste;
- `NHWear`;
- the dress code: where it applies and who passes;
- how to run the three tests and the coverage test;
- the writing rules.

- [ ] **Step 2: CHANGELOG and Discord post**

**CHANGELOG:** add `## [<next minor>] - <date>: Students talk like their clique, notice your clothes, and keep dress
codes` at the top, in the style of the existing entries: what players notice first, then the technical notes and
files.

**Discord post:** follow the shape of `updates/discord/game-updates/2026-11-04-clique-greetings.md`. It's short and
in players' words.

- [ ] **Step 3: Mirror to the vault**

1. Copy `docs/Line-Matrix.md` to the vault's `Docs/`.
2. Add a row for it in the home note's docs table.
3. In `Memory/Next Up.md`, mark "Line matrix + outfits (Combat Test)" done and add "Port the line matrix to the Map
   (needs Map cliques and standing)".

- [ ] **Step 4: Commit and push**

```bash
git -c user.name=Rello add docs/Line-Matrix.md updates/discord/game-updates/<YYYY-MM-DD>-line-matrix.md
git -c user.name=Rello commit -m "<next minor>: line matrix + outfits: clique talk by attitude and moment, outfit remarks, hangout dress codes" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- docs/Line-Matrix.md updates/discord/game-updates/<YYYY-MM-DD>-line-matrix.md CHANGELOG.md
git push
```

- [ ] **Step 5: Remind the owner to save NH Combat Test in Studio.**

---

## Spec coverage

| Spec section | Task |
|---|---|
| 1. Lines (`Config.CliqueTalk`, moments, placeholders, writing rules) | 1, 6 |
| 2. `Talk.Attitude`, `Talk.Pick`, fallback order | 2 |
| 2. Brain use: greeting order, Nudges (Bump, Crowded, Shoved), Gawk, Flee; Mutter unchanged | 5 |
| 3. `NHWear` | 3 |
| 3. Taste and `Talk.Outfit` verdicts; clique-less students at 15% | 4, 5 |
| 4. `Cliques.Dressed`; quests and Dialogue, Night Study, walking in | 7 |
| Failure handling: fallbacks, `pcall`, unfillable lines skipped, stand-ins | 2, 5 |
| Testing 1 to 4 | 1, 2, 3, 4, 8 |
| Files and docs | 9 |
