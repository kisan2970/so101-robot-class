"""SO-101 follower with a hard safety layer between any policy and the motors.

Every action passes through, in order:
  1. finite check (NaN/inf -> hold + fault)
  2. absolute joint envelope (derived from teleop demonstrations, see tools/derive_limits.py)
  3. per-tick step limit relative to the *measured* joint position
Observations fail closed: a camera frame older than `camera_max_age_ms` holds the arm and raises
SafetyFault instead of letting the policy act on stale vision.

"Hold" = write Goal_Position := Present_Position with torque kept on, so the arm stops where it is
instead of collapsing (torque-off drops the SO-101 under gravity).
"""

from __future__ import annotations

import json
import logging
import math
import time
from pathlib import Path

from lerobot.robots.so_follower.so_follower import SOFollower
from lerobot.types import RobotAction, RobotObservation
from lerobot.utils.decorators import check_if_not_connected

from .config_so101_safe_follower import SO101SafeFollowerConfig

logger = logging.getLogger(__name__)


class SafetyFault(RuntimeError):
    """Raised after the arm has been put on hold because an input could not be trusted."""


def load_safety(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as f:
        s = json.load(f)
    for key in ("joint_limits", "max_step"):
        if key not in s:
            raise ValueError(f"safety file {path} is missing '{key}'")
    return s


class SO101SafeFollower(SOFollower):
    config_class = SO101SafeFollowerConfig
    # Keep the parent's name so calibration is read from .../calibration/robots/so_follower/<id>.json
    name = "so_follower"

    def __init__(self, config: SO101SafeFollowerConfig):
        if config.max_relative_target is not None:
            logger.info("max_relative_target is ignored; step limits come from the safety file")
            config.max_relative_target = None
        super().__init__(config)
        path = Path(config.safety_file)
        if not path.exists():
            if config.require_safety_file:
                raise FileNotFoundError(
                    f"Safety file {path} not found. Run tools/derive_limits.py on teleop data first."
                )
            self.safety = None
        else:
            self.safety = load_safety(path)
            missing = set(self.bus.motors) - set(self.safety["joint_limits"])
            if missing:
                raise ValueError(f"safety file lacks limits for {sorted(missing)}")
        self.stats = {"actions": 0, "abs_clipped": 0, "step_clipped": 0, "holds": 0}
        self.last_clip: dict = {}

    # ------------------------------------------------------------------ hold / park
    def hold(self) -> None:
        """Freeze in place with torque on. Safe to call repeatedly; never raises."""
        try:
            present = self.bus.sync_read("Present_Position", normalize=False)
            self.bus.sync_write("Goal_Position", present, normalize=False)
            self.stats["holds"] += 1
        except Exception as e:  # comms may be the thing that failed; servos keep their last goal anyway
            logger.error(f"hold() could not talk to the bus: {e}")

    def park(self, speed_deg_s: float = 30.0, timeout_s: float = 8.0) -> bool:
        """Move slowly to the rest pose recorded in the safety file. Returns True if reached."""
        if not self.safety or "rest_pose" not in self.safety:
            logger.warning("no rest_pose in safety file; holding instead of parking")
            self.hold()
            return False
        target = self.safety["rest_pose"]
        dt = 1 / 30
        step = speed_deg_s * dt
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < timeout_s:
            present = self.bus.sync_read("Present_Position")
            err = {m: target[m] - present[m] for m in target}
            if max(abs(v) for v in err.values()) < 2.0:
                return True
            goal = {m: present[m] + max(-step, min(step, err[m])) for m in target}
            self.bus.sync_write("Goal_Position", goal)
            time.sleep(dt)
        logger.warning("park() timed out before reaching rest pose")
        return False

    # ------------------------------------------------------------------ observation
    @check_if_not_connected
    def get_observation(self) -> RobotObservation:
        obs = {f"{m}.pos": v for m, v in self.bus.sync_read("Present_Position").items()}
        for cam_key, cam in self.cameras.items():
            try:
                obs[cam_key] = cam.read_latest(max_age_ms=self.config.camera_max_age_ms)
            except (TimeoutError, RuntimeError) as e:  # stale frame, or capture thread died
                self.hold()
                raise SafetyFault(f"camera '{cam_key}' stale/stopped: {e}") from e
        return obs

    # ------------------------------------------------------------------ action
    def filter_action(self, goal: dict[str, float], present: dict[str, float]) -> dict[str, float]:
        """Pure function of (goal, present) -> safe goal. Exposed for offline/dry-run testing."""
        if self.safety is None:
            return goal
        lim, step = self.safety["joint_limits"], self.safety["max_step"]
        out, clip = {}, {}
        for m, g in goal.items():
            lo, hi = lim[m]
            a = min(max(g, lo), hi)
            if a != g:
                self.stats["abs_clipped"] += 1
                clip[m] = ("abs", g, a)
            s = step[m]
            b = min(max(a, present[m] - s), present[m] + s)
            if b != a:
                self.stats["step_clipped"] += 1
                clip.setdefault(m, ("step", g, b))
            out[m] = b
        self.last_clip = clip
        return out

    @check_if_not_connected
    def send_action(self, action: RobotAction) -> RobotAction:
        goal = {k.removesuffix(".pos"): float(v) for k, v in action.items() if k.endswith(".pos")}
        if set(goal) != set(self.bus.motors):
            self.hold()
            raise SafetyFault(f"action keys {sorted(goal)} do not match motors {sorted(self.bus.motors)}")
        if not all(math.isfinite(v) for v in goal.values()):
            self.hold()
            raise SafetyFault(f"non-finite action {goal}")
        present = self.bus.sync_read("Present_Position")
        safe = self.filter_action(goal, present)
        self.bus.sync_write("Goal_Position", safe)
        self.stats["actions"] += 1
        return {f"{m}.pos": v for m, v in safe.items()}

    @check_if_not_connected
    def disconnect(self):
        logger.info(f"safety stats: {self.stats}")
        super().disconnect()
