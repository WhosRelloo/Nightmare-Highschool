# Race transformations: design

- **Status:** concepts for the owner's pick. Nothing is built in the game yet.
- **Survey:** [`../research/2026-11-22-transformation-survey.md`](../research/2026-11-22-transformation-survey.md).
- **Concepts:** [`../mockups/2026-11-22-transformations/`](../mockups/2026-11-22-transformations/):
  - `races/`: per race, a lineup plus front and back of each direction;
  - `wings/`: 7 styles;
  - `horns/`: 7 styles;
  - `custom/`: palettes and finishes;
  - `anim/`: looping MP4s and GIFs of every wing style.

## 1. Owner rules (2026-11-22 / 23)

- **Quality:** cool, high quality and on theme (gothic, supernatural). No gore. Fitted to every body type and gender.
- **Animated and customizable**, with many wing **and** horn variations.
- **They still look a little like students:**
  - the face and the uniform stay readable;
  - **no werewolf muzzle and no fur on the head** (the ears stay);
  - **no Wraith lower-body shroud** (the legs and uniform show), and **Wraith heads kept clear** (no hood, no crown);
  - **no claws on any race**.
- **Sculpted geometry only**, built on PaintRigV3 proportions.

## 2. The forms

| Race | Direction | Silhouette | Parts |
|---|---|---|---|
| Vampire | **V1 Nocturne** | wings folded close like a cloak, long swept ears | Nocturne wings (bat, 4 digits, veined membrane, healed notch); ears |
| Vampire | **V2 Night Sovereign** | wings spread, horns swept back, a spined back | Wyrm wings (3 long digits, leading-edge spikes); Demon horns (ridged, twisted, Bloodstone tips); obsidian spines |
| Werewolf | **W1 Moonbound** | a fur mantle over the shoulders, fur cuffs, a bushy tail | layered fur locks on the shoulders, forearms and shins; wolf ears; tail. **No claws, no muzzle, no head fur.** |
| Werewolf | **W2 Feral Lord** | a heavier charcoal mantle down the arms and back | fur down the arms and back; glowing moon-mark crescents on the chest; tail. Same rules. |
| Ghoul | **G1 Ossuary** | a bone king: antlers, bone wings, ribs grown over the chest | Ossuary wings (bones with grave-cloth tatters); Wendigo antlers; rib plates, sternum, vertebral ridge, arm spurs, jaw guard |
| Ghoul | **G2 Gravecloth** | wound in grave linen, moss on the shoulders | linen wraps on the arms and chest, hanging tatters, grave-moss, iron coffin nails (in the cloth), the Thorn crown. No claws. |
| Wraith | **R1 Hollow Shroud** | a lit face, a tattered spectral capelet, veil wings | capelet open at the front; Wraithveil wings (a rippling mist membrane, trailing wisps). **Head clear, no claws; legs and uniform show.** |
| Wraith | **R2 Frost Revenant** | ice spikes at the shoulders, spectral chains, rime wings | shoulder spikes; a chain loop and a hanging chain; rime-crusted shins; Rime wings. **Head clear, no ice claws.** |

## 3. The wing library (7 styles, one skeleton)

Every style is generated from one jointed skeleton: humerus, forearm, 3 or 4 digits with knuckles, and clean tips (owner 2026-11-23: no thumb or fingertip hooks). That's why one animation rig drives them all.

| Style | Look | Default palette / finish |
|---|---|---|
| **Nocturne** | bat: 4 digits, scalloped membrane, raised veins, rim, a healed notch | Wine / Obsidian |
| **Wyrm** | drake: 3 long digits, thick bones, spikes down the leading edge | Wine / Bloodstone |
| **Tattered** | bat torn deep in every panel | Ashen / Bone |
| **Fallen** | raven feathers: primaries, secondaries, 3 rows of coverts, an iridescent sheen | Raven / Obsidian |
| **Ossuary** | bones only, grave-cloth tatters swaying between the digits | Wine / Bone |
| **Wraithveil** | a glowing mist membrane that ripples; wisps trail from every tip | Midnight / Ivory |
| **Rime** | an ice membrane, shards growing along the bones | Midnight / Ivory |

## 4. The horn library (7 styles)

All are ridged (annulated rings) and twisted, with a separate **tip finish**.

