# The phone

Added in 1.12.0. Server: `Services.Features.Phone`. Client: `Controllers.Gui.Phone`. Model: `ServerStorage.NHPhoneModel` (the owner's model; the original is in `NH_Backup.Keys_pre.Phone_original`).

## The handset
- **Spawning:** every character spawns with a **Phone** Tool, attribute `NHPhone`. Its model is welded to an invisible handle, and the screen shows the crest.
- **Equipping (hotbar, or Y):** opens the UI. Unequipping closes it. Closing from inside the phone (Camera, Timetable...) also puts it away.
- **The pose:** the game's animations don't raise the arm for tools, so on equip the server sets the right shoulder's `C0` to `Base * Angles(0, 45°, 105°)`, which replicates to everyone. Unequipping restores it.
- **The grip:** solved in Play against the R6 `RightGrip` weld. It stands the phone upright with the screen toward the face.

## The screen
A modern smartphone layout (the owner's reference) in the school's style:
- **Body:** rounded iron with a polished-gold gradient edge, side buttons, and the kit's `PanelBg` slate grain.
- **Notch:** a speaker slot and a lens.
- **Status bar:** the school clock, signal and battery.
- **Wallpaper:** a preset gradient, or your own image through `rbxthumb`, with the crest faint behind it.
- **App grid:** 4 wide. Each icon is a rounded enamel tile in its own colour, with the kit glyph pressed into a `SlotBg` well and a gold hairline. Labels are 13 pt Fantasy with a full outline and a shadow, and long names shrink to fit their tile.
- **Bottom:** page dots, a frosted dock, and red badges.

## Apps
| App | Where | What it does |
|---|---|---|
| Wallet | dock | send Yen (1 to 5,000, 5 s apart, confirm step); history (last 15) |
| Night FM | dock | your own music by audio ID (only you hear it); recent IDs (last 10) |
| Classmates | dock | everyone in the building; send Yen, invite to your study group |
| Camera | dock | the cinematic view |
| The Midnight Bell | grid | the live school paper |
| Timetable | grid | opens the timetable |
| Study Group | grid | opens the study group drawer |
| Factions | grid | opens the factions panel |
| Style | grid | wallpapers: 8 presets or an image ID |
| Options | grid | opens Options |

Per the owner, there's no Report Card, Locker or Journal in the phone.

## Data and remotes
- **Saved:** `PlayerData.Phone = { History, Recent, Wallpaper = { Preset, Image? } }`, written with `SetPhone` and checked by `Phone.Sanitize`.
- **Remotes:** `ReplicatedStorage.NHPhone` has Get, Send, Gazette, Contacts, SaveRecent and SaveWallpaper (RF), plus Changed (RE).

## Names
- Wallet, Classmates and the paper show a student's name only if you know it (`Strangers.Knows`); otherwise "a stranger".
