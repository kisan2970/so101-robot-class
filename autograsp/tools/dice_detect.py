"""Coloured-dice detector for the wrist camera (BGR frames, 640x480).

The dice is a saturated cube whose colour is set by "dice_color" in rig.json ("red" or "green", default red).
A static red/black marker also sits near the top of the scene, so detection accepts an optional ROI rect and a
previous position (tracking) to stay on the dice.
"""

from __future__ import annotations

import cv2
import numpy as np

from common import load_rig

# OpenCV HSV ranges (H 0-180). Red wraps around 0, so it needs two ranges.
COLORS = {
    "red": [((0, 120, 70), (8, 255, 255)), ((172, 120, 70), (180, 255, 255))],
    "green": [((40, 90, 60), (80, 255, 255))],
}
DEFAULT_COLOR = load_rig().get("dice_color", "red")


def color_mask(bgr: np.ndarray, color: str | None = None) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    m = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in COLORS[color or DEFAULT_COLOR]:
        m = cv2.bitwise_or(m, cv2.inRange(hsv, lo, hi))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))  # fill the black dots
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))


def red_mask(bgr: np.ndarray) -> np.ndarray:
    return color_mask(bgr, "red")


def find_dice(bgr, roi=None, prev=None, min_area=60, max_jump=140, color=None):
    """Return (cx, cy, area_px, bbox) of the best blob of the dice colour, or None.

    roi=(x0, y0, x1, y1): only blobs whose centroid lies inside are accepted.
    prev=(cx, cy): when given, pick the blob nearest to it (and reject jumps over max_jump px).
    color: "red" / "green"; None = rig.json "dice_color".
    """
    m = color_mask(bgr, color)
    n, _, stats, cents = cv2.connectedComponentsWithStats(m)
    best = None
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        cx, cy = cents[i]
        if a < min_area:
            continue
        cut = y + h >= m.shape[0] - 1  # close to the grasp the dice runs off the bottom edge: not square any more
        if not cut and (max(w, h) > 1.6 * min(w, h) or a < 0.4 * w * h):  # a dice is a filled near-square
            continue
        if roi and not (roi[0] <= cx <= roi[2] and roi[1] <= cy <= roi[3]):
            continue
        if prev is not None:
            d = float(np.hypot(cx - prev[0], cy - prev[1]))
            if d > max_jump:
                continue
            score = -d
        else:
            score = a
        if best is None or score > best[0]:
            best = (score, float(cx), float(cy), int(a), (int(x), int(y), int(w), int(h)))
    return None if best is None else best[1:]
