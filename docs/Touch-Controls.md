# Touch controls

On phones and tablets (touch-only screens), on-screen buttons do everything the keyboard does in combat, carrying, the skateboard and your race's actions. `StarterPlayerScripts.Controllers.Gui.TouchControls` (1.29.0).

![The touch buttons on foot](img/touch-controls.jpg)

## The buttons

They're kit orbs (the health orb's recipe: `OrbFill` glass, `OrbRing`, a `Glow` shadow and a gold `Glow` when pressed or on), in three arcs around Roblox's jump button. Sizes and distances are in jump-button sizes, so they scale with it: 70 px on phones, 120 px on tablets.

| Arc | On foot | Riding a board |
|---|---|---|
| Inner (1.32) | STRIKE (hold, M1), BLOCK (hold, F), DODGE (Q) | OLLIE, FLIP (kickflip), PUSH (hold) |
| Outer (2.34) | HEAVY (R), FEINT (right click), RUN (tap on, tap off: Shift), CROUCH / SLIDE (hold, Ctrl) | GET OFF |
| Third (3.3) | What you can do now (below) | - |

- **Same code as the keys.** Each button presses its action's current key through `Bind.Keybinds.Virtual`, using `InputController.Press(Name, Down)`. Holds, releases, cooldowns and rebinds all behave exactly as on a keyboard.
- **STRIKE with nothing drawn draws first.** The keyboard's click does nothing until E.
- **CROUCH held + STRIKE = uppercut**, like Ctrl + click (`M1` checks `Keybinds.VirtualDown("LeftControl")`).
- **As a wolf** (`WolfForm`), STRIKE bites (held, it keeps biting) and HEAVY leaps: the keyboard's click and R.
- **The thumbstick steers the board.** Up pushes, down brakes, left and right steer. `Controllers.World.Skateboard` reads the PlayerModule's move vector, so a gamepad stick works too. The jump button ollies while you ride; the humanoid's own jump is off until you get off.
- **Letting go:** a finger that slides off a button still lets go of it. Hiding the buttons lets go of every held key (Block, Crouch, Sprint, M1, M2).

### The third arc

In order of importance, only when they apply:

| Button | Shows | Does |
|---|---|---|
| GRIP | a downed body within 9 studs, or you're carrying one | `Packets.Grip` (B) |
| CARRY / DROP | the same | `Packets.Carry` (V) |
| DRAIN / FEED / SIPHON / EXORCISE | the same, with your race's action | `RaceAction` (N) |
| DRAW / SHEATHE | always (not as a wolf) | the Equip packet; it isn't blocked by a prompt on screen, since prompts are tapped |
| BOARD | no body nearby | `Skateboard.Toggle` (B) |
| TURN | night races (Vampire, Werewolf, Ghoul, Wraith) | `Transform` (T) |
| SIGHT | night races | `NightSight.Toggle` (H) |
| EMOTE | always | the emote menu (`Emotes.ToggleMenu`, Period) |

- **Slots:** the arc takes slots every 16 degrees from 174 degrees, while they stay below the clock panel (`ClockHud.Panel`).
- **MORE:** if more buttons apply than fit, the last slot is MORE. It opens the rest in a line to its left, and tapping one closes the line.

![MORE open next to a downed body, as a Vampire](img/touch-controls-more.jpg)

## Hidden

- **Situations:** the main menu, dialogue, lessons, sports (`InSport`, `HasSportBall`, `SportKeys`), while you're downed, carried or gripped, and while dead.
- **Cinematic view:** it hides every gui, so a small gold RETURN orb shows in its top bar instead. It's its own ScreenGui with the attribute `ShowInCinematic` and DisplayOrder 1001, above the letterbox.

## The rest of the screen on touch

- **KitHud** (`Gui.KitHud`):
  - **Size and position:** the buttons publish how much of the right edge they use (Player attribute `NHTouchReserveRight`, px). The health bar, hotbar, Yen plate and posture meter scale to fit left of that and slide left.
  - **Study Group dock:** the HUD sits on top of the dock in the bottom-left corner instead of covering it.
  - **Keyboards:** nothing changes.
- **Skill bar** (`SkillController`): it moves to just left of the arcs at their top. Today it's empty: the Fist has no skills yet.

## Testing in Studio

- **Turn it on:** set the ReplicatedStorage attribute `NHTouchTest = true` before Play to get the touch layout with a mouse. Clicking a button works like tapping it.
- **Stand-in jump button:** a JUMP orb stands in for Roblox's jump button, which a mouse session doesn't have.
- **Action log:** with the flag on, `InputController` writes each action it runs to the Player attribute `NHLastAction` ("Block:Began" and so on), so tests can see it.
- **Clean up:** clear the flag afterwards.

## Not done yet

- **Not tried on a real phone or tablet**, and multi-touch (holding two buttons at once) isn't tested. The layout was checked at 1731x683 and 1447x683 in Studio; phone sizes come from Roblox's jump-button rules.
- **Phone-size UI pass:** the rest of the UI keeps its desktop layout at a 0.92 touch scale, which is large on a phone. This covers the clock panel, the top bar, the left buttons (Factions, Journal), the region cards and the phone. It needs a pass of its own.
- **Not covered by touch buttons:** sports (they hide the buttons; Football has its own touch check), class activities, and the hotbar's number keys (the slots are tapped instead).
