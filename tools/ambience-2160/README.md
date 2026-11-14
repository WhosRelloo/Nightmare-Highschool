# Ambience foundations (2.17.0)

Concepts 1, 2, 3 and 6 of `docs/Environment-Ambience-Concepts.md`, and the start of 7 (our own sounds).

- `pre/` - the scripts as they were in NH Combat Test before 2.17.0.
- `live/` - the scripts as installed (new: AmbienceMix, AmbientSounds, Functions.RegionBoxes).
- `patches.py` - the old -> new edits (pre + patches = live for the four patched scripts); `clips.luau` is the
  Config.Ambience.Clips table it inserts, from `python tools/sfx/ambience.py --luau`.
- The sounds: `tools/sfx/ambience.py` -> `art/sfx/ambience/` (two sheets to upload, every sound on its own, manifest).
- The Map got `workspace.Regions` (29 boxes lined up above the school, NHCore) and the new Config.Regions; none of
  these scripts are on the Map yet.
