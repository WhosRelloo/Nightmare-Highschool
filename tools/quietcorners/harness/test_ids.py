import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
d = tempfile.mkdtemp()
cfg = os.path.join(d, "ReplicatedStorage.Config.QuietCornersArt.luau")
open(cfg, "w").write("return {\n\tSlip = { Human = 0; Vampire = 0 };\n\tCompassTicks = 0;\n\tBookTL = 5;\n}\n")
dump = os.path.join(d, "a.json")
json.dump([{"assetId": 9, "name": "QcSlipHuman"}, {"assetId": 8, "name": "QcSlipHuman"},
           {"assetId": 7, "name": "QcCompassTicks"}, {"assetId": 6, "name": "QcBookTL"}], open(dump, "w"))
out = subprocess.run([sys.executable, os.path.join(HERE, "ids.py"), "--live", d, dump], capture_output=True, text=True).stdout
t = open(cfg).read()
assert "Human = 9;" in t, t            # newest wins
assert "Vampire = 0 }" in t, t         # not uploaded: stays 0
assert "CompassTicks = 7;" in t, t
assert "BookTL = 5;" in t, t           # already set: never overwritten
assert "missing" in out and "QcSlipVampire" in out, out
print("PASS test_ids")
