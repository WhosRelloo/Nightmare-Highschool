"""Nightmare High logo -> height + material masks for the PBR relief (art/logo/nh_logo_pbr.py).

Region outlines are in the source image's pixel space (565 x 559, E:/Download/Nightmare High.png, copied to
art/logo/source.png). Run directly to write an overlay check: python regions.py <out.png>
"""
SHIELD = [(150, 126), (284, 80), (419, 129), (416, 350), (386, 375), (284, 400), (182, 375), (153, 350)]
# the banner: main band plus the two folded tails
RIBBON = [
    (28, 414), (119, 388), (128, 409), (206, 413), (300, 397), (388, 377), (438, 370), (475, 375), (538, 405),
    (530, 500), (470, 490), (395, 484), (380, 468), (300, 476), (206, 494), (106, 501), (100, 484), (28, 488),
]
SPIKE = [(268, 470), (300, 470), (284, 548)]

if __name__ == "__main__":
    import sys
    import cv2
    import numpy as np
    im = cv2.imread("E:/Download/Nightmare High.png", cv2.IMREAD_UNCHANGED)
    vis = im[..., :3].copy()
    for poly, col in ((SHIELD, (0, 255, 0)), (RIBBON, (255, 255, 0)), (SPIKE, (255, 0, 255))):
        cv2.polylines(vis, [np.array(poly, np.int32)], True, col, 1)
    cv2.imwrite(sys.argv[1] if len(sys.argv) > 1 else "overlay.png", cv2.resize(vis, None, fx=1.6, fy=1.6))
