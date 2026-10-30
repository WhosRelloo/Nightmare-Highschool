# UI Audit: NH Combat Test (2026-10-30)

**Scope:** every screen a player sees:
- the loading screen and main menu
- the slot picker
- the creator tabs: Look, Name & Clan, Spin Shop
- the in-school HUD: top bar, compass, clock, quest tracker, health, EXP strip, hotbar
- every panel: Factions (P), Journal (J), Settings (M), Wardrobe (K), Students (Tab), Student Record (L)

Checked for legibility, contrast, positioning, layering and scaling.

**How:**
- A client audit script (`ui_audit.luau`) walks every visible element and flags:
  - **small text**
  - **clipped** text
  - **contrast** under 3:1
  - anything **off screen**
  - top-level panels from different GUIs that **overlap**
- Screenshots of every screen, in a Studio playtest window of 1287×600 (UI kit scale 0.56), by day and by night.

## The rule we audited against
The UI kit scales everything by `min(width / 1920, height / 1080)`. On common laptops that is:

| Screen | Kit scale | 17px design text renders at |
|---|---|---|
| 1920×1080 | 1.00 | 17px |
| 1366×768 | 0.71 | 12px |
| 1280×720 | 0.67 | 11px |

**Bar:**
- Text must be at least **12px on a 720p screen**, so **18px design size** for kit-scaled UI.
- Text contrast should be at least **3:1**, and **4.5:1** for body notes.

## Findings and what happened

