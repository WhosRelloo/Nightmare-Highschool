# Staff teleport flocks: admin crows and the owner's bats

Up: [[Nightmare Highschool]] · Related: [[Admin-Panel]], [[VFX-Design-Bible]] (P2-7 teleport veil)

Added in 1.75.0 (2026-11-10). The owner asked:
- "make it so Admins get a special TP VFX when we TP to people. Make them cool crows like Itachi. You can model the VFX to the highest quality."
- "And make a special TP vfx for ONLY me where it's REALLYYYYY cool bats, etc."

The look is the game's own design: no anime art is copied.

## Who gets what
The server decides (`Features.Fx.TpStyle`). Clients only draw.

| Mover | Effect |
|---|---|
| The owner (`Config.AdminTp.Bats`: WhosRello, 37484441) | **Bats** |
| Admins (`Features.Admin.Level >= 1`: group rank 254+, the `Config.Cmdr` lists; everyone in Studio) | **Crows** |
| Everyone else, and every non-staff move (duel ring, homes) | the old violet veil, unchanged |

**Which moves:**
- **The staff member moving themself** (`Admin = true`): desk **Go to**, **Go to a place** (yourself), **Ctrl + click teleport**, and Cmdr's `to` / `teleport` on yourself.
- **A student moved by staff** (`By = staff`): **Bring**, **Bring all**, **Go to a place → send the student**, and Cmdr's `bring` / `teleport` on others. The student keeps the veil and lands inside a small swirl of that staff member's birds (`TpEscort`).
- **Invisible staff** (desk Self → Invisible) move silently. No effect at all, so nothing gives them away.
- **Quick puff:** a second Ctrl + click teleport within 2 s plays only a puff at each end (`Quick`), so spam-clicking stays fast.

## What it looks like
- **Crows** (about 1.6 s):
  - **Leaving:** the body breaks into 28 crows, picked from points across the torso, limbs and head. They burst out and scatter up and away, with about a quarter striking out toward where you went. Loose black feathers drift down and an ink wisp curls at the feet.
  - **The move:** the server moves you at 0.45 s.
  - **Arriving:** crows spiral in from 9 to 14 studs out, set their wings, and fold into the same body points from 0.35 to 1.05 s. The body fades back in from 0.85 to 1.15 s. A last puff of feathers follows.
  - **Eyes:** a faint crimson glint in each crow's eyes (SurfaceAppearance emissive).
- **Bats** (about 2.2 s):
  - **Leaving:** a crimson sigil flares under you and turns slowly. It's two rings of runic ticks, six bats wheeling round a crescent moon, with a crimson light (2 brightness, 12 range) and crimson-black ground mist. You tear apart into 44 bats that ride a rising vortex 11 to 16 studs up, then break outward. Crimson motes rise with them.
  - **The move:** at 0.55 s.
  - **Arriving:** the sigil flares where you land. Bats stoop from 13 to 19 studs up in a tightening spiral and collapse into you from 0.55 to 1.45 s. You fade in from 1.3 to 1.6 s, then a crimson ring goes out and six bats peel away.
  - **No blood anywhere:** crimson is only light, mist and eyes.
