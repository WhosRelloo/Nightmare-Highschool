# Line matrix

Added in 1.94.0. What a student says now depends on three things: their **clique**, how they **feel about you**
(attitude) and the **moment** (a greeting, a bump, a fight, the moon...). Students also notice what you wear, and each
clique's hangout keeps a dress code for in-person deals.

- **Place:** NH Combat Test (98950102230473) only. **The Map is not ported yet:** it needs cliques on its students and
  the standing service first.
- **Design:** `docs/superpowers/specs/2026-11-12-line-matrix-outfits-design.md`.
- **Repo mirror:** `tools/line-matrix/`. Studio is the source of truth at runtime; the repo copy is what you edit and
  install from.
- **Related:** `docs/Cliques.md` (standing, tiers, hangouts, quests), `docs/Gameplay-and-NPC-Concepts.md` (concepts 1 and 2).

## Where things live

| What | Studio path | Repo file |
|---|---|---|
| The lines | `ReplicatedStorage.Config.CliqueTalk` (a ModuleScript with one child module per clique, plus `Generic`) | `tools/line-matrix/Config.CliqueTalk.luau`, `tools/line-matrix/CliqueTalk/<Name>.luau` |
| Choosing a line, attitude, outfit verdicts | `ServerScriptService.Services.AI.StudentBrain.Talk` | `tools/line-matrix/Talk.luau` |
| The brain's call sites and the walk-in dress code | `ServerScriptService.Services.AI.StudentBrain` | `tools/ct-npc-1862/StudentBrain.luau` |
| Clique looks, taste, `ParseWear`, `WearsTop`, `WearsBottoms` | `ReplicatedStorage.Config.Cliques` | `tools/line-matrix/patches/ConfigCliques.json` |
| `NHWear` | `ReplicatedStorage.UI.Appearance` (`ApplyTo`) | `tools/line-matrix/patches/Appearance.json` |
| `Cliques.Dressed`, quest gate, dialogue, Night Study | `Social.Cliques`, `Quests.Quests`, `Social.Dialogue`, `ServerStorage.Dialogue.QuestChoices`, `Social.Hangouts` | `tools/line-matrix/patches/DressCode.json` |
| The tests | run with `execute_luau` (Edit mode) | `tools/line-matrix/tests/*.luau` |
| The play-test record | | `tools/line-matrix/PLAYTEST.md` |

The `patches/*.json` files are lists of `{ file_path, old_string, new_string }` edits for the live scripts.

## The module format

Each clique module returns `{ [Moment] = { [Attitude | "Any"] = { string } } }`. `Race` and `Outfit` nest one more level:

```lua
return {
	Greet = {
		Hostile = { `Bench warmer. Move.`, "Nobody picked you, {Name}. Nobody will." };
		Neutral = { ... };
	};
	Bump = { Any = { `Whoa, watch the shoulder!`, ... } };
	Race = { Human = { Hostile = { ... }; Any = { ... } }; Priest = { ... }; ... };
	Outfit = { FullLook = { ... }; RivalLook = { ... }; Likes = { ... }; Mocks = { ... } };
}
```

- **Modules:** one per clique, named exactly like its id in `Config.Cliques.Order` (`Vigil`, `Court`, `Athletes`,
  `Delinquents`, `Pack`, `Ordinary`, `Choir`, `Ink`), plus `Generic`. 9 modules in all.
- **Attitudes:** `Hostile`, `Wary`, `Neutral`, `Friendly`, `Respected` (the same names as `Cliques.Tiers`), plus `Any`
  for lines that suit every attitude. An attitude's own pool wins over `Any`.
- **Cells:** a cell is one pool for one moment (and sub-key) and attitude. A module has 105 of them: 11 plain moments
  times 5 attitudes, `Race` 6 races times 5, `Outfit` 4 verdicts times 5. Each cell must resolve to a pool of its own or
  through `Any`. The whole set is 945 cells and 2289 lines.
