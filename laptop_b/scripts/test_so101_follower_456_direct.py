import json
import time
from pathlib import Path

from lerobot.motors import Motor, MotorCalibration, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus, OperatingMode


PORT = "COM8"
FOLLOWER_ID = "my_so101_follower"
TEST_MOTORS = {
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
        / "robots"
        / "so_follower"
        / f"{FOLLOWER_ID}.json"
    )
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return {name: MotorCalibration(**raw[name]) for name in TEST_MOTORS}


def target_for(name: str, value: float) -> float:
    if name == "gripper":
        return value + 15 if value < 50 else value - 15
    return value + 10 if value < 80 else value - 10


def main() -> None:
    bus = FeetechMotorsBus(port=PORT, motors=TEST_MOTORS, calibration=load_calibration())
    bus.connect()
    try:
        for name in TEST_MOTORS:
            print(f"\nTesting {name}. Keep a hand near the power switch.")
            input("Press ENTER to move this motor a small amount, or Ctrl+C to stop...")
            current = bus.sync_read("Present_Position", [name])[name]
            target = target_for(name, current)
            print(f"{name}: current={current:.2f}, target={target:.2f}")
            bus.write("Operating_Mode", name, OperatingMode.POSITION.value, num_retry=3)
            bus.enable_torque(name, num_retry=3)
            bus.sync_write("Goal_Position", {name: target})
            time.sleep(1.0)
            after = bus.sync_read("Present_Position", [name])[name]
            print(f"{name}: after={after:.2f}, moved={after - current:.2f}")
            bus.disable_torque(name, num_retry=3)
    finally:
        try:
            bus.disconnect(disable_torque=False)
        except Exception as exc:
            print(f"Disconnect warning: {exc}")


if __name__ == "__main__":
    main()
