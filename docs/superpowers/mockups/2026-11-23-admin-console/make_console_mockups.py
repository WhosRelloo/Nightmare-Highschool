"""Mockups for the Headmaster's Console (admin panel rebuild, 2026-11-23).
usage: python make_console_mockups.py <out dir>
Draws the console at 1600x900 design px over a dim scene: iron frame, crimson/brass trim, velvet cards, 20 px+ text."""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
W, H = 1600, 900
FONT = "C:/Windows/Fonts/georgia.ttf"; BOLD = "C:/Windows/Fonts/georgiab.ttf"; ITAL = "C:/Windows/Fonts/georgiai.ttf"
f = lambda s, b=False, i=False: ImageFont.truetype(BOLD if b else ITAL if i else FONT, s)

IRON = (34, 30, 36); IRON2 = (46, 41, 48); VELVET = (58, 22, 30); VELVET2 = (74, 28, 38)
BRASS = (196, 156, 84); BRASS_D = (126, 98, 52); BONE = (236, 226, 206); DIM = (186, 172, 152)
CRIMSON = (196, 40, 52); GREEN = (110, 170, 110); INK = (18, 14, 18)


def bg():
    im = Image.new("RGB", (W, H), (20, 22, 34))
    d = ImageDraw.Draw(im)
    for y in range(H):  # a dim night scene behind the console
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(24 + 20 * t), int(26 + 14 * t), int(44 + 10 * t)))
    for x, h in [(80, 300), (260, 220), (1320, 260), (1500, 340)]:
        d.rectangle([x, H - h, x + 120, H], fill=(16, 16, 24))
    return im.filter(ImageFilter.GaussianBlur(6))


def frame(d, x0, y0, x1, y1, fill=IRON, edge=BRASS_D, r=10, w=3):
    d.rounded_rectangle([x0, y0, x1, y1], r, fill=fill, outline=edge, width=w)


def rivets(d, x0, y0, x1, y1):
    for x, y in [(x0 + 12, y0 + 12), (x1 - 12, y0 + 12), (x0 + 12, y1 - 12), (x1 - 12, y1 - 12)]:
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=BRASS, outline=BRASS_D)


def text(d, xy, s, size=20, col=BONE, b=False, i=False, anchor="la"):
    d.text(xy, s, font=f(size, b, i), fill=col, anchor=anchor)


def chip(d, x, y, s, on=False, danger=False):
    w = d.textlength(s, font=f(20)) + 24
    fill = CRIMSON if (on and danger) else (BRASS if on else IRON2)
    col = INK if on and not danger else BONE
    d.rounded_rectangle([x, y, x + w, y + 32], 16, fill=fill, outline=BRASS_D if not on else fill, width=2)
    text(d, (x + w / 2, y + 16), s, 20, col, anchor="mm")
    return x + w + 8


