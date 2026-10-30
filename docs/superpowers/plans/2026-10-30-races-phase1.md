# Races Phase 1: Roster, Passives, Palettes, Bloodline Tab (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** six server-rolled races with balanced, tier-scaled passives that really change combat and EXP, race skin palettes, and a Bloodline tab in the creator.

**Architecture:**
- `ReplicatedStorage.Lineage` stays the single race config. It gains the roster, families, tiers, passives, palettes and two pure helpers: `Passives` and `DamageScale`.
- `Services.Player.Progression` adds the race passive to the effects it already merges and applies.
- `Downed.ApplyDamage` gets one line calling `Lineage.DamageScale`.
- The client gets `Controllers.Gui.Bloodline`, a content builder that the Identity panel shows as a new first tab.

**Tech stack:**
- Roblox Luau (ModuleLoader: `Services.*` / `Controllers.*` with `OnStart`) and the NH UI kit (`ReplicatedStorage.UI.Components`).
- Studio MCP. Local sources live in the session folder's `Studio/src`, installed with `Studio/install.py`. Pure tests run with `Studio/rd.sh`.

**Spec:** `docs/superpowers/specs/2026-10-30-races-design.md` (sections 1, 2, 3 (palettes only) and 6).

## Global Constraints
- Only touch the place **NH Combat Test** (Studio id `ffaef9d8-31a8-498c-bded-1ed7d5490e48`). Never production, Tutorial or Rensei.
- **Saving:** only through ProfileService `PlayerData` (`Data.UpdateState`). Players never set Race. Only the server writes `Lineage`.
- **Shared Studio:** announce before Play to the sessions `local_49983083-…` (UI kit) and `local_cfab9213-…` (UI audit). The Edit datamodel is unavailable while anyone is in Play, so retry installs with `--wait`.
- **Ownership:** `ReplicatedStorage.Lineage`, `ServerScriptService.NHLineage` and the Wardrobe Lineage tab were handed over by the UI kit session. `UI.Appearance` and the skin picker stay **theirs**: we only add `Palette` data, and they do the clamp.
- **UI standard (UI Audit 1.0):** text is at least 18 px design size, and text contrast is at least 3:1 (notes use `C.TextDim:Lerp(C.Text, 0.45)`).
- **Original designs only.** Gothic-castle tone. No names or imagery from other games.
- **Balance numbers come verbatim from spec §2.** Per-sub boosts: base ×1.0, second sub ×1.15, third ×1.3. Boosts apply to **strengths only**, never to drawbacks.
- **Commits:** repo `E:\Nightmare-Highschool`, git identity Rello, end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never push game source. Docs, CHANGELOG and a Discord post (<2000 chars) go in at the end.

## File map
| File (session `Studio/`) | Installs to | Job |
|---|---|---|
| `src/Lineage.luau` (new local copy of the live module) | `ReplicatedStorage.Lineage` (ModuleScript) | roster, families, tiers, passives, palettes, `Passives`, `PassiveEffects`, `TierName`, `IsFullMoon`, `DamageScale` |
| `src/ConfigProgression.luau` | `ReplicatedStorage.Config.Progression` | new effect keys, labels, `Describe` for HP/s regen |
| `src/Progression.luau` | `ServerScriptService.Services.Player.Progression` | race passive merged into effects and applied; heal hooks; `Sheet.Race` |
| (Studio edit) `Downed` | `ServerScriptService.Services.Features.Downed` | one-line race damage scale |
| (Studio edit) `TestBridge` | `ServerScriptService.Services.Studio.TestBridge` | `SetRace`, `RaceDamage` test commands |
| `src/Bloodline.luau` (new) | `StarterPlayer.StarterPlayerScripts.Controllers.Gui.Bloodline` | builds the Bloodline tab content |
| `src/IdentityClient.luau` | `…Controllers.Gui.Identity` | a third tab, `Bloodline`, first in order |
| (Studio edit) `MainMenu` | `…Controllers.Gui.MainMenu` | nav: Look / Bloodline / Name & Clan / Spin Shop |
| (Studio edit) `Wardrobe` | `…Controllers.Gui.Wardrobe` | the Lineage tab points to Bloodline |
| `src/ProgressClient.luau` | `…Controllers.Gui.Progress` | the Record shows the race passive and has a Bloodline button |
| `tests/lineage_test.luau` (new) | run only | pure checks of Lineage and Config.Progression |

---

### Task 1: Lineage roster, families, tiers, passives, palettes

**Files:**
- Create: `Studio/src/Lineage.luau`, copied from `Studio/live/ReplicatedStorage.Lineage.luau` (the dump of the live module) and then edited.
- Create: `Studio/tests/lineage_test.luau`.

**Interfaces (produces):**
- `Lineage.Races[i]`: `{ Id, Name, Weight, Color, Text, Family, Tiers = {string,string,string}, Palette = {Color3}?, Passive = { Name, Text, Strengths = { [key] = {t1,t2,t3} }, Drawbacks = { [key] = number }, DrawbackText }, Subs = { { Id, Name, Weight, Rarity, Boost } } }`
- `Lineage.Family(raceId) -> "Mortal"|"Undead"|"Cursed"|nil`
- `Lineage.IsUndead(raceId) -> bool`
- `Lineage.IsMonster(raceId) -> bool`
- `Lineage.Passives(raceId, subId, tier) -> strengths, drawbacks, boost`
- `Lineage.PassiveEffects(raceId, subId, tier) -> effects` (strengths + drawbacks)
- `Lineage.TierName(raceId, tier) -> string`
- `Lineage.FullMoonEvery = 4`
- `Lineage.IsFullMoon(day, hour) -> bool`
- `Lineage.Palette(raceId) -> {Color3}?`

- [ ] **Step 1: Write the failing test** `Studio/tests/lineage_test.luau`:

