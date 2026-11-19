# Path wardrobe (2.34): import pack

The Standing Path rewards from docs/expansion/14-Progression-and-Identity.md §6.1. All of them are earned and never sold:
each one is granted when your path reaches its tier.

## 3D accessories (import into NH Combat Test)

Each accessory is one FBX plus four 1024 PBR maps (color, metalness, normal, roughness). Upload the maps to group 15981569
as Images, and import the FBX with the 3D Importer.

| File | Item | Unlock | Pieces |
|---|---|---|---|
| `NHAcc_AcademicPin.fbx` | Academic Pin: a gilt lapel brooch with a crimson enamel field, an ivory open book with gilt ruled lines, a gilt quill and two crimson silk tails | Academic 3, Honor Student | `AcademicPin` (Torso) |
| `NHAcc_KnuckleWraps.fbx` | Scarred Knuckle Wraps: worn linen tape wound over both hands with a figure-eight across the knuckles, scuffed knuckle turns, a black leather wrist band with a brass stud, frayed loose ends. No blood. | Combat 4, Notorious | `WrapL` (LeftArm), `WrapR` (RightArm) |
| `NHAcc_SilverSigil.fbx` | Silver Sigil: a silver pendant on a fine chain over the collar, with a black enamel field, a crescent moon, a seven-point star and a moonstone with a faint cold glow | Supernatural 4, Keeper of Secrets | `SilverSigil` (Torso), `SilverSigilStone` (Torso, Neon, no maps) |

Source: `art/characters/accessories/nh_acc_batchp1.py`. Built on the R6 accessory rig (the `nh_acc` space) and baked at
2048, then scaled to 1024 here.

## School tops (upload as Shirts or Images)

Classic 585 x 559 shirt templates. Source: `art/clothing/tools/pathwear.py`.

| File | Top | Unlock |
|---|---|---|
| `shirt_path_rolled_sleeves.png` | Rolled Sleeves: the navy vest uniform with sleeves rolled to the elbow | Social 3, Popular |
| `shirt_path_loose_tie.png` | Loosened Tie: the charcoal vest with the collar undone and the tie pulled loose and askew | Combat 3, Enforcer |
| `shirt_path_worn_blazer.png` | Worn Blazer: an old crest blazer, faded, with leather elbow patches, frayed cuffs, a darned tear and tarnished buttons | Supernatural 3, Initiated |

The fourth top, the Varsity Jacket (Athletic 3), is already in the game.

## After import

Claude reads the image ids by name, builds `ReplicatedStorage.NHAccessories.{AcademicPin, KnuckleWraps, SilverSigil}`
(`acc_assemble.py`), and adds the three tops to `UI.Appearance.Uniforms` marked `Earned`. The game code is already in:
grants on tier, the backfill for tiers reached earlier, and no store or NPC use.
