import time

from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus, OperatingMode


PORT = "COM8"
MOTORS = {
    "wrist_roll": Motor(5, "sts3215", MotorNormMode.DEGREES),
    "gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
}
RAW_STEP = {
    "wrist_roll": 120,
    "gripper": 80,
}


def choose_target(current: int, step: int) -> int:
    target = current + step
    if target > 3900:
        target = current - step
    if target < 150:
        target = current + step
    return max(0, min(4095, target))


def main() -> None:
    bus = FeetechMotorsBus(port=PORT, motors=MOTORS)
    bus.connect()
    try:
        for name, step in RAW_STEP.items():
            print(f"\nRaw test {name}. Keep a hand near power. Press ENTER to move a tiny raw step.")
            input()
            current = int(bus.sync_read("Present_Position", [name], normalize=False)[name])
            target = choose_target(current, step)
            print(f"{name}: raw current={current}, raw target={target}")
            bus.write("Operating_Mode", name, OperatingMode.POSITION.value, normalize=False, num_retry=3)
            bus.write("Torque_Limit", name, 350, normalize=False, num_retry=3)
            bus.enable_torque(name, num_retry=3)
            bus.sync_write("Goal_Position", {name: target}, normalize=False)
            time.sleep(1.0)
            after = int(bus.sync_read("Present_Position", [name], normalize=False)[name])
            print(f"{name}: raw after={after}, raw moved={after - current}")
            try:
                bus.disable_torque(name, num_retry=3)
            except Exception as exc:
                print(f"{name}: disable torque warning: {exc}")
    finally:
        bus.disconnect(disable_torque=False)


if __name__ == "__main__":
    main()
