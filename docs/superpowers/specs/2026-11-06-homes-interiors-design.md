# Homes and interiors: design

**Status:** concept approved by the owner ("Good", 2026-11-06). This spec is for the owner's go before building.
**Owner's ask:** "a big kit for the player home interior, building interiors, house interiors, etc. ... me and the builder want a mechanic in the game where the players have a starting dorm room and can later purchase a place off campus (once we do that later). And I want the interiors to change automatically depending on the student's grades. And when a student is doing bad in school they'll receive a text from their parents saying they're cutting them off from allowance, etc."

## What exists already

- **Report cards** (`School.ReportCards`, 1.40): every Monday at 6 AM (or the next login) the finished week becomes a card: each subject's average letter (F to A+), attendance, conduct, Mr. Hale's comment, and the allowance, paid once: A/A+ 60, B 40, C 20, D/F 0, +20 for perfect attendance, halved after a detention. The Office texts that it's in (`Phone.AddText(P, { From, Body }, true)`).
- **The phone's Texts app** (`Features.Phone`), the **door kit** (`Features.Doors`, `NHDoor`), and the **furnishings, library, window, lamp and other prop kits** (Blender, 2048 PBR, the house style).
- There is **no dorm** in NH Combat Test or the Map place yet.

## 1. Homes

| Home | How you get it | Phase |
|---|---|---|
| **Dorm room** | every student, free, from day one | 1 |
| **Studio Flat**, **Townhouse**, **Manor** (off campus) | bought with Yen | 3 (when the owner says) |

- **Private copies.** A home is yours alone. The dorm wing has doors (tagged `NHHomeDoor`). Walking through yours takes you into your own copy of the room, built from a template in an out-of-sight area below the map (a grid of home slots, one per player in the server). One hallway serves the whole server, and no room is ever "taken".
- **Getting in and out:** the door's prompt reads "Enter your room" and plays the game's teleport veil (`Fx.VeilMove`). Inside, the room's own door says "Leave" and brings you back to the hallway door.
- **Visitors:** from the phone's Classmates app, "Invite to my room": the friend gets a text with a Join button, and lands in your room. You can send everyone out.
- **When you leave the server** your room copy is destroyed. Nothing about it is saved except what you own and its grade state (which comes from your report card anyway).
- **Off campus (phase 3):** an estate agent (a prompt or a phone app) sells the homes. Your parents won't co-sign the lease while they've cut you off (see 3).

## 2. The room follows your grades

The home's look comes from your **latest report card's average**, and changes on its own when a new card lands. Before your first card it's B (a fresh start).

| Card | State | The room |
|---|---|---|
| A+ / A | **Spotless** | made bed, certificates framed on the wall, a warm lamp, a healthy plant, books shelved, a trophy shelf (your beast trophies show on it) |
| B | **Tidy** | neat, a couple of things out |
| C | **Lived-in** | a jacket over the chair, books stacked, a coffee cup |
| D | **Slipping** | clothes on the chair, a dim bulb, a half-dead plant, papers on the floor |
| F | **A wreck** | clothes on the floor, pizza boxes, a flickering light, overdue notices pinned up, a dead plant, an unmade bed |

- **How:** every home template's props carry `NHHomeState` variants. One furniture set has tidy-to-messy versions (a made and an unmade bed, a full and an empty shelf, live and dead plants), and some pieces only appear in some states (pizza boxes, certificates). When a room is built or the card changes, only the right state's pieces are shown.
- When it changes, a toast: "Your room looks different. Your report card is in."

## 3. Parents' texts

A new **Mom & Dad** contact in Texts, messaging right after the Office's report-card text:

| Card | Their text (one of a few, original lines) | Allowance |
|---|---|---|
| A+ / A | proud: "We knew you could. A little extra this week." | the card's allowance **+20** |
| B | pleased | as the card says |
| C | "We expect better than a C, sweetheart." | as the card says |
| D | a warning: "One more card like this and you're cut off." | as the card says (D pays 0 already) |
| F, or a second D in a row | "That's it. We're cutting off your allowance until your grades come up." | **cut off** |

- **Cut off:** no allowance at all from your parents (including the attendance bonus) until a card of **C or better**, which brings it back with "We're proud of you. Allowance is back on." While cut off, they won't co-sign an off-campus lease.
- The allowance is still paid by `ReportCards`; it asks Homes whether you're cut off and adds the A bonus.
- **Saved:** `PlayerData.Housing.CutOff` (and the count of D cards in a row), through ProfileService only.

## 4. The kit (art)

Made in Blender in the house style (2048 sharp PBR maps, gothic, light on wood, on theme), in batches like the other kits, published under the group.

- **Phase 1, the dorm room:** walls, floor, ceiling, a window (from the window kit), the door (from the door kit), a bed (made / unmade), a desk and chair, a wardrobe, a bookshelf (full / sparse / empty), a rug, a desk lamp and a ceiling light (warm / dim / flickering), a plant (healthy / wilting / dead), and the state extras: framed certificates, a trophy shelf, clothes piles, pizza boxes, papers, overdue notices, coffee cups. A dorm-wing hallway piece with room doors, for the builder.
- **Phase 2, building interiors** (shared, not private, placed by the builder): a shop, the café, a bookshop and a general town-building set (counters, shelves, tables, stools, signs).
- **Phase 3, off-campus homes:** the Studio Flat, Townhouse and Manor sets, reusing the phase 1 state system.

## 5. Code

| What | Where |
|---|---|
| Homes, templates, states, prices | `ReplicatedStorage.Config.Homes` |
| Private copies, doors, visitors, the grade state | `ServerScriptService.Services.Features.Homes` |
| The allowance hook and the parents' texts | `School.ReportCards` (asks `Homes`) |
| Room templates | `ServerStorage.NHHomes.<Home>` (props tagged by state) |
| Saving | `PlayerData.Housing = { Owned = { "Dorm" }, Current = "Dorm", CutOff = false, DStreak = 0 }` |

## 6. Phase 1 build order

1. The dorm room kit (art), in batches, checked in Studio.
2. `Config.Homes`, `Features.Homes`: private copies, the hallway doors, getting in and out, visitors.
3. The grade states.
4. The parents' texts and the allowance cut-off in `ReportCards`.
5. A placeholder dorm wing in NH Combat Test (the builder makes the real one in the Map place).
6. Play-tests on slot 4 (each grade state, a cut-off and its return, a visitor), then the records.

## Not in this

- Moving or buying furniture (decorating), which can come later on top of this.
- Off-campus homes and buying them (phase 3, when the owner says).
