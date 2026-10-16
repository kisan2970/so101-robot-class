"""Pick the red dice and drop it in the left cell with image-based visual servoing (no learned policy).

    python autograsp/tools/servo_pick.py --teach-start        # hand-position the FOLLOWER where it should start
    python autograsp/tools/servo_pick.py --teach-place        # hand-position the FOLLOWER where the dice is released
    python autograsp/tools/servo_pick.py                       # one pick-and-place, asks Enter between phases
    python autograsp/tools/servo_pick.py --auto                # no Enter prompts (after the steps are trusted)

Phases: start pose -> detect dice -> probe the image Jacobian (small joint nudges) -> servo the dice to the
grasp image goal (centre + size seen in the demos) -> close gripper -> start pose -> place pose -> release ->
start pose. Every command goes through the SO101SafeFollower (joint envelope + per-tick step limit).
Esc = hold the arm where it is; Ctrl+C does the same.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time

import cv2
import numpy as np

from common import CONFIG_DIR, camera_configs, enable_plugin, load_rig
from dice_detect import find_dice

ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex"]  # joints the servo may move
GOAL_PX = (365.0, 375.0, 30000.0)  # dice centre + area at the grasp moment in the demos
OPEN_GRIP, CARRY_GRIP, REST_GRIP = 32.0, 4.0, 0.5
DT = 1 / 30


class Abort(RuntimeError):
    pass


def feat(det) -> np.ndarray:
    """(cx, cy, size) with size = 100*ln(sqrt(area)) so all three are in comparable 'pixel-ish' units."""
    return np.array([det[0], det[1], 100.0 * np.log(np.sqrt(max(det[2], 1)))])


GOAL_S = feat((GOAL_PX[0], GOAL_PX[1], GOAL_PX[2]))


class Keys:
    def __init__(self):
        self.stop = threading.Event()
        try:
            from pynput import keyboard

            def on_press(k):
                if k == keyboard.Key.esc:
                    self.stop.set()

            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.start()
        except Exception as e:
            print(f"!! keyboard listener unavailable ({e}); only Ctrl+C can stop the robot")


class Rig:
    def __init__(self, robot, keys, min_area):
        self.robot, self.keys, self.min_area, self.prev = robot, keys, min_area, None

    def check(self):
        if self.keys.stop.is_set():
            self.robot.hold()
            raise Abort("Esc pressed: holding position")

    def read(self):
        self.check()
        obs = self.robot.get_observation()
        q = {m: obs[f"{m}.pos"] for m in [*ARM, "wrist_roll", "gripper"]}
        return q, cv2.cvtColor(obs["wrist"], cv2.COLOR_RGB2BGR)

    def dice(self, img, tracking=True):
        d = find_dice(img, prev=self.prev if tracking else None, min_area=self.min_area)
        if d is None and tracking and self.prev is not None:
            d = find_dice(img, min_area=self.min_area)  # re-acquire anywhere if the track was lost
        self.prev = None if d is None else (d[0], d[1])
        return d

    def send(self, goal: dict):
        self.check()
        self.robot.send_action({f"{m}.pos": float(v) for m, v in goal.items()})

    def move_to(self, target: dict, speed: float, timeout: float = 25.0, tol: float = 1.2):
        """Integrate the goal toward `target` (any subset of joints) at `speed` deg/s."""
        q, _ = self.read()
        goal = dict(q)
        step = speed * DT
        t0 = time.time()
        while time.time() - t0 < timeout:
            self.check()
            err = {m: target[m] - goal[m] for m in target}
            if max(abs(e) for e in err.values()) < 0.3:
                break
            for m in target:
                goal[m] += max(-step, min(step, err[m]))
            self.send(goal)
            time.sleep(DT)
        time.sleep(0.4)
        q, _ = self.read()
        worst = max(abs(target[m] - q[m]) for m in target)
        return worst < max(tol, 6.0)  # servo lag under load is a few degrees; large = blocked

    def grip(self, value: float, speed: float = 60.0):
        q, _ = self.read()
        self.move_to({"gripper": value}, speed, timeout=6.0)


TEACH = {
    "place_pose": "팔로워를 손으로 움직여 주사위가 '왼쪽 칸' 안에 내려놓일 자세로 가만히 두고 Enter: ",
    "start_pose": "팔로워를 손으로 움직여 손목 카메라에 격자 전체와 집게 두 개가 보이는 자세로 가만히 두고 Enter: ",
}


def teach_pose(rig_cfg, key: str) -> None:
    """Hand-position the FOLLOWER (torque off) and store its joint pose in rig.json under `key`."""
    from align_check import BASE, NAMES, bus_for

    lead = bus_for(rig_cfg["follower"]["port"], BASE / f"robots/so_follower/{rig_cfg['follower']['id']}.json")
    try:
        input("팔로워 토크를 풉니다(팔이 처질 수 있으니 손으로 받치세요). 준비되면 Enter: ")
        lead.disable_torque()
        input(TEACH[key])
        reads = [lead.sync_read("Present_Position") for _ in range(15) if time.sleep(0.05) is None]
    finally:
        lead.disconnect(disable_torque=False)
    pose = {n: round(float(np.mean([r[n] for r in reads])), 1) for n in NAMES if n != "gripper"}
    spread = {n: round(float(np.ptp([r[n] for r in reads])), 1) for n in pose}
    print(key, pose, "(hand jitter over 0.75 s:", spread, ")")
    lim = json.loads((CONFIG_DIR / "safety.json").read_text(encoding="utf-8"))["joint_limits"]
    bad = {n: v for n, v in pose.items() if not lim[n][0] <= v <= lim[n][1]}
    if bad:
        sys.exit(f"NOT saved: outside the safety envelope {bad} (limits { {n: lim[n] for n in bad} }). "
                 "Move the arm and try again.")
    path = CONFIG_DIR / "rig.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    d[key] = {**pose, "_source": f"taught by hand-positioning the FOLLOWER (servo_pick.py --teach-{key.split('_')[0]})"}
    path.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"saved to rig.json {key}")


def avg_feat(r: Rig, n: int):
    ss = []
    for _ in range(n):
        d = r.dice(r.read()[1])
        if d is None:
            return None
        ss.append(feat(d))
        time.sleep(0.05)
    return np.mean(ss, axis=0)


def probe_jacobian(r: Rig, delta: float, speed: float) -> np.ndarray:
    """Nudge each arm joint by +delta, watch how (cx, cy, size) change -> J (3 x len(ARM)) in feature/deg."""
    q0, img = r.read()
    if r.dice(img, tracking=False) is None:
        raise Abort("dice not visible at the start pose")
    s_ref = avg_feat(r, 6)
    if s_ref is None:
        raise Abort("dice flickers at the start pose")
    J = np.zeros((3, len(ARM)))
    for k, m in enumerate(ARM):
        r.move_to({m: q0[m] + delta}, speed)
        time.sleep(0.5)
        s_now = avg_feat(r, 6)
        if s_now is None:
            r.move_to({m: q0[m]}, speed)
            raise Abort(f"dice lost while probing {m}")
        J[:, k] = (s_now - s_ref) / delta
        r.move_to({m: q0[m]}, speed)
        time.sleep(0.4)
    print("probed Jacobian (rows cx, cy, size; cols", ARM, ")\n", np.round(J, 2))
    return J


def servo(r: Rig, J: np.ndarray, a) -> bool:
    q_prev, img = r.read()
    s_prev = None
    goal = dict(q_prev)
    ok_ticks, lost, t0 = 0, 0, time.time()
    log = []
    while time.time() - t0 < a.timeout:
        t_tick = time.time()
        q, img = r.read()
        d = r.dice(img)
        if d is None:
            lost += 1
            if lost > 20:
                r.robot.hold()
                raise Abort("dice lost for 20 ticks")
            time.sleep(DT)
            continue
        lost = 0
        s = feat(d)
        err = GOAL_S - s
        if s_prev is not None:  # Broyden rank-1 update of the Jacobian from the measured motion
            dq = np.array([q[m] - q_prev[m] for m in ARM])
            if np.linalg.norm(dq) > 0.3:
                J += a.broyden * np.outer((s - s_prev) - J @ dq, dq) / (dq @ dq)
        q_prev, s_prev = dict(q), s.copy()
        if abs(err[0]) < a.tol_px and abs(err[1]) < a.tol_px and abs(err[2]) < a.tol_size:
            ok_ticks += 1
            if ok_ticks >= 8:
                print(f"converged: dice at ({d[0]:.0f},{d[1]:.0f}) area {d[2]}")
                return True
        else:
            ok_ticks = 0
        if err[2] < -a.tol_size * 2:
            r.robot.hold()
            raise Abort("dice already larger than the grasp size but not centred: too close, stopping")
        dq_cmd = J.T @ np.linalg.solve(J @ J.T + a.damping * np.eye(3), a.gain * err)
        dq_cmd = np.clip(dq_cmd, -a.max_dq, a.max_dq)
        # integrate the goal (do NOT restart from the measured pose each tick: friction/gravity sag swallow a
        # sub-degree offset and the arm never moves); clamp the wind-up so the goal stays near the arm
        for i, m in enumerate(ARM):
            goal[m] = float(np.clip(goal[m] + dq_cmd[i], q[m] - a.windup, q[m] + a.windup))
        goal["wrist_roll"], goal["gripper"] = q["wrist_roll"], q["gripper"]
        r.send(goal)
        log.append((time.time() - t0, *s, *err, *[q[m] for m in ARM]))
        if len(log) % 10 == 0:
            gap = max(abs(goal[m] - q[m]) for m in ARM)
            print(f"  t={log[-1][0]:4.1f}s cx={s[0]:5.0f} cy={s[1]:5.0f} size_err={err[2]:6.1f} area={d[2]} "
                  f"dq={np.round(dq_cmd, 2)} goal-q gap={gap:.1f}")
        time.sleep(max(0, DT - (time.time() - t_tick)))
    r.robot.hold()
    raise Abort("servo timed out without converging")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--teach-place", action="store_true", help="save the follower pose where the dice is released")
    ap.add_argument("--teach-start", action="store_true", help="save the follower pose the servo starts from")
    ap.add_argument("--auto", action="store_true", help="no Enter prompts between phases")
    ap.add_argument("--speed", type=float, default=20.0, help="big moves, deg/s")
    ap.add_argument("--probe-delta", type=float, default=4.0)
    ap.add_argument("--gain", type=float, default=0.35)
    ap.add_argument("--damping", type=float, default=100.0)
    ap.add_argument("--max-dq", type=float, default=1.0, help="max joint change per tick during servo, deg")
    ap.add_argument("--broyden", type=float, default=0.2)
    ap.add_argument("--windup", type=float, default=12.0, help="max distance between the goal and the measured pose, deg")
    ap.add_argument("--timeout", type=float, default=45.0)
    ap.add_argument("--tol-px", type=float, default=25.0)
    ap.add_argument("--tol-size", type=float, default=12.0)
    ap.add_argument("--min-area", type=int, default=300)
    ap.add_argument("--safety-file", default=str(CONFIG_DIR / "safety.json"))
    a = ap.parse_args()
    rig = load_rig()
    if a.teach_place or a.teach_start:
        teach_pose(rig, "place_pose" if a.teach_place else "start_pose")
        return
    if "place_pose" not in rig:
        sys.exit("no place_pose in rig.json: run with --teach-place first")

    enable_plugin()
    from lerobot_robot_so101_safe import SO101SafeFollower, SO101SafeFollowerConfig

    start = {k: v for k, v in rig["start_pose"].items() if not k.startswith("_")}
    place = {k: v for k, v in rig["place_pose"].items() if not k.startswith("_")}
    robot = SO101SafeFollower(SO101SafeFollowerConfig(
        port=rig["follower"]["port"], id=rig["follower"]["id"], cameras=camera_configs(rig),
        safety_file=a.safety_file))
    print("start pose", start, "\nplace pose", place)
    print("작업 공간(주사위, 손, 케이블)을 확인하세요. Esc=즉시 정지.")
    if input("START 입력: ").strip().lower() not in {"start", "시작", "ㄴㅅㅁㄱㅅ"}:
        sys.exit("aborted")
    robot.connect()
    keys = Keys()
    r = Rig(robot, keys, a.min_area)

    def step(msg):
        if not a.auto:
            if input(f"\n[{msg}] Enter=진행, q=중단: ").strip().lower() == "q":
                raise Abort("operator stopped")
        else:
            print(f"\n[{msg}]")

    try:
        step("1. 시작 자세로 이동 + 그리퍼 열기")
        r.move_to({**start, "gripper": OPEN_GRIP}, a.speed)
        time.sleep(0.5)
        step("2. 주사위 검출 + 자코비안 추정 (관절을 4도씩 살짝 움직임)")
        J = probe_jacobian(r, a.probe_delta, 10.0)
        step("3. 주사위를 집을 위치로 접근 (비주얼 서보)")
        servo(r, J, a)
        step("4. 그리퍼 닫기")
        r.grip(CARRY_GRIP, 40.0)
        q, _ = r.read()
        print("gripper now", round(q["gripper"], 1))
        if q["gripper"] < 1.5:
            raise Abort("gripper closed fully: nothing in the jaws (grasp missed)")
        step("5. 시작 자세로 들어올림 -> 놓을 자세로 이동")
        r.move_to({**start, "gripper": CARRY_GRIP}, a.speed)
        r.move_to({**place, "gripper": CARRY_GRIP}, a.speed)
        step("6. 놓기")
        r.grip(OPEN_GRIP, 60.0)
        time.sleep(0.6)
        r.move_to({**start, "gripper": OPEN_GRIP}, a.speed)
        r.grip(REST_GRIP, 60.0)
        print("\n완료: 주사위가 왼쪽 칸에 놓였는지 눈으로 확인하세요.")
    except Abort as e:
        print(f"\n중단: {e}")
    except KeyboardInterrupt:
        robot.hold()
        print("\nCtrl+C: holding position")
    finally:
        keys.stop.clear()  # allow the return move after an Esc stop
        try:
            if input("시작 자세로 복귀할까요? (y/n): ").strip().lower() == "y":
                r.move_to({**start, "gripper": REST_GRIP}, a.speed)
        except Exception as e:
            print("복귀 실패:", e)
        input("팔을 손으로 받칠 준비가 되면 Enter (토크 해제 시 팔이 내려갑니다): ")
        robot.disconnect()


if __name__ == "__main__":
    main()
