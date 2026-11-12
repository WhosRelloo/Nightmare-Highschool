# 3D accessories (Kit A: player accessories; Kit B: the Headmaster's Circle)

Two approved kits of 3D accessories for the R6 body: **Kit A**, 28 player designs sold at the School Store, and
**Kit B**, "The Headmaster's Circle", 11 admin-only regalia pieces (`Admin = true`, never sold). The owner approved
both lists ("Make them all. I like it.") and the quality bar ("HIGH QUALITY WORK ONLY"), and set the fit rule:
**"Make sure nothing clips or overlaps or hovers."**

They're cosmetic only: no stats, and nothing reads or writes Race. The race-flavoured pieces can be worn by anyone.

R6 has no layered clothing, so every piece is a MeshPart riding one R6 part: either rigid, or rigged with bones that
`Controllers.Character.AccessorySway` swings (the same maths as HairSway).

Status: **Kits A and B are in the game** (NH Combat Test, 1.86.0): every batch imported, assembled in one pass and
play-tested together on slot 4, the rebuilt satchel and Head Student's sash included. The owner pre-approved every later batch "as long as they follow the standards" (2026-11-11). **All of both kits is
built** (batches 2-8: 49 more items, 2026-11-11), checked together with 0 fails, merged into `Config.Accessories`,
and in the game since 1.86.0. Kit C is in progress (below): C1 coats and C2 masks are **in the game** (1.87.1),
play-tested on slot 4.

## Batches

| Batch | Kit A / B | Items | State |
|---|---|---|---|
| 1 | A 1-6 | clique crest pins (8), Prefect and Head Student sashes, school tie, velvet bow tie, leather satchel, messenger bag, book strap, the Ink Club's chained grimoire, choir collar, falling ruff | **in the game, play-tested (1.79.0)**; satchel and Head sash rebuilt for the katana: **in the game (1.86.0)** |
| 2 | A 8-12 | tricorn, top hat, bowler (crimson bands), veiled mourning toque, fascinator, crooked witch hat, hunter's wide-brim, lace / bone / gilt masquerade half-masks | **in the game (1.86.0)**; staged in (`batch2/`) |
| 3 | A 13-16 | race-flavoured: opera-cape clasp, signet ring, moon-stone torc, wolf-tooth necklace, torn shoulder fur, lantern on a hook, grave-moss shawl, tattered hood, scythe pendant | **in the game (1.86.0)**; staged in (`batch3/`) |
| 4 | A 17-20 | hunter and armory: bandolier, pauldrons, gorget, bracers, gauntlets, back crossbow | **in the game (1.86.0)**; staged in (`batch4/`) |
| 5 | A 21-24 | magic: rune halo, orbiting sigils, a crow familiar, crystal pendant, potion belt | **in the game (1.86.0)**; staged in (`batch5/`) |
| 6 | A 25-28 | civilian: pocket watch, lace parasol, crook umbrella, candle lantern, knitted scarves (two colours) | **in the game (1.86.0)**; staged in (`batch6/`) |
| 7 | A 7 + B 2 | the Delinquents' long coat and the Headmaster's greatcoat (torso shell, sleeves on the arms, rigged split coattails) | **in the game (1.86.0)**; staged in (`batch7/`); hairs: see below |
| 8 (Kit B) | B 1, 3-11 | the Headmaster's Circle: crow mantle, thorned crown, raven-skull pauldron, iron keys, shadow trail, chained ledger, sigil halo, seal of office, signet, staff, observer mask | **in the game (1.86.0)**; staged in (`kitb/`) |
| C1-C2 (Kit C) | C 1-19 | 11 coats and jackets (skirts ride the legs: BodyFollow), 8 masks | **in the game, play-tested (1.87.1)**; staged in (`kitc/`) |

### Batches 2 to 8 (built 2026-11-11, in the game since 1.86.0)

