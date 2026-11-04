# Console controls

A gamepad plays the whole game: combat, carrying, race actions, the skateboard, the hotbar and every menu (1.31.0). `StarterPlayerScripts.Controllers.Gui.GamepadControls` adds what isn't a plain key; the combat buttons sit next to each action's keyboard key in `Bind.Keybinds.Config`.

## The buttons

| Button | On foot | Riding a board |
|---|---|---|
| RT | Strike (hold); as a wolf, bite | - |
| RB | Heavy; as a wolf, leap | - |
| LT | Block (hold) | Push (hold) |
| LB | Feint | - |
| B | Dodge (closes a menu when one is open) | - |
| A | Jump (Roblox's) | Ollie |
| X | Interact with a prompt, or draw / sheathe | Kickflip |
| Y | Carry / drop (and greet a stranger's prompt) | - |
| LS (L3) | Run, a toggle | - |
| RS (R3) | Crouch / slide, a toggle (held with RT: uppercut) | - |
| D-pad Up | Grip, or take out / put away your board | Get off |
| D-pad Down | Your race's action on a downed body | - |
| D-pad Left / Right | The hotbar slot before / after | - |
| View | The quick menu | - |
| Left stick | Move | Steer (up pushes, down brakes) |
| Right stick | Camera | Camera |

- **Combat buttons run the keyboard's action modules.** `Keybinds.Config` lists the keyboard key first, then the gamepad button. A Settings rebind replaces only the keyboard key (`InputController.Rebind` keeps `Button*` and `DPad*` entries).
- **LS and RS are toggles.** They press Shift and Ctrl through `InputController.Press`, as the touch buttons do. RS is bound through ContextActionService at priority 3000, because Roblox's gamepad camera uses RS for zoom.
- **The wolf** (`WolfForm`): RT keeps biting while held (every 0.35 s) and RB leaps, the keyboard's click and R.

## The quick menu (View)

![The quick menu](img/gamepad-menu.jpg)

- **Buttons:** Phone, Journal, Factions, Report Card, Students, Study Group, Locker, Wardrobe and Emotes. Night races also get Transform and Night Sight. Then Cinematic and Settings.
- **Controls list:** the button mapping is on the right side of the menu.
- **Built from kit parts:** `Kit.Panel` and `Kit.Button`.
- **Why View is free:** `GuiService.AutoSelectGuiEnabled` is off, so View opens this menu instead of Roblox's top-bar selection. Everything on the top bar is in this menu.

## Menus

![Menu navigation: the phone's first app selected](img/gamepad-phone-selected.jpg)

- **What counts as a menu:** a visible panel at least 400 design px tall or most of the screen, the emote menu, the study group drawer or the quick menu.
- **When one opens** on a gamepad, its top-left button is selected, and navigation is held inside it (`GuiService:AddSelectionParent`). The D-pad and left stick move between buttons, and A presses.
- **Selection outline:** the kit's FrameThin in gold (`PlayerGui.SelectionImageObject`).
- **B closes the open menu**, and doesn't dodge: B is taken at priority 3000 only while a menu or the cinematic view is open.
  - `GamepadControls.Menus` maps each menu's gui to its close function.
  - A menu not in the list gets its Close button selected instead.
  - Closing the phone also puts away the phone item if you're holding it from the hotbar.
- **Dialogue:** the first reply is selected. B leaves, as before.
- **The main menu** has its own D-pad, A and B navigation (unchanged).

## Hints

`Components.InputKind()` returns "Gamepad", "Touch" or "Keyboard" (from the last input), and `Components.InputKindChanged` fires when that changes. Hints switch with it:

| Where | Keyboard | Gamepad | Touch |
|---|---|---|---|
| Main menu | W / S or ↑ / ↓ to choose · Enter to select | D-pad to choose · A to select | Tap to choose |
| Save slots | A / D or ← / → … Enter to play … Backspace | D-pad to choose · A to play · B to go back | Tap a slot to play |
| Intro | Press any key to skip | Press any button to skip | Tap to skip |
| Dialogue | 1-9 reply · click text to skip · walk away to leave | D-pad to choose · A to reply · B to leave | Tap a reply |

Key caps use `Components.KeyName`, which now also names LS, RS, View, Menu and the D-pad directions.

## Testing in Studio

- **Turn it on:** set the ReplicatedStorage attribute `NHGamepadTest = true`, so the kit treats the session as a gamepad (hints, menu selection).
- **Press buttons:** Studio's keyboard input tool can send gamepad key codes (ButtonR2, DPadUp and so on).
- **Action log:** with the flag on, `InputController` writes each action it runs to the Player attribute `NHLastAction`.
- **Board:** a no-slot player gets one with the Player attribute `NHSkateTest`.
- **Clean up:** clear the flag afterwards.

## Not done yet

- **Not tried with a real controller or on a console.** Studio's simulated buttons aren't a gamepad:
  - A pressing the selected button, and stick navigation between buttons, weren't exercised.
  - Analog trigger thresholds weren't checked either.
- **Sliders** (Settings) can't be moved with the D-pad yet.
- **Class activities** (lessons) have no gamepad controls. The sports games already have theirs.
- **No lock-on** for combat. The camera is Roblox's default.