### Fixed (files owned by this session)
| Screen | Problem | Fix |
|---|---|---|
| EXP strip | Drew **on top of** the Factions, Journal and Settings panels (its layer sat above them) | Moved to its own layer, `NHExpStrip`, at DisplayOrder 3 (the HUD's layer), so panels cover it |
| EXP strip | Level numeral 13px (9px at 720p); "+N" gain 14px | Numeral 17px; gain 18px with a soft outline |
| Student Record (L) | Rows at the kit's small size (about 9px at 720p); Grit's text ran up to its **+** button; bonus values faint | Every row at least 16px, rows 40px tall so text wraps, bonus values at full text colour |
| Compass | Backing 70% opaque reads navy over a daytime sky; SE/SW/NE/NW letters 12px and faint | Backing 88% opaque; intercardinal letters 15px and brighter |
| Top bar | Washed blue in daylight | Plate more opaque (0.15); idle fade lighter (0.5 instead of 0.6) |
| Students list (Tab) | "Lv N · rank" line 12px; a scrollbar appeared with one student (the plate height ignored the list padding) | Sub line 14px and brighter, headers and counts +1px, rows 48px, plate height fixed |
| Name & Clan | Notes, odds and status 17px at **2.9:1 contrast**; clan tag 16px (rendered "COMMONCLAN" with the space lost); pity line 16px | Notes and status 18px at a lighter colour; tag 19px; pity 18px |
| Spin Shop | Group text and "You have" 16px; POPULAR / BEST VALUE 14px; "(not on sale yet)" 17px with broken letter spacing | 18px / 16px / 19px; group text gets a two-line row |
| Main menu | Key hint, version line, "Drag to turn your student" and SLOT I/II/III labels at **2.9:1**; version 16px | All lifted to a readable colour; version 18px |
| Loading screen | The ADMITTED stamp's small line was 9px | Taller line (about 12px) |

### Sent to the UI kit session (files it owns)
1. **The biggest win, kit scaling:** the linear curve makes all 15–17px kit text 10–11px on laptops.
   - Option 1: a gentler desktop curve, such as `s^0.6`. A 740px panel at 0.70 is 520px, which still fits a 542px-tall window.
   - Option 2: a text floor.
2. **Small text:**
   - Wardrobe: tabs, sections and notes (17)
   - Settings rows
   - Journal: quest details (15) and sections (17)
   - Quest tracker footer (15)
   - Clock: class line (14) and period (17)
   - Hotbar: item names (11) and hotkeys (13)
   - Spin reel sub-line (15)
   - Player-list rows
   - Factions reputation captions (12–13)
3. **Edges:** the clock and quest-tracker shadows run a few pixels past the right edge of the screen.
4. **Consistency:**
   - Notifications have no scaling.
   - The Factions panel isn't kit-scaled, so its **Factions [P]** button is twice the size of the Journal, Settings and Wardrobe buttons under it.
   - That left-edge button stack repeats the top bar. Suggestion: fold it into the top bar on keyboard devices and keep it for touch.
5. **Phones:** the touch minimum scale (0.92) makes 740px panels overflow a 390px-tall landscape phone.
6. **Input:** on Name & Clan the name box keeps keyboard focus, so Return on a creator button re-submits the name. Left for the gamepad pass.

### Follow-up done by the UI kit session (same day)
- **Scaling:** below 1× the kit now scales by `raw^0.6`, so 720p goes from 0.67 to **0.78** and 768p from 0.71 to **0.82**.
  - `Kit.FitToScreen` keeps tall panels such as the Wardrobe and Settings on screen (and on phones) by shrinking the panel, not the text.
- **Text:** the theme's sizes went up (small 15 to 18, body 18 to 20, tiny 13 to 15). This also lifts the Quest Journal and Quest Tracker.
- **Hard-coded sizes:** raised in the Wardrobe, Settings, HUD, clock, dialogue and Factions.
- **Clock:** moved in to x = −30. The **Quest Tracker** now matches at −30 (set from the quest side), so both shadows stay on screen. The tracker move hasn't been re-checked in a playtest; it's based on measuring the old 4px overshoot.
- **Scaling consistency:** Notifications and the Factions panel scale with the rest, so the Factions button now matches its neighbours.
- **Left-edge buttons:** on keyboard devices the Settings button is hidden, because the top bar's Menu covers it. Journal, Factions and Wardrobe stay until the top bar gets buttons for them.

### Bigger kit text vs. fixed-height rows (Quest Journal and Tracker)
- **Quest Tracker:**
  - **Before:** the footer overflowed its 16px row by about 1px at 0.70 scale and sat on the card's bottom border. The 52px objective box fit only two lines of 20px text.
  - **Fix:** card 380×140, objective 64, footer and timer 20.
  - **Verified in Play:** the objective ends at y 156 and the footer starts at 157. The right edges line up with the clock.
- **Quest Journal:**
  - Text rows size themselves, so nothing clipped on the Quests or Case Files tabs.
  - Deduction buttons are 230px wide, and the longest answer is 19 characters, so they fit.
  - The evidence board itself wasn't reached, because this student has no case yet.

### Checked and fine
- No two HUD pieces overlap each other.
- Nothing important is off screen at 1287×600. The "off-screen" Name & Clan notes were inside a scrolling list.
- Panels open with their keys (P, J, M, Tab, L) and cover the HUD.
- The Factions panel's own text is readable because it isn't scaled down (the size mismatch is a separate problem).

## Verified (Studio playtest, after the fixes)
- **Main menu:** the hint, version line and SLOT I/II/III labels are now light (#b9b2aa) at 18px. Earlier they were 2.9:1.
- **Name & Clan:**
  - The tag reads "COMMON CLAN · 1 in 15" with its space, at 19px.
  - Notes are 18px at the lighter colour. That includes "Enrolled. Renames left…", which got a second fix after the re-check.
- **EXP strip:** it lives in `NHExpStrip` (DisplayOrder 3) and shows level IV. With the Factions panel open, nothing crosses the panel any more.
- **Compass:** the centre stays dark ink over a daytime sky.
- **Students list:** with one student the list height matches its content (66 / 66), so there's no scrollbar.
- **Student Record:** Grit's effect wraps onto two lines clear of its **+** button, and bonus values are at full text colour.
- **Still small in a short window:** Record and other kit-scaled text are still small in a 600px-tall window. That's the kit scaling item above, which the UI kit session has taken on.
- **Top bar:** it still picks up some sky colour while it's faded idle. That's by design so it stays out of the way. It goes solid on hover and use.

## Not tested
- **Real phones and tablets.** The phone overflow comes from the maths, not a device. Studio's device emulator wasn't used.
- **Gamepad navigation** across the menu and panels.
- **Screens not reached in this pass:** dialogue boxes, class activities, the downed screen, the duel ring HUD and notifications with many messages stacked.

## Tooling
- `ui_audit.luau`: the audit script. Run it on the client during Play. It prints the issues per ScreenGui.
- It lives in the session folder with the other Studio patches, not in this repo, because game source isn't pushed.