```lua
-- Pure checks for ReplicatedStorage.Lineage + Config.Progression. Run: Studio/rd.sh tests/lineage_test.luau
local L = require(game.ReplicatedStorage.Lineage)
local fails, n = {}, 0
local function eq(name, got, want, tol)
	n += 1
	local ok = if type(want) == "number" then type(got) == "number" and math.abs(got - want) <= (tol or 1e-6) else got == want
	if not ok then table.insert(fails, string.format("%s: got %s want %s", name, tostring(got), tostring(want))) end
end
-- roster and odds
local odds = {}
for _, r in L.Odds() do odds[r.Id] = r.Chance end
eq("Human odds", odds.Human, 40, 0.01) eq("Priest odds", odds.Priest, 25, 0.01) eq("Vampire odds", odds.Vampire, 15, 0.01)
eq("Werewolf odds", odds.Werewolf, 10, 0.01) eq("Ghoul odds", odds.Ghoul, 6, 0.01) eq("Wraith odds", odds.Wraith, 4, 0.01)
for _, r in L.Races do
	eq(r.Id .. " tiers", #r.Tiers, 3)
	eq(r.Id .. " has passive", r.Passive ~= nil, true)
	eq(r.Id .. " family", L.Family(r.Id) ~= nil, true)
	for i, s in r.Subs do eq(s.Id .. " boost", s.Boost, ({ 1, 1.15, 1.3 })[i]) end
end
-- families
eq("Vampire undead", L.IsUndead("Vampire"), true) eq("Werewolf not undead", L.IsUndead("Werewolf"), false)
eq("Werewolf monster", L.IsMonster("Werewolf"), true) eq("Priest not monster", L.IsMonster("Priest"), false)
eq("nil race", L.IsMonster(nil), false)
-- passives: tier scaling, sub boost on strengths only
local s, d = L.Passives("Vampire", "RoyalVamp", 3)
eq("Royal T3 night power", s.NightPower, 0.12 * 1.3) eq("Royal T3 heal on kill", s.HealOnKill, 0.08 * 1.3)
eq("Vampire day drawback unboosted", d.DamageByDay, -0.05)
local e = L.PassiveEffects("Wraith", "Wraith", 1)
eq("Wraith T1 stealth", e.Stealth, -0.10) eq("Wraith max health drawback", e.MaxHealth, -10)
local h = L.PassiveEffects("Human", "Human", 1)
eq("Human T1 no slayer bonus", h.DamageVsMonster, nil) eq("Human T1 all EXP", h.AllExp, 0.08)
eq("Human T3 slayer", L.PassiveEffects("Human", "Superhuman", 3).DamageVsMonster, 0.08 * 1.15)
eq("Ghoul T2 regen", L.PassiveEffects("Ghoul", "Ghoul", 2).LowHealthRegen, 0.1)
eq("Priest night drawback", L.PassiveEffects("Priest", "Pope", 1).NightPower, -0.05)
eq("Werewolf drawback stealth", L.PassiveEffects("Werewolf", "Alpha", 2).Stealth, 0.10)
eq("bad tier clamps", L.Passives("Vampire", "Vampire", 9).NightPower, 0.12)
eq("unknown race", next(L.PassiveEffects("Elf", nil, 1)), nil)
-- tiers, moon, palettes
eq("tier name", L.TierName("Werewolf", 2), "Moonbound") eq("tier name clamp", L.TierName("Ghoul", 0), "Starveling")
eq("full moon night day 8 at 22h", L.IsFullMoon(8, 22), true) eq("same night 3am next day", L.IsFullMoon(9, 3), true)
eq("day 8 at noon", L.IsFullMoon(8, 12), false) eq("day 9 at 22h", L.IsFullMoon(9, 22), false)
eq("vampire palette size", #L.Palette("Vampire"), 9) eq("ghoul palette size", #L.Palette("Ghoul"), 6)
eq("human palette none", L.Palette("Human"), nil)
-- sanitize keeps new races, fixes mismatched subs
local z = L.Sanitize({ Race = "Werewolf", SubRace = "Bloodmoon" }) eq("sanitize werewolf", z.SubRace, "Bloodmoon")
local y = L.Sanitize({ Race = "Ghoul", SubRace = "RoyalVamp" }) eq("sanitize mismatch", y.SubRace, "Ghoul")
return if #fails == 0 then string.format("PASS %d checks", n) else string.format("FAIL %d/%d\n%s", #fails, n, table.concat(fails, "\n"))
```

- [ ] **Step 2: Run it to verify it fails.**
  - Run: `Studio/rd.sh tests/lineage_test.luau`
  - Expected: a FAIL listing (e.g. "Human odds: got 50 want 40") or an error that `Tiers` is nil.

- [ ] **Step 3: Implement in `Studio/src/Lineage.luau`.**
  - Replace the `Lineage.Races = { … }` table (live lines 44–72) with the block below.
  - Add the helpers right after `Lineage.RaceById, Lineage.SubById, Lineage.TraitById = …` (live line 101).
  - Update the header comment: six races; Werewolf, Ghoul and Wraith come from the user's 2026-10-30 brief.

