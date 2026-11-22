---
name: imported-assets-means-find-ids
description: "When the owner says they \"imported\" assets, they've uploaded them to Roblox group 15981569 — go find the ids yourself"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 4325cc21-86c8-4f98-9ae3-cee4a781ab8c
  modified: 2026-11-21T11:27:12.823Z
---

When the owner of Nightmare Highschool says they imported/uploaded art or other assets, the assets are already uploaded to the Roblox group **15981569** (the game's group). Don't ask them for the asset ids: look them up yourself in the group's creations (Creator Dashboard, group 15981569, the matching asset type, e.g. Images) and match them by file name.

**Why:** the owner said (2026-11-21) "I thought I already threw the new ui in. Check the group for the IDs & remember this for anytime I say I imported the assets." Asking for ids they already uploaded wastes their time.

**How to apply:** after "imported", open the group's creations in the browser (the built-in browser is signed in to roblox.com), find each file by its upload name (e.g. the `Bt*.png` set for the Bell Tower HUD), and copy the numeric ids into the relevant `Config.*Art` module. Note: uploaded images may get a separate Image id vs Decal id; HUD code needs the Image (rbxassetid) id.
