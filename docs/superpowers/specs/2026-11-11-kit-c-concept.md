# Kit C, "The Night School Wardrobe": concept (2026-11-11)

Owner: "create a huge kit for 3D clothing and accessories full of coats, jackets, masks, etc. and even more cool stuff
on theme with the game. Same quality of course." This is the proposal: the list and seven concept pieces (published for review: https://claude.ai/artifact/BUFm5jgdRTG9VCLZjUY9no). Nothing is
built for the game until the owner approves it.

The theme is a gothic night boarding school: crimson #600E1A, black, brass, bone, wax and ink.

## How it's made (the same as Kits A and B)
- Modelled in Blender, 2048 PBR bakes at 64 samples, clean topology.
- Swinging parts are rigged for the sway systems.
- Fitted to all 12 body types and Height v2.
- Proven with the clearance checker: nothing clips, overlaps or hovers, on every body, against every other piece and
  cape, the katana, and every hair. Hair tuck (1.85) lays hair over or round a piece where it can.
- Gender tags, Wardrobe and School Store entries, batch renders for approval, and records.

**Rigged to move with the R6 body (owner: "make sure all the 3d accessories and clothes are all rigged for fluent
movement with the R6 character").** An R6 character is rigid parts turning at the shoulders, hips and neck, so:
- **A piece on one part** (a mask on the head, boots on a leg, a glove on an arm) is welded to that part and moves with
  it exactly.
- **A piece that crosses a joint** (a coat's body and sleeves, a long skirt over the hips, a cloak over the shoulders)
  is one skinned mesh with bones at the joint. A client controller (`Controllers.Character.BodyFollow`, new) turns
  those bones every frame to match the R6 joint (the Shoulder and Hip Motor6Ds' own turn), so the sleeve bends out of
  the coat instead of a rigid sleeve sliding past a rigid shoulder. The weights blend across the joint, like a real
  garment.
- **Anything that hangs or swings** (tails, hems, straps, tassels, charms, a capelet) keeps its sway bones on top.
- **The checker proves it in motion:** every piece at the arms' and legs' full swing (every 5 degrees, both strides),
  not only at rest.
- **Retrofit:** the long coat and the greatcoat are rebuilt this way (one skinned coat each, the shoulder blended), and
  every Kit A and B piece is checked for any other part that crosses a joint.

**Legwear on R6:** the two leg blocks touch, with no gap between them. Boots, spats, stockings and skirt hems cover the
outer, front and back faces and stay flush on the inner face, and the toes stop short of the centre line, so the two
legs never pass through each other's piece when walking.

**Backpacks (owner, 2026-11-11: "Make the backpack straps, wrap around the character"; "Add another horizontal strap
that connects the straps going down, which would wrap around the torso. Remember this for when I ask you to make more
backpacks"):** every backpack's shoulder straps are loops hugging the torso (over the shoulder clear of the head, down
the chest slanting out to the armpit, under the arm and up the back), with a horizontal strap round the torso over them
and a front buckle; its back run tucks into the pack's sides, and the pack ties onto the straps on the back. The coffin
backpack concept is built this way (`docs/img/kitc/coffin_straps.jpg`).

**Lesson from the coats:** a collar that rises at the back of the neck clashes with almost every hairstyle (the long coat
fits 5 of 35). Every Kit C coat and jacket gets a low, open collar at the nape, aiming at 15 or more hairs each.

**New slots:** Gloves, Boots, Eyes (glasses, monocles) and Ears. The rest use the slots that already exist.

## Not repeated (already made or planned)
- **Kit A:** pins, sashes, ties, satchel, messenger bag, book strap, grimoire, choir collar, ruff, the hats (tricorn, top
  hat, bowler, toque, fascinator, witch, hunter's), lace, bone and gilt masks, the race pieces, the hunter set
  (bandolier, pauldrons, gorget, bracers, gauntlets, crossbow), halos, sigils, the crow familiar, crystal pendant, potion
  belt, pocket watch, umbrellas, candle lantern, knitted scarves, the long coat.
- **Kit B:** the regalia and the greatcoat.
- **Capes:** the five admin capes, and the Vamp, Rogue and Fur capes.
- **2D clothing:** the uniforms, the schoolgirl and civilian kits (one has a 2D varsity jacket; the one here is a 3D
  unisex coat), and the admin outfits.
- **QOL items:** lantern, map, compass, umbrella, timetable, keys, hall pass, library book, thermos, snack tin, first-aid
  pouch, hand warmer.
- **The Lord kits and the Sanguine Atelier** (frock coat with silver buckles, tricorn, gorget, bandolier, opera
  tailcoat, fur mantle, painter's gloves, crimson cravat and the rest).

## The list (66 designs, 9 batches)

### C1 Coats and jackets (11)
| Design | Look | Gender |
|---|---|---|
| Scholar's frock coat | charcoal wool, ink-blue silk lining, brass inkwell buttons, a pen-nib pin; knee-length skirts that swing | Unisex |
| Inverness cape-coat | black houndstooth wool with a short shoulder capelet that swings | Unisex |
| Academy cadet coat | military cut, double-breasted brass, crimson frogging and piping, a low stand collar | Unisex |
| **Varsity jacket** (concept) | crimson wool, cream leather sleeves, a chenille N, NIGHTMARE across the back; a colourway per clique | Unisex |
| Waxed hunting jacket | black-olive waxed canvas, corduroy collar, brass grommets, game pockets | Unisex |
| Oilskin rain cloak | cape sleeves, toggle fastenings, the hood worn down, a swinging hem | Unisex |
| Velvet smoking jacket | crimson quilted velvet, black satin shawl collar, a tasselled sash (for dorm nights) | Unisex |
| Lamplighter's coat | long oilcloth, a brass-buttoned storm flap, a lamp hook at the hip | Unisex |
| Crimson spencer | a cropped fitted jacket, puffed shoulders, black braid trim | Female |
| Chesterfield overcoat | black wool, velvet collar, hidden buttons | Male |
| Cable-knit cardigan coat | long, shawl collar, ink-blue, horn toggles | Unisex |

### C2 Masks (8)
| Design | Look |
|---|---|
| **Beaked night-watch mask** (concept) | leather, a long stitched beak with brass bands, round crimson-glass lenses; plague-doctor style, nothing medical or gory |
| **Kintsugi porcelain mask** (concept) | white porcelain mended with a gold seam, painted crimson lips and a painted tear-mark |
| Fox half-mask | black lacquer, crimson markings, silk tassels |
| Wolf half-mask | silver-grey, muzzle to the nose (anyone may wear it) |
| Iron grille mask | the lower face, riveted bars |
| Wax saint mask | candle wax, softened edges that have run like a candle (wax, never skin) |
| Moth mask | velvet moth wings across the eyes, feathered antennae |
| Black silk domino | simple and flush to the face (the most hair-friendly) |

Masks sit on the face, where fringes fall; hair tuck can't move a fringe (it stays on the root bone). Expect 12 to 25
hairs each, as with Kit A's masks.

### C3 Headwear (8)
Cadet peaked cap with a crest badge and chin strap; velvet beret with a crest pin, worn tilted; tweed flat cap; knitted
earflap hat with a pompom; big crimson velvet hair bow (Female); brass oak-leaf circlet; lace mantilla comb (Female);
a quill tucked behind the ear.

### C4 Eyes and ears (6)
**Brass monocle on a chain** (concept); round wire spectacles; smoked-glass brass goggles; pince-nez on a ribbon;
crimson drop earrings (Female); silver ear cuffs.

### C5 Hands and feet (8)
Fingerless leather gloves with brass studs; long lace evening gloves (Female); riding gloves with brass cuff buttons;
knitted mittens on a cord; **buckled knee boots** (concept); lace-up heeled boots (Female); canvas spats; fur-cuffed
winter boots.

### C6 Belts and harnesses (5)
Chest harness with crossed straps and brass rings; corset belt (Female); a chain belt with charms (crescent, key,
skull); a thigh holster of quills and an inkwell; a spyglass in a shoulder holster.

### C7 Jewellery and neckwear (8)
Cameo choker on black velvet (Female); a crescent locket; an enamel moth brooch; a hinged ruby ring with a secret
compartment; a charm bracelet; a black silk ascot with a pearl pin; a velvet tasselled stole; a black lace capelet
(Female).

### C8 Bags and things on the back (6)
**Coffin backpack** (concept); a bat-wing backpack whose wings stir as you run; a violin case; an alchemist's Gladstone
bag (held); a scroll tube; a birdcage purse with a paper moth inside (Female, held).

### C9 Night extras (6)
**Floating candelabra** (concept: three wax candles that hover over the shoulder and flicker); a black cat on the
shoulder (it blinks, flicks its ears and tail); a bat familiar; a halo of paper moths; a wax-sealed letter in the breast
pocket; a clockwork wind-up key in the back.

## Suggested order
C1 coats and C2 masks first (the headline pieces), then C8 bags and C9 extras (the fun ones), then C5 hands and feet
(they need the new Gloves and Boots slots), then C3, C4, C6 and C7.

## Questions for the owner
- Is the list right? Anything to add, drop or swap?
- Should the varsity jacket come in all 8 clique colourways (members only, like the pins) or one school colourway?
- Prices: Kit A runs from 120 to 1,100 Yen. Same range for Kit C, with coats at the top?
