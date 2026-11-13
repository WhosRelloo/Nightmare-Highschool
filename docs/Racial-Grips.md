# Racial Grips (2.6.0, reworked in 2.6.2 and 2.7.1)

Up: [[Combat-System]] · Related: [[Races-and-Bloodlines]], [[VFX-Design-Bible]]

Owner: "/design the racial grip animations that dont have any. And make animations for the victims of the racial
grips." Then: victims "look like they are getting eaten alive or exorcized (priest)", and "CREATE unique, on theme, and
HIGHEST quality vfx", custom sounds, and drawn VFX art. **No blood or gore anywhere** (the owner had a Roblox
moderation warning).

## What a racial grip is
N on a downed body (D-pad Down, the race button on touch) finishes it with your race's own move, through
`Downed.StartGrip` like the B grip: it lines the body up, a hit on you cancels it, and the body dies when your clip
ends. It heals you and feeds your race hunger (`Features.RaceAction`).

## Before (audit, 2026-11-12)
| Race | Grip | Gripper clip | Victim clip |
|---|---|---|---|
| Vampire | Blood Drain | 134503729182597 (arm-out drain) | none |
| Ghoul | Eat Body | 79651374323565 (owner's) | none |
| Werewolf | Eat Body | the Ghoul's | none |
| Wraith | Soul Siphon | placeholder kneel | none |
| Priest | Exorcise | placeholder kneel | none |
| Human | Exorcise (refused on mortals) | placeholder kneel | none |

The victim was placed once 3 studs away and stayed in its downed idle. The old effects sprayed dark-red "gore bursts"
(Eat Body) and red "blood droplets" (Blood Drain).

## Now
Every race has its own pair: the gripper clip and a victim clip authored together on two R6 rigs, with the victim
**welded** to the gripper's root at the clip's offset for the whole grip, so hands stay on the body. Sub-races use
their base race's grip with a richer effect (more particles; the top sub-races add a signature piece).

| Race (sub-races) | Grip | Length | Victim (eaten alive / exorcised) |
|---|---|---|---|
| Vampire (Nobleblood, Royal Vamp) | **The Kiss**: creeps in, crouches, hauls the body up by the collar, bites the neck from behind, three drinks, lets go, wipes the mouth | 3.0 s | shoves and claws at the arm across its chest, weakening each drink, then slumps back to the floor |
| Ghoul (Ghast, Crypt Lord) | **Eat Body** (owner's clip) | 3.5 s | pinned, shoves at the ghoul's head, kicks, rolls away clawing the floor, is dragged back, jerks at the last rip; the outstretched hand trembles and drops |
| Werewolf (Bloodmoon, Alpha) | **Maul**: snarl, pounce onto all fours, three raking swipes, a shake by the shoulders, a howl | 2.8 s | shields its face, the guard is knocked open on each swipe, tries to crawl away and is hauled back |
| Wraith (Revenant, Hollow King) | **Soul Siphon**: floats, palm to the chest, draws the hand up, yanks | 3.0 s | the chest arches after the hand as if on a string, then slams down limp |
| Priest (Grand Priest, Pope) | **Exorcism**: crouches by the head, hand on the forehead, the other raised, strikes the chest on the last word | 3.2 s | possessed: violent arches, drumming heels, head whipping under the hand, grabs the priest's wrist, a rigid arch a stud off the floor that snaps flat on the strike |
| Human (Superhuman) | **Hunter's Stake**: crouches over the body pinning the throat, the stake inches down against two hands, raised and driven | 2.6 s | grabs the stake arm and pushes back, the arms give way, one jolt |

Exorcism still only works on the unholy. The Hunter's Stake works on any body (Humans had no racial grip on mortals).

## 2.6.2 rework: menacing, smoother, and kneels from the game's crouch
Owner: "make the animations look more menacing, scary, and smoother. Also make sure the legs don't look weird during
the animation." Then, with reference shots and a "Kneel Example" model: "Kneels should look like this", "Just use the
crouching > get up animation as reference that we already have in the game" and "Don't be afraid to use other
animations we already have".

**The kneel is the game's crouch.** Human, Priest and Vampire kneel exactly like Crouch (rbxassetid://139672322709288,
the 171-key "Crouch idle" in Workspace), frame 0 on a default R6 rig:

| Part | Pose (relative to a standing HRP) |
|---|---|
| Torso | drops 0.90, leans 27 deg forward, turned 22 deg |
| Front leg | near vertical, planted 1.2 studs ahead |
| Back leg | slants 58 deg back and swings 42 deg out; the knee rests 0.41 under the floor top, as in game |
| Both legs | slide off their sockets up into the torso, which folds the knee (Pose position, for example (0.84, 0.75, 0.04)) |

- The HRP stays at standing height, as when crouching in game.
- The generator plants both legs in the world and re-solves each hip's rotation and slide every frame. The body can
  lean, turn and drive down into a strike (the hips sink up to 0.3) while the legs stay put.
- A grip with the right foot forward plays the crouch mirrored.
- Placements were searched so the hands reach and the legs stay clear of the victim:
  - Human: beside the chest, mirrored.
  - Priest: by the head, as played.
  - Vampire: behind the sitting victim's left shoulder, mirrored, turned 14 deg into the neck.
- The old 2.6.0 kneels pivoted rigid legs at the hip under a torso pitched up to 57 deg, and read as a lunge or a split.

**Menace and smoothness:**
- Creeping starts with the head cocked and claws curled.
- Heavier looming leans.
- The stake and the palm strike commit the hips.
- The Werewolf snarls with its claws out, then howls from a planted stance.
- The Wraith dives with its legs trailing back.
- The Priest stays over the body with the palm down and the head bowed.
- Clips are smoothed after the contacts are solved.

**Legs and the floor:**
- No part goes under the floor except the crouch knee. Victim limbs used to dip up to 1.4 studs under it.
- Arching victims plant their heels.
- Stand-to-kneel transitions take a step.
- The Human's victim strains its chest up toward the stake arm.
- The possessed body lifts a little while it grabs the priest's wrist.

Measured on the built clips (worst frame):

| Grip | Attacker hands | Victim hands | Lowest point |
|---|---|---|---|
| Human | 0.28 | 0.08 | crouch knee -3.41 (victim -3.09) |
| Priest | 0.27 (palm on the face at the strike) | 0.31 (the wrist grab) | crouch knee -3.41 |
| Vampire | 0.25 | 0.05 | crouch knee -3.41 |
| Werewolf | 0.38 | 0.00 | -3.04 |
| Wraith | palm 1.3 over the chest (by design, the soul streak spans it) | 0.00 | -3.04 |
| Ghoul | (owner's clip) | 0.22 | -3.08 |

The floor is -3.0. animpro passes on every clip; groundContact is waived on the three crouching attackers because
animpro can't see the leg slide.

## 2.7.1: heads look at what they are doing
Owner: "Make the head movements actually follow the animation and look natural for what they are trying to do. The
werewolf eating anim has the head up instead of down on the victim."

- A neck key can be a look: `look(body, part, point, tilt)` in `clips/_util.py`.
  - The face aims at a point on the other body's Torso, or at its head spot.
  - It's re-solved every frame within 80 deg turn, 75 deg down and 60 deg up, then turned by the tilt for
    expression.
  - Looks never read the other head's own turn, so two heads watching each other can't loop.
  - `set_necks(keys, {t: spec})` sets them by key time, at the end of each clip file.
- Deliberate head moves stay as fixed angles: impact whips, the possessed thrashing, the bite pose, the wraith
  victim's head falling back, and the howl and soul-rip looking up.
- Werewolf, before vs after (generator; Play matched it):

  | | Face | Miss from the victim |
  |---|---|---|
  | Before | level to 21-42 deg down | 57-81 deg |
  | After | 47-62 deg down | 8-25 deg (throat and chest) |

  The haul shakes it by the throat.
- Every grip now aims its heads at the right thing on its watching beats (worst miss):

  | Grip | Attacker | Victim |
  |---|---|---|
  | Human | face 3-10 deg, heart 3-9 deg | hunter's face 3-7 deg |
  | Priest | possessed face 2-16 deg | priest's face 1-3 deg |
  | Vampire | the neck through the drinks, chest within 5-8 deg | head tilted aside for the bite, by design |
  | Wraith | chest and soul streak 4-10 deg | wraith's face 3-13 deg |
  | Ghoul | - | ghoul's face 2-9 deg |

- `tools/racial-grips/gaze.py <clip> attacker|victim` prints the face pitch and miss per beat. `duo.py` and
  `solo.py` draw a nose marker so the gaze shows.

## VFX (client, `RaceActionFx.RaceGripFx`)
- **Every grip:** the race sigil on the floor, a camera ease-in and a hit-stop punch on the kill for the gripper, a
  darkening, desaturating screen with a slowing heartbeat for the victim. Shake honours Camera Shake, flashes honour
  Reduced Flashing, particle counts halve on low Effects Quality.
- **Vampire:** a bat storm hides the bite; a pale rose-white life thread from neck to mouth; the victim drains grey;
  crimson eyes and a rim that pulses with each drink; the bats scatter on release.
- **Ghoul:** the floor cracks with a green glow; grave mist and spores; bone spikes rise from the earth around the pair
  (never from the body); grit kicks up off the floor on each feed; the cage crumbles at the end.
- **Werewolf:** amber eyes; three silver claw-streak slashes with sparks and fur tufts; a pale moon and a dust
  shockwave on the howl (bigger on a full moon, doubled for an Alpha).
- **Wraith:** frost blooms across the floor and the colour drains; a translucent copy of the victim is drawn up toward
  the palm along a soul streak, torn free, and spirals into the fist; frost shatters.
- **Priest:** a gold rune seal, the gilded cross over the raised hand, a god-ray column with gold dust; ink smoke and
  dark tendrils fight back; on the strike a shadow demon is torn up out of the body and burns to embers, a white-gold
  flash and a shockwave.
- **Human:** a wooden stake with a silver band appears in the hand with a glint; dust on the knee and the strike; on a
  monster the body flashes pale and grey ash drifts off it.

Custom art (15 textures): `art/vfx/grips/` (`make_grip_sprites.py`), contact sheet `docs/img/260/vfx-contact-sheet.png`.
Custom sounds (15 cues): `art/sfx/racial-grips/` (`tools/sfx/racial_grips.py`), one cue per grip aligned to its beats,
a victim heartbeat loop, a finish sting and six sub-race extras. All synthesized; nothing wet or gory.

## Files
| Piece | Where |
|---|---|
| Kinds, clips, offsets, beats, colours, sound/texture ids | `ReplicatedStorage.Config.RaceGrips` |
| N action (race -> Kind, Studio preview ids, fallbacks) | `ActionManager.Misc.RaceAction` |
| The weld, the final frame, the release | `Features.Downed` (`StartGrip`, `EndGrip`, `FinishGrip`) |
| Rewards, the Fx payload (victim, sub-race, victim race) | `Features.RaceAction` |
| VFX, sound, camera | `Controllers.World.RaceActionFx.RaceGripFx` |
| Clips to publish | `ServerStorage.NH_GripAnims` (11 KeyframeSequences) |
| Generator | `tools/racial-grips` (see its README and `patches.md`). Checks: `duo.py` (both bodies), `solo.py`, `sinkcheck.py` |
| The kneel | `tools/racial-grips/clips/_util.py`: `kneel_legs` / `kneel_root` / `kneel_fit` (the crouch frames); the leg slide goes into the pack from `out/*.tuck.json` |

## Owner steps (group-owned assets)
1. **Publish the 11 KeyframeSequences** in `ServerStorage.NH_GripAnims` (right-click > Save to Roblox, under the
   group). They were rebuilt for 2.6.2, so publish these versions: GripVampire, GripVampireVictim, GripGhoulVictim, GripWerewolf, GripWerewolfVictim, GripWraith,
   GripWraithVictim, GripPriest, GripPriestVictim, GripHuman, GripHumanVictim. Send the ids.
2. **Upload the 15 sounds** in `art/sfx/racial-grips/` and the **15 textures** in `art/vfx/grips/` under the group.
3. Then the ids go into `Config.RaceGrips` (`Gripper`/`Victim`, `Sounds`, `Textures`).

Until then: in Studio the clips play from temporary preview ids; on a live server each race falls back to its old single
clip with no victim clip and no weld; effects use the existing `nh_*` and tier-up art; the grip sounds are silent.

## Verified for 2.6.0 (2026-11-13, NH Combat Test, slot 4 "Testy", Play)
- **All six grips through the real N key** on downed AI dummies (spawned and downed through `NHTestBridge`; race set
  with `SetRace` on the test slot only): the gripper and victim clips both played, the victim was welded
  (`GripWeld` checked on the Human run), and every dummy died at the end of the clip (no test NPCs left).
- **VFX module runs:** effects spawned under `workspace.NHFx` mid-grip; no `[RaceGripFx]` warnings.
- **Screenshots** (`docs/img/260/`): Human struggle, Vampire bite, Werewolf maul, Wraith soul pull, Priest possession,
  Ghoul feed; Edit previews of the Vampire grab and bite.
- **Contact:** the generator's per-frame report: the victim's hands on the vampire's arm within 0.04 studs; the
  wraith's palm on the chest within 0.01; the ghoul victim's hand on the ghoul's head within 0.3; most attacker holds
  within 0.4; the werewolf's haul and the priest's head hold slip up to about 0.8 studs on the fastest jolts.

## Verified for 2.6.2
- **Edit:**
  - All 11 sequences were rebuilt in NH Combat Test.
  - A rig posed from GripHuman at 1.3 s stood beside one posed from the game's Crouch. Both lowest points were 0.41
    under the floor top, and the side views match.
  - The Vampire bite and the Priest exorcism were posed from the installed clips, victims at their offsets, and
    screenshotted.
- **Play, slot 4 "Testy", the real N key:** Human, Priest and Vampire grips on downed dummies (`NHTestBridge`).
  - Both clips played every time, and each victim died and was removed at the end.
  - Sampled on the client mid-grip, the player's torso dropped 0.93-1.13 (1.31 on the Priest's palm strike).
  - The lowest point was always the back knee, 0.40-0.42 into the real floor. The HRP stayed at standing height.
  - The hip transforms carried the slide; for example, the Human's Right Hip was (0.59, 1.37, 0.12) at 1.3 s, the
    pack's value.
  - The Vampire stood back up by 2.9 s.
  - The client played the test mirror's copies of the clips (see the 2.6.0 note below).
  - Testy is back to Human / Human, and the slot flags are restored.

## Verified for 2.7.1
- **Generator:** head aim per beat on all six grips, as above.
- **Play on Testy:** the Werewolf through the real N key, a Human dummy as the victim.
  - Face 47-62 deg down, within 8-23 deg of the chest through the maul; on the throat during the haul; 74 deg up for
    the howl.
  - The victim died at the end. Testy and the flags were restored.

## Not verified / known limits
- **2.7.1:** the new heads on the Human, Priest, Vampire, Wraith and Ghoul-victim clips were checked in the generator
  only, not in Play.
- **2.6.2:**
  - The Werewolf, Wraith and Ghoul-victim clips have not been play-tested.
  - No side-on screenshot of the player mid-grip: the grip camera stays behind the player.
- **The client view used a test mirror.** Studio's temporary preview ids registered on the server don't load on the
  client, so the screenshots came from a test-only script that played the client's own registered copy of each clip in
  step with the server's. Published ids don't have this problem, but the real replicated playback is untested until the
  owner publishes.
- **Sounds and the custom textures** are not uploaded, so they were not heard or seen in game (fallback art showed).
- Not run: a grip on a **real player** victim (two players), an **interrupted** racial grip releasing the weld (code
  read only), the sub-race richer effects, different heights between gripper and victim (the offset scales with the
  gripper only).
- **Testy side effects:** feeding as each race opened the rite quests (The Font Below, First Hunt, Shroud, Exorcism,
  Grave-eater) and a Crimson Court rank-up in Testy's journal, and the test ran through a class period (a skipped-class
  violation). Testy's race is back to Human / Human.
- **Not ported to the Map place.**
