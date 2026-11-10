"""Props batch 44 (the showpiece kit): turn a Cycles render into an oil painting on canvas (system Python with numpy,
scipy, OpenCV and PIL).

  python showpiece44_canvas.py <raw.png> <Name> [--seed N]

Strokes are laid coarse to fine (Hertzmann-style): each layer samples the reference blurred to its brush size and
lays an elongated, anti-aliased stroke along the local edge flow (structure tensor) wherever the canvas still differs
from the reference; the finest layers only land on detail (faces, hands, rims of light). Each stroke also lays a ridge
of paint into a height map. Then bristle streaks run along the flow, the canvas weave shows through faintly, the
varnish warms and yellows, a fine craquelure crazes it and the corners fall off.
Writes art/props/textures/<Name>_canvas.png (colour), <Name>_canvasnormal.png (the impasto) and
<Name>_canvasrough.png (glossy varnish over the ridges, duller in the cracks)."""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = "E:/Nightmare-Highschool/art/props/textures"


def orientation(lum, sigma=5.0):
    gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3)
    jxx = cv2.GaussianBlur(gx * gx, (0, 0), sigma)
    jyy = cv2.GaussianBlur(gy * gy, (0, 0), sigma)
    jxy = cv2.GaussianBlur(gx * gy, (0, 0), sigma)
    theta = 0.5 * np.arctan2(2 * jxy, jxx - jyy) + np.pi / 2      # along the edges
    coher = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / (jxx + jyy + 1e-6)
    return theta, coher


