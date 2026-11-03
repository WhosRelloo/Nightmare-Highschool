# Nightmare Highschool: clothing variants

Classic clothing templates in five sets (42 in the first three), made from the six templates in `../source/`:

| Set | Pieces | Sheet |
|---|---|---|
| School uniform variants | 14 shirts, 7 pants | `contact_sheet.png` |
| Civilian (off-duty) clothes | 6 shirts, 5 pants | `contact_sheet_civilian.png` |
| Transformation outfits | 5 shirt + pants pairs | `contact_sheet_forms.png` |
| Female outfits (1.13.0, `tools/female.py`) | 7 tops + 7 skirts: sailor, chapel corset, bolero pinafore, cheer, lolita dress, cable-knit with plaid mini, gala gown | `contact_sheet_female.png` |
| Transformation outfits 2 (1.13.0, `tools/forms2.py`) | uniform versions of the Vampire, Wolf, Ghoul and Wraith shirts (worn over your own bottoms), and female Vampire (Countess) and Wraith (Banshee) pairs | `contact_sheet_forms2.png` |

- Every file is a 585x559 RGBA PNG on the classic Roblox shirt/pants layout. Use shirts for `Shirt.ShirtTemplate` and pants for `Pants.PantsTemplate`.
- Transparent areas follow the sources: the neck hole and margins of shirts are transparent, and pants keep the jeans' black margin and see-through upper torso panel.
- See-through parts of a limb show the character's skin. The shorts, skirt, rolled sleeves, short PE sleeves and jean rips rely on this.
- The magenta guide lines from the vest sources are removed. The "please roblox :(" note from the maroon polo is removed.
- All art is original, made from the user's own templates. The serif "NH" monogram is the one from `shirt_black_polo_khaki.png`, re-tinted, or redrawn in Georgia Bold where it needed to be larger.

Each contact sheet shows every piece as a template plus front and back mock-ups. On the uniform sheet, shirts are shown over the charcoal slacks and pants under the black polo. On the other two sheets, each piece is shown with its suggested match.

All three sets have the same quality pass. It covers:

- Shapes, lines and text drawn at 4x and averaged down, so edges are smooth.
- Rounded shading on every face, and darker shading where the arms and legs touch the body.
- Soft shadows under raised details: lapels, pockets, straps, chains, stoles, emblems and the cravat.
- Fur drawn at 2x, in clumps that run dark at the root to light at the tip.
- Creases at the elbows and knees.

## Uniform shirts

| File | What it is | Made from | Asset id |
|---|---|---|---|
| `shirt_vest_navy_ivory.png` | Navy sweater vest, ivory shirt, olive-gold trim, gold NH | maroon vest (texture) + black/red vest (shared layout) | `rbxassetid://131331968799241` |
| `shirt_vest_forest_cream.png` | Forest-green vest, cream shirt, gold NH | maroon vest + black/red vest | `rbxassetid://84070769570999` |
| `shirt_vest_charcoal_crimson.png` | Charcoal vest over crimson sleeves, white shirt in the V | maroon vest + black/red vest | `rbxassetid://129707810933747` |
| `shirt_vest_vigil_ivory_gold.png` | **The Vigil**: ivory vest, black sleeves, candle-gold trim, dark NH | maroon vest + black/red vest | `rbxassetid://103939605140092` |
| `shirt_vest_crimson_court.png` | **The Crimson Court**: blood-red vest, black sleeves, dark crimson trim | maroon vest + black/red vest | `rbxassetid://132432469548353` |
| `shirt_polo_navy_khaki.png` | Navy polo, light-grey collar, khaki tuck | maroon polo; NH from black polo | `rbxassetid://77872145794481` |
| `shirt_polo_forest_khaki.png` | Forest polo, cream collar, khaki tuck | maroon polo; NH from black polo | `rbxassetid://119718830007823` |
| `shirt_polo_ivory_crimson.png` | Ivory polo, crimson collar and cuffs, crimson NH | maroon polo; NH from black polo | `rbxassetid://105833892962820` |
| `shirt_polo_crimson_charcoal.png` | Crimson polo, charcoal collar, charcoal tuck | maroon polo; NH from black polo | `rbxassetid://88266973360357` |
| `shirt_polo_delinquent.png` | Delinquent: untucked ragged hem, rolled sleeves, open collar, loose striped tie, scuffs, a stitched tear | maroon polo; NH from black polo | `rbxassetid://91697438455703` |
| `shirt_blazer_black_crest.png` | Black blazer: crimson piping, notch lapels, white shirt, crimson/gold tie, NH crest pocket, gold buttons and cuff buttons | new; shirt collar from maroon polo | `rbxassetid://137306354290763` |
| `shirt_cardigan_charcoal_crest.png` | Charcoal knit cardigan: gold V trim, button placket, patch pockets, NH crest, ribbed cuffs, tie | maroon vest + black/red vest | `rbxassetid://76454801064615` |
| `shirt_varsity_jacket.png` | Varsity jacket: black wool body, crimson leather sleeves, striped rib collar/cuffs/hem, snaps, chenille NH; "NIGHTMARE" arched over a big NH on the back | new; neck from maroon polo | `rbxassetid://94185062881754` |
| `shirt_gym_pe.png` | PE shirt: ivory jersey, crimson crew neck, side stripes and short-sleeve cuffs, "NH / ATHLETICS"; "PROPERTY OF N.H. ATHLETIC DEPT." on the back | new; neck from maroon polo | `rbxassetid://85944456848493` |

