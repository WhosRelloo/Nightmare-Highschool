"""Design-note images for the training HUD (docs/img/training-*.jpg).

training-hud-pbr.jpg     the training HUD in its final PBR art, laid out at the game's design positions, beside the
                         real in-game Thornrose health bar, posture rail and hotbar (cropped from a Studio Play
                         screenshot). A COMPOSITE: in game the HUD shows kit stand-ins until the group import.
training-anim-beats.jpg  the animation beats, frame by frame, in the final art: the ring closing with its trail and the
                         needle sweeping, the Perfect stamp's squash, the combo flame heating up, the HOLD gear, the
                         molten pour, the step-up banner.

    python compose_training_preview.py <play screenshot with the bottom HUD>
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FINAL = HERE / "out" / "training" / "final"
DOCS = HERE.parents[2] / "docs" / "img"
f32 = np.float32
FT = "C:/Windows/Fonts/georgiab.ttf"
FB = "C:/Windows/Fonts/georgia.ttf"
GOLD, BONE, DIM = (235, 205, 120, 255), (228, 222, 208, 255), (150, 142, 138, 255)


def art(name, size=None, rot=0, alpha=1.0):
    im = Image.open(FINAL / f"{name}.png").convert("RGBA")
    if size:
        im = im.resize(size if isinstance(size, tuple) else (size, size), Image.LANCZOS)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC)
    if alpha < 1:
        a = np.array(im, f32)
        a[..., 3] *= alpha
        im = Image.fromarray(a.astype(np.uint8), "RGBA")
    return im


def paste_c(bg, im, cx, cy):
    bg.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def slice9(name, w, h, cx0, cy0, cx1, cy1, scale=0.5):
    """a 9-slice image drawn at w x h (slice edges kept at scale)"""
    src = Image.open(FINAL / f"{name}.png").convert("RGBA")
    W, H = src.size
    out = Image.new("RGBA", (w, h))
    L, T, R, B = cx0, cy0, W - cx1, H - cy1
    l, t, r, b = int(L * scale), int(T * scale), int(R * scale), int(B * scale)
    xs = [(0, L, 0, l), (L, cx1, l, w - r), (cx1, W, w - r, w)]
    ys = [(0, T, 0, t), (T, cy1, t, h - b), (cy1, H, h - b, h)]
    for sx0, sx1, dx0, dx1 in xs:
        for sy0, sy1, dy0, dy1 in ys:
            if dx1 > dx0 and dy1 > dy0:
                out.alpha_composite(src.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.LANCZOS), (dx0, dy0))
    return out


def ring_at(name, radius):
    size = max(8, int(radius / (470 / 1024)))
    return art(name, size)


def hud(shot):
    """the final art drawn over the in-game stand-ins at their exact place and scale, on a real Play screenshot (the
    health bar, posture rail, hotbar, clock and quest tracker are the game's own)"""
    bg = Image.open(shot).convert("RGBA")
    W, H = bg.size
    u = 475 / 680                       # the kit's UI scale in this screenshot (the plate is 680 design px wide)
    U_ = lambda v: int(round(v * u))
    # the stand-ins' own words (rating, combo) are drawn again below in the final art: cover them with the dark wall
    for box in ((596, 195, 800, 262), (880, 78, 1000, 148)):
        patch = bg.crop((box[0], box[1] + 70, box[2], box[3] + 70)).filter(ImageFilter.GaussianBlur(6))
        bg.paste(patch, box[:2])
    d = ImageDraw.Draw(bg)
    fT, fB, fS = ImageFont.truetype(FT, U_(30)), ImageFont.truetype(FB, U_(21)), ImageFont.truetype(FB, U_(17))
    # the set plate
    px, py = int(W / 2 - U_(340)), U_(28)
    bg.alpha_composite(slice9("TrainPlate", U_(680), U_(104), 64, 64, 704, 128, 0.5 * u), (px, py))
    bg.alpha_composite(art("TrainStationPullUp", U_(80)), (px + U_(14), py + U_(12)))
    d = ImageDraw.Draw(bg)
    d.text((px + U_(108), py + U_(16)), "PULL-UPS", font=fT, fill=GOLD)
    d.text((px + U_(108), py + U_(56)), "Arms  Lv 5  ·  Tier II", font=fB, fill=BONE)
    d.text((px + U_(660), py + U_(16)), "Rep 2 / 16", font=fT, fill=BONE, anchor="ra")
    bg.alpha_composite(art("TrainBadgeStreak", U_(32)), (px + U_(560), py + U_(58)))
    d.text((px + U_(596), py + U_(62)), "1 day", font=fS, fill=BONE)
    # the next-change bar
    bx, by = int(W / 2 + U_(20) - U_(300)), U_(176)
    fillw = int(U_(564) * 0.84)
    tile = art("TrainBarFill", (U_(112), U_(14)))
    x = bx + U_(18)
    while x < bx + U_(18) + fillw:
        w = min(tile.width, bx + U_(18) + fillw - x)
        bg.alpha_composite(tile.crop((0, 0, w, tile.height)), (x, by + U_(11)))
        x += tile.width
    paste_c(bg, art("TrainMarkGlow", U_(46)), bx + U_(18) + fillw, by + U_(18))
    bg.alpha_composite(art("TrainBarFrame", (U_(600), U_(36))), (bx, by))
    bg.alpha_composite(art("TrainIconArms", U_(52)), (bx - U_(62), by - U_(8)))
    # the gauge
    G = U_(380)
    gx, gy = int(W * 0.66), int(H * 0.47)
    paste_c(bg, art("TrainGauge", G), gx, gy)
    for k, a in ((3, 0.12), (2, 0.22), (1, 0.38)):
        paste_c(bg, art("TrainRing", int(G * (0.36 + k * 0.012) / (470 / 1024)), alpha=a), gx, gy)
    paste_c(bg, ring_at("TrainRing", G * 0.36), gx, gy)
    paste_c(bg, art("TrainNeedle", int(G * 0.62), rot=60), gx, gy)
    paste_c(bg, art("TrainIconArms", int(G * 0.2)), gx, gy)
    # the combo (above the gauge) with its flame
    fl = Image.open(FINAL / "TrainFlame.png").convert("RGBA").crop((256, 0, 512, 256)).resize((U_(96), U_(96)), Image.LANCZOS)
    paste_c(bg, fl, gx, gy - G // 2 - U_(64))
    d = ImageDraw.Draw(bg)
    d.text((gx, gy - G // 2 - U_(58)), "×2", font=ImageFont.truetype(FT, U_(64)), fill=GOLD, anchor="mm", stroke_width=2, stroke_fill=(20, 12, 8, 255))
    d.text((gx, gy - G // 2 - U_(18)), "COMBO", font=ImageFont.truetype(FT, U_(17)), fill=BONE, anchor="mm")
    # the stamp, left of the gauge
    rx, ry = gx - G // 2 - U_(40), gy - G // 2 + int(G * 0.3)
    paste_c(bg, art("TrainRatePerfect", U_(76)), rx - U_(38), ry)
    d.text((rx - U_(84), ry), "PERFECT", font=ImageFont.truetype(FT, U_(36)), fill=GOLD, anchor="rm")
    # the key cap
    bg.alpha_composite(slice9("TrainKey", U_(280), U_(60), 40, 40, 216, 88, 0.5 * u), (gx - U_(140), gy + G // 2 + U_(14)))
    d.text((gx, gy + G // 2 + U_(44)), "SPACE  or  CLICK", font=ImageFont.truetype(FT, U_(22)), fill=BONE, anchor="mm")
    big = bg.resize((W * 3 // 2, H * 3 // 2), Image.LANCZOS)
    dd = ImageDraw.Draw(big)
    dd.text((big.width - 12, big.height - 8), "Composite: the final PBR art over the in-game stand-ins (same place, same scale). Health bar, rail and hotbar are the game's own.",
            font=ImageFont.truetype(FB, 15), fill=DIM, anchor="rb")
    big.convert("RGB").save(DOCS / "training-hud-pbr.jpg", quality=90)
    print("wrote training-hud-pbr.jpg")


def beats():
    cell, n = 300, 6
    rows = 3
    W, H = cell * n, cell * rows + 60
    im = Image.new("RGBA", (W, H), (16, 13, 19, 255))
    d = ImageDraw.Draw(im)
    fS, fT = ImageFont.truetype(FB, 16), ImageFont.truetype(FT, 18)
    titles = ["Ring closes (trail, needle sweeps)", "Perfect: stamp squash + sparks", "Combo flame heats up"]
    G = 240
    for i in range(n):  # row 1: the ring closing on the mark
        cx, cy = i * cell + cell // 2, cell // 2 + 30
        paste_c(im, art("TrainGauge", G), cx, cy)
        p = i / (n - 1)
        r = (0.43 + (0.1855 - 0.43) * p) * G
        for k, a in ((3, 0.12), (2, 0.22), (1, 0.38)):
            paste_c(im, art("TrainRing", int(max(8, r + k * 6) / (470 / 1024)), alpha=a), cx, cy)
        paste_c(im, ring_at("TrainRing", r), cx, cy)
        paste_c(im, art("TrainNeedle", int(G * 0.62), rot=120 - 240 * p), cx, cy)
        paste_c(im, art("TrainIconArms", int(G * 0.2)), cx, cy)
        if i == n - 1:
            paste_c(im, art("TrainMarkGlow", G), cx, cy)
    for i, sc in enumerate((1.55, 0.9, 1.06, 1.0, 1.0, 1.0)):  # row 2: the stamp
        cx, cy = i * cell + cell // 2, cell + cell // 2 + 30
        s = int(96 * sc)
        sq = (int(s * (1.12 if i == 1 else 1)), int(s * (0.85 if i == 1 else 1)))
        paste_c(im, art("TrainRatePerfect", sq, alpha=1 if i < 4 else (0.6 if i == 4 else 0.25)), cx, cy - 20)
        if i in (1, 2):
            for k in range(14):
                a = k / 14 * 2 * math.pi
                rr = 60 + i * 34
                paste_c(im, art("TrainMarkGlow", 18), cx + rr * math.cos(a), cy - 20 + rr * math.sin(a))
        d = ImageDraw.Draw(im)
        d.text((cx, cy + 50), "PERFECT", font=ImageFont.truetype(FT, int(28 * sc)), fill=GOLD, anchor="mm")
    sheet = Image.open(FINAL / "TrainFlame.png").convert("RGBA")
    for i in range(n):  # row 3: the combo flame
        cx, cy = i * cell + cell // 2, 2 * cell + cell // 2 + 30
        fr = (i * 3) % 16
        f = sheet.crop(((fr % 4) * 256, (fr // 4) * 256, (fr % 4) * 256 + 256, (fr // 4) * 256 + 256))
        heat = i / (n - 1)
        sz = int(110 + 90 * heat)
        paste_c(im, f.resize((sz, sz), Image.LANCZOS), cx, cy - 10 - heat * 20)
        d = ImageDraw.Draw(im)
        combo = (2, 5, 9, 12, 18, 25)[i]
        col = tuple(int(GOLD[j] * (1 - heat * 0.5) + (255, 136, 60, 255)[j] * heat * 0.5) for j in range(4))
        d.text((cx, cy + 10), f"×{combo}", font=ImageFont.truetype(FT, int(48 + heat * 14)), fill=col, anchor="mm", stroke_width=2, stroke_fill=(20, 12, 8, 255))
        d.text((cx, cy + 56), "UNSTOPPABLE" if combo >= 20 else ("ON FIRE" if combo >= 10 else "COMBO"), font=fS, fill=BONE, anchor="mm")
    for r, t in enumerate(titles):
        d.text((12, r * cell + 8), t, font=fT, fill=GOLD)
    d.text((12, H - 34), "Also animated (in-game screenshots in docs/Training.md): the HOLD gear grinding, the molten pour, the step-up banner and flex, the shine sweeps.",
           font=fS, fill=DIM)
    im.convert("RGB").save(DOCS / "training-anim-beats.jpg", quality=90)
    print("wrote training-anim-beats.jpg")


if __name__ == "__main__":
    hud(sys.argv[1])
    beats()