- **Greet:** a clique's `Greet` gives every attitude its own pool (no `Any`), so the greeting always has the clique's
  tone. The coverage test enforces this.
- **Placeholders:** lines with a `{Key}` go in **double quotes**. See "Writing rules".

### The moments

| Moment | Fires when | Falls back to |
|---|---|---|
| `Greet` | a greeting (see "Greeting order" below) | the time-of-day pools, or `Def.Reactions[Tier]` for a clique student |
| `Bump` | Nudges `MakeWay`: you brush past them walking (speed 18 or less) | `Lines.MakeWay`. Faster than 18 gives the old `Lines.Sprint` ("No running in the halls!") |
| `Crowded` | Nudges `Space`: you stand too close | `Lines.Space` |
| `Shoved` | Nudges `Shove`: you ram them. Said when the student turns to look at you | `Lines.MakeWay` |
| `FightSeen` | they watch a fight (Gawk) | `Lines.Gawk`. When they only hear the fight, half the time they use the old `Heard.Fight` pool instead of the matrix |
| `Flee` | they run from a fight near them | `Lines.Flee` |
| `Transformed` | you are in a beast form (`Appearance.FormOf` returns a form), in a greeting or when they run from a monster | `Lines.Monster` |
| `Night` | a greeting after dark | `Lines.Greet.Night` |
| `FullMoon` | a greeting on a full-moon night, 60% of the time (the rest get `Night`). A new-moon night keeps the old `Lines.Greet.NewMoon` pool, with no matrix moment | `Lines.Greet.FullMoon` |
| `Race` | a greeting that remarks on your race (`Race.<Race>.<Attitude>`: Human, Priest, Vampire, Werewolf, Ghoul, Wraith) | `Lines.Greet.Race[Race]` |
| `Hurt` | a greeting when your health is under 35% | the time-of-day pools |
| `Outfit` | an outfit remark (`Outfit.<Verdict>.<Attitude>`) | the time-of-day pools |
| `DressCode` | a clique turns you away for your clothes | the quest or notification just says no, or stays silent |

**Mutter is unchanged.** Idle mutters still use `Def.Lines` and do not depend on a player.

### Greeting order

`greeting()` in `StudentBrain` takes the first one that applies. The cooldowns: 60 s between greetings per student per
player, and 6 s on the speech bubble itself.

1. **Saw you fight** in the last 5 minutes: `Greet` with the attitude capped at `Wary` (a `Hostile` student stays
   `Hostile`). Falls back to today's `Wary` pool.
2. **An outfit verdict**, if there is one: 35% of the time for a clique student, 15% for one without a clique, and at
   most once per student per player every 600 s.
3. **Hurt**: 50% of the time when your health is under 35%.
4. **Transformed**: always, when you are in a beast form.
5. **Race**: 30% of the time.
6. **Clique `Greet`**, for a clique student. Hostile, Wary and Respected students always greet from the matrix.
   Neutral and Friendly students do so 60% of the time. **The night still shows at the extremes:** after dark, 40% of
   these greetings are `Night` (or `FullMoon` on a full-moon night) instead, with the same attitude, so a Hostile
   student still gets a Hostile night line.
7. The older **Often** and **Again** lines (you've met before).
8. **FullMoon** or **Night** through the matrix, after dark.
9. The time-of-day greeting.

Every step falls back to today's pool when the matrix has nothing, so nobody ever goes silent.

## How attitude is worked out

`Talk.Attitude(S, Player)`:

1. Start from the player's `CliqueTier_<S.Clique>` attribute (`Respected` 60+, `Friendly` 20+, `Neutral` -10+, `Wary`
   -40+, `Hostile` below). No clique, no attribute or no player is `Neutral`.
2. A member of the student's clique (`CliqueMembership.IsMember`) is at least `Friendly`.
3. The student's own memory of you moves it one step, once:
   - **down** if `S.Memory[UserId].Fought` is less than 300 s ago;
   - otherwise **up** if `Met` is 4 or more, but never above `Friendly` (so `Respected` comes only from standing).

   **Fought beats met:** the two don't cancel out. A student who just saw you fight isn't warmed by familiarity.