```lua
-- Weights are relative. Families: Mortal (Human, Priest), Undead (Vampire, Ghoul, Wraith), Cursed (Werewolf).
-- Passive Strengths are { Tier I, Tier II, Tier III } and are multiplied by the sub-race's Boost; Drawbacks are flat.
-- Effect keys are Config.Progression's (applied by Services.Player.Progression). Numbers are a balance PROPOSAL.
Lineage.FullMoonEvery = 4 -- every 4th in-game night is a full moon
Lineage.Races = {
	{
		Id = "Human", Name = "Human", Weight = 40, Color = rgb(214, 196, 170), Family = "Mortal",
		Text = "Ordinary blood. Nothing holds you back, and nothing holds you up.",
		Tiers = { "Townsfolk", "Hunter", "Slayer" },
		Passive = { Name = "Stubborn Will", Text = "You learn from everything, and you don't break easily.",
			Strengths = { AllExp = { 0.08, 0.10, 0.12 }, PostureGain = { -0.04, -0.06, -0.08 }, DamageVsMonster = { 0, 0, 0.08 } },
			Drawbacks = {}, DrawbackText = "No power at night, and a monster's bite can turn you." },
		Subs = {
			{ Id = "Human", Name = "Human", Weight = 90, Rarity = "Common", Boost = 1 },
			{ Id = "Superhuman", Name = "Superhuman", Weight = 10, Rarity = "Rare", Boost = 1.15 },
		},
	},
	{
		Id = "Priest", Name = "Priest", Weight = 25, Color = rgb(235, 205, 120), Family = "Mortal",
		Text = "Born to the chapel. The light answers when you call.",
		Tiers = { "Acolyte", "Exorcist", "Saint" },
		Passive = { Name = "Consecrated", Text = "The dead flinch from you.",
			Strengths = { DamageVsUndead = { 0.06, 0.09, 0.12 }, DamageTakenFromUndead = { -0.06, -0.09, -0.12 }, ClassExp = { 0.05, 0.05, 0.05 } },
			Drawbacks = { NightPower = -0.05 }, DrawbackText = "Weaker after dark." },
		Subs = {
			{ Id = "Priest", Name = "Priest", Weight = 85, Rarity = "Uncommon", Boost = 1 },
			{ Id = "GrandPriest", Name = "Grand Priest", Weight = 12, Rarity = "Epic", Boost = 1.15 },
			{ Id = "Pope", Name = "Pope", Weight = 3, Rarity = "Legendary", Boost = 1.3 },
		},
	},
	{
		Id = "Vampire", Name = "Vampire", Weight = 15, Color = rgb(200, 40, 60), Family = "Undead",
		Text = "The night school was built for your kind.",
		Tiers = { "Fledgling", "Night Gentry", "Elder" },
		Passive = { Name = "Night Blood", Text = "Stronger in the dark; every kill feeds you.",
			Strengths = { NightPower = { 0.06, 0.09, 0.12 }, HealOnKill = { 0.04, 0.06, 0.08 } },
			Drawbacks = { DamageByDay = -0.05 }, DrawbackText = "Weaker by day." },
		Palette = { -- pale or dark tones only
			rgb(242, 234, 228), rgb(236, 228, 214), rgb(222, 212, 194), rgb(214, 208, 200), rgb(196, 198, 204),
			rgb(92, 62, 48), rgb(74, 52, 46), rgb(62, 44, 38), rgb(40, 34, 36),
		},
		Subs = {
			{ Id = "Vampire", Name = "Vampire", Weight = 85, Rarity = "Uncommon", Boost = 1 },
			{ Id = "Nobleblood", Name = "Nobleblood", Weight = 12, Rarity = "Epic", Boost = 1.15 },
			{ Id = "RoyalVamp", Name = "Royal Vamp", Weight = 3, Rarity = "Legendary", Boost = 1.3 },
		},
	},
	{
		Id = "Werewolf", Name = "Werewolf", Weight = 10, Color = rgb(150, 120, 90), Family = "Cursed",
		Text = "The moon remembers what you are, even when you forget.",
		Tiers = { "Cursed", "Moonbound", "Feral Lord" },
		Passive = { Name = "Moon-Blooded", Text = "Hard to put down, and hungrier at night.",
			Strengths = { MaxHealth = { 10, 15, 20 }, NightPower = { 0.05, 0.08, 0.10 }, FullMoonPower = { 0.025, 0.04, 0.05 } },
			Drawbacks = { Stealth = 0.10 }, DrawbackText = "Easier to spot while sneaking." },
		Subs = {
			{ Id = "Werewolf", Name = "Werewolf", Weight = 85, Rarity = "Uncommon", Boost = 1 },
			{ Id = "Bloodmoon", Name = "Bloodmoon", Weight = 12, Rarity = "Epic", Boost = 1.15 },
			{ Id = "Alpha", Name = "Alpha", Weight = 3, Rarity = "Legendary", Boost = 1.3 },
		},
	},
	{
		Id = "Ghoul", Name = "Ghoul", Weight = 6, Color = rgb(120, 140, 104), Family = "Undead",
		Text = "Something in the cellar woke up hungry. It was you.",
		Tiers = { "Starveling", "Grave-eater", "Charnel Lord" },
		Passive = { Name = "Grave Hunger", Text = "Rotten, tough, and mended by feeding.",
			Strengths = { DamageTaken = { -0.05, -0.08, -0.10 }, LowHealthRegen = { 0.01, 0.1, 0.2 }, HealOnExecute = { 0.06, 0.09, 0.12 } },
			Drawbacks = { ClassExp = -0.10 }, DrawbackText = "Learns less in class." },
		Palette = { -- ghoul tones only
			rgb(132, 138, 130), rgb(122, 140, 104), rgb(118, 100, 124), rgb(160, 158, 150), rgb(160, 152, 96), rgb(104, 118, 132),
		},
		Subs = {
			{ Id = "Ghoul", Name = "Ghoul", Weight = 85, Rarity = "Rare", Boost = 1 },
			{ Id = "Ghast", Name = "Ghast", Weight = 12, Rarity = "Epic", Boost = 1.15 },
			{ Id = "CryptLord", Name = "Crypt Lord", Weight = 3, Rarity = "Legendary", Boost = 1.3 },
		},
	},
	{
		Id = "Wraith", Name = "Wraith", Weight = 4, Color = rgb(150, 180, 210), Family = "Undead",
		Text = "Half of you never came back from the cold.",
		Tiers = { "Whisper", "Shroud", "Dirge" },
		Passive = { Name = "Unseen", Text = "Hard to see, hard to stagger, sharper after dark.",
			Strengths = { Stealth = { -0.10, -0.15, -0.20 }, PostureGain = { -0.06, -0.09, -0.12 }, NightExp = { 0.06, 0.09, 0.12 } },
			Drawbacks = { MaxHealth = -10 }, DrawbackText = "A frailer body." },
		Subs = {
			{ Id = "Wraith", Name = "Wraith", Weight = 85, Rarity = "Rare", Boost = 1 },
			{ Id = "Revenant", Name = "Revenant", Weight = 12, Rarity = "Epic", Boost = 1.15 },
			{ Id = "HollowKing", Name = "Hollow King", Weight = 3, Rarity = "Legendary", Boost = 1.3 },
		},
	},
}
```

The helpers, after the `RaceById` maps are built:

```lua
function Lineage.Family(raceId)
	local r = RaceById[raceId]
	return r and r.Family
end
function Lineage.IsUndead(raceId) return Lineage.Family(raceId) == "Undead" end
function Lineage.IsMonster(raceId)
	local f = Lineage.Family(raceId)
	return f == "Undead" or f == "Cursed"
end
function Lineage.Palette(raceId)
	local r = RaceById[raceId]
	return r and r.Palette
end
function Lineage.TierName(raceId, tier)
	local r = RaceById[raceId]
	if not r then return "" end
	return r.Tiers[math.clamp(math.floor(tonumber(tier) or 1), 1, #r.Tiers)]
end
-- strengths (tier value x sub-race boost), drawbacks (flat), boost
function Lineage.Passives(raceId, subId, tier)
	local r = RaceById[raceId]
	if not (r and r.Passive) then return {}, {}, 1 end
	tier = math.clamp(math.floor(tonumber(tier) or 1), 1, 3)
	local s = SubById[subId]
	local boost = (s and s.Race == r and s.Sub.Boost) or 1
	local strengths, drawbacks = {}, {}
	for k, byTier in pairs(r.Passive.Strengths) do
		local v = byTier[tier] * boost
		if math.abs(v) > 1e-6 then strengths[k] = v end
	end
	for k, v in pairs(r.Passive.Drawbacks or {}) do drawbacks[k] = v end
	return strengths, drawbacks, boost
end
function Lineage.PassiveEffects(raceId, subId, tier)
	local a, b = Lineage.Passives(raceId, subId, tier)
	local out = table.clone(a)
	for k, v in pairs(b) do out[k] = (out[k] or 0) + v end
	return out
end
-- The night of in-game day D runs 20:00 on D to 06:00 on D+1. Every FullMoonEvery-th night is a full moon.
function Lineage.IsFullMoon(day, hour)
	if type(day) ~= "number" or type(hour) ~= "number" then return false end
	if not (hour >= 20 or hour < 6) then return false end
	local night = if hour < 6 then day - 1 else day
	return night % Lineage.FullMoonEvery == 0
end
```

- [ ] **Step 4: Install and run the tests.**
  - Run: `python Studio/install.py ReplicatedStorage.Lineage ModuleScript Studio/src/Lineage.luau`, then `Studio/rd.sh tests/lineage_test.luau`.
  - Expected: `PASS 52 checks` (the exact count can differ; it must say PASS).

