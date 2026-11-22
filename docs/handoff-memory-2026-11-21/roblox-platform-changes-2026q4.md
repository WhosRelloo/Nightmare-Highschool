---
name: roblox-platform-changes-2026q4
description: "Roblox platform changes (Sep-Nov 2026 DevForum) that affect Nightmare Highschool, with status"
metadata:
  node_type: memory
  type: reference
  originSessionId: eaaae633-0702-42c2-a27c-a0661820655a
  modified: 2026-11-21T21:41:13.851Z
---

Read from DevForum announcements on 2026-11-21 (see [[devforum-read-via-browser]]). Re-check status before relying on a beta.
- Live, bug risk: PlayerCharacterDestroyBehavior default since Nov 11 (characters destroyed right after
  CharacterRemoving, players 5 s after PlayerRemoving); Shapecasts reimplemented (more precise, 4.1x faster, + Margin,
  SizeGradient, overrides); wedge collision fix (a bug thread says block parts changed too); min draw distance 500 studs
  on low quality; TextChatService migration required by May 2027 (message text unreadable in code).
- Live, useful: UIShadow text/inset/knockout/gradient; Color3 GetContrastingColor/GetContrastRatio/GetLuminance;
  Animation Graph State Machines + Luau Expressions; BasePart:BindToCollisionSummaries; Input Action Manager; Performance
  Simulator (Device Simulator > Performance); Frustum Streaming; DataModel.ServerLowMemoryWarning; Team Test client logs;
  Studio MCP video capture + save_place; custom terrain materials (Expanded Terrain).
- Beta / early access (not publishable): ParticleEmitter2D UI Particles (Emit/Clear, flipbooks, EmissionMode, Blend,
  Brightness; not clipped in Surface/BillboardGui); CreateSurfaceAppearanceAsync with asset ids; AnimatedImages
  (Aseprite); if local / while local; Luau export values; terrain scattering, path splines, projected decals;
  Team Test server inspection; orthographic camera. Coming: asset versioning (same id on re-upload).