4. The result stays between `Hostile` and `Respected`.

## How a line is picked

`Talk.Pick(S, Moment, Player, Opts)` (`Opts`: `Sub` for the race or verdict, `Attitude` to override, `Piece`, `Ctx`).
The lookup tries, in order:

1. the clique's own pool for that attitude;
2. the clique's `Any` pool;
3. `Generic`'s pool for that attitude;
4. `Generic`'s `Any`;
5. `nil`, so the brain uses today's pool.

The chosen pool goes through `Lines.Pick` (the no-repeat rules still hold) and `Lines.Fill`. A line whose `{Key}` has
no value (no name, no piece) is skipped and another is picked from the same pool; a pool with nothing fillable returns
`nil`. `Pool` does **not** go on to `Generic` when every line in the clique's cell is unfillable: the brain uses
today's pool instead. The brain wraps every call in `pcall`. `Talk.Line(Clique, Moment, Player, Opts)` does the same for a stand-in
student (`{ Clique = ... }`, no memory) such as a leader in dialogue; it gets its attitude from standing alone.

### Robust loading

A broken module never takes the students down with it:

- `StudentBrain` requires `Talk` in a `pcall` (waiting 5 s for it). If that fails, it uses a stand-in `Talk` whose
  `Pick` and `Outfit` return `nil` and whose `Attitude` is `Neutral`, so every student talks from today's pools.