## Uniform pants

| File | What it is | Made from | Asset id |
|---|---|---|---|
| `pants_jeans_dark_indigo.png` | Dark indigo wash, copper thread on the brightest stitching | `pants_jeans_a.png` | `rbxassetid://121799939715098` |
| `pants_jeans_black.png` | Black denim | `pants_jeans_b.png` | `rbxassetid://110540994331632` |
| `pants_jeans_ripped.png` | Grey jeans with bleached knees and rips (white threads across, skin shows through) | `pants_jeans_a.png` | `rbxassetid://90868263081350` |
| `pants_slacks_charcoal.png` | Charcoal slacks: pressed crease, black belt with gold buckle, black school shoes | new; jeans layout and see-through panel | `rbxassetid://130098092880820` |
| `pants_trousers_khaki.png` | Khaki trousers (matches the polo khaki): brown belt, school shoes | new; jeans layout | `rbxassetid://89680994163406` |
| `pants_shorts_khaki.png` | Khaki uniform shorts, bare knees, ivory socks with crimson and gold bands, school shoes | new; jeans layout | `rbxassetid://96381649874363` |
| `pants_skirt_pleated_tartan.png` | Pleated skirt in an original crimson/black/gold/navy tartan, black waistband, dark knee socks, school shoes | new; jeans layout | `rbxassetid://100333616291892` |

These are the ids of the upgraded uniforms. The first uploads, from before the quality pass, had different ids; they still work, but they show the older art. The swap list from old to new ids is in the shared notes folder, as `clothing-uniform-hq-id-swap.tsv`.

The same ids are in `asset_ids.json`. They were uploaded on 2026-10-30 from Studio ("NH Combat Test", placeId 98950102230473) with the Studio MCP `upload_image` tool, so they belong to the account Studio was signed in with.

## Civilian clothes

Off-duty streetwear in the school's crimson, black and gold. "Pairs with" is the suggested match shown on the sheet.

| File | What it is | Pairs with | Asset id |
|---|---|---|---|
| `shirt_civ_hoodie_blood_moon.png` | Charcoal hoodie with crimson-lined hood, drawstrings, kangaroo pocket, dripping "blood moon" crescent + "AFTER DARK"; large distressed crescent and "NIGHTMARE" on the back | joggers | `rbxassetid://90914064708461` |
| `shirt_civ_leather_jacket.png` | Black leather biker jacket: notched lapels with studs, gold zips, belt, epaulettes, back yoke; crimson tee with gold NH | black jeans + boots | `rbxassetid://83722187977173` |
| `shirt_civ_flannel_open.png` | Open crimson/black/gold flannel (original sett) over a black tee with a small moon, chest pockets, rolled sleeves, curved shirttail | cargo pants | `rbxassetid://129462723470516` |
| `shirt_civ_victorian_waistcoat.png` | Black brocade waistcoat with gold piping and buttons, crimson satin back with half belt, ruffled cravat with ruby brooch, pocket-watch chain, billowy poet sleeves with lace cuffs | pinstripes | `rbxassetid://125970574202008` |
| `shirt_civ_hussar_coat.png` | Oxblood hussar coat: gold frogging, velvet standing collar, shoulder cords, velvet cuffs with Austrian knots, braided back | pinstripes | `rbxassetid://79156591370434` |
| `shirt_civ_tee_the_hollow.png` | Black band tee for "The Hollow": skull and crimson moon, "NIGHT TOUR '26"; tour dates on the back at the school's own haunts (Archive, Boiler Yard, Bell Tower, Chapel, Beneath) | fishnet skirt | `rbxassetid://134074247430301` |
| `pants_civ_cargo_boots.png` | Charcoal cargo pants, crimson web belt, flap pockets, knee panels, black combat boots with crimson laces | flannel | `rbxassetid://78086076132092` |
| `pants_civ_black_jeans_boots.png` | Black jeans (from `pants_jeans_b`) tucked into combat boots, silver wallet chain | leather jacket | `rbxassetid://131422555821198` |
| `pants_civ_joggers_stripe.png` | Charcoal joggers, crimson-and-gold side stripe, drawstring waist, cuffed ankles, sneakers from `pants_jeans_a` | hoodie | `rbxassetid://134766584302221` |
| `pants_civ_pinstripe_riding_boots.png` | Pinstripe trousers, tall glossy riding boots with crimson cuffs and gold buckles | waistcoat / hussar coat | `rbxassetid://100445247848891` |
| `pants_civ_skirt_fishnet.png` | Black pleated skirt with crimson hem line, gold chain belt, fishnets (skin shows through), platform combat boots | band tee | `rbxassetid://80372266019660` |

