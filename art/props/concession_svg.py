"""SVG toolkit for the concession kit's printed atlas (concession_atlas.py, props batch 54).

Each label is one SVG drawn in label pixels (W x H). It is rendered three times by headless Edge at 2x:

  colour  the art as drawn
  foil    black, with every element of class "foil" white (occlusion kept: anything drawn over foil blacks it out again).
          Becomes the _gilt map (metal; atlas_mat also reads it as smoother).
  height  flat grey (128); class "emb" raised (light), class "deb" pressed in (dark). Becomes the _height map (a bump).

Class "fx" (shadows, glows, sheen overlays) shows only in the colour pass; class "nf" marks an element with no fill (a stroke)
so the mask passes don't fill it. Text is fitted with the same TTF files Edge uses (PIL measures it).
"""
import math
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageFilter, ImageFont

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
WORK = "E:/NH-Work/props54/atlas2/render"
FD = "C:/Windows/Fonts/"

# key: (css family, weight, style, ttf for measuring)
FONTS = {
    "serif": ("Palatino Linotype", "bold", "normal", "palab.ttf"),
    "serifr": ("Palatino Linotype", "normal", "normal", "pala.ttf"),
    "serifi": ("Palatino Linotype", "normal", "italic", "palai.ttf"),
    "serifbi": ("Palatino Linotype", "bold", "italic", "palabi.ttf"),
    "black": ("GothicE", "normal", "normal", "gothice_.ttf"),
    "impact": ("Impact", "normal", "normal", "impact.ttf"),
    "heavy": ("Arial Black", "normal", "normal", "ariblk.ttf"),
    "script": ("Segoe Script", "bold", "normal", "segoescb.ttf"),
    "hand": ("Ink Free", "normal", "normal", "Inkfree.ttf"),
    "print": ("Segoe Print", "bold", "normal", "segoeprb.ttf"),
    "gab": ("Gabriola", "normal", "normal", "Gabriola.ttf"),
    "frank": ("Franklin Gothic Medium", "normal", "normal", "framd.ttf"),
    "bank": ("BankGothic Md BT", "normal", "normal", "bgothm.ttf"),
    "dutch": ("Dutch801 XBd BT", "normal", "normal", "dutcheb.ttf"),
    "sblack": ("Segoe UI Black", "normal", "normal", "seguibl.ttf"),
    "comic": ("Comic Sans MS", "bold", "normal", "comicbd.ttf"),
    "georgia": ("Georgia", "bold", "normal", "georgiab.ttf"),
    "cons": ("Constantia", "bold", "normal", "constanb.ttf"),
}
_meas = {}


def text_width(s, f, size, ls=0.0):
    if f not in _meas:
        _meas[f] = ImageFont.truetype(FD + FONTS[f][3], 100)
    return _meas[f].getlength(s) * size / 100 + ls * max(0, len(s) - 1)


def fit_size(s, f, maxw, maxh, ls=0.0):
    w100 = text_width(s, f, 100, ls * 100 / max(maxh, 1))
    return max(4.0, min(maxh, maxh * maxw / max(w100 * maxh / 100, 1e-6)))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _attrs(fill="none", stroke=None, sw=0, cls="", op=1.0, extra=""):
    c = cls.split()
    if fill == "none" and "nf" not in c:
        c.append("nf")
    a = f'fill="{fill}"'
    if stroke:
        a += f' stroke="{stroke}" stroke-width="{sw:.2f}" stroke-linejoin="round" stroke-linecap="round"'
    if c:
        a += f' class="{" ".join(c)}"'
    if op < 1:
        a += f' opacity="{op:.3f}"'
    if extra:
        a += " " + extra
    return a


