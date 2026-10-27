from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus


PORT = "COM8"
MOTORS = {
    "wrist_roll": Motor(5, "sts3215", MotorNormMode.DEGREES),
    "gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
}
FIELDS = [
    "Operating_Mode",
    "Torque_Enable",
    "Lock",
    "Present_Position",
    "Present_Load",
    "Present_Voltage",
    "Present_Temperature",
    "Status",
    "Moving",
    "Present_Current",
]


def main() -> None:
    bus = FeetechMotorsBus(port=PORT, motors=MOTORS)
    bus.connect()
    try:
        for field in FIELDS:
            try:
                values = bus.sync_read(field, list(MOTORS), normalize=False)
                print(f"{field}: {values}")
            except Exception as exc:
                print(f"{field}: ERROR {exc}")
    finally:
        bus.disconnect(disable_torque=False)


if __name__ == "__main__":
    main()
