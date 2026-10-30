# Nightmare Highschool UI Kit

A gothic UI kit for Nightmare Highschool: a cursed school after dark, built from iron-gate arcades, chalk-smudged slate, wax seals, church candles and a cracked skull-bell. It lives in the **NH Combat Test** place.

| Where | What |
|---|---|
| `ReplicatedStorage.UI.Theme` | Colours, rarity and faction palettes, fonts, sizes, scale rules, texture ids, 9-slice data, tweens |
| `ReplicatedStorage.UI.Components` | Builder functions for every widget (API below) |
| `ReplicatedStorage.UI.ServerDirectory` | Live server list: MemoryStore heartbeat, remotes and client polling |
| `ReplicatedStorage.UI.Preview` | Sample layouts with NH data (`Build`, `BuildServerSelect`) |
| `ServerScriptService.NHServerDirectory` | One-line Script that runs `ServerDirectory.StartServer()` |
| `StarterGui.UIKitPreview` | Preview of every HUD/menu component. Saved **disabled**. |
| `StarterGui.ServerSelectPreview` | Preview of the server selection screen. Saved **disabled**. |
| `Tools/ui-textures/*.py` | Python scripts that generate all the texture art (re-run them to tweak it) |

![UI kit preview](img/ui-kit-preview.jpg)
![HUD at 1:1](img/ui-kit-hud-1to1.jpg)
![Server selection](img/server-select-preview.jpg)

## Viewing the previews

- **Edit mode:** select the ScreenGui in StarterGui and tick `Enabled`. Untick it again when you're done.
- **Live in a Studio playtest:** set the ScreenGui's `LivePreviewInStudio` attribute to `true`, then press Play. Its `PreviewGuard` LocalScript rebuilds it with working callbacks. On the server screen that means your own character in the preview pane and the real server list.
- **Real games:** the guard destroys both GUIs when they spawn, so players never see them.
- **Rebuilding the saved edit-mode preview** after a kit change (Studio command bar): `require(game.ReplicatedStorage.UI:Clone().Preview).Build(game.StarterGui.UIKitPreview)` (use `BuildServerSelect` for the server screen). The `Clone()` gets around `require` caching.

## Art and textures

All art is original and was made for this kit. It's procedurally generated, with **PBR shading baked into each image**. Roblox GUI images can't render live PBR materials, so each sprite was rendered from height, normal, albedo, roughness and metalness maps. The lighting is a GGX/Cook-Torrance key light, a rim light, hemispheric ambient and ambient occlusion. Grime raises roughness and darkens the albedo.

The textures are greyscale, so `ImageColor3` tints them. That's how the faction variants work: Vigil gold and Court red.

- **Ornate panel frame:** 4 corner pieces plus 4 edge strips tiled with `ScaleType.Tile`. The edges repeat a gothic iron-gate arcade instead of stretching.
- **9-slice frames:** `FrameThin` for rows, buttons and plates, and `FrameSlot` (bracket corners) for item slots and server rows.
- **Health bar:** PBR end caps, arcade rails (the panel edge tiles) and a veined fill that tiles horizontally.
- **Other art:**
  - a clock-face orb ring and a glass orb
  - wax-seal rarity gems
  - diamond knobs and pips
  - a divider, a soft glow and a drop shadow
  - icons: candle (Vigil), blood drop (Court / Vampire), quill nib (Human), cross (Priest)

## Conventions

```lua
local Components = require(game.ReplicatedStorage.UI.Components)
local root, api = Components.Toggle({ label = "Subtitles", value = true,
    onChanged = function(v) print(v) end,
    Position = UDim2.fromOffset(20, 20), Parent = someFrame })
```