- [ ] **Step 5: Keep the Wardrobe working.** The Wardrobe's `SubEntry` reads `Found.Sub.Rarity` and `Found.Race.Name`, both unchanged. Run `Studio/rd.sh` on a one-line check, `return #require(game.ReplicatedStorage.Lineage).Odds("Ghoul")`. Expected: `3`.

- [ ] **Step 6: Commit the plan's progress note** (the source stays out of the repo): nothing to commit yet. Record "Task 1 done" in the session task list.

### Task 2: Effect keys and labels in Config.Progression

**Files:**
- Modify: `Studio/src/ConfigProgression.luau` (the `Progression.Active`, `LABELS` and `Describe` blocks).
- Test: append to `Studio/tests/lineage_test.luau`.

**Interfaces (produces):**
- Active keys `AllExp`, `DamageVsUndead`, `DamageVsMonster`, `DamageTakenFromUndead`, `DamageByDay`, `HealOnKill`, `HealOnExecute`, `FullMoonPower`.
- `Describe` writes `LowHealthRegen` as HP per second.

- [ ] **Step 1: Add the failing checks** before the `return` line of the test:

```lua
local P = require(game.ReplicatedStorage.Config.Progression)
for _, k in { "AllExp", "DamageVsUndead", "DamageVsMonster", "DamageTakenFromUndead", "DamageByDay", "HealOnKill", "HealOnExecute", "FullMoonPower" } do
	eq(k .. " active", P.Active[k], true)
end
eq("describe all exp", P.Describe({ AllExp = 0.08 }), "+8% all EXP")
eq("describe regen", P.Describe({ LowHealthRegen = 0.1 }), "heal 1.5 HP/s when badly hurt")
eq("describe vs undead", P.Describe({ DamageVsUndead = 0.06 }), "+6% damage vs the undead")
eq("describe day", P.Describe({ DamageByDay = -0.05 }), "−5% damage by day")
```

- [ ] **Step 2: Run.** `Studio/rd.sh tests/lineage_test.luau` should FAIL with "AllExp active: got nil want true".

- [ ] **Step 3: Implement.**
  - In `Progression.Active`, add `AllExp = true; DamageVsUndead = true; DamageVsMonster = true; DamageTakenFromUndead = true; DamageByDay = true; HealOnKill = true; HealOnExecute = true; FullMoonPower = true;`.
  - Add the same keys to the comment table above it, each with "active".
  - In `LABELS`, add the entries below:

```lua
	AllExp = `all EXP`; DamageVsUndead = `damage vs the undead`; DamageVsMonster = `damage vs monsters`;
	DamageTakenFromUndead = `damage taken from the undead`; DamageByDay = `damage by day`;
	HealOnKill = `max health healed per kill`; HealOnExecute = `max health healed per execution`;
	FullMoonPower = `extra damage on a full-moon night`;
```

   In `Describe`, replace `if K == \`MaxHealth\` then Text = \`+{V} {Label}\`` with:

```lua
		if K == `MaxHealth` then Text = `{if V >= 0 then `+` else `−`}{math.abs(math.floor(V + 0.5))} {Label}`
		elseif K == `LowHealthRegen` then Text = `heal {string.format("%g", math.floor((1 + V * 5) * 10 + 0.5) / 10)} HP/s when badly hurt`
```

- [ ] **Step 4: Install and run.**
  - Run: `python Studio/install.py ReplicatedStorage.Config.Progression ModuleScript Studio/src/ConfigProgression.luau`, then the test.
  - Expected: PASS.

### Task 3: Race passives in Services.Player.Progression

**Files:**
- Modify: `Studio/src/Progression.luau`: `Shared.Effects` (line 85), `Shared.Apply` (119), `Shared.Award` bonus (156), `Shared.Sheet` (227), `Local.Hook` (254), `OnStart` watchers and loop (344–375).

**Interfaces:**
- **Consumes:** `Lineage.PassiveEffects`, `Lineage.Passives`, `Lineage.TierName`, `Lineage.IsFullMoon` (Task 1), and the new keys (Task 2).
- **Produces:**
  - Character attributes `NH_VsUndead`, `NH_VsMonster`, `NH_FromUndead` (numbers, nil when 0).
  - `Sheet.RaceInfo = { Race, Sub, Rarity, Tier, TierName, Passive, Strengths, Drawbacks }` (strings).

- [ ] **Step 1: Add race passives in `Shared.Effects`.** After the traits loop (line 101), insert:

```lua
	if L and L.Race then
		local Fx = Lineage.PassiveEffects(L.Race, L.SubRace, L.Tier)
		Local.Add(E, Fx)
		Sources.Race = { Race = L.Race; Sub = L.SubRace; Tier = L.Tier }
	end
```

- [ ] **Step 2: Update `Shared.Apply`.**
  - Replace the `local Night = …` and `local Dealt = …` lines (124–125) with the block below.
  - After the `NH_Stealth` line (132), add the three attribute lines below it.

```lua
	local Night = Local.IsNight()
	local FullMoon = Night and Local.IsFullMoon()
	local Dealt = 1 + (E.DamageDealt or 0) + (if Night then (E.NightPower or 0) + (if FullMoon then E.FullMoonPower or 0 else 0) else (E.DamageByDay or 0))
```
```lua
	local function opt(V) return if V and math.abs(V) > 1e-4 then V else nil end
	Character:SetAttribute(`NH_VsUndead`, opt(E.DamageVsUndead))
	Character:SetAttribute(`NH_VsMonster`, opt(E.DamageVsMonster))
	Character:SetAttribute(`NH_FromUndead`, opt(E.DamageTakenFromUndead))
```
   Add next to `Local.IsNight`:
```lua
function Local.IsFullMoon(): boolean
	local Clock = try({ `Services`, `School`, `SchoolClock` })
	local Ok, State = pcall(function() return Clock.GetState() end)
	return Ok and State and Lineage.IsFullMoon(State.Day, State.Hour) or false
end
```

- [ ] **Step 3: All-EXP bonus in `Award`.** After `local Bonus = 1 + (E[\`{Cat or \`\`}Exp\`] or 0)`, add `Bonus += E.AllExp or 0`.

- [ ] **Step 4: Healing hooks in `Local.Hook`** (inside it, after the `OnExecuted` award hook):

```lua
	local function heal(Character: Model?, Fraction: number)
		local H = Character and Character:FindFirstChildOfClass(`Humanoid`)
		if H and H.Health > 0 and Fraction > 0 and not Character:GetAttribute(`DownedUntil`) then
			H.Health = math.min(H.MaxHealth, H.Health + H.MaxHealth * Fraction)
		end
	end
	on({ `Services`, `Features`, `Downed` }, `OnExecuted`, function(Gripper)
		local Player = Players:GetPlayerFromCharacter(Gripper)
		if Player then heal(Gripper, Shared.Effects(Player).HealOnExecute or 0) end
	end)
	on({ `Services`, `Features`, `Downed` }, `OnDefeated`, function(Target, Killer)
		local Player = Killer and Players:GetPlayerFromCharacter(Killer)
		if Player and Killer ~= Target then heal(Killer, Shared.Effects(Player).HealOnKill or 0) end
	end)
```

