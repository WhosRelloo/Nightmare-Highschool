# Inventory: quality-of-life concepts

**Date:** 2026-11-12. These are concepts for the owner to pick from.

**Built:** batch 1 in 1.91.0, which is concepts 1 (empty pins shown), 5 (cooldown shades), 9 (the buff chip) and 30 (no
silent refusals: the snack messages; the kit's messages are still to do). Batch 2 in 1.92.0 is concepts 18 to 22
(the stand's tabs, Restock my pins, the quantity picker, dimming, and lunch from the timetable with its countdown).
Batch 3 in 1.93.0 is concepts 11, 13 and 15 (sort and filter, favourites, drop how many with Undo); sorting by
"newest" was left out because nothing records when you got an item. Batch 4 in 1.96.0 is concepts 4 and 7: the snack
wheel (held on G or D-pad Right, since Q and LB were taken) with the baked, animated Bell Wheel look, and Best food in
its middle. Everything else on this page is not built yet.

**The rule behind all of them:** less clicking, fewer surprises. A player should always know what they're carrying,
what each thing will do, and why something didn't work.

## What the inventory is today

| Part | What it does |
|---|---|
| **Locker** (`` ` `` key) | Tabs: All, Gear, Snacks, Boards and Kit. A 3D item grid with tooltips. Use, Pin/Unpin and Drop (click twice). The pouch shows your 4 pins. |
| **Hotbar** (`Gui.KitHud`) | Pinned snacks are Backpack Tools. Equip one and click to use it. |
| **Snacks** (`Config.Items`) | About 40 items at the stand, 5 daily specials, 14 lunch meals (only during lunch) and 5 beast trophies. Stacks of 20; 4 pins. |
| **Rules** | Food heals over time and shares a 12 s "full" cooldown. Drinks give one buff at a time, and a new one replaces the old. |
| **Everyday kit** (`Config.Kit`) | 12 carried items with their own counters, refills and HUD. |
| **The stand** | A grid of every item with ¥ and x5 buttons. |

**Save:** `PlayerData.Inventory = { Items, Pinned, Daily, Boards, Kit }`, written through ProfileService.

## What the audit found and fixed (1.90.1)

Every inventory script was read and the fixes were play-tested on slot 4. All 17 are in the CHANGELOG; the ones a player
would notice most:
- **Empty pins** blocked the pouch: "Unpin one first", with nothing to unpin.
- **Clicks** inside the rate limit did nothing.
- **The Locker:**
  - it stayed open after death with a frozen preview;
  - a quick double press reopened it;
  - its Pouch fell off phone screens;
  - every action threw a gamepad cursor back to the top-left.
- **Gamepad B** at the stand toggled the Locker instead of closing the stand.
- **The hall pass** was spent on fight chases it can't stop.
- **Flask coffee** wiped a paid snack buff.

**Still open:**
- **Lunch meals:** the stand menu never lists them, so they can't be bought. The concession session owns this.
- **Stand menu rebuilds:** it rebuilds about 40 3D cells on every change.

## The concepts

Each concept has a size: **S** is about a day, **M** a few days, **L** a week or more.

### A. Hotbar and quick use

1. **Empty pins show what they're waiting for (S).**
   - **Since 1.90.1:** an empty pin keeps its slot, gives way to new pins, and clears when clicked.
   - **But today:** the slot looks blank.
   - **The change:** show the snack greyed out with a "0", plus "Restock at the stand" on hover, on the pouch and the
     hotbar.
   - **Why:** your layout never shifts under you, and you can see what to rebuy.
2. **Drag to reorder (S).** Drag pouch slots in the Locker, or drag on the hotbar itself. The order is what keys 1-4
   use.
3. **More pins as you grow (S).**
   - **Unlock:** a 5th pin at level 10 and a 6th at level 20, or a 5th from a "Lunchbox" bought at the stand.
   - **Why:** it gives a reason to level that isn't damage.
4. **Snack wheel (M).**
   - **What:** hold `Q` (or `LB` on a gamepad) to open a radial of everything you carry that you can use. Release on
     one to eat or drink it.
   - **What it shows:** each item's count and its cooldown ring.
   - **Why:** you can use any snack, not just the 4 pinned ones, without opening the Locker mid-fight.
5. **Cooldown and "why not" on the slot (S).**
   - **The "full" timer:** a radial fill shows the 12 s on every food slot.
   - **Blocked slots:** a slot you can't use shows why on the slot itself (down, full, out of combat only, lunch
     closed). Today the reason is a toast.
6. **Hotbar loadouts (M).**
   - **What:** three saved pin sets, Day, Fight and Night. Switch from the Locker or by holding the hotbar's first key.
   - **Example:** Night can carry the bento, the hand warmer and Black Cat Cola; Day carries coffee and onigiri.

### B. Using things

7. **Smart eat (S).**
   - **What:** a "Best food" action, on the wheel's centre or a key. It picks the cheapest food in your bag that covers
     your missing health and doesn't waste much.
   - **Why:** it saves the bento when an onigiri will do.
8. **"Replace buff?" check (S).**
   - **When:** drinking while another buff has more than 60 s left.
   - **What:** the slot asks once: "Replace Canned Coffee (2:10 left)?" Tap again within 2 s to confirm.
   - **Why:** today you lose the old buff silently.
9. **Buff chip on the HUD (S).**
   - **What:** a small chip shows the active snack buff's icon, its effect and a countdown. It pulses at 15 s.
   - **Where:** next to the kit chips, which already use this style.
10. **Eat while walking (S).**
    - **What:** using already takes 1.1 s. Allow it at half walk speed instead of standing still.
    - **Interruptions:** cancel it if you're hit, as bandaging already does.

### C. The Locker screen

11. **Sort and filter (S).**
    - **Sort by:** kind (heal, buff, trophy), rarity, newest, most owned, or A-Z.
    - **Filter chips:** Heals, Buffs, Lunch, Specials, Trophies.
    - **Remembered:** the choice is kept per player (a local setting, not saved data).
12. **Search (S).** A small search box, which helps once the stand passes 40 items.
13. **Favourites (S).**
    - **What:** a star on any item puts it first in the grid and at the stand.
    - **Saved:** in `Inventory.Fav`, at most 12.
14. **"New" badges (S).** Items you haven't looked at yet get a small dot that clears on hover. It also shows on the
    tab.
15. **Drop with undo, not double-click (S).**
    - **What:** Drop happens at once and a 5 s "Undo" bar appears. Undo restores the items.
    - **Amounts:** dropping more than one asks how many (1, 5, All).
16. **Inspect (S).** Double-click an item to open a big turnable 3D view with its lore line. Trophies show where and
    when you won them (needs a small save field).
17. **Effect compare (S).** Hovering a buff shows what changes on your sheet, for example "Class EXP 12% to 15%". This
    uses the numbers the Report Card already has.

### D. The stand

18. **Category tabs at the stand (S).**
    - **Tabs:** Hot food, Snacks, Sweets, Drinks, Lunch (only while open), Today.
    - **Why:** 40+ items in one grid is a lot to scroll.
19. **Restock pinned (S).** One button, "Restock my pins", buys up to 5 of each pinned item. It shows the total first:
    "Restock: ¥215".
20. **Quantity picker (S).** Replace the fixed x5 button with − / + and a Max you can afford. Every button keeps the
    cost on it.
21. **"Can afford" dimming (S).** Items you can't afford are dimmed, and items you're full on (20) show "Full".
22. **Lunch countdown (S).** The menu shows "Lunch opens in 12 min" or "Lunch closes in 4 min", plus a lunch line
    on the menu board.
23. **The vendor talks (S).** Mrs. Okada greets regulars, comments on your order and mentions today's special. This
    is built on the line matrix's Generic voice, so it comes almost free once that lands.

### E. Carrying, storing and sharing

24. **Give to a friend (M).**
    - **What:** target a nearby player (within 8 studs) and "Give" a snack.
    - **Limits:** it needs their accept, and caps at 10 a day per giver so it can't be farmed.
    - **Study groups:** members can share with no accept step.
    - **Never giveable:** trophies and kit items.
25. **Feed a student (M).**
    - **What:** offer a snack to an NPC. It ties into the line matrix: each clique has tastes in food too, so the
      Athletes love the yakisoba bun and the Choir likes moon cake.
    - **Effect:** a liked food gives a small standing nudge, at most once a day per clique.
    - **Why:** it's the Bully gift loop, in our world.
26. **Dorm stash (M).**
    - **What:** a trunk in your dorm room holds overflow beyond 20 a stack, plus trophies you want to display.
    - **Why:** it makes the room matter.
    - **Bonus:** displayed trophies show on a shelf model.
27. **Confiscation (M).** If the hall monitor catches you with contraband during class (prank kits, Red Lantern), it
    takes one. Get it back at the Office after school for ¥20.
    - **Why:** it's Bully's authority loop, and the hall pass gets a second job.
    - **Owner's call:** this is pressure, not QOL. Leave it out if it's unwanted.

### F. Collection and feedback

28. **Taste book (M).** A page in the Locker of every snack, lunch and special, with a tick once you've eaten each.
    - **Rewards:** at 10, 25 and all, a title and a small permanent buff (+1 max health).
    - **Why:** it pushes players to try the 40 items instead of buying onigiri forever.
29. **Trophy case (S).** The Trophy tab shows all five beasts' trophies as silhouettes until you have them, with the
    beast's name and how rare the drop is.
30. **Clear messages everywhere (S).**
    - **Every refusal says why**, in the place you clicked: too far from the stand, full, not today, lunch closed,
      down, a trophy.
    - **Today:** the stand shows the reason, but the Locker and the hotbar often show nothing.

### G. Controls

31. **Gamepad (M).**
    - **Locker:** move through the grid with the D-pad. A uses, X pins, Y drops, and LB/RB change tabs.
    - **In play:** the D-pad's left and right cycle the hotbar, and LB holds the snack wheel.
32. **Touch (M).**
    - **Locker:** bigger slots (at least 64 px), and a long press for the item card instead of hover tooltips.
    - **Hotbar:** the slots get a use button.
33. **Keybinds in Settings (S).** Make the Locker key (`` ` ``, which is hard to reach on many layouts), the wheel and
    smart eat rebindable in the existing Settings.

### H. The kit and snacks together

34. **One hotbar (M).**
    - **What:** kit items (lantern, umbrella, thermos and so on) and snacks pin to the same hotbar with one set of
      rules, so a player can pin the lantern next to the bento.
    - **Today:** the kit has its own chips and counters, so there are two systems to learn.
35. **Refills as "ammo" (S).** Kit refills (lamp oil, bandages, charcoal) show as counts on the kit item's slot. They
    can be bought from the item's card ("Refill ¥15") anywhere in sight of the counter that sells them.

## Things to avoid

- **No spoilage or hunger meters.** They punish players for being offline, and that's the opposite of QOL.
- **No weight limits on snacks.** The stack cap of 20 and the pin cap already shape choices.
- **Nothing pay-to-win.** No Robux-only buffs and no Robux pin slots. Robux can buy cosmetic lunchboxes at most.
- **Nothing that hides the "why".** Every auto-action (smart eat, restock) shows what it will do before it spends Yen.

## Where I'd start

| Order | Concepts | Why |
|---|---|---|
| 1 | 1, 5, 9, 30 | Fixes how it feels today. All small. |
| 2 | 18, 19, 20, 21, 22 | The stand just tripled in size. |
| 3 | 11, 13, 15 | The Locker keeps up with 40+ items. |
| 4 | 4, 7 | The wheel and smart eat, the big feel upgrade. |
| 5 | 28, 25 | The taste book and feeding students, which tie into the line matrix. |

## Your calls

- **Empty pins:** show them greyed with "0" (my pick), or leave them blank as now?
- **More pins:** by level, by a stand item, or never?
- **Confiscation:** in or out?
- **Feeding students:** should it move standing, or only produce a line?
- **The Locker key:** keep `` ` ``, or move it (`B` for bag, `Tab`)?
