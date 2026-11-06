# The core game in the Map place (2026-11-05)

Owner: "let's transfer the core game (movement, cinematic mode, etc.) into the "Map" place first so me and the builder
can preview how the game's gonna FEEL with the map".

**Map place:** placeId 111107083446202, where the builder is building the school (Team Create, live).

## What the owner chose
- **Movement:** sprint and fast sprint, dash (Q), slide (Ctrl while sprinting) and crouch, vault, shift lock on Left Alt,
  the custom R6 character and animations, including the new jump and landing.
- **Cinematic mode and the camera:** the cinematic view (`\`), the game's camera, cursor and shift-lock reticle.
- **Day/night and ambience:** the school clock (5 real minutes a game hour), the day cycle's lighting grades, the moon
  phases, the ambient sounds and the soundscape.
- **Combat:** M1/M2, block and parry, the weapons, posture, the combat tag, downed and getting up, the wolf form.
- **No training dummies** (the owner's choice).
- **No saving.** `ServerScriptService.Services.Player.Data` in the Map place is an in-memory stand-in with the same API:
  every player gets a fresh copy of `PlayerData.DEFAULT_PLAYER_DATA` and it is thrown away on leaving. There is no
  ProfileService and no DataStore call in the add-on, so the real save data is never read or written.
- **Roblox's standard PlayerModule** (owner approved): the Map place uses Roblox's newer built-in player controls,
  which have no PlayerModule, so shift lock sat on Shift (which is sprint) and the game's camera hooks had nothing to
  attach to. The same unmodified PlayerModule and PlayerScriptsLoader that NH Combat Test runs were added.

## What was added
Every top-level item carries the attribute `NHCore = true`. `ServerStorage.NHCore.README` lists it all in the place.

| Where | What |
|---|---|
| ReplicatedStorage | ModuleLoader, PlayerData, Lineage, Config, Functions, Remotes, Packages, Assets (animations, sounds, effects, weapons), UI (Theme, Components, Settings) |
| ReplicatedFirst | Preloader, Packages (the animation preloader) |
| ServerScriptService | `Services` (only the core: ActionManager and its actions, Crouch, the Data stand-in, EntityLoader, StateManager, Server, Downed, Posture, CombatTag, CombatSpeed, Fx, Notifications, Transformation, Vow, MoonPhases, SchoolClock, the AI library DamageLogic uses, Studio.Game), `NHCoreMap` (the bootstrap) |
| ServerStorage | Packages (DamageLogic, HitBox, AirCombat, AnimMarkers, Trails, DamageTypes, SimplePath), Assets (weapon modules, Vows), Services (AirWeld), NHWolf (the wolf form), NHCore (the R6 character, the vignette, the runtime folders, the README) |
| StarterPlayer.StarterPlayerScripts | Loader, Controllers (only the core: StateController and its effects, Fx, GuiController, InputController, AnimationController, ShiftLockKey, Vault, Camera, Cinematic, ShiftLockCursor, Cursor, DownedHud, CombatTag, Notifications, DayCycle, Ambient, Soundscape, FullMoon, MoonPhases, GetUp, Veil), PlayerModule, PlayerScriptsLoader |

**Only while the game runs** (applied by `NHCoreMap`, never saved): gravity 210, jump-power mode (JumpPower 50, walk 16),
the custom character, the vignette, `workspace.Live` and `workspace.Visuals`. `NHCoreMap` also boots the server modules
(what NH Combat Test's `ServerScriptService.Loader` does), after that setup.

**Not touched:** nothing the builder made was moved, changed or deleted; no Workspace, Lighting or StarterPlayer
property was edited in Edit (checked after the transfer: gravity 196.2, `CharacterUseJumpPower` false, no
StarterCharacter, the builder's lighting and 5,075 workspace instances, none of them the add-on's). Not brought over:
the main menu and save slots, the school simulation and NPCs, the phone, quests, cliques, sports, skateboards, the
HUD clock.

## How it was carried over
The scripts and assets were serialized in NH Combat Test (`SerializationService`, 1,286 instances, 228 scripts, 666 KB),
moved across as text and unpacked in the Map place into the services, which were empty. The import refuses if a name
is already taken. The module list came from tracing every `require` from the chosen systems.

## Tested (Map place, local play-test, real keys and mouse)
- The character spawns on the game's R6 rig in `workspace.Live`, gravity 210, with the clock running and no errors
  on the server or the client (the only console lines are known: the aerial sound needs "share access", the chrono
  package's join message, and a Studio plugin's DataStore call).
- **Movement:** W walks (22 studs in 1.5 s); Shift sprints, then fast sprint at 2.2 s (40.5); Ctrl slides; Q dashes;
  Space plays Jump, Fall and Land.
- **Shift lock** on Left Alt with the game's reticle; Shift doesn't toggle it.
- **Cinematic:** `\` hides every HUD and shows the cinematic bars; pressing it again brings them back.
- **Combat:** E draws the weapon; three M1s and an M2 swing and spawn hitboxes.
- **Night:** with the clock moved to 23:00 (run time only), the night grade, darker ambient and the moon phase apply.
- **Not tried:** a fight against another player (there's no one to hit without dummies), the wolf form, the downed
  state, and walking the whole map. Two people in the place at once (the builder and the owner) wasn't tried.

## Removing it
Run this in the Map place's command bar, then save:

```lua
for _, s in {game.ReplicatedStorage, game.ReplicatedFirst, game.ServerScriptService, game.ServerStorage, game.StarterPlayer.StarterPlayerScripts} do for _, c in s:GetChildren() do if c:GetAttribute("NHCore") then c:Destroy() end end end
```

## Keeping it in step
The add-on is a copy taken at 1.53.0, with the 37 core scripts changed in 1.55.0 copied in afterwards (verified byte for byte). Later changes in NH Combat Test don't reach the Map place by themselves: copy it
again the same way (remove it with the command above first).
