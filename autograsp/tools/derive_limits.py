"""Derive the autonomous-mode safety envelope from teleoperation datasets.

Rationale: the policy should only command joint positions a human already drove the arm through,
plus a small margin. Step limits come from the fastest observed human motion.

    python autograsp/tools/derive_limits.py --datasets datasets/so101_pick_train --out autograsp/config/safety.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

MOTORS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]


def load_frames(root: Path) -> tuple[pd.DataFrame, int]:
    info = json.loads((root / "meta" / "info.json").read_text(encoding="utf-8"))
    files = sorted(glob.glob(str(root / "data" / "**" / "*.parquet"), recursive=True))
    if not files:
        raise FileNotFoundError(f"no parquet under {root}/data")
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    names = info["features"]["action"].get("names") or [f"{m}.pos" for m in MOTORS]
    if [n.removesuffix(".pos") for n in names] != MOTORS:
        raise ValueError(f"{root}: unexpected action names {names}")
    return df, info["fps"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", required=True)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "config" / "safety.json"))
    ap.add_argument("--margin-deg", type=float, default=5.0, help="margin added outside the demo envelope")
    ap.add_argument("--gripper-margin", type=float, default=3.0, help="margin in gripper units (0-100)")
    ap.add_argument("--control-fps", type=float, default=30.0)
    # max_step bounds |goal - measured position|, which is what the safety filter clamps. Servos trail the
    # commanded goal by ~3 ticks (and sag under gravity), so this gap is several times the per-tick change.
    ap.add_argument("--step-scale", type=float, default=1.2, help="x the 99.9th pct human |action - state| gap")
    ap.add_argument("--step-min", type=float, default=2.0)
    ap.add_argument("--step-max", type=float, default=15.0, help="hard cap on |goal - measured| (deg)")
    ap.add_argument("--gripper-step", type=float, default=100.0,
                    help="gripper gap cap; must stay large or the gripper cannot squeeze an object it is blocked by")
    ap.add_argument("--provisional", action="store_true", help="mark as not derived from task demos")
    args = ap.parse_args()

    states, actions, starts, speeds = [], [], [], []
    for d in args.datasets:
        df, fps = load_frames(Path(d))
        s = np.stack(df["observation.state"].to_numpy())
        a = np.stack(df["action"].to_numpy())
        states.append(s)
        actions.append(a)
        for _, ep in df.groupby("episode_index"):
            ea = np.stack(ep["action"].to_numpy())
            starts.append(np.stack(ep["observation.state"].to_numpy())[0])
            if len(ea) > 1:
                # deg per second, so datasets recorded at different fps are comparable
                speeds.append(np.abs(np.diff(ea, axis=0)) * fps)
    S, A = np.concatenate(states), np.concatenate(actions)
    both = np.concatenate([S, A])
    gap = np.abs(A - S)

    limits, step = {}, {}
    for i, m in enumerate(MOTORS):
        mg = args.gripper_margin if m == "gripper" else args.margin_deg
        lo, hi = float(both[:, i].min() - mg), float(both[:, i].max() + mg)
        if m == "gripper":
            lo, hi = max(lo, 0.0), min(hi, 100.0)
        limits[m] = [round(lo, 2), round(hi, 2)]
        if m == "gripper":
            step[m] = args.gripper_step
        else:
            g = np.percentile(gap[:, i], 99.9) * args.step_scale
            step[m] = round(float(np.clip(g, args.step_min, args.step_max)), 2)

    out = {
        "joint_limits": limits,
        "max_step": step,
        "rest_pose": {m: round(float(v), 2) for m, v in zip(MOTORS, np.median(np.stack(starts), axis=0))},
        "units": "degrees for body joints (use_degrees=True), 0-100 for gripper; "
                 "max_step caps |goal - measured position| per control tick",
        "control_fps": args.control_fps,
        "provisional": bool(args.provisional),
        "source_datasets": [str(Path(d).resolve()) for d in args.datasets],
        "n_frames": int(len(S)),
        "n_episodes": len(starts),
        "created": dt.datetime.now().isoformat(timespec="seconds"),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("joint_limits", "max_step", "rest_pose", "n_frames", "n_episodes")}, indent=2))
    print(f"wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
