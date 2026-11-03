"""Build every Nightmare Highschool clothing variant, check it, and make the contact sheet.

    python Clothing/tools/make_all.py
"""
import sys

import numpy as np
from PIL import Image

import civilian
import forms
import ghoul_uniform
import pants
import recolors
import sheet
import shirts_new
from nhcloth import OUT, W, H

# file -> (label, source it came from)
ITEMS = {
    "shirt_vest_navy_ivory.png": ("Navy vest, ivory shirt", "shirt_maroon_vest_grey + shirt_black_red_vest"),
    "shirt_vest_forest_cream.png": ("Forest vest, cream shirt", "shirt_maroon_vest_grey + shirt_black_red_vest"),
    "shirt_vest_charcoal_crimson.png": ("Charcoal vest, crimson shirt", "shirt_maroon_vest_grey + shirt_black_red_vest"),
    "shirt_vest_vigil_ivory_gold.png": ("Vigil vest (candle gold)", "shirt_maroon_vest_grey + shirt_black_red_vest"),
    "shirt_vest_crimson_court.png": ("Crimson Court vest", "shirt_maroon_vest_grey + shirt_black_red_vest"),
    "shirt_polo_navy_khaki.png": ("Navy polo", "shirt_maroon_polo_khaki (NH from shirt_black_polo_khaki)"),
    "shirt_polo_forest_khaki.png": ("Forest polo", "shirt_maroon_polo_khaki (NH from shirt_black_polo_khaki)"),
    "shirt_polo_ivory_crimson.png": ("Ivory polo, crimson collar", "shirt_maroon_polo_khaki (NH from shirt_black_polo_khaki)"),
    "shirt_polo_crimson_charcoal.png": ("Crimson polo, charcoal", "shirt_maroon_polo_khaki (NH from shirt_black_polo_khaki)"),
    "shirt_polo_delinquent.png": ("Delinquent polo", "shirt_maroon_polo_khaki (NH from shirt_black_polo_khaki)"),
    "shirt_blazer_black_crest.png": ("Black blazer, NH crest", "new; collar from shirt_maroon_polo_khaki"),
    "shirt_cardigan_charcoal_crest.png": ("Charcoal cardigan, NH crest", "shirt_maroon_vest_grey + shirt_black_red_vest"),
    "shirt_varsity_jacket.png": ("Varsity jacket", "new; neck from shirt_maroon_polo_khaki"),
    "shirt_gym_pe.png": ("Gym / PE shirt", "new; neck from shirt_maroon_polo_khaki"),
    "pants_jeans_dark_indigo.png": ("Dark indigo jeans", "pants_jeans_a"),
    "pants_jeans_black.png": ("Black jeans", "pants_jeans_b"),
    "pants_jeans_ripped.png": ("Ripped jeans", "pants_jeans_a"),
    "pants_slacks_charcoal.png": ("Charcoal slacks", "new; layout from pants_jeans_a"),
    "pants_trousers_khaki.png": ("Khaki trousers", "new; layout from pants_jeans_a"),
    "pants_shorts_khaki.png": ("Khaki shorts + socks", "new; layout from pants_jeans_a"),
    "pants_skirt_pleated_tartan.png": ("Pleated tartan skirt", "new; layout from pants_jeans_a"),
}


# file -> (label, what it's made from, the piece it's shown with on the sheet)
CIVILIAN = {
    "shirt_civ_hoodie_blood_moon.png": ("Blood Moon hoodie", "new", "pants_civ_joggers_stripe.png"),
    "shirt_civ_leather_jacket.png": ("Leather jacket, crimson tee", "new; NH from shirt_black_polo_khaki", "pants_civ_black_jeans_boots.png"),
    "shirt_civ_flannel_open.png": ("Open flannel over black tee", "new; collar from shirt_maroon_polo_khaki", "pants_civ_cargo_boots.png"),
    "shirt_civ_victorian_waistcoat.png": ("Victorian waistcoat, poet shirt", "shirt_maroon_vest_grey + shirt_black_red_vest", "pants_civ_pinstripe_riding_boots.png"),
    "shirt_civ_hussar_coat.png": ("Oxblood hussar coat", "new", "pants_civ_pinstripe_riding_boots.png"),
    "shirt_civ_tee_the_hollow.png": ("'The Hollow' band tee", "new", "pants_civ_skirt_fishnet.png"),
    "pants_civ_cargo_boots.png": ("Cargo pants, combat boots", "new; jeans layout", "shirt_civ_flannel_open.png"),
    "pants_civ_black_jeans_boots.png": ("Black jeans, boots, chain", "pants_jeans_b", "shirt_civ_leather_jacket.png"),
    "pants_civ_joggers_stripe.png": ("Striped joggers, sneakers", "new; sneakers from pants_jeans_a", "shirt_civ_hoodie_blood_moon.png"),
    "pants_civ_pinstripe_riding_boots.png": ("Pinstripes, riding boots", "new; jeans layout", "shirt_civ_victorian_waistcoat.png"),
    "pants_civ_skirt_fishnet.png": ("Black skirt, fishnets, boots", "new; jeans layout", "shirt_civ_tee_the_hollow.png"),
}
FORMS = {
    "shirt_form_vampire_noble.png": ("Vampire: Nobleblood coat", "new; collar from shirt_maroon_polo_khaki", "pants_form_vampire_noble.png"),
    "pants_form_vampire_noble.png": ("Vampire: coat tails, riding boots", "new; jeans layout", "shirt_form_vampire_noble.png"),
    "shirt_form_wolf.png": ("Wolf: shredded shirt, fur, claws", "new; collar from shirt_maroon_polo_khaki", "pants_form_wolf.png"),
    "pants_form_wolf.png": ("Wolf: torn trousers, paws", "new; jeans layout", "shirt_form_wolf.png"),
    "shirt_form_ghoul.png": ("Ghoul: rotted vest, open ribs", "shirt_maroon_vest_grey + shirt_black_red_vest", "pants_form_ghoul.png"),
    "pants_form_ghoul.png": ("Ghoul: grave trousers, bare feet", "new; jeans layout", "shirt_form_ghoul.png"),
    "shirt_form_wraith.png": ("Wraith: hooded shroud, sigil", "new; neck from shirt_maroon_polo_khaki", "pants_form_wraith.png"),
    "pants_form_wraith.png": ("Wraith: robe into mist", "new; jeans layout", "shirt_form_wraith.png"),
    "shirt_form_priest_vestments.png": ("Priest: cassock and stole", "new; neck from shirt_maroon_polo_khaki", "pants_form_priest_cassock.png"),
    "pants_form_priest_cassock.png": ("Priest: cassock skirt, sash", "new; jeans layout", "shirt_form_priest_vestments.png"),
}

