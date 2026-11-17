# 03. Story Bible (direction draft)

This is a direction for you to review, not final canon.
- **[CANON]** marks what the game already ships.
- **[PROPOSED]** marks new material that needs your approval.
- **[OPEN]** marks a decision that is yours to make.

The current story text is self-labelled "provisional", and your concept doc defines no storyline. So [CANON] means "in the game today", not "approved by you".

## 1. Existing canon (shipped, with sources)

| Fact | Source |
|---|---|
| Mira Holt sat in the back row of Room 102. She is being erased from memory and from the records. Her file reads "STATUS: COLLECTED". | `Config.Quests` (New Kid, The Empty Desk, After Hours), `Config.Cases.EmptyDesk`, `QuestSecrets` |
| Clue: "Room 102. Back row. Before they finish erasing her." Clue: "DON'T ANSWER ROLL CALL", carved with "M.H." | Clues LockerNote, DeskCarving |
| The Records Office keeps the original records, and the Night Custodian locks it each evening. | After Hours, `Config.Stealth` |
| 1893 is "the year the bell first rang by itself". A page from the 1893 records is missing. | Ezra, CliqueVigil2 "The Missing Page" |
| An east-wing bell rings at unscheduled hours, and the Vigil logs it. Pip dreams of a bell ringing with nobody there, and can't remember Mira's face. The old chapel bell cracked. | Ezra Lore, Pip, Sable |
| The basement doors lock from the inside every night, and no staff member has a key. | Vesper Lore, Dex |
| The Vigil keeps the lamps lit and "writes every one down". The Crimson Court rules after dark and marks walls. | Faction dialogue |
| There was a night of the fire at the north gate, and the old pitch was the churchyard field. | Coaches Dunmore and Mallory |
| Mortlake is "the first headmaster's line", and the Vauclair are the academy's patrons. | `Config.Clans` |
| Headmaster Corvin Ashgrave's portrait. Three founders, and the inscription "In the year of the Blood Moon the house was founded". A memorial to students lost on the night of the Blood Moon, October 1887. The Class of 1887 painting with one pale, see-through student. Cassius Vale (Vigil) and Corvin Crane (Court) duelling on the bell-tower stair. | Prop descriptions (`docs/School-Props.md`), art only |
| Six races: Human, Priest, Vampire, Werewolf, Ghoul, Wraith. Rites use the Blood Font, the Blood Ledger, the Cracked Bell, the Cold Mirror and an archive ward. | `ReplicatedStorage.Lineage`, rite quests |
| The cast: Ezra Vale, Vesper Crane, Dex Moreno, Pip Larkin, Bruno Vance, Rhys Thorne, Lucien Grey, Wren Ashby, Sable Vey, Coaches Varga, Mallory and Dunmore, Mrs. Okada, Mr. Hale, the Night Custodian, the substitutes (including Mr. Thaddeus Crane). | `Config.Npcs`, `Config.Stealth`, `Config.Substitutes` |

**Conflicts to settle [OPEN]:**
1. **Corvin:** Corvin Ashgrave (the Headmaster) and Corvin Crane (the Court twin) share a first name.
   - *Proposal:* keep Headmaster Corvin Ashgrave, and rename the twin to **Cassian Crane**.
   - *Or:* make it deliberate: the same man under two names.
2. **The bell:** 1887 (the Blood Moon losses) and 1893 (the bell rang by itself).
   - *Proposal:* both are true. 1887 is the founding catastrophe; 1893 is when the bell first rang without a ringer, the first sign that the seal works through attendance.
3. **Vesper's post:** the Boiler Yard or the Crimson Parlor.
   - *Proposal:* the Parlor by night, the Boiler Yard by day.
4. **Thaddeus Crane:** the substitute shares the surname Crane with Vesper.
   - *Proposal:* make it deliberate. He is a Court relative, and the Court keeps a man inside the staff.

## 2. The mythology direction: the Academy as a boundary [PROPOSED]

