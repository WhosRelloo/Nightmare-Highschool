"""Contact sheet: every variant as a template thumbnail plus front/back mock-ups."""
from PIL import Image, ImageDraw
import numpy as np

from nhcloth import OUT, SRC, R, font

SKIN = (224, 178, 138, 255)
BG = (18, 14, 16, 255)
CARD = (34, 28, 30, 255)
GOLD = (196, 160, 80, 255)


def face(img, name):
    x, y, w, h = R[name]
    return img.crop((x, y, x + w, y + h))


def figure(shirt, pants, back=False):
    """Blocky R6 stand-in: head, torso, arms, legs, skin under see-through areas."""
    fig = Image.new("RGBA", (256, 320), (0, 0, 0, 0))
    def part(box, layers):
        base = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), SKIN)
        for im in layers:
            base.alpha_composite(im.resize(base.size, Image.NEAREST))
        fig.paste(base, box[:2])
    t = "T_B" if back else "T_F"
    a_left, a_right = ("LA_B", "RA_B") if back else ("RA_F", "LA_F")
    # head
    ImageDraw.Draw(fig).rounded_rectangle((100, 0, 156, 58), 8, fill=SKIN)
    torso = [l for l in (face(pants, t) if pants else None, face(shirt, t) if shirt else None) if l]
    part((64, 64, 192, 192), torso)
    part((0, 64, 64, 192), [face(shirt, a_left)] if shirt else [])
    part((192, 64, 256, 192), [face(shirt, a_right)] if shirt else [])
    part((64, 192, 128, 320), [face(pants, a_left)] if pants else [])
    part((128, 192, 192, 320), [face(pants, a_right)] if pants else [])
    return fig


def checker(size, a=(58, 52, 54, 255), b=(70, 64, 66, 255), s=12):
    im = Image.new("RGBA", size, a)
    d = ImageDraw.Draw(im)
    for y in range(0, size[1], s):
        for x in range(0, size[0], s):
            if (x // s + y // s) % 2:
                d.rectangle((x, y, x + s - 1, y + s - 1), fill=b)
    return im


def build(items, path=OUT / "contact_sheet.png", title="Nightmare Highschool - clothing variants",
          note="Each card: the 585x559 template (transparent shown as checks) and a front/back mock-up. "
               "Shirts are shown over the charcoal slacks; pants under the black polo."):
    default_pants = Image.open(OUT / "pants_slacks_charcoal.png").convert("RGBA")
    default_shirt = Image.open(SRC / "shirt_black_polo_khaki.png").convert("RGBA")
    cw, ch = 340, 520
    cols = 5
    rows = (len(items) + cols - 1) // cols
    head = 90
    sheet = Image.new("RGBA", (cols * cw + 20, rows * ch + head + 10), BG)
    d = ImageDraw.Draw(sheet)
    d.text((20, 22), title, font=font(30), fill=GOLD)
    d.text((22, 60), note, font=font(14, bold=False), fill=(200, 190, 170, 255))
    for i, item in enumerate(items):
        fname, label = item[0], item[1]
        pair = item[2] if len(item) > 2 else None
        x0 = 10 + (i % cols) * cw
        y0 = head + (i // cols) * ch
        d.rounded_rectangle((x0 + 4, y0 + 4, x0 + cw - 6, y0 + ch - 6), 10, fill=CARD)
        img = Image.open(OUT / fname).convert("RGBA")
        thumb = checker((300, 287))
        thumb.alpha_composite(img.resize((300, 287), Image.LANCZOS))
        sheet.paste(thumb, (x0 + 20, y0 + 14))
        is_pants = fname.split("/")[-1].startswith("pants_")
        other = Image.open(OUT / pair).convert("RGBA") if pair else None
        shirt = (other or default_shirt) if is_pants else img
        pants = img if is_pants else (other or default_pants)
        for j, back in enumerate((False, True)):
            fg = figure(shirt, pants, back).resize((115, 144), Image.NEAREST)
            sheet.alpha_composite(fg, (x0 + 40 + j * 150, y0 + 312))
        d.text((x0 + 98, y0 + 460), "front", font=font(11, bold=False), fill=(150, 140, 130, 255), anchor="mm")
        d.text((x0 + 248, y0 + 460), "back", font=font(11, bold=False), fill=(150, 140, 130, 255), anchor="mm")
        d.text((x0 + 20, y0 + 474), label, font=font(15), fill=(236, 226, 200, 255))
        d.text((x0 + 20, y0 + 494), fname, font=font(11, bold=False), fill=(160, 150, 140, 255))
    sheet.convert("RGB").save(path, optimize=True)
    return path
