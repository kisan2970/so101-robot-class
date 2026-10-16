"""Camera discovery + simultaneous-capture benchmark using LeRobot's own OpenCVCamera code path.

    python autograsp/tools/cam_bench.py --scan                 # which indices open, snapshot each
    python autograsp/tools/cam_bench.py --seconds 10           # both rig cameras at once, measure real fps/age

Outputs go to autograsp/runs/cam_bench/. Check the snapshots: can YOU do the task from these views alone?
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

from common import AUTOGRASP, camera_configs, load_rig

OUT = AUTOGRASP / "runs" / "cam_bench"


def scan(max_index: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i in range(max_index):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        ok = cap.isOpened()
        frame = cap.read()[1] if ok else None
        if frame is not None:
            p = OUT / f"scan_index{i}.jpg"
            cv2.imwrite(str(p), frame)
            print(f"index {i}: {frame.shape[1]}x{frame.shape[0]} -> {p}")
        else:
            print(f"index {i}: not available")
        cap.release()


def bench(seconds: float) -> None:
    from lerobot.cameras.opencv.camera_opencv import OpenCVCamera

    rig = load_rig()
    cams = {n: OpenCVCamera(c) for n, c in camera_configs(rig).items()}
    for n, c in cams.items():
        t = time.perf_counter()
        c.connect()
        print(f"{n}: connected in {time.perf_counter() - t:.1f}s")
    period = 1 / rig["control_fps"]
    stats = {n: {"reads": 0, "new": 0, "stale_errors": 0, "read_ms": [], "age_ms": []} for n in cams}
    last = {n: None for n in cams}
    t_end = time.perf_counter() + seconds
    while time.perf_counter() < t_end:
        t0 = time.perf_counter()
        for n, c in cams.items():
            s = stats[n]
            r0 = time.perf_counter()
            try:
                img = c.read_latest(max_age_ms=1000)
            except TimeoutError:
                s["stale_errors"] += 1
                continue
            s["read_ms"].append((time.perf_counter() - r0) * 1e3)
            ts = getattr(c, "latest_timestamp", None)
            if ts is not None:
                s["age_ms"].append((time.perf_counter() - ts) * 1e3)
            s["reads"] += 1
            key = img[::40, ::40].tobytes()
            if key != last[n]:
                s["new"] += 1
                last[n] = key
        time.sleep(max(0.0, period - (time.perf_counter() - t0)))

    frames = []
    report = {}
    for n, c in cams.items():
        s = stats[n]
        img = c.read_latest(max_age_ms=2000)
        frames.append(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        report[n] = {
            "requested": {k: rig["cameras"][n].get(k) for k in ("index_or_path", "width", "height", "fps", "fourcc")},
            "delivered_shape": list(img.shape),
            "distinct_frames_per_s": round(s["new"] / seconds, 1),
            "read_ms_p95": round(float(np.percentile(s["read_ms"], 95)), 2) if s["read_ms"] else None,
            "frame_age_ms_p50": round(float(np.median(s["age_ms"])), 1) if s["age_ms"] else None,
            "frame_age_ms_p95": round(float(np.percentile(s["age_ms"], 95)), 1) if s["age_ms"] else None,
            "stale_errors": s["stale_errors"],
            "mean_brightness": round(float(img.mean()), 1),
        }
        c.disconnect()
    h = min(f.shape[0] for f in frames)
    sheet = np.hstack([cv2.resize(f, (int(f.shape[1] * h / f.shape[0]), h)) for f in frames])
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    cv2.imwrite(str(OUT / f"pair_{stamp}.jpg"), sheet)
    (OUT / f"bench_{stamp}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"snapshot: {OUT / f'pair_{stamp}.jpg'}")
    print("distinct_frames_per_s is a lower bound (static scenes repeat); wave a hand in view while measuring.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--max-index", type=int, default=6)
    ap.add_argument("--seconds", type=float, default=10)
    a = ap.parse_args()
    scan(a.max_index) if a.scan else bench(a.seconds)
