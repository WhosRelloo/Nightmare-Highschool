# Combat System: NH Combat Test

This doc covers what was added on top of the existing combat framework. For the base framework (ActionManager, DamageLogic, HitBox, StateManager), see `Project-Audit.md` §3–5.

## Downed / Carry / Grip

**Rule:** combat damage never kills directly. At 0 HP a character is **downed**. Only a **grip** (execute) kills.

| Step | What happens |
|---|---|
| Downed | **Health:** stays at 1. **Animations:** plays *Downed Idle* (`135755197014043`) while still, and *Downed Crawl* (`104405049546114`) while moving. **Movement:** can crawl at WalkSpeed 4 and can't jump. **Actions:** can't attack, block, dodge, sprint or equip. **Hits:** the body can't be hit. **Recovery:** gets back up after **15 s** at **25%** HP. |
| Carry (**V**) | **Pick up:** works on the nearest downed body within 8 studs. **While carrying:** the carrier walks at 12 and can't attack. **Animations:** the carrier plays *Carry* (`87080849662647`, arms only) and the body plays *Carried* (`113988398408159`), which drapes it over the **left shoulder**. The body's root is held at `Config.Downed.CarryOffset` = (-1.3, 2.0, 0.6) from the carrier's Torso, tuned with screenshots. **Drop:** press V again. Taking a hit also drops the body. |
| Grip (**B**) | **Target:** the nearest downed body within 8 studs, or the one you're carrying. **Placement:** the victim is placed 3 studs in front, facing the gripper. **Animations:** *Katana Grip* (`89687789815973`) and *Katana Grip (Victim)* (`127090783290737`) play together. **Outcome:** the victim **dies when the gripper's animation ends** (~2 s), and the gripper is credited with the kill. A hit on the gripper cancels the grip, and the victim stays downed. |

- Applies to **players, AI NPCs, and dummies.** Infinite-HP dummies can't be downed.
- To exempt a character, set the `NoDowned = true` attribute on its model.
- **Disconnect or reset while downed:** a reset counts as a kill for the last attacker. A disconnect only releases the body, with no kill credit.

### Files

| File | Role |
|---|---|
| `ReplicatedStorage.Config.Downed` | All tunables: timers, ranges, speeds, animation IDs, the grip animation pair per weapon, and the victim offset |
| `ServerScriptService.Services.Features.Downed` | The server-side system. Every rule above is enforced here. |
| `ServerStorage.Packages.DamageLogic` | Hits, chip damage and Burn now go through `Downed.ApplyDamage`. Downed, carried and gripped bodies can't be hit. |
| `ServerScriptService.Services.Player.ActionManager` | `CanActivate` refuses actions while Downed, Carried, Gripped or Gripping. While Carrying, only Sprint is allowed. |
| `ServerScriptService.Services.Managers.StateManager` | Movement rules for the new states: Downed = crawl, Carrying = 12, the others are locked. |
| `ReplicatedStorage.Remotes.Packets` | `Carry` and `Grip` (reliable, no arguments; the server picks the target) |
| `StarterPlayerScripts.Controllers.Character.InputController.General.Carry` / `Grip` | V / B bindings (`Keybinds.Config`) |
| `StarterPlayerScripts.Controllers.Gui.DownedHud` | One HUD line: your downed countdown, `[V] Carry [B] Grip` near a body, carry and grip status |

### Hooks for other systems

On `Services.Features.Downed`:

- `OnDowned(Target, Attacker?)`
- `OnRecovered(Target)`
- `OnExecuted(Gripper, Target)`
- `OnDefeated(Target, Killer?)`: fires on every death in `workspace.Live`
- `GetKiller(Model)`
- `IsDowned(Model)`
- `ApplyDamage(Target, Damage, Attacker?)`: use this for any new damage source

On `Services.AI.AI`:

- `NPCDefeated(NPCCharacter, Killer?)`

**Replicated attributes the client can read:**

| Where | Attributes |
|---|---|
| Humanoid | `Downed` |
| Character | `DownedUntil`, `Carrying`, `CarriedBy`, `GrippedBy`, `GripEndsAt` |

### Security

- The client only sends "carry" or "grip". The server chooses the target and checks:
  - range
  - state (the actor must be alive, not stunned, and not busy)
  - a 0.4 s rate limit per player
- **Known gap:** a downed player keeps network ownership so they can crawl. An exploiter could crawl faster than 4, which is the usual Roblox movement trust problem. Server-side speed checks are a later anti-exploit task.

## AI fairness (stunlock fix)

**Before:** an NPC hit every ~0.6 s with a 0.8 s stun. The player was stunned **80%** of the time and couldn't act.

**Now:** each NPC tracks its "pressure" on its target (`Services.AI.AI.NPCController`, *Stunlock guard*). It stops starting attacks when either of these happens:

- it has landed `MaxStringLength` (3) attacks in a row on a stunned target, or
- the target has been stunned non-stop for `MaxPressureTime` (0.8 s)

It then waits until the target has been un-stunned for `RecoveryWindow` (1.2 s). All three values are in `Config.NPC`.

Measured against an idle player:

| Setting | Stunned | Longest chain | Free windows | Damage/s |
|---|---|---|---|---|
| Before | 80% | continuous | ~none | ~6.5 |
| String cap only (4, 0.75 s) | 75–82% | 3.4 s | rare | n/a |
| 4 / 1.6 s / 1.0 s | 62–68% | 3.2–3.4 s | 1 per ~4 s | 4.7 |
| **3 / 0.8 s / 1.2 s (default)** | **51–52%** | **2.3 s** | **1 per ~3 s** | **3.6** |

A real player can also block, dodge, or Evasive (Q) out of stun. These numbers are worst-case, against a player who does nothing.

## AI death

When an AI NPC dies:

1. Its state becomes `Dead` and it stops acting.
2. It leaves the active list.
3. `AI.NPCDefeated(npc, killer)` fires.
4. The corpse is removed after `CorpseTime` (4 s).

If `RespawnTime` is set, a fresh NPC spawns at the dead NPC's home spot (default `nil`, which means no respawn).

Other AI changes:

- NPCs ignore downed targets and let go of a target that becomes downed.
- A downed NPC does nothing.
- The `Agro` tag leak is fixed: there is now one tag per target, and a dead or downed owner frees it.

## Verified (Studio playtests, single player)

**Real input:**

- V picks up a body and V drops it.
- B grips; B while carrying switches to a grip.
- Holding W while downed crawls about 8 studs in 2 s with the crawl animation.
- M1 clicks still land on dummies.

**Through the test bridge (server path):**

- downing through a real M1
- hits on a downed body do nothing
- carry follow and drop placement
- a hit on the gripper cancels the grip
- a hit on the carrier drops the body
- kill credit in all events
- player downed: actions refused, HUD countdown, recovery at 25 HP after 15 s
- NPC removed and corpse cleaned up after death
- respawn option

**Not tested:**

- multiplayer (two real players carrying or gripping each other)
- disconnect while carried
- mobile (there are no touch buttons for V/B yet)
- how the carry pose looks in motion. It was checked only in still screenshots from Studio, so judge the carry while walking yourself and nudge `CarryOffset` if needed.
