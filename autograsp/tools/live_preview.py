"""Live camera preview with joint angles overlaid (read-only: never enables torque or writes goals).

Camera and motor reads run in background threads, so the window and keys keep working even if the
camera driver hangs inside read(). A frame older than 1 s is shown as STALLED and the camera is reopened;
each stall is logged to runs/cam_bench/stalls.log (useful to diagnose cable / USB problems).

    python autograsp/tools/live_preview.py --index 1
Keys (click the window first):  s = save snapshot (+ pose json)   q / Esc = quit
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from pathlib import Path

import cv2
import numpy as np

from common import AUTOGRASP, load_rig

OUT = AUTOGRASP / "runs" / "cam_bench"


def open_bus(rig):
    from lerobot.motors import Motor, MotorCalibration, MotorNormMode
    from lerobot.motors.feetech import FeetechMotorsBus

    cal_path = (Path.home() / ".cache/huggingface/lerobot/calibration/robots/so_follower"
                / f"{rig['follower']['id']}.json")
    cal = {k: MotorCalibration(**v) for k, v in json.loads(cal_path.read_text()).items()}
    d = MotorNormMode.DEGREES
    names = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
    motors = {n: Motor(i + 1, "sts3215", d) for i, n in enumerate(names)}
    motors["gripper"] = Motor(6, "sts3215", MotorNormMode.RANGE_0_100)
    bus = FeetechMotorsBus(port=rig["follower"]["port"], motors=motors, calibration=cal)
    bus.connect(handshake=True)
    return bus


class CameraThread:
    """Keeps the newest frame; a hung read() only blocks this thread, never the UI."""

    def __init__(self, index: int):
        self.index = index
        self.lock = threading.Lock()
        self.frame, self.stamp = None, 0.0
        self.stop = threading.Event()
        self.gen = 0  # incremented on every reopen; a hung old thread notices and exits
        self.reopens = 0
        self.fps, self._times = 0.0, []
        self._start()

    def _start(self):
        self.gen += 1
        threading.Thread(target=self._run, args=(self.gen,), daemon=True).start()

    def _run(self, gen: int):
        cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
        cap.set(3, 640)
        cap.set(4, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        while not self.stop.is_set() and gen == self.gen:
            ok, f = cap.read()
            if ok and gen == self.gen:
                now = time.time()
                self._times = [t for t in self._times if now - t < 1.0] + [now]
                with self.lock:
                    self.frame, self.stamp, self.fps = f, now, float(len(self._times))
        cap.release()

    def latest(self):
        with self.lock:
            return self.frame, self.stamp

    def reopen(self):
        self.reopens += 1
        with self.lock:
            self.stamp = time.time()  # give the new stream a grace period
        self._start()


class PoseThread:
    def __init__(self, bus):
        self.bus, self.pose = bus, {}
        self.stop = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while not self.stop.is_set():
            try:
                self.pose = {m: round(v, 1) for m, v in self.bus.sync_read("Present_Position").items()}
            except Exception as e:
                self.pose = {"bus_error": str(e)[:40]}
            time.sleep(0.2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, default=1)
    ap.add_argument("--minutes", type=float, default=20)
    ap.add_argument("--no-arm", action="store_true")
    args = ap.parse_args()
    rig = load_rig()
    OUT.mkdir(parents=True, exist_ok=True)
    bus = None if args.no_arm else open_bus(rig)
    pose_t = PoseThread(bus) if bus else None
    cam = CameraThread(args.index)
    win = "wrist camera  (click, then s=save  q=quit)"
    stall_log = OUT / "stalls.log"
    t_end, stalled_since, last_reopen = time.time() + args.minutes * 60, None, 0.0
    try:
        while time.time() < t_end:
            frame, stamp = cam.latest()
            age = time.time() - stamp if stamp else None
            pose = pose_t.pose if pose_t else {}
            view = frame.copy() if frame is not None else np.zeros((480, 640, 3), np.uint8)
            src_h, src_w = view.shape[:2]
            if (src_w, src_h) != (640, 480):  # camera fell into a low-res mode: show it big, log once
                view = cv2.resize(view, (640, 480), interpolation=cv2.INTER_NEAREST)
            h, w = view.shape[:2]
            bad = (src_w, src_h) != (640, 480) or (frame is not None and cam.fps < 20)
            cv2.putText(view, f"{src_w}x{src_h} {cam.fps:.0f}fps", (w - 170, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (0, 0, 255) if bad else (0, 255, 0), 2)
            if bad and frame is not None and not getattr(cam, "_bad_logged", False):
                cam._bad_logged = True
                msg = f"{time.strftime('%H:%M:%S')} degraded {src_w}x{src_h} {cam.fps:.0f}fps pose={pose}"
                print(msg, flush=True)
                with open(stall_log, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            elif not bad:
                cam._bad_logged = False
            cv2.line(view, (w // 2, 0), (w // 2, h), (0, 255, 0), 1)
            cv2.line(view, (0, h // 2), (w, h // 2), (0, 255, 0), 1)
            cv2.rectangle(view, (0, h - 22), (w, h), (0, 0, 0), -1)
            cv2.putText(view, "  ".join(f"{k[:6]}={v}" for k, v in pose.items()), (5, h - 7),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255), 1)
            if age is None or age > 1.0:
                if stalled_since is None:
                    stalled_since = time.time()
                    msg = f"{time.strftime('%H:%M:%S')} stall pose={pose}"
                    print(msg, flush=True)
                    with open(stall_log, "a", encoding="utf-8") as f:
                        f.write(msg + "\n")
                cv2.putText(view, f"CAMERA STALLED {time.time() - stalled_since:.0f}s - reopening (#{cam.reopens})",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)
                if time.time() - stalled_since > 2.0 and time.time() - last_reopen > 3.0:
                    last_reopen = time.time()
                    cam.reopen()
            else:
                if stalled_since is not None:
                    print(f"{time.strftime('%H:%M:%S')} recovered after {time.time() - stalled_since:.1f}s",
                          flush=True)
                stalled_since = None
            cv2.imshow(win, view)
            k = cv2.waitKey(30) & 0xFF
            if k in (ord("q"), 27):
                break
            if k == ord("s") and frame is not None:
                stamp_s = time.strftime("%H%M%S")
                cv2.imwrite(str(OUT / f"preview_{stamp_s}.jpg"), frame)
                (OUT / f"preview_{stamp_s}.json").write_text(json.dumps(pose, indent=1), encoding="utf-8")
                print(f"saved preview_{stamp_s}.jpg {pose}", flush=True)
                cv2.putText(view, "SAVED", (w - 110, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.imshow(win, view)
                cv2.waitKey(300)
    finally:
        cam.stop.set()
        if pose_t:
            pose_t.stop.set()
        cv2.destroyAllWindows()
        if bus is not None:
            time.sleep(0.3)
            bus.disconnect(disable_torque=False)


if __name__ == "__main__":
    main()