Checked together with batch 1: `acc_check.py` **0 fails** over all 39 models (12 bodies, motion, sway limits, every
pair that can be worn together, the admin capes, the katana, each hair at the piece's fit). Contact sheets:
`img/accessories/batch2_sheet_a.jpg`, `batch2_sheet_b.jpg`, `batch3_sheet.jpg`, `batch4_sheet.jpg`, `batch5_sheet.jpg`, `batch6_sheet.jpg`.

| Batch | Items (hairs that can wear it, of 35) |
|---|---|
| 2 | tricorn (24), top hat (22), bowler (21), veiled mourning toque (10, Female), fascinator (24, Female), witch hat (23), hunter's wide-brim (22), lace / bone / gilt half-masks (15 / 11 / 11) |
| 3 | opera-cape clasp (32), bat signet ring (35), moonstone torc (10), wolf-fang necklace (11), torn shoulder fur (12), ghoul's lantern on the right hip (35, a light), grave-moss shawl (15), tattered hood (14; pale wisps drift off it), scythe pendant (8). Race-flavoured, anyone may wear them |
| 4 | bandolier (17), pauldrons (34), gorget (20), bracers (35), gauntlets (35), crossbow (21) |
| 5 | rune halo (30; it turns slowly in its own plane), orbiting sigils (35; four plates circle the head), crow familiar (18; it looks about, blinks, flicks its tail, settles its wings), caged crystal pendant (15), potion belt (32) |
| 6 | pocket watch (34), crook umbrella (35), lace parasol (35), candle lantern (35; a flickering light), striped / grey-violet scarves (4 each: almost every hair hangs where a scarf wraps the neck) |

What these batches added to the rules:
- **Hats at every hair's fit** (`acc_hatcapes.py`): the Midnight Lord's high collar meets every brimmed or veiled hat
  at some hair's fit, so it can't be worn with hats; the veiled toque can't be worn with capes or the crow.
- **Orbits are checked at every angle** (5 degree steps, the bob range, both hair-fit sizes), against bodies in both
  strides, hairs, hats at their fits, the capes and the other pieces (`nh_acc_batch5.py --motioncheck`).
- **The game's way of wearing a head piece** (scaled about the headband, lifted) is now what the checker tests for
  hair; the few hairs that cross a piece that way are ruled out (`hair_overrides.json`, applied by `acc_hairgroup.py`).
- **Pieces worn together share one hair fit** (a hat and its veil; `acc_hairgroup.py`).
- **A hood is a hat that reaches the shoulders**: its per-hair fits also keep it above the torso and out of the arms' swing (`acc_hoodfit.py`), which leaves 14 hairs.
- **Shared space across batches** became exclusive pairs: the crow vs the fur, the shawl and the hood; the crystal pendant vs the torc and the opera clasp.
- New slots: **Belt** (the potion belt) and **Watch** (the pocket watch); the bracers and gauntlets share **Arms**.

### Batch 7 (the coats) and Kit B (built 2026-11-11)

Final check over every built item (90 pieces, the katana and the five capes included, `--capes --hair`):
**`CHECK done 0 fails`**. Contact sheets: `img/accessories/batch7_sheet.jpg`, `kitb_sheet.jpg`.

| Item | Pieces, mount | Hairs (of 35) | Moves |
|---|---|---|---|
| Delinquent's Long Coat (Kit A 7, 1100) | shell (Torso), two sleeves (arms), two rigged coattails (Tails, locked fore-and-aft) | **4** (the shell) | the tails swing |
| Headmaster's Greatcoat (Kit B 2) | the same build in velvet, crimson lining and turnbacks, a gilt crow on the back | **4** (the shell) | the tails swing |
| Murder of Crows Mantle | feather mantle + two ember-eyed crows (Torso) | 6 | the crows look about, blink, flick their tails, settle their wings; a feather drifts off now and then |
| Crown of Thorned Brass | Head | 17 | the stone's glow breathes; a small crimson light |
| Raven-Skull Pauldron | left arm | 33 | ember eyes breathe |
| Three Iron Keys | Torso, orbiting the head | 35 | orbit 3 rpm, bob |
| Shadow Trail | a hidden anchor under the feet | 35 | dark smoke, a few feathers and rare embers while walking |
| Floating Chained Ledger | the book and its chain (right arm, the chain through a ring on a wrist cuff) | 35 | bobs; the pages turn over one by one, then settle |
| Crimson Sigil Halo | Head, behind it | 31 | turns in its own plane; **flares** when its wearer uses a staff teleport |
| Seal of Office | Torso (chest top) | 9 | |
| Headmaster's Signet | left hand | 35 | |
| Staff of Office | held in front of the right hand | 35 | the raven head's eyes breathe |
| Observer Half-Mask | Head | 13 | |

- **Admin only:** every Kit B item is `Admin = true`, has no price and is never sold or owned. It shows only in the
  Wardrobe's staff-only Admin tab, and the server refuses it on a non-staff player (the look check and `AccessoryWear`).
- **Regalia colour:** each Kit B item has `Tint` (`Ember` or `Crimson`). While regalia is worn, `AccessoryWear` sets
  `NHRegaliaTint` (Color3) and `NHRegalia` (the deciding item id) on the character: the most visible piece decides
  (halo, shoulders, hat, coat, held, collar, trail, familiar, face, ring). The staff teleport flock reads it to take
  the same colour (`Controllers.World.TpFlock`, 1.84.1: the birds' eye glints, the smoke and the motes).
- **The halo's flare:** `Features.Fx.VeilMove` stamps `NHAdminFlare` (server time) on a staff member's character when
  they teleport as their flock or move a student; an invisible staff member's move shows nothing (`install/patch_fx_flare.luau`).
- **The coats' hair limit (owner decision):** the coat shells fit only 4 of 35 hairs; even short cuts rest on the
  shoulder tops and the nape, where any coat goes. As built, putting on a coat refuses those hairs (and a hair change
  takes the coat off). Trimming the shoulders and scooping the nape gets 12-14 hairs; a full scoop gets 19 but no longer
  reads as a coat. Tails and sleeves fit all 35.
- **Exclusive with the coats:** every cape, sashes, bags, shoulders, arms, lapel pins, hip pieces, the belt, the watch,
  the crow familiar, the crystal pendant, the scarves, the torc, the fang necklace, the scythe pendant, the hood; and
  the regalia mantle, seal, ledger, pauldron and staff. The ties, bow tie, choir collar, ruff and gorget are compatible.
- **Kit B's own exclusions:** the mantle (neck, collar, sash, back, the crow familiar, the veiled toque, the hood);
  the seal (sashes, bags, the tie, the pendants, the furs, the crow); the halo (the brimmed and veiled hats, the hood,
  the Midnight collar); the ledger (arms, four capes); the staff (the blackened pauldrons, the Warden's mantle);
  the raven pauldron (the veiled toque).

## Any hair can wear any piece (1.88)

Owner: "Let players wear clothing their hair doesnt tuck, etc. for. It just wont have the new look for it." The hair no
longer rules a piece out. A hair a piece has no measured fit for (`NHHairFit` "x"), or whose tuck the hair's rig can't
take, still wears it:

- **Head pieces** sit at their default fit (the `*` entry: the generous end of the measured fits).
- **The hair isn't tucked** round that piece, so the two may overlap. That is the owner's call for this case only. The
  checks still measure every hair, and "fits" in the tables below means "gets the full look": a hair that fits gets the
  piece at its own measured size and its tuck.
- **The Wardrobe** lists such a piece as "(hair won't tuck)". Picking it wears it and says "this hair won't tuck round
  it, so they may overlap".
- **The server** no longer refuses the piece or takes it off on a hair change (`UI.Appearance`). The barber and the
  creator take nothing off.
- Conflict pairs (two pieces that pass through each other) are unchanged: still exclusive.

Changed in `UI.AccessoryWear` (`Wear.DefaultFit`; `FitsHair` now means "the full look"), `UI.Appearance` and
`Gui.Wardrobe` (`tools/accessories/install/patch_hair_open.luau`, backups in `NH_Backup.HairOpen_pre`).

## Hair tuck (hair that goes over, under or round a piece)

Owner: "For the coats and any other accessories, position the hair so that it wraps around them or under them, etc. so
it doesn't look like anything is clipping into each other and looks very natural and cool." Until now a piece simply
refused every hair that passed through it. Now, where it can be done cleanly, the hair moves instead.

**The rigs (v2).** The 35 catalog hairs were skinned almost entirely to their root bone (on Males_Long_Length_Messy
8,185 of 8,292 vertices): only the tips could move. `tools/hair-rig/nh_hair_autorig.py` now writes v2 weights: every
vertex follows its nearest lock chain, the crown stays on HairRoot (fading out over the first 0.16 studs of the lock),
and the weights are smoothed over the mesh's edges so each strand card bends as one piece. The bones are unchanged:
every bone's name and rest position, and every vertex at rest, match the hairs in the game exactly (checked on all 35).
**In the game since 1.85.1**: the owner imported `art/group-upload-hair-v2/` and `tools/hair-rig/swap_v2.luau` swapped
each catalog hair's Handle (backup: `ServerStorage.NH_Backup.Hair_v1`) and marked it `NHHairRig = 2`. Seen in Play on
slot 4: the straight bob lies over the falling ruff.

**The solve** (`art/characters/accessories/acc_hairtuck.py`). For every hair an item refused, it looks for the gentlest
turn of each lock's bones that clears the item, on the standard body and at the item's shallowest and deepest body
fits. A tuck is kept only if all of these hold, else the hair stays refused:
- no hair triangle crosses a piece triangle (the same test as `acc_check --hair`);
- no strand sinks into the head or torso further than at rest (the nape may sink a little where a collar hides it);
- strand cards are not stretched or crushed (the worst 0.5% of edges within 15%) or twisted against their neighbours
  (within 30 degrees);
- at most 3% of the head the hair covered at rest, and that the piece leaves in view, goes bare;
- bends near the scalp cost more than bends further down a lock (at most 40 degrees per bone axis).
Pieces that move on their own (orbits, bobs, idles: the crows, the ledger, the keys, the sigils, the halos) keep their
refusals: their tucks were only cleared at rest. Hats and masks gain little: what crosses them is the crown and the
fringe, which stay on the root bone.

**Result.** Every hair against every item that doesn't move (2,100 pairs), then `acc_tuckcheck.py` (below) until it
found nothing: **148 hair x item pairs are worn tucked**, and 31 items gained hairs:

| Item | Hairs before -> after (of 35) |
|---|---|
| Falling ruff | 22 -> 29 |
| Seal of Office | 9 -> 16 |
| Choir collar | 25 -> 30 |
| Moonstone torc | 10 -> 14 |
| Hunter's bandolier | 17 -> 21 |
| Prefect's sash | 17 -> 20 |
| Satchel, crossbow, gorget, scythe pendant | 20, 19, 20, 8 -> 23, 22, 23, 11 |
| Bow tie, messenger bag, fang necklace, moss shawl, tattered hood, crystal pendant, both scarves | +2 each (scarves 4 -> 6) |
| Raven pauldron, pauldrons, pocket watch, three crest pins | -> all 35 |
| Mourning toque, hunter's hat, bone mask, observer mask, potion belt | +1 each |
| **Long coat / greatcoat** | **4 -> 5** |

The coats gain least: the hair they cross lies on the shoulders and the nape, and a lock lifted over the collar on
the deepest body fit leaves the head bare. The check also found hairs that four items allowed but that crossed them
on some body type's depth fit (the old fit was measured on the standard body only). Those are refused now:
crimson fascinator 24 -> 23, opera clasp 32 -> 31, torn fur 12 -> 10, crow mantle 6 -> 4.

**Pairs and sway.** A tuck may not push hair into any other item the hair can wear with it (the solve keeps every such
item as an obstacle). `acc_tuckprune.py` drops the tucks the check still found unsafe in pairs (74, in
`tuck/drop.json`), so those hairs stay refused. A tucked lock holds still (`HairSway` `TUCK_SWAY = 0`): the tucks lay
the hair just clear of the piece, and at a 35% sway 73% of them swung back in.

**In the game.**
- Each item's pieces carry `NHHairTuck` (`acc_assemble.py` writes it from `tuck/<Model>.<LeadPiece>.json`).
- `UI.AccessoryWear` merges the tucks of everything worn (per bone, the larger turn) into the character's
  `NHHairTuck` and poses previews.
- `Controllers.Character.HairSway` eases the tuck in (about a quarter second); a tucked lock then holds still, the
  others sway as before.
- A hair that isn't a v2 rig is never turned, and a piece that needs a tuck for it isn't worn and isn't offered
  (`Wear.FitsHair`), so nothing changes until the hairs are imported.
- `acc_tuckcheck.py` checks it as the game wears it: each item alone, every two items worn together with their tucks
  merged (per bone, the larger turn), on the standard body and the shallowest and deepest body fits.

## Kit C, "The Night School Wardrobe" (in progress)

The owner approved the list (2026-11-11; spec `docs/superpowers/specs/2026-11-11-kit-c-concept.md`) and asked to start
with C1 (coats and jackets, 11) and C2 (masks, 8). Owner: "make sure all the 3d accessories and clothes are all rigged
for fluent movement with the R6 character". The varsity jacket is one school colourway and prices follow Kit A's range
(coats at the top); both were open questions the owner didn't answer, so these are defaults.

**Moving with the R6 body (`Controllers.Character.BodyFollow`, new, installed in NH Combat Test).** A Kit C coat's
skirts are one skinned piece (`<Coat>Skirt`, Torso mount, `NHFollow = "LL=1;RL=1"`) with a follow bone per leg
(`F_LL`, `F_RL`, children of Root, so `AccessorySway` never moves them). Every frame the controller sets each follow
bone's Transform so the vertices on it move exactly as the limb does: `M = rel * C1 * C0^-1` (the limb's motion in
the torso's space since rest, from the parts' own CFrames and the Motor6D's offsets), `Transform = B^-1 * M * B`
(B = the weld's offset times the bone's rest frame). Checked in Studio (Edit, `TransformedWorldCFrame`): a vertex on
the bone lands where the leg carries it to within 0.0000014 studs over five hip angles. **In Play (1.87.1)**, every
skirt and the Inverness cape, walking with the legs swinging to 53 degrees (the arms to 38): each follow bone sat
exactly where its limb carried it (0.0000 studs, every frame).

The character's Animator resets every bone's Transform each frame while a track plays (the walk), so BodyFollow sets
them in `PreRender`, after the animation step and before the frame is drawn. To measure it, read at `PreAnimation`
(the pose that was just drawn): after `Heartbeat` the Animator has already reset them, and a `PreRender:Wait()` resumes
before BodyFollow's own handler.

What the rig taught (`acc_check.py`, every body, the whole swing in 11-degree steps):
- **Each skirt half rides its leg entirely.** A skirt blended between the torso and the leg can't work on R6: the leg
  turns about the hip line at the torso's bottom centre, so its front face swings further than any part-turned cloth
  in front of it and comes through it, and cloth above the hip line turns the wrong way (into the torso). Riding the
  leg, the skirt's top slides into the torso as the leg swings forward, exactly as the leg's own top does, and drops
  below the coat's hem as it swings back.
- **A slit at each leg's front-outer corner** from the waist to z -1.80, where the panels join to the hem. Cloth over
  the left thigh's front-outer corner swings up into the sheathed katana's guard as the leg swings forward; every body
  type hit it at +44..+55 degrees, the standard body included. Below z -1.76 nothing can rise that far.
- **The skirt starts just below the shell's hem** (z -0.73, the shell ends at -0.72) and has its own depth fit,
  measured on the legs and the torso's lower part (`skirt_fit`): on the deep bodies the torso's fit pushed it off the
  legs into the guard.
- **New checker rules:** a skinned piece is bent the way BodyFollow bends it (`follow_deform`); a vertex that rides a
  limb entirely may go inside the torso as the limb swings (the limb's top does too; hidden), and the katana check
  doesn't count a riding vertex where the limb itself meets that katana part in that pose.

**Hair-friendly coats.** Hairs rest on the shoulder tops and the nape, where a coat goes (Kit A's coats fit 4 of 35
hairs). On the frock coat, long hair crossed the front of the shoulders near the neck and short cuts crossed the back
of the collar. Kit C's shell (`build_shell_k`) opens the neckline wider at the shoulders (`xo_top` 0.72) and scoops
the back neckline to z 0.78 at the centre, with a low collar that follows it down and lies flat on the back: the frock
coat's shell went from **4 to 15 of 35 hairs** before any hair tuck. The collar's fall stops at x 0.962: with the
wide neckline it reached the shoulder's edge, where the swung arm's top rises.

### C1 and C2: built, baked, staged (1.87.0)

| Id | Item | Price | Hairs with the full look (of 35) |
|---|---|---|---|
| `coat-scholar` | Scholar's Frock Coat | 1050 | 6 |
| `coat-inverness` | Inverness Cape-Coat | 1150 | 6 |
| `coat-chesterfield` | Chesterfield Overcoat (male) | 1100 | 9 |
| `coat-cadet` | Academy Cadet Coat | 1000 | 7 |
| `coat-lamplighter` | Lamplighter's Coat | 950 | 6 |
| `jacket-smoking` | Velvet Smoking Jacket | 950 | 7 |
| `cloak-oilskin` | Oilskin Rain Cloak | 900 | 7 |
| `jacket-spencer` | Crimson Spencer (female) | 900 | 9 |
| `jacket-varsity` | Nightmare Varsity Jacket | 850 | 8 |
| `jacket-hunting` | Waxed Hunting Jacket | 800 | 7 |
| `coat-cardigan` | Cable-Knit Cardigan Coat | 750 | 8 |
| `mask-watch` | Beaked Night-Watch Mask | 750 | 9 |
| `mask-kintsugi` | Kintsugi Porcelain Mask | 700 | 10 |
| `mask-wax` | Wax Saint Mask | 600 | 12 |
| `mask-moth` | Moth Mask | 600 | 12 |
| `mask-fox` | Fox Half-Mask | 550 | 11 |
| `mask-wolf` | Wolf Half-Mask | 550 | 9 |
| `mask-grille` | Iron Grille Mask | 500 | 10 |
| `mask-domino` | Black Silk Domino | 300 | 8 |

Contact sheets: `docs/img/accessories/kitc1_sheet_a.jpg`, `kitc1_sheet_b.jpg`, `kitc2_sheet.jpg`. Staged in
`art/group-upload-accessories/kitc/` (19 FBX, 70 maps).

**Covering the torso and arms** (owner: "Make the jackets cover the torso (In their respective designs)", then "Same
with the arms"). Each coat brings what's under it in its own design: a draped shirt with a cravat or tie, a waistcoat
clipped under the shell's opening, a jumper's neck. So the coats can't be worn with the Neck and Collar slots
(`Config.Accessories.Conflicts`). Sleeves run to the mid forearm (cuff at z -0.56, the inner edge stepping in below
the elbow): lower than that, the drawn katana's grip and the sheathed guard leave no room on the deep bodies. The hip
corners under the arms are their own pieces (`<Coat>HipsUp`, `<Coat>HipsLo`), each fitted per body from the cut edge,
because one fit for the whole corner hit the guard on the heavy and curvy bodies or hovered on the lean one. The short
jackets (varsity, hunting, smoking, spencer) use side panels in three bands instead.

**Hairs.** The hair tuck clears 3-6 more hairs per coat, but the tuck check (every body fit) found five long or
thick hairs crossing the shells that the hair fit had passed untucked (Males_TP_Locks, Males_Super_Messy_Long_Hair,
Males_Anime_Hero_Hair, Males_Black_Zoldyck_Hair, Females_Gojo_PonyV2), so those are refused: each coat fits **6-9 of
35** (Kit A's coats fit 4). `acc_tuckmerge.py` now applies a drop to a hair the item never needed a tuck for; before,
such drops were silently skipped. The masks were redesigned inside the brow line (x within 0.45, under z 1.78),
which lets 10-17 hairs through; the measured overrides for hairs that cross at the game's own hair scaling take each to
8-12. Masks can't be worn with the high-collared capes, the mourning toque's and the fascinator's veils, the thorned
crown (at its low hair fits) or the pieces at the chin (scarves, torc, hood, choir collar, the grille with every Neck
piece): 26 pairs.

**Kit A hairs the game still allows.** The merge fix also refuses 9 hair x item pairs in Kit A's layouts that an
earlier tuck check had dropped but the game's templates still allow: the ruff with the straight and wavy bobs, the
choir collar and the crystal pendant with Females_Natural_Trim_Pony, the moonstone torc with
Females_Long_Sweetheart_Pigtails, and the fang necklace, scythe pendant and both scarves with Females_Low_Ponytail.
In the game since 1.87.1 (`tools/accessories/refresh_hair_kita_drops.luau`; a dry run first showed exactly these 9
fits and their 9 tucks changing, nothing else).

**Checked:** `acc_check.py --capes --hair`, every Kit A, B and C piece together: 6 fails, all the fascinator's veil
over the grille, night-watch and wolf masks. Those became conflict pairs, and the masks and mourning hats re-checked
with 0 fails. `acc_tuckcheck.py` (every item alone and every
pair, three body fits): 0 fails.

**In the game (1.87.1).** The owner imported `kitc/`. 70 image ids read by name (no duplicates, all thumbnails
Completed), assembled in five parts (`tools/accessories/assemble_kitc_a..e.luau`, each under 65 KB). The importer
again put the rigs' bones on a separate part, so all 11 rigged pieces (9 skirts, the Inverness cape, the smoking
jacket's tails) were rebuilt from the builder's blends (`rebuild_bones_kitc.luau`): 3 bones each, 11 on the tails, all
skinned. Every piece has its maps, mount and fit; the in-game hair counts match the table above exactly.

Play test, slot 4 (Testy), through `UI.Appearance.ApplyTo`: all 11 coats and all 8 masks worn, each with a hair it
fits, none dropped, no console errors from accessories. BodyFollow was exact for every skirt (above). The smoking
jacket's tails swing (`Tails`, up to 10 degrees walking). Screenshots: the frock coat with the kintsugi mask (front,
side with the sheathed katana and the slit for its guard, back with the low ponytail tucked over the coat), the spencer
with the wax mask. Testy's saved look was unchanged afterwards. Not done: Wardrobe and Store clicks for Kit C, a
second player watching (BodyFollow runs for every character in range), the Map place.

**Next:** C8 bags, C9 extras, C5 hands and feet, C3, C4, C6, C7.

## The no-clipping rules (how "nothing clips, overlaps or hovers" is checked)

Every piece is measured by `art/characters/accessories/acc_check.py` (headless Blender), not judged by eye:

- **Bodies:** each piece against all 12 body types (the plain R6 boxes and the 11 meshed bodies of `docs/Body-Types.md`),
  after that body's depth fit. A vertex more than 0.003 studs inside a body fails; a piece that should rest on the body
  and sits more than 0.035 studs off it fails (hover).
- **Motion:** the arms and legs swung to +-55 degrees (the R6 walk's amplitude), and each rigged piece bent to its sway
  limit in every direction it may swing.
- **Other pieces:** every pair of pieces that can be worn together, at rest and with each swinging piece at its limits;
  and the five admin capes (`--capes`).
- **Hair** (head pieces, `acc_hairfit.py`): every rigged hair the barber sells, at its in-game size.
- **The katana** (1.79): the game's one sheathed weapon, measured in NH Combat Test (`E:/NH-Work/acc/katana_obstacles.json`,
  each part padded 12%): the scabbard at the left hip against every piece (rest, both strides, every sway limit, all
  12 bodies), and the drawn katana in the right hand against right-arm pieces.

### The katana (found in the 1.79 play-test)

The sheathed katana hangs at the **left hip**: its guard sits in front of the hip and the scabbard runs back along the
left side at hip height. In the first play-test it went straight through the satchel's bag (15 sample points inside),
and the new checker pass found the Head Student's sash crossing its guard on the deep bodies. So:

- **The left hip belongs to the sword.** The satchel is mirrored to the right hip (strap from the left shoulder), and
  the Head Student's sash now runs over the left shoulder to the right hip like the Prefect's (its rosette moved to
  the left breast). Hip pieces go on the right.
- **Held pieces are hidden while a weapon is drawn** (or a Tool is in the hand): the book strap hangs from the right
  hand, where the drawn katana's grip is. `Services.Features.Accessories` hides the Held slot's pieces while the
  Humanoid's `Equip` attribute is true.

What R6 forces, and how the kits deal with it:

- **The arms are flush on the torso's sides.** A strap round the torso has to pass under the arm. It lies in the arm's
  inner 0.1 studs, where the arm (which swings in its own plane) always covers it, so it reads as passing under the arm.
- **A striding leg's top corners poke out of the torso's lower front and back.** Sashes and straps cross the hips high,
  bags sit above that band, and hooks hang under the arms.
- **The head mesh dips about 0.12 studs below the torso top**, so collars and straps keep clear of the neck.
- **The only space no limb sweeps** is beside the hips under the arms (x > 1, z < -1). The satchel and the grimoire hang
  there, and swing only fore and aft (`NHSwayLock = "X"`); the tie swings only flat on the chest (`"Z"`).
- **Long hair over the neck and shoulders** (owner: "Rework them"): long hair hangs round the neck and down over the
  shoulders, chest and back (r 0.6 to 0.8 about the neck, z 0.85 to 1.35). So the choir collar is two lobes on the chest
  front and the ruff is a front "falling ruff" (a frill across the throat over a lace cascade); neither reaches the nape
  or the shoulder tops. Sashes cross the shoulder at x 0.92 and bag straps at x 0.86 (beyond that, a swinging arm's top
  corner rises through them).
- **Layers on the chest:** tie and pins on the shirt layer, sashes above, bag straps above those. Each piece's depth fit
  is per body, so `acc_check.py --fixlayers` raises an outer piece on a body only as far as needed to clear the inner
  pieces it crosses there (measured), and writes that back to the layout.
- **Every piece against every hair:** pieces that can't move (torso, limbs) are either clear of a hairstyle or not; a
  hairstyle that passes through a piece gets no fit for it (`NHHairFit` "x"), the same rule as hats. Since 1.88 it can
  still wear it, untucked (above).
- **Hats over hair:** a hat can't fit 35 hairstyles at one size. Each head piece carries a fit per rigged hair
  (`NHHairFit`: a uniform scale about the headband and a lift), the smallest one with no strand through it. A hair
  that would need more than the limit gets no fit. Before 1.88 it couldn't wear the piece; now it wears it at the
  default fit.

### What can't be worn together (`Config.Accessories.Conflicts`)

Some pairs would pass through each other whatever the geometry, so they're exclusive. Wearing one takes the other off
(the Wardrobe says what came off), and the server enforces it.

| Item or slot | Can't be worn with | Why |
|---|---|---|
| Choir collar | ties, sashes, bags | it covers the throat and the chest top |
| Falling ruff | ties | its frill and cascade cover the throat and the knot |
| a sash | bags, clique pins, the bow tie | the sashes cross the chest and back where those go (the flat school tie fits under) |
| every cape | bags, collars, sashes | capes hang over the back and both shoulders |
| Duelist's Shoulder Cape | clique pins, the bow tie | it crosses the left chest |
| Night Warden's Mantle | ties | it closes over the throat |
| Leather satchel | held pieces, hip pieces | it hangs on the right hip (away from the sword), where they hang too |

The Vamp, Rogue and Fur capes only exist in Studio; they follow the every-cape rule and haven't been measured.

### Hair compatibility (batch 1, the 35 rigged hairs, at rest)

| Piece | Hairs with the full look (any hair can wear it since 1.88) |
|---|---|
| School tie, book strap, grimoire | 35 |
| Clique pins | 34 |
| Bow tie | 31 |
| Messenger bag (the bag / its strap) | 30 / 20 |
| Choir collar | 25 |
| Falling ruff | 22 |
| Satchel (on the right since 1.79) | 20 |
| Prefect sash / Head Student sash | 17 / 17 |

Until 1.88 a hair change (barber, creator) took off any piece the new hair passed through. Now nothing comes off: the
piece stays, untucked.

What still stops the sashes and straps is very long hair hanging down the front of the chest, which any diagonal strap
crosses. Hair sway (HairSway bends strands as you move) isn't part of the check; only hair at rest is.

## How it works in the game

| Part | What |
|---|---|
| `ReplicatedStorage.Config.Accessories` | the item list (Id, Name, Slot, Model / Piece, Price, Gender, Clique, Admin, Tint), every batch merged in (an item stays hidden until its template is in `NHAccessories`: `Ready`), `Conflicts`, `Parse` / `Join` / `Resolve` / `Clean` / `CapeClash` |
| `ReplicatedStorage.UI.AccessoryWear` | wears the look's accessories: each piece on its R6 part, scaled to the part, deepened for the body type, fitted to the hair; Welds (so Height v2's stretch moves them) |
| `UI.Appearance` | look field `Acc` (comma list of ids, one per slot); `Sanitize`; `ApplyTo` calls `AccessoryWear.Wear`; the server's look check (owned or free in Studio, gender, staff for `Admin`, hair fit, cape clashes) |
| `Services.Player.Identity` | `Identity.Accessories`: owned ids (ProfileService through `SetIdentity`) |
| `Services.Features.Accessories` | the School Store sale: Yen, near `NHSchoolStore`, clique members only for clique pieces; remotes `NHAccRemotes` |
| `Controllers.Gui.Wardrobe` | the **Accessories** tab and the staff-only **Admin** tab (a wardrobe station shows Outfit, Accessories, Admin) |
| `Controllers.Gui.Enrollment` | the School Store's **Accessories** tab (the old stat-gear tab is now **Gear**) |
| `Controllers.Character.AccessorySway` | swings rigged pieces: profiles Flutter, Loops, Pendulum, BackHang, Tails; keep-out (never toward the body) and axis locks |
| `Controllers.Character.AccessoryFx` (1.79) | pieces' own motion and light: `NHOrbitAxis` / `NHOrbitRpm` (orbit about the mount), `NHBob`, `NHIdle` (a familiar's look / blink / tail / wings, a ledger's pages; bones in `NHIdleBones`), `NHPulse`, `NHFlare` (on `NHAdminFlare`), `NHTrail` (emitters while walking; any other emitter runs all the time), flickering lights; Reduce Motion tones it down and stops every emitter. Not used by batch 1 |
| `ReplicatedStorage.NHAccessories.<Item>` | templates (`tools/accessories/assemble_<batch>.luau` builds them from the owner's imports) |

Template attributes on each piece: `NHMount`, `NHFit` (on the nominal R6 part), `NHFitBody`, `NHSway`, `NHSwayKeepOut`,
`NHSwayLock`, `NHSeat` and `NHHairFit` (head pieces).

## The art pipeline

```
E:/Blender/blender.exe -b --factory-startup -P art/characters/accessories/nh_acc.py -- batch1 --gpu      # build, bake, export, render
E:/Blender/blender.exe -b --factory-startup -P art/characters/accessories/acc_check.py -- [--capes]     # the clearance check
E:/Blender/blender.exe -b --factory-startup -P art/characters/accessories/acc_hairfit.py               # head pieces vs every hair
python art/characters/accessories/acc_sheet.py out.jpg Item,Item                                        # contact sheets
python art/characters/accessories/acc_assemble.py batch1 Item,Item --ids ids.json                       # the Studio assembly script
python art/characters/accessories/acc_stage.py <folder> Item,Item [--suffix v2]                         # the upload folder (maps at 1024)
python art/characters/accessories/acc_textures.py                                                       # veil nets, lace (alpha)
```

- **Space:** studs on the nominal R6 body (torso 2 x 2 x 1 at the origin, head centre z 1.5), Blender -Y front, +X the
  character's left. FBX at `global_scale = 0.01`.
- **Maps:** one 2048 atlas per item (colour with baked AO, normal, roughness, metalness, an emissive mask for glowing
  parts), 64 samples on the GPU, from the props' 2048 PBR sets plus procedural cloth, velvet, metal and enamel.
  Veils and lace are alpha pieces (`AlphaMode Transparency`) with their own tiling textures.
- **Rigs:** `Root > H<n> > C<n>_<k>`, like the capes; pendulums keep everything above their pivot on `Root`.
- **Renders:** front, three-quarter, side, back and a close-up on the R6 mannequin, and on the Female body; head pieces
  on the game's own hairs (Males_Short, Females_Straight_Bob) at their in-game size.

## Verified

**Offline** (headless Blender): batch 1 passes `acc_check.py` with 0 fails on all 12 bodies, in motion, at every sway
limit, against every compatible piece, the five admin capes and the katana (the book strap is only reported against
the drawn katana: it's hidden while a weapon is drawn).

**In NH Combat Test, Studio Play, slot 4 "Testy" (Female body), 2026-11-11.** `Config.MainMenu.SlotCount = 4` and
`NHTestNoMenuKeys` during the test, both restored afterwards.

![Front](img/accessories/acc1_pt_front.jpg)

- **Templates:** the assembly built all 10 items (19 pieces) from the owner's import: every size matched the builder,
  every mesh came in upright, the swinging pieces carry their bones, all 38 maps set.
- **Wardrobe by real clicks** (locker-room station, E then the Accessories tab): the tab listed all 18 items by slot;
  the School Tie, Vigil pin, satchel, grimoire, book strap and Prefect's Sash went on and were saved to the profile.
  The Prefect's Sash took off the satchel and the pin (its exclusive pairs). The sash lies over the tie where they cross.
- **On the server character:** each piece welded to its part at its fit; the Female body's depth fit applied (the pin
  at z -0.472 = 0.902 x the nominal -0.523). Through the admin desk's Build remote: **Plus** deepened the satchel to
  1.204 and set the tie at z -0.632, **Petite** 0.965 and -0.550, exactly the fit table.
- **Swing, real held keys:** walking and turning (37 studs, 15.1 speed): book strap 16.3 deg, grimoire 9.2, tie 1.1;
  sprint and a jump (38.6): book strap 20.0, grimoire 7.4, tie 1.3; with the satchel, walk, strafe and sprint: satchel
  18.9. At rest 0.1 or less. All inside the limits the checker swept (Pendulum 34, Flutter 8).
- **School Store by real clicks:** the Accessories tab, other cliques' pins "Members only", Testy's own (Pack) pin
  bought for 180 (Yen 718 to 538, `Identity.Accessories` = pin-pack).
- **Server refusals** (the store remote): too far from the store, another clique's pin, buying twice, an unknown id.
- **Not staff** (`NHStaff` 0): the station showed Outfit and Accessories only, no Admin tab.
- **Console:** nothing from the new code (only the place's existing asset and sound messages).

**What the play-test changed** (all reinstalled in Edit, compiled, not yet re-played):
- the satchel and the Head Student's sash (see "The katana"), staged in `art/group-upload-accessories/batch1-fix/`;
- the Held slot hides while a weapon is drawn;
- a hair change at the barber kept a piece the new hair passes through (it wasn't drawn, but stayed in the saved
  look): the server now takes it off, the Wardrobe does too and says so, and the wear code leaves no empty holder;
- "Took off ..." messages stay up (they were replaced by "Saved to your profile" a second later);
- the store's header said "Uniform tops" over the accessories; each store card now shows the piece in 3D with its
  name and slot.

### The combined test (1.86.0, slot 4 "Testy", Studio Play)

The owner imported every remaining batch at once and asked for one assembly pass and one play-test.
- **IDs and templates:** 184 of 184 images read by name, all thumbnails Completed before any id was set; one
  assembly pass built 44 templates (52 with batch 1). Every piece checked in Studio against its build: size, upright,
  all maps, bones where rigged.
- **Bones lost on several-piece imports, rebuilt:** the importer puts a several-piece FBX's bones on a separate part
  of the imported model, and the assembly keeps only the named MeshParts, so 8 rigged pieces arrived skinned but
  boneless (both coats' tails, the scarves, the ledger, the mantle's crows). `acc_rebuild_bones.py` rebuilt them at
  the bind pose from the builds' rigs: the convention fitted on three single-piece imports to 0.0000018 studs. The
  assembly now reports any rigged piece without its bones.
- **Six outfits across every batch and Kit B** (`Appearance.ApplyTo`, looks not saved: Testy's profile unchanged):
  every kept piece was worn; the clash rules and hair refusals dropped exactly the expected pieces (Testy's very
  long hair refuses most head and back pieces; the short bob and Males_Short were used for coverage).
- **Motion on the client:** coat tails up to 12.5 degrees walking by real held keys; hair tuck held; crows' idle,
  ledger pages, orbits, pulses, trail, halo flare, regalia colour, flickering lights. No console lines from the
  accessory code.

## Not done yet

- A second play-test of the fixes above (the Held hide by a real draw, the barber taking a piece off, the store's 3D
  cards), a second player watching, NPCs (they don't wear accessories), combat animations (a swing of the sword
  isn't part of the check).
- Wardrobe and School Store clicks for the batch 2-8 items (1.86.0 wore them through `Appearance.ApplyTo`), a second
  player watching, combat animations. The orbits run slower on a client under 15 fps (`AccessoryFx` caps a frame's
  step at 1/15 s; seen at 16 fps in the 1.86.0 test).
- **Owner decision:** the coats' hair limit (above).
- **Seen in Play (1.86.0)**: the crows' and pages' bones move (the page-turn up to 142 degrees), the emitters run
  (the trail only while walking), the pulses, the halo's flare. **Not yet**: a real staff teleport's flare (the
  stamp was set by hand) and the emitters' look up close.
- The Vamp / Rogue / Fur capes against accessories (measure in Studio); built hairstyles and outside catalog hairs
  (a default fit, unverified).
- The Map place: `Config.Accessories`, `UI.AccessoryWear`, `Controllers.Character.AccessorySway` / `AccessoryFx`,
  `Services.Features.Accessories`, `ReplicatedStorage.NHAccessories`, and the `UI.Appearance`, `Player.Identity`,
  `Gui.Wardrobe`, `Gui.Enrollment` and `Features.Fx` (`patch_fx_flare`) patches (`tools/accessories/`).

**(1.86.1) In the Map place:** Kit A and Kit B with the Wardrobe tabs, the hair tuck and the regalia effects. Kit C and BodyFollow were not ported (paused).
