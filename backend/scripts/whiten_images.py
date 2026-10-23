"""Put every product photo on a white background.

Some catalogue photos sit on (or are letterboxed with) pure black. This makes a white-background copy of
every image in data/products/ and writes it to data/products_white/, which the backend serves at
/media/products/. The originals are never modified.

Only near-pure-black pixels that are connected to the image border are turned white, so dark garments
(navy, charcoal, black) that don't touch a black background stay as they are.

Run from backend/:  .venv/Scripts/python.exe scripts/whiten_images.py
"""

import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

DATA = Path(__file__).resolve().parents[2] / "data"
SRC, DST = DATA / "products", DATA / "products_white"
BLACK_MAX = 14  # a pixel is "background black" if every channel is at most this (JPEG noise allowance)
EDGE_SOFTEN = 48  # fringe pixels darker than this, next to the background, are blended toward white


BAR_MAX = 30  # edge rows/columns this dark (for 90%+ of their pixels) are letterbox bars or a frame
BAR_LIMIT = 0.12  # never peel more than 12% of the width/height, so a dark garment is never mistaken for a bar


def _edge_bars(img: np.ndarray) -> np.ndarray:
    """Mask of dark bars or frame lines along each edge (e.g. a 1px black frame, or gray-black letterboxing
    that isn't dark enough for the main threshold), peeled inward from each side while the line stays dark."""
    dark = img.max(axis=2) <= BAR_MAX
    h, w = dark.shape
    mask = np.zeros_like(dark)
    for axis, size in ((0, h), (1, w)):
        line_dark = dark.mean(axis=1 - axis) >= 0.9  # per row (axis 0) or per column (axis 1)
        for indices in (range(size), range(size - 1, -1, -1)):
            for n, i in enumerate(indices):
                if n >= size * BAR_LIMIT or not line_dark[i]:
                    break
                if axis == 0:
                    mask[i, :] = True
                else:
                    mask[:, i] = True
    return mask


def whiten(path: Path) -> bool:
    img = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
    dark = img.max(axis=2) <= BLACK_MAX
    labels, _ = ndimage.label(dark)
    border = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    background = np.isin(labels, border[border > 0])
    background |= _edge_bars(img)
    if not background.any():  # no black background, frame, or bars to remove
        return False
    out = img.astype(np.float32)
    out[background] = 255
    # Anti-alias the edge: in a 3-pixel ring around the removed background, blend dark fringe pixels
    # toward white in proportion to how dark they are, so outlines stay smooth instead of jagged.
    ring = ndimage.binary_dilation(background, iterations=3) & ~background
    brightness = img.max(axis=2).astype(np.float32)
    keep = np.clip((brightness - BLACK_MAX) / (EDGE_SOFTEN - BLACK_MAX), 0, 1)[..., None]  # 1 = keep pixel
    out[ring] = (img[ring] * keep[ring] + 255 * (1 - keep[ring]))
    Image.fromarray(out.astype(np.uint8)).save(DST / path.name, quality=92)
    return True


def main() -> None:
    DST.mkdir(exist_ok=True)
    changed = []
    for path in sorted(SRC.glob("*.jpg")):
        if whiten(path):
            changed.append(path.name)
        else:
            shutil.copy2(path, DST / path.name)
    print(f"{len(changed)} of {len(list(SRC.glob('*.jpg')))} images had a black background whitened -> {DST}")
    if "-v" in sys.argv:
        print("\n".join(changed))


if __name__ == "__main__":
    main()