- [ ] **Step 5: Re-apply when the race or the time of day changes.**
  - In `Watch`, change `if Name == \`Traits\` or Name == \`Signed\` then` to `if Name == \`Traits\` or Name == \`Signed\` or Name == \`Race\` or Name == \`SubRace\` or Name == \`RaceTier\` then`.
  - In the 1-second loop, change `if (E.NightPower or 0) > 0 then Shared.Apply(Player) end` to `if (E.NightPower or 0) ~= 0 or (E.DamageByDay or 0) ~= 0 or (E.FullMoonPower or 0) ~= 0 then Shared.Apply(Player) end`.

- [ ] **Step 6: `Sheet.RaceInfo`.** In `Shared.Sheet`, before `return {`, add the block below. Then add `RaceInfo = RaceInfo;` to the returned table.

```lua
	local RaceInfo = nil
	if Sources.Race then
		local R = Lineage.RaceById[Sources.Race.Race]
		local S = Lineage.SubById[Sources.Race.Sub]
		local Str, Dra = Lineage.Passives(Sources.Race.Race, Sources.Race.Sub, Sources.Race.Tier)
		RaceInfo = {
			Race = R and R.Name or Sources.Race.Race; Sub = S and S.Sub.Name or ``; Rarity = S and S.Sub.Rarity or ``;
			Tier = Sources.Race.Tier; TierName = Lineage.TierName(Sources.Race.Race, Sources.Race.Tier);
			Passive = R and R.Passive and R.Passive.Name or ``;
			Strengths = Config.Describe(Str); Drawbacks = if next(Dra) then Config.Describe(Dra) else (R and R.Passive and R.Passive.DrawbackText or ``);
		}
	end
```

- [ ] **Step 7: Install.**
  - Run: `python Studio/install.py ServerScriptService.Services.Player.Progression ModuleScript Studio/src/Progression.luau`.
  - Check that it compiles: `Studio/rd.sh` on `local ok, e = pcall(require, game.ServerScriptService.Services.Player.Progression) return tostring(ok) .. " " .. tostring(e)`. Expected: `true table: …`.

### Task 4: Race damage scale

**Files:**
- Modify: `Studio/src/Lineage.luau` (add `DamageScale`).
- Modify in Studio (multi_edit): `ServerScriptService.Services.Features.Downed`, inside `Shared.ApplyDamage`.
- Test: append to `Studio/tests/lineage_test.luau`.

**Interfaces (produces):** `Lineage.DamageScale(attacker: Model, target: Model) -> number`. It reads `Race` from the player or the model, `NH_VsUndead` and `NH_VsMonster` on the attacker, and `NH_FromUndead` on the target.

- [ ] **Step 1: Add the failing checks** to the test, before `return`:

```lua
local function model(race, attrs)
	local m = Instance.new("Model")
	m:SetAttribute("Race", race)
	for k, v in attrs or {} do m:SetAttribute(k, v) end
	return m
end
local priest = model("Priest", { NH_VsUndead = 0.06, NH_FromUndead = -0.06 })
local vamp = model("Vampire")
local wolf = model("Werewolf")
local slayer = model("Human", { NH_VsMonster = 0.08 })
eq("priest hits vampire", L.DamageScale(priest, vamp), 1.06)
eq("priest hits werewolf (not undead)", L.DamageScale(priest, wolf), 1)
eq("vampire hits priest", L.DamageScale(vamp, priest), 0.94)
eq("slayer hits werewolf", L.DamageScale(slayer, wolf), 1.08)
eq("no race npc", L.DamageScale(model(nil), model(nil)), 1)
for _, m in { priest, vamp, wolf, slayer } do m:Destroy() end
```

- [ ] **Step 2: Run.** It should FAIL with "attempt to call a nil value (field 'DamageScale')".

- [ ] **Step 3: Implement** in `Lineage.luau` after `IsFullMoon`:

```lua
local function raceOf(model)
	if typeof(model) ~= "Instance" then return nil end
	local p = Players:GetPlayerFromCharacter(model)
	return (p and p:GetAttribute("Race")) or model:GetAttribute("Race")
end
-- Extra damage multiplier from race families (Downed.ApplyDamage applies it after the stat multipliers).
function Lineage.DamageScale(attacker, target)
	local scale = 1
	local tr, ar = raceOf(target), raceOf(attacker)
	if Lineage.IsUndead(tr) then scale *= 1 + (attacker:GetAttribute("NH_VsUndead") or 0) end
	if Lineage.IsMonster(tr) then scale *= 1 + (attacker:GetAttribute("NH_VsMonster") or 0) end
	if Lineage.IsUndead(ar) then scale *= 1 + (target:GetAttribute("NH_FromUndead") or 0) end
	return scale
end
```

- [ ] **Step 4: Install Lineage and run the tests.** Expected: PASS.

- [ ] **Step 5: Patch Downed** (Studio multi_edit, Edit mode).
  - old: `	Damage *= Target:GetAttribute(\`NH_DamageTaken\`) or 1\n`
  - new:

```lua
	Damage *= Target:GetAttribute(`NH_DamageTaken`) or 1
	-- races: bonuses vs undead / monsters and protection from undead (ReplicatedStorage.Lineage)
	if Attacker and Attacker ~= Target then Damage *= require(ReplicatedStorage.Lineage).DamageScale(Attacker, Target) end
```

   Check that `ReplicatedStorage` is defined at the top of Downed (line 24: it is).

### Task 5: Test bridge commands and a Play check of the passives

**Files:**
- Modify in Studio: `ServerScriptService.Services.Studio.TestBridge`. Add the commands after `Commands.SpendStat`.
- Modify: `Studio/src/Lineage.luau`. Expose `Lineage.SetForTests(player, race, sub, tier)` inside `StartServer`, next to `GrantSpins`, using `save`.

- [ ] **Step 1: Server hook in `Lineage.StartServer`** (after `GrantSpins`):

```lua
	-- Studio test bridge only: force a race/sub/tier through the normal save path
	function Lineage.SetForTests(p, race, sub, tier)
		if not RunService:IsStudio() then return false end
		local l = current(p)
		if not (l and RaceById[race]) then return false end
		l.Race = race
		local s = SubById[sub]
		l.SubRace = (s and s.Race.Id == race) and sub or race
		l.Tier = math.clamp(math.floor(tonumber(tier) or 1), 1, 3)
		save(p, l)
		return true, l
	end
```

- [ ] **Step 2: TestBridge commands:**

