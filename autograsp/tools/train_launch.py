"""Compose and run `lerobot-train` for ACT (primary) or SmolVLA (comparison) on the local dataset.

Steps are derived from epochs (LeRobot AGENT_GUIDE §7) instead of a magic number. A few training episodes
can be withheld as an in-distribution validation split for tools/offline_eval.py.

    python autograsp/tools/train_launch.py --policy act --epochs 8 --val-every 10
    python autograsp/tools/train_launch.py --policy act --steps 300 --name smoke   # pipeline check
    python autograsp/tools/train_launch.py --policy smolvla --python .venv-smolvla/Scripts/python.exe
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

from common import PYTHON, dataset_root, load_rig

SHIM = Path(__file__).with_name("train_shim.py")

POLICY_DEFAULTS = {
    # chunk 50 @ 30 fps = 1.67 s of motion per inference; n_action_steps < chunk so the policy re-looks
    # at the scene more often than it would executing the whole chunk open-loop.
    "act": {"batch": 16, "extra": ["--policy.type=act", "--policy.chunk_size=50", "--policy.n_action_steps=15"]},
    "smolvla": {"batch": 16, "extra": ["--policy.path=lerobot/smolvla_base"]},
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", choices=list(POLICY_DEFAULTS), default="act")
    ap.add_argument("--repo", default=None, help="dataset repo id (default: rig.train_repo)")
    ap.add_argument("--root", default=None, help="dataset root (default: datasets/<repo name>)")
    ap.add_argument("--epochs", type=float, default=8)
    ap.add_argument("--steps", type=int, default=None, help="override epochs")
    ap.add_argument("--batch", type=int, default=None)
    ap.add_argument("--val-every", type=int, default=0, help="withhold every k-th episode (0 = none)")
    ap.add_argument("--exclude", default="", help="comma list of bad episodes to leave out of training")
    ap.add_argument("--no-augment", action="store_true", help="disable colour/affine image augmentation")
    ap.add_argument("--name", default=None)
    ap.add_argument("--python", default=str(PYTHON), help="interpreter (SmolVLA needs its own venv)")
    ap.add_argument("--num-workers", type=int, default=4)
    ap.add_argument("--print-only", action="store_true")
    ap.add_argument("extra", nargs="*", help="extra raw lerobot-train args")
    args = ap.parse_args()

    rig = load_rig()
    repo = args.repo or rig["train_repo"]
    root = Path(args.root) if args.root else dataset_root(rig, repo)
    info = json.loads((root / "meta" / "info.json").read_text(encoding="utf-8"))
    n_eps, n_frames = info["total_episodes"], info["total_frames"]

    episodes = list(range(n_eps))
    excluded = {int(e) for e in args.exclude.split(",") if e.strip()}
    val = [e for e in episodes if args.val_every and e % args.val_every == args.val_every - 1 and e not in excluded]
    train_eps = [e for e in episodes if e not in val and e not in excluded]
    train_frames = n_frames * len(train_eps) / max(n_eps, 1)  # approximation when episodes differ in length

    d = POLICY_DEFAULTS[args.policy]
    batch = args.batch or d["batch"]
    steps = args.steps or max(100, math.ceil(args.epochs * train_frames / batch))
    name = args.name or f"{args.policy}_{root.name}_{time.strftime('%m%d_%H%M')}"
    out = Path(rig["outputs_root"]) / "train" / name

    cmd = [
        args.python, str(SHIM),
        f"--dataset.repo_id={repo}", f"--dataset.root={root.as_posix()}",
        "--dataset.video_backend=pyav",  # torchcodec cannot load here (no system FFmpeg)
        f"--dataset.image_transforms.enable={'false' if args.no_augment else 'true'}",
        *d["extra"],
        "--policy.device=cuda", "--policy.push_to_hub=false",
        f"--batch_size={batch}", f"--steps={steps}",
        f"--save_freq={max(steps // 4, 100)}", f"--log_freq={max(min(steps // 50, 200), 10)}",
        f"--num_workers={args.num_workers}",
        f"--output_dir={out.as_posix()}", f"--job_name={name}", "--wandb.enable=false",
        *args.extra,
    ]
    if val or excluded:
        cmd.insert(4, f"--dataset.episodes={json.dumps(train_eps)}")

    print(f"dataset {root}: {n_eps} episodes / {n_frames} frames; train eps {len(train_eps)}, val eps {val}")
    print(f"policy={args.policy} batch={batch} steps={steps} (~{steps * batch / max(train_frames, 1):.1f} epochs)")
    print(" ".join(cmd))
    meta = {"cmd": cmd, "train_episodes": train_eps, "val_episodes": val, "excluded": sorted(excluded),
            "dataset_root": str(root)}
    if args.print_only:
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    (out.parent / f"{name}.launch.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
