"""Build the Luau that updates ReplicatedStorage.UI.EyeArt (2026-11-04) from the upload results in face_ids/.
Writes eyeart_tables.lua (served to Studio) and prints a summary."""
import glob
import json

ids = {}
for f in glob.glob("face_ids/*.json"):
    for url, aid in json.load(open(f)).items():
        ids[url.rsplit("/", 1)[1][:-4]] = aid
mouths = {k[len("mouth_"):]: v for k, v in ids.items() if k.startswith("mouth_")}
forms = {k[len("formface_"):]: v for k, v in ids.items() if k.startswith("formface_")}
marks = {k[len("mark_"):]: v for k, v in ids.items() if k.startswith("mark_")}

RACE_MOUTHS = [("race_stitched", "Sewn Shut", "Ghoul"), ("race_split", "Split Smile", "Ghoul"),
               ("race_fang", "Fanged Smirk", "Vampire"), ("race_wine", "Wine Lips", "Vampire"),
               ("race_canine", "Canines", "Werewolf"), ("race_feral", "Feral Grin", "Werewolf"),
               ("race_sewn", "Frozen Seam", "Wraith"), ("race_hush", "Hush", "Wraith"),
               ("race_serene", "Serene", "Priest"), ("race_solemn", "Solemn", "Priest")]
MARKS = [("freckles", "Freckles", None), ("scar", "Cheek Scar", None), ("beauty", "Beauty Mark", None),
         ("bandage", "Plaster", None),
         ("vamp_bat", "Bat Mark", "Vampire"), ("vamp_pallor", "Noble Pallor", "Vampire"),
         ("wolf_scars", "Claw Scars", "Werewolf"), ("wolf_tufts", "Wild Tufts", "Werewolf"),
         ("ghoul_stitches", "Stitched Cheeks", "Ghoul"), ("ghoul_rot", "Grave Rot", "Ghoul"),
         ("wraith_frost", "Frost Veins", "Wraith"), ("wraith_tears", "Void Tears", "Wraith"),
         ("priest_brand", "Holy Brand", "Priest"), ("priest_script", "Scripture", "Priest")]
FORMKEYS = ["vampire", "vampire2", "wolf", "ghoul", "ghoul2", "wraith"]

missing = [m for m, _, _ in RACE_MOUTHS if m not in mouths] + [m for m, _, _ in MARKS if m not in marks] + \
          [f for f in FORMKEYS if f not in forms]
if len(mouths) != 54:
    missing.append(f"{len(mouths)} mouths (want 54)")
if missing:
    raise SystemExit("missing: " + ", ".join(missing))

order = sorted(k for k in mouths if not k.startswith("race_"))
mouth_tbl = "EyeArt.MouthArt = {\n" + "".join(f'\t{k} = "{mouths[k]}",\n' for k in order) + \
    "".join(f'\t{k} = "{mouths[k]}",\n' for k, _, _ in RACE_MOUTHS) + "}\n"


def race(r):
    return f', Race = "{r}"' if r else ""


extra = (
    "-- 2026-11-04: race faces and menacing transformation faces (tools/ui-textures gen_face.py + gen_menace.py).\n"
    "-- Race = a Lineage race id: that race only (Appearance.RaceAllows). Mouths have a PBR-style material bake.\n"
    "EyeArt.RaceMouths = {\n" + "".join(f'\t{{ Id = "{i}", Name = "{n}"{race(r)} }},\n' for i, n, r in RACE_MOUTHS) + "}\n"
    "EyeArt.Marks = {\n" + "".join(f'\t{{ Id = "{i}", Name = "{n}"{race(r)} }},\n' for i, n, r in MARKS) + "}\n"
    "EyeArt.MarkArt = {\n" + "".join(f'\t{i} = "{marks[i]}",\n' for i, _, _ in MARKS) + "}\n"
    "-- drawn under the eyes while transformed: sunken sockets, a glow, void / ooze tears, snarl creases, cracks (no blood)\n"
    "EyeArt.FormFaceArt = {\n" + "".join(f'\t{k} = "{forms[k]}",\n' for k in FORMKEYS) + "}\n"
    "function EyeArt.Mark(id: string)\n\treturn EyeArt.MarkArt[id]\nend\n"
    "function EyeArt.FormFace(key: string)\n\treturn EyeArt.FormFaceArt[key] or EyeArt.FormFaceArt[(string.gsub(key, \"2$\", \"\"))]\nend\n\n"
)
open("eyeart_mouthart.lua", "w").write(mouth_tbl)
open("eyeart_extra.lua", "w").write(extra)
print("mouths", len(mouths), "forms", len(forms), "marks", len(marks))
