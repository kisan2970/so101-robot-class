import json
import time
from pathlib import Path

from lerobot.motors import Motor, MotorCalibration, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus


PORT = "COM7"
LEADER_ID = "my_so101_leader"
WATCH_MOTORS = {
    "wrist_flex": Motor(4, "sts3215", MotorNormMode.DEGREES),
    "wrist_roll": Motor(5, "sts3215", MotorNormMode.DEGREES),
    "gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
}


def load_calibration() -> dict[str, MotorCalibration]:
    path = (
        Path.home()
        / ".cache"
        / "huggingface"
        / "lerobot"
        / "calibration"
        / "teleoperators"
        / "so_leader"
        / f"{LEADER_ID}.json"
    )
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return {name: MotorCalibration(**raw[name]) for name in WATCH_MOTORS}


def main() -> None:
    bus = FeetechMotorsBus(port=PORT, motors=WATCH_MOTORS, calibration=load_calibration())
    bus.connect()
    try:
        bus.disable_torque(num_retry=3)
        print("Move leader wrist_flex, wrist_roll, and gripper by hand. Press Ctrl+C to stop.\n")
        while True:
            pos = bus.sync_read("Present_Position", list(WATCH_MOTORS))
            print("  ".join(f"{name}={pos[name]:7.2f}" for name in WATCH_MOTORS))
            time.sleep(0.25)
    finally:
        bus.disconnect(disable_torque=False)


if __name__ == "__main__":
    main()
