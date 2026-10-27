import json
import time
from pathlib import Path

from lerobot.motors import Motor, MotorCalibration, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus


LEADER_PORT = "COM7"
FOLLOWER_PORT = "COM8"
LEADER_ID = "my_so101_leader"
FOLLOWER_ID = "my_so101_follower"
FPS = 20
MAX_STEP_DEG = 3.0
RUN_SECONDS = 20
MOTORS = {
    "shoulder_pan": Motor(1, "sts3215", MotorNormMode.DEGREES),
    "shoulder_lift": Motor(2, "sts3215", MotorNormMode.DEGREES),
    "elbow_flex": Motor(3, "sts3215", MotorNormMode.DEGREES),
    "wrist_flex": Motor(4, "sts3215", MotorNormMode.DEGREES),
}


def load_calibration(kind: str, arm_id: str) -> dict[str, MotorCalibration]:
    base = Path.home() / ".cache" / "huggingface" / "lerobot" / "calibration"
    device_type = "so_leader" if kind == "teleoperators" else "so_follower"
    with (base / kind / device_type / f"{arm_id}.json").open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return {name: MotorCalibration(**raw[name]) for name in MOTORS}


def make_bus(port: str, calibration: dict[str, MotorCalibration]) -> FeetechMotorsBus:
    return FeetechMotorsBus(port=port, motors=MOTORS, calibration=calibration)


def clipped_step(current: dict[str, float], target: dict[str, float]) -> dict[str, float]:
    goal = {}
    for name in MOTORS:
        delta = target[name] - current[name]
        if delta > MAX_STEP_DEG:
            delta = MAX_STEP_DEG
        elif delta < -MAX_STEP_DEG:
            delta = -MAX_STEP_DEG
        goal[name] = current[name] + delta
    return goal


def main() -> None:
    leader_calib = load_calibration("teleoperators", LEADER_ID)
    follower_calib = load_calibration("robots", FOLLOWER_ID)
    leader = make_bus(LEADER_PORT, leader_calib)
    follower = make_bus(FOLLOWER_PORT, follower_calib)

    leader.connect()
    follower.connect()
    try:
        follower.enable_torque(list(MOTORS), num_retry=3)
        print("Safe 1-4 teleop started. ID 5/6 are not commanded by this script.")
        print("Press Ctrl+C to stop.\n")
        period = 1.0 / FPS
        deadline = time.monotonic() + RUN_SECONDS
        while time.monotonic() < deadline:
            started = time.monotonic()
            leader_pos = leader.sync_read("Present_Position", list(MOTORS))
            follower_pos = follower.sync_read("Present_Position", list(MOTORS))
            goal = clipped_step(follower_pos, leader_pos)
            follower.sync_write("Goal_Position", goal)
            print(
                "  ".join(
                    f"{name}:{follower_pos[name]:7.1f}->{goal[name]:7.1f}"
                    for name in MOTORS
                )
            )
            time.sleep(max(0.0, period - (time.monotonic() - started)))
    finally:
        follower.disconnect(disable_torque=True)
        leader.disconnect(disable_torque=False)


if __name__ == "__main__":
    main()