- Every builder works the same way: `Components.X(opts) -> (root: GuiObject, api: table)`.
- Lower-case opts are component data. PascalCase opts (`Name, Size, Position, AnchorPoint, LayoutOrder, Visible, ZIndex, Parent`) are copied onto the root, with `Parent` set last.
- `api.Root` is the root instance. Interactive parts have `:Set(v, silent?)` and `:Get()`, fire their `onChanged` / `onClick` callback, and mirror their value to the root's `Value` attribute.
- **Sizes are design pixels for a 1920×1080 screen.** Call `Components.AutoScale(screenGui)` once per ScreenGui. It adds a UIScale = min(w/1920, h/1080), clamped to `Theme.Scale.Min`/`Max`, and on touch-only devices it never goes below `Theme.Scale.TouchMin` (0.92). Since every tappable row and button is at least 44 px, tap targets stay at 40 px or more. Use anchors and scale positions for screen placement, since UIScale only scales offsets. Use `Panel{maxSize=}` and the built-in ScrollingFrames on small screens.
- **Z-order:** `ZIndexBehavior.Sibling`. Inside a panel: background 1, ornament 6, `Content` 7.

## Components

**Primitives**

| Builder | Description |
|---|---|
| `Text(props)` | TextLabel with kit defaults |
| `Emboss(label, bottomColor?, stroke?)` | Engraved title look: gradient plus dark stroke |
| `Slice(key, color, props)` | 9-slice image |
| `Image(key, props)` | Image by `Theme.Images` key |
| `new(class, props, children)` | Instance helper |
| `KeyName(key)` | Short display name for a key |
| `Divider{color?, height?}` | Ornamental horizontal rule |
| `SectionHeader{text, color?, height?}` | Gold embossed caps with a divider underneath |

**Panel{title?, accent?, frameColor?, bgColor?, ornament?, ornamentScale?, inset?, shadow?, maxSize?}**
- `accent`: `"Vigil"` | `"Court"`. `ornament`: `"ornate"` (default) | `"thin"` | `"none"`.
- An ornate panel: slate background, PBR iron border, drop shadow and an optional engraved title plaque on the top edge. Put your widgets in `api.Content`.
- api: `Content`, `:SetTitle(t)`, `:SetFrameColor(c)`.

**Button{text, onClick(api), style?, icon?, textSize?, enabled?}**
- `style`: `"default"` | `"gold"` | `"crimson"` | `"ghost"`. Has hover, press-scale and disabled states. Minimum height 44.
- api: `:SetText`, `:SetEnabled`.

**TabBar{tabs, selected?, onChanged(i, name), textSize?}**
- The selected tab is gold with a divider underline.
- api: `:Select(i, silent?)`, `:Get() -> i, name`.

**Toggle{label, value?, onChanged(bool), onText?, offText?}**
- The whole row is the tap target. A sliding diamond knob and a candle-gold glow show when it's on.
- api: `:Set`, `:Get`.

**Slider{label, min?, max?, step?, value?, suffix?, format?(v), onChanged(v), onReleased(v), color?, labelWidth?}**
- Drag with mouse or touch anywhere on the 44 px track area. Snaps to `step`.
- api: `:Set`, `:Get`.

**KeybindRow{label, key, onChanged(newKey)}**
- Click the key plate, then press a key (Esc cancels). Accepts the keyboard, mouse buttons 2 and 3, and gamepad.
- api: `:Set`, `:Get`.

**ItemSlot{item?, size?, key?, selected?, onClick(item, api)}**
- `item = {name, count?, rarity?, icon?, id?}`.
- Shows a count badge, a rarity wax seal, a rarity glow, an icon (or the name), a hotkey and a selected glow.
- Rarities (`Theme.Rarity`): Common, Uncommon, Rare, Epic, Legendary, Cursed.
- api: `:SetItem`, `:SetCount`, `:SetSelected`, `:Clear`.

**ItemGrid{items, slotSize?, gap?, capacity?, used?, showEmpty?, onSelect(item, i), counterOffset?, showCounter?}**
- A scrolling grid of slots with a capacity plaque ("89/100").
- api: `:SetItems`, `:Select(i)`, `:Filter(q)`, `:SetCapacity(used, cap)`, `Slots`.