**One-sentence truth:** Nightmare Highschool was founded on a **Threshold**, a thin place between the living world and an *Unwritten* below. The school's real work is not teaching; it is **keeping a roll**. As long as a full roll of students answers the bell, the boundary holds.

| Concept | Proposed meaning | How the player meets it |
|---|---|---|
| **The Threshold** | The ground the school stands on. It sits nearest to the surface at the bell tower, the chapel and the Records Office basement. | Region ambience shifts, echo rooms, moon nights |
| **The Sealed Foundation** | Under the basement (the doors that lock from inside) is the seal: a well of names. | Chapter 3 |
| **The Attendance Bell** | The bell is the seal's instrument. Each roll call *binds* those who answer it to the school's protection. A student who answers when the bell rings at the wrong hour is **claimed**: written out of the ordinary record and into the Unwritten Archive. | "DON'T ANSWER ROLL CALL"; the 3 AM bell; the Chapter 1 twist |
| **The Unwritten Archive** | A second register of the claimed, kept by the school itself. It is the true version of the Records Office. | Archive pages (collectibles), Chapter 2 |
| **Forgotten Students** | The claimed. The world edits around them: photographs, memories, desks. Mira Holt is the newest. The pale student in the Class of 1887 painting is one of the oldest. | Mira; the photographs that change |
| **The Founders' Covenant** | Three founders made the bargain in 1887, the Blood Moon year: a roll of students in exchange for the boundary holding. The races were the founders' answer. Each bloodline was invited because it can stand near the Threshold. | Chapter 4 |
| **The Anchor Network** | People, objects and places that keep the roll: the Vigil's lamps, the Court's wall marks, the register, the bell. The factions are two halves of the anchor, and neither knows the whole. | Factions' quests, Chapter 3 |
| **Echo Rooms** | Places where a claimed student's last day replays: a classroom at the wrong hour, a hall with the old lighting. | Investigations, crisis nights. Built in existing rooms with lighting and sound only. |
| **The Unclaimed Locker** | Locker 113 holds what the claimed leave behind for whoever comes next. It is the first thing the player is sent to. | New Kid (already uses Locker 113) |
| **The False Explanation** | The official story: a fire at the north gate in 1887, and students "transferred" since. The Headmaster maintains it. | Gazette, staff dialogue, Chapter 2 |

**Why this works with what exists:**
- It explains every shipped clue: the erasure, "don't answer roll call", COLLECTED, the 1893 bell, the basement doors, the lamps, the wall marks, the 1887 memorial.
- It explains why the attendance mechanic matters in fiction.
- It explains why races live at this school.

## 3. Characters: motivations [PROPOSED unless marked]

