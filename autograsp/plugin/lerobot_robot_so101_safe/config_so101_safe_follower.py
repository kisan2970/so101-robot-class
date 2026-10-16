"""Config for an SO-101 follower that filters every action through hard safety limits."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lerobot.robots.config import RobotConfig
from lerobot.robots.so_follower.config_so_follower import SOFollowerConfig


@RobotConfig.register_subclass("so101_safe_follower")
@dataclass
class SO101SafeFollowerConfig(RobotConfig, SOFollowerConfig):
    # JSON produced by tools/derive_limits.py: joint envelope, per-tick step limit, rest pose.
    safety_file: str = str(Path(__file__).resolve().parents[2] / "config" / "safety.json")
    # A camera frame older than this stops the robot (holds position) instead of acting on stale vision.
    camera_max_age_ms: int = 250
    # Refuse to start if the safety file is missing instead of silently running unrestricted.
    require_safety_file: bool = True