## Transformation outfits

Each form has one shirt and one pants piece. The names match the character attribute `Transformation`: `Vampire`, `Wolf`, `Ghoul` and `Wraith`. The Priest pair is for the Priest bloodline (Grand Priest / Pope). The UI kit session wired them in. When the attribute is set to Vampire, Wolf, Ghoul, Wraith or Priest, `Appearance.ApplyTo` dresses the form's outfit from `Appearance.Forms[x].Outfit`. Clearing the attribute puts the saved look back. In "use my Roblox outfit" mode, only the shirt and pants swap. Priest is a clothing-only form.

| File | What it is | Asset id |
|---|---|---|
| `shirt_form_vampire_noble.png` | **Vampire / Nobleblood**: black velvet frock coat with crimson silk lapels and tall collar, gold piping and filigree, crimson brocade waistcoat, lace jabot with ruby brooch and a blood drip, crimson cuffs with lace ruffles; gold-edged bat on the back | `rbxassetid://123566297876526` |
| `pants_form_vampire_noble.png` | Black trousers with crimson satin side stripe, velvet coat tails over the backs of the legs, tall riding boots | `rbxassetid://120337070428958` |
| `shirt_form_wolf.png` | **Wolf**: the school shirt shredded open over a fur chest, grimy and blood-flecked, claw slashes on the back, torn sleeves, fur arms, claws, loose crimson tie | `rbxassetid://110316094304704` |
| `pants_form_wolf.png` | Torn trousers ripped off at the shin, fur through the holes, clawed feet, paw pads on the soles | `rbxassetid://116024762677016` |
| `shirt_form_ghoul.png` | **Ghoul**: the maroon school vest rotted through, showing grey-green veined skin, an opened ribcage, stitched wounds, moss, bony hands | `rbxassetid://138136676091601` |
| `pants_form_ghoul.png` | Rotted funeral trousers with a rope belt, grave dirt, bare feet with toes | `rbxassetid://93438845814370` |
| `shirt_form_wraith.png` | **Wraith**: tattered black hooded shroud, deep-shadow hood with glowing rune dots, glowing sigil on the chest and back, spectral chains, sleeves dissolving into void and mist | `rbxassetid://122979597635421` |
| `pants_form_wraith.png` | Robe strips fraying into void and spectral mist, cord belt with a glowing knot, small sigils, faint glow under the feet | `rbxassetid://135040170021212` |
| `shirt_form_priest_vestments.png` | **Priest**: black cassock with crimson buttons and piping, ivory and gold stole with crosses, clerical tab, pectoral cross on a gold chain; radiant gold cross with a soft holy glow on the back | `rbxassetid://95623201138352` |
| `pants_form_priest_cassock.png` | Cassock skirt with crimson silk sash and fringe, stole ends with gold fringe, button line, gold hem band, black shoes | `rbxassetid://101142708870710` |

Hands and feet: the Wolf, Ghoul and Wraith outfits paint their own (claws, bony fingers, void). The Vampire and Priest outfits leave them bare, so the character's skin shows there.

## Ghoul race uniforms

This is the Tier I race look for Ghoul: the everyday school uniform as worn by an enrolled ghoul. It's subtler than the Ghoul transformation outfit.

