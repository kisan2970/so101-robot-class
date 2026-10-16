"""Autonomous pick-and-place trials with safety limits, timing telemetry, and failure labelling.

The control loop is local: camera + joint state -> policy -> safety filter -> motors, at a fixed rate.
No LLM is in the loop.

Real robot (asks you to confirm the workspace first):
    python autograsp/tools/run_eval.py --policy outputs/train/<run>/checkpoints/last/pretrained_model \
        --split seen --background B0 --light L0 --trials 10 --speed-scale 0.5

Dry run (no hardware): replays a recorded episode as the "camera + state" input and shows what would be
sent after the safety filter, plus inference latency:
    python autograsp/tools/run_eval.py --policy ... --dry-run-dataset datasets/so101_pick_train --dry-run-episode 0

Keys during a trial:  Enter = trial finished (success moment or give up)   Space = pause/resume (hold)
                      Esc = emergency stop (hold, end session)             Ctrl+C also holds and exits
Results: autograsp/runs/eval/<session>/trials.csv (+ per-trial .npz trajectory and .mp4 video)
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import threading
import time
from pathlib import Path

import numpy as np
import torch

from common import AUTOGRASP, CONFIG_DIR, camera_configs, enable_plugin, load_rig

FAILURES = {
    "1": ("F1_target", "대상 선택 오류 (다른 물체/빈 곳으로 감)"),
    "2": ("F2_approach", "접근 위치/방향 오류 (물체 옆을 잡음, 방향 틀림)"),
    "3": ("F3_grasp_miss", "그리퍼는 닫혔지만 물체를 못 잡음"),
    "4": ("F4_drop", "들어올리다/옮기다 떨어뜨림"),
    "5": ("F5_place", "목적지에 놓기 실패"),
    "6": ("F6_latency", "영상/제어 지연, 끊김, 떨림"),
    "7": ("F7_unreachable", "도달 불가 자세 / 안전 제한에 막힘"),
    "8": ("F8_other", "기타 (notes에 기록)"),
}


# ----------------------------------------------------------------------------- policy
def load_policy(path: str, device: str, n_action_steps: int | None, rename_map: dict | None = None):
    from lerobot.configs.policies import PreTrainedConfig
    from lerobot.policies import get_policy_class, make_pre_post_processors

    cfg = PreTrainedConfig.from_pretrained(path)
    cfg.pretrained_path = Path(path)
    cfg.device = device
    if n_action_steps is not None and hasattr(cfg, "n_action_steps"):
        cfg.n_action_steps = n_action_steps
    policy = get_policy_class(cfg.type).from_pretrained(path, config=cfg)
    policy.to(device).eval()
    overrides = {"device_processor": {"device": device}}
    if rename_map:  # same robot-key -> policy-key mapping used at training time (e.g. wrist -> camera1)
        overrides["rename_observations_processor"] = {"rename_map": rename_map}
    pre, post = make_pre_post_processors(policy_cfg=cfg, pretrained_path=path, preprocessor_overrides=overrides)
    return policy, pre, post, cfg


LEFT_TASK = "Move the dice to the left cell."  # must match tools/make_left_plan.py


def sector_task(n: int) -> str:
    return f"Move the tape to sector {n}."  # must match tools/make_sector_plan.py


# ----------------------------------------------------------------------------- dry-run robot
class ReplayRobot:
    """Feeds a recorded episode as observations; actions go through the real safety filter, not motors."""

    name = "so_follower"

    def __init__(self, root: str, episode: int, safe_robot):
        from lerobot.datasets.lerobot_dataset import LeRobotDataset

        self.ds = LeRobotDataset(f"local/{Path(root).name}", root=root, episodes=[episode], video_backend="pyav")
        self.cams = [k.removeprefix("observation.images.") for k in self.ds.meta.camera_keys]
        self.motors = [n.removesuffix(".pos") for n in self.ds.meta.features["action"]["names"]]
        self.i, self.n = 0, len(self.ds)
        self.safe = safe_robot  # unconnected SO101SafeFollower: only its filter_action is used
        self.last_state = None
        self.stats = safe_robot.stats

    @property
    def observation_features(self):
        f = {f"{m}.pos": float for m in self.motors}
        for c in self.cams:
            f[c] = tuple(self.ds.meta.features[f"observation.images.{c}"]["shape"])
        return f

    @property
    def action_features(self):
        return {f"{m}.pos": float for m in self.motors}

    def get_observation(self):
        if self.i >= self.n:
            raise StopIteration
        item = self.ds[self.i]
        self.i += 1
        obs = {f"{m}.pos": float(v) for m, v in zip(self.motors, item["observation.state"])}
        for c in self.cams:
            obs[c] = (item[f"observation.images.{c}"].permute(1, 2, 0).numpy() * 255).astype(np.uint8)
        self.last_state = {m: obs[f"{m}.pos"] for m in self.motors}
        self.recorded_action = item["action"].numpy()
        self.task = item.get("task", "")
        return obs

    def send_action(self, action):
        goal = {k.removesuffix(".pos"): float(v) for k, v in action.items()}
        safe = self.safe.filter_action(goal, self.last_state)
        return {f"{m}.pos": v for m, v in safe.items()}

    def hold(self):
        pass

    def disconnect(self):
        pass


# ----------------------------------------------------------------------------- keyboard
class Keys:
    def __init__(self):
        self.end = threading.Event()
        self.stop = threading.Event()
        self.paused = threading.Event()
        self.listener = None
        try:
            from pynput import keyboard

            def on_press(k):
                if k == keyboard.Key.esc:
                    self.stop.set()
                elif k == keyboard.Key.enter:
                    self.end.set()
                elif k == keyboard.Key.space:
                    self.paused.clear() if self.paused.is_set() else self.paused.set()

            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.start()
        except Exception as e:
            print(f"!! keyboard listener unavailable ({e}); only Ctrl+C can stop the robot")

    def new_trial(self):
        self.end.clear()
        self.paused.clear()


# ----------------------------------------------------------------------------- chunk executor
class ChunkExecutor:
    """Runs a chunking policy (SmolVLA etc.) without stalls or chunk-boundary jumps.

    * The next chunk is computed in a background thread once `refill_at` actions are left, from the
      newest observation, so the arm never waits ~0.3-0.4 s for inference.
    * Actions that became stale while that chunk was computing are skipped (tick-aligned), and the first
      `blend` actions are cross-faded with the old plan so a re-plan does not jerk the arm.
    * Each chunk is low-pass filtered (centered moving average, `smooth` ticks): flow-matching chunks
      carry ~1 deg tick-to-tick noise that the servos otherwise reproduce as visible shaking.
    """

    def __init__(self, policy, pre, post, device, robot_type, refill_at=20, smooth=5, blend=8):
        self.policy, self.pre, self.post, self.device = policy, pre, post, device
        self.robot_type, self.refill_at, self.smooth, self.blend = robot_type, refill_at, smooth, blend
        self.task = ""
        self.reset()

    def reset(self, task: str | None = None):
        if task is not None:
            self.task = task
        self.queue: list[np.ndarray] = []
        self.thread, self.result, self.launched_tick = None, None, 0
        self.tick, self.last = 0, None
        self.chunk_ms: list[float] = []

    def _infer(self, frame) -> np.ndarray:
        from lerobot.policies.utils import prepare_observation_for_inference

        t = time.perf_counter()
        with torch.inference_mode():
            obs = prepare_observation_for_inference(dict(frame), self.device, self.task, self.robot_type)
            chunk = self.post(self.policy.predict_action_chunk(self.pre(obs)))
        c = chunk.squeeze(0).float().cpu().numpy()
        if self.smooth > 1 and len(c) > self.smooth:
            k = self.smooth // 2
            padded = np.pad(c, ((k, k), (0, 0)), mode="edge")
            kernel = np.ones(self.smooth) / self.smooth
            c = np.stack([np.convolve(padded[:, j], kernel, mode="valid") for j in range(c.shape[1])], axis=1)
        self.chunk_ms.append((time.perf_counter() - t) * 1e3)
        return c

    def _run(self, frame):
        self.result = self._infer(frame)

    def step(self, frame) -> np.ndarray:
        if self.thread is not None and not self.thread.is_alive():
            new = list(self.result[min(self.tick - self.launched_tick, len(self.result) - 1):])
            old = self.queue
            for i in range(min(self.blend, len(old), len(new))):
                w = (i + 1) / (self.blend + 1)
                new[i] = (1 - w) * old[i] + w * new[i]
            self.queue, self.thread = new, None
        if not self.queue and self.thread is None:  # very first chunk of a trial: compute inline
            self.queue = list(self._infer(frame))
        elif self.thread is None and len(self.queue) <= self.refill_at:
            self.launched_tick = self.tick
            self.thread = threading.Thread(target=self._run, args=(dict(frame),), daemon=True)
            self.thread.start()
        if self.queue:
            self.last = self.queue.pop(0)
        self.tick += 1
        return self.last  # queue ran dry while computing: hold the last target


# ----------------------------------------------------------------------------- one trial
def run_trial(robot, policy, pre, post, cfg, ds_features, task, fps, max_s, keys, watchdog_ms, video_path,
              executor: ChunkExecutor | None = None):
    import cv2

    from lerobot.common.control_utils import predict_action
    from lerobot.policies.utils import make_robot_action
    from lerobot.utils.feature_utils import build_dataset_frame

    try:
        from lerobot_robot_so101_safe import SafetyFault
    except ImportError:  # pragma: no cover
        SafetyFault = RuntimeError

    policy.reset()
    pre.reset()
    post.reset()
    if executor is not None:
        executor.reset(task)
    device = torch.device(cfg.device)
    period = 1.0 / fps
    log = {k: [] for k in ("t", "state", "action_raw", "action_sent", "inf_ms", "loop_ms", "clipped")}
    frames, fault, slow, was_paused = [], None, 0, False
    t0 = time.perf_counter()
    end_reason = "timeout"
    while True:
        tick = time.perf_counter()
        if keys.stop.is_set():
            end_reason, fault = "estop", "operator_estop"
            break
        if keys.end.is_set():
            end_reason = "operator_end"
            break
        if tick - t0 > max_s:
            break
        if keys.paused.is_set():
            robot.hold()
            was_paused = True
            time.sleep(0.05)
            continue
        if was_paused:  # the queued action chunk was planned for a scene that may have changed
            policy.reset()
            if executor is not None:
                executor.reset()
            was_paused = False
        try:
            obs = robot.get_observation()
        except StopIteration:
            end_reason = "replay_end"
            break
        except SafetyFault as e:
            end_reason, fault = "fault", f"obs:{e}"
            break
        frame = build_dataset_frame(ds_features, obs, prefix="observation")
        ti = time.perf_counter()
        if executor is not None:
            action = torch.from_numpy(np.asarray(executor.step(frame), dtype=np.float32)).unsqueeze(0)
        else:
            action = predict_action(frame, policy, device, pre, post, cfg.use_amp, task=task,
                                    robot_type="so_follower")
            if device.type == "cuda":
                torch.cuda.synchronize()
        inf_ms = (time.perf_counter() - ti) * 1e3
        act = make_robot_action(action, ds_features)
        try:
            sent = robot.send_action(act)
        except SafetyFault as e:
            end_reason, fault = "fault", f"act:{e}"
            break
        names = ds_features["action"]["names"]
        log["t"].append(tick - t0)
        log["state"].append([obs[n] for n in names])
        log["action_raw"].append([act[n] for n in names])
        log["action_sent"].append([sent[n] for n in names])
        log["inf_ms"].append(inf_ms)
        log["clipped"].append(int(any(abs(act[n] - sent[n]) > 1e-3 for n in names)))
        if hasattr(robot, "recorded_action"):  # dry run: what the human did at this frame
            log.setdefault("action_recorded", []).append(robot.recorded_action.tolist())
        if len(log["t"]) % 2 == 0:
            cams = [k for k in obs if isinstance(obs[k], np.ndarray) and obs[k].ndim == 3]
            tiles = [cv2.resize(cv2.cvtColor(obs[c], cv2.COLOR_RGB2BGR), (320, 240)) for c in cams]
            frames.append(np.hstack(tiles))
        loop_ms = (time.perf_counter() - tick) * 1e3
        log["loop_ms"].append(loop_ms)
        slow = slow + 1 if loop_ms > watchdog_ms else 0
        if slow >= 5:
            end_reason, fault = "fault", f"loop slower than {watchdog_ms} ms for 5 ticks"
            break
        time.sleep(max(0.0, period - (time.perf_counter() - tick)))
    robot.hold()
    duration = time.perf_counter() - t0
    if executor is not None:
        log["chunk_ms"] = executor.chunk_ms

    if frames and video_path is not None:
        h, w = frames[0].shape[:2]
        vw = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), fps / 2, (w, h))
        for f in frames:
            vw.write(f)
        vw.release()
    return log, duration, end_reason, fault


def summarize(log, duration):
    inf = np.array(log["inf_ms"]) if log["inf_ms"] else np.array([np.nan])
    loop = np.array(log["loop_ms"]) if log["loop_ms"] else np.array([np.nan])
    n = len(log["t"])
    return {
        "steps": n,
        "achieved_hz": round(n / duration, 1) if duration > 0 else None,
        "inf_ms_p50": round(float(np.nanmedian(inf)), 1),
        "inf_ms_p95": round(float(np.nanpercentile(inf, 95)), 1),
        "inf_ms_max": round(float(np.nanmax(inf)), 1),
        "loop_ms_p95": round(float(np.nanpercentile(loop, 95)), 1),
        "clipped_frac": round(float(np.mean(log["clipped"])) if log["clipped"] else 0.0, 3),
        **({"mae_vs_recorded_deg": round(float(np.mean(np.abs(np.array(log["action_raw"])
                                                               - np.array(log["action_recorded"])))), 2)}
           if log.get("action_recorded") else {}),
    }


def ask(prompt, valid=None):
    while True:
        a = input(prompt).strip()
        if valid is None or a in valid:
            return a


# ----------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True, help="checkpoint dir containing config.json + model.safetensors")
    ap.add_argument("--trials", type=int, default=9)
    ap.add_argument("--split", choices=["seen", "unseen"], default="seen",
                    help="label only: seen = same desk/light/layout as training, unseen = something changed")
    ap.add_argument("--condition", default="train-setup", help="free-text label of the environment for the report")
    ap.add_argument("--targets", default="1,2,3,4,5,6,7,8,9", help="target sectors to cycle through (shuffled)")
    ap.add_argument("--left-task", action="store_true",
                    help='fixed task "Move the dice to the left cell."; --targets is only used to balance the start sectors')
    ap.add_argument("--rename-map", default='{"observation.images.wrist": "observation.images.camera1"}',
                    help="JSON robot-key -> policy-key map; must match training ('{}' for none)")
    ap.add_argument("--max-seconds", type=float, default=40)
    ap.add_argument("--fps", type=float, default=None, help="control rate (default rig.control_fps)")
    ap.add_argument("--n-action-steps", type=int, default=None,
                    help="how many actions of each predicted chunk to execute before re-observing")
    ap.add_argument("--speed-scale", type=float, default=1.0,
                    help="x the |goal - measured| cap from the safety file (<1 slows the arm below demo speed)")
    ap.add_argument("--executor", choices=["auto", "sync", "async"], default="auto",
                    help="async = look-ahead + smoothed chunks (default for SmolVLA/pi0); sync = LeRobot select_action")
    ap.add_argument("--smooth", type=int, default=5, help="moving-average window over each chunk (ticks)")
    ap.add_argument("--refill-at", type=int, default=30, help="start computing the next chunk with this many left")
    ap.add_argument("--safety-file", default=str(CONFIG_DIR / "safety.json"))
    ap.add_argument("--watchdog-ms", type=float, default=150)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--dry-run-dataset", default=None)
    ap.add_argument("--dry-run-episode", type=int, default=0)
    ap.add_argument("--session", default=None)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rig = load_rig()
    enable_plugin()
    from lerobot.utils.feature_utils import hw_to_dataset_features
    from lerobot_robot_so101_safe import SO101SafeFollower, SO101SafeFollowerConfig

    fps = args.fps or rig["control_fps"]
    dry = args.dry_run_dataset is not None
    rename = json.loads(args.rename_map)
    policy, pre, post, cfg = load_policy(args.policy, args.device, args.n_action_steps, rename)
    want_cams = {k for k in cfg.input_features if k.startswith("observation.images.")}
    use_async = args.executor == "async" or (args.executor == "auto" and cfg.type in {"smolvla", "pi0", "pi05"})
    executor = ChunkExecutor(policy, pre, post, torch.device(args.device), "so_follower",
                             refill_at=args.refill_at, smooth=args.smooth) if use_async else None

    safe_cfg = SO101SafeFollowerConfig(
        port=rig["follower"]["port"], id=rig["follower"]["id"],
        cameras={} if dry else camera_configs(rig), safety_file=args.safety_file,
    )
    safe = SO101SafeFollower(safe_cfg)
    safe.safety["max_step"] = {m: v * args.speed_scale for m, v in safe.safety["max_step"].items()}
    robot = ReplayRobot(args.dry_run_dataset, args.dry_run_episode, safe) if dry else safe

    have = {f"observation.images.{k}" for k, v in robot.observation_features.items() if isinstance(v, tuple)}
    have = {rename.get(k, k) for k in have}
    # SmolVLA tolerates missing cameras (camera2/3 here); every camera we feed must be one the policy knows
    if not have or not have <= want_cams:
        raise SystemExit(f"camera mismatch: policy expects {sorted(want_cams)}, robot provides {sorted(have)} "
                         f"after rename {rename}")
    ds_features = {**hw_to_dataset_features(robot.observation_features, "observation"),
                   **hw_to_dataset_features(robot.action_features, "action")}

    session = args.session or time.strftime("%Y%m%d_%H%M%S") + ("_dry" if dry else "")
    out = AUTOGRASP / "runs" / "eval" / session
    out.mkdir(parents=True, exist_ok=True)
    s = safe.safety
    summary = {
        "policy": args.policy, "policy_type": cfg.type, "device": args.device, "control_fps": fps,
        "n_action_steps": getattr(cfg, "n_action_steps", None), "chunk_size": getattr(cfg, "chunk_size", None),
        "cameras_fed": sorted(have), "rename_map": rename, "safety_file": args.safety_file,
        "provisional_limits": s.get("provisional"), "joint_limits": s["joint_limits"],
        "max_speed_deg_s": {m: round(v * fps, 1) for m, v in s["max_step"].items()},
        "rest_pose": s.get("rest_pose"), "camera_max_age_ms": safe_cfg.camera_max_age_ms,
        "watchdog_ms": args.watchdog_ms, "max_seconds_per_trial": args.max_seconds,
        "split": args.split, "condition": args.condition,
        "executor": "async" if use_async else "sync", "smooth": args.smooth, "refill_at": args.refill_at,
        "speed_scale": args.speed_scale,
    }
    (out / "session.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if not dry:
        print("\n자율 구동 전 확인: 위 관절 범위/최대 속도 안에서 팔이 움직입니다. 작업 공간에 사람 손·케이블·"
              "깨질 물건이 없는지, 전원 스위치에 손이 닿는지 확인하세요. Esc=즉시 정지(현 위치 유지).")
        # accept the word typed with the Korean IME on as well (START -> ㄴㅅㅁㄱㅅ)
        if ask("작업 공간을 확인했으면 START 또는 시작 을 입력: ").strip().lower() not in {"start", "시작", "ㄴㅅㅁㄱㅅ"}:
            raise SystemExit("aborted by operator")
        robot.connect()

    rng = random.Random(args.seed)
    targets = [int(t) for t in args.targets.split(",")]
    queue: list[int] = []
    keys = Keys()
    csv_path = out / "trials.csv"
    fields = ["trial", "time", "policy", "split", "condition", "start", "target", "task", "dry_run", "grasp",
              "placed_sector", "place", "failure", "end_reason", "fault", "duration_s", "steps", "achieved_hz",
              "inf_ms_p50", "inf_ms_p95", "inf_ms_max", "loop_ms_p95", "clipped_frac", "mae_vs_recorded_deg", "notes"]
    try:
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            if f.tell() == 0:
                w.writeheader()
            for trial in range(args.trials if not dry else 1):
                if not queue:  # every target once before any repeats
                    queue = targets[:]
                    rng.shuffle(queue)
                target = queue.pop()
                start = rng.choice([x for x in range(1, 10) if x != target])
                task = sector_task(target)
                if args.left_task:
                    start, task, target = target, LEFT_TASK, "left"  # start sector cycles through all 9
                if dry:
                    robot.get_observation()  # peek the episode's own task text
                    task, robot.i, start, target = robot.task or task, 0, "", ""
                else:
                    print(f"\n[trial {trial}] 물체를 {start}번 칸에 두세요.  지시: \"{task}\"  (목표 {target})")
                    print("  팔은 시작 자세 근처에 있어야 합니다. Enter=시작, 실행 중 Enter=종료, Space=일시정지, Esc=비상정지")
                    if ask("준비되면 Enter (q=종료): ", None) == "q":
                        break
                keys.new_trial()
                log, dur, end_reason, fault = run_trial(
                    robot, policy, pre, post, cfg, ds_features, task, fps, args.max_seconds, keys,
                    args.watchdog_ms, out / f"trial_{trial:03d}.mp4", executor)
                np.savez_compressed(out / f"trial_{trial:03d}.npz", **{k: np.array(v) for k, v in log.items()},
                                    names=np.array(ds_features["action"]["names"]))
                row = {"trial": trial, "time": time.strftime("%H:%M:%S"), "policy": args.policy, "split": args.split,
                       "condition": args.condition, "start": start, "target": target, "task": task,
                       "dry_run": int(dry), "end_reason": end_reason, "fault": fault or "",
                       "duration_s": round(dur, 2), **summarize(log, dur)}
                if dry:
                    row.update(grasp="", placed_sector="", place="", failure="", notes="dry run")
                else:
                    g = ask("물체를 집었나? (y/n): ", {"y", "n"}) == "y"
                    if args.left_task:
                        placed = "left" if g and ask("왼쪽 칸에 놓였나? (y/n): ", {"y", "n"}) == "y" else 0
                    else:
                        placed = int(ask("물체가 최종적으로 놓인 칸 번호 (0=칸 밖/떨어뜨림/못 옮김): ",
                                         {str(i) for i in range(10)})) if g else 0
                    ok = placed == target
                    code = ""
                    if not ok:
                        if g and placed not in (0, start):
                            code = FAILURES["1"][0]  # moved it, but to the wrong sector: language/target error
                        else:
                            print("\n".join(f"  {k}: {v[0]} - {v[1]}" for k, v in FAILURES.items()))
                            code = FAILURES[ask("실패 유형 번호: ", set(FAILURES))][0]
                    row.update(grasp=int(g), placed_sector=placed, place=int(ok), failure=code,
                               notes=input("메모(선택): ").strip())
                w.writerow(row)
                f.flush()
                print({k: row[k] for k in ("trial", "target", "placed_sector", "place", "failure", "end_reason",
                                           "duration_s", "achieved_hz", "inf_ms_p95", "clipped_frac")})
                if keys.stop.is_set():
                    print("emergency stop: session ended with the arm holding position")
                    break
    except KeyboardInterrupt:
        robot.hold()
        print("Ctrl+C: holding position")
    finally:
        if not dry:
            if ask("시작 자세로 천천히 복귀할까요? (y/n): ", {"y", "n"}) == "y":
                robot.park()
            input("팔을 손으로 받칠 준비가 되면 Enter (토크 해제 시 팔이 내려갑니다): ")
            robot.disconnect()
    print(f"results: {csv_path}")


if __name__ == "__main__":
    main()
