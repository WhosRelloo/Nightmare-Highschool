# 15. Tutorial: The Last Normal Night

**Status:** concept approved by the owner 2026-11-18 ("I like those concept ideas... make the whole scene and the models in
blender with the same quality as our others. I want cool scenes for the cinematic. Make all custom logos or art for
buildings yourself with our highest quality"). This spec turns the concept into a build. Branch `phase6-tutorial`.

**Sources:** the concept (chat, 2026-11-18), doc 03 (races, Prologue), doc 04 (cinematic framework), doc 12 (the `Cine`
interactive cutscene system), doc 14 (Standing Paths), and the house animation and camera style
(`r6-animation-cinematics`: Saddy references).

---

## 1. What it is

A playable cinematic of 6 to 8 minutes. It plays once, for a new character, before the existing Prologue ("The
Admission"). It's the reason you're at Nightmare High: one bad night in your quiet hometown, the evidence you left
behind, your parents finding out, and a bus that wasn't on any timetable.

- **Funny before it's dark.** It's warm small-town comedy with one supernatural slip, then the fog closes in.
- **It teaches by doing.** Every control is taught by a beat that needs it: a key hint that fades after one use, and
  no tutorial pop-ups.
- **It seeds the game.** Your prank choice sets a starting Standing Path lean, your race gets its first moment, and
  the evidence item comes back later as a running gag.
- **Skippable.** It plays on first entry. A Skip button (hold) jumps to the bus, and the Options menu has "Replay the
  Last Normal Night".

## 2. The town: Wickfield

An original, made-up small town that's a little too quiet. It's autumn, the leaves are orange, and lamplight spills
across wet streets. It's the opposite of Nightmare High's black and crimson: warm amber, cream clapboard and moss green,
so the bus into the fog feels like leaving home.

**The hometown block,** one compact set arranged around a town square, so every prank site is a short run from home:

| Set | What's there | Used by |
|---|---|---|
| **Your house** (14 Alder Lane) | a two-storey clapboard house: porch, bedroom window over the porch roof, a drainpipe, a back garden, a picket fence, a kennel with a sleeping dog, the kitchen and your bedroom (interiors) | the opening, the sneak out and in, the parents, breakfast |
| **Alder Lane** | three more houses (one kit, varied), mailboxes, streetlamps, leaf piles, parked cars | the sneak, the getaway |
| **Wickfield Square** | the Founder's Statue (Josiah Wick on a horse) with a plaque, a bandstand, benches, a church with a clock tower, and Main Street's shopfronts (Moonpie Diner, Wick & Sons Hardware, Reel Time Video, Suds Laundromat, the Wickfield Gazette office) | the cold open, the Social prank, the Priest slip |
| **Wickfield Junior High** | the school's front, the office window, the trophy hall and the hall-of-fame board | the Academic prank |
| **The lot behind the diner** | the bully's pickup truck, bins and a goose with opinions | the Combat prank |
| **Wickfield Field** | bleachers, a scoreboard, and the visiting Pembrook Prep Pumas' bus with their mascot head | the Athletic prank |
| **The Ashby House** | the condemned house at the end of the lane, with a sagging porch, boarded windows and the portrait | the Supernatural prank |
| **The bus stop** | a lone shelter on the edge of town in rain and fog, and the black school bus | the ending |

Built at Roblox scale for R6 (1 stud per Blender unit, doors 7 to 8 studs tall), like every other prop in the game.
It's placed in the NH Combat Test place as its own area away from the school (`Workspace.Hometown`), streamed in
only for the tutorial. **The Map place is never touched.**

## 3. Custom art and logos (all original, made by Claude)

Every sign and logo is original, drawn at 4x and baked into PBR (painted wood, enamel, neon tubes, brass letters and
gold leaf on glass). Nothing comes from an existing brand.

| Art | Where | Style |
|---|---|---|
| **The Wickfield town crest** (an oak leaf, a lantern, "Est. 1851") | the welcome sign, the town hall banner, the bus stop | carved, painted wood |
| **Wickfield Junior High "Wicks"** (a candle-flame mascot) | the school front, the hall-of-fame board, your old gym bag | varsity felt and painted brick |
| **Pembrook Prep Pumas** (a snarling puma head) | the rival bus and the mascot head | enamel badge |
| **Moonpie Diner** (a crescent biting a pie) | a neon sign on the diner, menus | neon tube with a chrome frame |
| **Wick & Sons Hardware**, **Reel Time Video**, **Suds Laundromat**, **The Wickfield Gazette** | shopfronts | gold leaf on glass, painted signboards, a lightbox |
| **The Founder's plaque** ("Josiah Wick, who never once broke a rule") | the statue plinth | cast bronze |
| **The Nightmare High admission envelope** (black, with a new crimson wax crest, not the UI Seal) | the breakfast scene | a 3D prop |
| **The brochure** (a cheerful tri-fold with tiny-print jokes) | the breakfast scene, readable close up | a printed page |
| **Your livestream overlay** ("LIVE", the viewer count climbing to 2M) | the Social prank and the parents' phone | UI art |
| **The "Missing: one garden gnome" flyer** and other street-pole posters | lamp posts | printed paper |

## 4. Characters and creatures

- **You:** your own character in your saved look, in pyjama-hoodie "night clothes" over the top (a 2D shirt
  template made for the tutorial), then your uniform on the bus.
- **Mom and Dad:** R6 NPCs dressed by the existing look system, in civilian clothes. Dad has reading glasses
  (an accessory). Comic timing is all in the pose and the camera.
- **The dog, Biscuit:** a sculpt-quality, rigged and animated basset hound. He sleeps, wakes, stares, sighs and
  goes back to sleep. No blocky organics.
- **The goose:** a sculpt-quality, rigged and animated Canada goose: neck stretched, wings out, a honk, a charge
  and a waddling victory lap. It's the Combat prank's fight. Played for laughs, nothing is hurt.
- **The bus driver:** a tall, thin figure in a driver's cap and coat whose face is always in shadow (a lit cap
  brim over darkness). There are no visible features to model, so it's always framed from the chin down or lit
  from behind.
- **The bully, Chet:** an R6 NPC heard from inside the diner ("WHO TOUCHED MY TRUCK"). Only his silhouette shows.

## 5. The run, beat by beat

Built on `Controllers.Cine` (doc 12). Each beat is a `Config.Cine` segment, and the prank choice is a graph branch.
Camera and animation follow the house style:
- an alive, tracking camera, low and leading the motion on movement beats
- slow orbits on showcase beats
- a hard cut on the impact frame for the gags
- moving holds, never dead stills

| # | Beat | Plays as | Teaches | About |
|---|---|---|---|---|
| 1 | **Cold open, 11:58 PM.** An aerial crane over Wickfield's rooftops: the church clock ticks to midnight and pigeons scatter. Push down Alder Lane to your window as it slides open. Freeze-frame on you halfway out, with a title card: *"This is me. You're probably wondering how I ended up at a school for monsters."* | cinematic | none | 25 s |
| 2 | **The sneak out.** You climb down the porch roof and the drainpipe, cross the garden and get over the fence. Biscuit wakes, stares, sighs and goes back to sleep. If you stand up near him he lets out one bored "wuff" and a bedroom light flicks on (a soft fail: you crouch and wait for it to go off). | play | move, crouch, climb, jump | 60 s |
| 3 | **The square.** You run into the square, where a lamp-post flyer shows "THE PLAN" (doodles of all five pranks). Pick one by walking to it, with a choice card for each. | play + choice | sprint, interact | 20 s |
| 4 | **The prank.** One of the five branches (§6). Each has a set-up, a gag and a climax. | play + Cine prompts | one mechanic each | 90 s |
| 5 | **The slip.** At the climax your race shows for the first time (§7), as a short comic beat shot like a reveal. | cinematic | none | 10 s |
| 6 | **The getaway.** A chase back to Alder Lane: the night watchman's flashlight sweeps, a sprinkler goes off, and a car's headlights catch you (dive into a hedge on a Press prompt). In slow motion you drop the evidence without noticing. The camera holds on it in a close-up while you're gone. | play + QTE | sprint, dodge, a Press prompt | 45 s |
| 7 | **Home, 12:41 AM.** You climb back in perfectly, sneak into bed and pull up the covers. A lamp clicks on. Mom and Dad are sitting in the dark at the foot of the bed. A slow push-in. | cinematic | none | 15 s |
| 8 | **The excuses.** Pick an excuse three times: "I was sleepwalking", "Define 'out'", "...the goose started it" (varies by prank). Each one fails worse: Dad holds up the evidence, Mom turns her phone round. Dialogue choices with comic camera reactions. | Cine choices | dialogue choices | 40 s |
| 9 | **Breakfast.** Morning sun, cereal. Mom slides the black envelope across. Dad, too calm: *"We found a school that specialises in... kids like you."* You can pick up the brochure, turn it over and read the fine print. | play (inspect) | inspect an item, the phone (Mom's text) | 40 s |
| 10 | **The bus.** At a rain-soaked bus stop at the edge of town, a black bus that wasn't on the timetable pulls in out of the fog. The doors hiss open and the driver's face is in shadow. You step on, the doors close, and Wickfield's lights fade into fog. Smash cut to the Nightmare Highschool title card, then the existing Prologue. | cinematic | none | 30 s |

## 6. The five pranks (each one leans a Standing Path)

The lean is a small head start: +1 to that path's first-tier tally, with no tier and no title. It's just a nudge, saved
as `Progress.Origin`.

| Prank | Lean | Set-up | Gag | Climax | Evidence left behind |
|---|---|---|---|---|---|
| **The Hall of Fame** | Academic | Climb in the Junior High office window (a crouch through a gap) | Swap every name on the hall-of-fame board for yours, one letter tile at a time (a timing prompt) | The board's lights flicker on, spelling your name 20 times | your library card, stuck in the window frame |
| **The Statue** | Social | Climb the Founder's Statue with toilet paper and a cone | Dress Josiah Wick up while your phone livestreams (the viewer count climbs with every flourish you land) | A perfect pose with the statue, then a flash, then 2M views | the livestream itself (and your phone case on the plinth) |
| **The Truck** | Combat | Sneak into the lot behind the diner and let down the tyres of Chet's truck | The goose sees you. A short combat tutorial: dodge, shove and a grip finish that ends with the goose sitting on the truck in triumph and you dusted with feathers | Chet bellows from inside the diner and you run | your monogrammed backpack, on the truck's bed |
| **The Mascot** | Athletic | Get across the dark field to the Pumas' bus | Lift the giant puma head, put it on and sprint (a stamina tutorial). The scoreboard lights up by itself | A victory lap with the floodlights coming on one by one | one muddy sneaker, stuck in the long-jump pit |
| **The Portrait** | Supernatural | Get into the Ashby House through the boarded door (stealth past creaking boards) | Take the portrait of old Mrs Ashby off the wall. Her painted eyes follow you, and when you look back she's smiling | The house's lights all come on at once, then off | your retainer, left on the parlour table |

The evidence item is kept (`Progress.Origin.Evidence`). It comes back later: Dad's texts on your phone, a Midnight
Bell item, a line from the hall monitor.

## 7. The slip (race reveals)

| Race | The slip |
|---|---|
| Human | Nothing happens to you. A stray cat on the wall does something impossible instead (it stands up and walks off on two legs), and you decide you didn't see it. |
| Vampire | You run past the dark diner window and have no reflection. You stop, step back, check twice, and wave. The window stays empty. |
| Werewolf | The moon slides out of a cloud. You clear the 3-metre fence in one bound, land in a crouch, look at your hands and shrug. |
| Ghoul | You're suddenly starving. You eat the evidence you were about to leave (then drop a different item later). |
| Wraith | You trip, phase halfway into a wall and get stuck at the waist. Your legs kick. You pop out the other side. |
| Priest | You run past the church and its bell tolls once by itself. Every pigeon on the roof turns to face you and bows. |

## 8. Shot list (house style)

| Shot | Lens and move | Notes |
|---|---|---|
| Cold-open crane | wide (20 mm look), slow crane down from the clock tower, horizon level, 1 to 2 deg/s drift | Wickfield shows its best side: lamplight, wet streets, leaves |
| Window open | medium close-up on the window, slow push | the freeze-frame and the card |
| Sneak | low chase cam behind and to the side, leading the motion, never locked | Biscuit's stare is a hard cut to a low close-up on his eyes |
| Prank gags | 3/4 high wide for the readable action; a hard cut on the gag's payoff frame to a low, close, dutched (about -13 deg) angle, then a moving hold (~0.4 s), then back to a calm wide | the house finisher recipe, used for comedy |
| The goose | a two-character exchange: a steady 3/4 high wide keeping both and the gap readable | the goose gets anticipation (a neck coil) and a long settle (a smug waddle) |
| The slip | a reveal: a slow push-in, then the gag on a cut | |
| The evidence drop | slow motion (0.25x for 1.2 s) on a low close-up as the item tumbles, then real time as you run off frame. The camera stays on the item | |
| Parents | the lamp-click shot is a static locked wide that's still breathing (a 1-2 % slow push). Excuse reactions are quick cuts to each face | the one place a near-still camera is the joke |
| Breakfast | warm, soft, 3/4 over the table. Insert shots of the envelope and the brochure | |
| The bus | low wide in the rain, the headlights flaring through fog, the doors in close-up. The final shot is from inside the bus looking back as the town fades | |

## 9. How it's built (the plan)

**Art (Blender, the props pipeline: modelled in studs, PBR baked, FBX plus maps, staged for import):**

1. **Signs and logos:** 2D art drawn at 4x, then made into sign props (painted boards, neon, gold-leaf glass,
   bronze relief).
2. **The house:** exterior, the bedroom and the kitchen.
3. **The street kit:** the house variants, the lamp, the fence, the mailbox, the hedge, leaf piles, a parked sedan.
4. **The square:** the statue, the bandstand, the church and clock tower, and the five Main Street shopfronts.
5. **The prank sites:** the Junior High front and office, the diner lot and Chet's truck, the field, the Pumas' bus and
   mascot head, the Ashby House.
6. **The creatures:** Biscuit and the goose, sculpted, rigged and animated (in the same quality bar as the Anatomy
   specimens).
7. **The bus stop and the black bus.**
8. **The props:** the envelope, the brochure, the evidence items, the night-clothes shirt, Dad's glasses and the
   cereal set.

**Game (code):**

- A `Tutorial` service decides who sees it (`Progress.Origin` is nil) and places them in `Workspace.Hometown`.
- The `Config.Cine` graph for the run, with branches for prank and race.
- `Progress.Origin = { Prank, Evidence, Day }`, which `Progression.Sanitize` keeps.
- Key hints, a hold-to-skip, and Replay from Options.
- New animations: on the non-bending R6 rig, in the house style, reusing existing clips where they fit (owner's
  rule).

**Releases (each playable and tested before the next):**

| Release | Builds |
|---|---|
| **3.0** | Hometown art part 1 (the house, the street kit, signs and logos) and the run's frame: the cold open, the sneak out, the parents, breakfast, the bus. One prank (The Statue) end to end. |
| **3.1** | The other four pranks, their sets, the goose and the race slips. |
| **3.2** | Polish: Biscuit, the evidence callbacks, Replay, and camera and animation passes against the house audits. |

## 10. Rules

- No gore, no injuries, nothing cruel to animals: the goose wins its fight and Biscuit is never in danger.
- No real brands, places or people. Every logo and name is original.
- Funny first: every beat has a joke or a payoff, and nothing outstays its welcome. Long text is never more than two
  lines.
- It plays once. Skip and Replay are always there.
- The Map place is never touched.

## 11. Open questions

1. **Placement: decided.** The owner, 2026-11-18: "Wickfield should be a place in it". Wickfield is its own area
   inside the NH Combat Test place (`Workspace.Hometown`), streamed in for the tutorial only. There's no teleport.
2. **Existing players:** offer it as a Replay only (proposed), or play it once on next join?
