# Factions and Reputation: NH Combat Test

**Status:** two factions are built and verified in Studio playtests (single player): **The Vigil** and **The Crimson Court**. Each has its own leader with dialogue, a hangout, an activity, a mission, ranks and perks. The reputation scores, leader relationships, titles and the Factions panel (P) all work. Two more factions are listed as rumours only.

## Theme

Something is wrong with Nightmare Highschool, and two cliques have picked sides. The theme is set through flavour text only; no story secrets are revealed.

| | The Vigil | The Crimson Court |
|---|---|---|
| Colour | candle gold | blood red |
| Who they are | students who dig through school records after hours and keep watch when the halls go dark (priest blood runs strong here) | the clique that runs the school after dark, or thinks it does (some really have fangs). They mark territory with crimson sigils. |
| Leader | **Ezra Vale**, Vigil Captain | **Vesper Crane**, Regent of the Crimson Court |
| Hangout | The Library Archive (candles, study table) | The Boiler Yard (boiler glow, crates) |
| You rise by | passing lessons, Night Study | marking walls unseen, escaping hall monitors, downing people |
| You lose standing by | getting caught skipping class | — |
| Initiation | earn a B or better in any lesson | mark a wall without being recognised |
| Activity | **Night Study**: a class minigame at the Archive table, after hours, once per in-game hour | **Mark the Walls**: paint sigils on 5 marked walls around campus, each once per in-game day |
| Mission | **Keep the Lamps Lit**: pass 3 different subjects in one in-game day → 40 standing, 30 Yen, title *Lamplighter* | **Bloodline Run**: mark 3 different walls in one class period unseen → 40 standing, 25 Yen, title *Night Prowler* |
| Trusted Member perk | **Vigil Pass**: once per in-game day, a hall monitor lets you off with a warning | **Shadowstep**: hall monitors lose track of you twice as fast |
| Inner Circle perk (needs a reputation score too) | **Blessed Scholar**: +50% Yen from passed lessons (needs Academics 40) | **Unseen**: witnesses must be twice as close to recognise you marking a wall (needs Intimidation 30) |

**Rumoured, not playable:** *The Ordinary* (humans who just want to graduate alive) and *The Hollow* (tied to whatever is under the school). They're listed in `Config.Factions.Planned` and in the panel's Rumours section.

## Ranks and standing (`Config.Factions`)

| Rank | Standing | Needs membership |
|---|---|---|
| Outsider | 0 | no |
| Prospect | 10 | no |
| Member | 30 | yes |
| Trusted Member | 70 | yes |
| Inner Circle | 120, plus the faction's reputation requirement | yes |

- **Before joining**, standing is capped at 29. The toast then tells you to talk to the leader.
- **Joining** needs Prospect standing and the initiation. It sets standing to at least 30, and Leader +10.
- **Rivals are exclusive.** Gaining X with one faction costs 0.25 × X with the other.
- **Leaving** keeps half your standing (max 29), costs Leader −15 and Trust −5. You can rejoin after 1 in-game day.
- **Popularity +3** for each rank reached *for the first time*, and once for your first join. Leaving and rejoining doesn't pay again.

**Standing sources:**

| Source | Faction | Amount |
|---|---|---|
| Lesson grade (class only, not practice) | Vigil | A+ 12, A 10, B 6, C 3, D 0, F −2 |
| Night Study | Vigil | A+ 8, A 7, B 5, C 3, D 1 |
| Caught skipping class | Vigil | −3 |
| Wall marked unseen | Court | 6 + the wall's risk bonus (0–4) |
| Wall marked but recognised (or spotted, then caught) | Court | 2 |
| Escaped a hall monitor | Court | 3, max 5 per day |
| Downed someone | Court | 2, max 5 per day |
| Hitting a leader | that leader's faction | −10 |

## Reputation (`Config.Reputation`)

Four school-wide scores, 0–100:

- **Popularity:** rank-ups, titles, joining
- **Intimidation:** downing (+2) and gripping (+3) people
- **Trust:** leaving a faction costs 5
- **Academics:** lesson grades (A+ 3 … F −1), Night Study +1