- **Your own screen:** a 0.14 s ink veil covers the camera cut.
- **Sound** (Pro Sound Effects, Roblox's licensed library):
  - crows: a flock wing burst (9120769674) and a raven craw (9118067220)
  - bats: bursts of bat wings (9125386714) and a giant swish pitched down for the sigil (9120723767)
- **Who sees it:** players within 150 studs of either end, plus the mover. Characters are hidden only on each viewer's screen (`LocalTransparencyModifier`, face SurfaceGuis and name tags), so nothing about the character is changed on the server.
- **Reduce Motion:** 10 crows or 12 bats that rise or glide straight in and fade. There's no scatter, vortex or swirl, the sigil stays still, and the ring is left out.
- **Effects quality Low:** half the birds.

## Regalia tint (1.84.1)
While the mover wears admin regalia (Kit B), the character attribute `NHRegaliaTint` (a Color3 set by `UI.AccessoryWear`) colours their flock.
- **What takes the colour:** each bird's eye glint (`SurfaceAppearance.EmissiveTint`), the smoke (30% toward it) and the motes.
- **The two colours:** Ember (1, 0.34, 0.07) or Crimson (0.92, 0.06, 0.12).
- **Without regalia:** the birds keep their own crimson glint.
- **Not tinted:** the bats' sigil, and the bring-escort swirl.
- **Related:** `Features.Fx.VeilMove` also stamps `NHAdminFlare` (a server time) on the staff member's character. The accessories session's `AccessoryFx` uses it to flare the sigil halo.

## The birds
Both are built by headless Blender scripts in `art/vfx/crow/`. Each is one skinned mesh with one material, using Roblox's DoubleSided wings and tail.

| | NHCrow | NHBat |
|---|---|---|
| Script | `nh_crow.py` | `nh_bat.py` (shares nh_crow's helpers) |
| Triangles | 1,612 | 1,036 |
| Span (true size) | 2.75 studs, shown at 0.62 | 2.24 studs, shown at 0.71 |
| Rig | Root > Body > Neck > Head, Body > Tail, Body > Wing{L,R}1 > 2 > 3 (11 bones) | Root > Body > Head, Body > Wing{L,R}1 > 2 > 3 (9 bones) |
| Build | one loft from tail to beak; a cambered covert wing with a scalloped trailing fringe; seven primaries, the outer five fingered; nine fanned tail feathers | one loft from tail to nose; tall cupped ears; membrane panels between four fingers, scalloped between the tips; the arm membrane to the ankle; a tail membrane; fangs, a thumb claw |
| Maps (2048) | painted per pixel from a baked feather coordinate: contour scallops (finer on the head), rows of coverts, barbed vanes with a rachis, nasal bristles, a crimson iris ring (emissive); soft baked AO | fur strands in clumps, wrinkled membranes with raised finger bones and a crimson cast at the trailing edge, ridged ears, crimson eyes (emissive) |

**The wingbeat** (`flap` in `Controllers.World.TpFlock`): no animation is published.
- The client sets each wing bone's `Bone.Transform`: a roll about the bird's backward axis, measured from the rig's rest pose.
- Crows (3.6 beats/s): the arm leads, then the forearm and hand follow later so the tip whips. The hand sweeps forward on the downstroke, and crows set their wings to land.
- Bats (7.5 beats/s): a deeper stroke, with the forearm and hand folding back on the upstroke.

**Sprites** (`make_tp_sprites.py`): `NHTpFeather` (one curved feather, 512) and `NHBatSigil` (1024, white on alpha, tinted crimson).

## Files
| Where | What |
|---|---|
| `ReplicatedStorage.Config.AdminTp` | Who gets bats, the radius, timings, counts, sound and texture ids |
| `ServerScriptService.Services.Features.Fx` | `TpStyle(P)`, and `VeilMove(P, CFrame, Opts)` with `Admin` / `Quick` / `By` |
| `ServerScriptService.Services.Features.Admin` | Bring, Go to, Go to a place, Bring all and click teleport pass their `Opts` |
| `ServerScriptService.Packages.Cmdr.BuiltInCommands.Admin.teleportServer` | Cmdr's teleport goes through `VeilMove` |
| `StarterPlayerScripts.Controllers.World.TpFlock` | The client: pool, wingbeat, paths, sigil, sound, hide and reveal |
| `ReplicatedStorage.NHTpFx.Crow` / `.Bat` | The rigged templates (the imported FBX, scaled for play) |
| `art/vfx/crow/` | The Blender sources, sprite script, mock-up script |
| `art/group-upload-tpvfx/` | The FBX and maps handed over for import |

## Safety
- **Clients never start it:** `ReplicatedStorage.NHFx` is server → client only, and its `OnServerEvent` is ignored. The flock events are fired only from staff paths after `Features.Admin` has checked the request (`Run` → permission → command) or after Cmdr's BeforeRun hook.
- **Studio test switches** (server-set player attributes, honoured only in Studio, where everyone is staff):
  - `NHTestNotAdmin` makes `TpStyle` return nil, so a "student" can be tested.
  - `NHTestTpStyle = "Crow"` or `"Bat"` forces a flock, so the owner's account can try the crows.

## Assets (group 15981569)
| | Id |
|---|---|
| NHCrow mesh (re-import without vertex colours) | 119830598565985 |
| NHCrow color / normal / rough / emissive | 128564516412240 / 70569800534402 / 75882004757354 / 110555480176660 |
| NHBat mesh | 110917411754122 |
| NHBat color / normal / rough / emissive | 132807093846946 / 126869399840099 / 103386643088308 / 86473465009685 |
| NHTpFeather / NHBatSigil | 112386227679173 / 133451806468775 |

The first import carried the bake's feather coordinate as vertex colours, which Roblox draws as a rainbow tint over the maps. `nh_crow.export` now strips colour attributes and writes `colors_type="NONE"`.

## Verified (NH Combat Test, Studio Play, 2026-11-10)
**[PT] On slot 4 "Testy", through the desk's real `NHAdmin.Run` remote:**
- **Ctrl + click as the owner:** `TpFlock Bat`, moved 30 studs in 0.67 s.
- **A second click within 2 s:** `TpFlock Bat quick`, 0.23 s.
- **Forced to crows:** `TpFlock Crow`. The client spawned 56 crows (28 leaving, 28 arriving).
- **As a student** (`NHTestNotAdmin`): only `Veil` and `VeilSmoke`, the old veil.
- **Invisible** (`NHInvisible`): moved with no events at all.
- **A client firing `TpFlock` / `TpEscort` on `NHFx` itself:** nothing came back.
- **Escort:** `TpEscort Crow` put 8 crows round the target.
- **Cmdr's `teleportServer`, called directly:** `TpFlock Crow`, moved 15. Cmdr's own BeforeRun hook refuses WhosRello, who isn't in `Config.Cmdr`.
- **Reduce Motion:** about 20 crows instead of 56 (10 leaving, 10 arriving).

**On screen** (a 25× slowed copy of the client drawing round a stand-in student, so frames could be caught):
- crows bursting and scattering, with the swirl forming at the far end (`img/tp-crows-scatter.jpg`, `img/tp-crows-flock.jpg`)
- both crimson sigils (`img/tp-bats-sigils.jpg`)
- the bat vortex rising while the arrival stoop gathers (`img/tp-bats-vortex.jpg`)
- the re-imported birds in Studio (`img/tp-birds-studio.jpg`)

**After the re-import:** crows (56) and bats (86 at 0.5 s) all launch with their wings beating.

**No errors** from the new code.

**Not tried:**
- a second real player watching (the onlooker's view was drawn locally)
- the desk's Go to a player and Bring with two players (the same `VeilMove` paths)
- hearing the sounds (they loaded without errors)
- a live server, and a true level-0 student (Studio makes everyone staff)

**Map place (1.75.1):** synced. `Config.AdminTp`, `NHTpFx` and `World.TpFlock` are copied, and `Features.Fx` and `Features.Admin` are NH Combat Test's files. The Map has no Cmdr, so the `teleportServer` edit doesn't apply there.
