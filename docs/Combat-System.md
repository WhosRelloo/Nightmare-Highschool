# Combat System: NH Combat Test

This doc covers what was added on top of the existing combat framework. For the base framework (ActionManager, DamageLogic, HitBox, StateManager), see `Project-Audit.md` §3–5.

## Weapons and movement (1.6 to 1.8.4)

Three classes run on the same combat code (`ServerScriptService.Services.Player.ActionManager.Combat`). Each weapon is a table in `ReplicatedStorage.Config.Weapons`.

| | Katana | Fist | Claws |
|---|---|---|---|
| Damage / damage type | 4, Blood | 3, Blunt | 3.5, Slash |
| Animation speed | 1.3 | 1.15 | 1.2 |
| Hitbox | 6×10×7, 3.5 studs ahead | 5×8×6, 2.8 ahead | 5.5×8×6.5, 3.1 ahead |
| Timing markers | in the animations | `Config.Weapons.Fist.Markers` (by animation id) | shares the Fist clips and markers |
| Running attack | shared lunge at 25 | lunge at 42, ×1.6 damage, heavy knockback | lunge at 46, ×1.5 damage |
| Aerial attack | forward glide (30), then a drop | downslam: hang, dive at 0.56 s, impact at 0.66 s | same as Fist |
| Equip | E draws the katana | E | starts equipped (Specter Claws) |

### Timing markers
`ServerStorage.Packages.AnimMarkers` reads an animation's `Hit` and `EndLag` keyframes. If a clip lacks them, or a freshly loaded track can't report them yet, it falls back to `Config.Weapons.<Name>.Markers[animationId]`. A real keyframe always wins.

Fist's running straight has `Hit = 0.33, EndLag = 0.67` in the fallback. Without it the running attack errored and never hit (fixed in 1.8.4).

### One mover per attack (1.8.4)
Each attack's movement comes from one place, so nothing fights it:
- **Running attack:**
  - The shared lunge (`EmitManager.Shared.M1["Running M1"]`) runs on the attacker's client, or on the server for NPCs.
  - It carries you at `Paramaters.Speed`: `Config.Weapons.X.RunningAttack.Lunge`, or 25 for Katana. It stops as soon as something is 3 studs in front of you.
  - You keep moving through the wind-up and are planted only for the recovery after the hit.
  - Weapons with a `RunningAttack` also sweep the hitbox a second time 0.07 s later.
- **Aerial attack, Katana:** the shared glide (`Shared.M1["Aerial M1"]`) moves you forward at 30 and down at 10 until you're near the ground or something is ahead of you.
- **Aerial attack, Fist and Claws (`Config.Weapons.X.AerialAttack`):**
  - The server sends `NoGlide`, so the glide is skipped.
  - A vertical-only hover holds your height through the wind-up and keeps your jump's sideways drift.
  - At `DiveAt` the dive speed is set from a ground raycast, so you meet the floor on the impact frame from any height (clamped between `Dive` and 170).
  - If a living target stands within 11 studs ahead, the dive curves to land 2 studs in front of them.
  - The hitbox is tall and sits low (`Offset`, `Size`), and sweeps twice.
- **M2:** each weapon has its own module in `ServerStorage.Assets.M2.<Weapon>`.

### Hit feedback
`DamageType` selects `ReplicatedStorage.Assets.Effects.HitType[...]`, `Effects.BlockHit[...]`, `Sounds.Hit[...]`, `Sounds.SwingSFX[...]` and `Sounds.BlockHit[...]`. Each needs an entry for every damage type. `Slash` was missing until 1.8.4, so Claws hits had no effect or sound.

### Claws equip (1.8.4)
`ReplicatedStorage.Assets.Weapons.Claws.Kit` holds the two Specter Claw parts. Each has a Motor6D `Weld` and a `WeldTo` StringValue (`Right Arm` / `Left Arm`).
- `ReplicatedStorage.Functions.ClawKit.Attach(character)` clones the kit into `Accessory.Weapons` and welds each part to its arm. `Remove(character)` takes it off.
- `EntityLoader.SetWeapon` attaches the kit for Claws students, sets `Equip`, and tells the client to play the Claws stance.
- Equip (E) keeps the kit on for Claws. The class locker stows it when you switch class.

### Sprint and dash (1.6, 1.8.4)
- `UnPackets.Sprint` records `SprintHeld` on the character.
- When a **slide** or **dash** ends with sprint still held, it sets `SprintCarry` and re-activates Sprint. Sprint then starts at the full 40.5 speed instead of walking up from 25.
- `ActionManager.CanActivate` checks the requested action's cooldown **before** cancelling the current action. Before 1.8.4, any press on cooldown (a dash, an M1, a skill) silently ended your sprint or block.

### Enemies that use this code
- **Delinquents** (`Features.Delinquents`) fight with the Fist moveset through the regular combat AI. Their difficulty tier (1.23: grunt Easy, brute Normal, leader Hard; see *Enemy difficulty*) sets how they parry, block, dodge, feint and attack. Before 1.23 a `Config.Skill` from 0 to 1 did this.
  - Since 1.8.5 they can be **downed** like students (`Config.Downed.NPCsCanBeDowned`), so they can be carried (V), gripped (B) or finished with a race action (N).
  - A downed delinquent left alone gets back up after 15 s at 25% health.
  - A finish, or any kill, pays the killer through `AI.NPCDefeated` → `Downed.GetKiller`.
- **Downed AI enemies stop where they fall.** `NPCController` clears the last walk target once, then idles while `Downed`, `Carried` or `Gripped`.
- **Wild wolves** (`Features.WildWolves`, `NoDowned`: they die outright, because the grip animations are for people) run their own fixed pattern: Bite, Bite, hop back, Leap. A red tell comes 0.5 s before a bite and 0.85 s before a leap, a 1.4 s punish window follows the leap, and only one wolf attacks a student at a time.

