---
name: roblox-import-quirks
description: "Import/upload facts for Nightmare Highschool props, textures and animations (scale, textures, group assets)"
metadata:
  node_type: memory
  type: reference
  originSessionId: eaaae633-0702-42c2-a27c-a0661820655a
  modified: 2026-11-21T21:40:53.349Z
---

- Prop FBX exports (art/props, global_scale 1.0, metres) import into Studio ~100x too big; `tools/phase6-2350/stage/hometown.lua`
  fits sizes. RBX Toolbox (owner's Blender 5.2 add-on) exports at global_scale 0.01 with cm units, which would import 1:1.
- The owner's imports arrive without SurfaceAppearances. `tools/phase6-2350/stage/textures.lua` dresses pieces from group
  image ids by the pipeline rules: `*Glow` -> Neon, `*Glass` -> Glass, canvas pieces -> `WF_<Name>_canvas*`, tiled
  groups (Siding/Roof/Brick...) -> `WF_<Tile>_*`, everything else -> the prop atlas `<Prop>_{color,normal,metal,rough}`.
  Re-imported props keep their FBX file name prefix (WickHouse_Siding under WFWickHouse).
- Group animations cannot be archived or deleted (develop.roblox.com archive API: "asset type not supported"); old uploads stay, unused.
- Find uploaded ids yourself in group 15981569 via `itemconfiguration.roblox.com/v1/creations/get-assets?assetType=Animation|Image&groupId=15981569`
  (fetch from a create.roblox.com page in the built-in browser; newest first). See [[imported-assets-means-find-ids]].
- Blender builds use `E:/Blender/blender.exe` (4.4, background); the owner also has Blender 5.2 with RBX Toolbox + Cursor Snapper (2D GP tool, not useful).
- C: has had ~1.3 GB free; Studio MCP video_capture then fails with NoSpaceOnDevice.