```lua
-- Races: force a lineage, then read what the race passive put on the character
function Commands.SetRace(PlayerName: string, Race: string, Sub: string?, Tier: number?)
	return { require(ReplicatedStorage.Lineage).SetForTests(Players:FindFirstChild(PlayerName), Race, Sub, Tier) }
end
function Commands.RaceDamage(AttackerName: string, TargetName: string, Damage: number)
	local Downed = require(ServerScriptService.Services.Features.Downed)
	local A, T = FindCharacter(AttackerName), FindCharacter(TargetName)
	local H = T and T:FindFirstChildOfClass(`Humanoid`)
	if not (A and H) then return `missing` end
	local Before = H.Health
	Downed.ApplyDamage(T, Damage, A)
	return Before - H.Health
end
```

   Note: `SetForTests` keeps the existing 15 s kill-tier loop (spec Phase 3 removes it). With 0 kills, the loop resets the tier to 1 within 15 s. So test Tier I numbers, or read the sheet within 15 s of setting the tier.

- [ ] **Step 3: Install Lineage, announce Play to both sessions, start Play** (one player, the main menu: pick a slot, Enter School).

- [ ] **Step 4: Check effects through the bridge** (server datamodel):
  - `ServerStorage.NHTestBridge:Invoke("SetRace", "<you>", "Werewolf", "Alpha", 1)`, then `Invoke("Progress", "<you>").RaceInfo`.
    - Expected: Race Werewolf, Sub Alpha, TierName "Cursed", Passive "Moon-Blooded", Strengths including "+13 max health" (10 × 1.3 rounded) and Drawbacks "+10% chance to be spotted".
    - Also: `Humanoid.MaxHealth` = 113 plus your stat and clan bonuses (note them before).
  - `SetRace … "Priest", "Priest", 1`: the character has `NH_VsUndead` = 0.06.
    - Spawn or pick a training dummy and set `dummy:SetAttribute("Race", "Vampire")`.
    - `Invoke("RaceDamage", "<you>", "<dummy>", 10)` → 10 × NH_DamageDealt × 1.06. Record the exact number.
  - `SetRace … "Vampire"` and set the clock to day (`SchoolClock.SetTime("12:00 PM")`): `NH_DamageDealt` drops by 0.05. At `SetTime("10:00 PM")` it rises by 0.06.

- [ ] **Step 5: Stop Play** and tell both sessions Studio is free.

### Task 6: Bloodline tab

**Files:**
- Create: `Studio/src/Bloodline.luau` → `StarterPlayer.StarterPlayerScripts.Controllers.Gui.Bloodline` (ModuleScript).
- Modify: `Studio/src/IdentityClient.luau`: `TABS`/`TAB_KEYS` (line 34), `Local.Render` (513–521).
- Modify in Studio: `Controllers.Gui.MainMenu`, the nav build (lines 899–913) and the `Local.CreatorTab` comment.
- Modify in Studio: `Controllers.Gui.Wardrobe`, the `Local.LineageTab` body (lines 492–557).
- Modify: `Studio/src/ProgressClient.luau`, the record bonuses (lines 189–192) and a Bloodline button.

**Interfaces:**
- **Consumes:** `Lineage.Get/Spin/Describe/Odds/Passives/TierName/Rarity/TraitSlots` and `Config.Progression.Describe`. From Identity: `Ctx = { Section(text), Note(text, color?), Row(height) -> Frame, Next() -> number, Options: ScrollingFrame, Status(text, color?), Render(), OpenTab(key) }`.
- **Produces:** `Bloodline.Build(Ctx)` builds the tab into `Ctx.Options` in layout order, and `Bloodline.Busy() -> bool`.

- [ ] **Step 1: `Studio/src/Bloodline.luau`:**

```lua
--[[
	Bloodline tab (client): your race, sub-race and tier, the race and variant spins, the race passive and
	your traits. Race is rolled by the server (ReplicatedStorage.Lineage); this only shows it and asks to spin.
	Built into the Identity panel (Controllers.Gui.Identity) by Bloodline.Build(Ctx).
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local Lineage = require(ReplicatedStorage:WaitForChild(`Lineage`))
local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Progression = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Progression`))
local C = Kit.Theme.Colors
local Fonts = Kit.Theme.Fonts
local ROMAN = { `I`, `II`, `III` }

local Shared = {}
local Data = nil   -- last known lineage
local SpinBusy = false

local function hex(c: Color3) return c:ToHex() end
local function entry(subId)
	local f = subId and Lineage.SubById[subId]
	if not f then return { text = `Unrolled`; sub = `Spin to find out`; color = C.TextDim } end
	local r = Lineage.Rarity[f.Sub.Rarity]
	return { text = f.Sub.Name; sub = `{f.Race.Name}  ·  {f.Sub.Rarity}`; color = r and r.Color or C.Text }
end

function Shared.Busy(): boolean return SpinBusy end

function Shared.Spin(Ctx, Kind: string, Slot: number?, Reel)
	if SpinBusy then return end
	SpinBusy = true
	Ctx.Status(`Spinning...`)
	task.spawn(function()
		local Ok, Result = Lineage.Spin(Kind, Slot)
		if not Ok then SpinBusy = false Ctx.Status(tostring(Result), C.Crimson) return end
		local function Done()
			Data = Lineage.Sanitize(Result)
			SpinBusy = false
			local Race, Sub, Traits = Lineage.Describe(Data)
			Ctx.Status(if Kind == `Trait` then `New trait: {Traits[Slot] and Traits[Slot].Name or "?"}` else `You are {Sub and Sub.Name or "?"} ({Race and Race.Name or "?"})`, C.Gold)
			Ctx.Render()
		end
		if Reel and Kind ~= `Trait` then
			local Pool = {}
			for _, R in Lineage.Races do
				if Kind == `Race` or R.Id == (Data and Data.Race) then
					for _, S in R.Subs do table.insert(Pool, entry(S.Id)) end
				end
			end
			Reel:Spin(Pool, entry(Result.SubRace), 2.6, Done)
		else
			Done()
		end
	end)
end

