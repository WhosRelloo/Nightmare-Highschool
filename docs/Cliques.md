# Cliques

Added in 1.21.0 (Phase 1). The owner, 2026-11-03: the game is heavily inspired by Bully, so there should be cliques and groups, Bully-style, with our theme on them.

Every student belongs to a crowd with its own hangout, leader, rival, dress and lines. Each clique remembers how you've treated its members, and the phone's **Cliques** app shows where you stand with each one.

- **Config:** `ReplicatedStorage.Config.Cliques`
- **Server:** `Services.Social.Cliques`
- **Client:** the phone (`Controllers.Gui.Phone`) and `Controllers.World.Chatter`

## The eight cliques
| Id | Clique | Crowd | Hangout | Leader | Rival |
|---|---|---|---|---|---|
| Vigil | The Vigil | Scholars | The Archive | Ezra Vale | The Crimson Court |
| Court | The Crimson Court | Night elite | The Crimson Parlor (new) | Vesper Crane | The Vigil |
| Athletes | The Athletes | Jocks | The Gymnasium | Captain Rhys Thorne (new) | The Ink Club |
| Delinquents | The Delinquents | Greasers | The Back Lot | Bruno Vance | The Ordinary |
| Pack | The Pack | Bullies | The Den (new) | Dex Moreno | The Chapel Choir |
| Ordinary | The Ordinary | Regulars | The Commons (new) | Pip Larkin | The Delinquents |
| Choir | The Chapel Choir | Faithful | The Chapel (new) | Lucien Grey (new) | The Pack |
| Ink | The Ink Club | Artists | The Ink Studio (new) | Wren Ashby (new) | The Athletes |

- **The two factions are cliques too.** The Vigil and the Crimson Court are still joined, ranked and given missions through `Services.Social.Factions` (see Factions-and-Reputation.md). Their clique card also shows your faction rank.
- **The Ordinary** used to be a rumoured faction in `Config.Factions.Planned`. It's now a clique you can stand well or badly with, but not join.

## Members
NPCs carry the attribute `Clique`:
- **Scheduled students:** the 14 students get theirs from `Config.Cliques.Students`, by schedule index: 3 Ordinary, 2 each of Vigil, Court, Athletes and Ink, and 1 each of Choir, Pack and Delinquents. Their school clothes come from their clique's palette (`Look.Tops` / `Bottoms` / `FemaleBottoms`, all real `Appearance` ids).
- **Named NPCs:** `Config.Cliques.Npcs` maps the cast, the delinquents and the ambient students by name. `Services.Social.Cliques` tags them as they appear in `Live` and `NHAmbient`.
- **The three new leaders:**
  - Captain Rhys Thorne, "Athletes captain"
  - Lucien Grey, "Chapel Choir cantor"
  - Wren Ashby, "Ink Club ringleader"

  Each stands at the middle of their clique's gathering spots. They're built from the NPC rig with a full `NpcLooks` spec, their feet are measured onto the floor, and their name tags match the cast's. Their quests come in Phase 3.
- **Turf clothes:** each clique also has a `Civ` palette (Court, Delinquents, Pack). It's in the config only for now; the dress code still uses its own swap pools.

## Hangouts
Students go to their clique's hangout:
- **At Break:** everyone.
- **After school:** athletes go to their club (gym, field, pitch); everyone else goes to the hangout.
- **In the evening:** the students who stay.

At the hangout they walk to a free **gathering spot**, face the group, sometimes lean, chat a while, then move to another spot.

- **Spots** are parts tagged `NHCliqueSpot`, with the attribute `NHCliqueSpot = <clique id>`.
  - **Count:** 61 in all: Athletes 8, Court 8, Delinquents 8, Ordinary 8, Pack 8, Vigil 7, Choir 7, Ink 7.
  - **In existing places:** the Vigil's are in the Archive, the Athletes' are courtside in the gym, and the Delinquents' are on the Back Lot.
