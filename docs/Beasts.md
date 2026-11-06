# Beasts

Night creatures run by one shared system. The wolves (`Features.WildWolves`) are separate and untouched. Design: `docs/superpowers/specs/2026-11-05-beasts-design.md`.

**Built so far:** the Hellhound (1.56.0).
**Planned, one at a time:** the Grave Ghoul, the Bone Spider, the Crypt Bat, the Night Stalker, the Stone Gargoyle.

![The Hellhound by day](img/hellhound-day.jpg)

## Where things are

| What | Where |
|---|---|
| The system (server) | `ServerScriptService.Services.Features.Beasts` |
| Each beast's numbers | `ReplicatedStorage.Config.Beasts` (`Defs.<Name>`) |
| The beast models | `ServerStorage.NHBeasts.<Model>`, with an `Animations` folder inside |
| The Hellhound's fire | `ReplicatedStorage.Beasts.HellhoundFX` (`Apply(model)`, `Breath(model, on)`) |
| The special-attack warning (client) | `StarterPlayerScripts.Controllers.StateController.Indicators.BeastTell` |
| Lairs | parts tagged `NHBeastLair` with a `Beast` attribute. The placeholder Hellhound lair is `workspace.NHBeastLairs.HellhoundLair`, in the boiler yard |
| Trophies | `ReplicatedStorage.Config.Items.Trophies` (`Kind = Trophy`) |
| Admin | the admin panel's Spawns tab, "Beast: <Name>" (command `SpawnBeast`) |

## How a beast fights

- **Spawning:** after dark (19:30 to 05:30) it comes out of its lair, wanders near it, and is gone by morning. Its first sight of a student plays its `Sighted` clip once (the Hellhound howls).
- **The pattern:** it attacks in a fixed order (`Pattern`) that loops, so players can learn it.
- **The Kanji:** only **special** moves (`Special = true`) show a warning first, the game's own critical-attack Kanji (`CombatFX.Heavy`), bigger and with the critical glow and ring, plus the Critical sound. Normal attacks have no warning.
- **Openings:** every special is followed by an opening (`Rest`, `Recover`) where it stands still.
- **Stuns:** students' hits stun it (`Stun1` / `Stun2`), and a posture break plays `GuardBroken`. For `StunGuard` seconds after a stun wears off, hits can't stun it again or call off its attack, so mashing can't stun-lock it.
- **Turns:** one beast attacks a student at a time; the rest circle.
- **Giving up:** it gives up past its `Leash` and walks home.
- **Damage:** it goes through `Downed.ApplyDamage`, so a beast can down a student but never kill one. Beasts are `NoDowned`: they die outright.
- **Reach:** measured from the beast's body, out to its mouth plus the move's range. A big beast's mouth is studs ahead of its middle, so a student pressed against it is still in reach.
- **Death:** the `Death` clip plays and the body fades. The killer gets `Reward.Exp` (Combat), `Reward.Yen`, and a `Reward.Trophy` at its chance, with a notice.

## The Hellhound

| | |
|---|---|
| Health | 180 (a wolf is 70) |
| Pattern | Bite (8), Bite2 (10), **Fire Breath** (3 a tick, 7 ticks), Bite (8), Hop back, **Pounce** (14) |
| Openings | about 2 s after the breath, about 4 s after the pounce |
| Stun guard | 2 s |
| Spawns | 1, in the boiler yard at night; back 4 minutes after a kill |
| Reward | 160 Combat EXP, ¥60, a 15% chance of the Ember Tooth |

It's the owner's wolf rig scaled up 1.35x and charred black. The owner's rules for its look:
- **No outline**, and only the game's own VFX.
- **Fire:** the burning-status flame, dimmed so it doesn't blow out under the night bloom, on a continuous mane down the back, the tail and the paws.
- **The head:** no fire except **burning eyes**, and **one horn** in the middle of the forehead.

The horn and the nine spikes are held to the bones with RigidConstraints, so they follow every animation. Checked in Play: 0° off while the head swung 27°.

![The Kanji before a special](img/hellhound-kanji.jpg)

## Trophies

A rare drop from a beast you kill, kept in your Locker under All. A trophy is never sold, never pinned to the hotbar and never used; you can drop it.

![The Ember Tooth in the Locker](img/ember-tooth-locker.jpg)

## Adding a beast

1. Build its model and rig.
2. Put the template in `ServerStorage.NHBeasts` with an `Animations` folder: `Idle`, `Walk`, `Run`, its attack clips, `Stun1`, `Stun2`, `GuardBroken`, `Death`, plus its unique clips.
3. Add its entry to `Config.Beasts.Defs`: stats, `Pattern`, `Moves`, `Spawn`, `Reward`.
4. Tag its lair parts `NHBeastLair` with `Beast = <its Spawn.Lair>`.
5. Add its trophy to `Config.Items.Trophies`.
6. Its admin button appears by itself.