function Shared.Build(Ctx)
	Data = if SpinBusy and Data then Data else Lineage.Get()
	local L = Data
	local Race, Sub, Traits = Lineage.Describe(L)
	local Free = RunService:IsStudio()
	local function count(k) return if Free then `free` else tostring(L.Spins[k] or 0) end

	-- crest: race name in its colour, sub-race, tier title
	Ctx.Section(`Bloodline`)
	local Crest = Ctx.Row(96)
	Kit.Decorate(Crest, { ornament = `slot`; shadow = false })
	local RaceCol = Race and Race.Color or C.Text
	local Name = Kit.Text({ Text = if Race then string.upper(Race.Name) else `UNROLLED`; Font = Fonts.Title; TextSize = 40; TextColor3 = RaceCol;
		TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 10); Size = UDim2.new(1, 0, 0, 44); Parent = Crest })
	pcall(Kit.Emboss, Name, RaceCol:Lerp(Color3.new(0, 0, 0), 0.5), 1.4)
	local Rarity = Sub and Lineage.Rarity[Sub.Rarity]
	Kit.Text({ Text = if Race then `<font color="#{hex(Rarity and Rarity.Color or C.Text)}">{Sub and Sub.Name or Race.Name}</font>   ·   Tier {ROMAN[L.Tier] or L.Tier}, {Lineage.TierName(L.Race, L.Tier)}` else ``;
		RichText = true; TextSize = 20; TextColor3 = C.Text; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 58); Size = UDim2.new(1, 0, 0, 26); Parent = Crest })
	if Race then Ctx.Note(Race.Text) end

	-- spins
	local _, Reel = Kit.SpinReel({ entry = entry(L.SubRace); height = 72; textSize = 36; Size = UDim2.new(1, 0, 0, 84); LayoutOrder = Ctx.Next(); Parent = Ctx.Options })
	local Buttons = Ctx.Row(48)
	Kit.Button({ text = `Spin race ({count("Race")})`; style = `crimson`; textSize = 20; onClick = function() Shared.Spin(Ctx, `Race`, nil, Reel) end;
		Position = UDim2.fromScale(0, 0); Size = UDim2.new(0.5, -6, 0, 44); Parent = Buttons })
	Kit.Button({ text = `Spin variant ({count("Variant")})`; textSize = 20; onClick = function() Shared.Spin(Ctx, `Variant`, nil, Reel) end;
		AnchorPoint = Vector2.new(1, 0); Position = UDim2.fromScale(1, 0); Size = UDim2.new(0.5, -6, 0, 44); Parent = Buttons })
	local Odds = {}
	for _, R in Lineage.Odds() do table.insert(Odds, `{R.Name} {string.format("%g", math.floor(R.Chance * 10 + 0.5) / 10)}%`) end
	Ctx.Note(`Race odds: {table.concat(Odds, ", ")}.  A race spin rolls a new race and variant; a variant spin keeps your race.` .. (if Free then `  Spins are free while testing in Studio.` else ``))
	local More = Ctx.Row(48)
	Kit.Button({ text = `Get more spins`; style = `gold`; textSize = 20; onClick = function() Ctx.OpenTab(`Shop`) end; Size = UDim2.new(0.5, -6, 0, 44); Parent = More })

	-- passive
	if Race and Race.Passive then
		Ctx.Section(`Passive: {Race.Passive.Name}`)
		Ctx.Note(Race.Passive.Text)
		local Str, Dra = Lineage.Passives(L.Race, L.SubRace, L.Tier)
		Ctx.Note(`<font color="#{hex(C.Gold)}">{Progression.Describe(Str)}</font>`, C.Text)
		Ctx.Note(`<font color="#{hex(C.Crimson)}">{if next(Dra) then Progression.Describe(Dra) else Race.Passive.DrawbackText}</font>`, C.Text)
		for T = (L.Tier or 1) + 1, 3 do
			local S2 = Lineage.Passives(L.Race, L.SubRace, T)
			Ctx.Note(`At Tier {ROMAN[T]} ({Lineage.TierName(L.Race, T)}): {Progression.Describe(S2)}`)
		end
	end

	-- traits (moved here from the Wardrobe's Lineage tab)
	Ctx.Section(`Traits`)
	for Slot = 1, Lineage.TraitSlots do
		local T = Traits[Slot]
		local Row = Ctx.Row(72)
		local Col = T and Lineage.Rarity[T.Rarity]
		Kit.Text({ Text = if T then `{T.Name}   <font color="#{hex(Col and Col.Color or C.Text)}">{T.Rarity}</font>` else `Empty slot`; RichText = true; TextSize = 22;
			TextColor3 = C.Text; Size = UDim2.new(1, -176, 0, 28); Parent = Row })
		local Desc = if T then T.Text else `Spin to fill this slot.`
		if T and T.Effects then
			local Ok, Fx = pcall(Progression.Describe, T.Effects)
			if Ok and Fx ~= `` then Desc = `{T.Text}  <font color="#{hex(C.Gold)}">{Fx}</font>` end
		end
		Kit.Text({ Text = Desc; RichText = true; TextWrapped = true; TextSize = 18; TextColor3 = C.TextDim:Lerp(C.Text, 0.45);
			Position = UDim2.fromOffset(0, 30); Size = UDim2.new(1, -176, 0, 40); Parent = Row })
		Kit.Button({ text = `Reroll ({count("Trait")})`; textSize = 20; onClick = function() Shared.Spin(Ctx, `Trait`, Slot) end;
			AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 12); Size = UDim2.fromOffset(164, 44); Parent = Row })
	end
	Ctx.Note(`Race, variant and traits are rolled, never chosen. Your tier grows as your bloodline evolves.`)
end

return Shared
```

- [ ] **Step 2: Identity panel tab.**
  - In `IdentityClient.luau`, change lines 34–35 to:

```lua
local TABS = { `Bloodline`, `Name & Clan`, `Spin Shop` }
local TAB_KEYS = { `Bloodline`, `Name`, `Shop` }
```

  - Replace `if Tab == 1 then Local.NameTab() else Local.ShopTab() end` in `Local.Render` with:

```lua
	local Key = TAB_KEYS[Tab]
	if Key == `Bloodline` then
		local Ok, Bloodline = pcall(require, script.Parent:WaitForChild(`Bloodline`, 5))
		if Ok and Bloodline then
			Bloodline.Build({ Section = Local.Section; Note = Local.Note; Row = Local.Row; Next = Local.Next; Options = Ui.Options;
				Status = Local.Status; Render = Local.Render; OpenTab = Shared.OpenTab })
		end
	elseif Key == `Name` then Local.NameTab() else Local.ShopTab() end
