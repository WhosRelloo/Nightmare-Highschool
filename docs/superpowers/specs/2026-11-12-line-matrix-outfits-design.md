# Line matrix + outfits: design

**Date:** 2026-11-12
**Place:** NH Combat Test (98950102230473) only. The Map comes later, after it has cliques and standing.
**From:** concepts 1 and 2 in `docs/Gameplay-and-NPC-Concepts.md`.

**Owner's answers:**
- Combat Test first.
- Students talk about what you wear, and hangouts have dress codes.
- Under a dress code, members won't deal with you, but you can still walk in.

## Goal

What a student says should depend on three things:
- **their clique:** each clique has its own way of talking;
- **how they feel about you:** your standing with their clique, shifted by their own memory of you;
- **the moment:** a greeting, a bump, a fight, the moon, and so on.

Students notice what you wear, through each clique's taste. A clique's hangout gives its in-person deals only to
players who are dressed the part, already liked, or members.

## What exists today (Combat Test)

**Students**
- Students are run by `ServerScriptService.Services.AI.StudentBrain`. Its lines live in its child
  `StudentBrain.Lines`.
- Each student `S` may have `S.Clique`.
- `S.Memory[UserId]` holds `Met`, `Greeted` and `Fought`.

**Choosing a line today**
- The brain calls `say(S, Pool, Cooldown)`, which runs `Lines.Pick(S, Pool, ctx())`.
- `greeting()` already uses `Def.Reactions[Tier]` 60% of the time. The tier comes from the
  `CliqueTier_<Clique>` player attribute.
- `mutterPool()` uses `Def.Lines` 40% of the time.

**Clique data**
- `ReplicatedStorage.Config.Cliques` covers 8 cliques: Vigil, Court, Athletes, Delinquents, Pack, Ordinary, Choir
  and Ink.
- Each clique has `Rival`, `Look` (`Tops`, `Bottoms`, `FemaleBottoms`, and an optional `Civ` set; all of them
  Appearance ids), `Lines` and `Reactions`.
- `Cliques.Tiers` are, from the top: Respected (60), Friendly (20), Neutral (-10), Wary (-40) and Hostile.

**Clothes**
- Players are dressed on the server by `Appearance.StartServer`, which calls `Appearance.ApplyTo(Character, Look)`.
- `Look` holds `Uniform` and `Bottoms` (indices into `Appearance.Uniforms` and `Appearance.BottomsList`) and `Acc`
  (accessory ids).
- Nothing is recorded on the character about what the player wears.
- `Config.Accessories.ById` lists 67 pieces. Each has `Name`, `Slot` and `Kit`.

**Deals**
- In-person quests go through `Social.Dialogue`, `Quests.Offers` and `Quests.CanStart(Player, Id)`, which returns
  `(Ok, Reason)`.
- Jobs are for members only. Dares arrive by phone text.
- The only perk tied to a hangout is the Vigil's Night Study (`Social.Hangouts.OnStudy`).

## Design

### 1. The lines: `ReplicatedStorage.Config.CliqueTalk`

**Files**
- `Config.CliqueTalk` is a ModuleScript. It returns a table of its child ModuleScripts:
  - one child per clique, named exactly like the clique: `Vigil`, `Court`, `Athletes`, `Delinquents`, `Pack`,
    `Ordinary`, `Choir`, `Ink`;
  - plus `Generic`.
- Each child returns `{ [Moment]: { [Attitude | "Any"]: { string } } }`.

**Attitudes**
- `Hostile`, `Wary`, `Neutral`, `Friendly` and `Respected`, the same names as `Cliques.Tiers`.
- `Any` holds lines that suit every attitude.

**Moments, and where each fires**

