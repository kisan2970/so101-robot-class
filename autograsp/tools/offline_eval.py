"""Open-loop action error of a checkpoint on recorded episodes, grouped by collection condition.

This is a cheap *proxy* for catching regressions and seen-vs-unseen gaps before touching the robot.
It is NOT a success rate: small errors can still compound into a failed grasp in closed loop.

    python autograsp/tools/offline_eval.py --policy <ckpt> --root datasets/so101_pick_heldout
    python autograsp/tools/offline_eval.py --policy <ckpt> --root datasets/so101_pick_train --episodes 9,19,29
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from common import CONFIG_DIR, enable_plugin
from run_eval import load_policy


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--episodes", default=None, help="comma list (default: all)")
    ap.add_argument("--grip-thresh", type=float, default=None,
                    help="gripper value treated as 'closed' for timing (default: midpoint of episode range)")
    ap.add_argument("--rename-map", default='{"observation.images.wrist": "observation.images.camera1"}',
                    help="dataset camera key -> policy camera key (same map used at training time)")
    args = ap.parse_args()
    rename = json.loads(args.rename_map)
    enable_plugin()
    from lerobot.common.control_utils import predict_action
    from lerobot.datasets.lerobot_dataset import LeRobotDataset

    root = Path(args.root)
    policy, pre, post, cfg = load_policy(args.policy, "cuda", None, rename)
    meta_ds = LeRobotDataset(f"local/{root.name}", root=root, video_backend="pyav")
    eps = [int(e) for e in args.episodes.split(",")] if args.episodes else list(range(meta_ds.meta.total_episodes))
    cams = meta_ds.meta.camera_keys
    want = [k for k in cfg.input_features if k.startswith("observation.images.")]
    have = {rename.get(k, k) for k in cams}
    if not have or not have <= set(want):  # SmolVLA tolerates missing cameras (camera2/3)
        raise SystemExit(f"camera mismatch: policy {want} vs dataset {cams} after rename {rename}")

    rows = []
    for ep in eps:
        ds = LeRobotDataset(f"local/{root.name}", root=root, episodes=[ep], video_backend="pyav")
        policy.reset()
        pre.reset()
        post.reset()
        pred, rec = [], []
        for i in range(len(ds)):
            item = ds[i]
            obs = {"observation.state": item["observation.state"].numpy()}
            for c in cams:
                obs[c] = (item[c].permute(1, 2, 0).numpy() * 255).astype(np.uint8)
            a = predict_action(obs, policy, torch.device("cuda"), pre, post, cfg.use_amp,
                               task=ds.meta.tasks.index[0] if len(ds.meta.tasks) else "", robot_type="so_follower")
            pred.append(a.squeeze(0).cpu().numpy())
            rec.append(item["action"].numpy())
        P, R = np.stack(pred), np.stack(rec)
        err = np.abs(P - R)
        thr = args.grip_thresh if args.grip_thresh is not None else (R[:, 5].max() + R[:, 5].min()) / 2
        fps = ds.meta.fps

        def first_close(x):
            # first frame after the gripper has opened where it closes again (grasp moment)
            opened = np.where(x > thr)[0]
            if not len(opened):
                return None
            after = np.where(x[opened[0]:] < thr)[0]
            return int(opened[0] + after[0]) if len(after) else None

        fr, fp = first_close(R[:, 5]), first_close(P[:, 5])
        rows.append({
            "episode_index": ep, "frames": len(R), "mae_body_deg": round(float(err[:, :5].mean()), 2),
            **{f"mae_{n.removesuffix('.pos')}": round(float(err[:, j].mean()), 2)
               for j, n in enumerate(ds.meta.features["action"]["names"])},
            "grasp_time_err_s": None if fr is None or fp is None else round((fp - fr) / fps, 2),
            "pred_grasp_found": fp is not None,
        })
        print(rows[-1])

    df = pd.DataFrame(rows)
    cond_path = CONFIG_DIR / "episode_conditions.csv"
    if cond_path.exists():
        cond = pd.read_csv(cond_path)
        cond = cond[cond["dataset"].str.endswith(root.name)]
        df = df.merge(cond, on="episode_index", how="left")
        keys = [k for k in ("split", "background", "light") if k in df]
        print("\nby condition:")
        print(df.groupby(keys, dropna=False)[["mae_body_deg", "mae_gripper", "grasp_time_err_s"]]
              .agg(["mean", "count"]).round(2).to_string())
    out = Path(args.policy).resolve().parent / f"offline_eval_{root.name}.csv"
    df.to_csv(out, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"\noverall mae_body_deg={df['mae_body_deg'].mean():.2f}  -> {out}")


if __name__ == "__main__":
    main()