- `Talk` requires `Config.CliqueTalk` in a `pcall`. If it is missing or broken, the matrix is empty and every `Pick`
  returns `nil` (today's pools again). `Talk.Use` still swaps the data in for the tests.
- In `greeting()`, `Talk.Attitude` (steps 1 and 6) and `Appearance.FormOf` (step 4) are pcalled: a failure counts as
  `Neutral`, or as no beast form.

### Placeholders

| Placeholder | Becomes |
|---|---|
| `{Name}` | the player's first name |
| `{Piece}` | the worn piece's name in lower case (`crimson-banded top hat`). Only `Outfit.Likes` and `Outfit.Mocks` get one |
| `{Clique}` | the student's clique display name, for example "The Athletes" |
| `{Rival}` | the rival clique's display name |

The brain's older `{Day}`, `{Period}` and `{Moon}` also work.

## Outfits

### NHWear

`UI.Appearance.ApplyTo` sets the character attribute `NHWear` on a player's character: `"top|bottoms|acc,acc"`, the top
and bottoms ids, then every accessory id. For example `varsity-jacket|striped-joggers|hat-top,collar-ruff`.

- It is written only by the server, from the profile look. Players never send it.
- `data.Acc` is already a comma string of `Config.Accessories` ids (not a table), so it is written as it is.
- A transformed look (a form outfit) leaves the last `NHWear` as it was. NPCs never get one.
- `Config.Cliques.ParseWear` reads it back as `{ Top, Bottoms, Acc }`.

### Taste

Each clique in `Config.Cliques.Defs` has `Taste = { Likes = { Rule }, Mocks = { Rule } }`. A rule is one of
`{ Id = "hat-top" }`, `{ Kit = "C" }`, `{ Slot = "Familiar" }` or `{ Top = "varsity-jacket" }`. Today every rule is an
`Id`. A clique never likes something its rival likes.

| Clique | Likes | Mocks |
|---|---|---|
| Vigil | watch-pocket, lantern-candle, tube-scroll, coat-scholar, coat-lamplighter, book-strap, pin-vigil | hat-fascinator, mask-gilt, jacket-smoking, parasol-lace, pin-court |
| Court | hat-top, mask-gilt, clasp-opera, jacket-smoking, ring-bat-signet, parasol-lace, hat-fascinator, pin-court | coat-lamplighter, bag-messenger, tube-scroll, cloak-oilskin, pin-vigil |
| Athletes | jacket-varsity, pin-athletes, scarf-knit-crimson, bag-messenger | grimoire-chained, case-violin, collar-ruff, parasol-lace, pin-ink |
| Delinquents | coat-delinquent, pin-delinquents, mask-grille, pauldrons-blackened, gorget-steel | sash-prefect, tie-bow, umbrella-crook, book-strap, pin-ordinary |
| Pack | necklace-wolf-fang, fur-torn, mask-wolf, torc-moonstone, jacket-hunting, pin-pack | collar-choir, mask-wax, pendant-crystal, pin-choir |
| Ordinary | umbrella-crook, cloak-oilskin, tie-school, coat-cardigan, coat-cadet, pin-ordinary | mask-bone, pendant-scythe, crossbow-hunter, pin-delinquents |
| Choir | collar-choir, collar-ruff, mask-wax, pendant-crystal, halo-rune, pin-choir | mask-wolf, necklace-wolf-fang, hat-witch, grimoire-chained, pin-pack |
| Ink | mask-fox, mask-moth, mask-domino, backpack-batwing, scarf-knit-violet, bag-satchel, pin-ink | jacket-varsity, sash-prefect, sash-head, tie-school, pin-athletes |

### Verdicts

`Talk.Outfit(S, Player)` returns `(Verdict, PieceName)`. The first match wins:

| Verdict | When |
|---|---|
| `FullLook` | the top is one of this clique's tops (`Look.Tops`, `Look.FemaleMatchTops`, or `Look.Civ.Tops`) and the bottoms are one of its bottoms (`Bottoms`, `FemaleBottoms`, `FemaleMatchBottoms`, or `Civ`) |
| `RivalLook` | the top is one of the rival clique's tops, and **no other clique wears it**. `black-blazer` (Court and Choir) and `ivory-polo` (Ordinary and Choir) are shared, so they never count as a rival's colours |
| `Likes` | a worn piece matches a `Likes` rule (`{Piece}` is that piece) |
| `Mocks` | a worn piece matches a `Mocks` rule (`{Piece}` is that piece) |
| `nil` | nothing to say |

- **Within a side,** rules are checked in the order written, so earlier rules win.
- **`Look.FemaleMatchTops`** is a new key that only the outfit check and the dress code read. It holds the girls'
  versions of each clique's school top (for example Vigil `vigil-vest-f`, Athletes `cheer-uniform` and `track-jacket`).
  It is separate from `Look.FemaleTops` because the NPC dressers (`Schedules`, `CliqueFights`) read `FemaleTops`: a
  first version that set `Look.FemaleTops` changed what NPC girls wore, so it was renamed. `outfit.luau` fails if any
  clique has a `Look.FemaleTops` again.
- **`Look.FemaleMatchBottoms`** is a new key that only the outfit check reads. It holds the girls' bottoms that count
  towards a clique's look (Athletes `cheer-skirt`, Delinquents `delinquent-long-skirt`, Pack `forest-tartan`). It is
  separate because the NPC dressers read `FemaleBottoms`, and changing what NPC girls wear was out of scope.
- **Students with no clique** have no taste. They remark on one random accessory you wear, always as `Likes`, from
  Generic's neutral "nice hat" lines, 15% of the time.
- **Mocks** lines must read right for every piece in that clique's list (see the writing rules).

## The dress code

`Social.Cliques.Dressed(Player, Clique)` is true when **any** of these holds:

- you wear a top from the clique's `Look.Tops`, `Look.FemaleMatchTops` or `Look.Civ.Tops` (read from `NHWear`,
  through `Config.Cliques.WearsTop`);
- your standing tier with the clique is `Friendly` or `Respected`;
- you are a member of the clique.

An unknown clique counts as dressed.

**`UseAvatar` players** (who wear their Roblox avatar) stamp an empty top and bottoms in `NHWear`, so for them only
standing (Friendly or better) or membership passes the dress code.

**Where it applies**