def icon(d, cx, cy, kind, col=BRASS):
    r = 18
    d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=IRON, outline=col, width=2)
    if kind == "shield": d.polygon([(cx - 12, cy - 12), (cx + 12, cy - 12), (cx + 12, cy + 2), (cx, cy + 14), (cx - 12, cy + 2)], outline=col, width=3)
    elif kind == "gavel": d.rectangle([cx - 12, cy - 8, cx + 4, cy - 2], fill=col); d.line([(cx - 2, cy - 2), (cx + 10, cy + 12)], fill=col, width=4)
    elif kind == "mute": d.polygon([(cx - 12, cy - 5), (cx - 4, cy - 5), (cx + 4, cy - 12), (cx + 4, cy + 12), (cx - 4, cy + 5), (cx - 12, cy + 5)], fill=col); d.line([(cx + 8, cy - 8), (cx + 16, cy + 8)], fill=CRIMSON, width=3)
    elif kind == "door": d.rectangle([cx - 9, cy - 13, cx + 9, cy + 13], outline=col, width=3); d.ellipse([cx + 3, cy - 1, cx + 6, cy + 2], fill=col)
    elif kind == "note": d.rectangle([cx - 10, cy - 13, cx + 10, cy + 13], outline=col, width=3); [d.line([(cx - 6, cy - 6 + k * 6), (cx + 6, cy - 6 + k * 6)], fill=col, width=2) for k in range(3)]
    elif kind == "eye": d.ellipse([cx - 14, cy - 8, cx + 14, cy + 8], outline=col, width=3); d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=col)
    elif kind == "moon": d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=col); d.ellipse([cx - 5, cy - 16, cx + 19, cy + 8], fill=IRON)
    elif kind == "sun": d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=col); [d.line([(cx, cy), (cx + 16 * dx, cy + 16 * dy)], fill=col, width=2) for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (.7, .7), (-.7, .7), (.7, -.7), (-.7, -.7)]]
    elif kind == "leaf": d.ellipse([cx - 12, cy - 8, cx + 12, cy + 8], outline=col, width=3); d.line([(cx - 12, cy + 8), (cx + 12, cy - 8)], fill=col, width=2)
    elif kind == "cloud": d.ellipse([cx - 14, cy - 4, cx + 2, cy + 10], fill=col); d.ellipse([cx - 4, cy - 10, cx + 14, cy + 10], fill=col)
    elif kind == "pin": d.ellipse([cx - 8, cy - 14, cx + 8, cy + 2], outline=col, width=3); d.line([(cx, cy + 2), (cx, cy + 14)], fill=col, width=3)
    elif kind == "flag": d.line([(cx - 10, cy - 14), (cx - 10, cy + 14)], fill=col, width=3); d.polygon([(cx - 10, cy - 14), (cx + 12, cy - 8), (cx - 10, cy - 2)], fill=col)
    else: d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=col)


def card(d, x, y, w, h, kind, title, help_, chips=(), danger=False, hot=False):
    frame(d, x, y, x + w, y + h, fill=VELVET2 if hot else VELVET, edge=BRASS if hot else BRASS_D, r=10, w=2)
    icon(d, x + 38, y + 38, kind, CRIMSON if danger else BRASS)
    text(d, (x + 76, y + 18), title, 22, BONE, b=True)
    hp = help_
    lim = w - 96 - (48 if danger else 0)
    while d.textlength(hp, font=f(20)) > lim and len(hp) > 4: hp = hp[:-2]
    if hp != help_: hp = hp[:-1] + "…"
    text(d, (x + 76, y + 48), hp, 20, DIM)
    cx = x + 18
    for k, (s, on) in enumerate(chips):
        cx = chip(d, cx, y + h - 46, s, on, danger)
    if danger:
        d.arc([x + w - 54, y + 14, x + w - 18, y + 50], -90, 160, fill=CRIMSON, width=4)
        text(d, (x + w - 64, y + 32), "hold", 20, CRIMSON, i=True, anchor="rm")


def topbar(d, side, tiles):
    frame(d, 40, 30, W - 40, 110, fill=IRON, edge=BRASS_D)
    rivets(d, 40, 30, W - 40, 110)
    d.polygon([(80, 48), (112, 48), (112, 80), (96, 94), (80, 80)], fill=CRIMSON, outline=BRASS)
    text(d, (96, 70), "N", 22, BONE, b=True, anchor="mm")
    text(d, (130, 52), "HEADMASTER'S CONSOLE", 21, BRASS, b=True)
    text(d, (130, 80), "staff only", 20, DIM, i=True)
    x = 476
    for s in ("MODERATE", "TEST"):
        on = s == side
        w = d.textlength(s, font=f(22, True)) + 36
        d.rounded_rectangle([x, 50, x + w, 92], 8, fill=BRASS if on else IRON2, outline=BRASS_D, width=2)
        text(d, (x + w / 2, 71), s, 22, INK if on else DIM, b=True, anchor="mm")
        x += w + 8
    x += 20
    for lab, val, col in tiles:
        w = max(d.textlength(val, font=f(22, True)), d.textlength(lab, font=f(20))) + 28
        if x + w > W - 344: break
        d.rounded_rectangle([x, 44, x + w, 98], 8, fill=IRON2, outline=BRASS_D, width=1)
        text(d, (x + 14, 50), lab, 20, DIM)
        text(d, (x + 14, 72), val, 22, col, b=True)
        x += w + 8
    d.rounded_rectangle([W - 330, 52, W - 60, 90], 18, fill=INK, outline=BRASS_D, width=2)
    text(d, (W - 312, 71), "Ctrl+K  Find any action…", 20, DIM, anchor="lm")


