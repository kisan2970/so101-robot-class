"""Validate a recorded dataset before training.

Checks per episode: length, timestamp regularity (dropped frames), NaN/inf, whether the gripper actually
closed, action->state lag (time-sync / control-delay signal), and writes a contact sheet of camera frames
(first / grasp-ish / last) so framing, blur, and lighting problems are visible.

    python autograsp/tools/check_dataset.py datasets/so101_pick_train
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

MOTORS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]


def lag_frames(a: np.ndarray, s: np.ndarray, max_lag: int = 10) -> int | None:
    """Lag (frames) at which the measured state best follows the commanded action."""
    da, ds = np.diff(a), np.diff(s)
    if da.std() < 1e-6 or ds.std() < 1e-6:
        return None
    best, best_c = None, -2.0
    for k in range(0, max_lag + 1):
        x, y = da[: len(da) - k], ds[k:]
        if len(x) < 5:
            break
        c = np.corrcoef(x, y)[0, 1]
        if c > best_c:
            best, best_c = k, c
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--sheet-episodes", type=int, default=12, help="episodes in the contact sheet")
    ap.add_argument("--gripper-close-thresh", type=float, default=15.0,
                    help="gripper travel (0-100) that counts as 'closed on something'")
    args = ap.parse_args()
    root = Path(args.root)
    info = json.loads((root / "meta" / "info.json").read_text(encoding="utf-8"))
    fps = info["fps"]
    df = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(root / "data/**/*.parquet"), recursive=True))])
    cams = [k for k, v in info["features"].items() if v["dtype"] == "video"]
    print(f"{root}: fps={fps} episodes={info['total_episodes']} frames={info['total_frames']} cameras={cams}")
    for c in cams:
        vi = info["features"][c].get("info", {})
        print(f"  {c}: {vi.get('video.width')}x{vi.get('video.height')} @ {vi.get('video.fps')} {vi.get('video.codec')}")

    rows, issues = [], []
    for ep, g in df.groupby("episode_index"):
        a, s = np.stack(g["action"].to_numpy()), np.stack(g["observation.state"].to_numpy())
        ts = g["timestamp"].to_numpy()
        dts = np.diff(ts)
        gaps = int((dts > 1.5 / fps).sum())
        grip = a[:, 5]
        lags = [lag_frames(a[:, j], s[:, j]) for j in range(6)]
        r = {
            "ep": int(ep), "frames": len(g), "dur_s": round(len(g) / fps, 1), "ts_gaps": gaps,
            "nonfinite": int((~np.isfinite(a)).sum() + (~np.isfinite(s)).sum()),
            "grip_travel": round(float(grip.max() - grip.min()), 1),
            "track_err_deg_p95": round(float(np.percentile(np.abs(a[:-3, :5] - s[3:, :5]), 95)), 1) if len(a) > 4 else None,
            "lag_frames": [l for l in lags],
        }
        rows.append(r)
        if gaps:
            issues.append(f"ep {ep}: {gaps} timestamp gaps (dropped frames / slow loop)")
        if r["nonfinite"]:
            issues.append(f"ep {ep}: non-finite values")
        if r["grip_travel"] < args.gripper_close_thresh:
            issues.append(f"ep {ep}: gripper barely moved ({r['grip_travel']}) - no grasp?")
        if len(g) < 2 * fps:
            issues.append(f"ep {ep}: very short ({r['dur_s']}s)")

    t = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(t.to_string(index=False))
    lags = [l for r in rows for l in r["lag_frames"] if l is not None]
    if lags:
        med = float(np.median(lags))
        print(f"\naction->state lag: median {med:.1f} frames = {med / fps * 1000:.0f} ms "
              "(consistent small lag is normal servo tracking; large or erratic lag = timing/comm problem)")
    print(f"\n{len(issues)} issue(s):" if issues else "\nno per-episode issues found")
    for i in issues:
        print("  -", i)

    if cams:
        make_sheet(root, info, df, cams, args.sheet_episodes)


def make_sheet(root: Path, info: dict, df: pd.DataFrame, cams: list[str], n_eps: int) -> None:
    import cv2

    from lerobot.datasets.lerobot_dataset import LeRobotDataset

    ds = LeRobotDataset(f"local/{root.name}", root=root, video_backend="pyav")
    eps = sorted(df["episode_index"].unique())
    pick = [eps[i] for i in np.linspace(0, len(eps) - 1, min(n_eps, len(eps))).astype(int)]
    tiles_rows = []
    for ep in pick:
        g = df[df["episode_index"] == ep]
        grip = np.stack(g["action"].to_numpy())[:, 5]
        idx = g["index"].to_numpy()
        # first frame, frame where gripper command is most closed (~grasp), last frame
        sel = [idx[0], idx[int(np.argmin(grip)) if grip[0] > grip.min() else len(idx) // 2], idx[-1]]
        row = []
        for i in sel:
            item = ds[int(i)]
            for c in cams:
                im = (item[c].permute(1, 2, 0).numpy() * 255).astype(np.uint8)
                im = cv2.resize(cv2.cvtColor(im, cv2.COLOR_RGB2BGR), (213, 160))
                cv2.putText(im, f"ep{ep} {c.split('.')[-1]}", (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                row.append(im)
        tiles_rows.append(np.hstack(row))
    sheet = np.vstack(tiles_rows)
    out_dir = Path(__file__).resolve().parents[1] / "runs" / "check"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{root.name}_contact_sheet.jpg"
    cv2.imwrite(str(out), sheet)
    print(f"\ncontact sheet (rows=episodes; first/grasp/last x cameras): {out}")


if __name__ == "__main__":
    main()
