# Project Audit — NH Combat Test

**Milestone 0.** Audit date: 2026-10-29.
**Place audited:** NH Combat Test (placeId 98950102230473, gameId 10773746169). This is the development place.
**Production place:** Nightmare High [Wave - 1] (placeId 11109987840). It was not opened, read, or modified.

## 1. What was inspected and how

| Source | Accessed? | Notes |
|---|---|---|
| Studio place (all services) | Yes | Full instance tree walk. All 147 first-party scripts were exported to a local mirror and read in full. Third-party packages were excluded from the line-by-line read: ProfileService, Cmdr core, chrono, Packet, Trove, SignalPlus, and Visuals.Rocks. |
| Live playtests | Yes | 8 Studio playtest sessions, single player, using real keyboard and mouse input plus a server-side test bridge (see §7). |
| Concept doc ("Swisha's Nightmare High Concept") | Yes | Read through the Google Drive connector. |
| Combat clip (Medal.tv "npc changes yes", uploaded by yun4mane) | **Metadata only** | The page has no transcript or text version of the video, so **the footage was not watched**. No combat decision in this audit comes from the clip. |
| GitHub repo WhosRelloo/Nightmare-Highschool | Yes | The repo is **empty**: no commits and no files. `gh` is not installed on this machine, so the repo was checked over the web. |

## 2. Concept document: established facts (source of truth)

- **School hours system.** There is a global in-game clock where 5 real minutes = 1 in-game hour, so 1 in-game day = 2 real hours. School hours last 4 in-game hours (20 real minutes) starting around 8 AM. School missions during school hours give **1.2× EXP**.
  - *Inconsistency in the doc:* it says school hours are "10% of the day", but 4 of 24 hours is about 16.7%. The clock should be built configurable, and the developer should pick the intended value.