def rail(d, rows, sel):
    frame(d, 40, 126, 360, H - 30)
    d.rounded_rectangle([56, 142, 344, 182], 18, fill=INK, outline=BRASS_D, width=2)
    text(d, (76, 162), "Search students or UserId", 20, DIM, anchor="lm")
    text(d, (60, 196), "RECENT", 20, BRASS_D, b=True)
    y = 226
    for k, (name, sub, flags) in enumerate(rows):
        on = k == sel
        d.rounded_rectangle([54, y, 346, y + 70], 8, fill=VELVET2 if on else IRON2, outline=BRASS if on else IRON2, width=2)
        d.ellipse([64, y + 13, 108, y + 57], fill=(120, 96, 90), outline=BRASS_D, width=2)
        text(d, (118, y + 40), sub, 20, DIM)
        fx = 340
        if len(flags) > 1: flags = [flags[-1], (f"+{len(flags) - 1}", DIM)]
        fw = sum(d.textlength(fl, font=f(20)) + 16 for fl, _ in flags)
        nm = name
        while d.textlength(nm, font=f(22, True)) > 340 - fw - 124 and len(nm) > 3: nm = nm[:-2]
        if nm != name: nm = nm[:-1] + "…"
        text(d, (118, y + 10), nm, 22, BONE, b=True)
        for fl, col in flags:
            w = d.textlength(fl, font=f(20)) + 12
            fx -= w
            d.rounded_rectangle([fx, y + 6, fx + w, y + 30], 6, fill=col)
            text(d, (fx + w / 2, y + 18), fl, 20, INK, anchor="mm")
            fx -= 4
        y += 78
        if k == 1:
            text(d, (60, y + 4), "IN THIS SERVER", 20, BRASS_D, b=True)
            y += 32


def tabs(d, names, on, x0=376, x1=1150):
    x = x0
    for n in names:
        w = d.textlength(n, font=f(20, True)) + 24
        sel = n == on
        d.rounded_rectangle([x, 126, x + w, 166], 8, fill=BRASS if sel else IRON2, outline=BRASS_D, width=2)
        text(d, (x + w / 2, 146), n, 20, INK if sel else DIM, b=True, anchor="mm")
        x += w + 5


def context(d, title, lines):
    frame(d, 1166, 126, W - 40, H - 30)
    text(d, (1186, 146), title, 22, BRASS, b=True)
    y = 186
    for kind, a, b in lines:
        if kind == "h":
            text(d, (1186, y), a, 20, BRASS_D, b=True); y += 34
        else:
            d.ellipse([1188, y + 8, 1198, y + 18], fill=CRIMSON if kind == "bad" else BRASS)
            text(d, (1210, y), a, 20, BONE, b=True)
            text(d, (1210, y + 26), b, 20, DIM); y += 62


def feed(d, lines):
    frame(d, 376, H - 150, 1150, H - 30, fill=IRON2)
    text(d, (392, H - 142), "RESULTS", 20, BRASS_D, b=True)
    SYM = ImageFont.truetype("C:/Windows/Fonts/seguisym.ttf", 20)
    for k, (ok, s) in enumerate(lines):
        yy = H - 114 + k * 26
        d.text((392, yy), "✓" if ok else "✕", font=SYM, fill=GREEN if ok else CRIMSON)
        text(d, (416, yy), s, 20, GREEN if ok else CRIMSON)


def save(im, name):
    im.save(os.path.join(OUT, name)); print("wrote", name)


ROWS = [("Rello", "Human I · Lv 6 · 0 ms", [("OWNER", BRASS)]),
        ("NightRaven_04", "Vampire II · Lv 14 · 82 ms", [("REPORTED", CRIMSON), ("NOTE", BRASS)]),
        ("ash_tidewell", "Werewolf I · Lv 9 · 120 ms", [("WANTED", CRIMSON)]),
        ("Pip_Larkin22", "Ghoul III · Lv 21 · 64 ms", [("MUTED", DIM)]),
        ("moonlit_mira", "Wraith I · Lv 3 · 45 ms", [("NEW", GREEN)]),
        ("BrunoV", "Human II · Lv 11 · 90 ms", [("IN MENU", DIM)])]