| Character | Public face [CANON] | Hidden motivation [PROPOSED] |
|---|---|---|
| **Ezra Vale** (Vigil) | A scholarly record-keeper | The Vigil believes the roll must be kept *honestly*: write every name, so no one vanishes unrecorded. Ezra has been keeping a secret list of the forgotten. |
| **Vesper Crane** (Court) | A silky ruler of the night | The Court believes the boundary should be *managed*: let it take the ones nobody will miss. She is wrong about Mira, and it costs her. |
| **Mira Holt** | The erased girl | She worked out the bell, warned others ("DON'T ANSWER") and answered it herself to save someone. She isn't dead; she is *Unwritten*, and can be reached in echo rooms. |
| **Headmaster Corvin Ashgrave** | A portrait and an office (no NPC yet) | The Covenant's current keeper. Not a villain: he believes the roll is the price of every student's safety. He keeps the False Explanation. |
| **The Night Custodian** | The Records Office watcher | Nobody has seen his face clearly. He *collects*: he moves the claimed students' files. He is part of the school's machinery, not a man. |
| **Mr. Hale** | Chemistry, the voice of the report card | He remembers one claimed student (his own class, years ago) and drinks about it. He becomes an ally in Chapter 2. |
| **Pip Larkin** | A jumpy first-year | Mira saved Pip. That is why Pip can't remember her face. |
| **Sable Vey** | The seer | Sees the roll as cards. She knows who is next, and hides it. |
| **Dex, Bruno, Rhys, Lucien, Wren** | Clique leaders | Each gets one chapter thread: Lucien (the Priest line and the chapel), Wren (paints what she shouldn't know), Dex (delivers sealed letters at night), Bruno (the Ring is where the old gate stood), Rhys (the field is the churchyard). |

## 4. Race integration [PROPOSED]
**One campaign for everyone.** Each race *reads* key evidence differently: an extra line, an optional clue or a short optional scene. No race is required, and no race locks content another race needs.

| Race | How it reads the Threshold |
|---|---|
| Human | Sees the official record clearly. The only race the False Explanation fully fools, which makes the twists hit hardest. Optional: the "ordinary witness" testimony that the Archive accepts. |
| Priest | Hears the bell as a hymn. Can read the chapel's inscriptions and the Covenant's Latin. Optional rite scenes in the chapel. |
| Vampire | The Court's bloodline was a founder's guest. Reads the Blood Ledger: who was offered. |
| Werewolf | Smells where the claimed were last. Tracks echo-room traces on moon nights. |
| Ghoul | Hears the names under the floor. Can find the Sealed Foundation's draft. |
| Wraith | Half-Unwritten already. Sees the faded students in photographs and can speak with Mira in echo rooms without a ritual. |

## 5. Chapter structure [PROPOSED; titles from your brief]

| Chapter | Pillar | Beats (short) | Gameplay identity |
|---|---|---|---|
| **Prologue: The Admission** | Arrival | The existing intro fly-in and admission file, then a short cinematic on first ENTER SCHOOL. The gate pushes in, and as the bell rings a roll call is read, with one name too many: a name nobody answers to (Mira's). Then Orientation. | Cinematic, tutorial |
| **Ch. 1: The Empty Desk** [CANON, expanded] | Normal school | Keeps New Kid, The Empty Desk and After Hours exactly. Adds: Orientation before them, a teacher's refusal (Mr. Hale won't answer about Room 102), and a cliffhanger cinematic when COLLECTED is read. | Investigation, stealth |
| **Ch. 2: The Things We Remember** | Memory | Photos change, classmates forget a rostered student you befriended, and the Archive's records disagree. Mr. Hale's story. You find Mira's warning network. | Social deduction, interviews, the Archive as a clue source, 2-player case |
| **Ch. 3: Beneath the Bell** | The Foundation | Bell nights, the basement doors, the Anchor Network. The factions' halves of the truth; you choose who to trust (a decision). Echo rooms. | Stealth at night, environmental puzzles, a crisis night (Lockdown) |
| **Ch. 4: The Bloodline Records** | Covenant | The founders' bargain and why the races are here. Race-specific readings. The Blood Ledger. The Headmaster appears. | Race-varied investigation, a 2-4 player case, a confrontation |
| **Ch. 5: The Last Attendance** | Resolution | A roll call where you must decide what the bell takes. A boss-scale encounter at the bell tower (using existing locations). Endings vary by your decisions. | Group finale with a solo alternative, cinematics, a choice |

**Ending conditions [OPEN]:**
- **Keep the Covenant:** the boundary holds and Mira stays Unwritten, but remembered.
- **Rewrite the Roll:** Mira returns, and the boundary needs a new anchor (you, as Prefect of the Roll).
- **Break the Bell:** a costly freedom with a post-game "thin school" state.

Proposal: each ending gives a different title and Archive state, and none locks ordinary play.

## 6. Open mysteries (kept open on purpose)
- Who answered the bell in 1893?
- What exactly is under the seal?
- Is the Night Custodian the first headmaster?
- Why does the Class of 1887 painting show the pale student smiling at *you*?

## 7. Tone rules
- **School first.** Every chapter starts in an ordinary routine: a class, a lunch, a match.
- **The strange enters through familiar things:** a desk, a photo, a name, a bell.
- **No gore, no blood pools.** Dread comes from absence: names, faces, records.
- **Nobody is a cartoon villain.** Every faction is right about something.