**SearchBar{placeholder?, text?, onChanged(t), onSubmit(t), grid?}**
- Passing an ItemGrid api as `grid` makes the search filter it automatically.
- api: `:Get`, `:Set`, `:Focus`, `TextBox`.

**StatSheet{title?, accent?, sections, rowHeight?}**
- `sections = {{header, rows = {{label, value, color?}, {label=, value=, bar=0..1}, {label=, pips={filled, total, color, caption}}}}}`.
- api: `:SetValue(label, text, color?)`, `Values`.

**DangerAlert{title?, subtitle?, seconds?, color?, icon?, onExpired()}**
- The cracked skull-bell, a pulsing red glow, an engraved title and a countdown.
- api: `:Start(seconds, onExpired?)`, `:Stop(hide?)`, `:SetText(title?, subtitle?)`.

**PlayerListRow{number?, name, faction?, race?, isLocal?, onClick?}**
- Shows "No. 0456", the faction icon and the name. The local player is gold. It's 30 px tall, or 44 px when `onClick` is set.
- api: `:Set(o)`.

**PlayerList{players, title?, rowGap?}**
- api: `:SetPlayers(list)`, `Rows`.

**DialogueBox{speaker, text, accent?, replies?, bodyHeight?, hint?, typewriter?, onReply(i, rep)}**
- `replies = {{text, onSelect, color?}}`. `typewriter` is characters per second.
- api: `:SetSpeaker`, `:SetText(t, cps?)`, `:SkipTypewriter`, `:SetHint`, `:SetReplies`.

**HealthBar{value?, color?, orb?, orbColor?, frameColor?, label?}**
- The bar's height drives all its parts (design height 64). Recent damage shows as a delayed "ghost" segment, and the % shows in the clock-face orb.
- api: `:Set(v, instant?)`, `:Get`, `:SetColor`.

**Hotbar{slots?, items?, selected?, slotSize?, gap?, onSelect(i, item), bindKeys?}**
- `bindKeys` = number keys 1-9. Pressing the selected slot again deselects it.
- api: `:Select(i?, silent?)`, `:SetItem(i, item)`, `:GetSelected`.

**VerticalMeter{value?, color?, segments?, label?}**
- A thin segmented gauge with diamond caps. Used in the preview for stamina, faith and thirst.
- api: `:Set(v, instant?)`, `:Get`, `:SetColor`.

### Server selection screen

**CharacterPreview{backText?, onBack(), footer?, player?, fallback?, model?, spin?, mirrorPose?, fov?, zoom?, yaw?}**
- A ViewportFrame (with a WorldModel) showing a character.
- **Live:** `api:BindPlayer(player)` follows `player.Character` across respawns.
  - `api:Watch(model)` mirrors any model and re-clones it (0.15 s debounce) when its look changes: parts, accessories, clothing, colours, meshes, textures, BodyColors or SurfaceAppearance.
  - It copies every Motor6D pose each frame, so the preview moves with the real character.
  - The planned character creator works with this as-is: whatever it applies to the character model shows up.
  - `fallback` (for example `StarterPlayer.StarterCharacter`) shows while there's no character.
- api: `:BindPlayer`, `:Watch`, `:Unwatch`, `:SetModel`, `:GetModel`, `:SetFooter`, `:SetSpin`.

**CreditsPanel{title?, entries = {{role, name}}, columns?}**
- A two-column grid of roles and names.

**ServerRow{name, players, maxPlayers, region?, period?, ping?, faction?, isCurrent?, jobId?, onJoin(server, api)}**
- Shows the campus name, a faction crest, "Students 18 / 30" with a population gauge, the in-game period, the region, the ping and a Join button.
- The button reads **Join**, **Full**, **Here** or **Joining...** to match the server's state.
- api: `:Set(o)`, `:SetJoining(bool)`, `data`, `JoinButton`.

