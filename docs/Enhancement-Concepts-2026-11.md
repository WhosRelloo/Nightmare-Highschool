# Enhancement concepts, end to end (November 2026)

The next list after the DevForum list (bug-risk audits, Bell Tower polish). It builds on what the game already has: Cine, cliques, the Living School, Progression & Identity, the Bell Tower, sports, the phone and Wickfield. Platform features are as of the 2026-11-21 DevForum read; see `docs/Pipeline-Lessons.md`.

**Suggested order:** A1, then C8 together with B6 (they reinforce each other), then B4, B5, D12 and G20, then the rest.

## A. The first 30 minutes
1. **Finish the tutorial.** Slice 2 covers the getaway, breakfast, and the bus arriving at the school gates. It then hands straight into a seamless first homeroom, so the first school day starts with no loading cut.
2. **A first friend.** One of the 24 rostered students meets you on day 1 and gives a short walk-and-talk tour. They explain the Bells and the cliques in character, instead of tooltips.
3. **Measure the tutorial.** Use Analytics Journeys to see where new players drop off, and Experiments to test a shorter cold open against a longer one.

## B. Moment-to-moment feel
4. **Impact-based hit reactions.** `BasePart:BindToCollisionSummaries` gives the contact point and relative speed. Use them to drive the stagger direction, hitstop length and dust, so heavy hits read as heavy.
5. **School parkour.** Reuse the tutorial's approach, vault, re-seat and dip tools to vault railings, slide under desks and drop from ledges. These double as escapes while Hunted.
6. **A sneak loop.** Add crouching, a noise meter, and cover against staff vision cones. The cones are cone-shaped Shapecasts (`SizeGradient`). This feeds Bell Tower R2 directly.
7. **One camera language.** Give gameplay cameras the same handheld noise, focus and grade as the cinematics, so story and play look like one game.

## C. A living school
8. **Bell Tower R2–R4.** This covers Bells, witnesses, the Almanac and the Conduct Ledger. Staff run Animation Graph state machines: patrol, suspicious, search, chase, return.
9. **Scripted school events as seamless cuts.** Fire drills, assemblies, pop quizzes and the lunch rush are triggered by the timetable, and the player keeps control throughout.
10. **Visible consequences.**
    - Prank messes become projected decals that stay until someone cleans them.
    - Rumours show up as graffiti and notes on boards.
    - Watched wings get a visual tint.
11. **Weather and terms.**
    - Rain changes routes and slows Sports.
    - Night gets new grades.
    - Each term ends in a Report Card ceremony cut.

## D. Look
12. **A lighting and grade pass for every region,** using the Cine `Looks`. Build out Wickfield and the grounds with custom terrain materials, path splines and scatter.
13. **HUD polish everywhere.**
    - UI Particles, once they're live: see "Bell Tower polish" below.
    - UIShadow glows and knockout glass.
    - Contrast checks with the `Color3` contrast methods.
14. **NPC presence.** Varied idles from the clip library, heads that look at you, and seated chatter groups.

## E. Sound
15. **Layered music by state.** Calm, Noticed, Hunted and fight layers crossfade as the state changes.
16. **Surfaces and voices.**
    - Footsteps change by surface.
    - PA and staff lines use text-to-speech with automatic translation.
    - Other sound ducks during cuts.

## F. Social and multiplayer
17. **Shared seamless cuts with your party.** Friends see each other in story moments, building on the existing group cuts.
18. **Clique co-op.** Prank heists, rumble days and turf events with shared rewards.
19. **Dorm and home visits** in the Homes interiors.

## G. Loops that make it fun
20. **A daily school day.** Three objectives on the Today card, a streak, and a weekly term recap card.
21. **Secrets.** Collectibles and lore pages behind the Collected cut, with Journal entries and region discovery.
22. **More phone games,** plus a weekly cross-server leaderboard.

## H. Robustness and performance
23. **Low-end pass.**
    - Run the Performance Simulator at quality level 1.
    - Use Frustum Streaming for long sightlines.
    - Clean up on `DataModel.ServerLowMemoryWarning`.
24. **Anti-exploit.**
    - Harden server authority.
    - Add Device Trust checks on high-value actions.
    - Key state by UserId, not Player instances.
25. **Automated visual checks.** After every release, take MCP screenshots and video of key scenes and compare them with the last release.

## I. Platforms and accessibility
26. **Controls.** Move every binding into the Input Action Manager, and run a phone-layout pass on each new HUD.
27. **Comfort.** Reduce Motion and Reduce Flash in every system, and colour-blind-safe Bell states.

## J. Pipeline
28. **A one-command prop pipeline.**
    - Build in Blender.
    - Rig it as a rigid rig (`stage/rigid_rig.py`).
    - Apply textures (`stage/textures.lua`).
    - Upload through Open Cloud with the owner's key, which removes the manual publishing steps.
    - Asset versioning keeps the same ids when an asset is re-uploaded.

## Bell Tower polish (owner decision, 2026-11-21: start once UI Particles is live)
Start when `ParticleEmitter2D` (UI Particles) leaves Studio beta and can be published. The work:
- **UI Particles:**
  - dust when a Bell lands on its hook;
  - a gold burst on an alibi;
  - an ink splash when the Conduct Seal changes level;
  - embers on the map's search candles;
  - a sparkle when a Lead Card pip fills.

  All of these are off under `NHReducedFlash`.
- **UIShadow:**
  - text shadows on the 20 px gold and amber lines;
  - an inset shadow for a pressed Seal or Dial;
  - a knockout shadow on the dial glass;
  - a gradient glow that could replace the tinted BellGlow image.
- **Contrast:** add a WCAG check for text on each Seal tint (`Color3:GetContrastRatio`) to the HUD fit check.
- **Controls and testing:** Input Action Manager bindings for J Journal, the Dial and the Ledger, and a Performance Simulator pass at Q1.