TILES_M = [("players", "14 / 30", BONE), ("server", "60 fps", GREEN), ("clock", "12:30 After School", BONE), ("on duty", "3 staff", BONE), ("lock", "open", GREEN)]

# 1. Moderate: Student
im = bg(); d = ImageDraw.Draw(im)
topbar(d, "MODERATE", TILES_M); rail(d, ROWS, 1)
tabs(d, ["Inbox 2", "Student", "Server", "Log"], "Student")
text(d, (378, 182), "NightRaven_04  ·  UserId 51203344  ·  Vampire II", 22, BONE, b=True)
cw, ch = 380, 168
card(d, 376, 220, cw, ch, "flag", "Warn", "Sends a warning and records it", [("Spam", True), ("Toxic", False), ("Exploit", False), ("Other…", False)])
card(d, 770, 220, cw, ch, "mute", "Mute", "Blocks chat on every channel", [("10m", False), ("1h", True), ("1d", False), ("Unmute", False)])
card(d, 376, 400, cw, ch, "door", "Kick", "Removes them from this server", [("Reason…", False)], danger=True)
card(d, 770, 400, cw, ch, "gavel", "Ban", "Every server; Perm is owner-only", [("1d", False), ("7d", True), ("30d", False), ("Perm", False)], danger=True)
card(d, 376, 576, cw, ch - 30, "eye", "Spectate", "Watch them without being seen", [])
card(d, 770, 576, cw, ch - 30, "note", "Note", "A saved note other staff will see", [("Write…", False)], hot=True)
feed(d, [(True, "Warned NightRaven_04: Spam (saved to history)"), (True, "Muted NightRaven_04 for 1h"), (False, "Ban refused: Perm is owner-only")])
context(d, "HISTORY  ·  saved", [("h", "THIS WEEK", ""), ("bad", "Report · from moonlit_mira", "Spam in Commons chat · 2 min ago"),
        ("ok", "Muted 1h · by Rello", "Spam · today 12:31"), ("ok", "Note · by Ezra_Staff", "Watch for alt accounts · Mon"),
        ("h", "EARLIER", ""), ("bad", "Warned · by Rello", "Toxic · 11 Nov"), ("ok", "Kicked · by Vale_Staff", "AFK in the lesson · 2 Nov")])
save(im, "moderate-student.png")

# 2. Test: World
im = bg(); d = ImageDraw.Draw(im)
topbar(d, "TEST", [("players", "14 / 30", BONE), ("clock", "23:00 Night", BONE), ("moon", "Waning", BONE), ("season", "Autumn", BONE), ("sky", "Night", BONE)])
rail(d, ROWS, 0)
tabs(d, ["Character", "Progress", "School", "Story", "World", "Spawns", "Self"], "World")
d.rounded_rectangle([378, 178, 1150, 210], 8, fill=IRON2, outline=BRASS_D, width=1)
text(d, (392, 194), "Preview just for me", 20, BONE, anchor="lm")
d.rounded_rectangle([1080, 182, 1140, 206], 12, fill=BRASS); d.ellipse([1114, 184, 1136, 204], fill=INK)
text(d, (620, 194), "season, moon and sky: your screen only", 20, DIM, i=True, anchor="lm")
card(d, 376, 222, cw, ch, "sun", "Time of day", "Moves the school clock forward", [("Dawn", False), ("Noon", False), ("Dusk", False), ("Midnight", True)])
card(d, 770, 222, cw, ch, "leaf", "Season", "Event seasons swap the skies", [("Autumn", True), ("Winter", False), ("Nightmare", False)])
card(d, 376, 402, cw, ch, "moon", "Moon tonight", "Full, new, crimson or blue", [("Full", False), ("New", False), ("Crimson", True), ("Blue", False)])
card(d, 770, 402, cw, ch, "cloud", "Sky", "Override the painted sky", [("Schedule", True), ("Storm", False), ("Any set…", False)])
card(d, 376, 576, cw, ch - 30, "pin", "Go to a place", "All 19 regions; or send the student", [("Chapel", False), ("Archive", False), ("…", False)])
card(d, 770, 576, cw, ch - 30, "moon", "Full moon tonight", "Jumps to 22:00 on the next full moon", [])
feed(d, [(True, "Moon tonight: Crimson (your screen only)"), (True, "Time: Midnight (23:00)"), (True, "Season: Autumn")])
context(d, "RELLO  ·  live", [("h", "CHARACTER", ""), ("ok", "Human I", "Height 4'11'' · Build Average"), ("ok", "Level 6", "423 EXP · 3 stat points"),
        ("h", "SCHOOL", ""), ("ok", "Bells 0 · Heat 0", "Discipline Clear · 1 detention owed"), ("h", "STORY", ""), ("ok", "First Hunt", "0 of 3 · tracked")])
