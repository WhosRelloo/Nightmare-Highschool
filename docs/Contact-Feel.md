# Contact feel: bumping into students has weight

**Version:** 1.97.0, 2026-11-12. NH Combat Test only.

**Owner's request:** "I want the NPC's to actually FEEL like im touching them, especially when I bump into them. I want it to have some weight to it."

## Why it was needed

Students are physics ghosts. `Features.Schedules` puts every part of a student in the collision group `NHWalkers`, which doesn't collide with players (`Entity`), and that stays as it is. It stops players shoving students through walls or body-blocking doorways.

Before this change, a player walked straight through a student and only the student's nudge animation played. Contact is now faked on the player's own client, so it feels solid with no physics jank, and the server reacts to how hard the hit was.

## What you feel

| Approach speed | Tier | What happens |
|---|---|---|
| under 4 | none | You slide around them. You can't walk through. |
| 4 to 18 (walking) | brush | Speed ×0.65 for 0.25 s, a light camera jolt, a soft thud and rustle, and your shoulder twists away (a mirror of the student's twist). |
| 18 and up (sprinting) | hard | Speed ×0.08 for 0.3 s, a rock back of about half a step, a sharper camera bump, a heavier thud, the full twist and a short lean back. |

- **Contact radius:** 2.2 studs, measured flat from root to root. You stop where shoulders would meet, then slide around to the side you were already on.
- **Cooldown:** one impact per student every 0.6 s.
- **Seated students** are solid but don't react.
- **Students who aren't solid:** downed, carried or dead ones.
- **Never stuck:** if you're pinned for 0.4 s (between two students, or a student pressing you into a wall), you're let through for 1.2 s.
- **Accessibility:** the camera jolt follows the Camera Shake setting (`NHShakeScale`), and the lean is skipped under Reduce Motion.
- **Thresholds:** walking speed is 14.4, so the hard tier starts at 18 (sprint is 25 to 41).

## How the student reacts

1. The client reports each impact to the server through `ReplicatedStorage.NHContact.Impact`.
2. The server calls `StudentBrain.Contact`, which records the hit in Nudges' memory and triggers the reaction straight away. This works even when the student's senses never noticed you coming: from behind, while they stand still, or in a crowd.
3. The reaction depends on the hit:
   - **A light brush:** the twist.
   - **A real hit:** the shove. Its carry grows with your speed, up to ×1.5, and the room check is kept.
4. The bump line ("Watch it!") now lands at the moment of contact (`Nudges.OnContact`), not as you approach.
   - **Sprinting:** the Sprint line ("No running in the halls!").
   - **Otherwise:** the clique's Bump line, 60% of the time.

## Server checks

A report only counts if all of these hold:

- **The student:** it's a live `NHBrain` student that isn't down.
- **The player:** alive, not down, and within 5 studs of the student's height.
- **Distance:** the flat distance is within 4 + (0.35 s + ping) × the speed the server itself saw. That speed is capped at the server's own WalkSpeed × 1.1 + 2, and anything past 4 studs must be ahead of the player.
- **Rate:** at most 4 reports a second.
- **Values:** Speed must be finite and within the server-seen top speed + 2. Direction must be finite, with a length of 2 or less.

## Files

| Repo | Live |
|---|---|
| `tools/contact-feel/StarterPlayer.StarterPlayerScripts.Controllers.World.ContactFeel.luau` | `StarterPlayer.StarterPlayerScripts.Controllers.World.ContactFeel` (client) |
| `tools/contact-feel/ServerScriptService.Services.Features.ContactFeel.luau` | `ServerScriptService.Services.Features.ContactFeel` (server) |
| `tools/ct-npc-1862/StudentBrain.luau` | `ServerScriptService.Services.AI.StudentBrain` (`Brain.Contact`; Bump line at contact) |
| `tools/npc-nudges/Nudges.luau` | `...StudentBrain.Nudges` (`Remember`, `TopSpeed`, the "Contact" kind, `OnContact`, carry scaling) |

The play test record is `tools/contact-feel/PLAYTEST.md`.

## Reused pieces

- **Camera jolt:** `EmitManager.ShakeCamera`.
- **Sounds:** the thud is `Assets.Sounds.Movement.Land`, and the rustle is a stand-in, `SwingSFX.Blunt.Swing`. The game has no cloth or body-thud sound yet.
- **Animations:** the published Nudge twist clips.
- **The slowdown:** a client-local WalkSpeed override built on CombatSpeed's pattern.
  - It never touches speeds of 5 or under.
  - It only restores the speed if the slowed value is still in place.
  - A 0.3 s tail after it ends puts the real speed back if Equip or AnimationController wrote the slowed value back.

## Known gaps

- **Not judged by ear or eye:** the sounds, the camera jolt and the lean. The rustle is a stand-in; audition a real cloth sound.
- **Not tested:**
  - the full-speed shove carry (every student in reach had a wall close by);
  - a transformed or downed player;
  - a student despawning in the middle of a nudge (the code guards against it);
  - a second player.
- **The walk animation** keeps cycling while you're held against a student. The humanoid rewrites velocity every step, so only your position is held.
- **The lean** is local to you; other players see the twist.
- **The Map place:** its Nudges copy is now behind, though the changes are additive, and it has no ContactFeel yet.
- **A bug that predates this feature:** pressing E to equip while walking can leave your WalkSpeed at 0. Equip and AnimationController both set it to 0 and then restore what they read, so they can restore each other's 0.
