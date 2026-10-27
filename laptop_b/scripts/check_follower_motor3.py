"""Bounded ID3 motion diagnosis: about 5 degrees away from the upper limit."""
import time

from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus


def main():
    name = 'elbow_flex'
    bus = FeetechMotorsBus(port='COM12', motors={name: Motor(3, 'sts3215', MotorNormMode.DEGREES)})
    active = False
    try:
        bus.connect()
        if bus.read('Status', name, normalize=False) != 0:
            raise RuntimeError('Motor reports an error; no motion attempted.')
        if bus.read('Operating_Mode', name, normalize=False) != 0:
            raise RuntimeError('Motor is not in position mode.')
        start = bus.read('Present_Position', name, normalize=False)
        low = bus.read('Min_Position_Limit', name, normalize=False)
        high = bus.read('Max_Position_Limit', name, normalize=False)
        if not low <= start <= high:
            raise RuntimeError('Start is outside stored limits.')
        target = max(low, start - 57)
        print(f'Start={start}, target={target}, stored limits={low}..{high}', flush=True)
        bus.write('Goal_Position', name, start, normalize=False)
        active = True
        bus.enable_torque()
        goal = start
        for _ in range(32):
            goal = max(target, goal - 5)
            bus.write('Goal_Position', name, goal, normalize=False)
            time.sleep(0.05)
            position = bus.read('Present_Position', name, normalize=False)
            status = bus.read('Status', name, normalize=False)
            if status or abs(position - start) > 114:
                raise RuntimeError(f'Abnormal movement/status: position={position}, status={status}')
        print('End position:', position, flush=True)
        print('Displacement degrees:', round((position - start) * 360 / 4095, 2), flush=True)
        for field in ('Goal_Position', 'Present_Load', 'Present_Current', 'Present_Voltage', 'Present_Temperature', 'Status'):
            print(field, bus.read(field, name, normalize=False), flush=True)
    finally:
        if bus.is_connected:
            try:
                bus.disconnect(disable_torque=active)
            finally:
                if bus.port_handler.is_open:
                    bus.port_handler.closePort()
        print('Test ended; ID3 torque disabled if enabled by this test.', flush=True)


if __name__ == '__main__':
    main()