## Leaders and relationships

Ezra and Vesper are NPCs (`Services.Social.Npcs`) standing at `EzraSpot` and `VesperSpot`:

- Faction-colour name tag and role, a small glow, and a **Talk** prompt on **E**.
- They walk back to their post if pushed or dropped, and teleport back if dragged more than 60 studs away.
- They can be downed and gripped like anyone. They respawn 30 s after dying.
- **Hitting one:** relationship −20, standing −10, and the dialogue closes. Counted at most once every 8 s per player.

**Relationship** runs −100…100 and is saved per leader: Hostile ≤ −50, Rival ≤ −20, Acquaintance ≤ 19, Friendly ≤ 49, Trusted. Meeting a leader sets it to at least 5. Joining gives +10.

## Dialogue (`Services.Social.Dialogue`)

**Server authoritative.** The client only receives the current line and the replies that passed their conditions. Every reply is re-checked on the server before it runs:

- the session is current
- the reply index is valid
- you're within 16 studs of the NPC, who must be alive and not downed
- the reply's condition still holds

Walking away closes it.

**Trees are plain data:** `ServerStorage.Dialogue.<NpcId>`. Both leaders use `LeaderTemplate`, so adding a leader means writing their lines only.

**Leader menu:**

| Reply | When it's offered | What happens |
|---|---|---|
| About the faction | always | explains the faction |
| "I want in." | not a member | joins, or explains why not: not noticed yet, initiation not done, rival member, cooldown |
| "Any work?" | member | mission text and progress |
| "Seen anything strange / Heard any rumours?" | Friendly or better, or a member | a lore line |
| Apologise | relationship below 0, once per in-game day | +8 |
| Insult | not a member | −10 |
| Leave | member | asks to confirm, then you leave |
| Goodbye | always | closes |

First meetings open with an introduction, and Hostile players get a cold short menu.

**Client** (`Gui.Dialogue`): a dark box at the bottom with the speaker in faction colour, their role and your relationship, typewriter text (click it to skip), and numbered replies (keys **1–9**, click or tap). Backpack hotkeys are off while it's open.

## Factions panel (`Gui.FactionsPanel`)

Press **P**, or the **Factions** button on the left edge (for touch). It's titled *"Who's Who After Dark"* and shows:

- **Reputation:** your four scores and your equipped title
- **A card per faction:**
  - rank, standing and a bar to the next rank
  - what you still need to join
  - the leader and your relationship
  - the hangout and activity
  - the mission and its progress
  - perks, with ★ when unlocked
- **Titles:** Equip or unequip. The server checks you own the title, rate-limited to one request per 0.5 s.
- **Rumours:** the two planned factions

## Files

| Where | What |
|---|---|
| `ReplicatedStorage.Config.Factions` / `Config.Reputation` | all rules and text |
| `ServerScriptService.Services.Social.Reputation` | scores, relationships, titles, `SocialAction` (title equip) |
| `…Social.Factions` | standing, ranks, joining, perks (as player attributes), missions, all event hooks |
| `…Social.Pranks` | mark-wall prompts and witness checks |
| `…Social.Hangouts` | Night Study prompt |
| `…Social.Npcs` | leader NPCs, Talk prompt, attack penalty |
| `…Social.Dialogue` + `ServerStorage.Dialogue.{LeaderTemplate, Ezra, Vesper}` | dialogue engine and trees |
| `StarterPlayerScripts.Controllers.Gui.{Dialogue, FactionsPanel}` | client UI |
| `workspace.School.{Archive, BoilerYard, MarkWalls}` | hangouts and walls (placeholder geometry) |
| `Remotes.Packets` | `DialogueEvent`, `DialogueAction`, `SocialAction` |

**Saved data:** `PlayerData.Social`:

- `Factions[Id]`: Standing, Member, Rank, BestRank, Flags, Missions, Daily, PassDay, JoinedDay, LeftDay
- `Reputation`, `Relationships`, `Titles`, `Title`
- `Marks`: walls marked today
- `StudyHour`
- `DialogueDaily`