- **Same uniform:** each one is still clearly the same uniform, with no recolour. It's torn, with a couple of tears that show the ghoul's own skin. Rips and the shoulder seams are crudely cross-stitched. Grave damp has wicked up from the hems and cuffs to a tide-line. There's grave dirt, the cuffs and hem are frayed, and it's a little faded.
- **Where it's used:** the UI kit session shows it when Race is Ghoul and the uniform is on. It's wired into Appearance, and the UI kit session checked it in Play: it renders correctly, and the tears show the ghoul's skin.
- **Mapping:** the four shirts are built on the exact in-game uniforms, which are `Appearance.Uniforms` 1-4.
- **The trousers:** the in-game Uniform Pants (`rbxassetid://11092315741`) is `pants_jeans_b` with white sneakers and a see-through upper torso. That asset can't be downloaded, so the ghoul pants use `pants_jeans_b` with the white sneakers redrawn as original art, then muddied, plus frayed hems over them.
- **Built by:** `tools/ghoul_uniform.py`. The sheet is `contact_sheet_ghoul_uniform.png`, and the Studio check is `studio_test_ghoul_uniform.jpg` (ghoul skin tone, from left to right: Red Vest, Red Shirt, Black Vest, Black Shirt).

| Key | File | Made from | Asset id |
|---|---|---|---|
| RedVest | `shirt_ghoul_uniform_red_vest.png` | `shirt_maroon_vest_grey.png` | `rbxassetid://84072695194585` |
| RedShirt | `shirt_ghoul_uniform_red_shirt.png` | `shirt_maroon_polo_khaki.png` | `rbxassetid://119270272051011` |
| BlackVest | `shirt_ghoul_uniform_black_vest.png` | `shirt_black_red_vest.png` | `rbxassetid://96506329567070` |
| BlackShirt | `shirt_ghoul_uniform_black_shirt.png` | `shirt_black_polo_khaki.png` | `rbxassetid://92900239530807` |
| Pants | `pants_ghoul_uniform.png` | `pants_jeans_b.png` + redrawn sneakers | `rbxassetid://132089587959690` |

## In-game check

These were tested on R6 rigs in Edit mode in NH Combat Test. `studio_test_front.jpg` shows the upgraded uniforms, from left to right:

1. delinquent polo + ripped jeans
2. blazer + charcoal slacks
3. varsity jacket + black jeans
4. cardigan + tartan skirt

Every face lines up. Skin shows through the rolled sleeves, the jean rips and below the skirt, as intended. The temporary rigs were deleted afterwards.

The civilian and transformation sets were checked the same way:

- `studio_test_forms_front.jpg` and `studio_test_forms_back.jpg` show, from left to right: Vampire, Wolf, Ghoul, Wraith. The skin colour is set to match each form.
- `studio_test_civilian_front.jpg` shows, from left to right: hoodie + joggers, leather jacket + black jeans, waistcoat + pinstripes, band tee + fishnet skirt.

The UI kit session also tested other combinations on its own rigs: PE shirt + shorts, Crimson Court vest + skirt, and blazer + ripped jeans. The uniform and civilian pieces are in the Wardrobe Outfit tab (24 tops, 13 bottoms), listed in `ReplicatedStorage.UI.Appearance.Uniforms` and `.BottomsList`. The UI kit session also checked the form swaps both ways (avatar ⇄ Wolf, uniform ⇄ Vampire, avatar + Priest) in Edit mode. None of this has been playtested yet.

## Rebuilding

The images are generated, not hand-painted. To change a colour or detail, edit the scripts in `../tools/` and run:

```
python Clothing/tools/make_all.py
```

That rebuilds every PNG and the contact sheet. It also checks each file's size and format, and checks that no magenta is left.

- `nhcloth.py`: layout rects, palette, fabric texture, monogram, crest, 4x supersampled drawing, and the quality pass (`finish`, `lift`, `save_hq`)
- `nhextra.py`: fur, boots, glow, torn edges, chains, plaid, damask
- `civilian.py`: the civilian set
- `forms.py`: the transformation set
- `recolors.py`: vest and polo colourways
- `shirts_new.py`: blazer, cardigan, varsity, PE shirt, delinquent polo
- `pants.py`: denim washes, rips, trousers, shorts, skirt, school shoes
- `sheet.py`: the contact sheet

Rebuilt files get new pixels, so upload them again to get new asset ids.

## Tools and ids
- `../tools/`: the generators (`make_all.py` builds the first three sets; `female.py` and `forms2.py` the 1.13.0 sets). Run from `tools/` with Python 3, numpy, scipy and Pillow.
- `asset_ids.json`: the uploaded Roblox id of every template (69 entries), as used in `ReplicatedStorage.UI.Appearance`.
