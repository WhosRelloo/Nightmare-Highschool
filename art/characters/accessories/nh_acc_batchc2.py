"""Accessories batch C2 (Kit C, "The Night School Wardrobe"): the masks. All Head pieces, slot Mask, unisex.

  KintsugiMask  white porcelain mended with a gold seam, gilt rims, painted lashes, crimson lips and a tear-mark
  WatchMask     the beaked night-watch mask: a stitched leather band brow to cheekbones, a long beak in brass bands,
                crimson-glass lenses
  FoxMask, WolfMask, GrilleMask      (nh_kitc_masks_a.py)
  WaxMask, MothMask, DominoMask      (nh_kitc_masks_b.py)

Masks hold on by sitting on the face: no ties or bands round the head (they would pass through every hairstyle).
Run: bash E:/NH-Work/acc/bake_batch.sh KintsugiMask,WatchMask,FoxMask,WolfMask,GrilleMask,WaxMask,MothMask,DominoMask
"""
import nh_acc as A
from nh_acc import item
import nh_kitc_hq as HQ
try:
    import nh_kitc_masks_a   # noqa: F401  registers FoxMask, WolfMask, GrilleMask
except ImportError:
    pass
try:
    import nh_kitc_masks_b   # noqa: F401  registers WaxMask, MothMask, DominoMask
except ImportError:
    pass

MASKS = ["KintsugiMask", "WatchMask", "FoxMask", "WolfMask", "GrilleMask", "WaxMask", "MothMask", "DominoMask"]


@item("KintsugiMask", "Kintsugi porcelain mask", views=["front34", "front", "side", "close"],
      close=((1.5, -3.6, 1.65), (0, -0.6, 1.45), 60))
def build_kintsugi(M):
    HQ.build_porcelain(M, "KintsugiMask")
    return {"notes": "Kit C2: white porcelain mended with a gold seam, gilt rims, painted lashes, crimson lips, a tear-mark"}


@item("WatchMask", "Beaked night-watch mask", views=["front34", "front", "side", "close"],
      close=((2.4, -4.6, 1.7), (0, -0.85, 1.45), 70))
def build_watch(M):
    HQ.build_plague(M, "WatchMask")
    return {"notes": "Kit C2: stitched leather half-mask, a long beak in brass bands, crimson-glass lenses"}
