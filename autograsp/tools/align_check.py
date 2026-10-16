"""Live leader-vs-follower joint difference (read-only), to align the leader before teleoperation.

    python autograsp/tools/align_check.py
Turn the leader joints until every row says OK, then close the window (Ctrl+C).
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from common import load_rig

BASE = Path.home() / ".cache/huggingface/lerobot/calibration"
NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
TOL = {"gripper": 15.0}  # 0-100 units; body joints use 10 deg


def bus_for(port: str, cal_file: Path):
    from lerobot.motors import Motor, MotorCalibration, MotorNormMode
    from lerobot.motors.feetech import FeetechMotorsBus

    cal = {k: MotorCalibration(**v) for k, v in json.loads(cal_file.read_text()).items()}
    motors = {n: Motor(i + 1, "sts3215", MotorNormMode.DEGREES) for i, n in enumerate(NAMES[:5])}
    motors["gripper"] = Motor(6, "sts3215", MotorNormMode.RANGE_0_100)
    bus = FeetechMotorsBus(port=port, motors=motors, calibration=cal)
    bus.connect(handshake=True)
    return bus


def main() -> None:
    rig = load_rig()
    fol = bus_for(rig["follower"]["port"], BASE / f"robots/so_follower/{rig['follower']['id']}.json")
    lead = bus_for(rig["leader"]["port"], BASE / f"teleoperators/so_leader/{rig['leader']['id']}.json")
    try:
        while True:
            f, l = fol.sync_read("Present_Position"), lead.sync_read("Present_Position")
            os.system("cls")
            print("리더를 follower 자세에 맞추세요 (읽기 전용, Ctrl+C로 종료)\n")
            print(f"{'joint':14s}{'follower':>10s}{'leader':>10s}{'diff':>9s}")
            all_ok = True
            for n in NAMES:
                d = l[n] - f[n]
                if n == "wrist_roll":
                    d = ((d + 180) % 360) - 180
                ok = abs(d) <= TOL.get(n, 10.0)
                all_ok &= ok
                hint = "" if ok else ("  <- 리더를 " + ("줄이는" if d > 0 else "늘리는") + " 방향으로")
                print(f"{n:14s}{f[n]:10.1f}{l[n]:10.1f}{d:9.1f}  {'OK' if ok else '맞추세요'}{hint}")
            print("\n" + ("모두 OK - 텔레오퍼레이션을 시작해도 됩니다. 이 창을 닫아 주세요." if all_ok else ""))
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        fol.disconnect(disable_torque=False)
        lead.disconnect(disable_torque=False)


if __name__ == "__main__":
    main()