- **Races.** There are 3 base races: Human, Priest, and Vampire. Sub-races come from a spin system: Superhuman, Grand Priest/Bishop, Pope, Nobleblood, and Royal Vamp. Some classes are locked to specific sub-races.
- **Progression.** It is modelled on Verdant Moon. It includes a stat system, kill-count race tiers (3 tiers per race), quests, hidden areas, and boss drops (for example Dracula's blood).
- **Classes and movesets.** These are concepts only:
  - Base Priest: Holy Beam, Angelic Lunge, Mercy (counter), Protect Me (halo buff), Angel's Gift
  - Base Vampire: Screech, Bloodsuck, Bats, Sharp Nails (bleed), Blood Wave
  - Human: Take This!, Wack, Knife
  - Tainted, Dracula's Descendant, Pastor's Touch, Life Creation, Buddha (meditation meter), DIO! (secret, diary spawn 5% per in-game day), and Brawler (Ken-style, fire)
- **Quests.** The heading exists, but there is no content under it.
- **Alpha scope.** A few missions and base races only.
- **Not defined in the doc:** factions, cliques, specific NPCs, storyline, chapters, classes or subjects, discipline, and a currency name. The current code uses **Yen**.

**Implication.** The master prompt's factions and story chapters are *proposals*, not lore. Races, classes, and EXP are established. The prompt never mentions them, so the architecture must leave room for them (race and class in player data, an EXP and level system, and the 1.2× school-hours EXP multiplier).

## 3. Place structure (as found)

```
Workspace
  Map/            Baseplate, SpawnLocation, LightingSettings
  Live/           ALL characters (players, dummies, NPCs) are parented here
                  (contained 7 inert duplicate dummies at edit time; see §6.2)
  Visuals/HitBoxes, Flashstep (VFX part), Model (empty)
ReplicatedStorage
  ModuleLoader            boots every module under Services (server) / Controllers (client)
  PlayerData              schema + defaults { Yen, Weapon, Vow }
  Config/                 Weapons (Katana only), NPC (AI defaults), Cmdr (admin IDs)
  Functions/              UpdateState, EmitManager (VFX), LinearVelocity, BP
  Packages/               bLua, TrackService, SignalPlus, Trove, chrono, Bind/{Keybinds, StateManager},
                          UI/CameraShaker, Core/{TagService,_Local,UniqueId}, Visuals/{Rocks,Blood}
  Remotes/                Packets (reliable), UnPackets (unreliable input remotes)
  Assets/                 Animations (60), Sounds, Effects, Weapons/Katana, UI/{FlashUI, RedScreen}
ReplicatedFirst           Preloader + AnimationLoader (preloads 60 animations)
ServerScriptService
  Loader                  starts chrono + ModuleLoader
  Cmdr/                   admin console (custom Debug/Adjust commands)
  Packages/               ProfileService, Cmdr
  Services/
    Server                collision groups
    Player/ActionManager  action dispatcher + Combat/Movement/General/Misc/Skills actions
    Player/Data           ProfileService persistence
    Managers/             EntityLoader (character setup), StateManager (state → walkspeed callbacks)
    Features/Vow          (dead code; see Implementation-Status)
    AI/AI                 NPC AI (NPCController, NPCBehaviors, NPCActions, NPCMovement, Rig, Animate)
    Studio/               Studio-only: Game config, Dummy (test dummies), TestBridge (added in this audit)
ServerStorage
  Packages/               HitBox, DamageLogic, DamageTypes(Burn), Trails, SimplePath, AirCombat
  Assets/M2/              Katana (live); Fist/LongSword/Trident (dead, no weapon config)
  Assets/Vows/            Fists, Flames (dead)
  Services/AirWeld        (unused)
  _InertLiveDummies_Backup/  (added in this audit; see §6.2)
StarterPlayer
  StarterCharacter        custom R6 rig
  StarterPlayerScripts/Controllers/
    Character/InputController  input → packet modules
    Character/AnimationController
    StateController       receives Replicate packets → client VFX (Misc, Movement, ScreenFX, …)
    Gui/Camera, Gui/Cmdr, GuiController (empty), SkillController (empty)
StarterGui                Vingette only (no HUD)
StarterPack               Template (Tool)
```

**Architecture pattern.** A single `ModuleLoader` requires every ModuleScript under `Services` and `Controllers` and calls `OnStart()` if it exists. Combat actions are ModuleScripts that the ActionManager finds by name. Characters live in `workspace.Live`. New systems should follow this pattern: add a ModuleScript with `OnStart` under `Services/` or `Controllers/`.

## 4. Dependency map (combat)

```
Client input:  Keybinds(Config) → InputController/<Action> → UnPackets.<Action> (UnreliableRemoteEvent)
Server:        ActionManager.OnStart handlers → Manager.new(Character):Activate(Action)
               → ActionManager/<Category>/<Action>.Activate
                  → TrackService (animation, keyframes 'Hit'/'EndLag') → HitBox:Go()
                  → DamageLogic.Processed (IFrames → Parry → Ragdoll → Block/posture → PostureBreak dummy)
                  → DamageLogic.TakeAction (TakeDamage, InCombat, states, knockback via LinearVelocity, AI threat)
                  → Packets.Replicate → client StateController VFX
Shared state:  Bind.StateManager (server-memory states), Core.TagService (server-memory tags),
               Humanoid attributes (Equip, Sprint, Posture), Character attributes (Combo, Tick)
Data:          Player/Data (ProfileService) ← EntityLoader.GetProfile ← every combat action (weapon lookup)
AI:            AI.Spawn → NPCController (Heartbeat LOD loop) → same ActionManager actions as players
```

## 5. Feature classification

### Combat and movement

| Feature | Status | Evidence |
|---|---|---|
| M1 combo (4-hit, Katana) | **Was broken. Fixed and verified.** | Root cause in §6.1. Verified with real mouse clicks: 4 packets, combo 1→4, dummy HP 100→84. |
| Running M1 / Aerial M1 | Implemented (code review only) | Not exercised in a playtest. |
| M2 / Katana heavy (block-breaking) | Implemented and working | Seen in the AI fight: dealt 5.2 per hit and broke posture. |
| Aerial M2 | Implemented but incomplete | No effective cooldown (wrong cooldown key). |
| Uppercut (Ctrl+M1) + air combat | Implemented and working | Seen in the AI fight: 10 damage, launch, 3 s `InAir` tag. |
| Feint (M2 button) | Implemented. Was broken by the same mouse bug, now fixed (code path) | Not re-tested in a playtest. |
| Block + posture + chip damage | Working, with a bug | Blocking dummy: posture +15 per hit, 0.6 chip damage. The break lands **one hit late** because the code checks the old posture value. Posture never regenerates. |
| Parry (0.25 s window on block press) | Working | Parry dummy: every attacker swing ended in ParryStun, dummy took 0 damage. |
| Posture break → Paralyzed | Working | PostureBreak dummy: posture reset to 0, WalkSpeed 0 for 1.5 s on every hit. |
| Dodge (Q) + i-frames, Evasive (stun break) | Implemented (code review only) | Not exercised. Perfect-dodge has no reward and its client VFX never fires. |
| Slide, Sprint (double-tap W), Jump | Implemented (code review only) | The AI uses Slide in combat (observed). |
| Equip (E) | Working | Verified with a real key press. |
| Knockback / stun / hit reactions | Working | Observed in all playtests. |
| Ragdoll | **Missing** | The state is checked everywhere, but nothing ever creates it. |
| Health regen, defeat or knockout state, kill credit | **Missing** | The default Health script is deleted. There is no Died or Defeated event. |
| Damage types | Partial | Only Burn is a real effect. Blunt and Blood are VFX only. |
| Vows (Fists / Flames) | **Present but dead** | Activation is commented out, and both need a `Hands` weapon that doesn't exist. |
| Extra weapons (Fist, LongSword, Trident) | **Present but dead** | The M2 modules exist, but there is no weapon config. |
| Concept-doc race and class movesets | **Missing** | Only a skill `Template` exists. |
| Mobile / touch / gamepad combat input | **Missing** | Keyboard and mouse only. |

### NPCs (all tested in playtests)

| NPC | Status | Evidence |
|---|---|---|
| Parry dummy | Working | Parried 4/4 swings. |
| Attacking dummy | Working | Hits the player for 4 every ~0.6 s. |
| ParryTrade dummy | Working | Parries, then counter-hits the player. |
| Blocking dummy | Working, with a bug | Blocks. Posture break is one hit late (see Block above). |
| PostureBreak dummy | Working | Every hit causes a posture break. |
| Inf Dummy | Working | Stunned on 4/4 hits, HP stays at infinite. |
| AI NPC (NPCController), targeting / chase / attack | Working | Acquires the nearest player within 50 studs. Slides in and uses M1, M2, and Uppercut combos. Re-chases after knockback. Takes damage normally (96→84 over 3 hits). |
| AI NPC disengage | Working, minimal | Goes Idle as soon as the target is more than 100 studs away. There is no return-home behaviour. |
| AI NPC **stunlocks players** | **Broken (design)** | The player was in Stun for 80% of samples. NPC hits arrive every ~0.6 s, each with a 0.8 s stun, so the player cannot fight back. This violates "avoid long stun chains". |
| AI NPC **death handling** | **Broken** | After death, the NPC stays in the active list with state "Attacking", and the corpse stays in Live. There is no despawn, respawn, or defeated event. |
| AI pathfinding | Implemented but unused | SimplePath is created, but the NPC only moves in straight lines. It cannot route around walls. |
| AI `Agro` tag | Bug | A permanent tag is added to the player on every chase tick, so it grows without limit (code review). |
| AI auto-spawn | Missing | `Services.AI.Spawn` is fully commented out. Admins spawn NPCs with the Cmdr command `npc`. The test bridge also spawns them. |
| School NPCs (teachers, hall monitors, students) | **Missing** | |

### Everything outside combat

| System | Status |
|---|---|
| Persistence (ProfileService, session-locked) | Implemented and working (profile loads, leaderstats are created). The schema is small: Yen, Weapon, Vow. |
| Currency (Yen) | Implemented (only through the admin command) |
| Admin tools (Cmdr: npc, state, posture, gb, weapon, ac, gd) | Implemented. Admin-only, using hard-coded user IDs. The developer's own ID (37484441) is **not** in the admin list, so Cmdr is unusable for them right now. |
| HUD, timetable, quest journal, dialogue, notifications, settings, map | **Missing** (StarterGui only has a vignette) |
| School clock, classes, attendance, discipline, detention, hall monitors | **Missing** |
| Factions, reputation, relationships, rivalries | **Missing** |
| Quests, dialogue, investigation, inventory, lockers, clubs, jobs, events | **Missing** |
| Races, classes, EXP and levels (from the concept doc) | **Missing** |
| School map geometry | **Missing.** The place is a flat baseplate, so temporary test geometry will be needed. |

## 6. Defects found and actions taken in this audit

### 6.1 M1 (and every mouse binding) never fired: fixed

- **Symptom.** Clicking did nothing. The server never received an M1 packet.
- **Root cause.** `ReplicatedStorage.Packages.Bind.Keybinds` built the input name with `inputObject.KeyCode.Name ~= "Unknown"`. Roblox has renamed the value-0 KeyCode from `Unknown` to `None`. Every mouse or touch input was therefore labelled `"None"` instead of `"MouseButton1"` / `"MouseButton2"`, and no binding ever matched.
  - Confirmed live: `Enum.KeyCode.Unknown.Name == "None"`, value 0.
  - This also broke **Feint** (MouseButton2).
- **Fix.** Added a `GetInputString()` helper that compares the enum (`inputObject.KeyCode ~= Enum.KeyCode.Unknown`) instead of its name. It is used by both InputBegan and InputEnded. The keybind error handler now `warn`s the actual error; it used to `print` a bare table.
- **Verified** with real mouse input in a playtest.
- **Separate note.** "M1 does nothing" also happens if the weapon isn't equipped. The player spawns unequipped and must press **E** first. Both the client and the server require `Equip`.

### 6.2 Inert duplicate dummies in Workspace.Live: moved, not deleted

- `Workspace.Live` held 7 edit-time copies: Blocking, Attacking, PostureBreak, Parry, Rig, ParryTrade, Inf Dummy.
- `EntityLoader` never initialized them: no weapon, default collision group, no behaviour. They sat at the spawn point. The working dummies spawn from `Services.Studio.Dummy.Npcs` at z≈15, so testers hitting the copies at spawn would see "NPCs that don't work".
- They were moved to `ServerStorage._InertLiveDummies_Backup`. Drag them back to restore them, or delete the folder.

### 6.3 Test tooling added

`ServerScriptService.Services.Studio.TestBridge` is a Studio-only ModuleScript. It creates `ServerStorage.NHTestBridge`, a BindableFunction that runs checks inside the game's own module instances. Commands:

- `SpawnAI`
- `AIStatus`
- `DestroyAI`
- `Inspect` (HP, posture, current action, states, tags)
- `DoAction`

It does nothing outside Studio: ModuleLoader skips `OnStart` for `Studio/` modules in live servers, and the module also checks `IsStudio()`.

### 6.4 Debug note for future work

Requiring a game module from the Studio command bar or a plugin gives you a **separate copy** of that module with its own state. Inspect live game state through the TestBridge instead. Requiring `Player.Data` or `UnPackets` from outside can also create duplicate remotes.

## 7. Limitations of this audit

- **Testing coverage.** Only single-player Studio playtests were run. No multiplayer test, disconnect test, or live-server test was run.
- **Real versus server-side inputs.**
  - Real inputs: M1 (mouse) and Equip (E key) were driven with real inputs.
  - Server-side only: the dummy and AI combat checks drove the player's attacks through the server ActionManager, which is the same code path a client packet reaches after the fix.
- **Combat clip.** Not viewed, because the video isn't readable with the available tools.
- **Assets.** Sound `rbxassetid://71086651442213` fails to load because the experience isn't authorized to use it. Asset `203785492` fails with "Asset type does not match". Neither one blocks combat.
- **Security.** The remote-exploit findings in Implementation-Status come from code review, not from exploit testing.