| Moment | Fires when |
|---|---|
| `Greet` | the greeting (replaces the time-of-day pools when a clique line is chosen) |
| `Bump` | Nudges MakeWay, a brush |
| `Crowded` | Nudges Space, you stand too close |
| `Shoved` | Nudges Shove |
| `FightSeen` | watching a fight (Gawk) |
| `Flee` | running from a fight near them |
| `Transformed` | you are in a beast form (today's Monster pool) |
| `Night` | a greeting after dark |
| `FullMoon` | a greeting on a full-moon night |
| `Race` | a greeting that remarks on your race; sub-keyed by race, see below |
| `Hurt` | a greeting when your Humanoid health is under 35% |
| `Outfit` | an outfit remark, sub-keyed by verdict, see section 3 |
| `DressCode` | members turn you away at their hangout, see section 4 |

**`Race`** is keyed `[Race][Attitude|Any]`, using the races in `Lineage`.

**Placeholders**, filled by the existing `Lines.Fill` plus three new ones:

| Placeholder | Becomes |
|---|---|
| `{Name}` | the player's first name (as the clique greetings use today) |
| `{Piece}` | the piece's name in lower case (`crimson-banded top hat`) |
| `{Clique}` | the student's clique display name |
| `{Rival}` | the rival clique's display name |

**Writing rules**
- **Amount:** 3 to 5 lines per cell. Every clique fills every moment for every attitude, or gives `Any` when the
  attitude makes no difference (`Bump` and `Shoved` often will).
- **Length:** 60 characters or fewer, so a bubble fits on one line.
- **Content:**
  - No gore and no blood (the owner's account has a moderation warning).
  - No slurs and no innuendo.
  - No Bully names, places or lines.
- **Voice:** each clique keeps the voice its `Lines` and `Reactions` already set:
  - **Vigil:** records and lamps.
  - **Court:** money and manners.
  - **Athletes:** sport.
  - **Delinquents:** turf and threats.
  - **Pack:** the moon and scent.
  - **Ordinary:** nervous common sense.
  - **Choir:** hymns and blessing.
  - **Ink:** art and pranks.
- **Generic** fills every moment for students without a clique.

### 2. Choosing a line: `StudentBrain.Talk`

`Talk` is a new ModuleScript, a child of `StudentBrain`. It has three functions.

**`Talk.Attitude(S, Player): string`**
1. Start from the player's `CliqueTier_<S.Clique>` attribute. Without a clique or an attribute, start from
   `Neutral`.
2. A member of `S.Clique` (`CliqueMembership.IsMember`) is at least `Friendly`.
3. Memory moves the attitude one step:
   - **down** if `S.Memory[UserId].Fought` is less than 300 s ago;
   - **up** if `Met >= 4`. This step can never go past `Friendly`, so `Respected` comes only from standing.
4. The result stays between `Hostile` and `Respected`.

**`Talk.Pick(S, Moment, Player, Sub?): string?`**

`Sub` is the race for `Race` and the verdict for `Outfit`. The lookup tries, in order:
1. clique `[Moment]([Sub])[Attitude]`
2. clique `[Moment]([Sub]).Any`
3. Generic `[Moment]([Sub])[Attitude]`
4. Generic `[Moment]([Sub]).Any`
5. `nil`, so the caller uses today's pool. Nobody ever goes silent.

The chosen pool goes through the existing `Lines.Pick(S, Pool, ctx())`, so the rules against repeating a line still
hold. The text then goes through `Lines.Fill` with the new placeholders.

**`Talk.Outfit(S, Player): (Verdict?, PieceName?)`**: see section 3.

**How the brain uses it**

- **`greeting()`**, in this order:
  1. The `Wary` override when the student saw you fight. As today, but through `Talk.Pick(S, "Greet", ...)` with the
     attitude capped at `Wary`, so a clique speaks in its own voice and a `Hostile` one stays `Hostile`. It falls back
     to today's `Wary` pool.
  2. An outfit verdict, 35% of the time when there is one, with a cooldown of 600 s per student per player.
  3. `Hurt`, 50% of the time when health is under 35%.
  4. `Transformed`, when the player is in a beast form (`Appearance.FormOf(Character)` returns a form).
  5. `Race`, 30% of the time.
  6. A clique `Greet`, 60% of the time for a clique student (this replaces today's `Def.Reactions` path).
  7. The existing `Again` and `Often`.
  8. `Night` or `FullMoon` through Talk, falling back to today's pools.
  9. The existing time-of-day greeting.
- **Nudges** (`Nudges.Handle`): `MakeWay` says `Bump`, `Space` says `Crowded` and a shove says `Shoved`, each
  falling back to today's pools. The bump lines get a `Player` argument where the record has one.
- **Gawk and Flee** use `FightSeen` and `Flee`, with today's pools as fallback.
- **Mutter is unchanged.** It still uses `Def.Lines` and does not depend on a player.

### 3. Outfits

**Recording what you wear**
- In `Appearance.ApplyTo`, when the character is not an NPC and the look is not a form outfit (`FormOutfit`), the
  server sets the character attribute `NHWear`:
  - a comma list of the top id (`Appearance.IdOf("Uniforms", Uniform)`), the bottoms id, and every accessory id in
    `Acc`.
- A form outfit (a transformed look) leaves the last `NHWear` as it was.
- Players never send `NHWear`. Only the server's `ApplyTo` writes it, from the profile look.

**Taste**
- Each clique in `Config.Cliques.Defs` gets `Taste = { Likes = { Rule }, Mocks = { Rule } }`.
- A `Rule` is one of `{ Id = "hat-top" }`, `{ Kit = "C" }`, `{ Slot = "Familiar" }` or `{ Top = "varsity-jacket" }`.
- Each clique gets 3 to 8 rules on each side, chosen from the 67 pieces by theme.
- A clique never likes something its rival likes.

**`Talk.Outfit(S, Player)`** reads `NHWear` from the player's character. Verdicts, first match wins:

| Verdict | When |
|---|---|
| `FullLook` | the top is in this clique's `Look.Tops` (or `Look.Civ.Tops`), and the bottoms are in its `Bottoms`, `FemaleBottoms` or the Civ ones |
| `RivalLook` | the top is in the rival clique's tops |
| `Likes` | a worn piece matches a `Likes` rule (`{Piece}` = that piece) |
| `Mocks` | a worn piece matches a `Mocks` rule (`{Piece}` = that piece) |
| `nil` | nothing to say |

Students without a clique use Generic's `Outfit` only for `Likes` and `Mocks`. Generic has no taste table, so these
students remark only on a random worn accessory, with neutral "nice hat" lines. This happens 15% of the time.

### 4. Dress codes

**`Social.Cliques.Dressed(Player, Clique): boolean`** is true when any one of these holds:
- the player wears a top from that clique's `Look.Tops` or `Look.Civ.Tops`;
- the player's tier with the clique is `Friendly` or `Respected`;
- the player is a member of the clique.

**Where it applies**

- **In-person quests:** in `Quests.CanStart`, a quest with `Def.Clique` that is not a `Dare`, `Job` or `Showdown`
  returns `false, "DressCode"` when `Dressed` is false.
  - Jobs are already members-only, so they always pass.
  - Dares come by phone and are not gated.
  - `Social.Dialogue` handles the `DressCode` reason: the giver says a `DressCode` line from its clique (through
    `Talk.Pick` with a stand-in student record `{ Clique = Def.Clique }`) and does not offer the quest.
- **Night Study:** `Hangouts.OnStudy` refuses with a Vigil `DressCode` line, shown in the same notification it uses
  today, when `Dressed(Player, "Vigil")` is false.
- **Walking in:** when a player who isn't dressed enters a clique's hangout zone (the zones `CliqueFights` already
  uses), the nearest member of that clique within 30 studs says a `DressCode` line. It says it once per visit, and at
  most once every 120 s per player.

**In practice**
- The gate only bites at Neutral standing. Wary and Hostile players are already refused by the existing standing
  checks, and Friendly players pass.
- Dressing up is how a Neutral player gets in the door before the clique likes them.

## Files

**Combat Test (Studio)**
- New: `ReplicatedStorage.Config.CliqueTalk`, with 9 child modules.
- New: `ServerScriptService.Services.AI.StudentBrain.Talk`.
- Changed:
  - `StudentBrain`: the greeting, Gawk and Flee call sites;
  - `StudentBrain.Nudges`: line calls only, no change to movement;
  - `ReplicatedStorage.Config.Cliques`: `Taste`;
  - `ReplicatedStorage.UI.Appearance` (`ApplyTo`): `NHWear`;
  - `Social.Cliques`: `Dressed`;
  - `Quests.Quests` (`CanStart`);
  - `Social.Dialogue`;
  - `Social.Hangouts`;
  - the hangout-entry hook in `Social.CliqueFights` or `StudentBrain`, wherever the zone check is already done.

**Repo mirror**
- Code: `tools/line-matrix/`.
- Docs: `docs/Line-Matrix.md` (how to add lines and taste), plus a CHANGELOG entry.

## Failure handling

- **Missing data falls back.** A missing clique module, moment, attitude or `NHWear` makes `Talk` return `nil`, and
  the caller falls back to today's pools. It never errors.
- **Calls are wrapped.** `Talk` calls from the brain are wrapped in `pcall`, as `Nudges.Handle` is today.
- **Stand-in students work.** A stand-in student such as `{ Clique = ... }`, with no `Memory`, gets its attitude from
  standing alone.
- **Bad strings are skipped.** If a placeholder can't be filled (no name, no piece), that line is skipped and another
  is picked from the same pool.

## Testing

1. **Coverage (Edit mode).** For every clique (plus Generic), every moment and every attitude, `Talk.Pick` with a
   stand-in student returns a string.
   - It reports any cell that falls through to Generic. The target is none for the 8 cliques.
   - Every line must be 60 characters or fewer and contain no `{` left unfilled.
2. **Outfit verdicts (Edit mode).** Stand-in characters with set `NHWear` values give the expected verdict for each
   clique: full look, rival look, liked piece, mocked piece and nothing.
3. **Play test on slot 4 "Testy"** (with `SlotCount = 4` and `NHTestNoMenuKeys`, then both put back):
   - wear the Athletes look, then the Ink look, and hear both cliques react;
   - set standing to each tier through TestBridge and hear the greeting tone change;
   - with Neutral Vigil standing and no Vigil top, Night Study is refused with a line; with a Vigil top it starts;
   - a Neutral-standing leader quest is refused with a `DressCode` line, then offered once dressed;
   - bumps, crowding and shoves near clique students use clique lines.
4. **No regressions.** Ambient students without a clique still greet, mutter and react as before.

## Not in this build

- **The Map port.** It needs cliques on Map students and the standing service first.
- **Moments for systems that don't exist yet:** curfew, holidays, "saw you break a rule" (concept 9) and rumours
  (concept 3).
- **Outfits changing standing.** The owner chose dress codes instead.