def paint(ref, seed=0):
    rng = np.random.default_rng(seed)
    h, w, _ = ref.shape
    lum = cv2.cvtColor(ref, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    theta, coher = orientation(lum, 6.0)
    canvas = cv2.GaussianBlur(ref, (0, 0), 18).astype(np.float32)
    height = np.zeros((h, w), np.float32)
    scale = w / 2048
    layers = [(int(22 * scale), 0.0, 1.0), (int(12 * scale), 14.0, 1.0), (int(6 * scale), 18.0, 0.9), (max(2, int(3 * scale)), 22.0, 0.8)]
    for r, thresh, cover in layers:
        blur = cv2.GaussianBlur(ref, (0, 0), max(1.0, r * 0.5)).astype(np.float32)
        err = np.linalg.norm(canvas - blur, axis=2)
        step = max(2, int(r * 0.8))
        ys, xs = np.mgrid[step // 2:h:step, step // 2:w:step]
        ys = (ys + rng.integers(-step // 2, step // 2 + 1, ys.shape)).clip(0, h - 1).ravel()
        xs = (xs + rng.integers(-step // 2, step // 2 + 1, xs.shape)).clip(0, w - 1).ravel()
        keep = err[ys, xs] > thresh
        if thresh == 0.0:
            keep[:] = True
        keep &= rng.random(len(keep)) < cover
        idx = np.nonzero(keep)[0]
        rng.shuffle(idx)
        for i in idx:
            y, x = int(ys[i]), int(xs[i])
            c = blur[y, x] * (1 + rng.normal(0, 0.035, 3))
            c = np.clip(c + rng.normal(0, 3.0), 0, 255)
            ang = np.degrees(theta[y, x]) + rng.normal(0, 8 + 25 * (1 - coher[y, x]))
            L = r * (1.6 + 2.4 * coher[y, x]) * rng.uniform(0.7, 1.3)
            Wd = r * rng.uniform(0.45, 0.7)
            axes = (max(1, int(L)), max(1, int(Wd)))
            cv2.ellipse(canvas, (x, y), axes, ang, 0, 360, tuple(float(v) for v in c), -1, cv2.LINE_AA)
            cv2.ellipse(height, (x, y), axes, ang, 0, 360, float(rng.uniform(0.35, 1.0)), -1, cv2.LINE_AA)
    return canvas, height, theta


def bristles(theta, h, w, seed=0):
    """High-frequency streaks running along the stroke flow (8 orientation bins of motion-blurred noise)."""
    rng = np.random.default_rng(seed + 7)
    noise = rng.random((h, w)).astype(np.float32)
    out = np.zeros((h, w), np.float32)
    bins = ((np.degrees(theta) % 180) / 22.5).astype(int) % 8
    k = 11
    for b in range(8):
        a = np.radians(b * 22.5 + 11.25)
        ker = np.zeros((k, k), np.float32)
        c = k // 2
        for t in np.linspace(-c, c, k * 2):
            ker[int(round(c + np.sin(a) * t)), int(round(c + np.cos(a) * t))] = 1
        ker /= ker.sum()
        out[bins == b] = cv2.filter2D(noise, -1, ker)[bins == b]
    return (out - out.mean()) / (out.std() + 1e-6)


def weave(h, w, period=5.0):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return (np.sin(x * 2 * np.pi / period) * np.sin(y * 2 * np.pi / period)).astype(np.float32)


def craquelure(h, w, seed=0, cells=900):
    rng = np.random.default_rng(seed + 3)
    pts = np.c_[rng.random(cells) * w, rng.random(cells) * h]
    small = (h // 4, w // 4)
    yy, xx = np.mgrid[0:small[0], 0:small[1]].astype(np.float32) * 4
    from scipy.spatial import cKDTree
    d, _ = cKDTree(pts).query(np.c_[xx.ravel(), yy.ravel()], k=2)
    edge = (d[:, 1] - d[:, 0]).reshape(small)
    crack = np.clip(1 - edge / 2.5, 0, 1).astype(np.float32)
    crack = cv2.resize(crack, (w, h), interpolation=cv2.INTER_LINEAR)
    return crack


def main(src, name, seed=0, varnish=0.12):
    ref = np.array(Image.open(src).convert("RGB"))
    h, w, _ = ref.shape
    canvas, height, theta = paint(ref, seed)
    # keep a little of the render's finest detail where it is sharpest (faces, rims), under the paint
    detail = ref.astype(np.float32) - cv2.GaussianBlur(ref, (0, 0), 2.0).astype(np.float32)
    canvas += detail * 0.25
    br = bristles(theta, h, w, seed)
    lum_mod = 1 + 0.035 * br + 0.018 * weave(h, w)
    canvas *= lum_mod[..., None]
    crack = craquelure(h, w, seed)
    canvas *= (1 - 0.18 * crack)[..., None]
    # varnish: warm and slightly yellowed, gently compressed, corners darkened
    c = canvas / 255
    c = c / (1 + c * 0.15)
    c = np.clip(c * 1.08, 0, 1)
    tint = np.array([1.0, 0.95, 0.82], np.float32)
    c = c * (1 - varnish) + c * tint * varnish
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2
    c *= (1 - 0.22 * np.clip(v - 0.35, 0, 1))[..., None]
    col = (np.clip(c, 0, 1) ** (1 / 1.0) * 255).astype(np.uint8)
    Image.fromarray(col).save(os.path.join(OUT, f"{name}_canvas.png"))
    # impasto normal map and varnish roughness
    hgt = cv2.GaussianBlur(height, (0, 0), 1.2) + 0.25 * br * 0.1 + 0.05 * weave(h, w) - 0.4 * crack
    gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=3) * 2.2
    gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=3) * 2.2
    n = np.dstack([-gx, gy, np.ones_like(gx)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)).save(os.path.join(OUT, f"{name}_canvasnormal.png"))
    rough = 0.34 - 0.08 * np.clip(hgt, 0, 1) + 0.25 * crack + 0.03 * br
    Image.fromarray((np.clip(rough, 0.05, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, f"{name}_canvasrough.png"))
    print("[canvas]", name, w, h)


if __name__ == "__main__":
    a = sys.argv[1:]
    seed = int(a[a.index("--seed") + 1]) if "--seed" in a else 0
    main(a[0], a[1], seed)
