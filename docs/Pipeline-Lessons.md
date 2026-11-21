# Pipeline lessons (read before importing, rigging or testing in Studio)

Hard-won facts from the 2.35.0 tutorial work (2026-11-21). Each one cost real time to learn.

## Importing props
- **Multi-piece animated props must be rigid rigs.** Studio's skinned FBX import ("Import as rig") laid the black bus
  and the Wick house out wrong at rest: pieces displaced, the roof lifted, the chimney gone. Their clips also carried
  bogus constant bone translations. Applying mesh transforms before export did not help, and the cause was never found.
  - Single-mesh rigs (Biscuit) and two-piece rigs (the picket gate) import fine.
  - **Do instead:** add the prop to `RIGID` in its art script. It then exports plain meshes and
    `art/props/anim/<Prop>_rigid.json`. Import it with **Import as rig OFF**, then run
    `python tools/phase6-2350/stage/rigid_rig.py <Prop> <Workspace path>` and the generated Luau in Edit. That fits the
    axes and scale from the piece centres, builds Motor6Ds and welds, and writes the clips to `NHCineClips` plus
    `ServerStorage.NHPublish.<Prop>` for publishing.
  - Keep a base loop playing on any rig while it's visible, so no frame shows a bare pose.
- **Scale.** Prop FBX files import about 100x too big. `stage/hometown.lua` fits sizes. The RBX Toolbox add-on (the
  owner's Blender 5.2) exports at `global_scale 0.01` with cm units, which would import 1:1.
- **Textures.** Imports arrive without SurfaceAppearances. `stage/textures.lua` dresses them from group image ids by
  the pipeline rules:
  - `*Glow` pieces become Neon, and `*Glass` pieces become Glass.
  - Canvas pieces use `WF_<Name>_canvas*`.
  - Tiled groups use `WF_<Tile>_*`.
  - Everything else uses the prop atlas.
  - Re-imported props keep their file-name prefix, e.g. `WickHouse_Siding` under `WFWickHouse`.
- **Screenshot the result before trusting any numbers.**

## Assets in the group (15981569)
- After the owner uploads assets, find the ids yourself: `itemconfiguration.roblox.com/v1/creations/get-assets?assetType=Animation|Image&groupId=15981569`,
  fetched from a create.roblox.com page in the built-in browser. Results come newest first.
- Group animations can't be archived or deleted (the API refuses them), so duplicates stay. Pick the newest set, and
  check the loop flags and lengths by loading the clips.

## Studio
- One session drives NH Combat Test at a time. Hand over with "Studio released", from Edit mode with slot 2 restored.
- Never save, close, reload or revert the place without the owner's word.
- Use slot 2 only. Take a fresh snapshot at the start of every Play round, restore only from it, and record
  CineState, Seen and Origin before and after.
- The Edit DataModel isn't readable during Play.
- `execute_luau` runs in its own VM, so requiring a game module there builds a rogue copy.
- Studio throttles to 15-40 fps when unfocused. Measure with real per-sample frame times.

## Reading the DevForum
- Fetching pages directly returns an empty 202. In the built-in browser, use Discourse JSON instead:
  `/c/updates/announcements/36.json`, `/t/<id>.json` and `/top.json?period=monthly`.