class Label:
    def __init__(self, key, W, H, bg="#000", bg_cls=""):
        self.key, self.W, self.H = key, int(W), int(H)
        self.defs, self.body = [], []
        self._n = 0
        self.rect(0, 0, W, H, bg, cls=bg_cls)

    def uid(self, p="d"):
        self._n += 1
        return f"{p}{self._n}"

    def add(self, s):
        self.body.append(s)
        return s

    # ---------------------------------------------------------------- paint servers
    def lin(self, stops, x1=0, y1=0, x2=0, y2=1, units="objectBoundingBox", spread="pad"):
        i = self.uid("g")
        st = "".join(f'<stop offset="{o}" stop-color="{c}"' + (f' stop-opacity="{a}"' if a != 1 else "") + "/>"
                     for o, c, a in [(s + (1,))[:3] for s in stops])
        self.defs.append(f'<linearGradient id="{i}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" gradientUnits="{units}" '
                         f'spreadMethod="{spread}">{st}</linearGradient>')
        return f"url(#{i})"

    def rad(self, stops, cx=0.5, cy=0.5, r=0.5, fx=None, fy=None):
        i = self.uid("r")
        st = "".join(f'<stop offset="{o}" stop-color="{c}"' + (f' stop-opacity="{a}"' if a != 1 else "") + "/>"
                     for o, c, a in [(s + (1,))[:3] for s in stops])
        f = f' fx="{fx}" fy="{fy}"' if fx is not None else ""
        self.defs.append(f'<radialGradient id="{i}" cx="{cx}" cy="{cy}" r="{r}"{f}>{st}</radialGradient>')
        return f"url(#{i})"

    def gilt(self, horiz=False):
        return self.lin([(0, "#7a5420"), (0.28, "#f2d48a"), (0.5, "#b8862e"), (0.72, "#f6dc98"), (1, "#8a5e22")],
                        0, 0, (1 if horiz else 0.25), (0 if horiz else 1))

    def silver(self):
        return self.lin([(0, "#6c7078"), (0.3, "#f2f4f8"), (0.55, "#9aa0aa"), (0.8, "#e8ecf2"), (1, "#70747c")], 0, 0, 0.3, 1)

    def holo(self):
        return self.lin([(0, "#f7a8d8"), (0.17, "#ffe39a"), (0.34, "#a8f0c8"), (0.5, "#9cd8ff"), (0.67, "#c8a8ff"), (0.84, "#ffb0c0"),
                         (1, "#f7a8d8")], 0, 0, 1, 0.6)

    def pattern(self, w, h, body, transform=""):
        i = self.uid("p")
        t = f' patternTransform="{transform}"' if transform else ""
        self.defs.append(f'<pattern id="{i}" width="{w}" height="{h}" patternUnits="userSpaceOnUse"{t}>{body}</pattern>')
        return f"url(#{i})"

    def clip(self, inner):
        i = self.uid("c")
        self.defs.append(f'<clipPath id="{i}">{inner}</clipPath>')
        return f'clip-path="url(#{i})"'

    def blur(self, sd):
        i = self.uid("f")
        self.defs.append(f'<filter id="{i}" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="{sd}"/></filter>')
        return f'filter="url(#{i})"'

    # ---------------------------------------------------------------- shapes
    def rect(self, x, y, w, h, fill="none", stroke=None, sw=0, cls="", op=1.0, rx=0, extra=""):
        return self.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx}" {_attrs(fill, stroke, sw, cls, op, extra)}/>')

    def circle(self, cx, cy, r, fill="none", stroke=None, sw=0, cls="", op=1.0, extra=""):
        return self.add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" {_attrs(fill, stroke, sw, cls, op, extra)}/>')

    def ellipse(self, cx, cy, rx, ry, fill="none", stroke=None, sw=0, cls="", op=1.0, rot=0, extra=""):
        t = f'transform="rotate({rot} {cx:.2f} {cy:.2f})" ' if rot else ""
        return self.add(f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" {t}{_attrs(fill, stroke, sw, cls, op, extra)}/>')

    def path(self, d, fill="none", stroke=None, sw=0, cls="", op=1.0, extra=""):
        return self.add(f'<path d="{d}" {_attrs(fill, stroke, sw, cls, op, extra)}/>')

    def poly(self, pts, fill="none", stroke=None, sw=0, cls="", op=1.0, closed=True, extra=""):
        p = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        tag = "polygon" if closed else "polyline"
        return self.add(f'<{tag} points="{p}" {_attrs(fill, stroke, sw, cls, op, extra)}/>')

    def line(self, x1, y1, x2, y2, stroke, sw, cls="", op=1.0, extra=""):
        return self.add(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" {_attrs("none", stroke, sw, cls, op, extra)}/>')

    def group(self, cls="", extra="", items=()):
        c = f' class="{cls}"' if cls else ""
        return self.add(f"<g{c} {extra}>" + "".join(items) + "</g>")

    def begin(self, cls="", extra=""):
        c = f' class="{cls}"' if cls else ""
        self.body.append(f"<g{c} {extra}>")

    def end(self):
        self.body.append("</g>")

    def text(self, s, x, y, size=None, f="serif", fill="#000", anchor="middle", maxw=None, maxh=None, cls="", ls=0.0,
             stroke=None, sw=0, rot=0, op=1.0, shadow=None, extra=""):
        """Text centred vertically on y (cap height). With maxw / maxh the size is fitted; returns the size used."""
        if size is None:
            size = fit_size(s, f, maxw, maxh, ls)
        elif maxw:
            size = min(size, fit_size(s, f, maxw, size, ls))
        fam, wt, sty, _ = FONTS[f]
        base = y + size * 0.35
        t = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot else ""
        def common(px, py):
            return (f'x="{px:.2f}" y="{py:.2f}" font-family="{fam}" font-weight="{wt}" font-style="{sty}" font-size="{size:.2f}" '
                    f'text-anchor="{anchor}" letter-spacing="{ls:.2f}"{t}')
        if shadow:
            dx, dy, col, a = shadow
            self.add(f'<text {common(x + dx, base + dy)} fill="{col}" opacity="{a}" class="fx" {self.blur(size * 0.03)}>{esc(s)}</text>')
        st = f' stroke="{stroke}" stroke-width="{sw:.2f}" stroke-linejoin="round" paint-order="stroke"' if stroke else ""
        c = f' class="{cls}"' if cls else ""
        o = f' opacity="{op}"' if op < 1 else ""
        self.add(f'<text {common(x, base)} fill="{fill}"{st}{c}{o} {extra}>{esc(s)}</text>')
        return size

    def text_arc(self, s, cx, cy, r, size, f="serif", fill="#000", start=-90, top=True, cls="", ls=0.0, stroke=None, sw=0):
        """Text along a circle: over the top (top=True, reading left to right) or along the bottom."""
        i = self.uid("a")
        if top:
            d = f"M {cx - r:.2f} {cy:.2f} A {r:.2f} {r:.2f} 0 0 1 {cx + r:.2f} {cy:.2f}"
        else:
            d = f"M {cx - r:.2f} {cy:.2f} A {r:.2f} {r:.2f} 0 0 0 {cx + r:.2f} {cy:.2f}"
        self.defs.append(f'<path id="{i}" d="{d}"/>')
        fam, wt, sty, _ = FONTS[f]
        st = f' stroke="{stroke}" stroke-width="{sw}" paint-order="stroke"' if stroke else ""
        c = f' class="{cls}"' if cls else ""
        dy = size * 0.35 if top else size * 0.35
        self.add(f'<text font-family="{fam}" font-weight="{wt}" font-style="{sty}" font-size="{size:.2f}" fill="{fill}" letter-spacing="{ls}"'
                 f'{st}{c} dy="{dy:.2f}"><textPath href="#{i}" startOffset="50%" text-anchor="middle">{esc(s)}</textPath></text>')

    # ---------------------------------------------------------------- output
    def svg(self, mode):
        css = {
            "color": ".nf{fill:none}",
            "foil": ("*{fill:#000 !important;stroke:#000 !important} .nf{fill:none !important} "
                     ".foil,.foil *{fill:#fff !important;stroke:#fff !important} .foil .nf,.nf.foil{fill:none !important} "
                     ".fx,.fx *{display:none}"),
            "height": ("*{fill:#808080 !important;stroke:#808080 !important} .nf{fill:none !important} "
                       ".emb,.emb *{fill:#e6e6e6 !important;stroke:#e6e6e6 !important} "
                       ".deb,.deb *{fill:#2a2a2a !important;stroke:#2a2a2a !important} .emb .nf,.deb .nf,.nf.emb,.nf.deb{fill:none !important} "
                       ".fx,.fx *{display:none}"),
        }[mode]
        # inline <style> applies to the whole page, so every rule is scoped to this pass's own svg
        css = " ".join(f"#pass-{mode} " + r.strip().replace(",", f",#pass-{mode} ") + "}" for r in css.split("}") if r.strip())
        return (f'<svg id="pass-{mode}" xmlns="http://www.w3.org/2000/svg" width="{self.W * 2}" height="{self.H * 2}" '
                f'viewBox="0 0 {self.W} {self.H}" style="display:block"><style>{css}</style><defs>{"".join(self.defs)}</defs>'
                f'{"".join(self.body)}</svg>')


# ------------------------------------------------------------------ rendering

def _render_one(args):
    L, slot = args
    os.makedirs(WORK, exist_ok=True)
    html = os.path.join(WORK, f"{L.key}.html")
    png = os.path.join(WORK, f"{L.key}.png")
    with open(html, "w", encoding="utf-8") as fh:
        fh.write('<html><body style="margin:0;background:#000">' + L.svg("color") + L.svg("foil") + L.svg("height") + "</body></html>")
    if os.path.exists(png):
        os.remove(png)
    for _ in range(3):
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        f"--user-data-dir={WORK}/edge{slot}", f"--window-size={L.W * 2},{L.H * 6}", f"--screenshot={png}",
                        "file:///" + html.replace("\\", "/")], capture_output=True, timeout=120)
        if os.path.exists(png):
            break
    im = Image.open(png).convert("RGB")
    W2, H2 = L.W * 2, L.H * 2
    col = im.crop((0, 0, W2, H2)).resize((L.W, L.H), Image.LANCZOS)
    foil = im.crop((0, H2, W2, 2 * H2)).convert("L").resize((L.W, L.H), Image.LANCZOS)
    hgt = im.crop((0, 2 * H2, W2, 3 * H2)).convert("L").filter(ImageFilter.GaussianBlur(1.6)).resize((L.W, L.H), Image.LANCZOS)
    return L.key, (col, foil, hgt)


def render_all(labels, workers=6):
    jobs = [(L, i % workers) for i, L in enumerate(labels)]
    with ThreadPoolExecutor(workers) as ex:
        return dict(ex.map(_render_one, jobs))