save(im, "test-world.png")

# 3. Moderate: Inbox
im = bg(); d = ImageDraw.Draw(im)
topbar(d, "MODERATE", TILES_M); rail(d, ROWS, 1)
tabs(d, ["Inbox 2", "Student", "Server", "Log"], "Inbox 2")
y = 186
for who, frm, why, ago, quote, claimed in [
        ("NightRaven_04", "moonlit_mira", "Spam", "2 min ago", "\"FREE ROBUX at my game!!\" ×4 in 20 s", False),
        ("ash_tidewell", "auto-flag", "7 knockdowns in 60 s", "6 min ago", "Commons, After School · 3 different students", True)]:
    frame(d, 376, y, 1150, y + 190, fill=VELVET, edge=CRIMSON if not claimed else BRASS_D, w=2)
    icon(d, 414, y + 40, "flag", CRIMSON)
    text(d, (452, y + 18), f"{who}  ·  {why}", 22, BONE, b=True)
    text(d, (452, y + 48), f"reported by {frm}  ·  {ago}", 20, DIM)
    d.rounded_rectangle([452, y + 82, 1130, y + 124], 8, fill=INK)
    text(d, (466, y + 103), quote, 20, BONE, i=True, anchor="lm")
    cx = 452
    for s, on in ([("Claimed by Rello", True)] if claimed else [("Claim", True)]) + [("Open student", False), ("Resolve", False), ("Dismiss", False)]:
        cx = chip(d, cx, y + 140, s, on)
    y += 210
feed(d, [(True, "Report from moonlit_mira saved to NightRaven_04's history")])
context(d, "INBOX", [("h", "OPEN", ""), ("bad", "2 reports", "1 claimed"), ("h", "TODAY", ""), ("ok", "5 resolved", "3 warned · 1 muted · 1 dismissed")])
save(im, "inbox.png")

# 4. The command palette
im = bg(); d = ImageDraw.Draw(im)
topbar(d, "TEST", [("players", "14 / 30", BONE), ("clock", "12:30 After School", BONE)])
rail(d, ROWS, 2)
tabs(d, ["Character", "Progress", "School", "Story", "World", "Spawns", "Self"], "School")
d.rectangle([0, 0, W, H], fill=None)
ov = Image.new("RGBA", (W, H), (0, 0, 0, 150)); im.paste(ov, (0, 0), ov); d = ImageDraw.Draw(im)
frame(d, 420, 170, 1180, 640, fill=IRON, edge=BRASS, w=3); rivets(d, 420, 170, 1180, 640)
d.rounded_rectangle([444, 194, 1156, 244], 22, fill=INK, outline=BRASS, width=2)
text(d, (470, 219), "bell", 24, BONE, anchor="lm")
text(d, (1140, 219), "Esc", 20, DIM, anchor="rm")
for k, (t, sec, h) in enumerate([("Ring the bell", "Test · School", "Ends the period now"), ("Set Bells", "Test · School · Bell Tower", "0-5 on the selected student"),
                                 ("Bell Tower: clear notoriety", "Test · School · Bell Tower", "Heat 0, Bells 0, no summons"), ("Skip to a period", "Test · School", "Always moves forward")]):
    y = 262 + k * 90
    on = k == 1
    d.rounded_rectangle([444, y, 1156, y + 78], 8, fill=VELVET2 if on else IRON2, outline=BRASS if on else IRON2, width=2)
    icon(d, 482, y + 39, "flag" if k else "sun", BRASS)
    text(d, (520, y + 10), t, 22, BONE, b=True)
    text(d, (520, y + 42), f"{h}   ·   {sec}", 20, DIM)
    if on: text(d, (1140, y + 39), "Enter", 20, BRASS, anchor="rm")
save(im, "palette.png")