- **Taken spots:** a spot counts as taken while a student is walking to it.
- **Unreachable spots:** if nobody can walk to a spot, it's skipped for 2 minutes. Three of the Archive spots sit round a table where the pathfinder has no room.

### The five new places (stand-ins)
These are built in `workspace.NHCliqueAreas` from primitives and the school's props, in the school's style. **The builder replaces them with the real map.** Moving a hangout means moving its region box and its spots.

| Place | Where | What's there |
|---|---|---|
| The Commons | 135, −45 | 64 × 40 paving with low walls, a fountain, 4 hall benches, planters, topiaries, lamps, a notice board and a sundial |
| The Chapel | −40, 150 | 22 × 34 gothic stone with stained glass, gables, a bell tower and a gold cross; altar, candelabra, and pews made from hall benches |
| The Ink Studio | 50, 228 | 26 × 20 dark plaster splashed with paint; easels, framed paintings, a workbench, two warm lamps |
| The Crimson Parlor | 165, 228 | 34 × 24 damask; a sofa, armchairs, a chess table, a chandelier and banners |
| The Den | −236, −80 | a mossy clearing in the woods: a fire, a coal pile, logs, rocks, a keg and a cart |

Each place has a region card (Regions.md). The Parlor and the Den are Turf, so NPCs there dress in civilian clothes.

## Standing
Standing is how a clique's members see you, from −100 to 100. It's saved per slot in `PlayerData.Social.Cliques` (one number per clique, cleaned on every read).

| Tier | From |
|---|---|
| Respected | 60 |
| Friendly | 20 |
| Neutral | −10 |
| Wary | −40 |
| Hostile | below −40 |

- **Phase 1 source:** putting a clique member on the floor costs **−8** with that clique (`Downed.OnDowned`, with you as the attacker).
- **Rivals:** any change gives the rival clique the opposite of a quarter of it. Downing a Delinquent gives The Ordinary +2.
- **Notifications:** you get one when your standing changes ("−8 The Delinquents"). Crossing into a new tier adds a line, for example "They're wary of you now." or "They respect you now."
- **API:**
  - `Cliques.Get(player)` returns `{ [id] = value }`
  - `Cliques.Add(player, id, amount, reason?)`
  - `Cliques.Tier(value)`
  - `Cliques.State(player)` returns the list for the phone

## The phone app
The **Cliques** icon takes the Factions icon's place on the phone's grid. The factions panel still opens with **L** and from the app.

The app shows each clique as a card with:
- its colour stripe and name
- its crowd and hangout, and its tagline
- your standing on a bar running out from the middle (left for negative, right for positive), with the number and the tier
- its leader and its rival
- **The Vigil and the Crimson Court only:** your faction rank ("member" if you've joined) and a **Faction** button that opens the factions panel

The page refreshes while it's open when your standing changes.

- **Remotes:** `ReplicatedStorage.NHCliques` (attribute `Ready`)
  - `Get` (RemoteFunction, 4 calls a second at most) returns the list
  - `Changed` (RemoteEvent) fires when your standing moves

## Voice lines
Every clique has five lines of its own. A student in a clique says one of them about half the time, and the student or kind lines otherwise (`Controllers.World.Chatter`). Staff never use clique lines.

## Test hooks (Studio only, `ServerStorage.NHTestBridge`)
- `SchedulePlan(kind, name?, hour?)`: put every student on a plan now, for example `("Break", "Break", 9)`
- `ScheduleDebug()`: each student's index, clique, activity and seat
- `Cliques(name)`: the phone's list for a player
- `CliqueAdd(name, id, amount, reason?)`: change a player's standing

## Next phases
- **Phase 2:** members react to your standing: greetings, taunts, cold shoulders, scuffles between rivals, and the hall monitor stepping in.
- **Phase 3:** turf, leader quests and rank rewards for every clique.