- **In-person quests.** `Quests.CanStart` returns `false, "DressCode"` for a quest with `Def.Clique` that is not a
  `Dare`, `Job` or `Showdown`. Jobs are members-only already, and dares arrive by phone. The leader's dialogue
  (`Social.Dialogue`) shows the `[Quest]` choice, and picking it makes the leader say a `DressCode` line instead of
  the offer (`ctx.DressLine`, through `Talk.Line`). Dress up, reopen the conversation, and the offer appears. Other
  callers of `CanStart` (the phone, clique events, auto-start) never see the reason, because they only ask about dares
  or quests with no clique.
  - **Which quests:** `CanStart` gates on `Def.Clique or Def.Requires.Clique.Id` (the leader quests only carry
    `Requires.Clique`). So **any future quest with a clique standing requirement is dress-gated too**, unless it is a
    `Dare`, `Job` or `Showdown`.
- **The leader's "!" marker is kept** for a player who is not dressed. They still need to be drawn to the leader to
  hear the line, so `Why == "DressCode"` counts as an offer in the quest seals.
- **Night Study** (the Vigil's Archive perk, `Social.Hangouts.OnStudy`) is refused with a Vigil `DressCode` line in a
  notification titled "Not dressed for the Archive", until you wear a Vigil top, are liked, or a member. The check fails open, so an
  error never locks anyone out.
- **Walking in.** When someone who isn't dressed walks into a clique's hangout, the nearest student of that clique within
  30 studs says a `DressCode` line: once per visit, and at most once every 120 s per player (`dressWatch` in
  `StudentBrain`, which pcalls each player so one error never stops the watch).
  - **How a hangout is found:** the boxes in `workspace.Regions` (named by `Def.Hangout`) are matched by their X/Z
    footprint, from 20 studs under the box's bottom face to 6 over its top face. Combat Test's boxes float 11 to 16
    studs above a floor near y 1, so a plain "inside the box" check never matched a player on the floor. The boxes were
    left where they are because turf fights and `Features.Regions` use them too.

**In practice:**

- **Leader quests:** the gate only bites at Neutral standing. Wary and Hostile players are already refused by
  `QuestOpen` (the quests' standing requirement), and Friendly players pass. Dressing the part is how a Neutral player
  gets a quest before the clique likes them.
- **Night Study has no standing gate.** The dress code is its only clique check, so a Hostile player in a Vigil top
  gets in. This is a known consequence, flagged for the owner to rule on.

## How to add or change things

### Add a line

1. Edit the right pool in `tools/line-matrix/CliqueTalk/<Clique>.luau`. Keep 3 to 5 lines per cell.
2. Run the coverage test for that module (below).
3. Install the module:
   ```
   python tools/line-matrix/install.py tools/line-matrix/CliqueTalk/Vigil.luau ReplicatedStorage.Config.CliqueTalk.Vigil > <scratch>/install.luau
   ```
   Pass the file's text to `execute_luau` in **Edit** mode. It should answer `installed ...: N b, checksum H`. The
   installer checks the checksum itself and never uses the shared `NHInstallBuffer`.

### Add a moment

1. Add its name to `MOMENTS` in `tests/coverage.luau`, and to `SUBS` if it has sub-keys.
2. Add the moment to **every** module (all 8 cliques and Generic), or coverage fails.
3. Add a call site in `StudentBrain`: `sayMatrix(S, "<Moment>", Player, Opts, Cooldown, FallbackPool)`. Always give
   today's pool as the fallback.
4. Add a row to the moments table above.

### Add a clique

1. Add it to `Config.Cliques` (`Defs`, `Order`) as described in `docs/Cliques.md`, with a `Look` and a `Taste`.
2. Write `tools/line-matrix/CliqueTalk/<Id>.luau`, named exactly like the clique id, and install it as a child of
   `Config.CliqueTalk`. Coverage reads the clique list from `Cliques.Order`, so it checks the new module at once.
3. Check that the clique never likes something its rival likes.

### Change a clique's taste

Edit its `Likes` and `Mocks` in `Config.Cliques` (`Defs[Id].Taste`; the repo copy is the `Taste` table in
`patches/ConfigCliques.json`). Then run `outfit.luau`, which checks every verdict and that no clique likes what its rival
likes. Check that each `Mocks` and `Likes` line in the clique's `Outfit` module reads right for each new piece.

### Change something that isn't a line

`tools/line-matrix/patches/*.json` hold the edits made to existing scripts. Apply a changed one with `multi_edit` in
Edit mode, or re-apply the repo file with `install.py` for whole files (`Talk`, `StudentBrain`).

## Running the tests

All four are run with the Studio `execute_luau` tool in **Edit** mode (never during someone's Play session), by passing
the file's text as `code`. Each returns a string starting `PASS`, `FAIL` or `ERROR`.

| Test | Checks |
|---|---|
| `tests/coverage.luau` | Every module, moment, sub-key and attitude has a pool; 3 to 5 lines per pool; 60 characters or fewer; only known placeholders; no "nil" (a backtick-interpolation sign); no banned gore words; every `Likes` and `Mocks` cell has a `{Piece}` line; no clique `Greet` uses `Any`. Set `ONLY` to a module name to check just that one. Expected: `PASS: 945 cells, 2289 lines` |
| `tests/talk.luau` | `Talk.Attitude`, `Pool`, `Pick` and `Line`: tier only, no tier, no player, fought a step down, met often a step up (never to Respected), member is at least Friendly, fallback to Generic, placeholders filled, stand-in students |
| `tests/outfit.luau` | `ParseWear`, and `Talk.Outfit` verdicts for each clique: full look, rival look, a top the rival shares with another clique (no rival look), liked piece, mocked piece, nothing; plus no clique likes what its rival likes, no clique sets `Look.FemaleTops`, and every `FemaleMatchTops` / `FemaleMatchBottoms` id exists |
| `tests/wear.luau` | Dresses a dummy rig with `ApplyTo` and reads `NHWear`. Expected: `PASS varsity-jacket|striped-joggers|hat-top,collar-ruff` |

The tests that clone a module (`talk`, `outfit`, `wear`) require a copy, so they see the installed source, not a cached
one. Note that a `require` from `execute_luau` is its own module copy: it cannot see the live student records. To check
the live brain, use a throw-away Play-only script (see `tools/line-matrix/PLAYTEST.md`).

## Writing rules

For anyone writing new clique lines. These came out of the review rounds on the first set.

**Format**
- **Amount:** 3 to 5 lines per cell. Fill every moment for every attitude, or give `Any` when the attitude makes no
  difference (`Bump` and `Shoved` often don't).
- **Length:** 60 characters or fewer, so a bubble fits on one line. The check runs on the **raw** line, so keep
  placeholder lines short enough that they stay at 60 or under once filled with the longest name: `{Rival}` and
  `{Clique}` names, and `{Piece}` up to about 25 characters (for example "crimson-banded top hat", "headmaster's
  greatcoat").
- **Placeholder lines go in double quotes.** `"Nobody picked you, {Name}."` is right. In Luau a backtick string
  interpolates `{Name}` itself, and with no local called `Name` it becomes "nil". Lines with no placeholder may use
  either quote. Coverage fails any line that contains "nil".
- **Voice:** each clique keeps the voice its `Lines` and `Reactions` already have. Vigil: records and lamps. Court:
  money and manners. Athletes: sport. Delinquents: turf and threats. Pack: the moon and scent. Ordinary: nervous common
  sense. Choir: hymns and blessing. Ink: art and pranks.
- **Vary motifs.** Don't reuse one catchphrase across many moments.
- **Time of day:** watch assumptions in lines that can fire at any time ("sun's up soon", "blocking the sun").

**Placeholders**
- `{Rival}` and `{Clique}` fill with display names that **start with "The"** ("The Crimson Court", "The Vigil", "The
  Athletes"). Check the real `Defs[Id].Name`. Use them at the start of a sentence or as a possessive ("{Rival}'s
  colours?", "{Clique} would be proud."). Never after a preposition or adjective ("go back to {Rival}", "Proper
  {Clique}", "Dressed like {Rival}"): it reads "to The X".
- Plural names (The Athletes, The Delinquents) take a bare apostrophe, so avoid the possessive with them and start the
  sentence with the name.
- `{Piece}` is always "the/that/your {Piece}", never "a {Piece}" (it breaks on vowels and plurals).
- A `{Piece}` line in `Likes` or `Mocks` must read right for **every** piece in that clique's `Taste` list (look the ids
  up). Don't assume it is a jacket, a sash or "official" gear.
- Wardrobe references must match the clique's real `Look` tops and bottoms and its `Taste` ids.

**Races**
- Insults, digs and accusations aimed at a race (Werewolf, Vampire, Ghoul, Wraith, Priest, Human) come **only from
  Hostile or Wary** pools. Friendly and Respected get their own kinder pools for every race.
- Keep `Any` lines free of race digs: `Any` is what Neutral (and any attitude without its own pool) hears.
- `Transformed` lines are **form-neutral**. The moment fires for every beast form, so don't name a form ("big dog",
  "claws") a vampire or wraith wouldn't match.
- No real-world slur or slur-adjacent word (for example "mutt"), even aimed at a monster form. No skin-colour insults
  ("pale", "grey") even at monster races.

**Content and moderation** (the owner's account has a moderation warning)
- No gore and no blood words, no slurs, no innuendo, no Bully (the game) names, places or lines.
- Nothing that reads flirty, possessive or strip-tease ("Take it off", "You're mine", "Sit for me").
- No home invites ("stay at mine"), no off-platform contact ("text me"), no stick-up or weapon-implying phrasing
  ("hands where I can see 'em"), no predatory framing ("easy pickings"), and no real-world pejorative for a group
  ("holy roller"), even aimed at a game race.

## Not done, and not tested

- **The Map is not ported yet.** It needs Map cliques and the standing service first.
- **Not tested in play** (the Edit-mode tests cover their lines and pools, not the live moment):
  - **`Transformed`, `Hurt`, `Night` and `FullMoon`** greetings.
  - **`Race` lines for any race but Human** (the test slot is Human).
  - **`Flee` and `FightSeen` with the test player as the fighter** they talk about.
  - **Re-entry at floor level.** After the `hangoutOf` footprint fix, one walk-in line at floor level was seen; the
    "no second line on a quick re-entry" rule was only proven before the fix, with the player raised into the box.
  - **A pure `Greet.Hostile` line after the strong-attitude fix.** The Wary cells were seen in the re-test; the Hostile
    one only in the earlier run.
  - **A second player.** Two players' memories and one student remarking to two players were not tried (Studio solo).
  - **Mutters from a student with no clique.** Every Combat Test brain student has a clique (the default is
    "Ordinary"), so the play test cleared one student's clique to check greetings and crowd lines (they fell back to
    today's pools and Generic as designed). Its mutter never ran, because that student was stuck on a path. Mutter is
    unchanged by this feature.
  - **The real Wardrobe UI.** Looks were applied server-side with `ApplyTo`; the Wardrobe remote shares that code.
- **Follow-up, out of scope: `Features.Regions.Inside` has the same floating-box blind spot** that the walk-in dress
  code worked around. It checks the same `workspace.Regions` boxes with a 6-stud margin, so a player on the floor is
  never "inside" a hangout box in Combat Test. Fix by moving or resizing the boxes to reach the floor, or by matching by
  footprint as `hangoutOf` does. Check the Map place's boxes too.
- **Small known quirks:** a shove's first line is the old Sprint pool (by design: it plays as the reaction starts, and
  the clique's `Shoved` line follows when they turn round); the dialogue hub keeps a stale `[Quest]` choice until it is
  reopened after changing clothes; Hostile students often say stare and flee lines (from the senses) rather than a
  greeting.
- **Not in this build:** moments for systems that don't exist yet (curfew, holidays, "saw you break a rule", rumours),
  and outfits changing standing (the owner chose dress codes instead).
