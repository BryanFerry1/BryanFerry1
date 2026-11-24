"""Cut the green-screen sheets exported from Canva into RGBA layers.

Inputs (assets/raw/):
  plate.png         background plate (blue bg, blobs, Doctolib + CPTS logos)
  sheet_images.png  static visuals on #00FF00
  sheets.mp4        3 pages x 5 s of animated characters on #00FF00
Outputs (assets/layers/):
  <name>.png               static RGBA layers
  <name>/0000.png ...      RGBA frame sequences for animated layers
"""
import os
import cv2
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "assets", "raw")
OUT = os.path.join(HERE, "assets", "layers")

STATIC = {  # name: (x, y, w, h) on sheet_images.png
    "burst": (20, 20, 720, 510),
    "google": (760, 20, 1140, 434),
    "search": (940, 470, 960, 221),
    "cpts_card": (20, 550, 400, 497),
    "login_card": (440, 550, 480, 421),
    "bubble": (940, 720, 560, 256),
    "bulb": (1540, 720, 200, 180),
}
VIDEO = {  # name: (page, x, y, w, h)
    "char_thinking": (0, 60, 40, 500, 1000),
    "char_waving": (0, 710, 40, 500, 1000),
    "char_laptop1": (0, 1360, 40, 500, 1000),
    "char_laptop2": (1, 60, 40, 500, 1000),
    "char_laptop3": (1, 710, 40, 500, 1000),
    "char_presenting": (1, 1360, 40, 500, 1000),
    "char_questions": (2, 40, 40, 500, 1000),
    "char_highfive": (2, 600, 40, 467, 1000),
    "envelope": (2, 1180, 40, 600, 514),
}
PAD = 8


def key(rgb, enclosed=False):
    """rgb uint8 HxWx3 -> RGBA uint8 with green removed.
    enclosed=False: only green connected to the border is removed (screenshots with green text).
    enclosed=True: all green is removed and despilled (characters: gaps between curls)."""
    f = rgb.astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    d = g - np.maximum(r, b)
    soft = 1.0 - np.clip((d - 40.0) / (150.0 - 40.0), 0, 1)  # 1 = opaque
    bg = soft < 0.5
    lab, n = ndimage.label(bg)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    border = border[border > 0]
    outside = np.isin(lab, border)
    if enclosed:
        outside = bg
    near = ndimage.binary_dilation(outside, iterations=3)
    if enclosed:
        near[:] = True
    alpha = np.where(near, soft, 1.0)
    alpha[outside] = np.minimum(alpha[outside], soft[outside])
    # despill on edge pixels only
    g2 = np.where(near, np.minimum(g, np.maximum(r, b) + 8), g)
    outc = np.stack([r, g2, b], -1)
    a8 = (alpha * 255).astype(np.uint8)
    return np.dstack([np.clip(outc, 0, 255).astype(np.uint8), a8])


def crop(img, x, y, w, h):
    H, W = img.shape[:2]
    return img[max(0, y - PAD):min(H, y + h + PAD), max(0, x - PAD):min(W, x + w + PAD)]


def save(path, rgba):
    cv2.imwrite(path, cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA), [cv2.IMWRITE_PNG_COMPRESSION, 3])


def main(static_only=False):
    os.makedirs(OUT, exist_ok=True)
    plate = cv2.imread(os.path.join(RAW, "plate_nologo.png"))  # logos are drawn on top separately
    cv2.imwrite(os.path.join(OUT, "plate.png"), plate)
    sheet = cv2.cvtColor(cv2.imread(os.path.join(RAW, "sheet_images_2x.png")), cv2.COLOR_BGR2RGB)  # 2x export
    for name, box in STATIC.items():
        box2 = tuple(v * 2 for v in box)
        save(os.path.join(OUT, name + ".png"), key(crop(sheet, *box2), enclosed=name in ("burst", "bulb", "bubble")))
        print("static", name)
    # logos (sheet on magenta: the CPTS logo contains green, so no green key here)
    lg = cv2.cvtColor(cv2.imread(os.path.join(RAW, "sheet_logos.png")), cv2.COLOR_BGR2RGB)
    c = lg[40:738, 40:740].astype(np.float32)
    d = np.minimum(c[..., 0], c[..., 2]) - c[..., 1]
    a = 1.0 - np.clip((d - 60.0) / (200.0 - 60.0), 0, 1)
    rgb = c.copy()
    edge = a < 0.98  # remove magenta spill on edges
    rgb[..., 0] = np.where(edge, np.minimum(rgb[..., 0], rgb[..., 1] + 40), rgb[..., 0])
    rgb[..., 2] = np.where(edge, np.minimum(rgb[..., 2], rgb[..., 1] + 40), rgb[..., 2])
    rgba = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)
    ys, xs = np.where(rgba[..., 3] > 10)
    save(os.path.join(OUT, "logo_cpts.png"), rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
    doc = lg[44:396, 804:1876]
    save(os.path.join(OUT, "logo_doctolib.png"), np.dstack([doc, np.full(doc.shape[:2], 255, np.uint8)]))
    print("logos")
    if static_only:
        return

    cap = cv2.VideoCapture(os.path.join(RAW, "sheets.mp4"))
    frames = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
    print(len(frames), "frames")
    per = len(frames) // 3
    for name, (page, x, y, w, h) in VIDEO.items():
        d = os.path.join(OUT, name)
        os.makedirs(d, exist_ok=True)
        # skip first/last 2 frames of each page (Canva page transitions)
        for i, fi in enumerate(range(page * per + 2, page * per + per - 2)):
            save(os.path.join(d, f"{i:04d}.png"), key(crop(frames[fi], x, y, w, h), enclosed=True))
        print("video", name)


if __name__ == "__main__":
    import sys
    main(static_only="--static" in sys.argv)
