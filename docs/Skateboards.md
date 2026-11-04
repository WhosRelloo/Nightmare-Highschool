# Skateboards

Ride around the school grounds on your own board, Bully style. Nine boards, one free for everyone.

## Riding
| Key | What it does |
|---|---|
| **B** | take your board out and step on (B is shared with Grip: with a downed body within grip reach, or one you're carrying, B grips instead) |
| **B** again | step off; the board is put away |
| **W** | push off and roll (one push from a stop, then you keep rolling) |
| **S** | brake, then roll back slowly |
| **A / D** | steer (you lean into the turn) |
| **Shift** | push hard: a few kicks and a short boost of top speed while you hold it |
| **Space** | ollie (a crouch, then the pop) |
| **E** | kickflip: a bigger pop while the board flips a full turn under your feet and lands flat |

- **Speeds:** 30 studs/s cruising, up to 50 on a boost (a sprint is 40.5; the anti-teleport check allows 100).
- **Crashes:** riding into a wall above 20 studs/s throws you off. It's a server ragdoll, so everyone sees the fall, and you're back up after 2.6 s.
- **While you ride:** combat and movement keys are off, any held snack is put away, interact prompts are off on your screen (E is the kickflip), and the camera is left as it is.
- **Not while:** you're down, gripped or carrying someone, sitting, in the main menu or in a sports match. A rider who gets downed or sat is stepped off.

**On a touch screen** (1.29.0): the thumbstick steers (up pushes, down brakes), the jump button ollies, and the touch buttons are OLLIE, FLIP, PUSH (hold) and GET OFF. A gamepad stick steers too. See [Touch-Controls](Touch-Controls.md).

## The boards
Owned boards live in the Locker's **Boards** tab (`` ` ``): click one to equip it, or buy the ones you don't have with Yen. The equipped board is the one B takes out.

| Board | Rarity | Price |
|---|---|---|
| Moonlit (the school on its hill under a full moon) | Common | free, everyone owns it |
| Bone Hand (bone-white, a skeleton's hand) | Common | ¥350 |
| Night Ravens (purple and black, a raven) | Uncommon | ¥600 |
| Grave Rovers (grave green, a cross and a ball) | Uncommon | ¥600 |
| Iron Wardens (iron grey and rust, a shield) | Uncommon | ¥600 |
| Gargoyle (carved stone, a grinning gargoyle) | Rare | ¥1,200 |
| The Vigil (ink and gold, a candle) | Rare | ¥1,500 |
| The Crimson Court (crimson, a thorned rose) | Rare | ¥1,500 |
| The Headmaster (black lacquer, gilt pinstripes, the crest) | Legendary | ¥4,000 |

The models are props batch 18 (`art/props/nh_props_batch18.py`, deck art from `art/props/skate_art.py`, 2048 maps, sheet `art/props/_batch18_final_sheet.png`). Every board has the same rig, so any of them rides the same.

## How it works
- **Config:** `ReplicatedStorage.Config.Boards` (the list, prices, the starter and the ride tuning).
- **Saved:** in `PlayerData.Inventory.Boards = { Owned = { id }, Equipped = id }` (`Config.Items.Sanitize` keeps it, `Config.Boards.Sanitize` checks it; the starter is always owned). `Services.Features.Inventory` gains `Boards(player)` / `SetBoards(player, boards)`, and its state carries `Boards` to the Locker.
- **Server** `Services.Features.Skateboard`:
  - spawns your equipped board under your feet (`workspace.Skateboards`)
  - welds it under your root with a Motor6D (`SkateboardRideMotor`), feet on the deck
  - ragdolls a crash (`ReplicatedStorage.NHSkate.EasyRagdoll`)
  - sets the character attributes everyone reads: `NHSkate` (board id), `NHSkatePose` (`Push` | `Ollie`) and `NHSkatePoseAt`
  - handles Buy / Equip
  - Remotes: `ReplicatedStorage.NHSkateboard`
- **Client** `Controllers.World.Skateboard`: your ride.
  - A BodyGyro holds your facing and a BodyVelocity your speed.
  - The wheels probe the ground, and a wall-like face at speed is a crash.
  - Your hip height is raised by the deck's height while you ride, so you stand on it.
  - Pushes, ollies and kickflips are timed, not animation markers.
  - **The kickflip** (`Config.Boards.Ride.kickflip`): E pops you up harder than an ollie. Between 20% and 80% of the trick the board turns a full turn about its long axis, pivoting on the deck and rising a little. This is the ride motor's `Transform`, which every client sets from the rider's `NHSkatePose = Kickflip`.
- **Poses** `Controllers.World.SkateboardPose`: every client poses every rider on the R6 joints, in Stepped after the Animator, within 220 studs. No animation assets are needed.
  - **Stance:** side-on, a soft crouch, arms out, head over the leading shoulder.
  - **Push:** the back foot sweeps down and back.
  - **Ollie and kickflip:** crouch, pop, tuck.
  - **Lean:** into the turn.
  - Every board spins its wheels with its speed and leans its trucks.
- **Assets** `ReplicatedStorage.NHSkate`: `Boards` (the rigged templates), `Sounds`, `FX` (the wheel trails, crimson rolling and gold on a boost) and `Effects`.
- **The rig** (`Studio/skate_setup.luau`): a `PartForMotor6D` root, with Motor6Ds to `Board`, `TruckF` / `TruckB` (lean about the long axis) and `WheelsFL/FR/BL/BR` (spin about the axle). The nose is the root's −X. Without the imported meshes it builds plain stand-in boards, so riding works before the models are in.
- **Input:** `InputController` lets only Grip through while you ride. `InputController General.Grip` calls `Skateboard.Toggle()` unless a downed body is within reach. Settings shows the key as **Grip / Skateboard**.
- **Studio tests without a save slot:** with the player attribute `NHSkateTest` = true (Studio only), the server lends the starter board.

## Credits
The riding is ported from the **"SkateBoard"** open-source Roblox kit by **vexarino** (payhip.com/b/7UnMA, shown in the video "Roblox studio SkateBoard"). The kit includes Easy Ragdoll by theonlyflare. Its page offers it to "use, modify, and customize for your own projects" but gives no formal licence for published games: ask the author before release. The kit shipped without animations; Nightmare High's poses are its own.

## Verified (Studio, 2026-11-04)
- **The boards:** the owner imported the nine FBX files and `skate_setup.luau` rigged them from the meshes. The wheels sit on the ground, the pivots match the rig, and the maps are on every piece.
- **Play, with no save slot loaded** (the `NHSkateTest` Studio switch):
  - **Getting on:** a request spawned the board under the rider and mounted it.
  - **The meshed Moonlit board:** its wheels were on the floor (0.90 on a 0.90 floor), it rolled at 20 studs/s with the wheels spinning, and B stepped off with hip height and auto-rotate restored.
  - **The stand-in boards:** W rolled at 25–47 studs/s, D turned 60° in 0.4 s with a lean, and Space rose 2.1 studs.
  - **A crash:** a wall at speed threw the rider into a ragdoll, who was back up afterwards.
  - **The pose:** stance yaw 78°, crouch 0.16, legs spread 29°, arms out 38°; the push squared the body to 45° and swept the back leg 28°.
- **The kickflip (1.26.0), in Play with no save slot:**
  - **Getting on:** interact prompts went off.
  - **E:** the rider rose 4.9 studs, and the board turned its full turn about its long axis and landed flat, with the rider still on it.
  - **B:** stepped off and turned prompts back on.
- **Not verified yet:**
  - another player watching a kickflip
  - the Locker's Boards tab, buying and equipping (they need a loaded record)
  - another player watching a rider and the crash
  - riding over kerbs, stairs and slopes