## Verified in Studio playtests (single player)

| What | Result |
|---|---|
| Vigil join path in dialogue | Intro → About → "I want in" refused (*not noticed*) → refused again (*initiation*) → **Joined** after the B grade. Standing 30, Ezra +10, Court then refused with *RivalMember*. |
| Real keys in dialogue | **2** opened the mission reply ("Keep the Lamps Lit… 0 of 3 today"), with screenshots of the box |
| Leaving | confirm → left. Standing 30 → 15, Ezra −15, rejoin refused with *Cooldown*. After 2 in-game days, rejoining worked. |
| Marking walls (evening, no monitor) | 2 walls painted, initiation flag set, the Vigil lost its 25% share, the same wall again was refused. Joined the Court through Vesper's dialogue. |
| Witness: monitor 8 studs away, Unseen on | **recognised**: +3 discipline points, +2 standing |
| Witness: monitor 18 studs away | **spotted**: chase, 0 standing. After escaping (1.8 s with Shadowstep) **+11** (6 clean + 2 wall bonus + 3 escape). |
| Bloodline Run | 3 walls in Period 3 → mission 1/3, 2/3, done. Title *Night Prowler* awarded and equipped. |
| Title equip | a click in the panel unequipped and re-equipped it (server attribute changed) |
| Attack penalty | hitting Vesper twice: relationship −20 and standing −10, applied once (rate limit) |
| Ranks and perks | Court 75 → Trusted + Shadowstep. 130 → still Trusted without Intimidation. Intimidation 30 → **Inner Circle + Unseen right away**. Vigil 75 → Vigil Pass. 135 + Academics 40 → Blessed Scholar and `LessonYenBonus = 1.5`. |
| Vigil Pass | the 1st truancy catch of the day: 0 points, pass used. The 2nd catch (next period): +2 points. |
| Night Study | refused during class. After hours: a Pop Quiz answered from the client: **A+**, sheet shows "Study session: passed / +8 The Vigil standing", math level unchanged. A 2nd try in the same hour was refused. |
| Factions panel | P opens it. Reputation, both cards, the mission "Complete", perks ★, titles and rumours all render (screenshots). |
| Errors | no script errors in any run |

**Bugs found and fixed during testing:**

1. **Join/leave farmed Popularity.** Each cycle re-paid the rank-up and join bonuses. They're now paid only the first time (`BestRank`, first join).
2. **Inner Circle waited for a standing change.** Reaching the Intimidation or Academics requirement didn't promote you until standing next changed. It now re-ranks when that score changes.
3. **A spotted mark paid out as "unseen" straight away.** It now waits: escape the chase and it counts as clean; get caught and it's the small "seen" amount.
4. **Leaders showed generic camo clothing.** The rig's clothing and BodyColors are removed so the faction tint shows.
5. **The panel didn't compile** (an extra `end` after an inline `if`). Found by compiling every new script before play.

**Not tested:**

- two players (e.g. rival members in one hangout, two people talking to one leader)
- mobile: the panel button and tap replies exist, but no phone test
- the Vigil mission *Keep the Lamps Lit* end to end. Its step runs from the same lesson event that the rest of the Vigil logic uses, and the progress readout works (0/3), but 3 lessons weren't played in one in-game day.
- the leaders' respawn after death

**Test tooling note:** `SetDiscipline` (TestBridge) changes saved data but not the `Suspended` / `DisciplineLevel` attributes until the next discipline event. Tests set those attributes by hand.

**Studio test profile now holds:** Vigil Inner Circle (Court left), the title *Night Prowler*, Academics 40, Intimidation 30, and a discipline record from the catch tests. This is Studio-only data. Use the `ResetSocial` and `SetDiscipline` bridge commands to clear it.

## Ideas for later

- Overhead title under the player's name (the `Title` attribute is already set)
- The two rumoured factions, once the story decides what's under the school
- Faction gear or uniforms instead of the placeholder tint
- Rival members fighting in hangouts → standing, using the existing `Downed.OnDowned`
