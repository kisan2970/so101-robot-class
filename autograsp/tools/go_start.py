"""Move the follower to the FIXED start pose (rig.json start_pose), then help line the leader up with it.

    python autograsp/tools/go_start.py            # follower -> start pose, then wait for the leader to match
    python autograsp/tools/go_start.py --follower-only

1. The follower drives itself there at a limited speed (torque stays on afterwards, so it does not drop).
2. The leader cannot be moved by software: the live table shows how far each leader joint is from the start
   pose and turns OK when it is within tolerance. Exit code 0 = both arms are at the start pose.
record_sector.py --go-start runs this before every block, so each block begins from the same pose.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from align_check import BASE, NAMES, bus_for
from common import CONFIG_DIR, load_rig

TOL = {"gripper": 15.0}  # body joints use --tol degrees


def start_goal(rig) -> dict[str, float]:
    goal = {n: float(v) for n, v in rig["start_pose"].items() if n in NAMES}
    safety = CONFIG_DIR / "safety.json"
    grip = 0.0
    if safety.exists():
        grip = float(json.loads(safety.read_text(encoding="utf-8"))["rest_pose"].get("gripper", 0.0))
    goal.setdefault("gripper", grip)
    return goal


def drive_follower(fol, goal, speed_deg_s: float, timeout_s: float) -> bool:
    cur = fol.sync_read("Present_Position")
    cmd = dict(cur)  # integrate the goal; comparing to the measured pose would stall under gravity sag
    fol.sync_write("Goal_Position", cmd)
    fol.enable_torque()
    step, dt = speed_deg_s / 30, 1 / 30
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        err = {n: goal[n] - cmd[n] for n in NAMES}
        if max(abs(e) for e in err.values()) < 0.5:
            time.sleep(0.5)
            now = fol.sync_read("Present_Position")
            lag = {n: round(goal[n] - now[n], 1) for n in NAMES}
            print(f"follower at start pose (remaining servo lag: {lag})")
            return True
        cmd = {n: cmd[n] + max(-step, min(step, err[n])) for n in NAMES}
        fol.sync_write("Goal_Position", cmd)
        time.sleep(dt)
    print("follower did not reach the start pose in time")
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--speed", type=float, default=25.0, help="follower speed, deg/s")
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--tol", type=float, default=10.0, help="leader tolerance for body joints, degrees")
    ap.add_argument("--follower-only", action="store_true", help="do not wait for the leader")
    args = ap.parse_args()

    rig = load_rig()
    goal = start_goal(rig)
    print("start pose:", {k: round(v, 1) for k, v in goal.items()})
    fol = bus_for(rig["follower"]["port"], BASE / f"robots/so_follower/{rig['follower']['id']}.json")
    lead = None
    try:
        if not drive_follower(fol, goal, args.speed, args.timeout):
            sys.exit(1)
        if args.follower_only:
            return
        lead = bus_for(rig["leader"]["port"], BASE / f"teleoperators/so_leader/{rig['leader']['id']}.json")
        ok_since = None
        while True:
            l = lead.sync_read("Present_Position")
            os.system("cls")
            print("리더를 follower(시작 자세)에 맞추세요. 모두 OK가 1초 유지되면 자동 종료 (Ctrl+C 취소)\n")
            print(f"{'joint':14s}{'start':>9s}{'leader':>9s}{'diff':>8s}")
            all_ok = True
            for n in NAMES:
                d = l[n] - goal[n]
                ok = abs(d) <= TOL.get(n, args.tol)
                all_ok &= ok
                hint = "" if ok else ("  <- 줄이세요" if d > 0 else "  <- 늘리세요")
                print(f"{n:14s}{goal[n]:9.1f}{l[n]:9.1f}{d:8.1f}  {'OK' if ok else '맞추세요'}{hint}")
            ok_since = (ok_since or time.time()) if all_ok else None
            if ok_since and time.time() - ok_since >= 1.0:
                print("\n두 팔 모두 시작 자세입니다.")
                return
            time.sleep(0.2)
    except KeyboardInterrupt:
        sys.exit(130)
    finally:
        fol.disconnect(disable_torque=False)  # keep holding the pose
        if lead is not None:
            lead.disconnect(disable_torque=False)


if __name__ == "__main__":
    main()