### Verified (1.8.4, dummy fighters, Play)
- **M1 combo hit times:**
  - Katana 0.30 / 0.87 / 1.47 / 2.08 s.
  - Fist 0.38 / 0.82 / 1.31 / 1.86 s.
  - Claws 0.35 / 0.77 / 1.32 / 1.87 s.
- **Running attack:** lands at 6, 10 and 14 studs for all three (Fist and Claws at 0.33 s, Katana at 0.50 s).
- **Downslam (Fist and Claws):** lands from 8 and 14 studs up, with targets below and 6 to 9 studs ahead. Katana's glide lands at about 9 studs.
- **M2:** lands for all three. Katana lands two hits.

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

## Crouch and slide (Left Ctrl)
- **One key.** Left Ctrl slides while you're sprinting (Slide moved from C). Otherwise, **hold** it to crouch, and let go to stand. It's rebindable in Settings as "Slide / Crouch".
- **Crouching** (`Services.Player.Crouch`, server authoritative):
  - Sets the Humanoid attribute `Crouch` and walk speed **7**.
  - Standing up restores the speed you had before (the game uses both 12 and 14.4 as normal speeds).
  - Sprinting, jumping or falling, an action (attack, dodge, block, slide, feint), stun states, being downed, carried or gripped, and the main menu all stand you up.
- **Animations:** `Crouch` (139672322709288) replaces the idle and `CrouchWalk` (112732055140240) replaces the walk.
  - They sit in every movement pack (Default, Katana, the shared one).
  - `Controllers.Character.AnimationController` swaps them in on the `Crouch` attribute and dips the camera 1.1 studs.
- **Stealth:** crouching multiplies detection by `Config.Stealth.Detection.CrouchMultiplier = 0.5`. This stacks with standing still (0.6). Sprinting still multiplies by 1.7.
- **Remote:** `UnPackets.Crouch` ("Activate" / "Release"). It's unreliable, so the client re-sends until the server's attribute matches.
- **Verified (Studio):**
  - Holding Ctrl crouched (speed 7, Crouch animation, camera dip). Walking played CrouchWalk at speed 7. Letting go stood up and restored speed 14.4.
  - Sprint + Ctrl played the slide with no crouch. A jump while holding stood you up.
- **Not yet:** a crouch button for phones and gamepads. After a jump you have to press Ctrl again to crouch.

## Enemy difficulty (1.23)

Every combat NPC (`Services.AI.AI`) has a tier: **Easy, Normal, Hard or Nightmare** (`Config.NPC.Tiers`). Its config picks one with `Tier` (default Normal); `Config.NPC.Resolve` lays the tier's combat fields over the config, and `NPCController.Create` uses the result. Older configs that only set `Skill` map to a tier.

| Tier | Who | Pips |
|---|---|---|
| Easy | delinquent grunt | 1 |
| Normal | delinquent brute, a plain `AI.Spawn`, the test bridge's `SpawnAI` | 2 |
| Hard | gang leader | 3 |
| Nightmare | the Ring Champion (duels), the Cmdr ParryDemon | 4 |

Admins spawn a sparring partner of any tier from the admin panel (Spawns).

**Tier fields**
- `React`: seconds from your swing starting to a dodge or a guard (a random value in the range).
- `Parry`, `Dodge`: the chance, rolled **once per swing you throw**, to parry or sidestep it. A heavy (M2, uppercut, slam) adds `Heavy`.
  - A parry is timed to the swing's hit: the animation's `Hit` marker (Fist uses `Config.Weapons.Fist.Markers`), pressed 0.14 s early, off by up to `Timing` either way.
  - The parry window is 0.25 s.
- `Block`, `BlockAfterHits`: the chance to raise a held guard instead, once it has taken that many hits in a row (the count resets after 2.5 s without one).
- `Evasive`: once per stun, the chance to break out with an evasive.
- `Feint`, `ReadBlock`: the chance to feint one of its own swings, multiplied by `ReadBlock` while you hold block.
- `Punish`: right after one of its parries lands, it attacks without waiting.
- `Uppercut`, `M2`: the chance to open with an uppercut (at most one roll a second) or a heavy instead of a light.
- `AttackCooldown`, `MaxStringLength`, `MaxPressureTime`, `RecoveryWindow`: attack pace and the stunlock guard (below).
- `ChaseSpeed`, `SprintSpeed` (19 to 24, so a sprinting player still gets away), `Jump`, `Slide` (chances per second while closing in).

**Rules for every tier**
- No parry or guard while stunned, so a combo that lands keeps landing.
- Nothing in the AI update waits. A parry or guard that has to cancel a swing first runs 50 ms later in its own thread.
- Every hit an NPC takes reaches the AI (`AI.OnNPCHit`, called from `DamageLogic`). Threat (who it fights) still comes only from players (`AI.OnNPCDamaged`).
- Targets must be up, in the world and fair game (`NPCController` `Local.CanTarget`): not downed, carried, gripped, `Protected`, `Dueling` or on the main menu. A duel champion ignores everyone but its opponent.
- When an NPC drops its target it gives the `Agro` claim back first (`Local.DropTarget`), so other NPCs can take over.

**Studio only:** `NHStat_*` attributes on each NPC count swings seen, plans, parries pressed and landed, dodges, guards, evasives, hits taken and punishes. The test bridge has `AIThreat(npc, attacker)` and `AIStats(npc)`.

**Tested (1.23):** see CHANGELOG 1.23.0. Against a dummy that threw one swing every 1.5 s, 19 of 20 parry presses landed, and Nightmare took no hits in 18 swings.

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
