"""Fill the Quiet Corners art ids from get-assets dumps (newest first), as fetched from a create.roblox.com tab:
itemconfiguration.roblox.com/v1/creations/get-assets?assetType=Image&groupId=15981569 (one page per file, 1.5 s apart).
usage: python -X utf8 -I ids.py [--live DIR] <page.json>...
Only `= 0` entries are filled. Per-race tables are one line: `\tSlip = { Human = 0; Priest = 0; ... };`."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
live = os.path.join(os.path.dirname(HERE), "live")
if args and args[0] == "--live":
    live, args = args[1], args[2:]
ids = {}
for f in args:
    data = json.load(open(f, encoding="utf-8"))
    rows = data.get("data", data) if isinstance(data, dict) else data
    for row in rows:
        name, aid = row.get("name"), row.get("assetId") or row.get("id")
        if name and aid and name not in ids:
            ids[name] = int(aid)
PREFIX = {"QuietCornersArt": "Qc", "DialogueArt": "Dl", "EvidenceArt": "Ev"}
SKIP = ("Crest", "CrestFlip", "Slices", "Boxes")
missing = []
for cfg, prefix in PREFIX.items():
    path = os.path.join(live, f"ReplicatedStorage.Config.{cfg}.luau")
    if not os.path.exists(path):
        continue
    out = []
    for line in open(path, encoding="utf-8").read().split("\n"):
        m = re.match(r"^\t(\w+) = \{(.*)\};", line)
        if m and m.group(1) not in SKIP:
            piece = m.group(1)

            def fill(mm, piece=piece):
                key = f"{prefix}{piece}{mm.group(1)}"
                if mm.group(2) != "0":
                    return mm.group(0)
                if key in ids:
                    return f"{mm.group(1)} = {ids[key]}"
                missing.append(key)
                return mm.group(0)
            line = line[:m.start(2)] + re.sub(r"(\w+) = (\d+)", fill, m.group(2)) + line[m.end(2):]
        else:
            m = re.match(r"^\t(\w+) = (\d+);", line)
            if m and m.group(2) == "0":
                key = prefix + m.group(1)
                if key in ids:
                    line = f"\t{m.group(1)} = {ids[key]};" + line[m.end():]
                else:
                    missing.append(key)
        out.append(line)
    open(path, "w", encoding="utf-8", newline="").write("\n".join(out))
print("filled from", len(ids), "names;", "missing:", " ".join(missing) if missing else "none")
