# Nightmare Highschool: Expansion Plan (Phase One deliverables)

**Status:** for review. **Nothing has been implemented.** No game code, data, map or production place was changed.
**Date:** 2026-11-17. **Code baseline:** 2.20.0 in NH Combat Test.

| # | Document | What it answers |
|---|---|---|
| 01 | [Existing-System Audit](01-Existing-System-Audit.md) | What is implemented, partial or planned; what can be reused; dependencies; what must stay untouched |
| 02 | [Feature Specifications](02-Feature-Specifications.md) | Each concept marked approved, revised, deferred or rejected; specs with the existing system each one extends |
| 03 | [Story Bible](03-Story-Bible.md) | Existing canon, proposed mythology, characters, race integration, the 5 chapters, endings, open decisions |
| 04 | [Cinematic Framework](04-Cinematic-Framework.md) | Director components, camera language, multiplayer, skip and recovery, mobile |
| 05 | [Class Redesign](05-Class-Redesign.md) | The hands-on "Bench": per-subject mechanics by level, grading, rewards, electives, anatomy lab |
| 06 | [Progression and Retention](06-Progression-and-Retention.md) | Short, medium and long-term goals, identity, Honours, balance |
| 07 | [Technical Architecture](07-Technical-Architecture.md) | Modules to extend, new modules, data changes, performance, security, dependencies |
| 08 | [Roadmap](08-Roadmap.md) | Phases 0-10 with scope, acceptance and testing; the first checkpoint |
| 09 | [Risk and Scope](09-Risk-and-Scope.md) | Conflicts, duplication avoided, risks, deferred items, approvals needed, the builder list |
| 10 | [Phase 0 Report](10-Phase0-Report.md) | 2.22.0: what Phase 0 changed, the tests, the save and place sizes, and the archive proposal |
| 11 | [Phase 1 Plan](11-Phase1-Plan.md) | Phase 1 (2.24): the Cine framework, the prologue, Orientation; plan and results |
| 12 | [Interactive Cutscenes](12-Interactive-Cutscenes.md) | Phase 1 (2.25-2.26): server-judged segment graphs, grades, the Strikethrough |
| 13 | [The Living School](13-Living-School.md) | Phase 2 (2.27-2.30): roster and memory, staff, incidents and rumours, broadcast and curfew |
| 14 | [Progression and Identity](14-Progression-and-Identity.md) | Phase 3 (2.31-2.34): Standing Paths, the Permanent Record and Honours, trophies, path wardrobe, the Today card |

## The short version
1. **Most of the foundations already exist and are tested.** The school day, lessons, attendance, discipline, factions and 8 cliques, dialogue, quests with an evidence board and stealth, the phone and Midnight Bell, races, moon, hunger, beasts, sports, training and the wardrobe are all in place. The expansion **extends** them; it doesn't replace them.
2. **The real gaps are:**
   - **Lessons:** they are UI overlays, not hands-on.
   - **People:** NPCs remember nothing between sessions, and only 2 NPCs keep a relationship. Teachers, the Headmaster, Mira and the Night Custodian have no presence.
   - **The living school:** there are no rumours, PA, incident log, curfew or crisis events.
   - **Story and recognition:** the story ends at Chapter 1, there's no cinematic framework, no tutorial, and no visible "becoming somebody" layer.
3. **The map stays untouched.** Hands-on lessons use a 3D bench in the UI. Places that would help are listed for the builder (09 §7).
4. **First step:** Phase 0 fixes the shared foundations (night windows, camera ownership, the single writer for `Social`, the enrollment hand-off, the profile-size measure). It needs your approval, along with the open decisions in 03 and 09 §6.
