---
name: rigid-rigs-for-multipiece-props
description: "Animated multi-piece props must be rigid Motor6D rigs, not skinned FBX imports (Nightmare Highschool)"
metadata:
  node_type: memory
  type: project
  originSessionId: eaaae633-0702-42c2-a27c-a0661820655a
  modified: 2026-11-21T21:40:44.794Z
---

Studio's skinned FBX import ("Import as rig") lays multi-piece Blender props out wrong at rest (the black bus and the
Wick house: pieces displaced, roof lifted, chimney gone), and their clips carry bogus constant bone translations.
Applying mesh transforms before export did NOT fix it; the cause was never found (2026-11-21). Single-mesh organic rigs
(Biscuit the dog) and 2-piece rigs (WFPicketGate) imported fine.

**Why:** two re-import rounds and two wrong theories were spent on the bus before switching.
**How to apply:** for any animated prop with several pieces, add it to `RIGID` in its art script (batch49
`RIGID`/`write_rigid`, batch52 for the bus). That exports plain meshes + `art/props/anim/<Prop>_rigid.json`. The owner imports
it with Import as rig OFF; then run `tools/phase6-2350/stage/rigid_rig.py <Prop> <path>` and the generated Luau in Edit
(fits axes/scale from piece centres, builds Motor6Ds, writes KeyframeSequences to NHCineClips +
ServerStorage.NHPublish for the owner to publish). Keep a base loop playing on rigs while visible. Verify by screenshot
before trusting numbers. See [[roblox-import-quirks]].
