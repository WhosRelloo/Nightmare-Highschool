# Cliques Phase 4: clique events (design)

Date: 2026-11-04. Owner's picks: all four events (pranks, rumble days, a bulletin, dares), rumbles about every 3 in-game days, players can prank too, dares by text **and** in person. Order of the next phases (owner): **events (this), then leader showdowns (friend or foe), then joining a clique.**

Builds on Phase 2 (`Social.CliqueFights`: fighters, scuffles, the hall monitor, fight lines) and Phase 3 (turf holding, leader quests, rewards). Release: **1.33.0**.

## 1. Pranks (`Services.Social.CliquePranks`, new)

**Prank spots.** Each hangout gets 2 prank spots, made at runtime from its `NHCliqueSpot` parts (the two farthest apart), as invisible anchors in `workspace.NHCliqueAreas.PrankSpots` with `NHPrankSpot = <clique>`. The builder can place real ones instead (any part with that attribute is used, and then none are generated for that clique).

**Messes** (stand-ins from the school's own art, cleaned by `Clean` or at 6 AM):

| Kind | Looks like |
|---|---|
| Tag | The prankster clique's slogan in its colour, in marker text (`Font.PermanentMarker`) on a SurfaceGui on the floor |
| Stink | Green smoke (the combat dust texture, tinted) and a "stink" bubble when students pass |
| Trash | The school's TrashCan model on its side, with scattered paper |

A mess is in `workspace.NHCliqueAreas.Messes`, with attributes `Victim`, `By` (clique) and `ByPlayer` (UserId, for player pranks). Students of the victim clique within 25 studs say a `Pranked` line.

**NPC pranks.** At Break, Lunch, After School and in the Evening, at most every `PrankEvery` (360) s and only when a student is within 120 studs of the target:
- a member of one side of a rival pair (a `SpawnFighter` from CliqueFights, peaceful until hit) walks to a prank spot at the rival's hangout, works for `PrankTime` (6) s with a "Shh" line, leaves the mess and walks off.
- **Stop it:** hit them before they finish: they drop the prank and fight you. Each rival you put down this way: `+6` with the victims (`PrankStop`). The usual −8 for downing a member applies.
- **Help:** hold E on the prank spot while they work (prompt "Keep watch"): they finish twice as fast; `+6` with the pranksters, `−6` with the victims (`PrankHelp`).
- **Clean:** hold E (3 s) on a mess: `+3` with the victims (`PrankClean`), once per mess.

**Your pranks.** A **Prank kit** from the concession stand (15 Yen, discounts apply; at most 3 a day, `KitsPerDay`). With a kit, hold E (4 s) on another clique's prank spot (prompt "Prank"):
- the mess goes down with your name on it (seen in the bulletin as "someone");
- `−15` with the victims, `+8` with the victims' rival (`PrankMine`). (The automatic rival share from Social.Cliques is skipped for this one, so it isn't counted twice.)
- **Witnesses:** `HallMonitor.CheckWitness(Player, "Vandalism")` (Recognized = a Vandalism violation now, Spotted = the monitor comes). On top of that, a victim member within 20 studs who can see you starts a confrontation (`CliqueFights.Confront`).
- A spot with a mess on it can't be pranked again until it's cleaned.

## 2. Rumble days (`CliqueFights.StartRumble`)