| Style | Look |
|---|---|
| **Ram** | a full coil beside each temple |
| **Demon** | long, swept back, the tip turning up |
| **Wendigo** | branching antlers with four tines each |
| **Thorn** | a crown of thorns round the head |
| **Broken** | one demon horn whole, the other snapped with a jagged end |
| **Sovereign** | tall upswept horns and a spiked halo standing behind the head |
| **Bull** | out to the sides, then forward and up |

## 5. Animation

| Piece | Motion | How |
|---|---|---|
| Wings, all styles | an idle breathe (a slow half-fold), a flap on sprint or jump (a 1.33 s loop), a fold on landing, flare on the transform | the shared wing skeleton is a **Bone rig in the MeshPart** (humerus, forearm, digit 1-4 with 2 bones each, thumb). One set of clips drives every style. The digits trail the arm (follow-through) |
| Feathers (Fallen) | the primaries flex with the stroke | bones per feather group |
| Tatters (Ossuary), wisps (Wraithveil) | sway and trail | bones on the strips |
| Veil membrane | a ripple across the panels | a looping bone wave |
| Tail (Werewolf) | the existing `TailSway` | the existing controller |
| Halo (Sovereign) | a slow spin | client tween |

- **The concepts animate the real geometry per frame** (shape keys from `hqwing.Wing.geom(fold, flap, lag, t)`). The clips in `anim/` show the exact motion the bone rig will reproduce.
- **Reduce Motion:** wings hold the idle pose, with no flap.

## 6. Customization (Bloodline → Looks)

Each slot is one Look option. Options unlock by tier, as the race Looks do now: Tier I gives the defaults, Tier II two more, Tier III the rest.

| Slot | Options | Races |
|---|---|---|
| Wing style | Nocturne, Wyrm, Tattered, Fallen, Ossuary, Wraithveil, Rime | Vampire: Nocturne, Wyrm, Tattered, Fallen. Ghoul: Ossuary. Wraith: Wraithveil, Rime, Tattered |
| Wing palette | Wine, Midnight, Ashen, Ember, Raven, Dove | all winged races |
| Bone finish | Obsidian, Bone, Gilded, Ivory, Bloodstone | all |
| Wing size | Small (0.8), Regular (1.0), Grand (1.2) | all |
| Horn style | Ram, Demon, Wendigo, Thorn, Broken, Sovereign, Bull, None | Vampire: Demon, Ram, Broken, Sovereign, Bull. Ghoul: Wendigo, Thorn, Ram |
| Horn finish and tip | Obsidian, Bone, Ivory, Bloodstone, Gilded | all |
| Fur colour, mantle | the existing 6 fur colours; Mantle: Shoulders (W1) or Full (W2) | Werewolf |

**Data:** this extends `PlayerData.Lineage.Looks` with the slots `WingStyle`, `WingPalette`, `WingFinish`, `WingSize`, `HornStyle`, `HornFinish` and `HornTip`. They're validated by `NHLineage.SetLook` and resolved by tier (`Lineage.ResolveLooks`).

## 7. Attachment and budgets

- **Wings:** one skinned MeshPart per wing per style, rigged with the shared skeleton. It's welded to the Torso at the shoulder-blade attachment and scaled by height.
  - About 8 to 14k tris per wing.
  - SurfaceAppearance 1024² for the membrane or feathers, 512² for the bones.
- **Horns:** one MeshPart per style (both horns), welded to the Head, scaled by height. 4 to 6k tris, 512² plus the tip.
- **Fur, bone, wraps, ice:** per body, raycast-fitted variants of one mesh per region (12 bodies), welded to their R6 parts.
  - Fur is shingled locks in one mesh per region, about 6 to 9k tris per region.
- **Palettes and finishes** are material swaps: one SurfaceAppearance set per palette, shared across styles.
- **Layering:**
  - wings sit behind capes; while transformed the cape folds away;
  - horns clear hats and hoods (hats are hidden while transformed);
  - fur goes over the transformed outfit.
- **Animation compatibility:** all existing R6 clips play unchanged. The augmentations are welded parts, and only the wing and tail bones animate on their own.

## 8. Open questions for the owner

1. **Pick per race:** V1 or V2, W1 or W2, G1 or G2, R1 or R2, or let players choose the direction too (it fits as one more Look slot)?
2. **Which wing and horn styles each race may use:** the table in §6 is a proposal.
3. **Priests and Humans:** should a Priest get a "Sanctified" form (Fallen wings in Dove, the Sovereign halo), and should Humans stay untransformed?
4. **Unlocks:** are all styles earned by tier, or are some sold in the Spin Shop?