GHOUL_UNIFORM = {
    "shirt_ghoul_uniform_red_vest.png": ("Ghoul: Red Vest", "shirt_maroon_vest_grey (in-game Red Vest)", "pants_ghoul_uniform.png"),
    "shirt_ghoul_uniform_red_shirt.png": ("Ghoul: Red Shirt", "shirt_maroon_polo_khaki (in-game Red Shirt)", "pants_ghoul_uniform.png"),
    "shirt_ghoul_uniform_black_vest.png": ("Ghoul: Black Vest", "shirt_black_red_vest (in-game Black Vest)", "pants_ghoul_uniform.png"),
    "shirt_ghoul_uniform_black_shirt.png": ("Ghoul: Black Shirt", "shirt_black_polo_khaki (in-game Black Shirt)", "pants_ghoul_uniform.png"),
    "pants_ghoul_uniform.png": ("Ghoul: Uniform Pants", "pants_jeans_b + redrawn white sneakers (in-game Uniform Pants)", "shirt_ghoul_uniform_red_vest.png"),
}


def check(path):
    im = Image.open(path)
    problems = []
    if im.size != (W, H):
        problems.append(f"size {im.size}")
    if im.mode != "RGBA":
        problems.append(f"mode {im.mode}")
    a = np.array(im.convert("RGBA")).astype(int)
    vis = a[..., 3] > 0
    mag = vis & (a[..., 0] > 200) & (a[..., 1] < 60) & (a[..., 2] > 200)
    if mag.sum() > 0:
        problems.append(f"{mag.sum()} magenta px")
    return problems


def main():
    sets = [
        ("uniform", ITEMS, recolors.build() + shirts_new.build() + pants.build(), "contact_sheet.png",
         "Nightmare Highschool - uniform variants",
         "Each card: the 585x559 template (transparent shown as checks) and a front/back mock-up. "
         "Shirts are shown over the charcoal slacks; pants under the black polo."),
        ("civilian", CIVILIAN, civilian.build(), "contact_sheet_civilian.png",
         "Nightmare Highschool - civilian clothes",
         "Off-duty streetwear in the school's crimson, black and gold. Each mock-up pairs the piece with its suggested match."),
        ("forms", FORMS, forms.build(), "contact_sheet_forms.png",
         "Nightmare Highschool - transformation outfits",
         "One shirt + pants pair per form (Transformation = Vampire / Wolf / Ghoul / Wraith) plus Priest vestments."),
        ("ghoul_uniform", GHOUL_UNIFORM, ghoul_uniform.build(), "contact_sheet_ghoul_uniform.png",
         "Nightmare Highschool - ghoul race uniforms",
         "The everyday school uniform as worn by an enrolled ghoul: torn, cross-stitched, grave-damp, frayed. Same uniform, same colours."),
    ]
    bad = False
    for key, table, built, sheet_name, title, note in sets:
        names = {p.name for p in built}
        missing, extra = set(table) - names, names - set(table)
        for p in built:
            probs = check(p)
            print(("OK   " if not probs else "FAIL ") + p.name + ("" if not probs else "  " + ", ".join(probs)))
            bad |= bool(probs)
        if missing or extra:
            print(key, "missing:", missing, "unlisted:", extra)
            bad = True
        items = [(k, v[0], v[2] if len(v) > 2 else None) for k, v in table.items() if k in names]
        print("sheet:", sheet.build(items, OUT / sheet_name, title, note).name)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