- **Choosing:** at 6 AM, if it's been at least `RumbleEveryDays` (3) days since the last one, pick a rival pair (the one with the most scuffles in the last day, else random) and schedule a rumble for the **next** day's After School. Everyone gets a phone text and a toast: "The Pack and the Choir are settling it after school tomorrow, at the Commons." It's also in the bulletin.
- **The fight:** at the start of After School (once a player is within 160 studs of the venue, or 10 in-game minutes in): **3 waves of 3 a side** (`RumbleWaves`, `RumbleSize`) at the Commons (`RumbleVenue`). A side's next wave walks in when its current wave is all down. At most `RumbleTime` (240) s.
- **Staff:** after 60 s, `HallMonitor.Respond` sends a monitor; after 120 s, a second (the "teacher" wave; the HallMonitor has no teachers, so it's another monitor with a teacher line). When the second arrives, it ends ("Everyone, OUT!").
- **Winning:** the side with more fighters downed on the other side when it ends (or the side that ran the other out of waves). Same joining rules as a scuffle: `+6` per rival downed, `+15` (`RumbleWin`) if your side wins.
- **Prize:** the winners hold the losers' hangout for the next in-game day (`SetTurf`, as a turf war).
- Students of those cliques at the Commons watch (`NHScuffleAt`).

## 3. Bulletin (the Cliques app: tabs **Standing** and **Today**)

A `Kit.TabBar` at the top of the Cliques page. **Today** shows:
- **Turf:** each hangout held by someone else, and by whom.
- **Rumble:** the next one (who, where, today / tomorrow), or the live one with waves left.
- **Pranks:** live pranks, and messes not yet cleaned (which hangout, by which clique; "someone" for a player).
- **Feuds:** today's scuffles per rival pair, and who won.
- **Your dares:** each with its leader, its task, its progress and the time left.

Data: a new `NHCliques.Today` RemoteFunction (rate-limited like `Get`).

## 4. Dares

- **Pool.** `Config.Cliques.Dares`: each clique has 3 dare templates, made from the quest system's existing objective types, for example:
  - win a scuffle for us (`Scuffle`),
  - prank our rival (a new `Prank` objective, counted by CliquePranks),
  - a timed delivery to someone (`Deliver`, with a deadline),
  - down one of our rival's members (`Down`, if the quest system has it; otherwise Scuffle),
  - be at a place by a time (an area objective).
- **Quests.** Each template is a real quest in `Config.Quests` (Category `Dare`, `Giver` = the leader), with a new `Daily = true` flag: it can be started again on a later in-game day, and an unfinished daily quest is dropped at 6 AM (`Quests.ExpireDaily`).
- **Rewards:** `+6` to `+10` with the clique and 10 to 25 Yen, set per template.
- **Texts.** At 6 AM (and on joining, if not sent yet today), 1 to 3 leaders with standing Neutral or better each text you one dare. It goes to the new **Texts** app on the phone (a list of conversations, newest first, saved per slot in `PlayerData.Phone.Texts`, last 30) with a toast "Wren texted you". A text has **Accept** (starts the quest) and **Not today**. Accepted dares are in the journal and tracker as usual.
- **In person.** Each leader gets a dialogue choice "Got a dare for me?" (Neutral or better): it starts one more dare from that leader, once per leader per day.
- **Hostile leaders** never text you (that's for the showdown phase).

## 5. Testing hooks (`Studio.TestBridge`)

`Prank(byClique, victimClique)` (an NPC prank now), `PrankMine(name, victim)` (yours, skipping the kit), `Messes()`, `CleanAll()`, `Rumble(a, b, now?)`, `Dares(name)` (send today's texts now), `Today(name)`.

## 6. Out of scope (later phases)

Leader showdowns and the King of the School title (Phase 5); joining a clique (Phase 6). Real map art for prank spots and messes (the builder).

## Implementation order

1. Config (`Config.Cliques`: `Events` settings, `Dares`, lines `Pranked`, `Shh`; `Config.Quests` dare quests; `Config.Shop` / Items: the prank kit).
2. CliquePranks: spots, messes, NPC pranks, stop / help / clean, your pranks with the kit, witnesses.
3. CliqueFights: `StartRumble`, the 6 AM scheduler, staff waves, turf prize; expose `SpawnFighter`, `Leave`, `Aim`, `Say` helpers to CliquePranks.
4. Quests: `Daily`, `ExpireDaily`, the `Prank` objective; dare texts (server) and the dialogue choice.
5. Phone: the Texts app, the Cliques app's Today tab; `NHCliques.Today`.
6. Test hooks, then a Studio Play test of each event (no slot, after hours / after school), keyboard and gamepad.
