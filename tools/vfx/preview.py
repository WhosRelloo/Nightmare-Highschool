import bpy, sys, os
import numpy as np
d = sys.argv[sys.argv.index("--") + 1]
for name in sys.argv[sys.argv.index("--") + 2:]:
    p = os.path.join(d, name)
    img = bpy.data.images.load(p)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    a = px[..., 3:4]
    bg = np.array([0.08, 0.07, 0.1], dtype=np.float32)
    rgb = px[..., :3] * np.array([1.0, 0.25, 0.3]) * a + bg * (1 - a)
    outp = np.concatenate([rgb, np.ones((h, w, 1), np.float32)], axis=2)
    o = bpy.data.images.new("p", width=w, height=h)
    o.pixels = outp.ravel()
    o.filepath_raw = os.path.join(d, "preview_" + name)
    o.file_format = "PNG"
    o.save()