**ServerBrowser{title?, servers?, onJoin, onQuickJoin, onRefresh, searchPlaceholder?, status?}**
- The header has the title, a live-status dot and line, search, Quick Join and Refresh, above a scrolling row list.
- `:UpdateServers(list)` **diffs rows in place** by `jobId`: existing rows update, new ones appear and vanished ones go, so the list doesn't jump.
- api: `:SetServers`, `:UpdateServers`, `:GetRow(key)`, `:Filter(q)`, `:SetStatus(text, live?)`. Set `api.OnJoin` / `OnQuickJoin` / `OnRefresh` to override the opts callbacks at runtime.

### ServerDirectory (the live list)

```lua
-- client, e.g. a lobby screen
local SD = require(game.ReplicatedStorage.UI.ServerDirectory)
local _, browser = Components.ServerBrowser({ Parent = screen })
local stop = SD.Bind(browser)            -- polls every 8 s, wires Join / Quick Join / Refresh
local _, char = Components.CharacterPreview({ player = game.Players.LocalPlayer,
    fallback = game.StarterPlayer.StarterCharacter, Parent = screen })
```

**Server side.** Every server runs `StartServer()` through `ServerScriptService.NHServerDirectory`.
- Every 15 s, and 2 s after anyone joins or leaves, it writes a snapshot to the MemoryStore sorted map `NH_ServerDirectory_v1` with a 45 s TTL.
- Each snapshot holds: jobId, placeId, name, players, maxPlayers, region, period, faction and updated.
- It removes the server's entry on `BindToClose`. Private servers don't advertise themselves.
- It creates `ReplicatedStorage.NHServerDirectory` (`List` and `Join` RemoteFunctions) at runtime.
- `List` is rate-limited per player and cached for 4 s.
- `Join` checks the target and teleports the player there with `TeleportAsync` and `ServerInstanceId`.
- Quick Join picks the fullest server that isn't full, or opens a new one.
- `StartServer({ publish = false, placeIds = {...} })` is for a separate lobby place.

**Where each field comes from:**

| Field | Source |
|---|---|
| Campus name | workspace attribute `CampusName`, or a stable name hashed from the JobId (Blackthorn Campus, Lantern Court, ...) |
| Period | the school clock: `SchoolClock.Epoch` via `Functions.SchoolTime`, e.g. "Period 1, 8:40 AM" |
| Region | workspace attribute `Region`, or set `SD.IpRegionLookupUrl` to an IP-lookup service (off by default: it needs HttpEnabled and calls a third party) |
| Faction | workspace attribute `ControllingFaction` (`"Vigil"` / `"Court"`) |
| Ping | not available. Roblox can't measure ping to another server, so live rows hide that column. |

**Client side.**
- `SD.Fetch() -> (servers, live)`
- `SD.Join(jobId)` and `SD.QuickJoin() -> (ok, msg)`
- `SD.Bind(browserApi, {interval}) -> stop()`

**In Studio**, MemoryStore only works in a published place with Studio API access, and teleports never run. The list then shows just the current server, the status reads "Local only", and Join explains why it can't teleport.

## Verified

- All modules and scripts compile (checked with `loadstring`).
- Every component was checked in edit-mode screenshots at 0.56× and 1:1.
- An edit-mode functional run covered:
  - toggles, slider step and clamp, tabs, keybinds, search filtering, capacity, hotbar, health, meters, button disable, dialogue replies, danger countdown, stat sheet and player list
  - the character mirror updating on a colour change, accessory add and remove, a clothing-template change, and the pose mirror
  - the server-list diff (row kept, updated, removed, reordered, empty state), snapshot fields, stable names and sorting
- **Not run:** a live playtest. Another session was using Play mode, so MemoryStore publishing, remotes, teleports, touch dragging and AutoScale on a real phone haven't been seen running.

## Not done / next

- The existing dialogue box, panels and HUD aren't switched over to the kit yet. That's for the session that owns those scripts.
- "Last joined" needs saved data (a DataStore). The footer currently shows "Enrolled as <DisplayName>".
- The credits list uses "Name" placeholders.
