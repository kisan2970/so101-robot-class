"""Shared helpers: rig config loading, paths, and LeRobot CLI argument builders."""

from __future__ import annotations

import json
import sys
from pathlib import Path

AUTOGRASP = Path(__file__).resolve().parents[1]
PROJECT = AUTOGRASP.parent
PLUGIN_DIR = AUTOGRASP / "plugin"
CONFIG_DIR = AUTOGRASP / "config"
PYTHON = PROJECT / ".venv" / "Scripts" / "python.exe"


def load_rig(path: str | Path | None = None) -> dict:
    with open(path or CONFIG_DIR / "rig.json", encoding="utf-8") as f:
        rig = json.load(f)
    for key in ("datasets_root", "outputs_root"):  # relative paths are relative to the project folder
        if key in rig and not Path(rig[key]).is_absolute():
            rig[key] = str((PROJECT / rig[key]).resolve())
    return rig


def enable_plugin() -> None:
    """Make the so101_safe_follower robot type importable without pip-installing anything."""
    if str(PLUGIN_DIR) not in sys.path:
        sys.path.insert(0, str(PLUGIN_DIR))
    import lerobot_robot_so101_safe  # noqa: F401  (registers the config subclass)


def cameras_cli(rig: dict, names: list[str] | None = None) -> str:
    cams = {k: v for k, v in rig["cameras"].items() if names is None or k in names}
    return json.dumps(cams)


def camera_configs(rig: dict) -> dict:
    from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig

    out = {}
    for name, c in rig["cameras"].items():
        c = {k: v for k, v in c.items() if k != "type"}
        out[name] = OpenCVCameraConfig(**c)
    return out


def dataset_root(rig: dict, repo_id: str) -> Path:
    return Path(rig["datasets_root"]) / repo_id.split("/", 1)[-1]
