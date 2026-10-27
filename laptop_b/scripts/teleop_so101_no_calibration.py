"""Relative leader/follower teleop using raw encoder positions; no calibration writes.

Both arms retain their starting offset. Body travel is limited to +/-20 degrees,
and gripper travel to +/-20% of its range. No software target speed limit is applied.
All commanded motors follow the same direction as the leader displacement.
Existing motor position limits are respected. Q, Escape, or Ctrl+C stops.
"""
import argparse
import msvcrt
import time

from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus

NAMES = ('shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper')


def make_bus(port, exclude_wrist_roll=False, exclude_elbow=False):
    return FeetechMotorsBus(port=port, motors={
        name: Motor(i, 'sts3215', MotorNormMode.DEGREES)
        for i, name in enumerate(NAMES, 1)
        if not (exclude_wrist_roll and name == 'wrist_roll')
        and not (exclude_elbow and name == 'elbow_flex')
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--leader-port', default='COM12')
    parser.add_argument('--follower-port', default='COM13')
    parser.add_argument('--seconds', type=float, default=60, help='Duration in seconds; 0 runs until interrupted')
    parser.add_argument('--run', action='store_true', help='Enable movement; otherwise read-only check')
    parser.add_argument('--exclude-wrist-roll', action='store_true', help='Do not command motor ID 5')
    parser.add_argument('--exclude-elbow', action='store_true', help='Exclude motor ID 3 from reads, goals and torque control')
    parser.add_argument('--recover-near-limit', action='store_true', help='Allow up to 5deg startup correction into stored motor limits')
    args = parser.parse_args()
    if args.seconds < 0 or args.leader_port == args.follower_port:
        parser.error('Use distinct ports and a non-negative duration (0 means unlimited).')
    leader = make_bus(args.leader_port, args.exclude_wrist_roll, args.exclude_elbow)
    follower = make_bus(args.follower_port, args.exclude_wrist_roll, args.exclude_elbow)
    active_names = tuple(follower.motors)
    active = False
    try:
        leader.connect()
        follower.connect()
        modes = follower.sync_read('Operating_Mode', normalize=False)
        if any(mode != 0 for mode in modes.values()):
            raise RuntimeError('Follower must already be in position mode (0).')
        lows = follower.sync_read('Min_Position_Limit', normalize=False)
        highs = follower.sync_read('Max_Position_Limit', normalize=False)
        leader_lows = leader.sync_read('Min_Position_Limit', normalize=False)
        leader_highs = leader.sync_read('Max_Position_Limit', normalize=False)
        start_l = leader.sync_read('Present_Position', normalize=False)
        start_f = follower.sync_read('Present_Position', normalize=False)
        for name in active_names:
            if not 0 <= lows[name] < highs[name] <= 4095:
                raise RuntimeError(f'Invalid follower limits: {name}')
            distance = max(lows[name] - start_f[name], start_f[name] - highs[name], 0)
            if distance and not (args.recover_near_limit and distance <= 56):
                raise RuntimeError(f'Follower outside motor limits: {name}')
        span_l = leader_highs['gripper'] - leader_lows['gripper']
        span_f = highs['gripper'] - lows['gripper']
        if span_l <= 0:
            raise RuntimeError('Invalid leader gripper range.')
        print(f'Leader {args.leader_port}; follower {args.follower_port}', flush=True)
        print('Leader starting position:', start_l, flush=True)
        print('Follower starting position:', start_f, flush=True)
        if not args.run:
            print('Read-only check passed. Add --run to start.', flush=True)
            return
        leader.disable_torque(num_retry=3)
        # Read fresh reference positions, then hold the current follower pose.
        start_l = leader.sync_read('Present_Position', normalize=False)
        start_f = follower.sync_read('Present_Position', normalize=False)
        for name in active_names:
            distance = max(lows[name] - start_f[name], start_f[name] - highs[name], 0)
            if distance and not (args.recover_near_limit and distance <= 56):
                raise RuntimeError(f'Follower moved outside limits before startup: {name}')
        statuses = follower.sync_read('Status', normalize=False)
        if any(statuses.values()):
            raise RuntimeError(f'Follower reports motor errors: {statuses}')
        startup_goal = {n: max(lows[n], min(highs[n], p)) for n, p in start_f.items()}
        # Aim slightly inside the range so ordinary servo error does not leave
        # the measured position just beyond the boundary; total move stays <=5deg.
        for name, position in start_f.items():
            if position < lows[name]:
                inset = max(0, min(11, 56 - (lows[name] - position)))
                startup_goal[name] = min(highs[name], lows[name] + inset)
            elif position > highs[name]:
                inset = max(0, min(11, 56 - (position - highs[name])))
                startup_goal[name] = max(lows[name], highs[name] - inset)
        recovering = startup_goal != start_f
        active = True
        follower.sync_write('Goal_Position', startup_goal, normalize=False)
        follower.enable_torque(num_retry=3)
        torque_state = follower.sync_read('Torque_Enable', normalize=False, num_retry=3)
        if any(value != 1 for value in torque_state.values()):
            raise RuntimeError(f'Follower torque did not enable: {torque_state}')
        print('Follower torque enabled:', torque_state, flush=True)
        if recovering:
            print('Correcting startup pose into stored limits (at most 5deg).', flush=True)
            settled = False
            for _ in range(30):
                time.sleep(0.1)
                positions = follower.sync_read('Present_Position', normalize=False)
                if all(lows[n] - 4 <= positions[n] <= highs[n] + 4 for n in active_names):
                    settled = True
                    break
            if not settled:
                raise RuntimeError(f'Startup correction did not settle: {positions}')
            start_f = dict(startup_goal)
            start_l = leader.sync_read('Present_Position', normalize=False)
        duration_label = 'until interrupted' if args.seconds == 0 else f'for {args.seconds:g}s'
        print(f'TELEOP ACTIVE {duration_label}. Move leader slowly. Ctrl+C stops.', flush=True)
        print('Follower torque will release on exit; support the arm.', flush=True)
        print('Travel limits ON: body +/-20deg, gripper +/-20%. Software speed limit OFF. Q/Esc stops.', flush=True)
        print('Motor ID 5 excluded:', args.exclude_wrist_roll, flush=True)
        print('Motor ID 3 excluded:', args.exclude_elbow, flush=True)
        deadline = None if args.seconds == 0 else time.monotonic() + args.seconds
        next_report = 0
        while deadline is None or time.monotonic() < deadline:
            if msvcrt.kbhit():
                key = msvcrt.getwch().lower()
                if key in ('q', '\x1b', '\x03'):
                    break
                if key in ('\x00', '\xe0'):
                    msvcrt.getwch()
            tick = time.monotonic()
            lp = leader.sync_read('Present_Position', normalize=False, num_retry=3)
            fp = follower.sync_read('Present_Position', normalize=False, num_retry=3)
            goals = {}
            for name in active_names:
                delta = lp[name] - start_l[name]
                # Shortest direction across the full-turn wrist encoder boundary.
                if name == 'wrist_roll':
                    delta = (delta + 2048) % 4096 - 2048
                window = 227
                if name == 'gripper':
                    delta *= span_f / span_l
                    window = max(1, int(span_f * 0.20))
                target = start_f[name] + max(-window, min(window, delta))
                lower = max(lows[name], start_f[name] - window)
                upper = min(highs[name], start_f[name] + window)
                goals[name] = int(max(lower, min(upper, target)))
            follower.sync_write('Goal_Position', goals, normalize=False)
            if tick >= next_report:
                status = 'Running | ' if deadline is None else 'Remaining %.0fs | ' % max(0, deadline - tick)
                print(status +
                      ' '.join(f'{n}={fp[n]}' for n in active_names), flush=True)
                next_report = tick + 2
            time.sleep(max(0, 0.05 - (time.monotonic() - tick)))
    finally:
        # Close both ports even if disabling torque fails on one bus.
        try:
            if follower.is_connected:
                try:
                    follower.disconnect(disable_torque=active)
                finally:
                    if follower.port_handler.is_open:
                        follower.port_handler.closePort()
        finally:
            if leader.is_connected:
                leader.disconnect(disable_torque=False)
        print('Stopped; ports closed.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted.', flush=True)
