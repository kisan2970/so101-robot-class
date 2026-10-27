"""Windows follower-only joint control. Default: read-only connection check."""
import argparse
import json
import msvcrt
import time
from pathlib import Path

from lerobot.motors import Motor, MotorCalibration, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus, OperatingMode
from lerobot.utils.constants import HF_LEROBOT_CALIBRATION

NAMES = ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default='COM13')
    parser.add_argument('--id', help='Calibration ID; otherwise match saved files to motor settings')
    parser.add_argument('--run', action='store_true', help='Enable interactive movement')
    args = parser.parse_args()
    motors = {name: Motor(i, 'sts3215', MotorNormMode.RANGE_0_100 if name == 'gripper'
                         else MotorNormMode.DEGREES) for i, name in enumerate(NAMES, 1)}
    bus = FeetechMotorsBus(port=args.port, motors=motors)
    active = False
    try:
        bus.connect()
        directory = Path(HF_LEROBOT_CALIBRATION) / 'robots' / 'so_follower'
        paths = [directory / f'{args.id}.json'] if args.id else sorted(directory.glob('*.json'))
        matched = None
        for path in paths:
            raw = json.loads(path.read_text(encoding='utf-8'))
            bus.calibration = {name: MotorCalibration(**raw[name]) for name in NAMES}
            if bus.is_calibrated:
                matched = path
                break
        if matched is None:
            raise RuntimeError('No matching saved calibration. Run lerobot-calibrate first; do not guess the ID.')
        print(f'Port: {args.port}; matching calibration ID: {matched.stem}')
        positions = bus.sync_read('Present_Position')
        print('Positions:', positions)
        if not args.run:
            print('Read-only check complete. Add --run for keyboard control.')
            return
        limits = {}
        for name in NAMES:
            cal = bus.calibration[name]
            if name == 'gripper':
                limits[name] = (0.0, 100.0)
            else:
                extent = (cal.range_max - cal.range_min) * 180 / 4095
                limits[name] = (-extent, extent)
            if not limits[name][0] <= positions[name] <= limits[name][1]:
                raise RuntimeError(f'{name} is outside its calibrated range. Reposition/calibrate first.')
        print('Support the arm: torque is disabled during startup and on exit.')
        print('1-6: select joint; A/D: -/+1 degree (gripper: 1%); Q/Esc: exit.')
        input('Clear the workspace and press Enter to begin: ')
        active = True
        bus.disable_torque()
        for name in NAMES:
            bus.write('Operating_Mode', name, OperatingMode.POSITION.value)
        # Capture the supported pose immediately before enabling torque.
        bus.sync_write('Goal_Position', bus.sync_read('Present_Position'))
        bus.enable_torque()
        selected = NAMES[0]
        print('Selected:', selected)
        while True:
            if not msvcrt.kbhit():
                time.sleep(0.02)
                continue
            key = msvcrt.getwch().lower()
            if key in ('\x00', '\xe0'):
                msvcrt.getwch()
                continue
            if key in ('q', '\x1b', '\x03'):
                break
            if key in '123456':
                selected = NAMES[int(key) - 1]
                print('Selected:', selected)
            elif key in ('a', 'd'):
                current = bus.read('Present_Position', selected)
                low, high = limits[selected]
                target = max(low, min(high, current + (1 if key == 'd' else -1)))
                bus.write('Goal_Position', selected, target)
                print(f'{selected}: {current:.2f} -> {target:.2f}')
                time.sleep(0.10)
                # Discard queued repeat keys so motion stops with released keys.
                while msvcrt.kbhit():
                    buffered = msvcrt.getwch().lower()
                    if buffered in ('q', '\x1b', '\x03'):
                        return
    finally:
        if bus.is_connected:
            try:
                bus.disconnect(disable_torque=active)
            finally:
                if bus.port_handler.is_open:
                    bus.port_handler.closePort()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nStopped.')
