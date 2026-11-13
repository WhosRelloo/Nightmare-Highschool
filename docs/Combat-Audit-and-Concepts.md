# Combat audit (fists first) and concepts

**Date:** 2026-11-13. The owner asked: "Completely audit and analyze the combat system, especially for fists, and
bugfix it and enhance it for a smoother gameplay. Then give me concepts on how we can enhance and expand on what we
have already." The base framework is in [[Combat-System]]. The house style for animation and feel is the
`r6-animation-cinematics` skill (Saddy's clips).

## What was read

About 250 KB of combat code in NH Combat Test, every file the fists touch:
- **Server:**
  - `ActionManager` and its actions: M1, Running M1, Aerial M1, M2, Uppercut, Block, Equip, Dodge, Evasive, Sprint.
  - Packages: `DamageLogic`, `HitBox`, `AnimMarkers`, `AirCombat`.
  - Features: `Posture`, `CombatTag`, `CombatSpeed`, `Downed`.
  - `M2.Fist` and its aerial.
- **Client:** `InputController` (M1, M2, Block, Dodge), `AnimationController`, the hit, parry, block-hit and
  posture-break effect handlers, `EmitManager`, `SkillController`.
- **Config:** `Config.Weapons`, `Config.Combat`.

## What was wrong, and what changed (2.8.0)

| # | Problem | Fix |
|---|---|---|
| 1 | **Sticky fists.** Each swing's recovery (EndLag) was read in clip time, but fists play at 1.15x. You were held about 14% past the end of every swing: 0.52 s instead of 0.45 s on the first. The same applies to the Katana (1.3x) and Claws (1.2x). | M1 converts EndLag to real seconds. |
| 2 | **Dropped clicks.** A click that arrived while a swing was still recovering was thrown away. Only holding the button chained the combo; tapping in rhythm lost hits. | The server remembers a click made in the last 0.5 s of a swing and starts the next one the moment it ends. Players only; NPCs are unchanged. Only a fresh press counts: the client re-sends M1 every 0.05 s while the button is down, so a normal 0.1 s click is 2-3 packets, and buffering those repeats turned one click into two swings (caught in the play-test). A packet more than 0.09 s after the last one is a new press. |
| 3 | **No contact weight.** A hit spawned particles and a sound, and that was all: no hit-stop and no camera kick for the attacker. | **Hit-stop:** the swing and the hit-react hold for 0.05 s on a light hit and 0.1 s on a heavy one (a combo ender, the running straight, the downslam, a downing hit). This is the house style's 3 and 6 frames. **Camera:** the attacker's and the victim's cameras jolt (scaled by the Camera Shake setting). |
| 4 | **The parry tap flashed the guard.** Tapping block to parry let go during the 0.25 s window, but the block thread kept running. It then played the guard pose and slowed you on top of whatever came next, an M1 for example. | The thread checks that it still owns the block, and letting go (or a cancel) now stops the parry pose too. Before, the old thread was the only thing that stopped it. |
| 5 | **Parry spam.** The 0.1 s block cooldown let you open a fresh 0.25 s parry window about every 0.35 s by mashing: roughly 70% of the time parrying. | A parry window that catches nothing locks the next one out for 0.5 s after it closes; you still guard at once. A parry that lands lifts the lock. Mashing now parries about a third of the time. |
| 6 | **The last hit could race the combo cooldown.** With the recovery now in real time, the end-of-combo cooldown and the end of the swing fall on the same instant. A buffered click could have started a fifth hit. | The cooldown is set before the swing ends. |
| 7 | **Katana combo order.** The four katana swings came from `GetChildren()`, which has no order. | Sorted 1-4. |
| 8 | **A Running M1 error path.** A hit after the attacker's character had gone called `HitBox:Disconnect`, which doesn't exist. | Returns instead. |

**Files:** `ActionManager`, `Combat.M1`, `Combat.M1.Running M1`, `General.Block`, `Packages.DamageLogic`,
`StateController.Misc.General.Damage Type` (client), `Config.Weapons`. Every edit is tagged `(combat audit)`. The scripts
as they were before are in `ServerStorage.NH_Backup.CombatAudit_pre_20261113`; the patched ones are mirrored in
`tools/combat-audit-280/`.

### Tested (NH Combat Test, slot 4 Testy on Fists, against the Inf Dummy, real mouse and keyboard)

| Check | Result |
|---|---|
| One click / two clicks / three clicks 0.25 s apart | 1 / 2 / 3 swings. The three clicks played back to back (gaps 0.49 and 0.50 s). |
| Holding the button 2.2 s | the full 4-hit string, then the 1 s combo cooldown, as before |
| 10 taps 0.3 s apart (through the remote) | swings 0.48, 0.36 and 0.43 s apart: each started the moment the last one's corrected recovery ended. Before, 0.40-0.52 s plus up to 0.3 s waiting for the next tap. |
| Hit-stop | on contact both the swing tracks held for 0.07 s (0.05 s plus a frame) and resumed |
| A parry tap (F, 0.1 s), then a click | the parry pose stopped on release (0.13 s later); no guard pose or Slow at 0.25 s |
| Mashing F (4 taps, 0.3 s apart) | 1st parried; 2nd and 3rd guarded straight away (no parry window); the 4th, 0.75 s after the first opened, parried again |
| Console | no script errors (only the place's existing sound-permission and archived-asset warnings) |
| Restored | `SlotCount` back to 3, `NHTestNoMenuKeys` cleared; Testy left on Fists (Testy also owns the katana) |

**Not tested:**
- **Gamepad and touch:** they go through the same remotes.
- **A second player:** whether another viewer sees the hit-stop, and how it feels against a real opponent with ping.
- **Combos against the AI tiers:** the camera kick by eye.
- **Discipline:** the tests ran at 2:41 PM After School, a hall-monitor duty segment, but Testy picked up no Fighting
  violations (checked against Testy's record afterwards). The 2.9.0 tests ran at night.

**NPCs:** Delinquents and other Fist NPCs swing about 14% faster now (fix 1 applies to everyone). The stunlock guard
(3 hits, 0.8 s, 1.2 s) still caps their pressure. The input buffer is players only.

## Found but left alone

- **Heavy (M2) damage.** Every weapon's heavy does 1.3x a light hit (Fist 3.9, against 3 for a light). The config's
  `M2Damage` (Fist 8, Katana 10) is never read. *Your call* (below).
- **Hitbox prediction.** `HitBox:Go` always places the box 0.2 s ahead along the attacker's velocity, and its
  `Prediction` flag is never checked. A sprinting attacker's box lands about 8 studs ahead; the running attack's
  verified ranges (6, 10, 14 studs) depend on that, so it stays.
- **Uppercut, Running and Aerial recovery** have the same clip-time EndLag. Running and Aerial play at 1x, so nothing
  changes for them. The Uppercut plays at 1.3x, and the AI's tier timings were tuned against it, so it's left for a
  separate pass.
- **Dead code:** the `MoveAttacker` and `ApplyImpulse` paths in `DamageLogic` are never used.
- **Fists need E first, and E is often taken.** M1, M2 and block do nothing until you raise your fists with E, and
  nothing says so. The client also gives E to any ProximityPrompt on screen, so near a student's talk or offer prompt,
  a quest prompt or the stand, E doesn't raise your fists at all. In the test, a mirror's quest prompt 7 studs away
  swallowed it. *Your call*.
- **Latency.** Your own swing starts on the server, so you see it about one ping after you click. The fix is
  client-predicted swings (concept C1).
- **A quarantined backdoor:** `ServerStorage.NHQuarantine.FemaleBody_Runtime_SUSPECTED_BACKDOOR`, isolated by an
  earlier session. It is not loaded by anything; it should be deleted once you've looked at it.

## Concepts

Each has a size: **S** is about a day, **M** a few days, **L** a week or more. They build on what exists: posture,
parry, the four-hit string, the running straight, the downslam, Z / X / C, downed, grips, races, moons, Training, the
armory, cliques, duels and the hall monitors.

### A. Feel and readability

**Built in 2.9.0 (the owner picked "Feel set 1-4"):** concepts 1 to 4, as described below, with these details:
- **Counter-hits:** a counter is a hit that lands before the target's own swing reaches its hit frame. Each swing (M1,
  the running straight, the uppercut and the Fist heavy) sets `NHWindupUntil` as it starts. A counter stuns 1.5x
  (measured 1.31 s against 0.87 s), holds the hit-stop 0.1 s, flashes the target white (skipped under Reduce
  Flashing), plays the Critical sound pitched up, and shows "COUNTER" over the attacker's combo count.
- **Directional reactions:** the four existing hit clips were measured from their keyframes and picked by side. Clips
  1 and 2 double over forward; 3 and 4 snap the head back to the left or right. From the front the hits alternate
  3, 1, 4, 2 (head, body, head, body); from behind 1 and 2; from the right 3 and 1; from the left 4 and 2. No new
  animations were needed.
- **Heavy tells:** the uppercut now plays the M2's critical tell (the Heavy flash and the Critical sound) as it winds
  up. The running straight is too quick for a tell to help.
- **Combo counter and damage numbers:** text only, in the kit's title font. The counter is a gold numeral over a
  spaced "H I T S" at the right edge (60% down, clear of the quest tracker). It appears from the 2nd hit and fades
  1.6 s after the last. Damage numbers float up over what you hit and are off by default. Both are toggles in
  Settings > Interface > Combat.

1. **Counter-hits (S).** A hit that lands while the target is winding up their own swing is a counter-hit:
   - **Effect:** +50% stun, a bigger hit-stop, a white flash ring and a distinct sound.
   - **Why:** it rewards reading, not mashing. It's the most important skill signal in fighting games.
2. **Directional hit reactions (S).** Hit reactions cycle through the set today. Pick by the side the hit came from
   (front, back, left, right) and by weight (light flinch, heavy stagger).
3. **Heavy tells (S).** Heavies and the uppercut glow briefly at wind-up, like the wolves' red tell, so defenders can
   read them. A future unblockable gets its own colour.
4. **Combo counter and damage numbers (S).** "3 HIT" in the corner while a string lands, and optional damage numbers
   in Settings. It also makes the Training dummies useful.
**Built in 2.11.0:** concept 5, which completes section A.
- **Mouse and keyboard:** middle mouse locks on to the nearest opponent in front (30 studs), and again lets go. While
  locked you face them between swings, and a small gold diamond breathes over their head. It lets go by itself when
  they drop, go down, get 40+ studs away, or you put your fists away. (`InputController.Combat.LockOn` and its `Core`;
  `Keybinds` `LockOn`.)
- **Gamepad and touch:** every pad button is already taken, so these get aim assist instead. Each swing (M1 or M2)
  turns you to the nearest opponent in front within 9 studs. Mouse players keep their own aim.
- **Not rebindable yet:** middle mouse isn't in Settings > Controls.

5. **Soft lock-on (M).** Hold a key or the gamepad's RS to face the nearest opponent between swings. Phones and pads
   need this most.

### B. The fist moveset

**Built in 2.10.0 (the owner picked "Fist moveset 6, 8, 9"):** concepts 6, 8 and 9, fists only, with these details:
- **String enders:** M2 within 0.8 s of a string hit landing replaces the plain heavy, and cancels that swing's recovery
  once its hit frame has passed. All share M2's cooldown (2.5 s). The string resets afterwards.
  - **After hit 1, the shove** (Fist M1.4): it knocks them about 20 studs back, with a short stun.
  - **After hit 2, the launcher:** the existing Uppercut, into the air combo.
  - **After hit 3, the body blow** (Fist M1.3): it plays the heavy tell. Clean, it doubles them over (1 s stun, a
    heavy hit-stop); into a guard it's +35 posture.

  "Hold back + M2" for the shove was tried first and dropped: the character turns to walk away, so the shove swung at
  nothing.
- **The clinch:** M1 while holding block (F, or L2 + R2 on a pad); 3 s cooldown.
  - **Goes through:** a guard and a parry window.
  - **Loses to an attack:** a target winding up a swing isn't caught.
  - **Caught:** a knee (Fist M2) for 4 damage and +25 posture, which breaks posture if that fills it, and they double
    over.
  - **Dodge:** a dodge's i-frames still slip it.
- **Riposte:** a landed parry gives you 0.9 s in which your next M1 is a riposte: 1.5x damage, a stagger and a heavy
  hit-stop.
- **The readout** names the move over the combo count (SHOVE, BODY BLOW, CLINCH, RIPOSTE), in gold or in crimson for
  RIPOSTE and COUNTER.
- **Stand-in clips:** existing Fist clips are used until bespoke ones are made: M1.4 for the shove, M1.3 for the body
  blow, M2 for the knee.
- **Bespoke clips (2.12.0):** the Shove, the Body Blow, the Clinch and a clinch victim, built on the game's own fist M1s
  (`tools/fist-moves/`).
  - **Seams:** each starts on the pose of the swing it cancels and ends on the fist idle, limb slides included.
    Measured in Studio, the seams join within 4 mm and 0.2 degrees.
  - **Where they live:** `ReplicatedStorage.Assets.Animations.Weapons.Fist.Moves`. The code uses a clip once its
    AnimationId is set, and the stand-in until then.

**Built in 2.11.0:** concepts 7, 10 and 11, which completes section B.
- **Delay string (7):** throw the 4th hit after a pause (0.3 s or more after hit 3 lands, before the string resets at
  1 s). If they've had their guard up 0.25 s or more, it goes straight through: full damage, the ender's knockback, and
  DELAY on the readout. A late, reactive block still parries it. (`Combat.M1`; `General.Block` records
  `BlockStartedAt`.)
- **Charged heavy (10):** hold M2 and the wind-up holds and charges, 0.4 s a step, up to three.
  - **Each step:** +15% damage and more guard damage (35, 50, 65), with a gold glow and a rising chime.
  - **The third step:** flares and breaks a guard outright.
  - **A tap:** the same instant heavy as before.
  - **Risk:** you can be counter-hit while charging.
  - **Code:** the M2 packet carries flags (1 aerial, 2 press, 4 let go), and the hold-repeats keep a charge alive if
    the let-go is lost (`Assets.M2.Fist`; client `Misc.General.Charge`).
- **Wall splat (11):** a hard horizontal knockback (40+: the 4th hit, the running straight, the shove, the heavy) that
  drives someone into a wall within its travel pins them there.
  - **The pin:** a 0.9 s stun and a head snap against the wall.
  - **Effects:** dust off the wall, a heavy thud and a camera jolt, with WALL SPLAT on the attacker's readout.
  - **Code:** `DamageLogic` `Local.WallSplat`; client `Misc.General."Wall Splat"`.

6. **String enders (M).** M2 pressed after hit 2 or 3 of the string replaces the 4th hit with a different ender:
   - after 2: a **launcher** (into the existing air combo);
   - after 3: a **body blow** (big posture damage);
   - holding back: a **shove** that opens space.

   This is fully built on the existing actions.
7. **Delay string (S).** Pausing about 0.3 s before the 4th hit turns it into a **feint-break** hook that beats a guard
   raised early. It rewards rhythm and works with the new input buffer.
8. **The clinch: grab beats block (M).** A short-range grab (fist only) that can't be blocked but loses to any attack:
   - **Effect:** a knee to the gut, +25 posture.
   - **Why:** it closes the attack, block and grab triangle. Today the only answer to someone turtling is posture
     pressure.
9. **Riposte (S).** A landed parry opens 0.4 s in which your next M1 is a riposte: +50% posture damage and a hit-stop
   flourish. Parrying becomes a turn swap, not just a pause.
10. **Charged heavy (S).** Hold M2 to charge in three steps. Each step adds posture damage and a glow, and a full charge
    breaks guard.
11. **Wall splat (M).** A heavy or combo ender that drives someone into a wall within 4 studs pins them there for 0.6 s
    (a dent and dust, no gore), and the attacker can follow up. The school's halls are full of walls and lockers.

### C. Tech

12. **Client-predicted swings (L).** Play your own swing locally the moment you click; the server confirms or rolls
    back. This removes the one-ping delay on every action, and it's the single biggest smoothness gain left.
13. **Lag-compensated hits (M).** The server checks a hit against where the target was when the attacker saw them
    (about 100 ms of position history), not where they are now. It replaces the fixed 0.2 s attacker prediction.
14. **Combat event log (S).** A Studio-only trace of each exchange (inputs, swings, hits, blocks, parries, timings) so
    tuning is measured, not guessed.

### D. Growth (fists are everyone's first class now)

15. **Fighting styles from Training (L).** Training already rates sets. Unlock a fist style there, swapped at the class
    locker:
    - **Boxer:** faster strings, slipping dodges.
    - **Street Brawler:** heavier enders, shoves.
    - **Grappler:** the clinch, throws.

    Each style changes the 4th hit and one skill.
16. **Hand gear at the armory (M):** wraps (+Grit), weighted gloves (+posture damage) and brass knuckles. The knuckles
    are contraband: they tie into the hall monitors and the confiscation concept.
17. **Race-flavoured fists (M).** Every race gets a small identity on the 4th hit, a VFX tint and one little effect:
    - Vampire: a sip of health on the ender.
    - Priest: a light burst that cuts a beast's posture.

    The Crimson and Blue moons already boost damage. They could also tint these enders.
18. **A Heat meter (M).** Landing hits and parries fills Heat. Spend a full bar on an EX version of Z, X or C (more
    damage, armour on startup). It gives fights a second resource besides posture, and skilled play earns it.

### E. Fights in the world

19. **Crowds at fights (M).** Students gather in a ring around a fight and cheer, which draws the hall monitors faster.
    This is concept 5 in [[Gameplay-and-NPC-Concepts]].
20. **The sparring room (S).** A gym mat where hits do no real damage and there's no posture break or monitor report.
    It has a dummy that reads out DPS, the combo count and parry timing. It's the place to learn the new parry and
    counter-hit rules.
21. **Study-group tag assists (M).** A study-group member nearby can be called in for one assist strike with a
    cooldown, which gives groups a reason to fight together.
22. **Beast stagger (S).** Fists break beast posture faster than blades: a "stagger" after enough hits opens a window.
    This gives fists a role against the night once you own a katana.

## Where I'd start

| Order | Concepts | Why |
|---|---|---|
| 1 | 1, 2, 3, 4 | Read the fight better; all small. **Built in 2.9.0** (5 in 2.11.0: all of A is done). |
| 2 | 6, 9, 8 | The fist moveset gets depth with what exists. **Built in 2.10.0** (7, 10, 11 in 2.11.0: all of B is done). |
| 3 | 12 | The biggest smoothness gain left, but large. |
| 4 | 15, 16 | Fists become a path, not a starter. |

## Your calls

- **Heavy damage:** keep every heavy at 1.3x a light, or use the config's `M2Damage` (Fist 8, Katana 10)?
- **Raising fists:** keep E (which any nearby prompt takes over), have the first click raise them, or move Equip to its
  own key? A click in class would then raise them, which a monitor may treat differently.
- **Parry lockout:** 0.5 s after a missed parry. Tighter or looser?
- **Hit-stop:** always on, or with its own setting? The camera kick already follows the Camera Shake setting; the
  pause itself has no setting.
