# Beasts kit: design (approved 2026-11-05)

Owner: "make a kit for rigged and animated beasts for the game (I want them to have an idle animation, walk animation, run animation, 2 hit animation variants, 2 stun variants, a block break variant, and a death animation. SOME should have an extra 1-2 unique animations depending on what they are)".

Owner's choices:
- **Beasts:** Hellhound, Grave Ghoul, Stone Gargoyle, Bone Spider, Night Stalker, Crypt Bat.
- **"2 hit animation variants" means its attacks** (two attack swings, like the wolf's Bite1 / Bite2).
- **Animation:** published keyframed clips, like the wolf's.
- **Where:** night roaming plus a lair for each beast.
- **Toughness:** a range.
- **The code:** a new shared Beasts system; the wolves stay as they are.
- **Rewards:** EXP and Yen, plus trophies.

## The system

- **`ServerScriptService.Services.Features.Beasts`** (server), built from `Features.WildWolves`. It runs every beast from data and leaves the wolves untouched.
- **`ReplicatedStorage.Config.Beasts`:** one entry per beast. Each entry has:
  - `Model`: the template name in `ServerStorage.NHBeasts`;
  - stats: `Health`, `WalkSpeed`, `RunSpeed`, `Sight`;
  - a fixed attack `Pattern`: a list of steps, each `{ Clip, Range, Damage, Tell, Hit, Recover, Move }`;
  - its unique moves (`Specials`), each with its own hook in the system;
  - `Spawn`: `Night`, `Max`, `Respawn`, and which lairs;
  - `Reward`: `Exp`, `Yen` and `Trophy` with its chance.
- **The wolf rules hold for every beast:**
  - a red tell before every attack;
  - one beast attacks a given student at a time while the rest circle;
  - your hits stun it (`Stun1` or `Stun2`), and posture break (`Paralyzed`) plays `GuardBroken`;
  - its damage goes through `Downed.ApplyDamage`, so a beast can down a student but never execute one;
  - its death plays `Death`, then pays the killer through the reward path and fades the body.
  - Beasts are `NoDowned`: they die outright.
- **Clips per beast** (`Animation` objects in the template's `Animations` folder): `Idle`, `Walk`, `Run`, `Attack1`, `Attack2`, `Stun1`, `Stun2`, `GuardBroken`, `Death`, plus 1 or 2 unique clips.
  - The attack clips carry `Hit` and `EndLag` keyframe markers.
  - A fallback in `Config.Beasts.<Beast>.Markers` covers a clip without them, as `Config.Weapons.Fist.Markers` does.
- **Spawning:**
  - **Night roaming** after dark (19:30 to 05:30), away from the school, gone by morning.
  - **Lairs:** parts tagged `NHBeastLair` with a `Beast` attribute (graveyard: ghouls; woods and cellars: spiders; rooftops: gargoyles; bell tower: bats; boiler yard: hellhounds).
  - Placeholder lairs go in NH Combat Test; the builder tags the real spots in the Map place later.
- **Trophies:** a rare drop into the inventory, one per beast. A bat's wing-claw, a spider's fang, a ghoul's grave-dirt locket, the stalker's finger-bone, a hellhound's ember-tooth, a gargoyle's stone chip.
- **Admin:** the admin panel's Spawns can spawn any beast.

## The beasts

| Beast | Look | HP (wolf 70) | Attacks | Unique |
|---|---|---|---|---|
| Crypt Bat | a 4-stud bat, torn wings | ~50 | two claw rakes | `Dive` (a swooping dive); `Screech` (a short stun in a cone) |
| Bone Spider | 6 studs across, bone and black chitin | ~65 | two fang strikes | `WebSpit` (slows you); climbs walls |
| Grave Ghoul | a gaunt grey crawler, human height (no blood or gore) | ~110 | two claw swipes | `Emerge` (bursts out of the ground in ambush); `Grab` (a lunging grab) |
| Night Stalker | 9 studs tall, thin, long-armed | ~130 | two long swipes | `Freeze` (doesn't move while a student looks at it); `Reach` (a long-reach swipe) |
| Hellhound | bigger than a wolf, charred hide with ember cracks, ember eyes | ~220 (mini-boss) | two bites | `FireBreath` (a cone); `Pounce` |
| Stone Gargoyle | sits as a statue on a ledge until you pass | ~250 (mini-boss) | two claw strikes | `Wake` (wakes and drops on you); `WingBuffet` (knockback) |

## The art

- **Models:** in Blender at the dead oak's standard (`art/props/nh_props_batch33.py`).
  - A creature skeleton is skinned into one mesh (Skin modifier), smoothed and given form.
  - Baked PBR maps at 2048 with 64 GPU samples.
  - Glowing parts (eyes, the hellhound's mouth and cracks) are separate Neon pieces, skinned to the same rig.
  - Each mesh stays under 20k triangles.
- **Rigs:** an armature with readable bone names (`Pelvis`, `Spine1`, `Chest`, `Neck`, `Head`, `Jaw`, `Tail1-4`, `FL_Upper` / `FL_Lower` / `FL_Foot` and so on).
  - Weights go to the nearest bones.
  - It's exported with the meshes (`nh_props.RIGS`).
  - In Roblox, a Humanoid on the root (renamed `HumanoidRootPart`) drives movement and an Animator plays the clips.
- **Clips:** built in Studio on the imported rig, as KeyframeSequences on its Bones with `Hit` / `EndLag` markers, and published by the owner, about 10 per beast.

## Build order

1. **Hellhound first, end to end:** the model, its rig, its clips, the owner's publishing, `Features.Beasts` and `Config.Beasts`, a fight test in Play. It proves the pipeline.
2. **Then, one at a time, each released on its own:** the Grave Ghoul, the Bone Spider, the Crypt Bat, the Night Stalker, the Stone Gargoyle.
