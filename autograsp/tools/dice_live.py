"""Live red-dice detection overlay on the wrist camera (camera only: never touches the motors).

    python autograsp/tools/dice_live.py            # keys: q / Esc = quit
Green ring = detected dice, blue = grasp goal (centre + size from the 9 demos), yellow = static red marker ignored.
"""

from __future__ import annotations

import argparse
import time

import cv2

from common import load_rig
from dice_detect import find_dice

GOAL = (365, 375, 30000)  # cx, cy, area_px of the dice at the grasp moment in the demos


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, default=None)
    ap.add_argument("--min-area", type=int, default=300)
    args = ap.parse_args()
    rig = load_rig()
    c = rig["cameras"]["wrist"]
    cap = cv2.VideoCapture(args.index if args.index is not None else c["index_or_path"], c.get("backend", cv2.CAP_DSHOW))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, c["width"]); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, c["height"])
    prev, t0, n = None, time.time(), 0
    while True:
        ok, f = cap.read()
        if not ok:
            time.sleep(0.05); continue
        d = find_dice(f, prev=prev, min_area=args.min_area) or find_dice(f, min_area=args.min_area)
        prev = None if d is None else (d[0], d[1])
        cv2.circle(f, (GOAL[0], GOAL[1]), int((GOAL[2] / 3.14159) ** 0.5), (255, 120, 0), 2)
        if d:
            cv2.circle(f, (int(d[0]), int(d[1])), 16, (0, 255, 0), 3)
            msg = f"dice cx={d[0]:.0f} cy={d[1]:.0f} area={d[2]}"
        else:
            msg = "no dice"
        n += 1
        cv2.putText(f, msg, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.imshow("dice_live", f)
        if cv2.waitKey(1) & 0xFF in (27, ord("q")):
            break
    cv2.destroyAllWindows(); cap.release()


if __name__ == "__main__":
    main()