```

  - Grep `IdentityClient.luau` for other `Tab == 1` / `Tab == 2` uses (e.g. `Reveal`, `Prompt`, the default `Tab` value) and change each to compare `TAB_KEYS[Tab]` with a key. The default tab must stay `Name` (index 2) so first-time naming still lands on Name & Clan.

- [ ] **Step 3: Main menu nav** (Studio multi_edit in `Controllers.Gui.MainMenu`):
  - `Nav.Size = UDim2.fromOffset(320, 3 * 62)` → `Nav.Size = UDim2.fromOffset(320, 4 * 62)`
  - `for I, Def in { { \`Look\`, \`Look\` }, { \`Name\`, \`Name & Clan\` }, { \`Shop\`, \`Spin Shop\` } } do` → `for I, Def in { { \`Look\`, \`Look\` }, { \`Bloodline\`, \`Bloodline\` }, { \`Name\`, \`Name & Clan\` }, { \`Shop\`, \`Spin Shop\` } } do`
  - The comment `-- Look = the Wardrobe; Name / Shop = the Identity panel.` → `-- Look = the Wardrobe; Bloodline / Name / Shop = the Identity panel.`
  - `Local.CreatorTab` already sends non-Look tabs to `Identity.OpenTab(Name)`. No other change.

- [ ] **Step 4: Wardrobe Lineage tab points to Bloodline.** Replace the body of `Local.LineageTab` (lines 493–556) with:

```lua
	Local.Section(`Lineage`)
	Local.Note(`Your race, variant, passive and traits now live in the Bloodline tab.`)
	local Row = Local.Row()
	Kit.Button({ text = `Open Bloodline`; style = `gold`; LayoutOrder = 1; Size = UDim2.fromOffset(250, 44); Parent = Row;
		onClick = function()
			local Ok, Identity = pcall(require, script.Parent:FindFirstChild(`Identity`))
			if Ok and Identity and Identity.OpenTab then Shared.Toggle(false) Identity.OpenTab(`Bloodline`) end
		end })
```

   Keep `SubEntry` and `Local.DoSpin` (unused now but harmless), or delete both only if nothing else references them (grep first).

- [ ] **Step 5: Record shows the race and opens Bloodline.** In `ProgressClient.luau`, before the Clan bonus row (line 190), insert:

```lua
	if Sheet.RaceInfo then
		local R = Sheet.RaceInfo
		table.insert(Bonuses, { label = R.Passive ~= `` and R.Passive or R.Race; value = R.Strengths; color = C.Text })
		table.insert(Bonuses, { label = `Drawback`; value = R.Drawbacks; color = C.Crimson })
	end
```

   Change the Lineage row (line 201) to `{ label = \`Lineage\`; value = if Sheet.RaceInfo then \`{Sheet.RaceInfo.Sub}  ·  Tier {Sheet.RaceInfo.Tier}, {Sheet.RaceInfo.TierName}\` else \`Unrolled\` };`. After the Close button, add:

```lua
	local Blood = Kit.Button({ text = `Bloodline`; style = `ghost`; textSize = 18; Name = `Bloodline`; AnchorPoint = Vector2.new(0, 0); Position = UDim2.fromOffset(6, 6); Size = UDim2.fromOffset(110, 32);
		onClick = function()
			local Ok, Identity = pcall(require, script.Parent:FindFirstChild(`Identity`))
			if Ok and Identity then Shared.Toggle(false) Identity.OpenTab(`Bloodline`) end
		end })
	Blood.Parent = Root
```

- [ ] **Step 6: Install all of it.**
  - Run `install.py` for Bloodline (`ModuleScript`), Identity and Progress.
  - Apply the MainMenu and Wardrobe edits.
  - Check that everything compiles: require each module from the server datamodel's view of `StarterPlayer…` with `loadstring` disabled; instead, start Play and watch the console for errors.

- [ ] **Step 7: Play check** (announce first):
  - **Creator:** the nav shows 4 buttons. Bloodline shows the crest, the reel, the odds (Human 40% … Wraith 4%), the passive in gold, the drawback in crimson, the "At Tier II/III" previews and the traits. Spin race: the reel lands, and the Record/sheet updates.
  - **Name & Clan** still opens and works the same.
  - **In school:** L opens the Record. It shows the race passive and drawback rows, and its Bloodline button opens the Identity panel on Bloodline.
  - **K → Lineage** shows the "Open Bloodline" button.
  - Run the UI audit script (`Studio/ui_audit.luau`, client) on the Bloodline tab. Expected: no `small` or `contrast` lines for `Identity`.
  - Take screenshots for the docs. Stop Play and tell the sessions.

### Task 7: Palette handover, docs, changelog, push

**Files:**
- Create: `docs/Races-and-Bloodlines.md`.
- Modify: `CHANGELOG.md` (new top entry, edited in place after `git pull`), `docs/Implementation-Status.md`, `README.md` (Latest update), `docs/UI-Kit.md` (the Lineage section now points to Races-and-Bloodlines).
- Create: `updates/discord/2026-10-30-bloodlines.md`.

- [ ] **Step 1: Message the UI kit session** (`local_49983083-1634-4eea-8a8b-37dd1f973d04`):
  - The palettes exist: `Lineage.Palette(raceId)` is 9 colours for Vampire and 6 for Ghoul, and nil means normal tones.
  - The user's answer on avatar mode: **clamp it too.** In "use my Roblox outfit" mode, a Vampire's or Ghoul's skin also moves to the nearest palette colour, and clothes and accessories stay.
  - Ask them to clamp in the server Set handler and `ApplyTo`, and to filter the swatches and wheel. Ask them to reply when it's done and playtested.

- [ ] **Step 2: Write `docs/Races-and-Bloodlines.md`:**
  - the roster table with odds, subs and tiers
  - the passives table with the exact numbers
  - families, the damage rules, full moon
  - the Bloodline tab, saving (unchanged `Lineage` fields), the test bridge commands
  - **Verified:** what Task 5 and 6 actually showed, with numbers
  - **Not yet:** cosmetics (Phase 2), hunger, rites, bite (Phase 3), and the palette clamp (UI kit session)

- [ ] **Step 3: CHANGELOG entry** `## [Races 1.0] - 2026-10-30: Six bloodlines, passives and the Bloodline tab` (Added / Changed / Verified / Not yet). Add a status row and a README line, and a Discord post under 2000 chars.

- [ ] **Step 4: Scan and commit.**
  - Run: `git -C E:\Nightmare-Highschool diff --cached | grep -iE "api[_-]?key|token|secret|cookie|password"`. Expected: no output.
  - Run: `git add docs CHANGELOG.md README.md updates/discord/2026-10-30-bloodlines.md && git commit -m "Races 1.0: six bloodlines, passives, Bloodline tab" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git pull --rebase && git push`.

- [ ] **Step 5: Mirror** the new and changed docs and changelog to `E:\Download\Obsidian (VAULT)\Rello Memory\Nightmare Highschool` (Docs/, Changelog/, and the home note's link list). Remind the user to save the place in Studio.

---

## Self-review notes
- **Spec coverage, Phase 1:**
  - §1 roster, odds, families and sub boosts → Task 1.
  - §2 passives and new keys → Tasks 1–4. `HealOnExecute` is split from `HealOnKill`, so the Ghoul heals only on executions as the spec table says. The spec's key list is updated in Task 7's doc.
  - §3 palettes → Task 1 data plus the Task 7 handover.
  - §6 Bloodline tab → Task 6 (the hunger meter and rite are Phase 3, so the tab shows only tier titles and previews).
- **Deferred by design:** cosmetics (Phase 2); hunger, rites, earned tiers and the bite (Phase 3). Phase 3 deletes the 15 s kill-tier loop.
- **Names used across tasks:** `Lineage.Passives`, `PassiveEffects`, `TierName`, `IsFullMoon`, `DamageScale`, `SetForTests`; attributes `NH_VsUndead`, `NH_VsMonster`, `NH_FromUndead`; `Sheet.RaceInfo` fields Race/Sub/Rarity/Tier/TierName/Passive/Strengths/Drawbacks. These match everywhere they're used.
