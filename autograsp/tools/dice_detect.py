"""Red-dice detector for the wrist camera (BGR frames, 640x480).

The dice is a saturated red cube. A static red/black marker also sits near the top of the scene, so detection
accepts an optional ROI polygon/rect and a previous position (tracking) to stay on the dice.
"""

from __future__ import annotations

import cv2
import numpy as np


def red_mask(bgr: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    lo = cv2.inRange(hsv, (0, 120, 70), (8, 255, 255))
    hi = cv2.inRange(hsv, (172, 120, 70), (180, 255, 255))
    m = cv2.bitwise_or(lo, hi)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))  # fill the black dots
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))


def find_dice(bgr, roi=None, prev=None, min_area=60, max_jump=140):
    """Return (cx, cy, area_px, bbox) of the best red blob, or None.

    roi=(x0, y0, x1, y1): only blobs whose centroid lies inside are accepted.
    prev=(cx, cy): when given, pick the blob nearest to it (and reject jumps over max_jump px).
    """
    m = red_mask(bgr)
    n, _, stats, cents = cv2.connectedComponentsWithStats(m)
    best = None
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        cx, cy = cents[i]
        if a < min_area:
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
